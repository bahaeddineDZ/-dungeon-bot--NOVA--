
import os
import json
import time
from datetime import datetime

def get_rarity_color(rarity):
    """الحصول على لون الندرة"""
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
                status[f"{file_name}_missing"] = False
        
        return status
    
    @staticmethod
    def get_system_stats():
        """إحصائيات النظام"""
        stats = {
            "total_users": 0,
            "total_commands_used": 0,
            "active_cooldowns": 0,
            "system_uptime": time.time()
        }
        
        try:
            # حساب عدد المستخدمين
            if os.path.exists("users.json"):
                with open("users.json", "r", encoding="utf-8") as f:
                    users_data = json.load(f)
                    stats["total_users"] = len(users_data)
            
            # حساب التبريدات النشطة
            if os.path.exists("cooldowns.json"):
                with open("cooldowns.json", "r", encoding="utf-8") as f:
                    cooldowns_data = json.load(f)
                    current_time = time.time()
                    active_count = 0
                    
                    for user_cooldowns in cooldowns_data.values():
                        for command, last_used in user_cooldowns.items():
                            if current_time - last_used < 3600:  # آخر ساعة
                                active_count += 1
                    
                    stats["active_cooldowns"] = active_count
        
        except Exception as e:
            print(f"Error calculating system stats: {e}")
        
        return stats

def format_number(number):
    """تنسيق الأرقام"""
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    else:
        return str(number)

def calculate_percentage(current, total):
    """حساب النسبة المئوية"""
    if total == 0:
        return 0
    return (current / total) * 100

def get_time_difference(timestamp):
    """حساب الفرق الزمني"""
    current_time = time.time()
    diff = current_time - timestamp
    
    if diff < 60:
        return f"{int(diff)} ثانية"
    elif diff < 3600:
        return f"{int(diff/60)} دقيقة"
    elif diff < 86400:
        return f"{int(diff/3600)} ساعة"
    else:
        return f"{int(diff/86400)} يوم"

def validate_user_data(user_data):
    """التحقق من صحة بيانات المستخدم"""
    required_fields = ["balance", "حقيبة", "المهنة"]
    
    for field in required_fields:
        if field not in user_data:
            return False, f"Missing field: {field}"
    
    # التحقق من تنسيق الرصيد
    balance = user_data.get("balance", {})
    if not isinstance(balance, dict):
        return False, "Balance must be a dictionary"
    
    required_currencies = ["دولار", "ذهب", "ماس"]
    for currency in required_currencies:
        if currency not in balance:
            balance[currency] = 0
    
    return True, "Valid"

def backup_data():
    """نسخ احتياطي للبيانات"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_files = [
        "users.json",
        "cooldowns.json",
        "system_logs.json",
        "user_tasks.json"
    ]
    
    backup_dir = f"backup_{timestamp}"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    for file_name in backup_files:
        if os.path.exists(file_name):
            import shutil
            shutil.copy2(file_name, os.path.join(backup_dir, file_name))
    
    return backup_dir

class EventLogger:
    """مسجل الأحداث"""
    
    @staticmethod
    def log_event(event_type, user_id, details):
        """تسجيل حدث"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "user_id": str(user_id),
            "details": details
        }
        
        events_file = "events.json"
        events = []
        
        if os.path.exists(events_file):
            with open(events_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        
        events.append(event)
        
        # الاحتفاظ بآخر 1000 حدث فقط
        if len(events) > 1000:
            events = events[-1000:]
        
        with open(events_file, "w", encoding="utf-8") as f:
            json.dump(events, f, ensure_ascii=False, indent=4)

def cleanup_old_data():
    """تنظيف البيانات القديمة"""
    current_time = time.time()
    one_month_ago = current_time - (30 * 24 * 3600)  # شهر واحد
    
    # تنظيف السجلات القديمة
    if os.path.exists("system_logs.json"):
        with open("system_logs.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
        
        for log_type in logs:
            if isinstance(logs[log_type], list):
                logs[log_type] = [
                    log for log in logs[log_type]
                    if datetime.fromisoformat(log.get("timestamp", "1970-01-01")).timestamp() > one_month_ago
                ]
        
        with open("system_logs.json", "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

# متغيرات النظام العامة
SYSTEM_VERSION = "2.0.1"
LAST_UPDATE = "2024-01-15"
FEATURES = [
    "نظام اقتصادي متطور",
    "أنظمة قتال متقدمة", 
    "سراديب وتحديات",
    "زراعة وصيد",
    "ألعاب تفاعلية",
    "نظام مهام ومستويات",
    "تداول واستثمار"
]
