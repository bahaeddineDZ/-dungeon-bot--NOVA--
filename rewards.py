
import random

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

# ====== المكافآت اليومية ======
DAILY_REWARD = {
    "دولار": 100000,
    "ذهب": 25,
    "ماس": 1,
    "experience": 200
}

# ====== مكافآت الألعاب ======
GAME_REWARDS = {
    "حجر_ورقة_مقص": {
        "win": 2000,
        "lose": 100,
        "draw": 500
    },
    "تخمين": {
        "base": 8000,
        "bonus_per_attempt": 500,
        "consolation": 500
    },
    "ذاكرة": {
        "success": 3000,
        "fail": 300
    },
    "رياضيات": {
        "correct": 1500,
        "wrong": 200
    },
    "كلمات": {
        "correct": 2500,
        "wrong": 250
    }
}

# ====== مكافآت الوظائف ======
JOB_REWARDS = {
    "مواطن": {"دولار": [60000, 90000], "ذهب": [0, 0]},
    "رسام": {"دولار": [60000, 90000], "ذهب": [0, 0]},
    "طبيب": {"دولار": [60000, 90000], "ذهب": [0, 0]},
    "مقدم": {"دولار": [40000, 60000], "ذهب": [10, 20]},
    "جنيرال": {"دولار": [40000, 60000], "ذهب": [10, 20]},
    "وزير": {"دولار": [40000, 60000], "ذهب": [10, 20]},
    "ملك": {"دولار": [0, 0], "ذهب": [20, 40]},
    "إمبراطور": {"دولار": [0, 0], "ذهب": [20, 40]}
}

def calculate_farming_reward(crop_emoji):
    """حساب مكافأة الزراعة"""
    if crop_emoji not in FARMING_REWARDS:
        return 0
    
    reward_info = FARMING_REWARDS[crop_emoji]
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
    bonuses = {
        "محارب": 1.2,
        "شامان": 1.0,
        "نينجا": 1.4,
        "سورا": 1.1
    }
    
    base_bonus = bonuses.get(spec_type, 1.0)
    rank_bonus = 1 + (spec_rank - 1) * 0.1
    
    return int(base_amount * base_bonus * rank_bonus)

def get_game_reward(game_type, result):
    """حساب مكافأة الألعاب"""
    game_rewards = GAME_REWARDS.get(game_type, {})
    return game_rewards.get(result, 0)

def calculate_work_reward(job_title):
    """حساب مكافأة العمل"""
    job_reward = JOB_REWARDS.get(job_title, JOB_REWARDS["مواطن"])
    
    dollars = random.randint(*job_reward["دولار"])
    gold = random.randint(*job_reward["ذهب"])
    
    return {"دولار": dollars, "ذهب": gold}

def get_level_bonus(user_level):
    """حساب مكافأة المستوى"""
    if user_level >= 50:
        return {"multiplier": 2.0, "bonus_exp": 500}
    elif user_level >= 25:
        return {"multiplier": 1.5, "bonus_exp": 300}
    elif user_level >= 10:
        return {"multiplier": 1.2, "bonus_exp": 150}
    else:
        return {"multiplier": 1.0, "bonus_exp": 0}

def calculate_streak_bonus(streak_days):
    """حساب مكافأة الاستمرارية"""
    if streak_days >= 30:
        return {"multiplier": 3.0, "bonus_diamonds": 5}
    elif streak_days >= 14:
        return {"multiplier": 2.0, "bonus_diamonds": 3}
    elif streak_days >= 7:
        return {"multiplier": 1.5, "bonus_diamonds": 1}
    else:
        return {"multiplier": 1.0, "bonus_diamonds": 0}

# ====== مكافآت خاصة ======
SPECIAL_REWARDS = {
    "first_win": {"دولار": 50000, "ذهب": 10, "ماس": 2},
    "perfect_score": {"دولار": 100000, "ذهب": 25, "ماس": 3},
    "weekly_achievement": {"دولار": 200000, "ذهب": 50, "ماس": 5},
    "monthly_champion": {"دولار": 1000000, "ذهب": 200, "ماس": 20}
}

def get_special_reward(reward_type):
    """الحصول على مكافأة خاصة"""
    return SPECIAL_REWARDS.get(reward_type, {})

def calculate_total_wealth(balance):
    """حساب الثروة الإجمالية"""
    dollars = balance.get("دولار", 0)
    gold = balance.get("ذهب", 0)
    diamonds = balance.get("ماس", 0)
    
    # قيم التحويل
    return dollars + (gold * 50) + (diamonds * 100)

def format_reward_message(rewards):
    """تنسيق رسالة المكافآت"""
    message_parts = []
    
    if "دولار" in rewards and rewards["دولار"] > 0:
        message_parts.append(f"💵 {rewards['دولار']:,} دولار")
    
    if "ذهب" in rewards and rewards["ذهب"] > 0:
        message_parts.append(f"🪙 {rewards['ذهب']:,} ذهب")
    
    if "ماس" in rewards and rewards["ماس"] > 0:
        message_parts.append(f"💎 {rewards['ماس']:,} ماس")
    
    if "experience" in rewards and rewards["experience"] > 0:
        message_parts.append(f"⭐ {rewards['experience']:,} خبرة")
    
    return " | ".join(message_parts) if message_parts else "لا توجد مكافآت"
