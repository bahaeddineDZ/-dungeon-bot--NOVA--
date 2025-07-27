
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select, Modal, TextInput
import random
import time
import asyncio

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system
from tasks_system import tasks_system

# متغيرات الأسعار
store_items = [
    {"name": "🗡️ سيف سام", "price": 10_000, "fluctuation": 0.2},
    {"name": "🧪 جرعة الحكمة", "price": 25_000, "fluctuation": 0.2},
    {"name": "🪓 منجل", "price": 100_000, "fluctuation": 0.3},
    {"name": "🧪 كيميائي أحمر", "price": 60_000, "fluctuation": 0.3},
    {"name": "🧣 وشاح الحكام", "price": 250_000, "fluctuation": 0.3},
    {"name": "🛡️ درع التنين المصفح", "price": 500_000, "fluctuation": 0.4},
    {"name": "🛡️ ترس العمالقة", "price": 750_000, "fluctuation": 0.4},
    {"name": "🎽 زي المحارب", "price": 350_000, "fluctuation": 0.4},
    {"name": "🧤 قفازات المهارة", "price": 300_000, "fluctuation": 0.4},
    {"name": "💍 خاتم الزواج", "price": 400_000, "fluctuation": 0.4},
    {"name": "🐉 دابة التنين", "price": 5_000_000, "fluctuation": 0.6},
    {"name": "👑 تاج الهيمنة", "price": 10_000_000, "fluctuation": 0.6}
]

PRICES = {item["name"]: item["price"] for item in store_items}
PRICE_FILE = "prices.json"
PRICE_STATE_FILE = "price_state.json"
PRICE_DURATION = 6 * 60

def setup_economy_commands(bot):
    """إعداد أوامر النظام الاقتصادي"""
    
    @bot.command(name="رصيد")
    async def balance(ctx):
        user_id = str(ctx.author.id)
        data = load_data()

        if user_id not in data:
            await ctx.send("❌ يجب عليك أولاً استخدام أمر `بدء` لإنشاء حساب.")
            return

        user = data[user_id]
        balance = user.get("balance", {})
        dollar = balance.get("دولار", 0)
        gold = balance.get("ذهب", 0)
        diamond = balance.get("ماس", 0)
        
        total_wealth = dollar + (gold * 50) + (diamond * 100)
        
        if total_wealth >= 10000000:
            color = 0x9b59b6
            wealth_title = "🌟 إمبراطور الثروة"
        elif total_wealth >= 5000000:
            color = 0xf39c12
            wealth_title = "👑 ملك الثروة"
        elif total_wealth >= 1000000:
            color = 0xe67e22
            wealth_title = "🥇 تاجر ثري"
        elif total_wealth >= 100000:
            color = 0x3498db
            wealth_title = "🥈 تاجر متوسط"
        else:
            color = 0x95a5a6
            wealth_title = "🥉 تاجر مبتدئ"

        embed = discord.Embed(
            title=f"💰 محفظة {ctx.author.display_name}",
            description=f"**{wealth_title}**\n💎 إجمالي الثروة: **{total_wealth:,}** نقطة",
            color=color
        )
        
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        
        embed.add_field(
            name="💵 الدولار الأمريكي",
            value=f"**{dollar:,}** دولار",
            inline=True
        )
        embed.add_field(
            name="🪙 الذهب الخالص",
            value=f"**{gold:,}** أونصة\n💰 القيمة: {gold * 50:,}$",
            inline=True
        )
        embed.add_field(
            name="💎 الماس النادر",
            value=f"**{diamond:,}** قيراط\n💰 القيمة: {diamond * 100:,}$",
            inline=True
        )
        
        level_info = tasks_system.get_user_level_info(user_id)
        embed.add_field(
            name="🏆 المستوى والخبرة",
            value=f"📈 المستوى: **{level_info['level']}**\n⭐ الخبرة: **{level_info['experience']:,}**",
            inline=True
        )
        
        embed.set_footer(text="💡 استخدم الأوامر المختلفة لزيادة ثروتك ومستواك!")

        await ctx.send(embed=embed)

    @bot.command(name="حقيبة")
    async def inventory(ctx):
        user_id = str(ctx.author.id)
        init_user(user_id, ctx.author.display_name)
        data = load_data()
        inventory_list = data[user_id].get("حقيبة", [])

        if not inventory_list:
            await ctx.send("🎒 حقيبتك فارغة.")
            return

        item_counts = {}
        for item in inventory_list:
            item_counts[item] = item_counts.get(item, 0) + 1

        items_str = "\n".join(f"• {name} × {count}"
                              for name, count in item_counts.items())
        await ctx.send(f"🎒 محتويات حقيبتك:\n{items_str}")

    @bot.command(name="تحويل")
    async def transfer(ctx, member: discord.Member, العملة: str, المبلغ: int):
        if member.id == ctx.author.id:
            await ctx.send("❌ لا يمكنك تحويل العملات إلى نفسك.")
            return

        if المبلغ <= 0:
            await ctx.send("❌ يجب أن يكون المبلغ أكبر من 0.")
            return

        user_id = str(ctx.author.id)
        target_id = str(member.id)

        init_user(user_id, ctx.author.display_name)
        init_user(target_id, member.display_name)

        data = load_data()
        user = data[user_id]
        target = data[target_id]

        if العملة not in ["دولار", "ذهب", "ماس"]:
            await ctx.send("❌ العملة غير معروفة. اختر من: دولار، ذهب، ماس.")
            return

        if user["balance"].get(العملة, 0) < المبلغ:
            await ctx.send(f"❌ ليس لديك ما يكفي من {العملة} لإتمام التحويل.")
            return

        user["balance"][العملة] -= المبلغ
        target["balance"][العملة] = target["balance"].get(العملة, 0) + المبلغ

        save_data(data)

        await ctx.send(f"✅ تم تحويل {المبلغ} {العملة} إلى {member.mention} بنجاح.")
