
import os
import json
import random
import time
import asyncio

import discord
from discord.ext import tasks
from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, Button, Select, Modal, TextInput

# استيراد الوحدات
from bot_setup import setup_bot, get_discord_token
from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown, format_time, load_cooldowns, DEFAULT_COOLDOWN
from logs_system import logs_system, LeaderboardView, LogsView
from tasks_system import tasks_system
from keep_alive import keep_alive
from dungeons_system import *
from help_system import AdvancedHelpSystem

# إعداد البوت
bot = setup_bot()

# متغيرات عامة
DATA_FILE = "users.json"
PRICE_FILE = "prices.json"
advanced_help_system = None

# الأحداث الأساسية
@bot.event
async def on_ready():
    global advanced_help_system
    print(f"🔷 البوت جاهز: {bot.user}")
    
    advanced_help_system = AdvancedHelpSystem(bot)
    print("📚 تم تفعيل نظام الشروحات المطور")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    content = message.content.strip().lower()
    
    # التحقق من وجود ملف البيانات
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

    with open("users.json", "r") as f:
        users = json.load(f)

    # إنشاء حساب جديد للمستخدم
    if user_id not in users:
        users[user_id] = {
            "balance": {"دولار": 0, "ذهب": 0, "ماس": 0},
            "حقيبة": [],
            "fish_pond": [],
            "المهنة": "مواطن",
            "الصورة": "",
            "specialization": None,
            "spec_level": 1,
            "name": message.author.display_name
        }

        with open("users.json", "w") as f:
            json.dump(users, f, indent=4, ensure_ascii=False)

        embed = Embed(
            title="🎊 أهلاً وسهلاً في عالم NOVA BANK! 🎊",
            description=(
                f"🌟 **مرحباً {message.author.mention}!** \n\n"
                "🏆 **لقد انضممت إلى أكبر نظام اقتصادي تفاعلي!**\n\n"
                "🎯 **ما الذي ينتظرك:**\n"
                "💰 **اقتصاد متطور:** 3 عملات مختلفة (دولار، ذهب، ماس)\n"
                "🏪 **متجر ديناميكي:** أسعار تتغير كل 6 دقائق!\n"
                "⚔️ **4 اختصاصات قتالية:** محارب، شامان، نينجا، سورا\n"
                "🏰 **5 سراديب أسطورية:** تحديات ملحمية ومكافآت خرافية\n"
                "🌾 **زراعة وصيد:** 5 محاصيل و 6 أنواع أسماك\n"
                "🎮 **5 ألعاب تفاعلية:** اختبر مهاراتك واربح المكافآت\n"
                "🎯 **نظام مهام متقدم:** مهام يومية وأسبوعية بمكافآت ضخمة\n"
                "📈 **نظام مستويات:** اكسب الخبرة وارتق في المراتب\n\n"
                "🔥 **رصيدك الأولي:**\n"
                "💵 **0** دولار | 🪙 **0** ذهب | 💎 **0** ماس\n\n"
                "🚀 **ابدأ رحلتك نحو الثروة والمجد!**"
            ),
            color=0x00d4ff
        )

        embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
        embed.set_footer(text="💡 نصيحة: ابدأ بالأمر 'يومي' للحصول على رصيد أولي مجاني!")

        await message.channel.send(embed=embed)
        return

    # معالجة الأوامر
    ctx = type('Context', (), {
        'author': message.author,
        'channel': message.channel,
        'guild': message.guild,
        'send': message.channel.send
    })()

    # الأوامر الأساسية
    if content == "سلام":
        await handle_salam(ctx)
    elif content == "حسابي":
        await handle_my_profile(ctx)
    elif content == "رصيد":
        await handle_balance(ctx)
    elif content == "حقيبة":
        await handle_inventory(ctx)
    elif content == "تبريد":
        await handle_show_cooldowns(ctx)
    elif content == "مهنتي":
        await handle_my_job(ctx)
    elif content == "عمل":
        await handle_work(ctx)
    elif content == "اختصاص":
        await handle_specialization(ctx)
    elif content == "حجر_ورقة_مقص" or content == "حجر ورقة مقص":
        await handle_rock_paper_scissors(ctx)
    elif content == "تخمين":
        await handle_guessing_game(ctx)
    elif content == "يومي":
        await handle_daily_reward(ctx)
    elif content == "متجر":
        await handle_store(ctx)
    elif content == "زراعة":
        await handle_farming(ctx)
    elif content == "صيد":
        await handle_fishing(ctx)
    elif content == "تداول":
        await handle_trading(ctx)
    elif content == "استثمار":
        await handle_investment(ctx)
    elif content == "نهب":
        await handle_theft(ctx)
    elif content == "سراديب":
        await handle_dungeons(ctx)
    elif content == "مهام":
        await handle_tasks(ctx)
    elif content == "سجلات":
        await handle_logs(ctx)
    elif content == "مساعدة" or content == "help":
        await handle_help(ctx)
    elif content.startswith("تحويل "):
        await handle_transfer(ctx, content)
    elif content.startswith("شراء "):
        await handle_buy(ctx, content)
    elif content.startswith("بيع "):
        await handle_sell(ctx, content)

# دوال معالجة الأوامر
async def handle_salam(ctx):
    await ctx.send("وعليكم السلام   👑")

async def handle_my_profile(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    if user_id not in data:
        init_user(user_id, ctx.author.display_name)
        data = load_data()

    user_data = data[user_id]
    balance = user_data.get("balance", {})
    balance_text = (
        f"💵 {balance.get('دولار', 0):,} دولار\n"
        f"🪙 {balance.get('ذهب', 0):,} ذهب\n"
        f"💎 {balance.get('ماس', 0):,} ماس"
    )

    specialization = user_data.get("specialization", {})
    if isinstance(specialization, dict) and specialization:
        spec_text = f"النوع: {specialization.get('type', '❌')}\nالرتبة: {specialization.get('rank', '❌')}"
    else:
        spec_text = "❌ لا يوجد"

    bag_count = len(user_data.get("حقيبة", []))
    job = user_data.get("المهنة", "❌ لا توجد")

    embed = discord.Embed(
        title="📒 حسابك الشخصي",
        description=f"معلومات {ctx.author.mention}",
        color=0x00b0f4
    )

    embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embed.add_field(name="🪙 الرصيد", value=balance_text, inline=False)
    embed.add_field(name="🎒 الحقيبة", value=f"{bag_count} عنصر", inline=True)
    embed.add_field(name="🛠️ الاختصاص", value=spec_text, inline=True)
    embed.add_field(name="👷 المهنة", value=job, inline=True)

    await ctx.send(embed=embed)

async def handle_balance(ctx):
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("❌ يجب عليك أولاً كتابة أي رسالة لإنشاء حساب.")
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

async def handle_inventory(ctx):
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

async def handle_show_cooldowns(ctx):
    user_id = str(ctx.author.id)
    cooldowns = load_cooldowns().get(user_id, {})
    current_time = int(time.time())

    embed = discord.Embed(
        title="📊 قائمة التبريد الخاصة بك",
        description="تعرف على حالة أوامرك الحالية:",
        color=0x2ECC71
    )

    any_cooldowns = False

    for command_name, cooldown_time in DEFAULT_COOLDOWN.items():
        last_used = cooldowns.get(command_name, 0)
        elapsed = current_time - last_used
        time_left = cooldown_time - elapsed

        if time_left > 0:
            minutes, seconds = divmod(time_left, 60)
            time_str = f"{minutes}د {seconds}ث" if minutes else f"{seconds}ث"

            embed.add_field(
                name=f"🔸 `{command_name}`",
                value=f"🔁 قيد التبريد\n⏳ **{time_str}** متبقية",
                inline=True
            )
            any_cooldowns = True
        else:
            embed.add_field(
                name=f"🟢 `{command_name}`",
                value="✅ **جاهز الآن** للاستخدام",
                inline=True
            )

    if not any_cooldowns:
        embed.description += "\n\n🎉 كل أوامرك جاهزة الآن! 🚀"

    await ctx.send(embed=embed)

async def handle_my_job(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    job = data[user_id].get("المهنة", "مواطن")
    await ctx.send(f"👷 وظيفتك الحالية: **{job}**")

async def handle_work(ctx):
    user_id = str(ctx.author.id)

    allowed, time_left = check_cooldown(user_id, "عمل")
    if not allowed:
        await ctx.send(f"⏳ يمكنك العمل مرة أخرى بعد {time_left}.")
        return

    update_cooldown(user_id, "عمل")

    init_user(user_id, ctx.author.display_name)
    data = load_data()

    current_job = data[user_id].get("المهنة", "مواطن")

    job_ranks = {
        "مواطن": 1, "رسام": 2, "طبيب": 3, "مقدم": 4,
        "جنيرال": 5, "وزير": 6, "ملك": 7, "إمبراطور": 8
    }

    rank = job_ranks.get(current_job, 1)

    dollars = 0
    gold = 0

    if rank >= 7:
        gold = random.randint(20, 40)
    elif rank >= 4:
        gold = random.randint(10, 20)
        dollars = random.randint(40_000, 60_000)
    else:
        dollars = random.randint(60_000, 90_000)

    data[user_id]["balance"]["دولار"] += dollars
    data[user_id]["balance"]["ذهب"] += gold

    save_data(data)

    embed = discord.Embed(
        title=f"💼 عملت في وظيفة {current_job}",
        description=f"🎉 لقد أتممت يوم عمل ناجح!",
        color=0x2ecc71
    )

    if dollars > 0:
        embed.add_field(name="💵 المكافأة النقدية", value=f"{dollars:,} دولار", inline=True)
    if gold > 0:
        embed.add_field(name="🪙 مكافأة الذهب", value=f"{gold:,} أونصة", inline=True)

    logs_system.add_log(
        "work_logs",
        user_id,
        ctx.author.display_name,
        f"عمل في وظيفة {current_job}",
        {"job": current_job, "earned": dollars + gold, "dollars": dollars, "gold": gold}
    )

    await ctx.send(embed=embed)

async def handle_specialization(ctx):
    from specialization_commands import SPECIALIZATIONS_INFO, get_role_level_bonus, ranks
    
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        init_user(user_id, ctx.author.display_name)
        data = load_data()

    user = data[user_id]
    balance = user.get("balance", {})
    gold = balance.get("ذهب", 0)
    spec = user.get("specialization")

    def get_bonus_description(role_type, rank_name):
        bonus = get_role_level_bonus(role_type, rank_name)
        if not bonus:
            return ""
        if bonus["type"] == "revenge":
            return f"🔁 استرداد {bonus['percentage']}٪ من الأموال المسروقة"
        elif bonus["type"] == "shield":
            return f"🛡️ حماية لمدة {bonus['duration']} دقيقة"
        elif bonus["type"] == "steal_boost":
            return f"🥷 نهب {bonus['percentage']}٪ من أموال الضحية"
        elif bonus["type"] == "reflect":
            return f"🧿 عكس النهب بنسبة {bonus['percentage']}٪"
        return ""

    if not spec:
        role_options = ["محارب", "شامان", "نينجا", "سورا"]
        
        class SpecializationSelectionView(View):
            def __init__(self):
                super().__init__(timeout=180)
                
                for role in role_options:
                    self.add_item(SpecializationInfoButton(role))

        class SpecializationInfoButton(Button):
            def __init__(self, role):
                info = SPECIALIZATIONS_INFO[role]
                super().__init__(
                    label=f"{info['emoji']} {role}",
                    style=ButtonStyle.primary
                )
                self.role = role

            async def callback(self, interaction: Interaction):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("🚫 ليس لك صلاحية!", ephemeral=True)
                    return

                info = SPECIALIZATIONS_INFO[self.role]
                
                embed = Embed(
                    title=f"{info['emoji']} {info['title']}",
                    description=info['description'],
                    color=info['color']
                )
                
                embed.add_field(
                    name="🎯 القدرات الخاصة",
                    value=f"• **الأساسية:** {info['abilities']['primary']}\n• **الثانوية:** {info['abilities']['secondary']}\n• **السلبية:** {info['abilities']['passive']}",
                    inline=False
                )
                
                embed.add_field(
                    name="🎮 أسلوب اللعب",
                    value=info['playstyle'],
                    inline=True
                )
                
                embed.add_field(
                    name="📊 الصعوبة",
                    value=info['difficulty'],
                    inline=True
                )

                class ConfirmSpecView(View):
                    def __init__(self, selected_role):
                        super().__init__(timeout=60)
                        self.selected_role = selected_role

                    @discord.ui.button(label="✅ اختيار هذا الاختصاص", style=ButtonStyle.success)
                    async def confirm_spec(self, confirm_interaction: Interaction, button: Button):
                        if confirm_interaction.user.id != ctx.author.id:
                            await confirm_interaction.response.send_message("🚫 ليس لك صلاحية!", ephemeral=True)
                            return

                        user["specialization"] = {"type": self.selected_role, "rank": 1, "upgrade_cost": 100}
                        save_data(data)

                        success_embed = Embed(
                            title="🎉 تم اختيار الاختصاص بنجاح!",
                            description=f"أصبحت الآن **{SPECIALIZATIONS_INFO[self.selected_role]['title']}**!",
                            color=0x2ecc71
                        )
                        
                        desc = get_bonus_description(self.selected_role, "نبيل")
                        success_embed.add_field(
                            name="🔹 قدرتك الحالية",
                            value=desc,
                            inline=False
                        )

                        await confirm_interaction.response.edit_message(embed=success_embed, view=None)

                await interaction.response.edit_message(embed=embed, view=ConfirmSpecView(self.role))

        main_embed = Embed(
            title="🎯 اختيار الاختصاص",
            description="**اختر اختصاصك الذي سيحدد أسلوب لعبك وقدراتك الخاصة!**\n\nكل اختصاص له مميزات فريدة وأسلوب لعب مختلف. اختر بحكمة!",
            color=0x3498db
        )
        
        await ctx.send(embed=main_embed, view=SpecializationSelectionView())
        return

    # عرض الاختصاص الحالي
    info = SPECIALIZATIONS_INFO[spec['type']]
    current_rank = spec.get("rank", 1)
    current_rank_name = ranks[current_rank - 1]
    
    main_embed = Embed(
        title=f"{info['emoji']} {info['title']}",
        description=f"**رتبتك الحالية:** {current_rank_name}\n{info['description']}",
        color=info['color']
    )
    
    current_desc = get_bonus_description(spec['type'], current_rank_name)
    main_embed.add_field(
        name="🔹 قدرتك الحالية",
        value=current_desc,
        inline=False
    )

    await ctx.send(embed=main_embed)

async def handle_rock_paper_scissors(ctx):
    user_id = str(ctx.author.id)
    can_use, time_left = check_cooldown(user_id, "حجر_ورقة_مقص")
    if not can_use:
        await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
        return

    class RPSView(View):
        def __init__(self):
            super().__init__(timeout=30)
            self.user_choice = None

        @discord.ui.button(label="🪨 حجر", style=ButtonStyle.secondary)
        async def rock(self, interaction: Interaction, button: Button):
            await self.play_game(interaction, "حجر", "🪨")

        @discord.ui.button(label="📄 ورقة", style=ButtonStyle.primary)
        async def paper(self, interaction: Interaction, button: Button):
            await self.play_game(interaction, "ورقة", "📄")

        @discord.ui.button(label="✂️ مقص", style=ButtonStyle.danger)
        async def scissors(self, interaction: Interaction, button: Button):
            await self.play_game(interaction, "مقص", "✂️")

        async def play_game(self, interaction: Interaction, choice, emoji):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                return

            bot_choices = ["حجر", "ورقة", "مقص"]
            bot_emojis = {"حجر": "🪨", "ورقة": "📄", "مقص": "✂️"}
            bot_choice = random.choice(bot_choices)

            if choice == bot_choice:
                result = "تعادل! 🤝"
                color = 0xFFD700
                reward = 500
            elif (choice == "حجر" and bot_choice == "مقص") or \
                 (choice == "ورقة" and bot_choice == "حجر") or \
                 (choice == "مقص" and bot_choice == "ورقة"):
                result = "فزت! 🎉"
                color = 0x00FF00
                reward = 2000
            else:
                result = "خسرت! 😢"
                color = 0xFF0000
                reward = 100

            init_user(user_id, ctx.author.display_name)
            data = load_data()
            data[user_id]["balance"]["دولار"] += reward
            save_data(data)

            embed = discord.Embed(
                title="🎮 حجر ورقة مقص",
                description=f"{emoji} أنت اخترت: **{choice}**\n{bot_emojis[bot_choice]} البوت اختار: **{bot_choice}**\n\n{result}\n💰 ربحت: {reward} دولار",
                color=color
            )

            logs_system.add_log(
                "game_logs",
                user_id,
                ctx.author.display_name,
                "لعب حجر ورقة مقص",
                {"game": "حجر_ورقة_مقص", "result": result, "reward": reward}
            )
            
            if "فزت" in result:
                completed_tasks = tasks_system.update_task_progress(user_id, "win_games", 1)
                if completed_tasks:
                    embed.add_field(
                        name="🎯 مهام مكتملة!",
                        value=f"✅ أكملت {len(completed_tasks)} مهمة!",
                        inline=False
                    )

            update_cooldown(user_id, "حجر_ورقة_مقص")
            await interaction.response.edit_message(embed=embed, view=None)

    embed = discord.Embed(
        title="🎮 لعبة حجر ورقة مقص",
        description="اختر حركتك:",
        color=0x3498db
    )
    await ctx.send(embed=embed, view=RPSView())

async def handle_guessing_game(ctx):
    user_id = str(ctx.author.id)
    can_use, time_left = check_cooldown(user_id, "تخمين")
    if not can_use:
        await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
        return

    secret_number = random.randint(1, 100)
    max_attempts = 15

    class GuessingView(View):
        def __init__(self, author: discord.Member, target: int):
            super().__init__(timeout=120)
            self.author = author
            self.target = target
            self.attempts_left = max_attempts
            self.message = None
            self.game_over = False
            self.result_text = f"🎯 خمن رقمًا بين 1 و 100\n📉 لديك {self.attempts_left} محاولة"

        @discord.ui.button(label="🎲 خمن", style=ButtonStyle.primary)
        async def guess_button(self, interaction: Interaction, button: Button):
            if interaction.user.id != self.author.id:
                await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                return

            if self.game_over:
                await interaction.response.send_message("❌ اللعبة انتهت!", ephemeral=True)
                return

            view = self

            class NumberModal(Modal, title="🔮 أدخل رقمك"):
                def __init__(modal_self):
                    super().__init__()
                    modal_self.number_input = TextInput(
                        label="اكتب رقمًا من 1 إلى 100",
                        placeholder="مثلاً: 42",
                        max_length=3,
                        required=True
                    )
                    modal_self.add_item(modal_self.number_input)

                async def on_submit(modal_self, modal_interaction: Interaction):
                    try:
                        guess = int(modal_self.number_input.value.strip())
                        if not 1 <= guess <= 100:
                            raise ValueError
                    except ValueError:
                        await modal_interaction.response.send_message("🚫 الرقم غير صالح. اختر من 1 إلى 100.", ephemeral=True)
                        return

                    init_user(user_id, ctx.author.display_name)
                    data = load_data()

                    view.attempts_left -= 1

                    if guess == view.target:
                        reward = (view.attempts_left * 500) + 8000
                        data[user_id]["balance"]["دولار"] = data[user_id]["balance"].get("دولار", 0) + reward
                        save_data(data)
                        update_cooldown(user_id, "تخمين")
                        view.result_text = f"🎉 صحيح! الرقم هو {view.target}.\n💰 ربحت {reward} دولار.\n🏆 محاولات متبقية: {view.attempts_left}"
                        view.game_over = True
                        view.disable_all_items()
                    elif view.attempts_left == 0:
                        reward = 500
                        data[user_id]["balance"]["دولار"] = data[user_id]["balance"].get("دولار", 0) + reward
                        save_data(data)
                        update_cooldown(user_id, "تخمين")
                        view.result_text = f"💥 انتهت المحاولات! الرقم الصحيح كان {view.target}.\n💸 مكافأة تشجيعية: {reward} دولار."
                        view.game_over = True
                        view.disable_all_items()
                    else:
                        hint = "🔺 أعلى" if guess < view.target else "🔻 أقل"
                        view.result_text = f"❌ خطأ! رقمك: {guess}\n{hint}\n📉 المحاولات المتبقية: {view.attempts_left}"

                    await modal_interaction.response.defer()
                    await view.update_message()

            await interaction.response.send_modal(NumberModal())

        async def update_message(self):
            embed = discord.Embed(
                title="🔮 لعبة التخمين",
                description=self.result_text,
                color=discord.Color.green() if not self.game_over else (discord.Color.gold() if "🎉" in self.result_text else discord.Color.red())
            )
            if self.message:
                await self.message.edit(embed=embed, view=self)

        def disable_all_items(self):
            for item in self.children:
                item.disabled = True

    view = GuessingView(ctx.author, secret_number)
    embed = discord.Embed(
        title="🔮 لعبة تخمين الرقم",
        description=f"خمن رقماً بين 1 و 100!\n📉 لديك {max_attempts} محاولة.\n🏆 كلما خمنت أسرع، زادت المكافأة!",
        color=discord.Color.green()
    )
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg

# باقي دوال معالجة الأوامر...
async def handle_daily_reward(ctx):
    await ctx.send("⏳ جارٍ تنفيذ أمر المكافأة اليومية...")

async def handle_store(ctx):
    await ctx.send("🏪 عرض المتجر...")

async def handle_farming(ctx):
    await ctx.send("🌾 نظام الزراعة...")

async def handle_fishing(ctx):
    await ctx.send("🎣 نظام الصيد...")

async def handle_trading(ctx):
    await ctx.send("📈 نظام التداول...")

async def handle_investment(ctx):
    await ctx.send("💼 نظام الاستثمار...")

async def handle_theft(ctx):
    await ctx.send("🥷 نظام النهب...")

async def handle_dungeons(ctx):
    await ctx.send("🏰 نظام السراديب...")

async def handle_tasks(ctx):
    await ctx.send("🎯 نظام المهام...")

async def handle_logs(ctx):
    await ctx.send("📊 عرض السجلات...")

async def handle_help(ctx):
    if advanced_help_system:
        await advanced_help_system.show_help(ctx)
    else:
        await ctx.send("📚 نظام المساعدة غير متوفر حالياً.")

async def handle_transfer(ctx, content):
    await ctx.send("💸 أمر التحويل يحتاج إلى معاملات إضافية.")

async def handle_buy(ctx, content):
    await ctx.send("🛒 أمر الشراء يحتاج إلى معاملات إضافية.")

async def handle_sell(ctx, content):
    await ctx.send("💰 أمر البيع يحتاج إلى معاملات إضافية.")

# تشغيل البوت
if __name__ == "__main__":
    keep_alive()
    token = get_discord_token()
    bot.run(token)
