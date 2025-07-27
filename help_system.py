import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select, Modal, TextInput
import json
import time

class AdvancedHelpSystem:
    def __init__(self, bot):
        self.bot = bot
        self.help_categories = {
            "اقتصاد": {
                "emoji": "💰",
                "commands": ["رصيد", "يومي", "عمل", "ترقية", "تداول", "استثمار"],
                "description": "أوامر إدارة الأموال والعملات"
            },
            "متجر": {
                "emoji": "🛒",
                "commands": ["متجر", "شراء", "بيع", "حقيبة"],
                "description": "نظام المتجر والتسوق"
            },
            "قتال": {
                "emoji": "⚔️",
                "commands": ["اختصاص", "نهب", "انتقام", "حماية", "درع", "تحدي", "مبارزة"],
                "description": "أنظمة القتال والاختصاصات"
            },
            "ألعاب": {
                "emoji": "🎮",
                "commands": ["حجر_ورقة_مقص", "تخمين", "ذاكرة", "رياضيات", "كلمات"],
                "description": "الألعاب التفاعلية والترفيه"
            },
            "زراعة": {
                "emoji": "🌾",
                "commands": ["مزارع", "زرع", "مزرعة"],
                "description": "نظام الزراعة والمحاصيل"
            },
            "صيد": {
                "emoji": "🎣",
                "commands": ["صياد", "صيد", "حوض"],
                "description": "نظام الصيد وتربية الأسماك"
            },
            "سراديب": {
                "emoji": "🏰",
                "commands": ["سراديب", "عتاد", "تبريد_سراديب"],
                "description": "عالم السراديب والمعارك الملحمية"
            },
            "مهام": {
                "emoji": "🎯",
                "commands": ["مهام", "مستوى", "خبرة", "مكافآت"],
                "description": "نظام المهام ونقاط الخبرة"
            },
            "إحصائيات": {
                "emoji": "📊",
                "commands": ["قوائم", "سجلات", "إحصائيات", "أنشطتي", "ثروة"],
                "description": "السجلات والإحصائيات"
            }
        }

    def create_main_help_embed(self):
        """إنشاء الصفحة الرئيسية للمساعدة"""
        embed = Embed(
            title="📚 مركز المساعدة الشامل",
            description="🎮 **مرحباً بك في دليل نظام NOVA BANK الكامل!**\n\nاختر فئة من الأسفل للحصول على معلومات مفصلة:",
            color=0x3498db
        )

        # إضافة معلومات عامة
        embed.add_field(
            name="🌟 نظرة عامة",
            value="هذا نظام اقتصادي متطور يحتوي على:\n• 3 عملات مختلفة\n• 4 اختصاصات قتالية\n• 7 سراديب أسطورية\n• أنظمة زراعة وصيد\n• ألعاب تفاعلية متنوعة",
            inline=False
        )

        embed.add_field(
            name="🚀 للمبتدئين",
            value="1. ابدأ بالأمر `يومي` للحصول على رصيد أولي\n2. اختر اختصاصك بـ `اختصاص`\n3. اعمل بانتظام بـ `عمل`\n4. تسوق من `متجر`",
            inline=True
        )

        embed.add_field(
            name="💡 نصائح مهمة",
            value="• استخدم `تبريد` لمعرفة متى يمكنك استخدام الأوامر\n• راقب أسعار المتجر لأفضل الصفقات\n• كمل المهام للحصول على خبرة إضافية",
            inline=True
        )

        embed.set_footer(text="💬 استخدم الأزرار أدناه للتنقل بين الفئات")

        return embed

class DetailedHelpView(View):
    def __init__(self, help_system):
        super().__init__(timeout=300)
        self.help_system = help_system

        # إضافة أزرار الفئات
        for category, info in help_system.help_categories.items():
            self.add_item(CategoryButton(category, info, help_system))

class CategoryButton(Button):
    def __init__(self, category, info, help_system):
        super().__init__(
            label=category,
            emoji=info["emoji"],
            style=ButtonStyle.primary,
            row=len([i for i in range(5)]) // 3
        )
        self.category = category
        self.info = info
        self.help_system = help_system

    async def callback(self, interaction: Interaction):
        embed = Embed(
            title=f"{self.info['emoji']} {self.category}",
            description=self.info["description"],
            color=0x2ecc71
        )

        # إضافة الأوامر مع شرح مبسط
        commands_text = ""
        for command in self.info["commands"]:
            commands_text += f"• `{command}` - {self.get_command_description(command)}\n"

        embed.add_field(
            name="📝 الأوامر المتاحة",
            value=commands_text,
            inline=False
        )

        # إضافة نصائح خاصة بالفئة
        tips = self.get_category_tips(self.category)
        if tips:
            embed.add_field(
                name="💡 نصائح ومعلومات",
                value=tips,
                inline=False
            )

        embed.set_footer(text="🔙 استخدم الأزرار للعودة أو التنقل")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    def get_command_description(self, command):
        """وصف مختصر لكل أمر"""
        descriptions = {
            "رصيد": "عرض أموالك وعملاتك",
            "يومي": "مكافأة يومية مجانية",
            "عمل": "اعمل واربح المال",
            "ترقية": "ارقِ وظيفتك",
            "تداول": "تداول في الأسواق",
            "استثمار": "استثمر في الشركات",
            "متجر": "تسوق واشتر العناصر",
            "شراء": "شراء سريع",
            "بيع": "بيع العناصر",
            "حقيبة": "عرض ممتلكاتك",
            "اختصاص": "اختيار وترقية التخصص",
            "نهب": "نهب اللاعبين الآخرين",
            "انتقام": "انتقم من الناهبين",
            "حماية": "احمِ نفسك أو غيرك",
            "درع": "درع سورا الخاص",
            "تحدي": "تحدي لاعب في مراهنة",
            "مبارزة": "مبارزة سريعة",
            "حجر_ورقة_مقص": "لعبة كلاسيكية",
            "تخمين": "خمن الرقم",
            "ذاكرة": "لعبة الذاكرة",
            "رياضيات": "حل المعادلات",
            "كلمات": "ترتيب الكلمات",
            "مزارع": "شراء البذور",
            "زرع": "زراعة البذور",
            "مزرعة": "إدارة المزرعة",
            "صياد": "شراء الطُعم",
            "صيد": "اصطياد الأسماك",
            "حوض": "إدارة حوض السمك",
            "سراديب": "دخول السراديب",
            "عتاد": "شراء المعدات",
            "تبريد_سراديب": "حالة تبريد السراديب",
            "مهام": "عرض المهام",
            "مستوى": "معلومات المستوى",
            "خبرة": "قائمة الخبرة",
            "مكافآت": "المكافآت المتاحة",
            "قوائم": "قوائم الترتيب",
            "سجلات": "السجلات والأنشطة",
            "إحصائيات": "الإحصائيات العامة",
            "أنشطتي": "أنشطتك الأخيرة",
            "ثروة": "قائمة الأثرياء"
        }
        return descriptions.get(command, "وصف غير متوفر")

    def get_category_tips(self, category):
        """نصائح خاصة بكل فئة"""
        tips = {
            "اقتصاد": "• استخدم الأمر يومي كل 24 ساعة\n• العمل يعطي دخل ثابت\n• التداول مربح لكن محفوف بالمخاطر",
            "متجر": "• الأسعار تتغير كل 6 دقائق\n• راقب المؤشرات للشراء بسعر منخفض\n• احتفظ بالعناصر النادرة",
            "قتال": "• كل اختصاص له قدرات خاصة\n• النهب له فترة تبريد\n• المحارب يمكنه الانتقام",
            "ألعاب": "• كل لعبة لها فترة تبريد\n• الفوز يعطي مكافآت أكبر\n• حتى الخسارة تعطي مكافأة تشجيعية",
            "زراعة": "• كل محصول له وقت نمو مختلف\n• المحاصيل الأغلى تحتاج وقت أطول\n• تابع مزرعتك بانتظام",
            "صيد": "• الطُعم الأفضل يزيد فرص الصيد\n• ضع الأسماك في الحوض لتنمو\n• الأسماك الأكبر سعراً أعلى",
            "سراديب": "• تحتاج عتاد جيد للسراديب الصعبة\n• كل سرداب له زعيم مختلف\n• الاختصاص يؤثر على القتال",
            "مهام": "• المهام تتجدد يومياً\n• إنجاز المهام يعطي خبرة\n• الخبرة ترفع مستواك",
            "إحصائيات": "• تابع تقدمك وتطورك\n• قارن نفسك بالآخرين\n• السجلات تظهر نشاطاتك"
        }
        return tips.get(category, "")

def setup_advanced_help(bot):
    """إعداد نظام المساعدة المتقدم"""
    help_system = AdvancedHelpSystem(bot)

    @bot.command(name="شروحات")
    async def advanced_help(ctx):
        """نظام المساعدة المتقدم"""
        embed = help_system.create_main_help_embed()
        view = DetailedHelpView(help_system)
        await ctx.send(embed=embed, view=view)

    return help_system