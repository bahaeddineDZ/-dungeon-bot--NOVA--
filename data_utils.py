import json
import os
import discord
from discord.ext import commands
from discord import Interaction, Embed, ButtonStyle
from discord.ui import View, Button, Select
from discord import SelectOption
DATA_FILE = "users.json"

# تحميل البيانات
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# حفظ البيانات
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# تهيئة المستخدم
def init_user(user_id, username=None):
    user_id = str(user_id)
    data = load_data()

    default_data = {
        "username": username or "مستخدم مجهول",
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
        "spec_level": 1
    }

    if user_id in data:
        # تحويل الشكل القديم إلى الشكل الجديد تلقائيًا
        if isinstance(data[user_id].get("balance"), int):
            balance_int = data[user_id]["balance"]
            data[user_id]["balance"] = {
                "دولار": balance_int,
                "ذهب": 0,
                "ماس": 0
            }

        user = data[user_id]
        # تحديث الحقول الناقصة إن وُجدت
        for key, value in default_data.items():
            if key not in user:
                user[key] = value

        # تحديث اسم المستخدم إذا تم توفيره
        if username:
            user["username"] = username

    else:
        # إنشاء حساب جديد بالكامل
        data[user_id] = default_data
        print(f"✅ تم إنشاء حساب جديد للمستخدم: {user_id}")

    save_data(data)

# تجربة إنشاء مستخدم يدويًا
if __name__ == "__main__":
    test_id = 123456789
    init_user(test_id)

# قائمة الاختصاصات
specializations_data = {
    "نينجا": {"boost_type": "steal_boost", "percentage": 10},
    "سورا": {"boost_type": "defense_boost", "percentage": 15},
    "شامان": {"boost_type": "heal_boost", "percentage": 20},
    "محارب": {"boost_type": "attack_boost", "percentage": 12}
}

specializations = list(specializations_data.keys())

# قائمة الاختيار
class SpecSelect(Select):
    def __init__(self, user_id):
        options = [SelectOption(label=spec, value=spec) for spec in specializations]
        super().__init__(placeholder="اختر اختصاصك", options=options)
        self.user_id = user_id

    async def callback(self, interaction: Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ هذا الخيار ليس لك!", ephemeral=True)
            return

        data = load_data()
        data[self.user_id]["specialization"] = self.values[0]
        save_data(data)

        await interaction.response.edit_message(
            content=f"✅ تم اختيار الاختصاص: **{self.values[0]}**", view=None
        )

# واجهة اختيار الاختصاص لأول مرة
class SpecView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.add_item(SpecSelect(user_id))

# واجهة الاختصاص للمستخدم الذي يملك واحداً
class ExistingSpecView(View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id

    @discord.ui.button(label="🔄 تغيير الاختصاص", style=ButtonStyle.danger)
    async def change_spec(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ هذا الزر ليس لك!", ephemeral=True)
            return

        data = load_data()
        data[self.user_id]["specialization"] = None
        data[self.user_id]["spec_level"] = 1
        save_data(data)

        await interaction.response.edit_message(
            content="❗ تم حذف اختصاصك، اكتب `اختصاص` لاختيار واحد جديد.",
            view=None
        )

    @discord.ui.button(label="⬆️ تطوير المستوى", style=ButtonStyle.success)
    async def upgrade_spec(self, interaction: Interaction, button: Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("❌ هذا الزر ليس لك!", ephemeral=True)
            return

        data = load_data()
        data[self.user_id]["spec_level"] += 1
        save_data(data)

        await interaction.response.edit_message(
            content=f"✅ تم تطوير مستواك في **{data[self.user_id]['specialization']}** إلى المستوى **{data[self.user_id]['spec_level']}**.",
            view=None
        )

# أمر البوت: اختصاص
@commands.command(name="اختصاص")
async def specialization(ctx):
    user_id = str(ctx.author.id)
    init_user(user_id)
    data = load_data()
    user = data[user_id]
    spec = user["specialization"]
    level = user["spec_level"]

    if spec is None:
        await ctx.send("👤 لم تقم باختيار اختصاصك بعد، يرجى الاختيار:", view=SpecView(user_id))
    else:
        embed = Embed(
            title="📘 معلومات الاختصاص",
            description=f"👤 **{ctx.author.name}**\n🧪 **الاختصاص:** {spec}\n📈 **المستوى:** {level}",
            color=0x00b0f4
        )
        await ctx.send(embed=embed, view=ExistingSpecView(user_id))

# إعداد البوت
bot = commands.Bot(command_prefix="", intents=discord.Intents.all())

# بذور المزرعة (معلومات جانبية حتى الآن)
SEEDS = {
    "🌱 قمح": {"cost": 20000, "grow_time": 60, "sell_price": 40000},
    "🌿 شعير": {"cost": 40000, "grow_time": 120, "sell_price": 80000},
    "🌾 أرز": {"cost": 80000, "grow_time": 240, "sell_price": 160000},
}

# لا تنسى إضافة الأمر للبوت في ملف التشغيل الرئيسي
# bot.add_command(specialization)
