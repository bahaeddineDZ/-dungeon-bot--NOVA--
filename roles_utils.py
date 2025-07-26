# roles_utils.py

import random
import time
from datetime import datetime, timedelta
# داخل roles_utils.py أو utils.py

def is_under_protection(user_data):
    protection_end = user_data.get("protection_until", 0)
    return time.time() < protection_end

# جميع الاختصاصات والرتب
ranks = ["نبيل", "شجاع", "فارسي", "أسطوري"]
roles = ["محارب", "شامان", "سورا", "نينجا"]

 def get_role_level_bonus(role, rank_name):
    if rank_name not in ranks:
        return None
    index = ranks.index(rank_name)

    if role == "محارب":
        return {"type": "revenge", "percentage": [40, 60, 80, 100][index]}
    elif role == "شامان":
        return {"type": "shield", "duration": [60, 90, 120, 150][index]}  # بالدقائق
    elif role == "نينجا":
        return {"type": "steal_boost", "percentage": [20, 40, 60, 80][index]}
    if role == "سورا":
        return {"type": "reflect_steal", "percentage": [20, 30, 40, 50][index]}
    else:
        return None

# 🔁 وظيفة للمحارب: استرجاع نسبة من الدولار المسروق
def calculate_revenge_amount(role, rank, stolen_amount):
    if role != "محارب":
        return 0
    bonus = get_role_level_bonus(role, rank)
    return int((bonus["percentage"] / 100) * stolen_amount)

# 🥷 وظيفة للنينجا: حساب نسبة النهب حسب الرتبة
def calculate_ninja_steal(role, rank, target_balance):
    if role != "نينجا":
        return 0
    bonus = get_role_level_bonus(role, rank)
    return int((bonus["percentage"] / 100) * target_balance)
def does_steal_fail(chance_percent=20):
    """إرجاع True إذا فشل النهب (حسب النسبة)"""
    return random.randint(1, 100) <= chance_percent

# 🛡️ وظيفة للشامان: تفعيل الحماية
def activate_protection(user_data, role, rank):
    if role != "شامان":
        return
    bonus = get_role_level_bonus(role, rank)
    duration_minutes = bonus["duration"]
    protection_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    user_data["protection_until"] = protection_until.isoformat()


# التحقق من وجود حماية مفعّلة
def is_under_protection(user_data):
    protection_until = user_data.get("protection_until")
    if protection_until:
        return datetime.utcnow() < datetime.fromisoformat(protection_until)
    return False

# إزالة الحماية
def remove_protection(user_data):
    user_data.pop("protection_until", None)

# 🛡️ وظيفة سورا: تفعيل الحماية

def reflect_theft(attacker_data, defender_data):
    defender_role = defender_data.get("specialization", {}).get("type")
    defender_rank = defender_data.get("specialization", {}).get("rank", 1)

    if defender_role != "سورا":
        return False  # ليس سورا، لا شيء يحدث

    bonus = get_role_level_bonus(defender_role, defender_rank)
    if not bonus:
        return False

    reflection_percent = bonus.get("reflection", 0)

    # الموارد التي ستُعكس
    for currency in ["دولار", "ذهب", "ماس"]:
        stolen_amount = attacker_data.get("balance", {}).get(currency, 0)
        reflected_amount = int(stolen_amount * reflection_percent / 100)

        # خصم من المهاجم
        attacker_data["balance"][currency] = max(
            0, attacker_data["balance"].get(currency, 0) - reflected_amount)

        # إضافة للمدافع
        defender_data["balance"][currency] = defender_data["balance"].get(currency, 0) + reflected_amount

    return True  # تم العكس
