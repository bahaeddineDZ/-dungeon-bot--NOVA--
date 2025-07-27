
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Modal, TextInput
import random
import time
import json
from datetime import datetime, timedelta

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system

# ملف بيانات الزواج
MARRIAGE_FILE = "marriages.json"

def load_marriages():
    """تحميل بيانات الزواج"""
    try:
        with open(MARRIAGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_marriages(marriages):
    """حفظ بيانات الزواج"""
    with open(MARRIAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(marriages, f, indent=4, ensure_ascii=False)

def get_user_marriage(user_id):
    """الحصول على معلومات زواج المستخدم"""
    marriages = load_marriages()
    return marriages.get(str(user_id))

def is_married(user_id):
    """فحص إذا كان المستخدم متزوج"""
    return get_user_marriage(user_id) is not None

def get_marriage_benefits():
    """المكافآت الزوجية"""
    return {
        "daily_bonus": 0.5,  # 50% مكافأة إضافية
        "work_bonus": 0.3,   # 30% مكافأة عمل
        "game_bonus": 0.2    # 20% مكافأة ألعاب
    }

# هدايا الزواج
MARRIAGE_GIFTS = {
    "🌹 وردة حمراء": {"price": 1000, "love_points": 5, "emoji": "🌹"},
    "💎 خاتم ماسي": {"price": 50000, "love_points": 25, "emoji": "💎"},
    "🍫 شوكولاتة": {"price": 500, "love_points": 2, "emoji": "🍫"},
    "💍 خاتم ذهبي": {"price": 10000, "love_points": 15, "emoji": "💍"},
    "👗 فستان أنيق": {"price": 25000, "love_points": 20, "emoji": "👗"},
    "🎁 صندوق مفاجآت": {"price": 75000, "love_points": 40, "emoji": "🎁"}
}

def setup_marriage_commands(bot):
    """إعداد أوامر الزواج"""

    @bot.command(name="زواج")
    async def marry_command(ctx, partner: discord.Member = None):
        """طلب الزواج من شخص"""
        user_id = str(ctx.author.id)
        
        if not partner:
            await ctx.send("❌ يجب تحديد الشخص الذي تريد الزواج منه!\n💡 استخدم: `زواج @الشخص`")
            return
        
        if partner.id == ctx.author.id:
            await ctx.send("❌ لا يمكنك الزواج من نفسك! 😅")
            return
        
        if partner.bot:
            await ctx.send("❌ لا يمكن الزواج من البوتات! 🤖")
            return
        
        # فحص إذا كان أحدهما متزوج بالفعل
        if is_married(user_id):
            await ctx.send("❌ أنت متزوج بالفعل! استخدم `طلاق` أولاً.")
            return
        
        if is_married(str(partner.id)):
            await ctx.send(f"❌ {partner.mention} متزوج بالفعل!")
            return
        
        # فحص التبريد
        can_use, time_left = check_cooldown(user_id, "زواج")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل طلب الزواج مرة أخرى.")
            return
        
        class MarriageProposalView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.accepted = False
            
            @discord.ui.button(label="💕 قبول الزواج", style=ButtonStyle.success)
            async def accept_marriage(self, interaction: Interaction, button: Button):
                if interaction.user.id != partner.id:
                    await interaction.response.send_message("❌ هذا الطلب ليس لك!", ephemeral=True)
                    return
                
                # التحقق مرة أخرى من حالة الزواج
                if is_married(user_id) or is_married(str(partner.id)):
                    await interaction.response.send_message("❌ أحدكما متزوج بالفعل الآن!", ephemeral=True)
                    return
                
                # إنشاء الزواج
                marriages = load_marriages()
                marriage_data = {
                    "partner_id": str(partner.id),
                    "partner_name": partner.display_name,
                    "marriage_date": datetime.now().isoformat(),
                    "love_points": 100,
                    "gifts_given": 0,
                    "anniversaries": 0
                }
                
                # إضافة الزواج لكلا الطرفين
                marriages[user_id] = marriage_data.copy()
                marriages[user_id]["partner_id"] = str(partner.id)
                marriages[user_id]["partner_name"] = partner.display_name
                
                marriages[str(partner.id)] = marriage_data.copy()
                marriages[str(partner.id)]["partner_id"] = user_id
                marriages[str(partner.id)]["partner_name"] = ctx.author.display_name
                
                save_marriages(marriages)
                
                # تسجيل النشاط
                logs_system.add_log(
                    "marriage_logs",
                    user_id,
                    ctx.author.display_name,
                    f"تزوج من {partner.display_name}",
                    {"partner": partner.display_name, "date": marriage_data["marriage_date"]}
                )
                
                # تحديث التبريد
                update_cooldown(user_id, "زواج")
                
                embed = Embed(
                    title="🎉 مبروك الزواج! 🎉",
                    description=f"💕 **{ctx.author.mention} و {partner.mention} أصبحا زوجين!**\n\n🎊 نتمنى لكما حياة سعيدة مليئة بالحب والسعادة!",
                    color=0xe91e63
                )
                
                embed.add_field(
                    name="💎 مكافآت الزواج",
                    value=(
                        "💰 +50% مكافأة يومية\n"
                        "👷 +30% مكافأة عمل\n"
                        "🎮 +20% مكافأة ألعاب\n"
                        "💝 إمكانية إرسال الهدايا"
                    ),
                    inline=True
                )
                
                embed.add_field(
                    name="🎯 نصائح للزوجين",
                    value=(
                        "🎁 `هدية` - أرسل هدايا لشريكك\n"
                        "🏖️ `شهر_عسل` - اذهبا في رحلة\n"
                        "👫 `زوجي` - معلومات العلاقة"
                    ),
                    inline=True
                )
                
                embed.set_footer(text="💕 الحب هو أجمل شيء في الحياة!")
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/690323752369848364.png")
                
                await interaction.response.edit_message(embed=embed, view=None)
            
            @discord.ui.button(label="💔 رفض الزواج", style=ButtonStyle.danger)
            async def reject_marriage(self, interaction: Interaction, button: Button):
                if interaction.user.id != partner.id:
                    await interaction.response.send_message("❌ هذا الطلب ليس لك!", ephemeral=True)
                    return
                
                embed = Embed(
                    title="💔 تم رفض طلب الزواج",
                    description=f"{partner.mention} رفض طلب الزواج من {ctx.author.mention}",
                    color=0xe74c3c
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
        
        # إرسال طلب الزواج
        embed = Embed(
            title="💍 طلب زواج!",
            description=f"💕 **{ctx.author.mention}** يطلب الزواج من **{partner.mention}**!\n\n💭 هل توافق على هذا الاقتران المبارك؟",
            color=0xe91e63
        )
        
        embed.add_field(
            name="💎 مميزات الزواج",
            value="💰 مكافآت مضاعفة\n🎁 هدايا رومانسية\n🏖️ رحلات شهر عسل",
            inline=True
        )
        
        embed.set_footer(text="⏰ لديك دقيقتان للرد على الطلب")
        
        await ctx.send(embed=embed, view=MarriageProposalView())

    @bot.command(name="طلاق")
    async def divorce_command(ctx):
        """طلب الطلاق"""
        user_id = str(ctx.author.id)
        
        if not is_married(user_id):
            await ctx.send("❌ أنت لست متزوجاً!")
            return
        
        marriage = get_user_marriage(user_id)
        partner_id = marriage["partner_id"]
        partner_name = marriage["partner_name"]
        
        # تكلفة الطلاق
        divorce_cost = 100000  # 100K دولار
        
        data = load_data()
        init_user(user_id, ctx.author.display_name)
        user = data[user_id]
        
        if user["balance"].get("دولار", 0) < divorce_cost:
            await ctx.send(f"❌ تحتاج إلى {divorce_cost:,} دولار لإجراء الطلاق!")
            return
        
        class DivorceConfirmView(View):
            def __init__(self):
                super().__init__(timeout=60)
            
            @discord.ui.button(label="💔 تأكيد الطلاق", style=ButtonStyle.danger)
            async def confirm_divorce(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                    return
                
                # خصم التكلفة
                user["balance"]["دولار"] -= divorce_cost
                save_data(data)
                
                # حذف الزواج
                marriages = load_marriages()
                if user_id in marriages:
                    del marriages[user_id]
                if partner_id in marriages:
                    del marriages[partner_id]
                save_marriages(marriages)
                
                # تسجيل النشاط
                logs_system.add_log(
                    "marriage_logs",
                    user_id,
                    ctx.author.display_name,
                    f"طلق من {partner_name}",
                    {"partner": partner_name, "cost": divorce_cost}
                )
                
                embed = Embed(
                    title="💔 تم الطلاق",
                    description=f"تم إنهاء الزواج بين {ctx.author.mention} و {partner_name}\n\n💸 تم خصم {divorce_cost:,} دولار كرسوم طلاق",
                    color=0xe74c3c
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
            
            @discord.ui.button(label="❌ إلغاء", style=ButtonStyle.secondary)
            async def cancel_divorce(self, interaction: Interaction, button: Button):
                await interaction.response.edit_message(content="❌ تم إلغاء طلب الطلاق.", view=None)
        
        embed = Embed(
            title="⚠️ تأكيد الطلاق",
            description=f"هل أنت متأكد من طلاق **{partner_name}**؟\n\n💸 **التكلفة:** {divorce_cost:,} دولار\n💔 **سيتم فقدان جميع مكافآت الزواج**",
            color=0xe74c3c
        )
        
        await ctx.send(embed=embed, view=DivorceConfirmView())

    @bot.command(name="زوجي")
    async def spouse_info(ctx):
        """معلومات عن الزوج/الزوجة"""
        user_id = str(ctx.author.id)
        
        if not is_married(user_id):
            await ctx.send("❌ أنت لست متزوجاً! استخدم `زواج @الشخص` للزواج.")
            return
        
        marriage = get_user_marriage(user_id)
        partner_name = marriage["partner_name"]
        marriage_date = datetime.fromisoformat(marriage["marriage_date"])
        love_points = marriage.get("love_points", 100)
        gifts_given = marriage.get("gifts_given", 0)
        
        # حساب مدة الزواج
        days_married = (datetime.now() - marriage_date).days
        
        embed = Embed(
            title="💕 معلومات الزواج",
            description=f"💍 **زوجك:** {partner_name}",
            color=0xe91e63
        )
        
        embed.add_field(
            name="📅 تاريخ الزواج",
            value=marriage_date.strftime("%Y/%m/%d"),
            inline=True
        )
        
        embed.add_field(
            name="⏰ مدة الزواج",
            value=f"{days_married} يوم",
            inline=True
        )
        
        embed.add_field(
            name="💖 نقاط الحب",
            value=f"{love_points}/100",
            inline=True
        )
        
        embed.add_field(
            name="🎁 الهدايا المرسلة",
            value=f"{gifts_given} هدية",
            inline=True
        )
        
        # تقييم العلاقة
        if love_points >= 80:
            relationship_status = "💕 علاقة رائعة"
            color = 0x2ecc71
        elif love_points >= 60:
            relationship_status = "💛 علاقة جيدة"
            color = 0xf39c12
        elif love_points >= 40:
            relationship_status = "🧡 علاقة متوسطة"
            color = 0xe67e22
        else:
            relationship_status = "💔 علاقة تحتاج اهتمام"
            color = 0xe74c3c
        
        embed.add_field(
            name="📊 حالة العلاقة",
            value=relationship_status,
            inline=True
        )
        
        embed.color = color
        embed.set_footer(text="💡 أرسل هدايا لتحسين نقاط الحب!")
        
        await ctx.send(embed=embed)

    @bot.command(name="هدية")
    async def send_gift(ctx, gift_name: str = None):
        """إرسال هدية للزوج/الزوجة"""
        user_id = str(ctx.author.id)
        
        if not is_married(user_id):
            await ctx.send("❌ يجب أن تكون متزوجاً لإرسال الهدايا!")
            return
        
        # فحص التبريد
        can_use, time_left = check_cooldown(user_id, "هدية")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل إرسال هدية أخرى.")
            return
        
        if not gift_name:
            # عرض قائمة الهدايا
            embed = Embed(
                title="🎁 متجر الهدايا الرومانسية",
                description="اختر هدية لإرسالها لشريك حياتك:",
                color=0xe91e63
            )
            
            gifts_text = ""
            for name, info in MARRIAGE_GIFTS.items():
                gifts_text += f"{info['emoji']} **{name}**\n💰 السعر: {info['price']:,} دولار | 💖 نقاط الحب: +{info['love_points']}\n\n"
            
            embed.add_field(
                name="💝 الهدايا المتاحة",
                value=gifts_text,
                inline=False
            )
            
            embed.set_footer(text="💡 استخدم: هدية [اسم الهدية]")
            await ctx.send(embed=embed)
            return
        
        # البحث عن الهدية
        selected_gift = None
        for gift, info in MARRIAGE_GIFTS.items():
            if gift_name.lower() in gift.lower():
                selected_gift = (gift, info)
                break
        
        if not selected_gift:
            await ctx.send("❌ هدية غير موجودة! استخدم `هدية` لعرض القائمة.")
            return
        
        gift_name, gift_info = selected_gift
        price = gift_info["price"]
        love_points = gift_info["love_points"]
        
        # فحص الرصيد
        data = load_data()
        init_user(user_id, ctx.author.display_name)
        user = data[user_id]
        
        if user["balance"].get("دولار", 0) < price:
            await ctx.send(f"❌ لا تملك ما يكفي من المال!\nتحتاج: {price:,} دولار")
            return
        
        # خصم المال وإرسال الهدية
        user["balance"]["دولار"] -= price
        save_data(data)
        
        # تحديث نقاط الحب
        marriages = load_marriages()
        marriage = marriages[user_id]
        marriage["love_points"] = min(100, marriage["love_points"] + love_points)
        marriage["gifts_given"] = marriage.get("gifts_given", 0) + 1
        
        # تحديث بيانات الشريك أيضاً
        partner_id = marriage["partner_id"]
        if partner_id in marriages:
            marriages[partner_id]["love_points"] = marriage["love_points"]
        
        save_marriages(marriages)
        
        # تسجيل النشاط
        logs_system.add_log(
            "marriage_logs",
            user_id,
            ctx.author.display_name,
            f"أرسل هدية: {gift_name}",
            {"gift": gift_name, "cost": price, "love_points": love_points}
        )
        
        update_cooldown(user_id, "هدية")
        
        embed = Embed(
            title="💝 تم إرسال الهدية!",
            description=f"🎁 أرسلت **{gift_name}** إلى {marriage['partner_name']}!",
            color=0x2ecc71
        )
        
        embed.add_field(
            name="💖 تأثير الهدية",
            value=f"نقاط الحب: +{love_points}\nالنقاط الحالية: {marriage['love_points']}/100",
            inline=True
        )
        
        embed.add_field(
            name="💰 التكلفة",
            value=f"{price:,} دولار",
            inline=True
        )
        
        await ctx.send(embed=embed)

    @bot.command(name="شهر_عسل")
    async def honeymoon(ctx):
        """الذهاب في شهر عسل"""
        user_id = str(ctx.author.id)
        
        if not is_married(user_id):
            await ctx.send("❌ يجب أن تكون متزوجاً للذهاب في شهر عسل!")
            return
        
        # فحص التبريد
        can_use, time_left = check_cooldown(user_id, "شهر_عسل")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل شهر عسل آخر.")
            return
        
        marriage = get_user_marriage(user_id)
        love_points = marriage.get("love_points", 100)
        
        # تكلفة شهر العسل
        honeymoon_cost = 50000
        
        data = load_data()
        init_user(user_id, ctx.author.display_name)
        user = data[user_id]
        
        if user["balance"].get("دولار", 0) < honeymoon_cost:
            await ctx.send(f"❌ تحتاج إلى {honeymoon_cost:,} دولار لشهر العسل!")
            return
        
        # تنفيذ شهر العسل
        user["balance"]["دولار"] -= honeymoon_cost
        
        # المكافآت حسب نقاط الحب
        base_reward = 75000
        love_bonus = int(base_reward * (love_points / 100))
        total_reward = base_reward + love_bonus
        
        # مكافآت إضافية عشوائية
        bonus_gold = random.randint(10, 25)
        bonus_exp = random.randint(300, 500)
        
        user["balance"]["دولار"] += total_reward
        user["balance"]["ذهب"] = user["balance"].get("ذهب", 0) + bonus_gold
        user["experience"] = user.get("experience", 0) + bonus_exp
        
        save_data(data)
        update_cooldown(user_id, "شهر_عسل")
        
        # أماكن شهر العسل العشوائية
        destinations = [
            "🏝️ جزر المالديف", "🗼 باريس", "🏔️ سويسرا", 
            "🌸 اليابان", "🏖️ هاواي", "🏛️ اليونان"
        ]
        destination = random.choice(destinations)
        
        embed = Embed(
            title="🏖️ شهر عسل رومانسي!",
            description=f"🎊 استمتعتما برحلة رائعة إلى **{destination}**!",
            color=0xe91e63
        )
        
        embed.add_field(
            name="💰 مكافآت الرحلة",
            value=f"💵 {total_reward:,} دولار\n🪙 {bonus_gold} ذهب\n⭐ {bonus_exp} خبرة",
            inline=True
        )
        
        embed.add_field(
            name="💖 تأثير الحب",
            value=f"نقاط الحب: {love_points}/100\nمكافأة الحب: +{love_bonus:,}$",
            inline=True
        )
        
        embed.set_footer(text="💕 الذكريات الجميلة لا تُنسى!")
        
        await ctx.send(embed=embed)

    return True
