import json
import time
import os

FILE_PATH = "cooldown_data.json"

DEFAULT_COOLDOWN = {
    "يومي": 86400,           # 24 ساعة
    "عمل": 3600,             # ساعة واحدة
    "upgrade": 7200,         # ساعتان
    "تداول": 1800,           # 30 دقيقة
    "استثمار": 3600,        # ساعة واحدة
    "نهب": 1800,             # 30 دقيقة
    "حجر_ورقة_مقص": 300,   # 5 دقائق
    "تخمين": 600,           # 10 دقائق
    "ذاكرة": 900,           # 15 دقيقة
    "رياضيات": 300,         # 5 دقائق
    "كلمات": 600,           # 10 دقائق
    "صيد": 600,             # 10 دقائق
    "درع": 3600,            # ساعة واحدة
    # أوامر الزواج
    "زواج": 86400,          # 24 ساعة
    "هدية": 3600,           # ساعة واحدة
    "شهر_عسل": 604800,      # أسبوع
    # الألعاب الجديدة
    "لوتو": 3600,           # ساعة واحدة
    "روليت": 1800,          # 30 دقيقة
    "بلاك_جاك": 900,        # 15 دقيقة
}

COOLDOWN_FILE = "cooldowns.json"

def load_cooldowns():
    if not os.path.exists(COOLDOWN_FILE):
        return {}
    with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_cooldowns(cooldowns):
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(cooldowns, f, ensure_ascii=False, indent=4)

def check_cooldown(user_id, command):
    user_id = str(user_id)
    cooldowns = load_cooldowns()
    user_cooldowns = cooldowns.get(user_id, {})

    current_time = int(time.time())
    last_used = user_cooldowns.get(command, 0)
    cooldown_duration = DEFAULT_COOLDOWN.get(command, 0)

    time_passed = current_time - last_used

    if time_passed >= cooldown_duration:
        return True, ""
    else:
        time_left = cooldown_duration - time_passed
        return False, format_time(time_left)

def update_cooldown(user_id, command):
    user_id = str(user_id)
    cooldowns = load_cooldowns()

    if user_id not in cooldowns:
        cooldowns[user_id] = {}

    cooldowns[user_id][command] = int(time.time())
    save_cooldowns(cooldowns)

def format_time(seconds):
    if seconds < 60:
        return f"{seconds} ثانية"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes} دقيقة و {remaining_seconds} ثانية"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} ساعة و {minutes} دقيقة"