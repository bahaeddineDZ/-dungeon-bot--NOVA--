
import random

# ====== مكافآت الألعاب ======
GAME_REWARDS = {
    "حجر_ورقة_مقص": {
        "win": 2000,
        "draw": 500,
        "lose": 100
    },
    "تخمين": {
        "win_base": 5000,
        "win_per_attempt": 1000,
        "lose": 300
    },
    "ذاكرة": {
        "win": 3000,
        "lose": 300
    },
    "رياضيات": {
        "win": 1500,
        "lose": 200
    },
    "كلمات": {
        "win": 2500,
        "lose": 250
    }
}

# ====== مكافآت العمل حسب المهنة ======
JOB_REWARDS = {
    "مواطن": {"dollars": (60000, 90000), "gold": 0},
    "رسام": {"dollars": (60000, 90000), "gold": 0},
    "مدرب": {"dollars": (60000, 90000), "gold": 0},
    "مقدم": {"dollars": (40000, 60000), "gold": (10, 20)},
    "جنيرال": {"dollars": (40000, 60000), "gold": (10, 20)},
    "وزير": {"dollars": (40000, 60000), "gold": (10, 20)},
    "ملك": {"dollars": 0, "gold": (20, 40)},
    "إمبراطور": {"dollars": 0, "gold": (20, 40)}
}

# ====== المكافأة اليومية ======
DAILY_REWARD = {
    "دولار": 100000,
    "ذهب": 10,
    "ماس": 1
}

# ====== مكافآت الزراعة ======
FARMING_REWARDS = {
    "🌾 قمح": {"min": 1000, "max": 3000},
    "🥕 جزر": {"min": 2000, "max": 4000},
    "🍅 طماطم": {"min": 3500, "max": 6000},
    "🌽 ذرة": {"min": 6000, "max": 9000},
    "🍓 فراولة": {"min": 10000, "max": 15000}
}

# ====== مكافآت الصيد ======
FISHING_REWARDS = {
    "🐟": {"name": "سمك عادي", "min": 10000, "max": 50000},
    "🐠": {"name": "استوائي", "min": 30000, "max": 150000},
    "🦈": {"name": "قرش", "min": 100000, "max": 200000},
    "🦐": {"name": "روبيان", "min": 15000, "max": 40000},
    "🦑": {"name": "حبار", "min": 12000, "max": 25000},
    "🦀": {"name": "سلطعون", "min": 8000, "max": 20000}
}

# ====== دوال حساب المكافآت ======

def calculate_work_reward(job_title):
    """حساب مكافأة العمل حسب المهنة"""
    if job_title not in JOB_REWARDS:
        job_title = "مواطن"
    
    reward_info = JOB_REWARDS[job_title]
    dollars = 0
    gold = 0
    
    if reward_info["dollars"] != 0:
        dollars = random.randint(*reward_info["dollars"])
    
    if reward_info["gold"] != 0:
        gold = random.randint(*reward_info["gold"])
    
    return {"دولار": dollars, "ذهب": gold}

def calculate_game_reward(game_name, result, extra_data=None):
    """حساب مكافأة الألعاب حسب النتيجة"""
    if game_name not in GAME_REWARDS:
        return 0
    
    rewards = GAME_REWARDS[game_name]
    
    if game_name == "تخمين" and result == "win" and extra_data:
        attempts_left = extra_data.get("attempts_left", 0)
        return rewards["win_base"] + (attempts_left * rewards["win_per_attempt"])
    
    return rewards.get(result, 0)

def calculate_farming_reward(crop_name):
    """حساب مكافأة الزراعة"""
    if crop_name not in FARMING_REWARDS:
        return 0
    
    reward_info = FARMING_REWARDS[crop_name]
    return random.randint(reward_info["min"], reward_info["max"])

def calculate_fishing_reward(fish_emoji):
    """حساب مكافأة الصيد"""
    if fish_emoji not in FISHING_REWARDS:
        return 0
    
    reward_info = FISHING_REWARDS[fish_emoji]
    return random.randint(reward_info["min"], reward_info["max"])

def get_daily_reward():
    """الحصول على المكافأة اليومية"""
    return DAILY_REWARD.copy()

def calculate_trade_result(amount):
    """حساب نتيجة التداول"""
    success = random.random() < 0.6  # 60% نسبة النجاح
    
    if success:
        multiplier = random.uniform(1.1, 1.9)
        profit = int(amount * multiplier) - amount
        return {"success": True, "profit": profit, "new_balance_change": profit}
    else:
        multiplier = random.uniform(0.2, 0.95)
        loss = amount - int(amount * multiplier)
        return {"success": False, "profit": -loss, "new_balance_change": -loss}

def calculate_investment_result(amount):
    """حساب نتيجة الاستثمار"""
    percent = random.randint(-40, 50)
    result_amount = int(amount * (1 + (percent / 100)))
    profit = result_amount - amount
    
    return {
        "percent": percent,
        "result_amount": result_amount,
        "profit": profit,
        "success": percent >= 0
    }

# ====== مكافآت الاختصاصات ======
def calculate_specialization_bonus(spec_type, spec_rank, base_amount):
    """حساب مكافأة الاختصاص"""
    if spec_type == "نينجا":
        # نينجا يحصل على مكافأة نهب إضافية
        rank_multipliers = {"نبيل": 1.2, "شجاع": 1.4, "فارسي": 1.6, "أسطوري": 1.8}
        multiplier = rank_multipliers.get(spec_rank, 1.2)
        return int(base_amount * multiplier)
    
    return base_amount

# ====== مكافآت النشاطات الخاصة ======
SPECIAL_ACTIVITY_REWARDS = {
    "first_login": {"دولار": 50000, "ذهب": 5, "ماس": 0},
    "weekly_bonus": {"دولار": 500000, "ذهب": 50, "ماس": 5},
    "monthly_bonus": {"دولار": 2000000, "ذهب": 200, "ماس": 20}
}

def get_special_reward(activity_type):
    """الحصول على مكافأة نشاط خاص"""
    return SPECIAL_ACTIVITY_REWARDS.get(activity_type, {"دولار": 0, "ذهب": 0, "ماس": 0})
