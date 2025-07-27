
import json
import os
import time
import random
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select, Modal, TextInput
from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system
from tasks_system import tasks_system

# ================================= بيانات المتجر =================================

STORE_ITEMS = [
    # 🔹 شائعة
    {"name": "🗡️ سيف سام", "price": 10_000, "fluctuation": 0.2, "rarity": "شائع"},
    {"name": "🧪 جرعة الحكمة", "price": 25_000, "fluctuation": 0.2, "rarity": "شائع"},

    # 🔸 غير شائعة
    {"name": "🪓 منجل", "price": 100_000, "fluctuation": 0.3, "rarity": "غير شائع"},
    {"name": "🧪 كيميائي أحمر", "price": 60_000, "fluctuation": 0.3, "rarity": "غير شائع"},
    {"name": "🧣 وشاح الحكام", "price": 250_000, "fluctuation": 0.3, "rarity": "غير شائع"},

    # 🔶 نادرة
    {"name": "🛡️ درع التنين المصفح", "price": 500_000, "fluctuation": 0.4, "rarity": "نادر"},
    {"name": "🛡️ ترس العمالقة", "price": 750_000, "fluctuation": 0.4, "rarity": "نادر"},
    {"name": "🎽 زي المحارب", "price": 350_000, "fluctuation": 0.4, "rarity": "نادر"},
    {"name": "🧤 قفازات المهارة", "price": 300_000, "fluctuation": 0.4, "rarity": "نادر"},
    {"name": "💍 خاتم الزواج", "price": 400_000, "fluctuation": 0.4, "rarity": "نادر"},

    # 🔱 أسطورية
    {"name": "🐉 دابة التنين", "price": 5_000_000, "fluctuation": 0.6, "rarity": "أسطوري"},
    {"name": "👑 تاج الهيمنة", "price": 10_000_000, "fluctuation": 0.6, "rarity": "أسطوري"}
]

BASE_PRICES = {item["name"]: item["price"] for item in STORE_ITEMS}
PRICE_FILE = "shop_prices.json"
PRICE_STATE_FILE = "price_state.json"
PRICE_DURATION = 6 * 60  # 6 دقائق بالثواني

# ================================= إدارة الأسعار =================================

class PriceManager:
    @staticmethod
    def load_prices():
        """تحميل الأسعار الحالية"""
        if not os.path.exists(PRICE_FILE):
            with open(PRICE_FILE, "w", encoding="utf-8") as f:
                json.dump(BASE_PRICES, f, indent=4, ensure_ascii=False)
        
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def save_prices(prices):
        """حفظ الأسعار"""
        with open(PRICE_FILE, "w", encoding="utf-8") as f:
            json.dump(prices, f, indent=4, ensure_ascii=False)

    @staticmethod
    def to_multiple_of_5(value):
        """تقريب السعر لمضاعف 5"""
        return 5 * round(value / 5)

    @staticmethod
    def fluctuate_price(base_price, fluctuation_rate):
        """تحديد تقلب السعر"""
        delta = random.uniform(-fluctuation_rate, fluctuation_rate)
        new_price = max(1, int(base_price * (1 + delta)))
        return PriceManager.to_multiple_of_5(new_price)

    @staticmethod
    def get_price_indicator(old, new):
        """مؤشر تغيير السعر"""
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

    @staticmethod
    def update_prices_if_needed():
        """تحديث الأسعار إذا لزم الأمر"""
        if not os.path.exists(PRICE_STATE_FILE):
            return PriceManager.regenerate_prices()

        with open(PRICE_STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        last_update = data.get("last_update", 0)
        now = time.time()

        if now - last_update >= PRICE_DURATION:
            return PriceManager.regenerate_prices()

        return data.get("prices", BASE_PRICES)

    @staticmethod
    def regenerate_prices():
        """إعادة توليد الأسعار"""
        prices = {}
        for item in STORE_ITEMS:
            base_price = item["price"]
            fluctuated = PriceManager.fluctuate_price(base_price, item.get("fluctuation", 0.2))
            prices[item["name"]] = fluctuated

        data = {"last_update": time.time(), "prices": prices}
        with open(PRICE_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return prices

    @staticmethod
    def get_price_footer():
        """نص تذييل معلومات الأسعار"""
        if os.path.exists(PRICE_STATE_FILE):
            with open(PRICE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            remaining = PRICE_DURATION - (time.time() - data.get("last_update", 0))
            minutes = int(max(0, remaining // 60))
            seconds = int(max(0, remaining % 60))
            return f"⏳ تحديث الأسعار خلال {minutes} دقيقة و {seconds} ثانية."
        else:
            return "⏳ الأسعار تم تحديثها للتو."

# ================================= واجهات المتجر =================================

class ShopMainView(View):
    """الواجهة الرئيسية للمتجر"""
    
    def __init__(self, prices):
        super().__init__(timeout=60)
        self.prices = prices
        
        for item in STORE_ITEMS:
            self.add_item(ShopItemButton(item, self.prices))

class ShopItemButton(Button):
    """زر عنصر في المتجر"""
    
    def __init__(self, item, prices):
        self.item = item
        self.prices = prices
        
        # تحديد معلومات العنصر
        name = item["name"]
        base_price = item["price"]
        current_price = prices.get(name, base_price)
        indicator = PriceManager.get_price_indicator(base_price, current_price)
        
        # تحديد لون الزر حسب التغيير في السعر
        diff = current_price - base_price
        percentage = diff / base_price
        
        if percentage < -0.1:
            style = ButtonStyle.danger  # انخفض كثيراً
        elif -0.1 <= percentage <= 0.1:
            style = ButtonStyle.secondary  # قريب من المتوسط
        elif percentage > 0.2:
            style = ButtonStyle.success  # مرتفع كثيراً
        else:
            style = ButtonStyle.primary  # عادي
        
        # إعداد الزر
        emoji = name[0]
        item_name = name[2:].strip()
        
        super().__init__(
            label=f"{item_name} – {current_price:,}$ {indicator}",
            emoji=emoji,
            style=style
        )

    async def callback(self, interaction: Interaction):
        view = ItemActionView(self.item["name"], self.prices)
        await interaction.response.send_message(
            f"🎯 اختر العملية التي تريد تنفيذها على: **{self.item['name']}**",
            view=view,
            ephemeral=True
        )

class ItemActionView(View):
    """واجهة اختيار العملية (شراء/بيع)"""
    
    def __init__(self, item_name, prices):
        super().__init__(timeout=30)
        self.item_name = item_name
        self.prices = prices

    @discord.ui.button(label="🛒 شراء", style=ButtonStyle.success)
    async def buy_button(self, interaction: Interaction, button: Button):
        shop = ShopSystem()
        await shop.handle_buy_item(interaction, self.item_name, self.prices)

    @discord.ui.button(label="💰 بيع", style=ButtonStyle.danger)
    async def sell_button(self, interaction: Interaction, button: Button):
        shop = ShopSystem()
        await shop.handle_sell_item(interaction, self.item_name, self.prices)

# ================================= نظام المتجر الرئيسي =================================

class ShopSystem:
    """فئة إدارة نظام المتجر"""
    
    def __init__(self):
        self.price_manager = PriceManager()

    async def show_main_shop(self, ctx):
        """عرض المتجر الرئيسي"""
        prices = self.price_manager.update_prices_if_needed()
        footer_text = self.price_manager.get_price_footer()

        embed = Embed(
            title="🏪 المتجر الديناميكي العالمي",
            description=(
                "🌟 **مرحباً بك في السوق العالمي!**\n\n"
                "📈 الأسعار تتغير كل **6 دقائق** حسب العرض والطلب\n"
                "🛒 اضغط على أي عنصر لاختيار إجراء (شراء / بيع)\n"
                "💡 **نصيحة:** راقب المؤشرات لتحصل على أفضل الصفقات!"
            ),
            color=0x2c3e50
        )
        embed.set_footer(text=footer_text)

        view = ShopMainView(prices)
        await ctx.send(embed=embed, view=view)

    async def handle_buy_item(self, interaction: Interaction, item_name, prices):
        """معالجة شراء عنصر"""
        user_id = str(interaction.user.id)
        
        # فحص التبريد
        allowed, remaining = check_cooldown(user_id, "شراء")
        if not allowed:
            await interaction.response.send_message(
                f"⏳ الرجاء الانتظار {remaining} قبل استخدام هذا الأمر مرة أخرى.",
                ephemeral=True
            )
            return

        init_user(user_id, interaction.user.display_name)
        data = load_data()
        user_balance = data[user_id]["balance"]["دولار"]
        
        # معلومات العنصر
        item_info = next((item for item in STORE_ITEMS if item["name"] == item_name), None)
        if not item_info:
            await interaction.response.send_message("❌ عنصر غير موجود!", ephemeral=True)
            return
        
        price_per_unit = prices.get(item_name, item_info["price"])
        max_affordable = user_balance // price_per_unit
        
        if max_affordable == 0:
            await interaction.response.send_message(
                f"❌ لا يمكنك شراء {item_name} - رصيدك غير كافٍ!\n💰 تحتاج: {price_per_unit:,}$ | لديك: {user_balance:,}$",
                ephemeral=True
            )
            return

        # عرض خيارات الكمية
        view = BuyQuantityView(item_name, price_per_unit, max_affordable, user_balance, user_id, interaction.user)
        
        embed = Embed(
            title="🛒 اختيار كمية الشراء",
            description=f"**العنصر:** {item_name}\n**السعر:** {price_per_unit:,}$ للقطعة الواحدة\n**رصيدك:** {user_balance:,}$\n**الحد الأقصى:** {max_affordable:,} قطعة",
            color=0x3498db
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_sell_item(self, interaction: Interaction, item_name, prices):
        """معالجة بيع عنصر"""
        user_id = str(interaction.user.id)
        
        # فحص التبريد
        allowed, remaining = check_cooldown(user_id, "بيع")
        if not allowed:
            await interaction.response.send_message(
                f"⏳ الرجاء الانتظار {remaining} قبل استخدام هذا الأمر مجددًا.",
                ephemeral=True
            )
            return

        init_user(user_id, interaction.user.display_name)
        data = load_data()
        user_data = data.get(user_id, {})
        bag = user_data.get("حقيبة", [])
        
        # فحص وجود العنصر في الحقيبة
        item_count = bag.count(item_name)
        if item_count == 0:
            await interaction.response.send_message(
                f"❌ لا تملك {item_name} في حقيبتك!",
                ephemeral=True
            )
            return
        
        # معلومات السعر
        item_info = next((item for item in STORE_ITEMS if item["name"] == item_name), None)
        sale_price = prices.get(item_name, item_info["price"] if item_info else 1000)
        
        # عرض خيارات البيع
        view = SellQuantityView(item_name, sale_price, item_count, user_id, interaction.user)
        
        embed = Embed(
            title="💰 اختيار كمية البيع",
            description=f"**العنصر:** {item_name}\n**السعر:** {sale_price:,}$ للقطعة الواحدة\n**لديك:** {item_count} قطعة\n**القيمة الإجمالية:** {sale_price * item_count:,}$",
            color=0xe67e22
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

# ================================= واجهات الشراء والبيع =================================

class BuyQuantityView(View):
    """واجهة اختيار كمية الشراء"""
    
    def __init__(self, item_name, price_per_unit, max_affordable, user_balance, user_id, user):
        super().__init__(timeout=60)
        self.item_name = item_name
        self.price_per_unit = price_per_unit
        self.max_affordable = max_affordable
        self.user_balance = user_balance
        self.user_id = str(user_id)
        self.user = user

    @discord.ui.button(label="1️⃣ واحد", style=ButtonStyle.secondary)
    async def buy_one(self, interaction: Interaction, button: Button):
        await self.confirm_purchase(interaction, 1)

    @discord.ui.button(label="🔟 عشرة", style=ButtonStyle.secondary)
    async def buy_ten(self, interaction: Interaction, button: Button):
        qty = min(10, self.max_affordable)
        await self.confirm_purchase(interaction, qty)

    @discord.ui.button(label="💯 مائة", style=ButtonStyle.primary)
    async def buy_hundred(self, interaction: Interaction, button: Button):
        qty = min(100, self.max_affordable)
        await self.confirm_purchase(interaction, qty)

    @discord.ui.button(label="💸 كل ما أستطيع", style=ButtonStyle.danger)
    async def buy_max(self, interaction: Interaction, button: Button):
        await self.confirm_purchase(interaction, self.max_affordable)

    @discord.ui.button(label="✍️ كتابة يدوية", style=ButtonStyle.success, row=1)
    async def manual_input(self, interaction: Interaction, button: Button):
        modal = BuyQuantityModal(self)
        await interaction.response.send_modal(modal)

    async def confirm_purchase(self, interaction: Interaction, quantity: int):
        """تأكيد عملية الشراء"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
            return

        total_cost = self.price_per_unit * quantity
        remaining_balance = self.user_balance - total_cost
        
        embed = Embed(
            title="🛒 تأكيد عملية الشراء",
            color=0x2ecc71
        )
        
        embed.add_field(name="📦 العنصر", value=self.item_name, inline=False)
        embed.add_field(name="🔢 الكمية", value=f"{quantity:,} قطعة", inline=True)
        embed.add_field(name="💰 سعر الوحدة", value=f"{self.price_per_unit:,}$", inline=True)
        embed.add_field(name="🧮 التكلفة الإجمالية", value=f"**{total_cost:,}$**", inline=False)
        embed.add_field(name="💳 الرصيد بعد الشراء", value=f"{remaining_balance:,}$", inline=True)
        
        view = FinalPurchaseConfirmView(self.item_name, quantity, total_cost, self.user_id, self.user)
        
        if hasattr(interaction, 'response') and not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)

class BuyQuantityModal(Modal, title="كتابة الكمية يدوياً"):
    """نافذة إدخال الكمية يدوياً"""
    
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.qty_input = TextInput(
            label=f"أدخل الكمية المطلوبة (الحد الأقصى: {parent_view.max_affordable:,})",
            placeholder=f"مثال: {min(5, parent_view.max_affordable)}",
            required=True,
            max_length=10
        )
        self.add_item(self.qty_input)

    async def on_submit(self, interaction: Interaction):
        try:
            qty = int(self.qty_input.value.replace(",", "").strip())
            if qty <= 0:
                await interaction.response.send_message("❌ الكمية يجب أن تكون أكبر من صفر!", ephemeral=True)
                return
            if qty > self.parent_view.max_affordable:
                await interaction.response.send_message(
                    f"❌ لا يمكنك شراء {qty:,} قطعة!\n💰 الحد الأقصى الذي تستطيع شراؤه: {self.parent_view.max_affordable:,}",
                    ephemeral=True
                )
                return
            
            await self.parent_view.confirm_purchase(interaction, qty)
            
        except ValueError:
            await interaction.response.send_message("❌ أدخل رقماً صحيحاً فقط!", ephemeral=True)

class FinalPurchaseConfirmView(View):
    """تأكيد الشراء النهائي"""
    
    def __init__(self, item_name, quantity, total_cost, user_id, user):
        super().__init__(timeout=30)
        self.item_name = item_name
        self.quantity = quantity
        self.total_cost = total_cost
        self.user_id = user_id
        self.user = user

    @discord.ui.button(label="✅ تأكيد الشراء", style=ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
            return

        # تنفيذ عملية الشراء
        data = load_data()
        user_data = data[self.user_id]
        current_balance = user_data["balance"]["دولار"]
        
        if current_balance < self.total_cost:
            await interaction.response.send_message(
                "❌ رصيدك لم يعد كافياً لإتمام العملية!",
                ephemeral=True
            )
            return
        
        # خصم المبلغ وإضافة العناصر
        user_data["balance"]["دولار"] -= self.total_cost
        user_data.setdefault("حقيبة", []).extend([self.item_name] * self.quantity)
        save_data(data)
        
        # تحديث مهام الشراء
        completed_tasks = tasks_system.update_task_progress(self.user_id, "buy_items", self.quantity)
        
        # تسجيل النشاط
        logs_system.add_log(
            "shop_logs",
            self.user_id,
            self.user.display_name,
            f"اشترى {self.quantity} من {self.item_name}",
            {"item": self.item_name, "quantity": self.quantity, "cost": self.total_cost}
        )
        
        success_embed = Embed(
            title="✅ تمت عملية الشراء بنجاح!",
            description=f"🎉 تم شراء **{self.quantity:,}** من {self.item_name}",
            color=0x00ff00
        )
        
        success_embed.add_field(name="💰 المبلغ المدفوع", value=f"{self.total_cost:,}$", inline=True)
        success_embed.add_field(name="💳 رصيدك الجديد", value=f"{user_data['balance']['دولار']:,}$", inline=True)
        
        if completed_tasks:
            success_embed.add_field(
                name="🎯 مهام مكتملة",
                value=f"أكملت {len(completed_tasks)} مهمة!",
                inline=False
            )
        
        update_cooldown(self.user_id, "شراء")
        await interaction.response.edit_message(embed=success_embed, view=None)

    @discord.ui.button(label="❌ إلغاء", style=ButtonStyle.danger)
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="❌ تم إلغاء عملية الشراء.", embed=None, view=None)

class SellQuantityView(View):
    """واجهة اختيار كمية البيع"""
    
    def __init__(self, item_name, sale_price, max_quantity, user_id, user):
        super().__init__(timeout=60)
        self.item_name = item_name
        self.sale_price = sale_price
        self.max_quantity = max_quantity
        self.user_id = str(user_id)
        self.user = user

    @discord.ui.button(label="1️⃣ واحد", style=ButtonStyle.secondary)
    async def sell_one(self, interaction: Interaction, button: Button):
        await self.confirm_sale(interaction, 1)

    @discord.ui.button(label="🔟 عشرة", style=ButtonStyle.secondary)
    async def sell_ten(self, interaction: Interaction, button: Button):
        qty = min(10, self.max_quantity)
        await self.confirm_sale(interaction, qty)

    @discord.ui.button(label="💸 بيع الكل", style=ButtonStyle.danger)
    async def sell_all(self, interaction: Interaction, button: Button):
        await self.confirm_sale(interaction, self.max_quantity)

    @discord.ui.button(label="✍️ كتابة يدوية", style=ButtonStyle.success, row=1)
    async def manual_sell(self, interaction: Interaction, button: Button):
        modal = SellQuantityModal(self)
        await interaction.response.send_modal(modal)

    async def confirm_sale(self, interaction: Interaction, quantity: int):
        """تأكيد عملية البيع"""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
            return

        total_earning = self.sale_price * quantity
        
        embed = Embed(
            title="💰 تأكيد عملية البيع",
            color=0xe67e22
        )
        
        embed.add_field(name="📦 العنصر", value=self.item_name, inline=False)
        embed.add_field(name="🔢 الكمية", value=f"{quantity:,} قطعة", inline=True)
        embed.add_field(name="💰 سعر الوحدة", value=f"{self.sale_price:,}$", inline=True)
        embed.add_field(name="🧮 الربح الإجمالي", value=f"**{total_earning:,}$**", inline=False)
        
        view = FinalSaleConfirmView(self.item_name, quantity, total_earning, self.user_id, self.user)
        
        if hasattr(interaction, 'response') and not interaction.response.is_done():
            await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.edit_original_response(embed=embed, view=view)

class SellQuantityModal(Modal, title="كتابة الكمية يدوياً"):
    """نافذة إدخال كمية البيع يدوياً"""
    
    def __init__(self, parent_view):
        super().__init__()
        self.parent_view = parent_view
        self.qty_input = TextInput(
            label=f"أدخل الكمية المراد بيعها (الحد الأقصى: {parent_view.max_quantity})",
            placeholder=f"مثال: {min(5, parent_view.max_quantity)}",
            required=True,
            max_length=10
        )
        self.add_item(self.qty_input)

    async def on_submit(self, interaction: Interaction):
        try:
            qty = int(self.qty_input.value.replace(",", "").strip())
            if qty <= 0:
                await interaction.response.send_message("❌ الكمية يجب أن تكون أكبر من صفر!", ephemeral=True)
                return
            if qty > self.parent_view.max_quantity:
                await interaction.response.send_message(
                    f"❌ لا تملك {qty:,} قطعة!\n📦 الحد الأقصى الذي تملكه: {self.parent_view.max_quantity}",
                    ephemeral=True
                )
                return
            
            await self.parent_view.confirm_sale(interaction, qty)
            
        except ValueError:
            await interaction.response.send_message("❌ أدخل رقماً صحيحاً فقط!", ephemeral=True)

class FinalSaleConfirmView(View):
    """تأكيد البيع النهائي"""
    
    def __init__(self, item_name, quantity, total_earning, user_id, user):
        super().__init__(timeout=30)
        self.item_name = item_name
        self.quantity = quantity
        self.total_earning = total_earning
        self.user_id = user_id
        self.user = user

    @discord.ui.button(label="✅ تأكيد البيع", style=ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ هذا ليس لك!", ephemeral=True)
            return

        # تنفيذ عملية البيع
        data = load_data()
        user_data = data[self.user_id]
        bag = user_data.get("حقيبة", [])
        available_count = bag.count(self.item_name)
        
        if available_count < self.quantity:
            await interaction.response.send_message(
                f"❌ لم تعد تملك {self.quantity} من {self.item_name}!\nلديك فقط {available_count}",
                ephemeral=True
            )
            return
        
        # إزالة العناصر وإضافة المال
        for _ in range(self.quantity):
            bag.remove(self.item_name)
        
        user_data["balance"]["دولار"] += self.total_earning
        user_data["حقيبة"] = bag
        save_data(data)
        
        # تسجيل النشاط
        logs_system.add_log(
            "shop_logs",
            self.user_id,
            self.user.display_name,
            f"باع {self.quantity} من {self.item_name}",
            {"item": self.item_name, "quantity": self.quantity, "earning": self.total_earning}
        )
        
        success_embed = Embed(
            title="✅ تمت عملية البيع بنجاح!",
            description=f"🎉 تم بيع **{self.quantity:,}** من {self.item_name}",
            color=0x00ff00
        )
        
        success_embed.add_field(name="💰 المبلغ المحصل", value=f"{self.total_earning:,}$", inline=True)
        success_embed.add_field(name="💳 رصيدك الجديد", value=f"{user_data['balance']['دولار']:,}$", inline=True)
        success_embed.add_field(name="📦 المتبقي", value=f"{bag.count(self.item_name)} قطعة" if self.item_name in bag else "لا يوجد", inline=True)
        
        update_cooldown(self.user_id, "بيع")
        await interaction.response.edit_message(embed=success_embed, view=None)

    @discord.ui.button(label="❌ إلغاء", style=ButtonStyle.danger)
    async def cancel(self, interaction: Interaction, button: Button):
        await interaction.response.edit_message(content="❌ تم إلغاء عملية البيع.", embed=None, view=None)

# ================================= دوال التصدير =================================

def setup_shop_commands(bot):
    """إعداد أوامر المتجر"""
    shop_system = ShopSystem()
    
    @bot.command(name="متجر")
    async def shop_command(ctx):
        """عرض المتجر الرئيسي"""
        await shop_system.show_main_shop(ctx)
    
    @bot.command(name="شراء")
    async def buy_command(ctx):
        """أمر الشراء (للتوافق مع النظام القديم)"""
        await shop_system.show_main_shop(ctx)
    
    @bot.command(name="بيع")
    async def sell_command(ctx):
        """أمر البيع (للتوافق مع النظام القديم)"""
        await shop_system.show_main_shop(ctx)

# إنشاء كائن المتجر للاستخدام الخارجي
shop_system = ShopSystem()
