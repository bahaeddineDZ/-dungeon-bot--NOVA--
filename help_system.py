
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
                "description": "أوامر إدارة الأموال والعملات الثلاث",
                "color": 0x2ecc71
            },
            "متجر": {
                "emoji": "🛒",
                "commands": ["متجر", "شراء", "بيع", "حقيبة"],
                "description": "نظام المتجر الديناميكي والتسوق الذكي",
                "color": 0x3498db
            },
            "قتال": {
                "emoji": "⚔️",
                "commands": ["اختصاص", "نهب", "انتقام", "حماية", "درع", "تحدي", "مبارزة"],
                "description": "أنظمة القتال والاختصاصات الأربعة",
                "color": 0xe74c3c
            },
            "ألعاب": {
                "emoji": "🎮",
                "commands": ["حجر_ورقة_مقص", "تخمين", "ذاكرة", "رياضيات", "كلمات", "لوتو", "روليت", "بلاك_جاك"],
                "description": "مجموعة شاملة من الألعاب التفاعلية والمثيرة",
                "color": 0x9b59b6
            },
            "زراعة": {
                "emoji": "🌾",
                "commands": ["مزارع", "زرع", "مزرعة"],
                "description": "نظام الزراعة المتطور مع 5 أنواع محاصيل",
                "color": 0x27ae60
            },
            "صيد": {
                "emoji": "🎣",
                "commands": ["صياد", "صيد", "حوض"],
                "description": "نظام الصيد الاحترافي وتربية الأسماك",
                "color": 0x16a085
            },
            "زواج": {
                "emoji": "💍",
                "commands": ["زواج", "طلاق", "زوجي", "هدية", "شهر_عسل"],
                "description": "نظام الزواج والحياة الاجتماعية",
                "color": 0xe91e63
            },
            "سراديب": {
                "emoji": "🏰",
                "commands": ["سراديب", "عتاد", "تبريد_سراديب"],
                "description": "عالم السراديب الخمسة والمعارك الملحمية",
                "color": 0x8b0000
            },
            "مهام": {
                "emoji": "🎯",
                "commands": ["مهام", "مستوى", "خبرة", "مكافآت"],
                "description": "نظام المهام التقدمي ونقاط الخبرة",
                "color": 0xf39c12
            },
            "إحصائيات": {
                "emoji": "📊",
                "commands": ["قوائم", "سجلات", "إحصائيات", "أنشطتي", "ثروة"],
                "description": "السجلات والتقارير التفصيلية",
                "color": 0x34495e
            }
        }

    def create_main_help_embed(self):
        """إنشاء الصفحة الرئيسية للمساعدة المحسنة"""
        embed = Embed(
            title="📚 مركز المساعدة الشامل - NOVA BANK",
            description="🌟 **أهلاً وسهلاً في أقوى نظام اقتصادي تفاعلي!**\n\n🎯 اختر فئة من الأسفل للحصول على دليل مفصل ومعلومات احترافية:",
            color=0x3498db
        )

        # معلومات النظام الشاملة
        embed.add_field(
            name="🏆 ميزات النظام المتطورة",
            value=(
                "💰 **3 عملات:** دولار، ذهب، ماس\n"
                "⚔️ **4 اختصاصات:** محارب، شامان، نينجا، سورا\n"
                "🏰 **5 سراديب:** تحديات ملحمية\n"
                "🌾 **5 محاصيل:** نظام زراعة متكامل\n"
                "🎣 **6 أنواع أسماك:** صيد احترافي\n"
                "🎮 **8+ ألعاب:** ترفيه لا محدود\n"
                "💍 **نظام زواج:** حياة اجتماعية ثرية"
            ),
            inline=False
        )

        embed.add_field(
            name="🚀 دليل البداية السريعة",
            value=(
                "1️⃣ `يومي` - احصل على 100K$ + 25🪙 + 1💎\n"
                "2️⃣ `اختصاص` - اختر قوتك الخاصة\n"
                "3️⃣ `عمل` - ابني ثروتك تدريجياً\n"
                "4️⃣ `متجر` - تسوق بذكاء\n"
                "5️⃣ `زواج` - ابحث عن شريك حياتك!"
            ),
            inline=True
        )

        embed.add_field(
            name="💡 نصائح ذهبية للنجاح",
            value=(
                "🔄 راقب أوقات التبريد بـ `تبريد`\n"
                "📈 تابع أسعار المتجر الديناميكية\n"
                "🎯 أكمل المهام للحصول على خبرة\n"
                "💑 تزوج للحصول على مكافآت مضاعفة\n"
                "⚔️ طور اختصاصك للقتال الأقوى"
            ),
            inline=True
        )

        embed.add_field(
            name="🎮 الألعاب والتحديات",
            value=(
                "🎲 ألعاب الحظ والمهارة\n"
                "⚔️ تحديات بين اللاعبين\n"
                "🏰 سراديب أسطورية\n"
                "🎯 مهام يومية وأسبوعية"
            ),
            inline=True
        )

        embed.set_footer(text="💬 استخدم الأزرار أدناه للتنقل | 🔄 يتم تحديث النظام باستمرار")
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/851461487498878986.png")

        return embed

class DetailedHelpView(View):
    def __init__(self, help_system):
        super().__init__(timeout=300)
        self.help_system = help_system
        self.current_page = 0

        # إضافة أزرار الفئات مع تنسيق أفضل
        categories = list(help_system.help_categories.items())
        for i, (category, info) in enumerate(categories):
            row = i // 3  # 3 أزرار في كل صف
            self.add_item(CategoryButton(category, info, help_system, row))

        # إضافة أزرار التنقل
        self.add_item(NavigationButton("🏠", "الصفحة الرئيسية", help_system, 3))
        self.add_item(SearchButton("🔍", "بحث سريع", help_system, 3))

class CategoryButton(Button):
    def __init__(self, category, info, help_system, row):
        super().__init__(
            label=category,
            emoji=info["emoji"],
            style=ButtonStyle.primary,
            row=row
        )
        self.category = category
        self.info = info
        self.help_system = help_system

    async def callback(self, interaction: Interaction):
        embed = Embed(
            title=f"{self.info['emoji']} {self.category}",
            description=f"📖 **{self.info['description']}**\n\n🎯 **الأوامر المتاحة في هذه الفئة:**",
            color=self.info["color"]
        )

        # تفصيل الأوامر مع أوصاف محسنة
        commands_text = ""
        for i, command in enumerate(self.info["commands"], 1):
            desc = self.get_command_description(command)
            commands_text += f"**{i}.** `{command}`\n└─ {desc}\n\n"

        embed.add_field(
            name="📝 دليل الأوامر التفصيلي",
            value=commands_text,
            inline=False
        )

        # نصائح متقدمة
        tips = self.get_category_tips(self.category)
        if tips:
            embed.add_field(
                name="💡 نصائح احترافية وأسرار",
                value=tips,
                inline=False
            )

        # إحصائيات الفئة
        stats = self.get_category_stats(self.category)
        if stats:
            embed.add_field(
                name="📊 معلومات إضافية",
                value=stats,
                inline=False
            )

        embed.set_footer(text="🔙 استخدم زر الصفحة الرئيسية للعودة | 🔍 استخدم البحث للعثور على أمر محدد")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    def get_command_description(self, command):
        """أوصاف مفصلة ومحسنة لكل أمر"""
        descriptions = {
            # اقتصاد
            "رصيد": "عرض ثروتك الكاملة مع تقييم مستوى الثراء",
            "يومي": "مكافأة يومية ضخمة: 100K$ + 25🪙 + 1💎 + 200 خبرة",
            "عمل": "اعمل حسب مهنتك واربح أموال متزايدة",
            "ترقية": "ارقِ وظيفتك من مواطن إلى ملك",
            "تداول": "تداول في الأسواق العالمية (نجاح 60%)",
            "استثمار": "استثمر في 5 شركات مختلفة",

            # متجر
            "متجر": "تسوق من متجر ديناميكي بأسعار متغيرة",
            "شراء": "شراء سريع للعناصر المتاحة",
            "بيع": "بيع ممتلكاتك بأفضل الأسعار",
            "حقيبة": "عرض جميع ممتلكاتك مُنظمة",

            # قتال
            "اختصاص": "اختر من 4 اختصاصات فريدة مع قدرات خاصة",
            "نهب": "انهب اللاعبين واسرق أموالهم",
            "انتقام": "انتقم من الناهبين (محارب فقط)",
            "حماية": "احمِ نفسك أو غيرك (شامان فقط)",
            "درع": "درع سورا المقدس لساعة كاملة",
            "تحدي": "تحدِ لاعباً في مراهنة ملحمية",
            "مبارزة": "مبارزة سريعة بدون مراهنة",

            # ألعاب
            "حجر_ورقة_مقص": "اللعبة الكلاسيكية مع مكافآت مميزة",
            "تخمين": "خمن رقم من 1-100 في 15 محاولة",
            "ذاكرة": "احفظ تسلسل من 4 رموز",
            "رياضيات": "حل معادلات رياضية بسرعة",
            "كلمات": "رتب الأحرف لتكوين كلمة صحيحة",
            "لوتو": "العب لوتو برقام محظوظة",
            "روليت": "روليت كازينو حقيقي",
            "بلاك_جاك": "لعبة الورق الشهيرة",

            # زراعة
            "مزارع": "اشتر بذور من 5 أنواع مختلفة",
            "زرع": "ازرع بذورك واتركها تنمو",
            "مزرعة": "راقب محاصيلك واحصدها",

            # صيد
            "صياد": "اشتر طُعم من 3 أنواع مختلفة",
            "صيد": "اصطد أسماك من 6 أنواع",
            "حوض": "ربي الأسماك وشاهدها تنمو",

            # زواج
            "زواج": "تزوج من لاعب آخر واحصل على مكافآت",
            "طلاق": "إنهاء الزواج (مكلف!)",
            "زوجي": "معلومات عن شريك حياتك",
            "هدية": "أرسل هدية رومانسية لزوجتك",
            "شهر_عسل": "اذهب في شهر عسل مع مكافآت",

            # سراديب
            "سراديب": "ادخل واحد من 5 سراديب أسطورية",
            "عتاد": "اشتر أقوى الأسلحة والدروع",
            "تبريد_سراديب": "تحقق من أوقات التبريد",

            # مهام
            "مهام": "شاهد مهامك اليومية والأسبوعية",
            "مستوى": "معلومات مستواك وخبرتك",
            "خبرة": "قائمة أصحاب أعلى خبرة",
            "مكافآت": "مركز المكافآت والجوائز",

            # إحصائيات
            "قوائم": "قوائم ترتيب متنوعة",
            "سجلات": "سجلات أنشطتك التفصيلية",
            "إحصائيات": "إحصائيات النظام العامة",
            "أنشطتي": "آخر 15 نشاط لك",
            "ثروة": "قائمة أغنى 10 أشخاص"
        }
        return descriptions.get(command, "وصف غير متوفر")

    def get_category_tips(self, category):
        """نصائح متقدمة لكل فئة"""
        tips = {
            "اقتصاد": (
                "💰 استخدم `يومي` كل 24 ساعة بدون فشل\n"
                "📈 التداول نسبة نجاح 60% - استثمر بحذر\n"
                "👑 الترقية للملك تعطي 20-40 ذهب يومياً\n"
                "💎 الماس أثمن عملة - احتفظ به للعتاد"
            ),
            "متجر": (
                "📊 الأسعار تتغير كل 6 دقائق\n"
                "🔺🔻 راقب المؤشرات للشراء بسعر منخفض\n"
                "💎 العناصر النادرة تحتاج ماس\n"
                "🎒 احتفظ بمساحة في الحقيبة دائماً"
            ),
            "قتال": (
                "⚔️ المحارب: ينتقم ويسترد 40-100% من المسروق\n"
                "🔮 الشامان: يحمي نفسه والآخرين لمدة تصل لـ150 دقيقة\n"
                "🥷 النينجا: ينهب 20-80% من رصيد الضحية\n"
                "🧿 السورا: يعكس النهب ويحصل على درع مقدس"
            ),
            "ألعاب": (
                "🎮 كل لعبة لها فترة تبريد مختلفة\n"
                "🏆 الفوز يضاعف المكافآت\n"
                "💰 حتى الخسارة تعطي مكافأة تشجيعية\n"
                "🎯 الألعاب الجديدة تحتاج مستوى أعلى"
            ),
            "زراعة": (
                "🌾 القمح أسرع نمو (60 دقيقة)\n"
                "🍓 الفراولة أغلى سعر (4 ساعات)\n"
                "💧 لا تنسى متابعة المزرعة\n"
                "📈 المحاصيل الأغلى = وقت أطول"
            ),
            "صيد": (
                "🪱 الطُعم النادر يزيد فرص الصيد بـ20%\n"
                "🐟 ضع الأسماك في الحوض لتنمو\n"
                "📈 الأسماك تزيد قيمتها 10% كل ساعة\n"
                "🦈 القرش أندر وأغلى سمكة"
            ),
            "زواج": (
                "💕 الزواج يضاعف مكافآت بعض الأوامر\n"
                "🎁 الهدايا تقوي العلاقة وتزيد المكافآت\n"
                "🏖️ شهر العسل يعطي مكافآت خاصة\n"
                "💔 الطلاق مكلف - فكر جيداً!"
            ),
            "سراديب": (
                "⚔️ تحتاج عتاد قوي للسراديب الأصعب\n"
                "💎 كل سرداب يحتاج ماس للدخول\n"
                "🏆 الانتصار يعطي مكافآت ضخمة\n"
                "⏳ الهزيمة تعطي عقوبة 15 دقيقة"
            ),
            "مهام": (
                "📅 المهام تتجدد يومياً في منتصف الليل\n"
                "⭐ كل مهمة تعطي خبرة ومكافآت\n"
                "📈 المستوى الأعلى = مهام أصعب ومكافآت أكبر\n"
                "🎯 أكمل 3 مهام يومياً للحصول على مكافأة إضافية"
            ),
            "إحصائيات": (
                "📊 تابع تقدمك مقارنة بالآخرين\n"
                "🏆 كن في المراكز الأولى للحصول على شهرة\n"
                "📈 السجلات تساعدك في تحسين استراتيجيتك\n"
                "💎 بعض الإنجازات تعطي مكافآت سرية"
            )
        }
        return tips.get(category, "")

    def get_category_stats(self, category):
        """معلومات إضافية وإحصائيات لكل فئة"""
        stats = {
            "اقتصاد": "💰 العملات: دولار (أساسي) | ذهب (ترقيات) | ماس (عتاد)",
            "قتال": "⚔️ 4 اختصاصات × 4 رتب = 16 مستوى قوة مختلف",
            "ألعاب": "🎮 8 ألعاب مختلفة مع مكافآت متدرجة",
            "زراعة": "🌾 5 محاصيل: قمح، جزر، طماطم، ذرة، فراولة",
            "صيد": "🎣 6 أنواع أسماك + 3 أنواع طُعم",
            "زواج": "💍 نظام جديد مع 5 أوامر تفاعلية",
            "سراديب": "🏰 5 سراديب بمستويات صعوبة مختلفة",
            "مهام": "🎯 مهام يومية وأسبوعية مع نظام خبرة متطور"
        }
        return stats.get(category, "")

class NavigationButton(Button):
    def __init__(self, emoji, label, help_system, row):
        super().__init__(emoji=emoji, label=label, style=ButtonStyle.secondary, row=row)
        self.help_system = help_system

    async def callback(self, interaction: Interaction):
        embed = self.help_system.create_main_help_embed()
        view = DetailedHelpView(self.help_system)
        await interaction.response.edit_message(embed=embed, view=view)

class SearchButton(Button):
    def __init__(self, emoji, label, help_system, row):
        super().__init__(emoji=emoji, label=label, style=ButtonStyle.success, row=row)
        self.help_system = help_system

    async def callback(self, interaction: Interaction):
        class SearchModal(Modal, title="🔍 البحث السريع"):
            def __init__(self):
                super().__init__()
                self.search_input = TextInput(
                    label="ابحث عن أمر أو موضوع",
                    placeholder="مثال: نهب، زواج، سراديب...",
                    required=True,
                    max_length=50
                )
                self.add_item(self.search_input)

            async def on_submit(self, modal_interaction: Interaction):
                search_term = self.search_input.value.strip().lower()
                
                # البحث في جميع الأوامر
                results = []
                for category, info in help_system.help_categories.items():
                    for command in info["commands"]:
                        if search_term in command.lower() or search_term in category.lower():
                            results.append(f"📁 **{category}** → `{command}`")

                if results:
                    embed = Embed(
                        title="🔍 نتائج البحث",
                        description=f"🎯 **البحث عن:** {search_term}\n\n" + "\n".join(results[:10]),
                        color=0x2ecc71
                    )
                    if len(results) > 10:
                        embed.set_footer(text=f"🔢 تم العثور على {len(results)} نتيجة، يتم عرض أول 10")
                else:
                    embed = Embed(
                        title="🚫 لا توجد نتائج",
                        description=f"❌ لم يتم العثور على نتائج للبحث: **{search_term}**\n\n💡 جرب كلمات أخرى مثل: اقتصاد، قتال، ألعاب",
                        color=0xe74c3c
                    )

                await modal_interaction.response.send_message(embed=embed, ephemeral=True)

        await interaction.response.send_modal(SearchModal())

def setup_advanced_help(bot):
    """إعداد نظام المساعدة المتقدم والمحسن"""
    help_system = AdvancedHelpSystem(bot)

    @bot.command(name="شروحات")
    async def advanced_help(ctx):
        """نظام المساعدة المتقدم والتفاعلي"""
        try:
            embed = help_system.create_main_help_embed()
            view = DetailedHelpView(help_system)
            await ctx.send(embed=embed, view=view)
        except Exception as e:
            print(f"خطأ في نظام الشروحات: {e}")
            await ctx.send("❌ حدث خطأ في تحميل نظام الشروحات. يرجى المحاولة لاحقاً.")

    return help_system
