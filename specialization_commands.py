
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button
import time
from datetime import datetime, timedelta

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown

# بيانات الاختصاصات
ranks = ["نبيل", "شجاع", "فارسي", "أسطوري"]

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
        "description": "قاتل في الظلال يتحرك بصمت ويضرب بسرعة البرق قبل أن يختفي",
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

def setup_specialization_commands(bot):
    """إعداد أوامر الاختصاصات"""
    
    @bot.command(name="اختصاص")
    async def choose_or_upgrade_role(ctx):
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

        # باقي الكود للاختصاص الموجود...
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
