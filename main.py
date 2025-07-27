# ====== built-in modules ==-------------====
import os
import json
import random
import time
import asyncio

# ====== third-party modules ======
import discord
from discord.ext import commands, tasks
from discord.ext.commands.cooldowns import CooldownMapping, BucketType
from discord import Embed, Interaction, ButtonStyle
from discord.ui import View, Button, Select, Modal, TextInput

# ====== project modules ======
from cooldown import check_cooldown, update_cooldown, format_time, load_cooldowns, DEFAULT_COOLDOWN
from data_utils import load_data, save_data, init_user
from logs_system import logs_system, LeaderboardView, LogsView
from tasks_system import tasks_system
from keep_alive import keep_alive
from dungeons_system import *
from help_system import setup_advanced_help

# ====== إعداد المتغيرات ======
DATA_FILE = "users.json"
PRICE_FILE = "prices.json"
advanced_help_system = None

# ====== إعداد البوت ======
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="", intents=intents)
bot.remove_command("help")
setup_advanced_help(bot)

# ====== الأحداث والمهام ======

@tasks.loop(seconds=60)
async def update_farm():
    update_farm_data()

# ------------------------------------------------------------------- مكافآت الاختصاص --- فاصل--------
ranks = ["نبيل", "شجاع", "فارسي", "أسطوري"]

def get_role_level_bonus(role, rank_name):
    if rank_name not in ranks:
        return None
    index = ranks.index(rank_name)

    if role == "محارب":
        return {"type": "revenge", "percentage": [40, 60, 80, 100][index]}
    elif role == "شامان":
        return {"type": "shield", "duration": [60, 90, 120, 150][index]}
    elif role == "نينجا":
        return {"type": "steal_boost", "percentage": [20, 40, 60, 80][index]}
    elif role == "سورا":
        return {"type": "reflect", "percentage": [20, 40, 60, 80][index]}
    else:
        return None

# بيانات الاختصاصات المفصلة
SPECIALIZATIONS_INFO = {
    "محارب": {
        "emoji": "⚔️",
        "title": "المحارب الشجاع",
        "description": "محارب شرس يخوض المعارك بلا خوف ويثأر لكرامته المفقودة",
        "color": 0xe74c3c,
        "abilities": {
            "primary": "🔁 الانتقام المدمر",
            "secondary": "💪 قوة جسدية عالية",
            "passive": "🛡️ مقاومة للأضرار"
        },
        "playstyle": "هجومي - دفاعي متوازن",
        "difficulty": "⭐⭐⭐ متوسط"
    },
    "شامان": {
        "emoji": "🔮",
        "title": "الشامان الحكيم",
        "description": "ساحر قديم يتحكم في القوى الروحية ويحمي حلفاءه بقدراته السحرية",
        "color": 0x3498db,
        "abilities": {
            "primary": "🛡️ حماية مقدسة",
            "secondary": "✨ شفاء ذاتي",
            "passive": "🔮 مقاومة السحر"
        },
        "playstyle": "دعم - حماية",
        "difficulty": "⭐⭐ سهل"
    },
    "نينجا": {
        "emoji": "🥷",
        "title": "النينجا الخفي",
        "description": "قاتل في الظلام يتحرك بصمت ويضرب بسرعة البرق قبل أن يختفي",
        "color": 0x8e44ad,
        "abilities": {
            "primary": "💨 نهب خاطف",
            "secondary": "👤 تخفي مثالي",
            "passive": "⚡ سرعة فائقة"
        },
        "playstyle": "هجومي - سريع",
        "difficulty": "⭐⭐⭐⭐ صعب"
    },
    "سورا": {
        "emoji": "🧿",
        "title": "السورا الغامض",
        "description": "كائن أسطوري يملك قوى سحرية تمكنه من عكس هجمات الأعداء عليهم",
        "color": 0xf39c12,
        "abilities": {
            "primary": "🔄 عكس الضرر",
            "secondary": "🧿 درع سحري",
            "passive": "🌟 امتصاص الطاقة"
        },
        "playstyle": "دفاعي - تكتيكي",
        "difficulty": "⭐⭐⭐⭐⭐ أسطوري"
    }
}

# ------------------------------------------------------------------ فاصل --- أوامر الاختصاص -------------------------------------

role_options = ["محارب", "شامان", "نينجا", "سورا"]

async def handle_specialization_command(message):
    """معالجة أمر الاختصاص"""
    user_id = str(message.author.id)
    data = load_data()

    if user_id not in data:
        init_user(user_id, message.author.display_name)
        data = load_data()

    user = data[user_id]
    balance = user.get("balance", {})
    gold = balance.get("ذهب", 0)
    spec = user.get("specialization")

    # دالة لجلب وصف الميزة حسب النوع والرتبة
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

    # إذا لم يكن لديه اختصاص
    if not spec:
        class SpecializationSelectionView(View):
            def __init__(self):
                super().__init__(timeout=180)

                # إضافة أزرار الاختصاصات
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
                if interaction.user.id != message.author.id:
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

                # عرض القدرات في كل رتبة
                abilities_by_rank = ""
                for i, rank in enumerate(ranks):
                    bonus = get_role_level_bonus(self.role, rank)
                    if bonus:
                        desc = get_bonus_description(self.role, rank)
                        abilities_by_rank += f"**{rank}:** {desc}\n"

                embed.add_field(
                    name="📈 تطور القدرات",
                    value=abilities_by_rank,
                    inline=False
                )

                class ConfirmSpecView(View):
                    def __init__(self, selected_role):
                        super().__init__(timeout=60)
                        self.selected_role = selected_role

                    @discord.ui.button(label="✅ اختيار هذا الاختصاص", style=ButtonStyle.success)
                    async def confirm_spec(self, confirm_interaction: Interaction, button: Button):
                        if confirm_interaction.user.id != message.author.id:
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

                        success_embed.add_field(
                            name="💡 نصيحة",
                            value="استخدم الذهب لترقية رتبتك وتحسين قدراتك!",
                            inline=False
                        )

                        await confirm_interaction.response.edit_message(embed=success_embed, view=None)

                    @discord.ui.button(label="🔙 رجوع", style=ButtonStyle.secondary)
                    async def back_to_selection(self, back_interaction: Interaction, button: Button):
                        main_embed = Embed(
                            title="🎯 اختيار الاختصاص",
                            description="**اختر اختصاصك الذي سيحدد أسلوب لعبك وقدراتك الخاصة!**\n\nكل اختصاص له مميزات فريدة وأسلوب لعب مختلف. اختر بحكمة!",
                            color=0x3498db
                        )

                        await back_interaction.response.edit_message(embed=main_embed, view=SpecializationSelectionView())

                await interaction.response.edit_message(embed=embed, view=ConfirmSpecView(self.role))

        main_embed = Embed(
            title="🎯 اختيار الاختصاص",
            description="**اختر اختصاصك الذي سيحدد أسلوب لعبك وقدراتك الخاصة!**\n\nكل اختصاص له مميزات فريدة وأسلوب لعب مختلف. اختر بحكمة!",
            color=0x3498db
        )

        await message.channel.send(embed=main_embed, view=SpecializationSelectionView())
        return

    # إذا كان لديه اختصاص
    class ExistingSpecView(View):
        def __init__(self):
            super().__init__(timeout=120)

            current_rank = spec.get("rank", 1)
            upgrade_cost = spec.get("upgrade_cost", 100)

        @discord.ui.button(label="📊 عرض التفاصيل", style=ButtonStyle.primary)
        async def show_details(self, interaction: Interaction, button: Button):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("🚫 ليس لك صلاحية!", ephemeral=True)
                return

            info = SPECIALIZATIONS_INFO[spec['type']]
            current_rank = spec.get("rank", 1)
            current_rank_name = ranks[current_rank - 1]

            embed = Embed(
                title=f"{info['emoji']} {info['title']} - رتبة {current_rank_name}",
                description=info['description'],
                color=info['color']
            )

            # القدرة الحالية
            current_desc = get_bonus_description(spec['type'], current_rank_name)
            embed.add_field(
                name="🔹 قدرتك الحالية",
                value=current_desc,
                inline=False
            )

            # التقدم في الرتب
            rank_progress = ""
            for i, rank in enumerate(ranks):
                if i < current_rank:
                    rank_progress += f"✅ **{rank}**\n"
                elif i == current_rank:
                    rank_progress += f"🔸 **{rank}** ← أنت هنا\n"
                else:
                    rank_progress += f"🔒 **{rank}**\n"

            embed.add_field(
                name="📈 تقدم الرتب",
                value=rank_progress,
                inline=True
            )

            # الإحصائيات
            stats_text = f"🏆 الرتبة: **{current_rank_name}**\n💰 رصيد الذهب: **{gold:,}**"
            if current_rank < len(ranks):
                next_cost = spec.get('upgrade_cost', 100)
                stats_text += f"\n⬆️ تكلفة الترقية: **{next_cost}** ذهب"

            embed.add_field(
                name="📊 الإحصائيات",
                value=stats_text,
                inline=True
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

        @discord.ui.button(label="⬆️ ترقية الرتبة", style=ButtonStyle.success)
        async def upgrade_rank(self, interaction: Interaction, button: Button):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("🚫 ليس لك صلاحية!", ephemeral=True)
                return

            current_rank = spec.get("rank", 1)
            upgrade_cost = spec.get("upgrade_cost", 100)

            if current_rank >= len(ranks):
                await interaction.response.send_message("👑 لقد وصلت لأعلى رتبة ممكنة!", ephemeral=True)
                return

            if gold < upgrade_cost:
                await interaction.response.send_message(
                    f"❌ تحتاج إلى **{upgrade_cost:,}** ذهب للترقية\n💰 رصيدك الحالي: **{gold:,}** ذهب",
                    ephemeral=True
                )
                return

            # تنفيذ الترقية
            user["balance"]["ذهب"] -= upgrade_cost
            spec["rank"] = current_rank + 1
            new_rank_name = ranks[spec["rank"] - 1]
            spec["upgrade_cost"] = upgrade_cost + (50 * current_rank)
            save_data(data)

            # رسالة النجاح
            success_embed = Embed(
                title="🎉 تمت الترقية بنجاح!",
                description=f"تم ترقيتك إلى رتبة **{new_rank_name}**!",
                color=0x2ecc71
            )

            new_desc = get_bonus_description(spec['type'], new_rank_name)
            embed.add_field(
                name="🔹 قدرتك الجديدة",
                value=new_desc,
                inline=False
            )

            if spec["rank"] < len(ranks):
                success_embed.add_field(
                    name="💰 تكلفة الترقية القادمة",
                    value=f"{spec['upgrade_cost']:,} ذهب",
                    inline=True
                )

            success_embed.add_field(
                name="💰 رصيدك الجديد",
                value=f"{user['balance']['ذهب']:,} ذهب",
                inline=True
            )

            await interaction.response.edit_message(embed=success_embed, view=None)

        @discord.ui.button(label="🔄 تغيير الاختصاص", style=ButtonStyle.danger)
        async def change_spec(self, interaction: Interaction, button: Button):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("🚫 ليس لك صلاحية!", ephemeral=True)
                return

            change_cost = 50
            if gold < change_cost:
                await interaction.response.send_message(
                    f"❌ تحتاج إلى **{change_cost}** ذهب لتغيير الاختصاص\n💰 رصيدك الحالي: **{gold}** ذهب",
                    ephemeral=True
                )
                return

            class ConfirmChangeView(View):
                def __init__(self):
                    super().__init__(timeout=30)

                @discord.ui.button(label="✅ تأكيد التغيير", style=ButtonStyle.danger)
                async def confirm_change(self, confirm_interaction: Interaction, button: Button):
                    user["balance"]["ذهب"] -= change_cost
                    user.pop("specialization", None)
                    save_data(data)

                    await confirm_interaction.response.edit_message(
                        content=f"✅ تم خصم **{change_cost}** ذهب وحذف اختصاصك\n🔄 استخدم الأمر مرة أخرى لاختيار اختصاص جديد",
                        view=None
                    )

                @discord.ui.button(label="❌ إلغاء", style=ButtonStyle.secondary)
                async def cancel_change(self, cancel_interaction: Interaction, button: Button):
                    await cancel_interaction.response.edit_message(content="❌ تم إلغاء تغيير الاختصاص", view=None)

            warning_embed = Embed(
                title="⚠️ تأكيد تغيير الاختصاص",
                description=f"هل أنت متأكد من تغيير اختصاصك؟\n\n**سيتم:**\n• خصم **{change_cost}** ذهب\n• حذف اختصاصك الحالي\n• العودة للمستوى الأول في الاختصاص الجديد",
                color=0xe74c3c
            )

            await interaction.response.send_message(embed=warning_embed, view=ConfirmChangeView(), ephemeral=True)

    # عرض معلومات الاختصاص الحالي
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

    main_embed.add_field(
        name="💰 رصيد الذهب",
        value=f"{gold:,} ذهب",
        inline=True
    )

    if current_rank < len(ranks):
        upgrade_cost = spec.get('upgrade_cost', 100)
        main_embed.add_field(
            name="⬆️ تكلفة الترقية",
            value=f"{upgrade_cost:,} ذهب",
            inline=True
        )

    await message.channel.send(embed=main_embed, view=ExistingSpecView())

# ----------------------------------------------------------------------- فاصل --- أمر النهب -----------
from datetime import datetime, timedelta
import time

def calculate_ninja_steal(role, rank, target_balance):
    if role != "نينجا":
        return 0
    bonus = get_role_level_bonus(role, rank)
    return int((bonus["percentage"] / 100) * target_balance)

def reflect_theft(attacker_data, defender_data):
    defender_specialization = defender_data.get("specialization", {})
    defender_role = defender_specialization.get("type", "")
    defender_rank = defender_specialization.get("rank", 1)

    if defender_role != "سورا":
        return False

    bonus = get_role_level_bonus(defender_role, defender_rank)
    if not bonus or bonus.get("type") != "reflect_steal":
        return False

    reflection_percent = bonus.get("percentage", 0)

    stolen_amount = attacker_data.get("last_steal", 0)
    reflected_amount = int(stolen_amount * (reflection_percent / 100))

    attacker_data["balance"]["دولار"] = max(0, attacker_data["balance"].get("دولار", 0) - reflected_amount)
    defender_data["balance"]["دولار"] = defender_data["balance"].get("دولار", 0) + reflected_amount

    for currency in ["ذهب", "ماس"]:
        stolen_resource = attacker_data.get("balance", {}).get(currency, 0)
        reflected_resource = int(stolen_resource * (reflection_percent / 100))

        attacker_data["balance"][currency] = max(0, attacker_data["balance"].get(currency, 0) - reflected_resource)
        defender_data["balance"][currency] = defender_data["balance"].get(currency, 0) + reflected_resource

    return True

def activate_sora_shield(user_data, role):
    if role != "سورا":
        return False

    protection_until = datetime.utcnow() + timedelta(minutes=60)
    user_data["sora_shield_until"] = protection_until.isoformat()
    return True

def is_sora_shield_active(user_data):
    shield_until = user_data.get("sora_shield_until")
    if not shield_until:
        return False
    try:
        shield_end_time = datetime.fromisoformat(shield_until)
        return datetime.utcnow() < shield_end_time
    except Exception:
        user_data.pop("sora_shield_until", None)
        return False

async def handle_shield_command(message):
    """معالجة أمر درع"""
    user_id = str(message.author.id)
    init_user(user_id, message.author.display_name)
    data = load_data()
    user = data[user_id]

    if user.get("specialization", {}).get("type", "") == "سورا":
        protection_until = datetime.utcnow() + timedelta(minutes=60)
        user["sora_shield_until"] = protection_until.isoformat()
        save_data(data)
        await message.channel.send("✅ تم تفعيل درع سورا لمدة ساعة واحدة.")
    else:
        await message.channel.send("❌ فقط سورا يمكنه تفعيل الدرع.")
        return

    # ⛨ تفعيل الدرع
    protection_until = datetime.utcnow() + timedelta(minutes=60)
    user["sora_shield_until"] = protection_until.isoformat()

    # 🔄 حفظ وتحديث التبريد
    save_data(data)
    update_cooldown(user_id, "درع")

    await message.channel.send("✅ تم تفعيل درع سورا لمدة ساعة واحدة.")

async def handle_steal_command(message, args):
    """معالجة أمر نهب"""
    if len(args) < 2:
        await message.channel.send("❌ استخدم: نهب @المستخدم")
        return

    try:
        target_mention = args[1].strip('<@!>')
        target = message.guild.get_member(int(target_mention))
    except:
        await message.channel.send("❌ لم يتم العثور على المستخدم المحدد.")
        return

    # فحص التبريد
    can_steal, cooldown_msg = check_cooldown(message.author.id, "نهب")
    if not can_steal:
        await message.channel.send(f"⏳ يجب الانتظار قبل المحاولة مرة أخرى: {cooldown_msg}")
        return

    user_id = str(message.author.id)
    target_id = str(target.id)

    if target_id == user_id:
        await message.channel.send("❌ لا يمكنك نهب نفسك.")
        return

    init_user(user_id, message.author.display_name)
    init_user(target_id, target.display_name)
    data = load_data()

    user = data[user_id]
    victim = data[target_id]

    user_role = user.get("role", "")
    user_rank = user.get("rank", "نبيل")
    victim_role = victim.get("role", "")
    victim_rank = victim.get("rank", "نبيل")

    user.setdefault("balance", {}).setdefault("دولار", 0)
    victim.setdefault("balance", {}).setdefault("دولار", 0)

    victim_specialization = victim.get("specialization", {}) or {}
    is_sora = victim_specialization.get("type", "") == "سورا"
    shield_active = is_sora and is_sora_shield_active(victim)

    # حماية الشامان
    protection_end = victim.get("shield_until", 0)
    now_ts = time.time()
    if now_ts < protection_end:
        remaining = int(protection_end - now_ts)
        minutes = remaining // 60
        seconds = remaining % 60
        await message.channel.send(f"🛡️ {target.name} تحت حماية الشامان لمدة {minutes} دقيقة و{seconds} ثانية أخرى.")
        return

    victim_balance = victim["balance"]["دولار"]
    if victim_balance < 50:
        await message.channel.send(f"❌ {target.name} لا يملك ما يكفي ليتم نهبه.")
        return

    base_steal = int(victim_balance * 0.1)
    steal_amount = base_steal

    if user_role == "نينجا":
        steal_amount = calculate_ninja_steal(user_role, user_rank, victim_balance)

    user["last_steal"] = steal_amount

    # إذا درع سورا مفعل
    if shield_active:
        bonus = get_role_level_bonus("سورا", victim_specialization.get("rank", 1))
        reflection_percent = bonus.get("percentage", 20) if bonus else 20
        amount_reflected = int(steal_amount * (reflection_percent / 100))
        amount_reflected = min(amount_reflected, user["balance"]["دولار"])

        user["balance"]["دولار"] = max(0, user["balance"]["دولار"] - amount_reflected)
        victim["balance"]["دولار"] += amount_reflected

        save_data(data)
        update_cooldown(message.author.id, "نهب")
        await message.channel.send(f"❌ درع سورا مفعل! تم عكس {amount_reflected}$ من محاولتك وتمت إضافتها إلى {target.name}.")
        return

    # عكس السرقة التقليدي إن لم يكن درع مفعل
    if is_sora:
        reversed_success = reflect_theft(user, victim)
        if reversed_success:
            save_data(data)
            update_cooldown(message.author.id, "نهب")
            await message.channel.send(f"❌ فشلت محاولتك! تم عكس السرقة ⚡ وتم خصم المبلغ منك وتحويله إلى {target.name}.")
            return

    # السرقة العادية
    steal_amount = min(steal_amount, victim_balance)
    user["balance"]["دولار"] += steal_amount
    victim["balance"]["دولار"] -= steal_amount

    # التحقق من اختصاص الضحية لحفظ سجل الانتقام
    victim_specialization = victim.get("specialization", {})
    if isinstance(victim_specialization, dict):
        victim_role = victim_specialization.get("type", "")
    else:
        victim_role = ""

    if victim_role == "محارب":
        revenge_log = victim.setdefault("revenge_log", [])
        revenge_log = [entry for entry in revenge_log if entry["thief_id"] != user_id]
        revenge_log.append({
            "thief_id": user_id,
            "amount": steal_amount,
            "time": time.time()
        })
        victim["revenge_log"] = revenge_log

    # تسجيل النشاط
    logs_system.add_log(
        "theft_logs",
        user_id,
        message.author.display_name,
        f"نهب {target.name}",
        {"amount": steal_amount, "target": target.name, "victim_id": target_id}
    )

    update_cooldown(message.author.id, "نهب")
    save_data(data)
    await message.channel.send(f"💰 لقد نهبت {target.name} وسرقت {steal_amount}$ بنجاح!")

async def handle_protect_command(message, args):
    """معالجة أمر الحماية"""
    user_id = str(message.author.id)
    data = load_data()
    init_user(user_id, message.author.display_name)
    user = data[user_id]

    if user.get("role") != "شامان":
        await message.channel.send("🛡️ فقط الشامان يستطيع استخدام أمر الحماية.")
        return

    member = None
    if len(args) > 1:
        try:
            target_mention = args[1].strip('<@!>')
            member = message.guild.get_member(int(target_mention))
        except:
            pass

    rank = user.get("rank", "نبيل")
    role_bonus = get_role_level_bonus("شامان", rank)
    duration = role_bonus["duration"]
    now = time.time()

    # تحديد من سيتم حمايته
    if rank == "أسطوري" and member:
        target_id = str(member.id)
    elif member:
        await message.channel.send("❌ لا يمكنك حماية لاعب آخر إلا إذا كنت في رتبة أسطوري.")
        return
    else:
        target_id = user_id

    target = data.get(target_id)
    if not target:
        await message.channel.send("🚫 اللاعب غير موجود في البيانات.")
        return

    if target.get("shield_until", 0) > now:
        await message.channel.send(f"🛡️ {member.mention if member else 'أنت'} محمي بالفعل.")
        return

    # تفعيل الحماية
    target["shield_until"] = now + duration
    target["shield_target"] = target_id

    if target_id == user_id:
        await message.channel.send(f"🛡️ تم تفعيل الحماية لك لمدة `{duration // 60}` دقيقة.")
    else:
        await message.channel.send(f"🛡️ تم تفعيل الحماية لـ {member.mention} لمدة `{duration // 60}` دقيقة.")
    user["shield_until"] = time.time() + duration
    save_data(data)

async def handle_revenge_command(message, args):
    """معالجة أمر الانتقام"""
    if len(args) < 2:
        await message.channel.send("❗ الرجاء تحديد الشخص الذي تريد الانتقام منه.\nمثال: `انتقام @اسم_العضو`")
        return

    try:
        target_mention = args[1].strip('<@!>')
        target = message.guild.get_member(int(target_mention))
    except:
        await message.channel.send("❌ لم يتم العثور على المستخدم المحدد.")
        return

    user_id = str(message.author.id)
    target_id = str(target.id)

    if target_id == user_id:
        await message.channel.send("❌ لا يمكنك الانتقام من نفسك.")
        return

    init_user(user_id, message.author.display_name)
    init_user(target_id, target.display_name)
    data = load_data()

    user = data[user_id]
    target_user = data[target_id]

    # التحقق من الاختصاص
    specialization = user.get("specialization", {})
    if isinstance(specialization, dict):
        role = specialization.get("type", "")
        rank_level = specialization.get("rank", 1)
        if rank_level <= len(ranks):
            rank = ranks[rank_level - 1]
        else:
            rank = "نبيل"
    else:
        role = ""
        rank = "نبيل"

    if role != "محارب":
        await message.channel.send("❌ فقط المحارب يمكنه الانتقام.")
        return

    user.setdefault("revenge_log", [])
    revenge_log = user["revenge_log"]

    revenge_entry = next((entry for entry in revenge_log if entry["thief_id"] == target_id), None)
    if not revenge_entry:
        await message.channel.send(f"⚔️ لا يوجد سجل نهب من {target.name} لتنتقم منه.")
        return

    # مدة الصلاحية: 24 ساعة
    if time.time() - revenge_entry["time"] > 86400:
        user["revenge_log"] = [entry for entry in revenge_log if entry["thief_id"] != target_id]
        await message.channel.send(f"⌛ انتهت صلاحية الانتقام من {target.name}.")
        save_data(data)
        return

    # تحديد نسبة الانتقام حسب الرتبة
    bonus = get_role_level_bonus(role, rank)
    if bonus and bonus.get("type") == "revenge":
        revenge_percentage = bonus.get("percentage", 40)
    else:
        revenge_percentage = 40  # النسبة الافتراضية للمحارب

    revenge_amount = int(revenge_entry["amount"] * revenge_percentage / 100)
    revenge_amount = min(revenge_amount, target_user["balance"]["دولار"])

    if revenge_amount <= 0:
        await message.channel.send(f"💸 {target.name} لا يملك ما يمكن انتزاعه.")
        return

    user["balance"]["دولار"] += revenge_amount
    target_user["balance"]["دولار"] -= revenge_amount

    # حذف السجل بعد الانتقام
    user["revenge_log"] = [entry for entry in revenge_log if entry["thief_id"] != target_id]

    # تسجيل النشاط
    logs_system.add_log(
        "revenge_logs",
        user_id,
        message.author.display_name,
        f"انتقم من {target.name}",
        {"amount": revenge_amount, "target": target.name, "victim_id": target_id}
    )

    await message.channel.send(
        f"⚔️ انتقمت من {target.name} واستعدت {revenge_amount}$ من أموالك! (نسبة الانتقام: {revenge_percentage}%)"
    )
    save_data(data)

#------------------------------------------------------------------- فاصل----- نظام الأسعار المتغيرة --------------------------

store_items = [
    # 🔹 شائعة
    {"name": "🗡️ سيف سام", "price": 10_000, "fluctuation": 0.2},
    {"name": "🧪 جرعة الحكمة", "price": 25_000, "fluctuation": 0.2},

    # 🔸 غير شائعة
    {"name": "🪓 منجل", "price": 100_000, "fluctuation": 0.3},
    {"name": "🧪 كيميائي أحمر", "price": 60_000, "fluctuation": 0.3},
    {"name": "🧣 وشاح الحكام", "price": 250_000, "fluctuation": 0.3},

    # 🔶 نادرة
    {"name": "🛡️ درع التنين المصفح", "price": 500_000, "fluctuation": 0.4},
    {"name": "🛡️ ترس العمالقة", "price": 750_000, "fluctuation": 0.4},
    {"name": "🎽 زي المحارب", "price": 350_000, "fluctuation": 0.4},
    {"name": "🧤 قفازات المهارة", "price": 300_000, "fluctuation": 0.4},
    {"name": "💍 خاتم الزواج", "price": 400_000, "fluctuation": 0.4},

    # 🔱 أسطورية
    {"name": "🐉 دابة التنين", "price": 5_000_000, "fluctuation": 0.6},
    {"name": "👑 تاج الهيمنة", "price": 10_000_000, "fluctuation": 0.6}
]

PRICES = {item["name"]: item["price"] for item in store_items}
PRICE_FILE = "prices.json"
PRICE_STATE_FILE = "price_state.json"
PRICE_DURATION = 6 * 60  # 6 دقائق بالثواني

# تحميل/حفظ الأسعار
def load_prices():
    if not os.path.exists(PRICE_FILE):
        with open(PRICE_FILE, "w") as f:
            json.dump(PRICES, f, indent=4, ensure_ascii=False)
    with open(PRICE_FILE, "r") as f:
        return json.load(f)

def save_prices(prices):
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f, indent=4, ensure_ascii=False)

# توليد تقلب في السعر
def to_multiple_of_5(value):
    return 5 * round(value / 5)

def fluctuate_price(base_price, fluctuation_rate):
    delta = random.uniform(-fluctuation_rate, fluctuation_rate)
    new_price = max(1, int(base_price * (1 + delta)))
    return to_multiple_of_5(new_price)

def get_price_indicator(old, new):
    change = new - old
    if change > 0:
        if change / old > 0.2:
            return "🚀✨"  # ارتفاع كبير
        else:
            return "🤑🔺"   # ارتفاع طفيف
    elif change < 0:
        if abs(change) / old > 0.2:
            return "🧠🔻💥"  # انخفاض كبير
        else:
            return "💰🔻"   # انخفاض طفيف
    else:
        return "🟰🧘"       # ثابت

# تحديث الأسعار إذا لزم الأمر
def update_prices_if_needed():
    if not os.path.exists(PRICE_STATE_FILE):
        return regenerate_prices()

    with open(PRICE_STATE_FILE, "r") as f:
        data = json.load(f)

    last_update = data.get("last_update", 0)
    now = time.time()

    if now - last_update >= PRICE_DURATION:
        return regenerate_prices()

    return data.get("prices", PRICES)

def regenerate_prices():
    prices = {}
    for item in store_items:
        base_price = item["price"]
        fluctuated = fluctuate_price(base_price, item.get("fluctuation", 0.2))
        prices[item["name"]] = fluctuated

    data = {"last_update": time.time(), "prices": prices}
    with open(PRICE_STATE_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return prices

# ---------------------------------------------------------فاصل----------------- المتجر --------------------------
async def handle_shop_command(message):
    """معالجة أمر المتجر"""
    prices = update_prices_if_needed()
    user_id = str(message.author.id)
    init_user(user_id, message.author.display_name)
    data = load_data()
    user_balance = data[user_id]["balance"]["دولار"]
    user_bag = data[user_id].get("حقيبة", [])

    if os.path.exists(PRICE_STATE_FILE):
        with open(PRICE_STATE_FILE, "r") as f:
            data_file = json.load(f)
        remaining = PRICE_DURATION - (time.time() - data_file.get("last_update", 0))
        minutes = int(max(0, remaining // 60))
        seconds = int(max(0, remaining % 60))
        footer_text = f"⏳ تحديث الأسعار خلال {minutes} دقيقة و {seconds} ثانية."
    else:
        footer_text = "⏳ الأسعار تم تحديثها للتو."

    embed = Embed(
        title="🏪 المتجر الديناميكي العالمي",
        description=(
            "🌟 **مرحباً بك في السوق العالمي!**\n\n"
            "📈 الأسعار تتغير كل **6 دقائق** حسب العرض والطلب\n"
            "🛒 اضغط على أي عنصر لاختيار شراء أو بيع مباشرة!\n"
            "💡 **نصيحة:** راقب المؤشرات لتحصل على أفضل الصفقات!"
        ),
        color=0x2c3e50
    )
    embed.add_field(
        name="💰 رصيدك الحالي",
        value=f"{user_balance:,} دولار",
        inline=True
    )
    embed.set_footer(text=footer_text)

    class ShopView(View):
        def __init__(self):
            super().__init__(timeout=120)
            for item in store_items:
                name = item["name"]
                base_price = item["price"]
                current_price = prices.get(name, base_price)
                indicator = get_price_indicator(base_price, current_price)
                button = self.make_button(item, current_price, indicator)
                if button:
                    self.add_item(button)

        def make_button(self, item, current_price, indicator):
            emoji = item["name"][0]
            item_name = item["name"][2:].strip()
            base_price = item["price"]

            diff = current_price - base_price
            percentage = diff / base_price

            # تحديد لون الزر حسب الفرق في السعر
            if percentage < -0.1:
                style = ButtonStyle.danger  # 🔴 انخفض السعر كثيرًا
            elif -0.1 <= percentage <= 0.1:
                style = ButtonStyle.secondary  # ⚪ قريب من المتوسط
            elif percentage > 0.2:
                style = ButtonStyle.success  # 🟢 مرتفع كثيرًا
            else:
                style = ButtonStyle.primary  # 🔵 عادي

            button = Button(
                label=f"{item_name} – {current_price:,}$ {indicator}",
                emoji=emoji,
                style=style
            )

            async def callback(interaction: Interaction):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("❌ هذا المتجر ليس لك!", ephemeral=True)
                    return

                # فحص ما إذا كان المستخدم يملك هذا العنصر
                item_count = user_bag.count(item["name"])

                view = QuickActionView(item["name"], current_price, item_count)
                embed_item = Embed(
                    title=f"🛒 {item['name']}",
                    description=f"💰 السعر الحالي: **{current_price:,}$**\n📦 تملك: **{item_count}** قطعة",
                    color=0x3498db
                )
                await interaction.response.send_message(embed=embed_item, view=view, ephemeral=True)

            button.callback = callback
            return button

    class QuickActionView(View):
        def __init__(self, item_name, item_price, owned_count):
            super().__init__(timeout=60)
            self.item_name = item_name
            self.item_price = item_price
            self.owned_count = owned_count

        @discord.ui.button(label="🛒 شراء", style=ButtonStyle.success, emoji="💵")
        async def buy_action(self, interaction: Interaction, button: Button):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            # حساب الكميات الممكنة للشراء
            max_affordable = user_balance // self.item_price

            if max_affordable == 0:
                await interaction.response.send_message(
                    f"❌ لا يمكنك شراء {self.item_name}!\n💰 تحتاج: {self.item_price:,}$ | لديك: {user_balance:,}$",
                    ephemeral=True
                )
                return

            view = BuyQuantityView(self.item_name, self.item_price, max_affordable)
            embed = Embed(
                title=f"🛒 شراء {self.item_name}",
                description=f"💰 السعر: **{self.item_price:,}$** للقطعة\n💳 رصيدك: **{user_balance:,}$**\n🛒 الحد الأقصى: **{max_affordable:,}** قطعة",
                color=0x2ecc71
            )
            await interaction.response.edit_message(embed=embed, view=view)

        @discord.ui.button(label="💰 بيع", style=ButtonStyle.danger, emoji="🔻")
        async def sell_action(self, interaction: Interaction, button: Button):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            if self.owned_count == 0:
                await interaction.response.send_message(
                    f"❌ لا تملك أي {self.item_name} للبيع!",
                    ephemeral=True
                )
                return

            view = SellQuantityView(self.item_name, self.item_price, self.owned_count)
            embed = Embed(
                title=f"💰 بيع {self.item_name}",
                description=f"💰 سعر البيع: **{self.item_price:,}$** للقطعة\n📦 تملك: **{self.owned_count}** قطعة\n💎 القيمة الإجمالية: **{self.item_price * self.owned_count:,}$**",
                color=0xe67e22
            )
            await interaction.response.edit_message(embed=embed, view=view)

    class BuyQuantityView(View):
        def __init__(self, item_name, item_price, max_quantity):
            super().__init__(timeout=60)
            self.item_name = item_name
            self.item_price = item_price
            self.max_quantity = max_quantity

        @discord.ui.button(label="1️⃣ قطعة واحدة", style=ButtonStyle.secondary)
        async def buy_one(self, interaction: Interaction, button: Button):
            await self.process_buy(interaction, 1)

        @discord.ui.button(label="🔟 عشرة", style=ButtonStyle.primary)
        async def buy_ten(self, interaction: Interaction, button: Button):
            quantity = min(10, self.max_quantity)
            await self.process_buy(interaction, quantity)

        @discord.ui.button(label="💯 مئة", style=ButtonStyle.primary)
        async def buy_hundred(self, interaction: Interaction, button: Button):
            quantity = min(100, self.max_quantity)
            await self.process_buy(interaction, quantity)

        @discord.ui.button(label="🔄 نصف ما أستطيع", style=ButtonStyle.success)
        async def buy_half_max(self, interaction: Interaction, button: Button):
            quantity = max(1, self.max_quantity // 2)
            await self.process_buy(interaction, quantity)

        @discord.ui.button(label="💸 الحد الأقصى", style=ButtonStyle.danger)
        async def buy_max(self, interaction: Interaction, button: Button):
            await self.process_buy(interaction, self.max_quantity)

        async def process_buy(self, interaction: Interaction, quantity):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            total_cost = self.item_price * quantity

            # تحديث البيانات
            data = load_data()
            user = data[user_id]

            if user["balance"]["دولار"] < total_cost:
                await interaction.response.send_message(
                    f"❌ لا تملك ما يكفي من المال!\nتحتاج: {total_cost:,}$ | لديك: {user['balance']['دولار']:,}$",
                    ephemeral=True
                )
                return

            # تنفيذ الشراء
            user["balance"]["دولار"] -= total_cost
            for _ in range(quantity):
                user.setdefault("حقيبة", []).append(self.item_name)
            save_data(data)

            # تحديث مهام الشراء
            completed_tasks = tasks_system.update_task_progress(user_id, "buy_items", quantity)

            embed = Embed(
                title="✅ تمت عملية الشراء بنجاح!",
                description=f"🎉 اشتريت **{quantity:,}** من {self.item_name}",
                color=0x00ff00
            )
            embed.add_field(name="💰 المبلغ المدفوع", value=f"{total_cost:,}$", inline=True)
            embed.add_field(name="💳 رصيدك الجديد", value=f"{user['balance']['دولار']:,}$", inline=True)

            if completed_tasks:
                embed.add_field(name="🎯 مهام مكتملة!", value=f"✅ أكملت {len(completed_tasks)} مهمة!", inline=False)

            await interaction.response.edit_message(embed=embed, view=None)

    class SellQuantityView(View):
        def __init__(self, item_name, item_price, owned_quantity):
            super().__init__(timeout=60)
            self.item_name = item_name
            self.item_price = item_price
            self.owned_quantity = owned_quantity

        @discord.ui.button(label="1️⃣ قطعة واحدة", style=ButtonStyle.secondary)
        async def sell_one(self, interaction: Interaction, button: Button):
            await self.process_sell(interaction, 1)

        @discord.ui.button(label="🔟 عشرة", style=ButtonStyle.primary)
        async def sell_ten(self, interaction: Interaction, button: Button):
            quantity = min(10, self.owned_quantity)
            await self.process_sell(interaction, quantity)

        @discord.ui.button(label="💯 مئة", style=ButtonStyle.primary)
        async def sell_hundred(self, interaction: Interaction, button: Button):
            quantity = min(100, self.owned_quantity)
            await self.process_sell(interaction, quantity)

        @discord.ui.button(label="🔄 نصف ما أملك", style=ButtonStyle.success)
        async def sell_half(self, interaction: Interaction, button: Button):
            quantity = max(1, self.owned_quantity // 2)
            await self.process_sell(interaction, quantity)

        @discord.ui.button(label="💸 بيع الكل", style=ButtonStyle.danger)
        async def sell_all(self, interaction: Interaction, button: Button):
            await self.process_sell(interaction, self.owned_quantity)

        async def process_sell(self, interaction: Interaction, quantity):
            if interaction.user.id != message.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            total_earning = self.item_price * quantity

            # تحديث البيانات
            data = load_data()
            user = data[user_id]
            bag = user.get("حقيبة", [])

            # التأكد من وجود العناصر
            available_count = bag.count(self.item_name)
            if available_count < quantity:
                await interaction.response.send_message(
                    f"❌ لا تملك {quantity} من {self.item_name}!\nلديك فقط: {available_count}",
                    ephemeral=True
                )
                return

            # تنفيذ البيع
            for _ in range(quantity):
                bag.remove(self.item_name)
            user["balance"]["دولار"] += total_earning
            save_data(data)

            embed = Embed(
                title="✅ تمت عملية البيع بنجاح!",
                description=f"💰 بعت **{quantity:,}** من {self.item_name}",
                color=0x00ff00
            )
            embed.add_field(name="💰 المبلغ المحصل", value=f"{total_earning:,}$", inline=True)
            embed.add_field(name="💳 رصيدك الجديد", value=f"{user['balance']['دولار']:,}$", inline=True)
            embed.add_field(name="📦 المتبقي", value=f"{bag.count(self.item_name)} قطعة", inline=True)

            await interaction.response.edit_message(embed=embed, view=None)

    await message.channel.send(embed=embed, view=ShopView())

# =========== باقي الدوال والأوامر ============

# حساب ثروة اللاعب
def calculate_wealth(user_data):
    if not isinstance(user_data, dict):
        return 0

    balance = user_data.get("balance", {})
    if isinstance(balance, int):
        balance = {
            "دولار": balance,
            "ذهب": 0,
            "ماس": 0
        }

    if not isinstance(balance, dict):
        return 0

    dollars = balance.get("دولار", 0)
    gold = balance.get("ذهب", 0)
    diamonds = balance.get("ماس", 0)

    return dollars + (gold * 50) + (diamonds * 100)

# دوال معالجة الأوامر
async def handle_greeting_command(message):
    """معالجة أمر السلام"""
    await message.channel.send("وعليكم السلام   👑")

async def handle_balance_command(message):
    """معالجة أمر الرصيد"""
    user_id = str(message.author.id)
    data = load_data()

    if user_id not in data:
        await message.channel.send("❌ يجب عليك أولاً استخدام أمر `بدء` لإنشاء حساب.")
        return

    user = data[user_id]
    balance = user.get("balance", {})
    dollar = balance.get("دولار", 0)
    gold = balance.get("ذهب", 0)
    diamond = balance.get("ماس", 0)

    # حساب إجمالي الثروة
    total_wealth = dollar + (gold * 50) + (diamond * 100)

    # تحديد لون الثروة
    if total_wealth >= 10000000:
        color = 0x9b59b6  # بنفسجي للأثرياء جداً
        wealth_title = "🌟 إمبراطور الثروة"
    elif total_wealth >= 5000000:
        color = 0xf39c12  # ذهبي للأثرياء
        wealth_title = "👑 ملك الثروة"
    elif total_wealth >= 1000000:
        color = 0xe67e22  # برتقالي للمتوسطين
        wealth_title = "🥇 تاجر ثري"
    elif total_wealth >= 100000:
        color = 0x3498db  # أزرق للمبتدئين
        wealth_title = "🥈 تاجر متوسط"
    else:
        color = 0x95a5a6  # رمادي للفقراء
        wealth_title = "🥉 تاجر مبتدئ"

    embed = discord.Embed(
        title=f"💰 محفظة {message.author.display_name}",
        description=f"**{wealth_title}**\n💎 إجمالي الثروة: **{total_wealth:,}** نقطة",
        color=color
    )

    embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)

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

    # معلومات إضافية عن المستوى
    level_info = tasks_system.get_user_level_info(user_id)
    embed.add_field(
        name="🏆 المستوى والخبرة",
        value=f"📈 المستوى: **{level_info['level']}**\n⭐ الخبرة: **{level_info['experience']:,}**",
        inline=True
    )

    embed.set_footer(text="💡 استخدم الأوامر المختلفة لزيادة ثروتك ومستواك!")

    await message.channel.send(embed=embed)

async def handle_job_command(message):
    """معالجة أمر مهنتي"""
    user_id = str(message.author.id)
    init_user(user_id, message.author.display_name)
    data = load_data()
    job = data[user_id].get("المهنة", "مواطن")
    await message.channel.send(f"👷 وظيفتك الحالية: **{job}**")

async def handle_wealth_command(message):
    """معالجة أمر الثروة"""
    user_id = str(message.author.id)
    data = load_data()

    if user_id not in data:
        await message.channel.send("❌ لم يتم العثور على بيانات المستخدم.")
        return

    wealth_message = "👑 قائمة أصحاب الثروات\n🏆 أغنى 10 أشخاص في النظام الاقتصادي\n\n"

    # حساب ثروات جميع المستخدمين
    all_wealth = {uid: calculate_wealth(info) for uid, info in data.items()}
    sorted_wealth = sorted(all_wealth.items(), key=lambda x: x[1], reverse=True)

    for idx, (uid, total_wealth) in enumerate(sorted_wealth[:10]):
        uid_str = str(uid)
        user_data = data.get(uid_str, {})

        # 🧠 جلب الاسم من البيانات أو من ديسكورد
        name = user_data.get("username", f"مستخدم {uid_str[:8]}")
        if name in ["مستخدم مجهول", f"مستخدم {uid_str[:8]}"]:
            try:
                user = await bot.fetch_user(int(uid_str))
                if user:
                    name = user.display_name
                else:
                    member = message.guild.get_member(int(uid_str))
                    name = member.display_name if member else f"مستخدم {uid_str[:8]}"
            except:
                name = f"مستخدم {uid_str[:8]}"

        balance = user_data.get("balance", {})
        if isinstance(balance, int):
            balance = {
                "دولار": balance,
                "ذهب": 0,
                "ماس": 0
            }

        # 🥇 رمز المركز
        medal = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🏅"

        # 📝 إنشاء السطر
        wealth_message += f"{medal} {name} 🏰\n"
        wealth_message += f"💰 {total_wealth} نقطة ثروة\n"
        wealth_message += f"💵 {balance.get('دولار', 0)} | 🪙 {balance.get('ذهب', 0)} | 💎 {balance.get('ماس', 0)}\n\n"

    await message.channel.send(wealth_message)

async def handle_work_command(message):
    """معالجة أمر العمل"""
    user_id = str(message.author.id)

    # تحقق من التبريد
    allowed, time_left = check_cooldown(user_id, "عمل")
    if not allowed:
        await message.channel.send(f"⏳ يمكنك العمل مرة أخرى بعد {time_left}.")
        return

    # حدّث وقت التبريد
    update_cooldown(user_id, "عمل")

    # تجهيز المستخدم والبيانات
    init_user(user_id, message.author.display_name)
    data = load_data()

    current_job = data[user_id].get("المهنة", "مواطن")

    job_ranks = {
        "مواطن": 1,
        "رسام": 2,
        "طبيب": 3,
        "مقدم": 4,
        "جنيرال": 5,
        "وزير": 6,
        "ملك": 7,
        "إمبراطور": 8
    }

    rank = job_ranks.get(current_job, 1)

    # الأرباح حسب الرتبة
    dollars = 0
    gold = 0

    if rank >= 7:
        gold = random.randint(20, 40)
    elif rank >= 4:
        gold = random.randint(10, 20)
        dollars = random.randint(40_000, 60_000)
    else:
        dollars = random.randint(60_000, 90_000)

    # تحديث الرصيد
    data[user_id]["balance"]["دولار"] += dollars
    data[user_id]["balance"]["ذهب"] += gold
    save_data(data)

    # تسجيل النشاط
    total_earned = dollars + (gold * 50)  # تحويل الذهب لقيمة نقدية للسجل
    logs_system.add_log(
        "work_logs", 
        user_id,
        message.author.display_name,
        f"عمل في وظيفة {current_job}",
        {"job": current_job, "earned": total_earned, "dollars": dollars, "gold": gold}
    )

    # تحديث مهام جمع الذهب
    msg = f"💼 مهنتك الحالية: {current_job}\n"
    msg += f"👏 عملت وربحت اليوم:\n"
    if dollars:
        msg += f"💵 {dollars}$\n"
    if gold:
        msg += f"🪙 {gold} ذهب\n"
        completed_tasks = tasks_system.update_task_progress(user_id, "collect_gold", gold)
        if completed_tasks:
            msg += f"\n🎯 أكملت {len(completed_tasks)} مهمة!"

    await message.channel.send(msg)

async def handle_upgrade_command(message):
    """معالجة أمر الترقية"""
    user_id = str(message.author.id)

    # التحقق من التبريد
    allowed, remaining = check_cooldown(user_id, "upgrade")
    if not allowed:
        await message.channel.send(f"⏳ الرجاء الانتظار {remaining} قبل استخدام الأمر مرة أخرى.")
        return

    # تحميل البيانات
    data = load_data()
    if user_id not in data:
        await message.channel.send("❌ يجب أن تبدأ باستخدام الأمر 'بدء' أولاً.")
        return

    current_job = data[user_id].get("المهنة", "مواطن")

    jobs_order = ["مواطن", "رسام", "مدرب", "مقدم", "جنيرال", "وزير", "ملك"]
    upgrade_costs = {
        "مواطن": {"ذهب": 100, "دولار": 10},
        "رسام": {"ذهب": 200, "دولار": 20},
        "مدرب": {"ذهب": 300, "دولار": 30},
        "مقدم": {"ذهب": 500, "دولار": 50},
        "جنيرال": {"ذهب": 800, "دولار": 80},
        "وزير": {"ذهب": 1200, "دولار": 120}
    }

    if current_job == "ملك":
        await message.channel.send("👑 لقد وصلت إلى أعلى رتبة!")
        return

    # تحديد الترقية التالية
    try:
        next_job_index = jobs_order.index(current_job) + 1
        next_job = jobs_order[next_job_index]
    except (ValueError, IndexError):
        await message.channel.send("❌ المهنة الحالية غير صالحة.")
        return

    # التحقق من الموارد
    cost = upgrade_costs.get(current_job)
    if not cost:
        await message.channel.send("❌ لا توجد تكلفة معرفة لهذه الترقية.")
        return

    user_gold = data[user_id]["balance"].get("ذهب", 0)
    user_dollar = data[user_id]["balance"].get("دولار", 0)

    if user_gold >= cost["ذهب"] and user_dollar >= cost["دولار"]:
        data[user_id]["balance"]["ذهب"] -= cost["ذهب"]
        data[user_id]["balance"]["دولار"] -= cost["دولار"]
        data[user_id]["المهنة"] = next_job
        save_data(data)
        update_cooldown(user_id, "upgrade")
        await message.channel.send(f"✅ تمت ترقيتك إلى **{next_job}**!")
    else:
        await message.channel.send(
            f"❌ لا تملك ما يكفي من الموارد للترقية إلى **{next_job}**.\n"
            f"🔸 تحتاج إلى: {cost['ذهب']} ذهب و {cost['دولار']} دولار."
        )

async def handle_daily_command(message):
    """معالجة أمر يومي"""
    user_id = str(message.author.id)
    cooldowns = load_cooldowns()
    current_time = int(time.time())
    user_cooldowns = cooldowns.get(user_id, {})

    # تحقق من الكولداون
    allowed, time_left = check_cooldown(user_id, "يومي")
    if not allowed:
        await message.channel.send(f"⏳ يمكنك العمل مرة أخرى بعد {time_left}.")
        return

    last_used = user_cooldowns.get("يومي", 0)
    elapsed = current_time - last_used
    time_left = DEFAULT_COOLDOWN["يومي"] - elapsed

    if time_left > 0:
        await message.channel.send(f"⏳ لا يمكنك الحصول على المكافأة الآن.\nالوقت المتبقي: {format_time(time_left)}")
        return

    # إذا وصل إلى هنا فالمكافأة متاحة
    init_user(user_id, message.author.display_name)
    data = load_data()
    data[user_id]["balance"]["دولار"] += 100_000
    data[user_id]["balance"]["ذهب"] += 10
    data[user_id]["balance"]["ماس"] += 1
    save_data(data)

    # تسجيل النشاط
    logs_system.add_log(
        "daily_logs",
        user_id,
        message.author.display_name,
        "حصل على المكافأة اليومية",
        {"dollars": 100000, "gold": 25, "diamonds": 1}
    )

    # حدّث وقت التبريد
    update_cooldown(user_id, "يومي")
    save_cooldowns(cooldowns)

    await message.channel.send("🎁 حصلت على مكافأتك اليومية:\n💵 100 ألف دولار\n🪙 25 ذهب\n💎 1 ماس")

async def handle_profile_command(message):
    """معالجة أمر حسابي"""
    user_id = str(message.author.id)

    data = load_data()
    if user_id not in data:
        init_user(user_id, message.author.display_name)
        data = load_data()

    user_data = data[user_id]

    # تنسيق الرصيد
    balance = user_data.get("balance", {})
    balance_text = (
        f"💵 {balance.get('دولار', 0):,} دولار\n"
        f"🪙 {balance.get('ذهب', 0):,} ذهب\n"
        f"💎 {balance.get('ماس', 0):,} ماس"
    )

    # تنسيق الاختصاص
    specialization = user_data.get("specialization", {})
    if isinstance(specialization, dict) and specialization:
        spec_text = f"النوع: {specialization.get('type', '❌')}\nالرتبة: {specialization.get('rank', '❌')}"
    else:
        spec_text = "❌ لا يوجد"

    # تنسيق باقي الحقول
    bag_count = len(user_data.get("bag", []))
    job = user_data.get("المهنة", "❌ لا توجد")
    skill = user_data.get("skill", "❌ لا توجد")
    farm = user_data.get("farm", "❌ لا توجد")

    # إنشاء الرسالة المضمنة
    embed = discord.Embed(
        title="📒 حسابك الشخصي",
        description=f"معلومات {message.author.mention}",
        color=0x00b0f4
    )

    embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)

    embed.add_field(name="🪙 الرصيد", value=balance_text, inline=False)
    embed.add_field(name="🎒 الحقيبة", value=f"{bag_count} عنصر", inline=True)
    embed.add_field(name="🛠️ الاختصاص", value=spec_text, inline=True)
    embed.add_field(name="👷 المهنة", value=job, inline=True)
    embed.add_field(name="🎯 المهارة", value=skill, inline=True)
    embed.add_field(name="🌾 المزرعة", value=farm, inline=True)

    embed.set_footer(text=f"📅 منذ: {message.author.created_at.strftime('%Y/%m/%d')}")

    await message.channel.send(embed=embed)

async def handle_inventory_command(message):
    """معالجة أمر الحقيبة"""
    user_id = str(message.author.id)
    init_user(user_id, message.author.display_name)
    data = load_data()
    inventory_list = data[user_id].get("حقيبة", [])

    if not inventory_list:
        await message.channel.send("🎒 حقيبتك فارغة.")
        return

    # تجميع العناصر مع عدد كل نوع
    item_counts = {}
    for item in inventory_list:
        item_counts[item] = item_counts.get(item, 0) + 1

    # تحويل النتيجة إلى نص منسق
    items_str = "\n".join(f"• {name} × {count}"
                          for name, count in item_counts.items())
    await message.channel.send(f"🎒 محتويات حقيبتك:\n{items_str}")

async def handle_cooldowns_command(message):
    """معالجة أمر التبريد"""
    user_id = str(message.author.id)
    cooldowns = load_cooldowns().get(user_id, {})
    current_time = int(time.time())

    embed = discord.Embed(
        title="📊 قائمة التبريد الخاصة بك",
        description="تعرف على حالة أوامرك الحالية:",
        color=0x2ECC71  # أخضر أنيق
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
                value=(
                    f"🔁 قيد التبريد\n"
                    f"⏳ **{time_str}** متبقية"
                ),
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

    embed.set_footer(text="⏱️ التحديث لحظي • حافظ على توازن استخدامك ⚙️")
    await message.channel.send(embed=embed)

# =========== الحدث الرئيسي ===========

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if not os.path.exists("users.json"):
        with open("users.json", "w") as f:
            json.dump({}, f)

    with open("users.json", "r") as f:
        users = json.load(f)

    # تحقق إذا كان المستخدم جديدًا
    if user_id not in users:
        users[user_id] = {
            "balance": {
                "دولار": 0,
                "ذهب": 0,
                "ماس": 0
            },
            "حقيبة": [],
            "fish_pond": [],
            "المهنة": "مواطن",
            "الصورة": "",
            "specialization": None,
            "spec_level": 1,
            "name": message.author.display_name  # Store display name
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

        class WelcomeView(View):
            def __init__(self):
                super().__init__(timeout=300)  # 5 دقائق

            @discord.ui.button(label="📚 الشروحات الكاملة", style=ButtonStyle.success, emoji="📖")
            async def help_guide(self, interaction: Interaction, button: Button):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("❌ هذا الزر مخصص للاعب الجديد فقط!", ephemeral=True)
                    return

                # استدعاء نظام الشروحات المطور
                if advanced_help_system:
                    embed = advanced_help_system.create_main_help_embed()
                    from help_system import DetailedHelpView
                    view = DetailedHelpView(advanced_help_system)
                    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                else:
                    await interaction.response.send_message("📚 استخدم الأمر `شروحات` للحصول على دليل شامل!", ephemeral=True)

            @discord.ui.button(label="🎯 قائمة الأوامر", style=ButtonStyle.primary, emoji="⚡")
            async def show_commands(self, interaction: Interaction, button: Button):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("❌ هذا الزر مخصص للاعب الجديد فقط!", ephemeral=True)
                    return

                quick_start = (
                    "🚀 **أوامر البداية السريعة:**\n\n"
                    "💰 `يومي` - احصل على مكافأة يومية مجانية\n"
                    "💼 `عمل` - اعمل واربح المال\n"
                    "🎯 `اختصاص` - اختر تخصصك القتالي\n"
                    "🏪 `متجر` - تسوق واشتر المعدات\n"
                    "🎒 `حقيبة` - اعرض ممتلكاتك\n"
                    "💰 `رصيد` - اعرض أموالك\n\n"
                    "📋 **للمزيد:** استخدم الأمر `اوامر` لعرض جميع الأوامر المتاحة"
                )

                quick_embed = Embed(
                    title="⚡ دليل البداية السريعة",
                    description=quick_start,
                    color=0xffaa00
                )
                await interaction.response.send_message(embed=quick_embed, ephemeral=True)

            @discord.ui.button(label="🎁 المكافأة اليومية", style=ButtonStyle.danger, emoji="💎")
            async def daily_reward(self, interaction: Interaction, button: Button):
                if interaction.user.id != message.author.id:
                    await interaction.response.send_message("❌ هذا الزر مخصص للاعب الجديد فقط!", ephemeral=True)
                    return

                await interaction.response.send_message(
                    "🎁 **مكافأة ترحيبية خاصة!**\n"
                    "استخدم الأمر `يومي` الآن للحصول على:\n"
                    "💵 **100,000** دولار\n"
                    "🪙 **25** ذهب\n"
                    "💎 **1** ماس\n"
                    "⭐ **200** نقطة خبرة\n\n"
                    "💡 يمكنك الحصول على هذه المكافأة كل 24 ساعة!",
                    ephemeral=True
                )

        await message.channel.send(embed=embed, view=WelcomeView())

    # معالجة الأوامر
    content = message.content.strip().lower()
    args = content.split()

    if content == "متجر":
        await handle_shop_command(message)
        return
    elif content == "اختصاص":
        await handle_specialization_command(message)
        return
    elif content == "سلام":
        await handle_greeting_command(message)
        return
    elif content == "رصيد":
        await handle_balance_command(message)
        return
    elif content == "مهنتي":
        await handle_job_command(message)
        return
    elif content == "ثروة":
        await handle_wealth_command(message)
        return
    elif content == "عمل":
        await handle_work_command(message)
        return
    elif content == "ترقية":
        await handle_upgrade_command(message)
        return
    elif content == "يومي":
        await handle_daily_command(message)
        return
    elif content == "حسابي":
        await handle_profile_command(message)
        return
    elif content == "حقيبة":
        await handle_inventory_command(message)
        return
    elif content == "تبريد":
        await handle_cooldowns_command(message)
        return
    elif content == "درع":
        await handle_shield_command(message)
        return
    elif content.startswith("نهب "):
        await handle_steal_command(message, args)
        return
    elif content.startswith("حماية"):
        await handle_protect_command(message, args)
        return
    elif content.startswith("انتقام "):
        await handle_revenge_command(message, args)
        return

    # متابعة بقية الأوامر
    await bot.process_commands(message)

# ========================= تشغيل البوت =========================

@bot.event
async def on_ready():
    global advanced_help_system
    print(f"🔷 البوت جاهز: {bot.user}")

    # تفعيل نظام الشروحات المطور
    advanced_help_system = setup_advanced_help(bot)
    print("📚 تم تفعيل نظام الشروحات المطور")

# تشغيل الخدمات
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
