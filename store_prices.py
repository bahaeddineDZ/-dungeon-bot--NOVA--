# -------------------------- نظام الأسعار المتغيرة --------------------------
import json
import random

PRICE_FILE = "prices.json"

def load_prices():
    try:
        with open(PRICE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_prices(prices):
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(prices, f, indent=4)

def fluctuate_price(prices):
    for item in prices:
        change = random.randint(-5, 5)
        prices[item] = max(1, prices[item] + change)
    return prices

def get_price_indicator(change):
    if change > 0:
        return "📈"
    elif change < 0:
        return "📉"
    return "➖"

def store_items():
    return list(load_prices().keys())

store_items = [
    {"name": "🗡️ سيف سام", "price": 1000},
    {"name": "🪓 منجل", "price": 3_000_000},
    {"name": "🛡️ درع التنين المصفح", "price": 6_000_000},
    {"name": "🛡️ ترس العمالقة", "price": 8_000_000},
    {"name": "🐉 دابة التنين", "price": 250_000_000},
    {"name": "🧣 وشاح الحكام", "price": 2_500_000},
    {"name": "🧪 جرعة الحكمة", "price": 1_000_000},
    {"name": "🧪 كيميائي أحمر", "price": 1_500_000},
    {"name": "💍 خاتم الزواج", "price": 7_000_000},
    {"name": "🎽 زي المحارب", "price": 4_500_000},
    {"name": "🧤 قفازات المهارة", "price": 3_200_000},
    {"name": "👑 تاج الهيمنة", "price": 300_000_000}
]

def load_prices():
    if not os.path.exists(PRICE_FILE):
        base_prices = {item["name"]: item["price"] for item in store_items}
        with open(PRICE_FILE, "w") as f:
            json.dump(base_prices, f, indent=4, ensure_ascii=False)
    with open(PRICE_FILE, "r") as f:
        return json.load(f)

def save_prices(prices):
    with open(PRICE_FILE, "w") as f:
        json.dump(prices, f, indent=4, ensure_ascii=False)

def fluctuate_price(base_price):
    fluctuation = random.uniform(-0.2, 0.25)
    return max(1, int(base_price * (1 + fluctuation)))

def get_price_indicator(old, new):
    if new > old:
        return "⬆️"
    elif new < old:
        return "⬇️"
    else:
        return "↔️"
