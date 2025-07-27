
# systems.py - وظائف مساعدة للأنظمة المختلفة

import json
import time
import random
from datetime import datetime

def format_number(number):
    """تنسيق الأرقام مع فواصل"""
    return f"{number:,}"

def calculate_percentage(current, total):
    """حساب النسبة المئوية"""
    if total == 0:
        return 0
    return round((current / total) * 100, 1)

def time_until_midnight():
    """حساب الوقت المتبقي حتى منتصف الليل"""
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    midnight += timedelta(days=1)
    return (midnight - now).total_seconds()

def generate_random_reward(min_val, max_val, multiplier=1.0):
    """توليد مكافأة عشوائية"""
    base_reward = random.randint(min_val, max_val)
    return int(base_reward * multiplier)

def validate_user_input(value, min_val=None, max_val=None):
    """التحقق من صحة إدخال المستخدم"""
    try:
        num_value = int(value)
        if min_val is not None and num_value < min_val:
            return False, f"القيمة يجب أن تكون أكبر من {min_val}"
        if max_val is not None and num_value > max_val:
            return False, f"القيمة يجب أن تكون أصغر من {max_val}"
        return True, num_value
    except ValueError:
        return False, "يجب إدخال رقم صحيح"

def get_rarity_color(rarity):
    """الحصول على لون حسب الندرة"""
    colors = {
        "شائع": 0x95a5a6,
        "غير شائع": 0x3498db,
        "نادر": 0x9b59b6,
        "أسطوري": 0xf39c12,
        "خرافي": 0xe74c3c
    }
    return colors.get(rarity, 0x95a5a6)

class SystemStatus:
    """فئة لمراقبة حالة الأنظمة"""
    
    @staticmethod
    def check_all_systems():
        """فحص جميع الأنظمة"""
        status = {
            "cooldown_system": True,
            "data_system": True,
            "logs_system": True,
            "tasks_system": True,
            "dungeons_system": True,
            "equipment_system": True
        }
        
        # فحص ملفات البيانات الأساسية
        required_files = [
            "users.json",
            "cooldowns.json", 
            "system_logs.json",
            "user_tasks.json"
        ]
        
        for file_name in required_files:
            if not os.path.exists(file_name):
                status[f"{file_name}_missing"] = True
        
        return status

# دوال مساعدة للعملات
def convert_to_base_currency(amount, currency_type):
    """تحويل العملات إلى الدولار للمقارنة"""
    rates = {
        "دولار": 1,
        "ذهب": 50,
        "ماس": 100
    }
    return amount * rates.get(currency_type, 1)

def format_currency(amount, currency_type):
    """تنسيق العملة مع الرمز المناسب"""
    symbols = {
        "دولار": "💵",
        "ذهب": "🪙", 
        "ماس": "💎"
    }
    symbol = symbols.get(currency_type, "💰")
    return f"{symbol} {format_number(amount)}"

# نظام الإنجازات (للاستخدام المستقبلي)
ACHIEVEMENTS = {
    "first_work": {
        "name": "عامل مجتهد",
        "description": "قم بالعمل لأول مرة",
        "reward": {"دولار": 10000}
    },
    "millionaire": {
        "name": "مليونير",
        "description": "اجمع مليون دولار",
        "reward": {"ذهب": 50}
    },
    "master_thief": {
        "name": "لص محترف", 
        "description": "انهب 100 مرة بنجاح",
        "reward": {"ماس": 10}
    }
}
