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

  

# ================= أوامر أخرى محولة من @bot.command =================

# ====== قواعد السمك والطعم ======
BAIT_SHOP = {
    "🐛 دودة": {"price": 100, "bonus": 0.00},
    "🦐 روبيان": {"price": 300, "bonus": 0.07},
    "🪱 طُعم نادر": {"price": 1000, "bonus": 0.20},
}

FISH_DEFINITIONS = {
    "🐟": {"name": "سمك عادي", "min": 10000, "max": 50000},
    "🐠": {"name": "استوائي", "min": 30000, "max": 150000},
    "🦈": {"name": "قرش", "min": 100000, "max": 200000},
    "🦐": {"name": "روبيان", "min": 15000, "max": 40000},
    "🦑": {"name": "حبار", "min": 12000, "max": 25000},
    "🦀": {"name": "سلطعون", "min": 8000, "max": 20000},
}# ====== متجر الطُعم ======
async def handle_fisher_shop_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()

    class BuyBaitButton(Button):
        def __init__(self, bait, price):
            super().__init__(label=f"{bait} - {price}💵", style=discord.ButtonStyle.primary, custom_id=bait)
            self.bait = bait
            self.price = price

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)
                return

            # اطلب من المستخدم إدخال الكمية
            await interaction.response.send_message("🔢 من فضلك أرسل عدد الوحدات التي تريد شراءها:", ephemeral=True)

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.isdigit()

            try:
                msg = await bot.wait_for("message", check=check, timeout=30)
                quantity = int(msg.content)
                total_price = self.price * quantity

                # تحميل البيانات وتحديث الرصيد
                user_id = str(interaction.user.id)
                data = load_data()
                user_data = data.get(user_id, {})

                # التأكد من تنسيق الرصيد
                balance = user_data.get("balance", {})
                if isinstance(balance, int):
                    balance = {"دولار": balance, "ذهب": 0, "ماس": 0}
                balance["دولار"] = balance.get("دولار", 0)

                if balance["دولار"] < total_price:
                    await interaction.followup.send("❌ لا تملك ما يكفي من الدولارات.", ephemeral=True)
                    return

                # خصم السعر
                balance["دولار"] -= total_price
                user_data["balance"] = balance

                # إضافة الطُعم إلى الحقيبة
                bag = user_data.setdefault("حقيبة", [])
                for _ in range(quantity):
                    bag.append(self.bait)

                data[user_id] = user_data
                save_data(data)

                await interaction.followup.send(f"✅ اشتريت {quantity} من {self.bait} بـ {total_price}💵 بنجاح!", ephemeral=True)

            except asyncio.TimeoutError:
                await interaction.followup.send("⏰ لم يتم الرد في الوقت المناسب.", ephemeral=True)

    class CloseButton(Button):
        def __init__(self):
            super().__init__(label="❌ إغلاق", style=discord.ButtonStyle.danger, row=1)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == ctx.author.id:
                await interaction.message.delete()
            else:
                await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)

    class BaitShopView(View):
        def __init__(self):
            super().__init__(timeout=60)
            for bait, info in BAIT_SHOP.items():
                self.add_item(BuyBaitButton(bait, info['price']))
            self.add_item(CloseButton())

        async def on_timeout(self):
            try:
                await ctx.send("⏳ انتهى وقت المتجر.", ephemeral=True)
            except:
                pass

    embed = discord.Embed(
        title="🎣 متجر الطُعم",
        description="اختر طُعمًا للشراء باستخدام 💵 الدولار:",
        color=0x00ffcc
    )
    await ctx.send(embed=embed, view=BaitShopView())

# ====== الصيد ======
class FishAllOrAmountButton(Button):
    def __init__(self, ctx):
        super().__init__(label="🎯 صيد كلي / جزئي", style=discord.ButtonStyle.primary, row=1)
        self.ctx = ctx

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        data = load_data()
        user_data = data.get(user_id, {})
        bag = user_data.get("حقيبة", [])
        bait_list = [item for item in bag if item in BAIT_SHOP]

        if not bait_list:
            await interaction.response.send_message("❌ لا تملك أي طُعوم.", ephemeral=True)
            return

        bait_types = list(set(bait_list))
        bait_info = "\n".join([f"{i+1}. {bait} (x{bait_list.count(bait)})" for i, bait in enumerate(bait_types)])

        await interaction.response.send_message(
            f"🎣 اختر نوع الطُعم وعدد الاستخدام:\n\n{bait_info}\n\n📝 مثال: `رقم الطعم  ثم العدد او كل``",
            ephemeral=True
        )

        def check(msg):
            return msg.author == interaction.user and msg.channel == interaction.channel

        try:
            msg = await bot.wait_for("message", check=check, timeout=30)
            parts = msg.content.strip().split()
            if len(parts) != 2:
                await msg.reply("❌ الصيغة غير صحيحة. أعد المحاولة مثل: `1 كل` أو `2 3`", delete_after=10)
                return

            index_str, amount_str = parts
            index = int(index_str) - 1
            if index < 0 or index >= len(bait_types):
                await msg.reply("❌ رقم الطُعم غير صحيح.", delete_after=10)
                return

            selected_bait = bait_types[index]
            bait_count = bait_list.count(selected_bait)

            if amount_str.lower() == "كل":
                amount = bait_count
            elif amount_str.isdigit():
                amount = int(amount_str)
                if amount <= 0 or amount > bait_count:
                    await msg.reply(f"❌ عدد غير صالح. لديك: {bait_count}.", delete_after=10)
                    return
            else:
                await msg.reply("❌ العدد غير مفهوم.", delete_after=10)
                return

            results = []
            caught_fish = 0
            for _ in range(amount):
                bag.remove(selected_bait)
                fish = random.choice(["🐟 سمكة صغيرة", "🐠 سمكة ملونة", "🦈 قرش نادر", "🪸 لا شيء..."])
                if fish != "🪸 لا شيء...":
                    bag.append(fish)
                    caught_fish += 1
                    results.append(f"{selected_bait} 🎯 ⟶ {fish}")
                else:
                    results.append(f"{selected_bait} 🎯 ⟶ 🪸 لا شيء")

            save_data(data)
            
            # تحديث مهام الصيد
            if caught_fish > 0:
                completed_tasks = tasks_system.update_task_progress(user_id, "catch_fish", caught_fish)
                result_text = "\n".join(results)
                if completed_tasks:
                    result_text += f"\n\n🎯 رائع! أكملت {len(completed_tasks)} مهمة صيد!"
            else:
                result_text = "\n".join(results)
                
            await msg.reply(f"📦 نتائج الصيد:\n{result_text}", mention_author=False)

        except asyncio.TimeoutError:
            pass  # لا نعرض إشعار عند انتهاء الوقت

# واجهة الصيد
class FishingView(View):
    def __init__(self, ctx):
        super().__init__(timeout=None)
        self.ctx = ctx
        self.add_item(FishAllOrAmountButton(ctx))

# أمر الصيد
async def handle_fishing_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    view = FishingView(ctx)
    await ctx.send("🎣 اختر طريقة الصيد:", view=view)



async def handle_pond_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    user_data = data[user_id]
    bag = user_data.get("حقيبة", [])
    pond_data = user_data.setdefault("حوض", [])  # كل سمكة عبارة عن dict

    # تنسيق الحوض الحالي
    def format_pond():
        if not pond_data:
            return "🐠 الحوض فارغ."
        desc = ""
        for i, fish in enumerate(pond_data, 1):
            age_hours = int((time.time() - fish["time"]) // 3600)
            base_value = fish["base"]
            growth = int(base_value * 0.10 * age_hours)
            current_value = base_value + growth
            desc += f"{i}. {fish['emoji']} {fish['name']} | 🕒 {age_hours}س | 💰 {current_value}💵\n"
        return desc or "🐠 الحوض فارغ."

    # عرض واجهة التفاعل
    class PondView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=180)

        @discord.ui.button(label="➕ وضع سمكة", style=discord.ButtonStyle.primary)
        async def add_fish(self, interaction: discord.Interaction, _):
            fish_items = [item for item in bag if any(f in item for f in ["سمكة", "ملونة", "قرش", "استوائي", "روبيان", "حبار", "سلطعون"])]
            if not fish_items:
                await interaction.response.send_message("🎣 لا توجد أسماك في حقيبتك لوضعها في الحوض.", ephemeral=True)
                return

            # عرض قائمة الأسماك القابلة للوضع
            options = []
            seen = set()
            for fish in fish_items:
                if fish not in seen:
                    seen.add(fish)
                    count = fish_items.count(fish)
                    options.append(discord.SelectOption(label=f"{fish} × {count}", value=fish, emoji=fish[0]))

            class FishSelect(discord.ui.Select):
                def __init__(self):
                    super().__init__(placeholder="اختر سمكة", min_values=1, max_values=1, options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    chosen = self.values[0]
                    emoji = chosen[0]
                    fish_info = FISH_DEFINITIONS.get(emoji)
                    if not fish_info:
                        await select_interaction.response.send_message("❌ لا يمكن تحديد بيانات السمكة.", ephemeral=True)
                        return

                    max_count = bag.count(chosen)
                    await select_interaction.response.send_message(
                        f"📝 كم عدد {emoji} {fish_info['name']} التي تريد وضعها في الحوض؟ (اكتب رقم أو `كل`)",
                        ephemeral=True
                    )

                    def check(msg):
                        return msg.author == select_interaction.user and msg.channel == select_interaction.channel

                    try:
                        msg = await bot.wait_for("message", check=check, timeout=30)
                        content = msg.content.strip().lower()
                        if content == "كل":
                            amount = max_count
                        elif content.isdigit():
                            amount = int(content)
                            if amount <= 0 or amount > max_count:
                                await msg.reply(f"❌ عدد غير صالح. لديك {max_count}.", delete_after=10)
                                return
                        else:
                            await msg.reply("❌ إدخال غير صالح. أعد المحاولة.", delete_after=10)
                            return

                        # تنفيذ الإضافة للحوض
                        for _ in range(amount):
                            bag.remove(chosen)
                            base_value = random.randint(fish_info["min"], fish_info["max"])
                            pond_data.append({
                                "emoji": emoji,
                                "name": fish_info["name"],
                                "base": base_value,
                                "time": time.time()
                            })

                        save_data(data)
                        await msg.reply(f"✅ تمت إضافة {amount} × {emoji} {fish_info['name']} إلى الحوض.")

                    except asyncio.TimeoutError:
                        pass  # لا نعرض شيء عند انتهاء الوقت

            view = discord.ui.View()
            view.add_item(FishSelect())
            await interaction.response.send_message("🎣 اختر سمكة لوضعها في الحوض:", view=view, ephemeral=True)


        @discord.ui.button(label="💰 بيع سمكة", style=discord.ButtonStyle.green)
        async def sell_fish(self, interaction: discord.Interaction, _):
            if not pond_data:
                await interaction.response.send_message("❌ لا توجد أسماك لبيعها في الحوض.", ephemeral=True)
                return

            # بناء قائمة الأسماك للبيع
            options = []
            for i, fish in enumerate(pond_data):
                age_hours = int((time.time() - fish["time"]) // 3600)
                value = fish["base"] + int(fish["base"] * 0.10 * age_hours)
                label = f"{fish['emoji']} {fish['name']} - {value}💵"
                options.append(discord.SelectOption(label=label, value=str(i), emoji=fish["emoji"]))

            class SellSelect(discord.ui.Select):
                def __init__(self):
                    super().__init__(placeholder="اختر سمكة لبيعها", min_values=1, max_values=1, options=options)

                async def callback(self, select_interaction: discord.Interaction):
                    index = int(self.values[0])
                    fish = pond_data.pop(index)
                    age_hours = int((time.time() - fish["time"]) // 3600)
                    value = fish["base"] + int(fish["base"] * 0.10 * age_hours)
                    user_data["balance"]["دولار"] = user_data["balance"].get("دولار", 0) + value
                    save_data(data)
                    await select_interaction.response.edit_message(content=f"💵 تم بيع {fish['emoji']} {fish['name']} مقابل {value} دولار.", view=None)

            view = discord.ui.View()
            view.add_item(SellSelect())
            await interaction.response.send_message("💰 اختر سمكة لبيعها:", view=view, ephemeral=True)

    # إرسال الواجهة
    embed = discord.Embed(
        title="🐟 حوض السمك",
        description=format_pond(),
        color=0x1ABC9C
    )
    await ctx.send(embed=embed, view=PondView())
# -------------------------- حقيبة --------فاصل -----------------------------
# -------------------------- حقيبة --------فاصل -----------------------------
# -------------------------- حقيبة --------فاصل -----------------------------
# -------------------------- حقيبة --------فاصل -----------------------------
async def handle_inventory_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    inventory_list = data[user_id].get("حقيبة", [])

    if not inventory_list:
        await ctx.send("🎒 حقيبتك فارغة.")
        return

    # تجميع العناصر مع عدد كل نوع
    item_counts = {}
    for item in inventory_list:
        item_counts[item] = item_counts.get(item, 0) + 1

    # تحويل النتيجة إلى نص منسق
    items_str = "\n".join(f"• {name} × {count}"
                          for name, count in item_counts.items())
    await ctx.send(f"🎒 محتويات حقيبتك:\n{items_str}")
# ------------------------------------------------- حسابي ---------------------فاصل-----
# ------------------------------------------------- حسابي ---------------------فاصل-----

class HelpView(View):
    def __init__(self):
        super().__init__(timeout=None)

        # كل زر يمثل شرحاً مفصلاً لجزء من النظام
        self.add_item(self.HelpButton("💰 المال", "money", ButtonStyle.primary))
        self.add_item(self.HelpButton("🌾 الزراعة", "farming", ButtonStyle.success))
        self.add_item(self.HelpButton("🎣 الصيد", "fishing", ButtonStyle.success))
        self.add_item(self.HelpButton("🛍️ المتجر", "shop", ButtonStyle.secondary))
        self.add_item(self.HelpButton("💼 الحقيبة", "bag", ButtonStyle.secondary))
        self.add_item(self.HelpButton("📆 التوقيت", "cooldown", ButtonStyle.secondary))
        self.add_item(self.HelpButton("📆 اختصاص", "specialization", ButtonStyle.secondary))
        self.add_item(self.HelpButton("🪙 العملات", "currencies", ButtonStyle.secondary))

    class HelpButton(Button):
        def __init__(self, label, topic, style):
            super().__init__(label=label, style=style)
            self.topic = topic

        async def callback(self, interaction: Interaction):
            explanations = {
                "money": "💰 **أوامر المال:**\n- `رصيد`: يظهر كم تملك من الدولار والذهب والماس.\n- `تحويل @المستخدم المبلغ`: يحول  دولار لمستخدم آخر.",
                "farming": "🌾 **الزراعة:**\n- `مزرعة`: فتح المزرعة.\n- `شراء بذور`: شراء البذور المتوفرة.\n- `زرع`: زراعة البذور.\n- `حصاد`:يتم بيع المحاصيل واضاتها لرصيدك .",
                "fishing": "🎣 **الصيد:**\n- `صياد`: فتح متجر الطُعم.\n- `صيد`: استخدام الطُعم للحصول على الأسماك.\n- `بيع سمك`: بيع الأسماك مقابل دولار أو ذهب.",
                "shop": "🛍️ **المتجر:**\n- يعرض عناصر قابلة للشراء مثل السيوف والدروع.\n- بعض الأسعار تتغير حسب السوق.\n- الأسهم 🔺🔻 تظهر تغير الأسعار.",
                "bag": "💼 **الحقيبة:**\n- تحتوي على كل الممتلكات (محاصيل، أدوات، أسماك...)\n- تستخدمها أثناء القتال، الزراعة أو البيع.",
                "cooldown": "📆 **التبريد:**\n- لا يمكن استخدام بعض الأوامر إلا بعد مدة محددة.\n- يظهر لك كم تبقى من وقت.",
                "specialization": "📆 **اختصاص:**\n- اختر اختصاصك قبل المعركة.\n-  سورا يعكس النهب محارب ينتقم من الناهب - شامان حماية - نينجا نهب مضاعف.",
                "currencies": "🪙 **العملات:**\n- **دولار**: يُستعمل للشراء.\n- **ذهب**: يُستخدم لشراء أدوات نادرة.\n- **ماس**: عملة مميزة تُجمع من الأحداث أو الشراء الخاص."
            }

            content = explanations.get(self.topic, "❓ لا يوجد شرح متاح.")
            await interaction.response.send_message(content, ephemeral=True)

# تم استبدال الأمر بنظام الشروحات المطور في help_system.py

# ------------------------------------------------- تحويل---------------------فاصل-----
async def handle_transfer_command(message):
    if member.id == ctx.author.id:
        await ctx.send("❌ لا يمكنك تحويل العملات إلى نفسك.")
        return

    if المبلغ <= 0:
        await ctx.send("❌ يجب أن يكون المبلغ أكبر من 0.")
        return

    user_id = str(ctx.author.id)
    target_id = str(member.id)

    init_user(user_id, ctx.author.display_name)
    init_user(target_id, target.display_name)

    data = load_data()
    user = data[user_id]
    target = data[target_id]

    if العملة not in ["دولار", "ذهب", "ماس"]:
        await ctx.send("❌ العملة غير معروفة. اختر من: دولار، ذهب، ماس.")
        return

    if user.get(العملة, 0) < المبلغ:
        await ctx.send(f"❌ ليس لديك ما يكفي من {العملة} لإتمام التحويل.")
        return

    # ✅ إجراء التحويل
    user[العملة] -= المبلغ
    target[العملة] = target.get(العملة, 0) + المبلغ

    save_data(data)

    await ctx.send(f"✅ تم تحويل {المبلغ} {العملة} إلى {member.mention} بنجاح.")

# ------------------------------------------------- حسابي ---------------------فاصل-----
async def handle_my_profile_command(message):
        user_id = str(ctx.author.id)

        data = load_data()
        if user_id not in data:
            init_user(user_id, ctx.author.display_name)
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
            description=f"معلومات {ctx.author.mention}",
            color=0x00b0f4
        )

        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

        embed.add_field(name="🪙 الرصيد", value=balance_text, inline=False)
        embed.add_field(name="🎒 الحقيبة", value=f"{bag_count} عنصر", inline=True)
        embed.add_field(name="🛠️ الاختصاص", value=spec_text, inline=True)
        embed.add_field(name="👷 المهنة", value=job, inline=True)
        embed.add_field(name="🎯 المهارة", value=skill, inline=True)
        embed.add_field(name="🌾 المزرعة", value=farm, inline=True)

        embed.set_footer(text=f"📅 منذ: {ctx.author.created_at.strftime('%Y/%m/%d')}")

        await ctx.send(embed=embed)
# ----------------------------------------فاصل --------- اوامر   --------------------------
command_categories = {
        "🎯 قتال": ["حماية", "درع", "اختصاص", "انتقام", "نهب", "تحدي_سريع", "مبارزة", "سباق_سريع"],
        "🛒 اقتصاد": ["متجر", "شراء", "بيع", "رصيد", "حقيبة", "حسابي", "تداول", "استثمار"],
        "🧰 مهنة": ["مهنتي", "تبريد", "عمل", "ترقية"],
        "🎣 صيد": ["صياد", "صيد", "حوض"],
        "🌾 زراعة": ["مزارع", "زرع", "مزرعة"],
        "🎮 ألعاب": ["حجر_ورقة_مقص", "تخمين", "ذاكرة", "رياضيات", "كلمات"],
        "🎯 مهام": ["مهام", "مستوى", "خبرة", "مكافآت"],
        "🏰 سراديب": ["سراديب", "عتاد", "إحصائيات_سراديب"],
        "📊 إحصائيات": ["قوائم", "سجلات", "إحصائيات", "أنشطتي", "ثروة"],
        "🎁 أخرى": ["يومي", "شروحات"]
    }
    # ===== الواجهة الفرعية =====
class CommandButtons(View):
        def __init__(self, bot, ctx, commands_list, title):
            super().__init__(timeout=30)
            self.bot = bot
            self.ctx = ctx
            self.title = title

            for index, name in enumerate(commands_list):
                row = index // 5  # 3 أزرار في الصف
                self.add_item(Button(label=name, custom_id=name, style=discord.ButtonStyle.primary, row=row))

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.ctx.author.id

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(content=f"⏱️ انتهى الوقت - {self.title}", view=self)
            except:
                pass

        @discord.ui.button(label="🔙 رجوع", style=discord.ButtonStyle.secondary, row=4)
        async def back_button(self, interaction: discord.Interaction, button: Button):
            await show_commands(interaction, return_from_sub=True)

        @discord.ui.button(label="🔒 قفل", style=discord.ButtonStyle.danger, row=4)
        async def close_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()

        async def on_button_click(self, interaction: discord.Interaction):
            command_name = interaction.data["custom_id"]
            command = self.bot.get_command(command_name)
            if command:
                await interaction.response.defer()
                
                # التعامل مع الأوامر التي تتطلب معاملات خاصة
                if command_name in ["تحدي", "سباق"]:
                    await interaction.followup.send(
                        f"⚠️ **الأمر {command_name} يتطلب معاملات إضافية:**\n\n"
                        f"🔸 للتحدي: `{command_name} @المستخدم العملة المبلغ`\n"
                        f"🔸 مثال: `{command_name} @أحمد دولار 1000`\n\n"
                        f"**العملات المتاحة:** دولار، ذهب",
                        ephemeral=True
                    )
                else:
                    await self.ctx.invoke(command)
            else:
                await interaction.response.send_message("❌ لم يتم العثور على الأمر.", ephemeral=True)
    # ===== الواجهة الرئيسية =====
class CategoryView(View):
        def __init__(self, bot, ctx):
            super().__init__(timeout=30)
            self.bot = bot
            self.ctx = ctx

            for index, (category, _) in enumerate(command_categories.items()):
                row = index // 5
                self.add_item(Button(label=category, custom_id=category, style=discord.ButtonStyle.blurple, row=row))

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            return interaction.user.id == self.ctx.author.id

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True
            try:
                await self.message.edit(content="⏱️ انتهى الوقت.", view=self)
            except:
                pass

        @discord.ui.button(label="🔒 قفل", style=discord.ButtonStyle.danger, row=4)
        async def close_button(self, interaction: discord.Interaction, button: Button):
            await interaction.message.delete()
    # ===== أمر عرض الواجهة الرئيسية =====
async def handle_show_commands_command(message):
        view = CategoryView(bot, ctx)

        async def callback(interaction: discord.Interaction):
            category = interaction.data["custom_id"]
            commands_list = command_categories.get(category)
            if commands_list:
                sub_view = CommandButtons(bot, ctx, commands_list, category)
                async def sub_callback(inner_interaction):
                    await sub_view.on_button_click(inner_interaction)

                for item in sub_view.children:
                    if isinstance(item, Button) and item.custom_id:
                        item.callback = sub_callback

                sub_view.message = await interaction.response.edit_message(
                    content=f"🧠 أوامر {category}:", view=sub_view
                )

        for item in view.children:
            if isinstance(item, Button) and item.custom_id:
                item.callback = callback

        if return_from_sub:
            await ctx.edit_original_message(content="🧠 اختر فئة الأوامر:", view=view)
        else:
            view.message = await ctx.send("🧠 اختر فئة الأوامر:", view=view)
# ----------------------------------------- أفاصل زراعة -------------------------------------
SEED_SHOP = {
    "🌾 قمح": {"price": 150, "grow_time": 3600, "min": 1000, "max": 3000},
    "🥕 جزر": {"price": 250, "grow_time": 5400, "min": 2000, "max": 4000},
    "🍅 طماطم": {"price": 400, "grow_time": 7200, "min": 3500, "max": 6000},
    "🌽 ذرة": {"price": 600, "grow_time": 10800, "min": 6000, "max": 9000},
    "🍓 فراولة": {"price": 1000, "grow_time": 14400, "min": 10000, "max": 15000},
}
async def handle_farm_shop_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()

    class BuySeedButton(Button):
        def __init__(self, seed, price):
            super().__init__(label=f"{seed} - {price}💵", style=ButtonStyle.primary)
            self.seed = seed
            self.price = price

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)
                return

            user_data = data[user_id]
            balance = user_data["balance"].get("دولار", 0)

            if balance < self.price:
                await interaction.response.send_message("❌ لا تملك ما يكفي من 💵 الدولار.", ephemeral=True)
                return

            user_data["balance"]["دولار"] -= self.price
            user_data.setdefault("حقيبة", []).append(self.seed)
            save_data(data)

            await interaction.response.send_message(f"✅ اشتريت {self.seed} بـ {self.price}💵!", ephemeral=True)

    class FarmView(View):
        def __init__(self):
            super().__init__(timeout=60)
            for seed, info in SEED_SHOP.items():
                self.add_item(BuySeedButton(seed, info["price"]))

        async def on_timeout(self):
            try:
                await ctx.send("⏳ انتهى وقت المتجر.", ephemeral=True)
            except:
                pass

    embed = discord.Embed(title="🌱 متجر البذور", description="اختر بذورًا للشراء:", color=0x91C788)
    await ctx.send(embed=embed, view=FarmView())
async def handle_plant_seed_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    user_data = data[user_id]
    bag = user_data.get("حقيبة", [])
    seeds_in_bag = [item for item in bag if item in SEED_SHOP]

    if not seeds_in_bag:
        await ctx.send("❌ لا تملك أي بذور. استخدم `!مزارع` للشراء.")
        return

    class SeedSelect(discord.ui.Select):
        def __init__(self):
            unique_seeds = list(set(seeds_in_bag))
            options = [
                discord.SelectOption(label=f"{seed} × {seeds_in_bag.count(seed)}", value=seed, emoji=seed[0])
                for seed in unique_seeds
            ]
            super().__init__(placeholder="اختر البذور للزراعة", min_values=1, max_values=1, options=options)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ ليس لك.", ephemeral=True)
                return

            selected_seed = self.values[0]
            info = SEED_SHOP[selected_seed]

            bag.remove(selected_seed)
            user_data.setdefault("مزرعة", []).append({
                "emoji": selected_seed[0],
                "name": selected_seed,
                "planted_at": time.time(),
                "grow_time": info["grow_time"],
                "min": info["min"],
                "max": info["max"],
            })
            save_data(data)

            await interaction.response.edit_message(content=f"✅ تم زرع {selected_seed}!", view=None)

    view = discord.ui.View()
    view.add_item(SeedSelect())
    await ctx.send("🌾 اختر البذور التي تريد زراعتها:", view=view)
async def handle_farm_status_command(message):
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    user_data = data[user_id]
    farm = user_data.setdefault("مزرعة", [])

    ready = []
    not_ready = []

    now = time.time()
    for crop in farm:
        elapsed = now - crop["planted_at"]
        if elapsed >= crop["grow_time"]:
            ready.append(crop)
        else:
            not_ready.append((crop, crop["grow_time"] - elapsed))

    desc = ""
    if ready:
        desc += "✅ **محاصيل جاهزة للحصاد:**\n"
        for crop in ready:
            desc += f"{crop['emoji']} {crop['name']} - جاهزة!\n"
    if not_ready:
        desc += "\n⏳ **محاصيل تنمو حاليًا:**\n"
        for crop, remain in not_ready:
            mins = int(remain // 60)
            desc += f"{crop['emoji']} {crop['name']} - {mins} دقيقة متبقية\n"

    if not desc:
        desc = "🌱 لا توجد محاصيل مزروعة."

    class HarvestButton(Button):
        def __init__(self):
            super().__init__(label="💰 حصاد المحاصيل الجاهزة", style=ButtonStyle.green)

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا الزر ليس لك.", ephemeral=True)
                return

            total = 0
            harvested = []

            for crop in ready:
                value = random.randint(crop["min"], crop["max"])
                total += value
                harvested.append(crop)

            for h in harvested:
                farm.remove(h)

            user_data["balance"]["دولار"] = user_data["balance"].get("دولار", 0) + total
            save_data(data)

            # تسجيل النشاط
            logs_system.add_log(
                "farm_logs",
                user_id,
                ctx.author.display_name,
                f"حصد {len(harvested)} محصول",
                {"crops_count": len(harvested), "earned": total}
            )
            
            # تحديث مهام الزراعة
            completed_tasks = tasks_system.update_task_progress(user_id, "harvest_crops", len(harvested))
            
            success_msg = f"🌾 تم حصاد {len(harvested)} محصول مقابل 💵 {total} دولار."
            if completed_tasks:
                success_msg += f"\n🎯 أكملت {len(completed_tasks)} مهمة!"

            await interaction.response.edit_message(content=success_msg, view=None)

    view = View()
    if ready:
        view.add_item(HarvestButton())

    embed = discord.Embed(title="🌾 حالة المزرعة", description=desc, color=0xC4F1BE)
    await ctx.send(embed=embed, view=view)
# ----------------------------------------- نظام المهام والخبرة -------------------------------------

async def handle_tasks_command_command(message):
    """عرض المهام الحالية للمستخدم"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    # فحص وتحديث المهام
    tasks_system.check_and_update_tasks(user_id)
    
    # جلب المهام النشطة
    user_tasks = tasks_system.load_user_tasks(user_id)
    active_tasks = user_tasks.get("active_tasks", [])
    
    if not active_tasks:
        await ctx.send("📝 لا توجد مهام متاحة حالياً. سيتم إنشاء مهام جديدة قريباً!")
        return
    
    class TasksView(View):
        def __init__(self):
            super().__init__(timeout=120)
            
            # تجميع المهام حسب الفئة
            daily_tasks = [t for t in active_tasks if t["category"] == "daily"]
            weekly_tasks = [t for t in active_tasks if t["category"] == "weekly"]
            
            if daily_tasks:
                self.add_item(TasksCategoryButton("📅 يومية", daily_tasks))
            if weekly_tasks:
                self.add_item(TasksCategoryButton("🗓️ أسبوعية", weekly_tasks))
    
    class TasksCategoryButton(Button):
        def __init__(self, label, tasks_list):
            super().__init__(label=label, style=ButtonStyle.primary)
            self.tasks_list = tasks_list
        
        async def callback(self, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return
            
            embed = Embed(
                title=f"🎯 {self.label}",
                description="اختر مهمة لعرض تفاصيلها أو استلام المكافأة:",
                color=0x3498db
            )
            
            view = TaskDetailView(self.tasks_list)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    class TaskDetailView(View):
        def __init__(self, tasks_list):
            super().__init__(timeout=60)
            
            for task in tasks_list[:10]:  # حد أقصى 10 مهام
                self.add_item(TaskButton(task))
    
    class TaskButton(Button):
        def __init__(self, task):
            self.task = task
            progress_percent = int((task["progress"] / task["target"]) * 100)
            
            if task["completed"] and not task.get("claimed", False):
                style = ButtonStyle.success
                label = f"✅ {task['name'][:20]}..."
            elif task["completed"]:
                style = ButtonStyle.secondary
                label = f"🏆 {task['name'][:20]}..."
            else:
                style = ButtonStyle.primary
                label = f"⏳ {task['name'][:20]}... ({progress_percent}%)"
            
            super().__init__(label=label, style=style)
        
        async def callback(self, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return
            
            # تحديد لون الصعوبة
            difficulty_colors = {
                "سهل": 0x2ecc71,
                "متوسط": 0xf39c12,
                "صعب": 0xe67e22,
                "صعب جداً": 0xe74c3c,
                "أسطوري": 0x9b59b6
            }
            
            color = difficulty_colors.get(self.task["difficulty"], 0x3498db)
            
            embed = Embed(
                title=f"🎯 {self.task['name']}",
                description=self.task["description"],
                color=color
            )
            
            # شريط التقدم
            progress_percent = int((self.task["progress"] / self.task["target"]) * 100)
            progress_bar = "█" * (progress_percent // 10) + "░" * (10 - progress_percent // 10)
            
            embed.add_field(
                name="📊 التقدم",
                value=f"`{progress_bar}` {self.task['progress']}/{self.task['target']} ({progress_percent}%)",
                inline=False
            )
            
            embed.add_field(
                name="🏅 الصعوبة",
                value=self.task["difficulty"],
                inline=True
            )
            
            # عرض المكافآت
            rewards_text = ""
            for currency, amount in self.task["reward"].items():
                if currency == "دولار":
                    rewards_text += f"💵 {amount:,} دولار\n"
                elif currency == "ذهب":
                    rewards_text += f"🪙 {amount} ذهب\n"
                elif currency == "ماس":
                    rewards_text += f"💎 {amount} ماس\n"
                elif currency == "exp":
                    rewards_text += f"⭐ {amount} خبرة\n"
            
            embed.add_field(
                name="🎁 المكافآت",
                value=rewards_text.strip(),
                inline=True
            )
            
            # وقت انتهاء الصلاحية
            time_left = self.task["expires_at"] - time.time()
            if time_left > 0:
                hours = int(time_left // 3600)
                minutes = int((time_left % 3600) // 60)
                embed.add_field(
                    name="⏰ الوقت المتبقي",
                    value=f"{hours}س {minutes}د",
                    inline=True
                )
            
            view = None
            if self.task["completed"] and not self.task.get("claimed", False):
                view = ClaimRewardView(self.task)
            
            await interaction.response.edit_message(embed=embed, view=view)
    
    class ClaimRewardView(View):
        def __init__(self, task):
            super().__init__(timeout=30)
            self.task = task
        
        @discord.ui.button(label="🎁 استلام المكافأة", style=ButtonStyle.success)
        async def claim_reward(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return
            
            reward = tasks_system.claim_task_reward(user_id, self.task["id"])
            
            if reward:
                reward_text = ""
                for currency, amount in reward.items():
                    if currency == "دولار":
                        reward_text += f"💵 {amount:,} دولار\n"
                    elif currency == "ذهب":
                        reward_text += f"🪙 {amount} ذهب\n"
                    elif currency == "ماس":
                        reward_text += f"💎 {amount} ماس\n"
                    elif currency == "exp":
                        reward_text += f"⭐ {amount} خبرة\n"
                
                embed = Embed(
                    title="🎉 تم استلام المكافأة!",
                    description=f"✅ تم إنجاز المهمة: **{self.task['name']}**\n\n🎁 **المكافآت المستلمة:**\n{reward_text}",
                    color=0x2ecc71
                )
                
                await interaction.response.edit_message(embed=embed, view=None)
            else:
                await interaction.response.send_message("❌ حدث خطأ في استلام المكافأة.", ephemeral=True)
    
    # جلب معلومات المستوى
    level_info = tasks_system.get_user_level_info(user_id)
    
    embed = Embed(
        title="🎯 لوحة المهام",
        description=f"مرحباً {ctx.author.mention}! إليك مهامك الحالية:",
        color=0x3498db
    )
    
    embed.add_field(
        name="📈 مستواك",
        value=f"🏆 المستوى: **{level_info['level']}**\n⭐ الخبرة: **{level_info['experience']:,}**\n🎯 للمستوى القادم: **{level_info['exp_needed']}**",
        inline=False
    )
    
    # إحصائيات المهام
    completed_count = sum(1 for t in active_tasks if t["completed"])
    total_count = len(active_tasks)
    
    embed.add_field(
        name="📊 إحصائيات المهام",
        value=f"✅ مكتملة: **{completed_count}**\n⏳ جارية: **{total_count - completed_count}**\n📝 إجمالي: **{total_count}**",
        inline=False
    )
    
    await ctx.send(embed=embed, view=TasksView())

async def handle_level_command_command(message):
    """عرض معلومات المستوى والخبرة"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    level_info = tasks_system.get_user_level_info(user_id)
    
    # حساب شريط الخبرة
    progress_percent = int((level_info['exp_progress'] / level_info['exp_for_next_level']) * 100)
    progress_bar = "█" * (progress_percent // 5) + "░" * (20 - progress_percent // 5)
    
    embed = Embed(
        title="🏆 ملف المستوى",
        color=0xf39c12
    )
    
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )
    
    embed.add_field(
        name="📊 معلومات المستوى",
        value=(
            f"🏆 **المستوى الحالي:** {level_info['level']}\n"
            f"⭐ **إجمالي الخبرة:** {level_info['experience']:,}\n"
            f"🎯 **للمستوى القادم:** {level_info['exp_needed']} نقطة"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📈 شريط التقدم",
        value=f"`{progress_bar}` {progress_percent}%\n{level_info['exp_progress']}/{level_info['exp_for_next_level']}",
        inline=False
    )
    
    # تحديد الرتبة حسب المستوى
    if level_info['level'] >= 100:
        rank = "🌟 أسطوري"
        rank_color = 0x9b59b6
    elif level_info['level'] >= 50:
        rank = "💎 خبير"
        rank_color = 0x3498db
    elif level_info['level'] >= 25:
        rank = "🥇 متقدم"
        rank_color = 0xf39c12
    elif level_info['level'] >= 10:
        rank = "🥈 متوسط"
        rank_color = 0x95a5a6
    else:
        rank = "🥉 مبتدئ"
        rank_color = 0xe67e22
    
    embed.add_field(
        name="🏅 الرتبة",
        value=rank,
        inline=True
    )
    
    embed.color = rank_color
    
    await ctx.send(embed=embed)

async def handle_experience_leaderboard_command(message):
    """عرض قائمة أفضل اللاعبين من ناحية الخبرة"""
    data = load_data()
    
    # جمع بيانات الخبرة للجميع
    experience_data = []
    for user_id, user_data in data.items():
        exp = user_data.get("experience", 0)
        level = user_data.get("level", 1)
        username = user_data.get("username", f"مستخدم {user_id[:8]}")
        
        if exp > 0:  # فقط المستخدمين الذين لديهم خبرة
            experience_data.append({
                "user_id": user_id,
                "username": username,
                "experience": exp,
                "level": level
            })
    
    # ترتيب حسب الخبرة
    experience_data.sort(key=lambda x: x["experience"], reverse=True)
    
    if not experience_data:
        await ctx.send("📊 لا توجد بيانات خبرة متاحة حتى الآن.")
        return
    
    embed = Embed(
        title="⭐ قائمة أصحاب أعلى خبرة",
        description="🏆 أفضل 10 لاعبين من ناحية نقاط الخبرة:",
        color=0xf39c12
    )
    
    description = ""
    for i, player in enumerate(experience_data[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        description += (
            f"{medal} **{player['username']}**\n"
            f"🏆 المستوى {player['level']} | ⭐ {player['experience']:,} خبرة\n\n"
        )
    
    embed.description += f"\n{description}"
    
    # إضافة موقع المستخدم الحالي
    user_id = str(ctx.author.id)
    user_rank = None
    for i, player in enumerate(experience_data, 1):
        if player["user_id"] == user_id:
            user_rank = i
            break
    
    if user_rank:
        embed.set_footer(text=f"🎯 موقعك: #{user_rank} من أصل {len(experience_data)} لاعب")
    
    await ctx.send(embed=embed)

async def handle_rewards_command_command(message):
    """عرض المكافآت اليومية والأسبوعية المتاحة"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    # فحص المكافآت المتاحة
    current_time = time.time()
    user_cooldowns = load_cooldowns().get(user_id, {})
    
    # فحص المكافأة اليومية
    daily_last_used = user_cooldowns.get("يومي", 0)
    daily_available = (current_time - daily_last_used) >= DEFAULT_COOLDOWN["يومي"]
    
    class RewardsView(View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.button(label="🎁 مكافأة يومية", style=ButtonStyle.success if daily_available else ButtonStyle.secondary, disabled=not daily_available)
        async def daily_reward(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return
            
            # تنفيذ المكافأة اليومية
            data = load_data()
            user = data[user_id]
            
            # إضافة المكافآت
            user["balance"]["دولار"] += 100000
            user["balance"]["ذهب"] += 25
            user["balance"]["ماس"] += 1
            
            # إضافة خبرة
            user["experience"] = user.get("experience", 0) + 200
            tasks_system._update_experience_level(user)
            
            save_data(data)
            update_cooldown(user_id, "يومي")
            
            embed = Embed(
                title="🎉 تم استلام المكافأة اليومية!",
                description=(
                    "✅ **تهانينا!** حصلت على:\n\n"
                    "💵 **100,000** دولار\n"
                    "🪙 **25** ذهب\n"
                    "💎 **1** ماس\n"
                    "⭐ **200** نقطة خبرة"
                ),
                color=0x2ecc71
            )
            embed.set_footer(text="🔄 يمكنك الحصول على المكافأة التالية غداً!")
            
            await interaction.response.edit_message(embed=embed, view=None)
        
        @discord.ui.button(label="🏆 مكافآت خاصة", style=ButtonStyle.primary)
        async def special_rewards(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return
            
            # عرض المكافآت الخاصة حسب المستوى
            level_info = tasks_system.get_user_level_info(user_id)
            level = level_info['level']
            
            embed = Embed(
                title="🏆 المكافآت الخاصة",
                description="🎯 مكافآت حسب مستواك:",
                color=0xf39c12
            )
            
            if level >= 5:
                embed.add_field(
                    name="🥉 مكافأة المستوى 5+",
                    value="💰 مكافآت عمل مضاعفة",
                    inline=False
                )
            
            if level >= 10:
                embed.add_field(
                    name="🥈 مكافأة المستوى 10+",
                    value="🎮 ألعاب إضافية مفتوحة",
                    inline=False
                )
            
            if level >= 25:
                embed.add_field(
                    name="🥇 مكافأة المستوى 25+",
                    value="⚔️ قدرات قتال محسنة",
                    inline=False
                )
            
            if level >= 50:
                embed.add_field(
                    name="💎 مكافأة المستوى 50+",
                    value="👑 مكانة VIP في النظام",
                    inline=False
                )
            
            if level < 5:
                embed.add_field(
                    name="🔒 مكافآت مقفلة",
                    value="🎯 ارفع مستواك للحصول على المزيد!",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    embed = Embed(
        title="🎁 مركز المكافآت",
        description=f"مرحباً {ctx.author.mention}! إليك المكافآت المتاحة:",
        color=0x3498db
    )
    
    # حالة المكافأة اليومية
    if daily_available:
        daily_status = "✅ **متاحة الآن!**"
        daily_color = "🟢"
    else:
        time_left = DEFAULT_COOLDOWN["يومي"] - (current_time - daily_last_used)
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        daily_status = f"⏳ متاحة خلال: **{hours}س {minutes}د**"
        daily_color = "🔴"
    
    embed.add_field(
        name=f"{daily_color} المكافأة اليومية",
        value=f"{daily_status}\n💰 **المحتويات:** 100K$ + 25🪙 + 1💎 + 200⭐",
        inline=False
    )
    
    # معلومات المستوى
    level_info = tasks_system.get_user_level_info(user_id)
    embed.add_field(
        name="📊 إحصائياتك",
        value=f"🏆 المستوى: **{level_info['level']}**\n⭐ الخبرة: **{level_info['experience']:,}**",
        inline=True
    )
    
    await ctx.send(embed=embed, view=RewardsView())

# ========================================= ألعاب المراهنة بين المستخدمين =========================================

# نظام التحديات المتاحة
ACTIVE_CHALLENGES = {}

async def handle_quick_challenge_menu_command(message):
    """قائمة تحدي سريعة للاختيار من الأزرار"""
    embed = discord.Embed(
        title="⚔️ تحدي المراهنة",
        description="🎯 **كيفية بدء التحدي:**\n\n"
                   "🔸 استخدم الأمر: `تحدي @المستخدم العملة المبلغ`\n"
                   "🔸 مثال: `تحدي @أحمد دولار 10000`\n\n"
                   "**العملات المتاحة:** دولار، ذهب\n"
                   "**الألعاب المتاحة:**\n"
                   "🪨📄✂️ حجر ورقة مقص\n"
                   "🎲 نرد الحظ\n"
                   "🔢 تخمين الرقم",
        color=0xe74c3c
    )
    await ctx.send(embed=embed)

async def handle_challenge_player_command(message):
    """تحدي لاعب آخر في مراهنة"""
    user_id = str(ctx.author.id)
    opponent_id = str(opponent.id)
    
    if opponent.id == ctx.author.id:
        await ctx.send("❌ لا يمكنك تحدي نفسك!")
        return
    
    if opponent.bot:
        await ctx.send("❌ لا يمكن تحدي البوتات!")
        return
    
    # التحقق من العملة
    if currency not in ["دولار", "ذهب"]:
        await ctx.send("❌ العملة غير صحيحة. استخدم: دولار أو ذهب")
        return
    
    if amount <= 0:
        await ctx.send("❌ المبلغ يجب أن يكون أكبر من 0")
        return
    
    # تهيئة المستخدمين
    init_user(user_id, ctx.author.display_name)
    init_user(opponent_id, opponent.display_name)
    
    data = load_data()
    challenger_balance = data[user_id]["balance"].get(currency, 0)
    opponent_balance = data[opponent_id]["balance"].get(currency, 0)
    
    # فحص الرصيد
    if challenger_balance < amount:
        await ctx.send(f"❌ ليس لديك {amount} {currency}!")
        return
    
    if opponent_balance < amount:
        await ctx.send(f"❌ {opponent.mention} لا يملك {amount} {currency}!")
        return
    
    # إنشاء التحدي
    challenge_id = f"{user_id}_{opponent_id}_{int(time.time())}"
    ACTIVE_CHALLENGES[challenge_id] = {
        "challenger": user_id,
        "opponent": opponent_id,
        "currency": currency,
        "amount": amount,
        "created_at": time.time()
    }
    
    class ChallengeView(View):
        def __init__(self):
            super().__init__(timeout=120)
        
        @discord.ui.button(label="✅ قبول التحدي", style=ButtonStyle.success)
        async def accept_challenge(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذا التحدي ليس لك!", ephemeral=True)
                return
            
            if challenge_id not in ACTIVE_CHALLENGES:
                await interaction.response.send_message("❌ التحدي لم يعد متاحاً!", ephemeral=True)
                return
            
            # بدء اللعبة
            await interaction.response.send_message("🎮 تم قبول التحدي! اختاروا لعبة:", view=GameSelectionView(challenge_id), ephemeral=False)
        
        @discord.ui.button(label="❌ رفض التحدي", style=ButtonStyle.danger)
        async def decline_challenge(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذا التحدي ليس لك!", ephemeral=True)
                return
            
            if challenge_id in ACTIVE_CHALLENGES:
                del ACTIVE_CHALLENGES[challenge_id]
            
            await interaction.response.edit_message(content=f"❌ {opponent.mention} رفض التحدي.", view=None)
    
    currency_emoji = "💵" if currency == "دولار" else "🪙"
    embed = Embed(
        title="⚔️ تحدي مراهنة!",
        description=f"🥊 **{ctx.author.mention}** يتحدى **{opponent.mention}**!\n\n💰 **المراهنة:** {amount:,} {currency_emoji} {currency}\n🎮 **نوع اللعبة:** سيتم الاختيار بعد القبول",
        color=0xe74c3c
    )
    
    embed.add_field(
        name="📋 تفاصيل التحدي",
        value=f"🏆 الفائز يحصل على **{amount * 2:,}** {currency}\n⏱️ مدة القبول: **2 دقيقة**",
        inline=False
    )
    
    await ctx.send(embed=embed, view=ChallengeView())

class GameSelectionView(View):
    def __init__(self, challenge_id):
        super().__init__(timeout=60)
        self.challenge_id = challenge_id
    
    @discord.ui.button(label="🪨📄✂️ حجر ورقة مقص", style=ButtonStyle.primary)
    async def rock_paper_scissors(self, interaction: Interaction, button: Button):
        await self.start_game(interaction, "rps")
    
    @discord.ui.button(label="🎲 نرد الحظ", style=ButtonStyle.secondary)
    async def dice_game(self, interaction: Interaction, button: Button):
        await self.start_game(interaction, "dice")
    
    @discord.ui.button(label="🔢 تخمين الرقم", style=ButtonStyle.success)
    async def number_guess(self, interaction: Interaction, button: Button):
        await self.start_game(interaction, "guess")
    
    async def start_game(self, interaction: Interaction, game_type):
        if self.challenge_id not in ACTIVE_CHALLENGES:
            await interaction.response.send_message("❌ التحدي لم يعد متاحاً!", ephemeral=True)
            return
        
        challenge = ACTIVE_CHALLENGES[self.challenge_id]
        challenger_id = challenge["challenger"]
        opponent_id = challenge["opponent"]
        
        # التحقق من أن المستخدم جزء من التحدي
        if str(interaction.user.id) not in [challenger_id, opponent_id]:
            await interaction.response.send_message("❌ لست جزءاً من هذا التحدي!", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        if game_type == "rps":
            await self.play_rps(interaction)
        elif game_type == "dice":
            await self.play_dice(interaction)
        elif game_type == "guess":
            await self.play_guess(interaction)
    
    async def play_rps(self, interaction: Interaction):
        """لعبة حجر ورقة مقص"""
        challenge = ACTIVE_CHALLENGES[self.challenge_id]
        
        class RPSBattleView(View):
            def __init__(self):
                super().__init__(timeout=60)
                self.choices = {}
            
            @discord.ui.button(label="🪨", style=ButtonStyle.secondary)
            async def rock(self, rps_interaction: Interaction, button: Button):
                await self.make_choice(rps_interaction, "حجر", "🪨")
            
            @discord.ui.button(label="📄", style=ButtonStyle.primary)
            async def paper(self, rps_interaction: Interaction, button: Button):
                await self.make_choice(rps_interaction, "ورقة", "📄")
            
            @discord.ui.button(label="✂️", style=ButtonStyle.danger)
            async def scissors(self, rps_interaction: Interaction, button: Button):
                await self.make_choice(rps_interaction, "مقص", "✂️")
            
            async def make_choice(self, rps_interaction: Interaction, choice, emoji):
                user_id = str(rps_interaction.user.id)
                if user_id not in [challenge["challenger"], challenge["opponent"]]:
                    await rps_interaction.response.send_message("❌ لست جزءاً من هذا التحدي!", ephemeral=True)
                    return
                
                self.choices[user_id] = choice
                await rps_interaction.response.send_message(f"✅ اخترت {emoji} {choice}", ephemeral=True)
                
                if len(self.choices) == 2:
                    await self.determine_winner(rps_interaction)
            
            async def determine_winner(self, rps_interaction):
                challenger_choice = self.choices.get(challenge["challenger"])
                opponent_choice = self.choices.get(challenge["opponent"])
                
                # تحديد الفائز
                if challenger_choice == opponent_choice:
                    result = "تعادل! 🤝"
                    winner = None
                elif (challenger_choice == "حجر" and opponent_choice == "مقص") or \
                     (challenger_choice == "ورقة" and opponent_choice == "حجر") or \
                     (challenger_choice == "مقص" and opponent_choice == "ورقة"):
                    result = "فوز المتحدي! 🎉"
                    winner = challenge["challenger"]
                else:
                    result = "فوز المتحدى! 🎉"
                    winner = challenge["opponent"]
                
                await self.finish_game(rps_interaction, winner, result, challenger_choice, opponent_choice)
        
        embed = Embed(
            title="🪨📄✂️ حجر ورقة مقص",
            description="اختاروا حركتكم!",
            color=0x3498db
        )
        
        await interaction.followup.send(embed=embed, view=RPSBattleView())
    
    async def play_dice(self, interaction: Interaction):
        """لعبة النرد"""
        challenge = ACTIVE_CHALLENGES[self.challenge_id]
        
        challenger_roll = random.randint(1, 6)
        opponent_roll = random.randint(1, 6)
        
        if challenger_roll > opponent_roll:
            winner = challenge["challenger"]
            result = "فوز المتحدي! 🎉"
        elif opponent_roll > challenger_roll:
            winner = challenge["opponent"]
            result = "فوز المتحدى! 🎉"
        else:
            winner = None
            result = "تعادل! 🤝"
        
        embed = Embed(
            title="🎲 نتيجة نرد الحظ",
            description=f"🎲 المتحدي: **{challenger_roll}**\n🎲 المتحدى: **{opponent_roll}**\n\n{result}",
            color=0xf39c12
        )
        
        await self.finish_game(interaction, winner, result)
    
    async def play_guess(self, interaction: Interaction):
        """لعبة تخمين الرقم"""
        challenge = ACTIVE_CHALLENGES[self.challenge_id]
        secret_number = random.randint(1, 10)
        
        class GuessView(View):
            def __init__(self):
                super().__init__(timeout=30)
                self.guesses = {}
            
            @discord.ui.button(label="🔢 خمن رقم", style=ButtonStyle.primary)
            async def guess_number(self, guess_interaction: Interaction, button: Button):
                user_id = str(guess_interaction.user.id)
                if user_id not in [challenge["challenger"], challenge["opponent"]]:
                    await guess_interaction.response.send_message("❌ لست جزءاً من هذا التحدي!", ephemeral=True)
                    return
                
                class GuessModal(Modal, title="خمن الرقم"):
                    def __init__(self):
                        super().__init__()
                        self.number_input = TextInput(
                            label="أدخل رقماً من 1 إلى 10",
                            placeholder="مثال: 7",
                            max_length=2
                        )
                        self.add_item(self.number_input)
                    
                    async def on_submit(self, modal_interaction: Interaction):
                        try:
                            guess = int(self.number_input.value)
                            if not 1 <= guess <= 10:
                                raise ValueError
                        except ValueError:
                            await modal_interaction.response.send_message("❌ أدخل رقماً من 1 إلى 10!", ephemeral=True)
                            return
                        
                        view.guesses[user_id] = guess
                        await modal_interaction.response.send_message(f"✅ خمنت الرقم {guess}", ephemeral=True)
                        
                        if len(view.guesses) == 2:
                            await view.determine_winner(modal_interaction)
                
                await guess_interaction.response.send_modal(GuessModal())
            
            async def determine_winner(self, guess_interaction):
                challenger_guess = self.guesses.get(challenge["challenger"])
                opponent_guess = self.guesses.get(challenge["opponent"])
                
                challenger_diff = abs(challenger_guess - secret_number)
                opponent_diff = abs(opponent_guess - secret_number)
                
                if challenger_diff < opponent_diff:
                    winner = challenge["challenger"]
                    result = "فوز المتحدي! 🎉"
                elif opponent_diff < challenger_diff:
                    winner = challenge["opponent"]
                    result = "فوز المتحدى! 🎉"
                else:
                    winner = None
                    result = "تعادل! 🤝"
                
                result_text = f"🔢 الرقم السري: **{secret_number}**\n🎯 المتحدي خمن: **{challenger_guess}** (فرق: {challenger_diff})\n🎯 المتحدى خمن: **{opponent_guess}** (فرق: {opponent_diff})\n\n{result}"
                
                await self.parent.finish_game(guess_interaction, winner, result_text)
        
        view = GuessView()
        view.parent = self
        
        embed = Embed(
            title="🔢 تخمين الرقم السري",
            description="خمنوا رقماً من 1 إلى 10!\nالأقرب للرقم السري يفوز!",
            color=0x9b59b6
        )
        
        await interaction.followup.send(embed=embed, view=view)
    
    async def finish_game(self, interaction, winner, result_text, *args):
        """إنهاء اللعبة وتوزيع المكافآت"""
        challenge = ACTIVE_CHALLENGES[self.challenge_id]
        data = load_data()
        
        challenger_id = challenge["challenger"]
        opponent_id = challenge["opponent"]
        currency = challenge["currency"]
        amount = challenge["amount"]
        
        if winner:
            # تحويل المال
            data[challenger_id]["balance"][currency] -= amount
            data[opponent_id]["balance"][currency] -= amount
            data[winner]["balance"][currency] += amount * 2
            
            winner_name = data[winner].get("username", "اللاعب")
            currency_emoji = "💵" if currency == "دولار" else "🪙"
            
            embed = Embed(
                title="🏆 انتهاء المباراة!",
                description=f"{result_text}\n\n💰 **{winner_name}** ربح {amount * 2:,} {currency_emoji} {currency}!",
                color=0x00ff00
            )
            
            # تسجيل النشاط
            logs_system.add_log(
                "game_logs",
                winner,
                data[winner].get("username", "مجهول"),
                f"فاز في تحدي مراهنة",
                {"game": "challenge", "winnings": amount * 2, "currency": currency}
            )
        else:
            # إعادة المال في حالة التعادل
            embed = Embed(
                title="🤝 تعادل!",
                description=f"{result_text}\n\n💰 تم إعادة المراهنة لكلا اللاعبين.",
                color=0xf39c12
            )
        
        save_data(data)
        del ACTIVE_CHALLENGES[self.challenge_id]
        
        if hasattr(interaction, 'followup'):
            await interaction.followup.send(embed=embed)
        else:
            await interaction.response.send_message(embed=embed)

async def handle_quick_duel_command(message):
    """مبارزة سريعة بدون مراهنة"""
    if not opponent:
        await ctx.send("❌ يجب تحديد المنافس!\nمثال: `مبارزة @المستخدم`")
        return
    
    if opponent.id == ctx.author.id:
        await ctx.send("❌ لا يمكنك مبارزة نفسك!")
        return
    
    if opponent.bot:
        await ctx.send("❌ لا يمكن مبارزة البوتات!")
        return
    
    class DuelView(View):
        def __init__(self):
            super().__init__(timeout=60)
        
        @discord.ui.button(label="⚔️ قبول المبارزة", style=ButtonStyle.danger)
        async def accept_duel(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذه المبارزة ليست لك!", ephemeral=True)
                return
            
            # مبارزة سريعة - نتيجة عشوائية مع تأثير الاختصاص
            user_id = str(ctx.author.id)
            opponent_id = str(opponent.id)
            
            init_user(user_id, ctx.author.display_name)
            init_user(opponent_id, opponent.display_name)
            
            data = load_data()
            user_spec = data[user_id].get("specialization", {})
            opponent_spec = data[opponent_id].get("specialization", {})
            
            # حساب قوة كل لاعب
            user_power = random.randint(1, 100)
            opponent_power = random.randint(1, 100)
            
            # مكافآت الاختصاص
            if user_spec.get("type") == "محارب":
                user_power += 10
            elif user_spec.get("type") == "نينجا":
                user_power += 5
            
            if opponent_spec.get("type") == "محارب":
                opponent_power += 10
            elif opponent_spec.get("type") == "نينجا":
                opponent_power += 5
            
            # تحديد الفائز
            if user_power > opponent_power:
                winner = ctx.author
                loser = opponent
                winner_power = user_power
                loser_power = opponent_power
            elif opponent_power > user_power:
                winner = opponent
                loser = ctx.author
                winner_power = opponent_power
                loser_power = user_power
            else:
                winner = None
            
            if winner:
                reward = random.randint(1000, 5000)
                winner_id = str(winner.id)
                data[winner_id]["balance"]["دولار"] += reward
                
                embed = Embed(
                    title="⚔️ نتيجة المبارزة!",
                    description=f"🥊 **{ctx.author.mention}** ({user_power}) ⚔️ **{opponent.mention}** ({opponent_power})\n\n🏆 **الفائز: {winner.mention}**\n💰 المكافأة: {reward:,} دولار",
                    color=0x00ff00
                )
                
                # تسجيل النشاط
                logs_system.add_log(
                    "game_logs",
                    winner_id,
                    winner.display_name,
                    f"فاز في مبارزة ضد {loser.display_name}",
                    {"game": "duel", "reward": reward, "opponent": loser.display_name}
                )
            else:
                embed = Embed(
                    title="⚔️ مبارزة متعادلة!",
                    description=f"🥊 **{ctx.author.mention}** ({user_power}) ⚔️ **{opponent.mention}** ({opponent_power})\n\n🤝 تعادل! كلاكما محارب قوي!",
                    color=0xf39c12
                )
            
            save_data(data)
            await interaction.response.edit_message(embed=embed, view=None)
        
        @discord.ui.button(label="❌ رفض المبارزة", style=ButtonStyle.secondary)
        async def decline_duel(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذه المبارزة ليست لك!", ephemeral=True)
                return
            
            await interaction.response.edit_message(content=f"❌ {opponent.mention} رفض المبارزة.", view=None)
    
    embed = Embed(
        title="⚔️ دعوة للمبارزة!",
        description=f"🥊 **{ctx.author.mention}** يتحدى **{opponent.mention}** في مبارزة شرف!\n\n🎯 مبارزة مجانية بمكافأة عشوائية للفائز\n⏱️ مدة القبول: دقيقة واحدة",
        color=0xe74c3c
    )
    
    await ctx.send(embed=embed, view=DuelView())

async def handle_quick_racing_menu_command(message):
    """قائمة سباق سريعة للاختيار من الأزرار"""
    embed = discord.Embed(
        title="🏁 سباق السرعة",
        description="🎯 **كيفية بدء السباق:**\n\n"
                   "🔸 استخدم الأمر: `سباق @المستخدم العملة المبلغ`\n"
                   "🔸 مثال: `سباق @أحمد دولار 5000`\n\n"
                   "**العملات المتاحة:** دولار، ذهب\n"
                   "**القواعد:** أسرع من يضغط الزر يفوز بالمبلغ كاملاً!",
        color=0x3498db
    )
    await ctx.send(embed=embed)

async def handle_racing_game_command(message):
    """سباق سرعة بين لاعبين"""
    user_id = str(ctx.author.id)
    opponent_id = str(opponent.id)
    
    if opponent.id == ctx.author.id:
        await ctx.send("❌ لا يمكنك سباق نفسك!")
        return
    
    if opponent.bot:
        await ctx.send("❌ لا يمكن سباق البوتات!")
        return
    
    if currency not in ["دولار", "ذهب"]:
        await ctx.send("❌ العملة غير صحيحة. استخدم: دولار أو ذهب")
        return
    
    if amount <= 0:
        await ctx.send("❌ المبلغ يجب أن يكون أكبر من 0")
        return
    
    init_user(user_id, ctx.author.display_name)
    init_user(opponent_id, opponent.display_name)
    
    data = load_data()
    challenger_balance = data[user_id]["balance"].get(currency, 0)
    opponent_balance = data[opponent_id]["balance"].get(currency, 0)
    
    if challenger_balance < amount or opponent_balance < amount:
        await ctx.send(f"❌ أحدكما لا يملك {amount} {currency}!")
        return
    
    class RaceView(View):
        def __init__(self):
            super().__init__(timeout=60)
            self.race_started = False
            self.finish_times = {}
        
        @discord.ui.button(label="🏁 قبول السباق", style=ButtonStyle.success)
        async def accept_race(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذا السباق ليس لك!", ephemeral=True)
                return
            
            self.race_started = True
            
            # بدء العد التنازلي
            await interaction.response.edit_message(
                content="🏁 **استعدوا للسباق!**\n⏰ اضغطوا الزر بأسرع ما يمكن عند ظهور الإشارة!",
                view=None
            )
            
            # انتظار عشوائي
            wait_time = random.uniform(2, 5)
            await asyncio.sleep(wait_time)
            
            # إشارة البدء
            race_button_view = RaceButtonView(self, currency, amount)
            embed = Embed(
                title="🟢 ابدأ الآن!",
                description="🏃‍♂️ اضغط الزر بأسرع ما يمكن!",
                color=0x00ff00
            )
            
            await interaction.edit_original_response(embed=embed, view=race_button_view)
        
        @discord.ui.button(label="❌ رفض السباق", style=ButtonStyle.danger)
        async def decline_race(self, interaction: Interaction, button: Button):
            if interaction.user.id != opponent.id:
                await interaction.response.send_message("❌ هذا السباق ليس لك!", ephemeral=True)
                return
            
            await interaction.response.edit_message(content=f"❌ {opponent.mention} رفض السباق.", view=None)
    
    class RaceButtonView(View):
        def __init__(self, parent_view, currency, amount):
            super().__init__(timeout=10)
            self.parent_view = parent_view
            self.currency = currency
            self.amount = amount
            self.start_time = time.time()
        
        @discord.ui.button(label="🏃‍♂️ اضغط هنا!", style=ButtonStyle.danger)
        async def race_button(self, interaction: Interaction, button: Button):
            user_id = str(interaction.user.id)
            if user_id not in [str(ctx.author.id), str(opponent.id)]:
                await interaction.response.send_message("❌ لست جزءاً من هذا السباق!", ephemeral=True)
                return
            
            if user_id in self.parent_view.finish_times:
                await interaction.response.send_message("❌ لقد ضغطت بالفعل!", ephemeral=True)
                return
            
            finish_time = time.time() - self.start_time
            self.parent_view.finish_times[user_id] = finish_time
            
            await interaction.response.send_message(f"⏱️ وقتك: {finish_time:.3f} ثانية!", ephemeral=True)
            
            # إذا انتهى كلا اللاعبين
            if len(self.parent_view.finish_times) == 2:
                await self.determine_winner(interaction)
        
        async def determine_winner(self, interaction):
            challenger_time = self.parent_view.finish_times.get(str(ctx.author.id))
            opponent_time = self.parent_view.finish_times.get(str(opponent.id))
            
            if challenger_time < opponent_time:
                winner = ctx.author
                winner_time = challenger_time
            else:
                winner = opponent
                winner_time = opponent_time
            
            # تحديث الأرصدة
            data = load_data()
            winner_id = str(winner.id)
            loser_id = str(opponent.id) if winner == ctx.author else str(ctx.author.id)
            
            data[winner_id]["balance"][self.currency] += self.amount
            data[loser_id]["balance"][self.currency] -= self.amount
            save_data(data)
            
            currency_emoji = "💵" if self.currency == "دولار" else "🪙"
            
            embed = Embed(
                title="🏁 نتائج السباق!",
                description=f"🥇 **الفائز: {winner.mention}**\n⏱️ الوقت: **{winner_time:.3f}** ثانية\n\n💰 ربح: {self.amount:,} {currency_emoji} {self.currency}",
                color=0xffd700
            )
            
            embed.add_field(
                name="📊 الأوقات النهائية",
                value=f"🏃‍♂️ {ctx.author.mention}: {challenger_time:.3f}s\n🏃‍♂️ {opponent.mention}: {opponent_time:.3f}s",
                inline=False
            )
            
            # تسجيل النشاط
            logs_system.add_log(
                "game_logs",
                winner_id,
                winner.display_name,
                f"فاز في سباق ضد {ctx.author.display_name if winner == opponent else opponent.display_name}",
                {"game": "race", "time": winner_time, "winnings": self.amount, "currency": self.currency}
            )
            
            await interaction.edit_original_response(embed=embed, view=None)
    
    currency_emoji = "💵" if currency == "دولار" else "🪙"
    embed = Embed(
        title="🏁 دعوة سباق السرعة!",
        description=f"🏃‍♂️ **{ctx.author.mention}** يتحدى **{opponent.mention}** في سباق سرعة!\n\n💰 **المراهنة:** {amount:,} {currency_emoji} {currency}\n🎯 **القواعد:** أسرع من يضغط الزر يفوز!",
        color=0x3498db
    )
    
    await ctx.send(embed=embed, view=RaceView())

# ----------------------------------------- ألعاب تفاعلية -------------------------------------
# لعبة الحجر ورقة مقص
async def handle_rock_paper_scissors_command(message):
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

            # تحديد النتيجة
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

            # إضافة المكافأة
            init_user(user_id, ctx.author.display_name)
            data = load_data()
            data[user_id]["balance"]["دولار"] += reward
            save_data(data)

            embed = discord.Embed(
                title="🎮 حجر ورقة مقص",
                description=f"{emoji} أنت اخترت: **{choice}**\n{bot_emojis[bot_choice]} البوت اختار: **{bot_choice}**\n\n{result}\n💰 ربحت: {reward} دولار",
                color=color
            )

            # تسجيل النشاط
            logs_system.add_log(
                "game_logs",
                user_id,
                ctx.author.display_name,
                "لعب حجر ورقة مقص",
                {"game": "حجر_ورقة_مقص", "result": result, "reward": reward}
            )
            
            # تحديث مهام الألعاب
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

async def handle_guessing_game_command(message):
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
                        if "balance" not in data[user_id]:
                            data[user_id]["balance"] = {}
                        data[user_id]["balance"]["دولار"] = data[user_id]["balance"].get("دولار", 0) + reward
                        save_data(data)
                        update_cooldown(user_id, "تخمين")
                        view.result_text = f"🎉 صحيح! الرقم هو {view.target}.\n💰 ربحت {reward} دولار.\n🏆 محاولات متبقية: {view.attempts_left}"
                        view.game_over = True
                        view.disable_all_items()
                    elif view.attempts_left == 0:
                        reward = 500
                        if "balance" not in data[user_id]:
                            data[user_id]["balance"] = {}
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

        async def on_timeout(self):
            if not self.game_over:
                self.disable_all_items()
                if self.message:
                    embed = discord.Embed(
                        title="⏳ انتهى الوقت",
                        description=f"❌ لم يتم التخمين في الوقت المحدد.\n🔍 الرقم الصحيح كان: {self.target}",
                        color=discord.Color.red()
                    )
                    await self.message.edit(embed=embed, view=self)

    view = GuessingView(ctx.author, secret_number)
    embed = discord.Embed(
        title="🔮 لعبة تخمين الرقم",
        description=f"خمن رقماً بين 1 و 100!\n📉 لديك {max_attempts} محاولة.\n🏆 كلما خمنت أسرع، زادت المكافأة!",
        color=discord.Color.green()
    )
    msg = await ctx.send(embed=embed, view=view)
    view.message = msg

# لعبة الذاكرة
async def handle_memory_game_command(message):
    user_id = str(ctx.author.id)
    can_use, time_left = check_cooldown(user_id, "ذاكرة")
    if not can_use:
        await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
        return

    emojis = ["🍎", "🍌", "🍇", "🍓", "🥝", "🍑", "🥭", "🍍"]
    sequence_length = 4
    sequence = random.sample(emojis, sequence_length)

    class MemoryView(View):
        def __init__(self, show_sequence=True):
            super().__init__(timeout=30)
            self.user_sequence = []
            self.target_sequence = sequence
            self.show_sequence = show_sequence

            if not show_sequence:
                for emoji in emojis:
                    self.add_item(self.MemoryButton(emoji))

        class MemoryButton(Button):
            def __init__(self, emoji):
                super().__init__(emoji=emoji, style=ButtonStyle.secondary)
                self.emoji_value = emoji

            async def callback(self, interaction: Interaction):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                view = self.view
                view.user_sequence.append(self.emoji_value)

                if len(view.user_sequence) == len(view.target_sequence):
                    # تحقق من النتيجة
                    if view.user_sequence == view.target_sequence:
                        reward = 3000
                        init_user(user_id, ctx.author.display_name)
                        data = load_data()
                        data[user_id]["balance"]["دولار"] += reward
                        save_data(data)

                        embed = discord.Embed(
                            title="🧠 ممتاز! ذاكرة رائعة!",
                            description=f"✅ تذكرت التسلسل الصحيح!\n💰 ربحت: {reward} دولار",
                            color=0x00FF00
                        )
                        update_cooldown(user_id, "ذاكرة")
                        await interaction.response.edit_message(embed=embed, view=None)
                    else:
                        reward = 300
                        init_user(user_id, ctx.author.display_name)
                        data = load_data()
                        data[user_id]["balance"]["دولار"] += reward
                        save_data(data)

                        embed = discord.Embed(
                            title="😔 للأسف، تسلسل خاطئ",
                            description=f"❌ التسلسل الصحيح كان: {' '.join(view.target_sequence)}\n💰 مكافأة تشجيعية: {reward} دولار",
                            color=0xFF0000
                        )
                        update_cooldown(user_id, "ذاكرة")
                        await interaction.response.edit_message(embed=embed, view=None)
                else:
                    # استمرار اللعبة
                    current_progress = " ".join(view.user_sequence)
                    embed = discord.Embed(
                        title="🧠 لعبة الذاكرة",
                        description=f"اختياراتك حتى الآن: {current_progress}\nاختر الرمز التالي:",
                        color=0x3498db
                    )
                    await interaction.response.edit_message(embed=embed, view=view)

    # عرض التسلسل أولاً
    sequence_display = " ".join(sequence)
    embed = discord.Embed(
        title="🧠 لعبة الذاكرة",
        description=f"احفظ هذا التسلسل:\n\n**{sequence_display}**\n\nسيختفي خلال 5 ثوان...",
        color=0xE74C3C
    )

    message = await ctx.send(embed=embed)
    await asyncio.sleep(5)

    # إخفاء التسلسل وبدء اللعبة
    embed = discord.Embed(
        title="🧠 لعبة الذاكرة",
        description="الآن أعد ترتيب التسلسل بالضغط على الأزرار:",
        color=0x3498db
    )
    await message.edit(embed=embed, view=MemoryView(False))

# لعبة الرياضيات السريعة
async def handle_math_game_command(message):
    user_id = str(ctx.author.id)
    can_use, time_left = check_cooldown(user_id, "رياضيات")
    if not can_use:
        await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
        return

    # توليد معادلة رياضية عشوائية
    num1 = random.randint(10, 50)
    num2 = random.randint(1, 20)
    operation = random.choice(["+", "-", "*"])

    if operation == "+":
        answer = num1 + num2
        op_symbol = "➕"
    elif operation == "-":
        answer = num1 - num2
        op_symbol = "➖"
    else:  # multiplication
        answer = num1 * num2
        op_symbol = "✖️"

    class MathModal(Modal, title="🧮 حل المعادلة"):
        def __init__(self, correct_answer):
            super().__init__()
            self.correct_answer = correct_answer
            self.answer_input = TextInput(
                label=f"احسب: {num1} {operation} {num2} = ?",
                placeholder="أدخل الإجابة",
                required=True
            )
            self.add_item(self.answer_input)

        async def on_submit(self, interaction: Interaction):
            try:
                user_answer = int(self.answer_input.value)
            except ValueError:
                await interaction.response.send_message("❌ أدخل رقماً صحيحاً!", ephemeral=True)
                return

            if user_answer == self.correct_answer:
                reward = 1500
                init_user(user_id, ctx.author.display_name)
                data = load_data()
                data[user_id]["balance"]["دولار"] += reward
                save_data(data)

                embed = discord.Embed(
                    title="🎯 إجابة صحيحة!",
                    description=f"✅ {num1} {op_symbol} {num2} = {self.correct_answer}\n💰 ربحت: {reward} دولار",
                    color=0x00FF00
                )
                update_cooldown(user_id, "رياضيات")
                await interaction.response.send_message(embed=embed)
            else:
                reward = 200
                init_user(user_id, ctx.author.display_name)
                data = load_data()
                data[user_id]["balance"]["دولار"] += reward
                save_data(data)

                embed = discord.Embed(
                    title="❌ إجابة خاطئة",
                    description=f"الإجابة الصحيحة: {num1} {op_symbol} {num2} = {self.correct_answer}\n💰 مكافأة تشجيعية: {reward} دولار",
                    color=0xFF0000
                )
                update_cooldown(user_id, "رياضيات")
                await interaction.response.send_message(embed=embed)

    class StartMathView(View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="🧮 ابدأ الحل", style=ButtonStyle.primary)
        async def start_math(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                return
            await interaction.response.send_modal(MathModal(answer))

    embed = discord.Embed(
        title="🧮 لعبة الرياضيات السريعة",
        description=f"حل هذه المعادلة بسرعة!\n\n**{num1} {op_symbol} {num2} = ?**",
        color=0x1ABC9C
    )
    await ctx.send(embed=embed, view=StartMathView())

# لعبة الكلمات المبعثرة
async def handle_word_game_command(message):
    user_id = str(ctx.author.id)
    can_use, time_left = check_cooldown(user_id, "كلمات")
    if not can_use:
        await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
        return

    words = [
        "برمجة", "حاسوب", "إنترنت", "تطبيق", "موبايل", 
        "ذكاء", "تقنية", "معلومات", "شبكة", "نظام"
    ]

    original_word = random.choice(words)
    scrambled = list(original_word)
    random.shuffle(scrambled)
    scrambled_word = "".join(scrambled)

    class WordModal(Modal, title="📝 رتب الكلمة"):
        def __init__(self, correct_word):
            super().__init__()
            self.correct_word = correct_word
            self.word_input = TextInput(
                label=f"رتب هذه الأحرف: {scrambled_word}",
                placeholder="أدخل الكلمة الصحيحة",
                required=True
            )
            self.add_item(self.word_input)

        async def on_submit(self, interaction: Interaction):
            user_word = self.word_input.value.strip()

            if user_word == self.correct_word:
                reward = 2500
                init_user(user_id, ctx.author.display_name)
                data = load_data()
                data[user_id]["balance"]["دولار"] += reward
                save_data(data)

                embed = discord.Embed(
                    title="📚 ممتاز! كلمة صحيحة!",
                    description=f"✅ الكلمة الصحيحة: **{self.correct_word}**\n💰 ربحت: {reward} دولار",
                    color=0x00FF00
                )
                update_cooldown(user_id, "كلمات")
                await interaction.response.send_message(embed=embed)
            else:
                reward = 250
                init_user(user_id, ctx.author.display_name)
                data = load_data()
                data[user_id]["balance"]["دولار"] += reward
                save_data(data)

                embed = discord.Embed(
                    title="📖 للأسف، كلمة خاطئة",
                    description=f"❌ الكلمة الصحيحة كانت: **{self.correct_word}**\n💰 مكافأة تشجيعية: {reward} دولار",
                    color=0xFF0000
                )
                update_cooldown(user_id, "كلمات")
                await interaction.response.send_message(embed=embed)

    class StartWordView(View):
        def __init__(self):
            super().__init__(timeout=60)

        @discord.ui.button(label="📝 ابدأ الترتيب", style=ButtonStyle.primary)
        async def start_word(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                return
            await interaction.response.send_modal(WordModal(original_word))

    embed = discord.Embed(
        title="📝 لعبة الكلمات المبعثرة",
        description=f"رتب هذه الأحرف لتكوين كلمة صحيحة:\n\n**{scrambled_word}**",
        color=0xE67E22
    )
    await ctx.send(embed=embed, view=StartWordView())

# ----------------------------------------- أفاصل تداول -------------------------------------
async def handle_trade_command(message):
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "تداول")
        if not can_use:
            await ctx.send(f"⏳ لا يمكنك استخدام الأمر الآن. الرجاء الانتظار {time_left}.")
            return

        await ctx.send("✅ تم تنفيذ الأمر بنجاح.")

        init_user(user_id, ctx.author.display_name)
        data = load_data()
        user = data[user_id]
        balance = user["balance"]["دولار"]

        if balance <= 0:
            await ctx.send("❌ لا يوجد لديك أي دولار للتداول.")
            return

        class TradeView(View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None

            @discord.ui.button(label="ربع الرصيد 💸", style=discord.ButtonStyle.secondary)
            async def quarter(self, interaction: Interaction, button: Button):
                await self.trade_action(interaction, int(balance * 0.25))

            @discord.ui.button(label="نصف الرصيد 💰", style=discord.ButtonStyle.primary)
            async def half(self, interaction: Interaction, button: Button):
                await self.trade_action(interaction, int(balance * 0.5))

            @discord.ui.button(label="ثلاث أرباع 🪙", style=discord.ButtonStyle.primary)
            async def three_quarters(self, interaction: Interaction, button: Button):
                await self.trade_action(interaction, int(balance * 0.75))

            @discord.ui.button(label="كل الرصيد 🤑", style=discord.ButtonStyle.danger)
            async def all_in(self, interaction: Interaction, button: Button):
                await self.trade_action(interaction, balance)

            async def trade_action(self, interaction: Interaction, amount: int):
                nonlocal data, user

                if amount > user["balance"]["دولار"] or amount <= 0:
                    await interaction.response.send_message("❌ مبلغ غير صالح.", ephemeral=True)
                    return

                success = random.random() < 0.6  # 60% نسبة النجاح
                result = 0

                if success:
                    multiplier = random.uniform(1.1, 1.9)
                    result = int(amount * multiplier) - amount
                    user["balance"]["دولار"] += result
                    color = 0x2ecc71
                    status = "✅ نجاح"
                    symbol = "💰 الربح"
                else:
                    multiplier = random.uniform(0.2, 0.95)
                    result = amount - int(amount * multiplier)
                    user["balance"]["دولار"] -= result
                    color = 0xe74c3c
                    status = "❌ فشل"
                    symbol = "🔻 الخسارة"

                save_data(data)

                embed = discord.Embed(title="📈 نتيجة التداول", color=color)
                embed.add_field(name="المبلغ المتداول", value=f"{amount:,} دولار", inline=False)
                embed.add_field(name="الحالة", value=status, inline=False)
                embed.add_field(name=symbol, value=f"{result:,} دولار", inline=False)
                embed.add_field(name="رصيدك الجديد", value=f"{user['balance']['دولار']:,} دولار", inline=False)

                # تسجيل النشاط
                logs_system.add_log(
                    "trade_logs",
                    user_id,
                    ctx.author.display_name,
                    f"تداول {amount:,} دولار",
                    {"amount": amount, "profit": result, "success": success}
                )

                await interaction.response.edit_message(embed=embed, view=None)

        embed = discord.Embed(
            title="💹 التداول في السوق العالمي",
            description=f"💵 رصيدك الحالي: `{balance:,} دولار`\nاختر نسبة التداول أو أرسل مبلغًا يدويًا:",
            color=0x3498db
        )

        await ctx.send(embed=embed, view=TradeView())

    # شركات الاستثمار
INVESTMENT_COMPANIES = [
        "📈 شركة الذهب الدولية",
        "🏦 بنك الاستثمار الآمن",
        "💻 تكنولوجيا المستقبل",
        "🛢️ النفط العالمية",
        "🏗️ شركة البناء الكبرى"
    ]

class AmountInputModal(Modal):
        def __init__(self, view):
            super().__init__(title="أدخل مبلغ الاستثمار")
            self.view_ref = view
            self.amount_input = TextInput(label="المبلغ بالدولار", placeholder="أدخل رقم")
            self.add_item(self.amount_input)

        async def on_submit(self, interaction: Interaction):
            try:
                amount = int(self.amount_input.value.replace(",", "").strip())
                if amount <= 0 or amount > self.view_ref.user_balance:
                    await interaction.response.send_message("❌ المبلغ غير صالح أو أكبر من رصيدك.", ephemeral=True)
                    return
                self.view_ref.amount = amount
                await interaction.response.defer()
                await self.view_ref.update_main_message(interaction)
            except ValueError:
                await interaction.response.send_message("❌ أدخل رقمًا صحيحًا.", ephemeral=True)

class InvestmentView(View):
    def __init__(self, user_id, user_balance):
        super().__init__(timeout=120)
        self.user_id = str(user_id)
        self.user_balance = user_balance
        self.amount = 0
        self.company = None

        # قائمة الشركات للاستثمار
        options = [discord.SelectOption(label=comp) for comp in INVESTMENT_COMPANIES]
        self.select_menu = Select(
            placeholder="اختر الشركة للاستثمار فيها",
            options=options,
            custom_id="select_company"
        )
        self.select_menu.callback = self.select_company
        self.add_item(self.select_menu)

    async def select_company(self, interaction: Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        self.company = self.select_menu.values[0]
        await interaction.response.defer()
        # تحديث الرسالة بدلاً من إرسال رسالة جديدة
        await self.update_main_message(interaction)

    @discord.ui.button(label="💰 كل الرصيد", style=ButtonStyle.gray)
    async def all_balance(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        self.amount = self.user_balance
        await interaction.response.defer()
        await self.update_main_message(interaction)

    @discord.ui.button(label="💵 نصف الرصيد", style=ButtonStyle.gray)
    async def half_balance(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        self.amount = self.user_balance // 2
        await interaction.response.defer()
        await self.update_main_message(interaction)

    @discord.ui.button(label="💳 ربع الرصيد", style=ButtonStyle.gray)
    async def quarter_balance(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        self.amount = self.user_balance // 4
        await interaction.response.defer()
        await self.update_main_message(interaction)

    @discord.ui.button(label="✍️ أدخل مبلغ يدوي", style=ButtonStyle.secondary)
    async def manual_amount(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        modal = AmountInputModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="✅ استثمر الآن", style=ButtonStyle.green)
    async def confirm_investment(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ ليس لك الحق في استخدام هذه الأزرار.", ephemeral=True)
            return
        if not self.company:
            await interaction.response.send_message("❗️ يرجى اختيار الشركة أولاً.", ephemeral=True)
            return
        if self.amount <= 0:
            await interaction.response.send_message("❗️ يرجى تحديد مبلغ الاستثمار أولاً.", ephemeral=True)
            return
        await self.process_investment(interaction)

    async def update_main_message(self, interaction: Interaction):
        """تحديث الرسالة الرئيسية بدلاً من إنشاء نوافذ جديدة"""
        embed = discord.Embed(
            title="💼 اختر الشركة والمبلغ للاستثمار",
            description=f"💵 رصيدك الحالي: **{self.user_balance:,} دولار**",
            color=0x3498db
        )
        
        if self.company:
            embed.add_field(name="🏢 الشركة المختارة", value=self.company, inline=True)
        
        if self.amount > 0:
            embed.add_field(name="💰 المبلغ المحدد", value=f"{self.amount:,} دولار", inline=True)
        
        if self.company and self.amount > 0:
            embed.add_field(name="✅ جاهز للاستثمار", value="اضغط 'استثمر الآن' لتأكيد العملية", inline=False)
        
        await interaction.edit_original_response(embed=embed, view=self)

    async def process_investment(self, interaction: Interaction):
        percent = random.randint(-40, 50)
        success = percent >= 0
        result_amount = int(self.amount * (1 + (percent / 100)))

        data = load_data()
        user = data[self.user_id]
        old_balance = user["balance"]["دولار"]
        user["balance"]["دولار"] = old_balance - self.amount + result_amount
        save_data(data)

        embed = discord.Embed(
            title="📊 نتائج الاستثمار",
            color=0x2ecc71 if success else 0xe74c3c
        )
        embed.add_field(name="🏢 الشركة", value=self.company, inline=True)
        embed.add_field(name="💸 المبلغ المستثمر", value=f"{self.amount:,} دولار", inline=True)
        embed.add_field(name="📊 نسبة الربح/الخسارة", value=f"{percent:+}%", inline=True)
        embed.add_field(name="💰 الرصيد السابق", value=f"{old_balance:,} دولار", inline=True)
        embed.add_field(name="💼 الرصيد الجديد", value=f"{user['balance']['دولار']:,} دولار", inline=True)

        await interaction.response.edit_message(embed=embed, view=None)
# الأمر الرئيسي
async def handle_invest_command(message):
    user_id = str(ctx.author.id)

    can_use, time_left = check_cooldown(user_id, "استثمار")
    if not can_use:
        await ctx.send(f"⏳ لا يمكنك استخدام الأمر الآن. الرجاء الانتظار {time_left}.")
        return


    init_user(user_id, ctx.author.display_name)
    data = load_data()
    user = data.get(user_id)
    if user is None:
        await ctx.send("❌ لم يتم العثور على بيانات المستخدم.")
        return

    balance = user.get("balance", {}).get("دولار", 0)

    if balance < 100:
        await ctx.send("❌ لا يمكنك الاستثمار بأقل من 100 دولار.")
        return

    view = InvestmentView(user_id, balance)
    message = await ctx.send(
        f"💼 اختر الشركة والمبلغ للاستثمار يا {ctx.author.mention}\n"
        f"💵 رصيدك الحالي: **{balance:,} دولار**",
        view=view
    )
    view.message = message


# ========== أوامر السجلات وقوائم الترتيب ==========

async def handle_leaderboards_command(message):
    """عرض قوائم الترتيب لأفضل اللاعبين"""
    embed = Embed(
        title="🏆 قوائم الترتيب",
        description="اختر نوع القائمة التي تريد عرضها:",
        color=0xf39c12
    )

    view = LeaderboardView(bot, ctx.guild)
    await ctx.send(embed=embed, view=view)

async def handle_logs_command_command(message):
    """عرض السجلات والأنشطة"""
    user_id = str(ctx.author.id)

    embed = Embed(
        title="📊 السجلات والأنشطة",
        description="اختر نوع السجلات التي تريد عرضها:",
        color=0x3498db
    )

    view = LogsView(bot, user_id)
    await ctx.send(embed=embed, view=view)

async def handle_stats_command_command(message):
    """عرض إحصائيات عامة للنظام"""
    data = load_data()
    logs = logs_system.load_logs()

    # حساب الإحصائيات
    total_users = len(data)
    total_wealth = sum(
        (user.get("balance", {}).get("دولار", 0) if isinstance(user.get("balance"), dict) 
         else user.get("balance", 0) if isinstance(user.get("balance"), int) else 0)
        for user in data.values()
    )

    total_thefts = len(logs.get("theft_logs", []))
    total_trades = len(logs.get("trade_logs", []))
    total_work_days = len(logs.get("work_logs", []))
    total_games = len(logs.get("game_logs", []))
    total_farms = len(logs.get("farm_logs", []))

    embed = Embed(
        title="📊 إحصائيات النظام العامة",
        color=0x2c3e50
    )

    embed.add_field(
        name="👥 المستخدمين",
        value=f"إجمالي المستخدمين: **{total_users:,}**",
        inline=False
    )

    embed.add_field(
        name="💰 الاقتصاد",
        value=f"إجمالي الثروة: **{total_wealth:,}** دولار\nعمليات التداول: **{total_trades:,}**",
        inline=True
    )

    embed.add_field(
        name="⚔️ النشاطات",
        value=f"عمليات النهب: **{total_thefts:,}**\nأيام العمل: **{total_work_days:,}**",
        inline=True
    )

    embed.add_field(
        name="🎮 الترفيه",
        value=f"الألعاب المُلعبة: **{total_games:,}**\nعمليات الزراعة: **{total_farms:,}**",
        inline=True
    )

    await ctx.send(embed=embed)

async def handle_my_activities_command(message):
    """عرض آخر أنشطة المستخدم"""
    user_id = str(ctx.author.id)
    user_logs = logs_system.get_user_logs(user_id, limit=15)

    if not user_logs:
        await ctx.send("📭 لا توجد أنشطة مسجلة لك حتى الآن.")
        return

    embed = Embed(
        title=f"📋 آخر أنشطتك يا {ctx.author.display_name}",
        color=0x3498db
    )

    description = ""
    for i, log in enumerate(user_logs[:10], 1):
        time_obj = datetime.fromisoformat(log["timestamp"])
        time_str = time_obj.strftime("%m/%d %H:%M")
        description += f"**{i}.** 🕒 {time_str} - {log['action']}\n"

    embed.description = description
    embed.set_footer(text=f"إجمالي الأنشطة: {len(user_logs)}")

    await ctx.send(embed=embed)

async def handle_delete_account_command(message):
    user_id = str(ctx.author.id)
    data = load_data()

    if user_id not in data:
        await ctx.send("❌ لا يوجد لديك حساب لحذفه.")
        return

    del data[user_id]  # نحذف الحساب بالكامل
    save_data(data)

    await ctx.send("🗑️ تم حذف حسابك بنجاح. يمكنك البدء من جديد في أي وقت باستخدام أحد الأوامر.")

async def handle_admin_give_command(message):
    """أمر خاص بالمسؤول لإعطاء العملات"""
    # التحقق من أن المستخدم هو المسؤول
    if str(ctx.author.id) != "597118308118036491":
        await ctx.send("❌ هذا الأمر مخصص للمسؤول فقط!")
        return
    
    # التحقق من صحة العملة
    valid_currencies = ["دولار", "ذهب", "ماس"]
    if currency not in valid_currencies:
        await ctx.send(f"❌ العملة غير صحيحة. استخدم: {', '.join(valid_currencies)}")
        return
    
    if amount <= 0:
        await ctx.send("❌ المبلغ يجب أن يكون أكبر من 0")
        return
    
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    data = load_data()
    
    # إضافة العملة
    data[user_id]["balance"][currency] = data[user_id]["balance"].get(currency, 0) + amount
    save_data(data)
    
    # رسالة التأكيد
    currency_emojis = {"دولار": "💵", "ذهب": "🪙", "ماس": "💎"}
    emoji = currency_emojis.get(currency, "💰")
    
    embed = discord.Embed(
        title="👑 أمر المسؤول - تم بنجاح",
        description=f"✅ تم إضافة **{amount:,}** {emoji} {currency} إلى حسابك",
        color=0xffd700
    )
    
    embed.add_field(
        name="💰 رصيدك الجديد",
        value=f"{emoji} {data[user_id]['balance'][currency]:,} {currency}",
        inline=True
    )
    
    await ctx.send(embed=embed)

# ================================= نظام السراديب المتقدم =================================

async def handle_dungeons_command_command(message):
    """عرض قائمة السراديب المتاحة"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    # التحقق من وجود اختصاص
    data = load_data()
    user = data[user_id]
    specialization = user.get("specialization")
    
    if not specialization:
        await ctx.send("❌ يجب عليك اختيار اختصاص أولاً باستخدام الأمر `اختصاص`!")
        return
    
    # جلب تقدم المستخدم
    progress = get_user_dungeon_progress(user_id)
    
    class DungeonsView(View):
        def __init__(self):
            super().__init__(timeout=120)
            
            # إضافة أزرار السراديب
            for dungeon_name, dungeon_info in DUNGEONS.items():
                self.add_item(DungeonButton(dungeon_name, dungeon_info))

    class DungeonButton(Button):
        def __init__(self, dungeon_name, dungeon_info):
            # تحديد لون الزر حسب المستوى
            colors = {1: ButtonStyle.secondary, 2: ButtonStyle.primary, 3: ButtonStyle.success, 4: ButtonStyle.danger, 5: ButtonStyle.success}
            style = colors.get(dungeon_info["level"], ButtonStyle.secondary)
            
            super().__init__(
                label=f"مستوى {dungeon_info['level']} - {dungeon_name[2:]}",
                style=style,
                emoji=dungeon_name[0]
            )
            self.dungeon_name = dungeon_name
            self.dungeon_info = dungeon_info

        async def callback(self, interaction: Interaction):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            # فحص إمكانية الدخول
            can_enter, message = can_enter_dungeon(user_id, self.dungeon_name)
            
            embed = Embed(
                title=f"🏰 {self.dungeon_name}",
                description=self.dungeon_info["description"],
                color=0x8b0000 if not can_enter else 0x228b22
            )
            
            embed.add_field(
                name="👹 الزعيم",
                value=f"{self.dungeon_info['boss']}\n💀 الصحة: {self.dungeon_info['boss_hp']}\n⚔️ الهجوم: {self.dungeon_info['boss_attack']}\n🛡️ الدفاع: {self.dungeon_info['boss_defense']}",
                inline=True
            )
            
            embed.add_field(
                name="💎 تكلفة الدخول",
                value=f"{self.dungeon_info['entry_cost']['ماس']} ماس",
                inline=True
            )
            
            # عرض المكافآت
            rewards = self.dungeon_info["rewards"]
            rewards_text = f"🪙 ذهب: {rewards['ذهب'][0]}-{rewards['ذهب'][1]}\n💵 دولار: {rewards['دولار'][0]:,}-{rewards['دولار'][1]:,}\n💎 عناصر نادرة محتملة"
            
            embed.add_field(
                name="🎁 المكافآت",
                value=rewards_text,
                inline=False
            )
            
            embed.add_field(
                name="🎯 حالة الدخول",
                value=message,
                inline=False
            )
            
            # زر الدخول
            view = EnterDungeonView(self.dungeon_name, can_enter) if can_enter else None
            
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    class EnterDungeonView(View):
        def __init__(self, dungeon_name, can_enter):
            super().__init__(timeout=60)
            self.dungeon_name = dungeon_name
            self.can_enter = can_enter

        @discord.ui.button(label="⚔️ دخول السرداب", style=ButtonStyle.danger)
        async def enter_dungeon(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            # تنفيذ دخول السرداب مع نظام التبريد المحسن
            await interaction.response.defer()
            
            # فحص شامل للشروط
            can_enter, message = can_enter_dungeon(user_id, self.dungeon_name)
            if not can_enter:
                await interaction.followup.send(f"🚫 {message}")
                return
            
            # فحص تكلفة الدخول مرة أخرى
            data = load_data()
            user = data[user_id]
            required_diamonds = DUNGEONS[self.dungeon_name]["entry_cost"]["ماس"]
            
            if user["balance"].get("ماس", 0) < required_diamonds:
                await interaction.followup.send(f"❌ تحتاج إلى {required_diamonds} ماس لدخول هذا السرداب!")
                return
            
            # خصم التكلفة وتطبيق تبريد الدخول
            user["balance"]["ماس"] -= required_diamonds
            update_dungeon_cooldown(user_id, "entry")
            
            # جلب العتاد والإحصائيات
            equipment = get_user_equipment(user_id)
            player_stats = calculate_combat_stats(user, equipment)
            player_stats["user_id"] = user_id  # إضافة معرف المستخدم للإحصائيات
            
            # رسالة بدء المعركة
            dungeon_info = DUNGEONS[self.dungeon_name]
            start_embed = Embed(
                title="⚔️ بدء المعركة!",
                description=f"🏰 دخلت إلى **{self.dungeon_name}**\n👹 تواجه: **{dungeon_info['boss']}**\n⏱️ الوقت المتوقع: {dungeon_info.get('estimated_time', 'غير محدد')}",
                color=0x8b0000
            )
            await interaction.followup.send(embed=start_embed)
            
            # بدء المعركة
            victory, battle_log, rewards = simulate_dungeon_battle(player_stats, self.dungeon_name)
            
            # تطبيق التبريد حسب النتيجة
            if victory:
                update_dungeon_cooldown(user_id, "boss_defeat", self.dungeon_name)
            else:
                update_dungeon_cooldown(user_id, "death_penalty")
            
            # تطبيق المكافآت المحسنة
            if victory and rewards:
                user["balance"]["ذهب"] = user["balance"].get("ذهب", 0) + rewards.get("ذهب", 0)
                user["balance"]["دولار"] = user["balance"].get("دولار", 0) + rewards.get("دولار", 0)
                
                # إضافة الخبرة
                user["experience"] = user.get("experience", 0) + rewards.get("experience", 0)
                
                # إضافة الماس إن وجد
                if "ماس" in rewards:
                    user["balance"]["ماس"] = user["balance"].get("ماس", 0) + rewards["ماس"]
                
                # إضافة العناصر النادرة
                if "rare_items" in rewards:
                    user.setdefault("حقيبة", []).extend(rewards["rare_items"])
            
            save_data(data)
            
            # تحديث التقدم
            update_user_dungeon_progress(user_id, self.dungeon_name, victory)
            
            # إرسال تقرير المعركة المحسن
            battle_report = "\n".join(battle_log)
            
            # إنشاء تقرير نهائي جميل
            result_embed = Embed(
                title="📋 تقرير المعركة",
                description=f"⚔️ **السرداب:** {self.dungeon_name}\n👹 **الزعيم:** {dungeon_info['boss']}",
                color=0x00ff00 if victory else 0xff0000
            )
            
            if victory:
                result_embed.add_field(
                    name="🎉 النتيجة",
                    value="✅ **انتصار ساحق!**",
                    inline=False
                )
                if rewards:
                    rewards_text = ""
                    if rewards.get("ذهب"):
                        rewards_text += f"🪙 {rewards['ذهب']} ذهب\n"
                    if rewards.get("دولار"):
                        rewards_text += f"💵 {rewards['دولار']:,} دولار\n"
                    if rewards.get("experience"):
                        rewards_text += f"⭐ {rewards['experience']} خبرة\n"
                    if rewards.get("ماس"):
                        rewards_text += f"💎 {rewards['ماس']} ماس\n"
                    
                    result_embed.add_field(
                        name="🎁 المكافآت",
                        value=rewards_text.strip(),
                        inline=True
                    )
            else:
                result_embed.add_field(
                    name="💀 النتيجة",
                    value="❌ **هزيمة مؤلمة**\n⏳ عقوبة 15 دقيقة",
                    inline=False
                )
            
            # تقسيم الرسالة إذا كانت طويلة
            if len(battle_report) > 1500:
                chunks = [battle_report[i:i+1500] for i in range(0, len(battle_report), 1500)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await ctx.send(f"```ansi\n{chunk}\n```")
                    else:
                        await ctx.send(f"```ansi\n{chunk}\n```")
            else:
                await ctx.send(f"```ansi\n{battle_report}\n```")
            
            # إرسال التقرير النهائي
            await ctx.send(embed=result_embed)

    embed = Embed(
        title="🏰 عالم السراديب المظلمة",
        description="🗡️ **مرحباً أيها المحارب!**\n\nاختر سرداباً لتخوض معركة ملحمية ضد زعمائه الأقوياء!\n\n⚠️ **تحذير:** كل سرداب له زعيم مختلف وتحديات فريدة!",
        color=0x8b0000
    )
    
    # معلومات الاختصاص
    spec_info = SPECIALIZATION_BONUSES.get(specialization.get("type", "محارب"))
    embed.add_field(
        name=f"🎯 اختصاصك: {specialization.get('type', 'محارب')}",
        value=f"🔹 {spec_info['special_ability']}\n🔹 {spec_info['dungeon_bonus']}",
        inline=False
    )
    
    # إحصائيات المستخدم
    embed.add_field(
        name="📊 إحصائياتك",
        value=f"🏆 انتصارات: {progress['total_victories']}\n💀 هزائم: {progress['total_defeats']}\n🏰 سراديب مكتملة: {len(progress['completed_dungeons'])}",
        inline=True
    )
    
    await ctx.send(embed=embed, view=DungeonsView())

async def handle_equipment_command_command(message):
    """عرض متجر العتاد ومعدات المستخدم"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    data = load_data()
    user = data[user_id]
    diamonds = user["balance"].get("ماس", 0)
    
    # جلب عتاد المستخدم الحالي
    equipment = get_user_equipment(user_id)
    
    class EquipmentView(View):
        def __init__(self):
            super().__init__(timeout=120)

        @discord.ui.button(label="🛒 متجر العتاد", style=ButtonStyle.primary)
        async def equipment_shop(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            class ShopView(View):
                def __init__(self):
                    super().__init__(timeout=120)
                    
                    # تجميع العتاد حسب النوع
                    weapons = {k: v for k, v in EQUIPMENT_SHOP.items() if v["type"] == "weapon"}
                    armors = {k: v for k, v in EQUIPMENT_SHOP.items() if v["type"] == "armor"}
                    others = {k: v for k, v in EQUIPMENT_SHOP.items() if v["type"] not in ["weapon", "armor"]}
                    
                    self.add_item(ShopSelect("⚔️ الأسلحة", weapons))
                    self.add_item(ShopSelect("🛡️ الدروع", armors))
                    self.add_item(ShopSelect("🎯 معدات أخرى", others))

            class ShopSelect(Select):
                def __init__(self, category, items):
                    self.items_dict = items
                    options = []
                    
                    for name, info in items.items():
                        price_text = f"{info['price']['ماس']} ماس"
                        options.append(discord.SelectOption(
                            label=name[:50],
                            description=f"{price_text} - {info['description'][:50]}",
                            value=name
                        ))
                    
                    super().__init__(placeholder=f"اختر من {category}", options=options[:25])

                async def callback(self, interaction: Interaction):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                        return

                    item_name = self.values[0]
                    item_info = self.items_dict[item_name]
                    price = item_info["price"]["ماس"]
                    
                    if diamonds < price:
                        await interaction.response.send_message(
                            f"❌ لا تملك ما يكفي من الماس!\nتحتاج: {price} ماس | لديك: {diamonds} ماس",
                            ephemeral=True
                        )
                        return

                    class BuyConfirmView(View):
                        def __init__(self):
                            super().__init__(timeout=30)

                        @discord.ui.button(label="✅ شراء", style=ButtonStyle.success)
                        async def confirm_buy(self, buy_interaction: Interaction, button: Button):
                            if buy_interaction.user.id != ctx.author.id:
                                await buy_interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                                return

                            # تنفيذ الشراء
                            data = load_data()
                            user = data[user_id]
                            
                            if user["balance"].get("ماس", 0) < price:
                                await buy_interaction.response.send_message("❌ لا تملك ما يكفي من الماس!", ephemeral=True)
                                return
                            
                            user["balance"]["ماس"] -= price
                            
                            # إضافة العنصر حسب نوعه
                            if item_info["type"] == "consumable":
                                user.setdefault("حقيبة", []).append(item_name)
                            else:
                                # إضافة للعتاد
                                equipment_data = load_equipment_data()
                                user_equipment = equipment_data.get(str(user_id), {
                                    "weapon": None, "armor": None, "helmet": None, "ring": None, "consumables": []
                                })
                                
                                # إلغاء العنصر السابق من نفس النوع
                                old_item = user_equipment.get(item_info["type"])
                                if old_item:
                                    user.setdefault("حقيبة", []).append(old_item)
                                
                                user_equipment[item_info["type"]] = item_name
                                equipment_data[str(user_id)] = user_equipment
                                save_equipment_data(equipment_data)
                            
                            save_data(data)
                            
                            await buy_interaction.response.send_message(
                                f"✅ تم شراء {item_name} بنجاح!\n💎 الماس المتبقي: {user['balance']['ماس']}",
                                ephemeral=True
                            )

                        @discord.ui.button(label="❌ إلغاء", style=ButtonStyle.danger)
                        async def cancel_buy(self, buy_interaction: Interaction, button: Button):
                            await buy_interaction.response.edit_message(content="❌ تم إلغاء عملية الشراء.", view=None)

                    embed = Embed(
                        title=f"🛒 شراء {item_name}",
                        description=f"📝 {item_info['description']}\n\n💎 السعر: **{price} ماس**\n💎 لديك: **{diamonds} ماس**",
                        color=0x00ff00 if diamonds >= price else 0xff0000
                    )
                    
                    if item_info["type"] != "consumable":
                        stats_text = f"⚔️ الهجوم: +{item_info.get('attack', 0)}\n🛡️ الدفاع: +{item_info.get('defense', 0)}"
                        embed.add_field(name="📊 الإحصائيات", value=stats_text, inline=True)

                    await interaction.response.send_message(embed=embed, view=BuyConfirmView(), ephemeral=True)

            await interaction.response.send_message("🛒 **متجر العتاد الأسطوري**\nاختر فئة العتاد:", view=ShopView(), ephemeral=True)

        @discord.ui.button(label="⚔️ عتادي الحالي", style=ButtonStyle.secondary)
        async def my_equipment(self, interaction: Interaction, button: Button):
            if interaction.user.id != ctx.author.id:
                await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
                return

            # حساب الإحصائيات الحالية
            stats = calculate_combat_stats(user, equipment)
            
            embed = Embed(
                title="⚔️ عتادك الحالي",
                color=0x4169e1
            )
            
            # عرض العتاد المُجهز
            equipment_text = ""
            for slot, item in equipment.items():
                if slot != "consumables":
                    if item:
                        equipment_text += f"🔹 **{slot.title()}:** {item}\n"
                    else:
                        equipment_text += f"🔸 **{slot.title()}:** لا يوجد\n"
            
            embed.add_field(name="🎒 العتاد المُجهز", value=equipment_text or "لا يوجد عتاد", inline=False)
            
            # عرض الإحصائيات
            embed.add_field(
                name="📊 إحصائياتك القتالية",
                value=f"❤️ الصحة: {stats['hp']}\n⚔️ الهجوم: {stats['attack']}\n🛡️ الدفاع: {stats['defense']}",
                inline=True
            )
            
            embed.add_field(
                name="🎯 اختصاصك",
                value=f"**{stats['specialization']}** (رتبة {stats['rank']})",
                inline=True
            )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    embed = Embed(
        title="⚔️ مخزن العتاد الأسطوري",
        description="🛡️ **مرحباً أيها المحارب!**\n\nهنا يمكنك شراء أقوى المعدات والأسلحة لتحسين قدراتك القتالية!\n\n💎 جميع الأسعار بالماس فقط - العملة الأثمن في المملكة!",
        color=0x4169e1
    )
    
    embed.add_field(
        name="💎 رصيد الماس",
        value=f"**{diamonds}** ماس",
        inline=True
    )
    
    # عرض العتاد الحالي المُجهز
    equipped_count = sum(1 for item in equipment.values() if item and isinstance(item, str))
    embed.add_field(
        name="⚔️ العتاد المُجهز",
        value=f"**{equipped_count}** قطعة",
        inline=True
    )

    await ctx.send(embed=embed, view=EquipmentView())

async def handle_dungeon_cooldowns_command(message):
    """عرض حالة تبريد السراديب للمستخدم"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    cooldowns = load_dungeon_cooldowns()
    user_cooldowns = cooldowns.get(str(user_id), {})
    current_time = time.time()
    
    embed = Embed(
        title="⏳ حالة تبريد السراديب",
        description="📊 معلومات تفصيلية عن أوقات التبريد الخاصة بك:",
        color=0x3498db
    )
    
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )
    
    # فحص التبريد العام
    entry_time = user_cooldowns.get("entry", 0)
    entry_remaining = DUNGEON_COOLDOWNS["entry"] - (current_time - entry_time)
    
    if entry_remaining > 0:
        entry_status = f"🔴 {format_cooldown_time(entry_remaining)}"
    else:
        entry_status = "🟢 متاح الآن"
    
    embed.add_field(
        name="🚪 تبريد الدخول العام",
        value=entry_status,
        inline=True
    )
    
    # فحص عقوبة الموت
    death_time = user_cooldowns.get("death_penalty", 0)
    death_remaining = DUNGEON_COOLDOWNS["death_penalty"] - (current_time - death_time)
    
    if death_remaining > 0:
        death_status = f"💀 {format_cooldown_time(death_remaining)}"
    else:
        death_status = "🟢 لا توجد عقوبة"
    
    embed.add_field(
        name="💀 عقوبة الهزيمة",
        value=death_status,
        inline=True
    )
    
    # فحص تبريد الزعماء
    boss_cooldowns = []
    for key, timestamp in user_cooldowns.items():
        if key.startswith("boss_defeat_"):
            dungeon_name = key.replace("boss_defeat_", "")
            remaining = DUNGEON_COOLDOWNS["boss_defeat"] - (current_time - timestamp)
            if remaining > 0:
                boss_cooldowns.append(f"👹 {dungeon_name}: {format_cooldown_time(remaining)}")
    
    if boss_cooldowns:
        embed.add_field(
            name="👹 تبريد الزعماء",
            value="\n".join(boss_cooldowns[:5]),  # أول 5 فقط
            inline=False
        )
    else:
        embed.add_field(
            name="👹 تبريد الزعماء",
            value="🟢 جميع الزعماء متاحون",
            inline=False
        )
    
    # المحاولات اليومية
    progress = get_user_dungeon_progress(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    daily_attempts = progress["daily_attempts"].get(today, 0)
    
    embed.add_field(
        name="📅 المحاولات اليومية",
        value=f"📊 العادية: {daily_attempts}/5\n📊 الأسطورية: {min(daily_attempts, 3)}/3",
        inline=True
    )
    
    embed.set_footer(text="💡 التبريد يساعد في توازن اللعبة ويجعل كل معركة مميزة!")
    
    await ctx.send(embed=embed)

async def handle_dungeon_stats_command(message):
    """عرض إحصائيات السراديب للمستخدم"""
    user_id = str(ctx.author.id)
    init_user(user_id, ctx.author.display_name)
    
    progress = get_user_dungeon_progress(user_id)
    data = load_data()
    user = data[user_id]
    equipment = get_user_equipment(user_id)
    stats = calculate_combat_stats(user, equipment)
    
    embed = Embed(
        title="📊 إحصائيات السراديب",
        description=f"📈 تقرير مفصل عن إنجازاتك في عالم السراديب",
        color=0x8b0000
    )
    
    embed.set_author(
        name=ctx.author.display_name,
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )
    
    # إحصائيات المعارك
    total_battles = progress["total_victories"] + progress["total_defeats"]
    win_rate = (progress["total_victories"] / total_battles * 100) if total_battles > 0 else 0
    
    embed.add_field(
        name="⚔️ سجل المعارك",
        value=f"🏆 انتصارات: **{progress['total_victories']}**\n💀 هزائم: **{progress['total_defeats']}**\n📊 معدل الفوز: **{win_rate:.1f}%**",
        inline=True
    )
    
    # السراديب المكتملة
    completed_names = [d.split()[1] if len(d.split()) > 1 else d for d in progress['completed_dungeons']]
    completed_text = "\n".join([f"✅ {name}" for name in completed_names[:5]])
    if len(progress['completed_dungeons']) > 5:
        completed_text += f"\n... و {len(progress['completed_dungeons']) - 5} أخرى"
    
    embed.add_field(
        name="🏰 السراديب المكتملة",
        value=completed_text or "❌ لم تكمل أي سرداب بعد",
        inline=True
    )
    
    # الإحصائيات القتالية الحالية
    embed.add_field(
        name="📊 قدراتك القتالية",
        value=f"❤️ الصحة: **{stats['hp']}**\n⚔️ الهجوم: **{stats['attack']}**\n🛡️ الدفاع: **{stats['defense']}**",
        inline=True
    )
    
    # المحاولات اليومية
    today = datetime.now().strftime("%Y-%m-%d")
    today_attempts = progress["daily_attempts"].get(today, 0)
    embed.add_field(
        name="📅 المحاولات اليوم",
        value=f"🎯 استخدمت: **{today_attempts}/3**\n⏰ متبقي: **{3 - today_attempts}**",
        inline=True
    )
    
    # تقييم الأداء
    if win_rate >= 80:
        performance = "🌟 أسطوري"
        performance_color = 0xffd700
    elif win_rate >= 60:
        performance = "💎 ممتاز"
        performance_color = 0x1e90ff
    elif win_rate >= 40:
        performance = "🥈 جيد"
        performance_color = 0x32cd32
    else:
        performance = "🥉 مبتدئ"
        performance_color = 0xff6347
    
    embed.add_field(
        name="🏅 تقييم الأداء",
        value=performance,
        inline=True
    )
    
    embed.color = performance_color
    
    # نصائح للتحسين
    tips = []
    if stats['attack'] < 200:
        tips.append("⚔️ حسّن أسلحتك لزيادة الهجوم")
    if stats['defense'] < 150:
        tips.append("🛡️ اشتر دروعاً أقوى للحماية")
    if win_rate < 50:
        tips.append("💡 جرب السراديب الأسهل أولاً")
    
    if tips:
        embed.add_field(
            name="💡 نصائح للتحسين",
            value="\n".join(tips),
            inline=False
        )
    
    await ctx.send(embed=embed)



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
    elif content == "صيد":
        await handle_fishing_command(message)
        return
    elif content == "صياد":
        await handle_fisher_shop_command(message)
        return
    elif content == "حوض":
        await handle_pond_command(message)
        return
    elif content == "مزارع":
        await handle_farm_shop_command(message)
        return
    elif content == "زرع":
        await handle_plant_seed_command(message)
        return
    elif content == "مزرعة":
        await handle_farm_status_command(message)
        return
    elif content == "مهام":
        await handle_tasks_command(message)
        return
    elif content.startswith("تحويل"):
        await handle_transfer_command(message)
        return

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


# -------------------------- تشغيل البوت --------------------------

# فحص وجود الرمز المميز
discord_token = os.getenv('DISCORD_TOKEN')
if not discord_token:
    print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")
    print("💡 تأكد من إضافة الرمز المميز في تبويب Secrets")
    exit(1)

