
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select, Modal, TextInput
import json
import time

class AdvancedHelpSystem:
    def __init__(self, bot):
        self.bot = bot
        
        # نظام الشروحات المفصل
        self.detailed_explanations = {
            "economy": {
                "title": "💰 النظام الاقتصادي المتقدم",
                "icon": "💰",
                "description": "نظام اقتصادي متكامل يحاكي الاقتصاد الحقيقي",
                "sections": {
                    "currencies": {
                        "title": "💱 العملات",
                        "content": """
**💵 الدولار الأمريكي:**
• العملة الأساسية في النظام
• يُكتسب من: العمل، التداول، الألعاب، بيع المحاصيل
• يُستخدم في: الشراء من المتجر، التداول، الاستثمار

**🪙 الذهب:**
• عملة نادرة وقيمة
• يُكتسب من: الوظائف العليا، المكافآت الخاصة
• يُستخدم في: شراء العتاد، ترقية الاختصاص
• القيمة: 1 ذهب = 50 دولار

**💎 الماس:**
• أندر العملات وأغلاها
• يُكتسب من: المكافآت النادرة، إنجاز المهام الصعبة
• يُستخدم في: شراء العتاد الأسطوري، دخول السراديب
• القيمة: 1 ماس = 100 دولار
                        """,
                        "tips": [
                            "💡 نوّع مصادر دخلك لزيادة ثروتك",
                            "🎯 ركز على جمع الماس للعتاد القوي",
                            "📈 راقب نسب التحويل بين العملات"
                        ]
                    },
                    "jobs": {
                        "title": "👷 نظام الوظائف",
                        "content": """
**التدرج الوظيفي:**
1. **مواطن** → دخل: 60-90k دولار
2. **رسام** → دخل: 60-90k دولار  
3. **طبيب** → دخل: 60-90k دولار
4. **مقدم** → دخل: 40-60k دولار + 10-20 ذهب
5. **جنيرال** → دخل: 40-60k دولار + 10-20 ذهب
6. **وزير** → دخل: 40-60k دولار + 10-20 ذهب
7. **ملك** → دخل: 20-40 ذهب فقط
8. **إمبراطور** → دخل: 20-40 ذهب فقط

**متطلبات الترقية:**
• مبالغ متزايدة من الذهب والدولار
• كل ترقية تحتاج موارد أكثر من السابقة
                        """,
                        "tips": [
                            "⚡ ارتق بذكاء - الوظائف العليا تعطي ذهب أكثر",
                            "💰 احفظ الموارد للترقيات المهمة",
                            "🏆 الهدف النهائي: وصول رتبة الإمبراطور"
                        ]
                    }
                }
            },
            
            "combat": {
                "title": "⚔️ نظام القتال والاختصاصات",
                "icon": "⚔️",
                "description": "نظام قتال متطور مع اختصاصات فريدة",
                "sections": {
                    "specializations": {
                        "title": "🎯 الاختصاصات",
                        "content": """
**⚔️ المحارب (Warrior):**
• القدرة الخاصة: الانتقام
• يمكنه استرداد 40-100% من الأموال المسروقة
• رتب القوة: نبيل (40%) → شجاع (60%) → فارسي (80%) → أسطوري (100%)
• مناسب للاعبين الذين يتعرضون للنهب كثيراً

**🛡️ الشامان (Shaman):**
• القدرة الخاصة: الحماية
• يمكنه حماية نفسه أو الآخرين من النهب
• مدة الحماية: 60-150 دقيقة حسب الرتبة
• في الرتبة الأسطورية يمكنه حماية الآخرين

**🥷 النينجا (Ninja):**
• القدرة الخاصة: النهب المضاعف
• يمكنه نهب 20-80% من أموال الضحية
• أسرع في النهب وأكثر فعالية
• مناسب للاعبين العدوانيين

**🧿 السورا (Sura):**
• القدرة الخاصة: عكس النهب
• احتمال 20-80% لعكس النهب على المهاجم
• يمكنه تفعيل درع خاص ضد النهب
• توازن مثالي بين الهجوم والدفاع
                        """,
                        "tips": [
                            "🎯 اختر الاختصاص حسب أسلوب لعبك",
                            "📈 طوّر رتبتك لقدرات أقوى",
                            "⚖️ كل اختصاص له نقاط قوة وضعف"
                        ]
                    },
                    "combat_mechanics": {
                        "title": "⚔️ آليات القتال",
                        "content": """
**نظام النهب:**
• يمكن نهب 10% من رصيد الضحية كحد أدنى
• النينجا يحصل على نسبة أعلى حسب رتبته
• لا يمكن نهب من لديه أقل من 50 دولار
• تبريد 30 دقيقة بين كل نهبة

**نظام الحماية:**
• الشامان يمكنه تفعيل حماية مؤقتة
• السورا له درع خاص ضد النهب
• المحاربون يمكنهم الانتقام خلال 24 ساعة

**نظام الانتقام:**
• متاح للمحاربين فقط
• يجب أن يكون هناك سجل نهب خلال 24 ساعة
• نسبة الاسترداد تعتمد على رتبة المحارب
                        """,
                        "tips": [
                            "🛡️ استخدم الحماية في الأوقات المناسبة",
                            "⚡ النهب يتطلب استراتيجية وتوقيت",
                            "🔄 الانتقام فرصة لاسترداد أموالك"
                        ]
                    }
                }
            },
            
            "dungeons": {
                "title": "🏰 نظام السراديب",
                "icon": "🏰",
                "description": "تحديات PvE مع مكافآت أسطورية",
                "sections": {
                    "dungeon_types": {
                        "title": "🏚️ أنواع السراديب",
                        "content": """
**المستوى 1 - 🏚️ سرداب المبتدئين:**
• الزعيم: 💀 هيكل عظمي قديم
• الصحة: 150 | الهجوم: 25 | الدفاع: 10
• التكلفة: 1 ماس
• المكافآت: 10-25 ذهب، 50k-100k دولار

**المستوى 2 - 🌊 كهف الأمواج:**
• الزعيم: 🐙 أخطبوط عملاق
• الصحة: 300 | الهجوم: 40 | الدفاع: 20
• التكلفة: 3 ماس
• المكافآت: 25-50 ذهب، 100k-200k دولار

**المستوى 3 - 🔥 برج اللهب:**
• الزعيم: 🔥 تنين النار الأحمر
• الصحة: 500 | الهجوم: 60 | الدفاع: 35
• التكلفة: 5 ماس
• المكافآت: 50-100 ذهب، 200k-400k دولار

**المستوى 4 - 💀 قصر الموت:**
• الزعيم: 👻 ملك الأشباح
• الصحة: 800 | الهجوم: 85 | الدفاع: 50
• التكلفة: 8 ماس
• المكافآت: 100-200 ذهب، 400k-800k دولار

**المستوى 5 - ⚡ عرش الآلهة:**
• الزعيم: ⚡ إله الحرب الأسطوري
• الصحة: 1200 | الهجوم: 120 | الدفاع: 80
• التكلفة: 15 ماس
• المكافآت: 200-400 ذهب، 800k-1.5M دولار
                        """,
                        "tips": [
                            "📈 ابدأ بالسراديب السهلة لتطوير قدراتك",
                            "⚔️ حسّن عتادك قبل التحديات الصعبة",
                            "💎 العتاد النادر يأتي من السراديب العليا"
                        ]
                    },
                    "equipment": {
                        "title": "⚔️ نظام العتاد",
                        "content": """
**أنواع العتاد:**

**الأسلحة:**
• ⚔️ سيف خشبي: +10 هجوم (2 ماس)
• 🗡️ سيف فولاذي: +25 هجوم (5 ماس)
• ⚔️ سيف التنين: +50 هجوم، +5 دفاع (15 ماس)
• 🔱 رمح الآلهة: +80 هجوم، +10 دفاع (30 ماس)

**الدروع:**
• 🛡️ درع جلدي: +15 دفاع (3 ماس)
• 🛡️ درع حديدي: +30 دفاع (7 ماس)
• 🛡️ درع التنين: +5 هجوم، +60 دفاع (20 ماس)

**الإكسسوارات:**
• ⛑️ خوذة برونزية: +2 هجوم، +8 دفاع (2 ماس)
• 👑 تاج المحارب: +8 هجوم، +15 دفاع (12 ماس)
• 💍 خاتم القوة: +15 هجوم، +5 دفاع (10 ماس)
• 💍 خاتم الحماية: +3 هجوم، +20 دفاع (10 ماس)

**المستهلكات:**
• 🧪 جرعة الشفاء: +100 صحة (1 ماس)
• ⚡ جرعة القوة: +20 هجوم لـ3 جولات (3 ماس)
                        """,
                        "tips": [
                            "⚖️ وازن بين الهجوم والدفاع",
                            "💰 استثمر في العتاد النادر للسراديب الصعبة",
                            "🧪 لا تنس المستهلكات في المعارك الطويلة"
                        ]
                    }
                }
            },
            
            "farming": {
                "title": "🌾 نظام الزراعة",
                "icon": "🌾", 
                "description": "ازرع واحصد لتحقق أرباح مستدامة",
                "sections": {
                    "crops": {
                        "title": "🌱 أنواع المحاصيل",
                        "content": """
**المحاصيل المتاحة:**

**🌾 القمح:**
• سعر البذور: 150 دولار
• وقت النمو: 1 ساعة
• الربح: 1,000-3,000 دولار
• نسبة الربح: 567%-1900%

**🥕 الجزر:**
• سعر البذور: 250 دولار
• وقت النمو: 1.5 ساعة
• الربح: 2,000-4,000 دولار
• نسبة الربح: 700%-1500%

**🍅 الطماطم:**
• سعر البذور: 400 دولار
• وقت النمو: 2 ساعة
• الربح: 3,500-6,000 دولار
• نسبة الربح: 775%-1400%

**🌽 الذرة:**
• سعر البذور: 600 دولار
• وقت النمو: 3 ساعة
• الربح: 6,000-9,000 دولار
• نسبة الربح: 900%-1400%

**🍓 الفراولة:**
• سعر البذور: 1,000 دولار
• وقت النمو: 4 ساعة
• الربح: 10,000-15,000 دولار
• نسبة الربح: 900%-1400%
                        """,
                        "tips": [
                            "⏰ كلما زاد وقت النمو، زاد الربح",
                            "📊 احسب نسبة الربح لكل ساعة لتحسين الاستثمار",
                            "🌱 ازرع قبل النوم للاستفادة من الوقت"
                        ]
                    },
                    "farming_strategy": {
                        "title": "📈 استراتيجيات الزراعة",
                        "content": """
**للمبتدئين:**
• ابدأ بالقمح لتدوير سريع للأموال
• ازرع كميات صغيرة لتقليل المخاطر
• راقب أوقات النضج

**للمتوسطين:**
• نوّع بين محاصيل سريعة وبطيئة
• استثمر في الجزر والطماطم
• خطط للزراعة قبل فترات الغياب

**للمحترفين:**
• ركز على الذرة والفراولة للأرباح العالية
• احسب العائد على الاستثمار بدقة
• استخدم جدولة زمنية للحصاد المنتظم

**نصائح متقدمة:**
• ازرع قبل النوم للاستفادة من 8 ساعات
• استثمر أرباح المحاصيل السريعة في البطيئة
• راقب رصيدك لتجنب الإفلاس إذا فشل المحصول
                        """,
                        "tips": [
                            "🕐 التوقيت مفتاح النجاح في الزراعة",
                            "📊 اعتمد على البيانات في اتخاذ القرارات",
                            "🔄 نوّع محاصيلك لتقليل المخاطر"
                        ]
                    }
                }
            },
            
            "trading": {
                "title": "📈 نظام التداول والاستثمار",
                "icon": "📈",
                "description": "اضارب في الأسواق المالية العالمية",
                "sections": {
                    "trading_basics": {
                        "title": "📊 أساسيات التداول",
                        "content": """
**كيف يعمل التداول:**
• نسبة نجاح: 60% (أعلى من الخسارة)
• في حالة النجاح: ربح 10%-90% من المبلغ
• في حالة الفشل: خسارة 5%-80% من المبلغ
• تبريد: ساعتان بين كل تداول

**خيارات التداول:**
• ربع الرصيد (25%)
• نصف الرصيد (50%) 
• ثلاث أرباع الرصيد (75%)
• كل الرصيد (100%) - خطر عالي!

**إدارة المخاطر:**
• لا تستثمر أبداً كل رصيدك
• ابدأ بمبالغ صغيرة لتعلم السوق
• احتفظ بصندوق طوارئ للخسائر
                        """,
                        "tips": [
                            "⚠️ التداول محفوف بالمخاطر - استثمر بحذر",
                            "📈 الأرباح العالية تأتي مع مخاطر عالية",
                            "🎯 استخدم استراتيجية ثابتة وتمسك بها"
                        ]
                    },
                    "investment": {
                        "title": "💼 نظام الاستثمار",
                        "content": """
**شركات الاستثمار:**
• 📈 شركة الذهب الدولية
• 🏦 بنك الاستثمار الآمن
• 💻 تكنولوجيا المستقبل
• 🛢️ النفط العالمية
• 🏗️ شركة البناء الكبرى

**نتائج الاستثمار:**
• نطاق العائد: من -40% إلى +50%
• كل شركة لها مخاطر مختلفة
• تبريد: 3 ساعات بين كل استثمار

**استراتيجيات الاستثمار:**
• التنويع: وزع استثماراتك على عدة شركات
• الصبر: الاستثمار لعبة طويلة المدى
• التحليل: راقب أداء الشركات المختلفة
                        """,
                        "tips": [
                            "🏢 كل شركة لها نمط مختلف من المخاطر والعوائد",
                            "⏳ كن صبوراً - الاستثمار الجيد يحتاج وقت",
                            "📊 احتفظ بسجل لاستثماراتك لتحليل الأداء"
                        ]
                    }
                }
            }
        }
    
    def create_main_help_embed(self):
        """إنشاء الصفحة الرئيسية للمساعدة"""
        embed = Embed(
            title="📚 مركز المساعدة الشامل",
            description="""
🌟 **مرحباً بك في دليل النظام الكامل!**

هذا الدليل التفاعلي سيأخذك في جولة شاملة عبر جميع أنظمة اللعبة:

🎯 **ما ستتعلمه:**
• كيفية بناء امبراطوريتك الاقتصادية
• أسرار القتال والاختصاصات المتقدمة  
• استراتيجيات الزراعة والتداول المربحة
• تحديات السراديب والعتاد الأسطوري
• نصائح من الخبراء لتصبح أقوى لاعب

💡 **اختر القسم الذي تريد استكشافه:**
            """,
            color=0x2c3e50
        )
        
        embed.add_field(
            name="🚀 كيفية الاستخدام",
            value="• اضغط على الأزرار للانتقال بين الأقسام\n• كل قسم يحتوي على شروحات مفصلة ونصائح عملية\n• استخدم أزرار التنقل للعودة والمتابعة",
            inline=False
        )
        
        embed.set_footer(text="💡 نصيحة: ابدأ بالنظام الاقتصادي إذا كنت مبتدئاً")
        return embed

class DetailedHelpView(View):
    def __init__(self, help_system):
        super().__init__(timeout=300)  # 5 دقائق
        self.help_system = help_system
        self.current_section = None
        self.current_subsection = None
        
        # إضافة أزرار الأقسام الرئيسية
        self.add_item(SectionButton("💰", "economy", "الاقتصاد"))
        self.add_item(SectionButton("⚔️", "combat", "القتال"))
        self.add_item(SectionButton("🏰", "dungeons", "السراديب"))
        self.add_item(SectionButton("🌾", "farming", "الزراعة"))
        self.add_item(SectionButton("📈", "trading", "التداول"))

class SectionButton(Button):
    def __init__(self, emoji, section_key, label):
        super().__init__(emoji=emoji, label=label, style=ButtonStyle.primary)
        self.section_key = section_key
    
    async def callback(self, interaction: Interaction):
        view = self.view
        section_data = view.help_system.detailed_explanations[self.section_key]
        
        embed = Embed(
            title=f"{section_data['icon']} {section_data['title']}",
            description=section_data['description'],
            color=0x3498db
        )
        
        # إضافة أقسام فرعية
        subsections_text = ""
        for key, subsection in section_data['sections'].items():
            subsections_text += f"📋 **{subsection['title']}**\n"
        
        embed.add_field(
            name="📑 الأقسام المتاحة:",
            value=subsections_text,
            inline=False
        )
        
        # إنشاء view للأقسام الفرعية
        new_view = SubsectionView(view.help_system, self.section_key, section_data)
        
        await interaction.response.edit_message(embed=embed, view=new_view)

class SubsectionView(View):
    def __init__(self, help_system, section_key, section_data):
        super().__init__(timeout=300)
        self.help_system = help_system
        self.section_key = section_key
        self.section_data = section_data
        
        # إضافة أزرار للأقسام الفرعية
        for key, subsection in section_data['sections'].items():
            self.add_item(SubsectionButton(subsection['title'][:20], key, subsection))
        
        # زر العودة
        self.add_item(BackButton())

class SubsectionButton(Button):
    def __init__(self, label, subsection_key, subsection_data):
        super().__init__(label=label, style=ButtonStyle.secondary)
        self.subsection_key = subsection_key
        self.subsection_data = subsection_data
    
    async def callback(self, interaction: Interaction):
        embed = Embed(
            title=f"📖 {self.subsection_data['title']}",
            description=self.subsection_data['content'],
            color=0x27ae60
        )
        
        # إضافة النصائح
        if 'tips' in self.subsection_data:
            tips_text = "\n".join(self.subsection_data['tips'])
            embed.add_field(
                name="💡 نصائح الخبراء:",
                value=tips_text,
                inline=False
            )
        
        embed.set_footer(text="استخدم الأزرار للتنقل بين الأقسام المختلفة")
        
        # إضافة زر العودة
        back_view = View(timeout=300)
        back_view.add_item(BackToSectionButton(self.view.help_system, self.view.section_key, self.view.section_data))
        back_view.add_item(BackToMainButton(self.view.help_system))
        
        await interaction.response.edit_message(embed=embed, view=back_view)

class BackButton(Button):
    def __init__(self):
        super().__init__(label="🔙 رجوع", style=ButtonStyle.danger)
    
    async def callback(self, interaction: Interaction):
        help_system = self.view.help_system
        embed = help_system.create_main_help_embed()
        new_view = DetailedHelpView(help_system)
        await interaction.response.edit_message(embed=embed, view=new_view)

class BackToSectionButton(Button):
    def __init__(self, help_system, section_key, section_data):
        super().__init__(label="🔙 رجوع للقسم", style=ButtonStyle.secondary)
        self.help_system = help_system
        self.section_key = section_key
        self.section_data = section_data
    
    async def callback(self, interaction: Interaction):
        embed = Embed(
            title=f"{self.section_data['icon']} {self.section_data['title']}",
            description=self.section_data['description'],
            color=0x3498db
        )
        
        subsections_text = ""
        for key, subsection in self.section_data['sections'].items():
            subsections_text += f"📋 **{subsection['title']}**\n"
        
        embed.add_field(
            name="📑 الأقسام المتاحة:",
            value=subsections_text,
            inline=False
        )
        
        new_view = SubsectionView(self.help_system, self.section_key, self.section_data)
        await interaction.response.edit_message(embed=embed, view=new_view)

class BackToMainButton(Button):
    def __init__(self, help_system):
        super().__init__(label="🏠 الصفحة الرئيسية", style=ButtonStyle.primary)
        self.help_system = help_system
    
    async def callback(self, interaction: Interaction):
        embed = self.help_system.create_main_help_embed()
        new_view = DetailedHelpView(self.help_system)
        await interaction.response.edit_message(embed=embed, view=new_view)

# دمج النظام مع البوت
def setup_advanced_help(bot):
    help_system = AdvancedHelpSystem(bot)
    
    @bot.command(name="شروحات")
    async def advanced_help_command(ctx):
        embed = help_system.create_main_help_embed()
        view = DetailedHelpView(help_system)
        await ctx.send(embed=embed, view=view)
    
    @bot.command(name="مساعدة")
    async def help_alias(ctx):
        await advanced_help_command(ctx)
    
    return help_system
