import json
import random
import time
import os
from datetime import datetime, timedelta
import discord
from discord.ext import commands

# ملفات البيانات
DUNGEONS_FILE = "dungeons_data.json"
EQUIPMENT_FILE = "equipment_data.json"
DUNGEON_COOLDOWNS_FILE = "dungeon_cooldowns.json"

# إعدادات التبريد (بالثواني)
DUNGEON_COOLDOWNS = {
    "entry": 1800,      # 30 دقيقة بين دخول السراديب
    "daily_limit": 86400,  # حد أقصى 5 محاولات يومياً
    "boss_defeat": 3600,   # ساعة واحدة بعد هزيمة زعيم معين
    "death_penalty": 900   # 15 دقيقة عقوبة الموت
}

# ======== تعريف السراديب المحدثة ========
DUNGEONS = {
    "🏚️ سرداب المبتدئين": {
        "level": 1,
        "tier": "عادي",
        "description": "سرداب مهجور مليء بالجرذان والهياكل العظمية الضعيفة. مناسب للمحاربين الجدد.",
        "boss": "💀 هيكل عظمي قديم",
        "boss_hp": 200,
        "boss_attack": 30,
        "boss_defense": 15,
        "boss_abilities": ["🩸 ضربة نازفة", "🛡️ تعافي بطيء"],
        "entry_cost": {"ماس": 2},
        "rewards": {
            "ذهب": [15, 35],
            "دولار": [75000, 150000],
            "experience": [100, 200]
        },
        "rare_drops": {
            "🗡️ سيف العظام النادر": 0.05,  # 5% فرصة
            "🧪 جرعة قوة صغيرة": 0.15
        },
        "required_level": 1,
        "estimated_time": "5-10 دقائق"
    },
    "🌊 كهف الأمواج": {
        "level": 2,
        "description": "كهف مائي تحرسه وحوش البحر. احذر من الأمواج العاتية!",
        "boss": "🐙 أخطبوط عملاق",
        "boss_hp": 300,
        "boss_attack": 40,
        "boss_defense": 20,
        "entry_cost": {"ماس": 3},
        "rewards": {
            "ذهب": [25, 50],
            "دولار": [100000, 200000]
        },
        "required_level": 5
    },
    "🔥 برج اللهب": {
        "level": 3,
        "description": "برج محاط بالنيران الأبدية. وحوش النار تملأ كل طابق.",
        "boss": "🔥 تنين النار الأحمر",
        "boss_hp": 500,
        "boss_attack": 60,
        "boss_defense": 35,
        "entry_cost": {"ماس": 5},
        "rewards": {
            "ذهب": [50, 100],
            "دولار": [200000, 400000]
        },
        "required_level": 15
    },
    "💀 قصر الموت": {
        "level": 4,
        "description": "قصر مسكون بأرواح المحاربين الساقطين. الموت يجول في كل زاوية.",
        "boss": "👻 ملك الأشباح",
        "boss_hp": 800,
        "boss_attack": 85,
        "boss_defense": 50,
        "entry_cost": {"ماس": 8},
        "rewards": {
            "ذهب": [100, 200],
            "دولار": [400000, 800000]
        },
        "required_level": 25
    },
    "⚡ عرش الآلهة": {
        "level": 5,
        "tier": "أسطوري",
        "description": "أقدس الأماكن وأخطرها. هنا يقيم إله الحرب المنتقم.",
        "boss": "⚡ إله الحرب الأسطوري",
        "boss_hp": 1500,
        "boss_attack": 150,
        "boss_defense": 100,
        "boss_abilities": ["⚡ صاعقة الغضب", "🌪️ عاصفة الدمار", "🛡️ درع مقدس"],
        "entry_cost": {"ماس": 20},
        "rewards": {
            "ذهب": [300, 500],
            "دولار": [1200000, 2000000],
            "experience": [800, 1200]
        },
        "rare_drops": {
            "👑 تاج إله الحرب": 0.01,  # 1% فرصة نادرة جداً
            "⚡ صولجان البرق": 0.03,
            "🧪 إكسير الآلهة": 0.08
        },
        "required_level": 50,
        "estimated_time": "20-30 دقيقة"
    },
    "🌋 جحيم التنانين": {
        "level": 6,
        "tier": "ملحمي",
        "description": "بركان ملتهب يسكنه أقوى التنانين. فقط الأبطال الأسطوريون يجرؤون على دخوله.",
        "boss": "🐲 ملك التنانين النارية",
        "boss_hp": 2000,
        "boss_attack": 200,
        "boss_defense": 120,
        "boss_abilities": ["🔥 نفس النار المدمر", "🌋 ثوران بركاني", "🛡️ قشور ماسية", "💀 لعنة التنين"],
        "entry_cost": {"ماس": 35},
        "rewards": {
            "ذهب": [500, 800],
            "دولار": [2000000, 3500000],
            "experience": [1500, 2000]
        },
        "rare_drops": {
            "🐲 قلب التنين الأبدي": 0.005,  # 0.5% نادر جداً
            "🔥 درع قشور التنين": 0.02,
            "🗡️ نصل اللهب المقدس": 0.04
        },
        "required_level": 75,
        "estimated_time": "30-45 دقيقة"
    },
    "🌌 بُعد الظلام اللانهائي": {
        "level": 7,
        "tier": "أسطوري+",
        "description": "بُعد مظلم خارج حدود الواقع. هنا تسكن كائنات من عوالم أخرى لا يمكن تصورها.",
        "boss": "👁️ عين الفراغ الأزلية",
        "boss_hp": 3000,
        "boss_attack": 300,
        "boss_defense": 180,
        "boss_abilities": ["🌌 انهيار الواقع", "👁️ نظرة الجنون", "🕳️ ثقب أسود", "💀 محو الوجود"],
        "entry_cost": {"ماس": 75},
        "rewards": {
            "ذهب": [1000, 1500],
            "دولار": [5000000, 8000000],
            "experience": [3000, 4000]
        },
        "rare_drops": {
            "👁️ عين البصيرة الكونية": 0.001,  # 0.1% نادر للغاية
            "🌌 عباءة النجوم": 0.01,
            "🔮 جوهرة الأبعاد": 0.03
        },
        "required_level": 100,
        "estimated_time": "45-60 دقيقة"
    }
}

# ======== متجر العتاد ========
EQUIPMENT_SHOP = {
    # أسلحة
    "⚔️ سيف خشبي": {
        "type": "weapon",
        "attack": 10,
        "defense": 0,
        "price": {"ماس": 2},
        "description": "سيف بسيط للمبتدئين"
    },
    "🗡️ سيف فولاذي": {
        "type": "weapon",
        "attack": 25,
        "defense": 0,
        "price": {"ماس": 5},
        "description": "سيف قوي من الفولاذ المصقول"
    },
    "⚔️ سيف التنين": {
        "type": "weapon",
        "attack": 50,
        "defense": 5,
        "price": {"ماس": 15},
        "description": "سيف أسطوري مصنوع من قشور التنين"
    },
    "🔱 رمح الآلهة": {
        "type": "weapon",
        "attack": 80,
        "defense": 10,
        "price": {"ماس": 30},
        "description": "رمح مقدس يحمل قوة الآلهة"
    },

    # دروع
    "🛡️ درع جلدي": {
        "type": "armor",
        "attack": 0,
        "defense": 15,
        "price": {"ماس": 3},
        "description": "درع خفيف من الجلد المدبوغ"
    },
    "🛡️ درع حديدي": {
        "type": "armor",
        "attack": 0,
        "defense": 30,
        "price": {"ماس": 7},
        "description": "درع قوي من الحديد المقوى"
    },
    "🛡️ درع التنين": {
        "type": "armor",
        "attack": 5,
        "defense": 60,
        "price": {"ماس": 20},
        "description": "درع أسطوري مصنوع من قشور التنين الذهبي"
    },

    # خوذات
    "⛑️ خوذة برونزية": {
        "type": "helmet",
        "attack": 2,
        "defense": 8,
        "price": {"ماس": 2},
        "description": "خوذة بسيطة من البرونز"
    },
    "👑 تاج المحارب": {
        "type": "helmet",
        "attack": 8,
        "defense": 15,
        "price": {"ماس": 12},
        "description": "تاج يرمز لشجاعة المحاربين"
    },

    # خواتم
    "💍 خاتم القوة": {
        "type": "ring",
        "attack": 15,
        "defense": 5,
        "price": {"ماس": 10},
        "description": "خاتم سحري يزيد من القوة"
    },
    "💍 خاتم الحماية": {
        "type": "ring",
        "attack": 3,
        "defense": 20,
        "price": {"ماس": 10},
        "description": "خاتم سحري يوفر حماية إضافية"
    },

    # مستهلكات
    "🧪 جرعة الشفاء": {
        "type": "consumable",
        "effect": "heal",
        "value": 100,
        "price": {"ماس": 1},
        "description": "تعيد 100 نقطة صحة"
    },
    "⚡ جرعة القوة": {
        "type": "consumable",
        "effect": "attack_boost",
        "value": 20,
        "duration": 3,
        "price": {"ماس": 3},
        "description": "تزيد الهجوم بـ 20 نقطة لـ 3 جولات"
    }
}

# ======== مكافآت الاختصاصات ========
SPECIALIZATION_BONUSES = {
    "محارب": {
        "attack_bonus": 1.2,
        "defense_bonus": 1.1,
        "hp_bonus": 1.3,
        "special_ability": "ضربة قاتلة: فرصة 15% لضربة مضاعفة",
        "dungeon_bonus": "مقاومة أكبر للأضرار الجسدية"
    },
    "شامان": {
        "attack_bonus": 1.0,
        "defense_bonus": 1.3,
        "hp_bonus": 1.4,
        "special_ability": "شفاء ذاتي: استعادة 10% من الصحة كل جولة",
        "dungeon_bonus": "مقاومة للسحر والتأثيرات السلبية"
    },
    "نينجا": {
        "attack_bonus": 1.4,
        "defense_bonus": 0.9,
        "hp_bonus": 1.1,
        "special_ability": "هجوم خاطف: هجمتان في جولة واحدة أحياناً",
        "dungeon_bonus": "فرصة تجنب الهجمات بنسبة 20%"
    },
    "سورا": {
        "attack_bonus": 1.1,
        "defense_bonus": 1.2,
        "hp_bonus": 1.2,
        "special_ability": "عكس الضرر: 25% من الضرر المُستقبل يُعاد للعدو",
        "dungeon_bonus": "امتصاص جزء من طاقة الأعداء المهزومين"
    }
}

# ======== وظائف النظام ========

def load_dungeons_data():
    """تحميل بيانات السراديب"""
    if not os.path.exists(DUNGEONS_FILE):
        return {}
    with open(DUNGEONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dungeons_data(data):
    """حفظ بيانات السراديب"""
    with open(DUNGEONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_equipment_data():
    """تحميل بيانات العتاد"""
    if not os.path.exists(EQUIPMENT_FILE):
        return {}
    with open(EQUIPMENT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_equipment_data(data):
    """حفظ بيانات العتاد"""
    with open(EQUIPMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_user_dungeon_progress(user_id):
    """جلب تقدم المستخدم في السراديب"""
    data = load_dungeons_data()
    return data.get(str(user_id), {
        "completed_dungeons": [],
        "total_victories": 0,
        "total_defeats": 0,
        "daily_attempts": {},
        "best_times": {}
    })

def update_user_dungeon_progress(user_id, dungeon_name, victory, battle_time=None):
    """تحديث تقدم المستخدم"""
    data = load_dungeons_data()
    user_progress = data.get(str(user_id), {
        "completed_dungeons": [],
        "total_victories": 0,
        "total_defeats": 0,
        "daily_attempts": {},
        "best_times": {}
    })

    # تحديث الإحصائيات
    if victory:
        user_progress["total_victories"] += 1
        if dungeon_name not in user_progress["completed_dungeons"]:
            user_progress["completed_dungeons"].append(dungeon_name)

        # تحديث أفضل وقت
        if battle_time and (dungeon_name not in user_progress["best_times"] or 
                           battle_time < user_progress["best_times"][dungeon_name]):
            user_progress["best_times"][dungeon_name] = battle_time
    else:
        user_progress["total_defeats"] += 1

    # تحديث المحاولات اليومية
    today = datetime.now().strftime("%Y-%m-%d")
    user_progress["daily_attempts"][today] = user_progress["daily_attempts"].get(today, 0) + 1

    data[str(user_id)] = user_progress
    save_dungeons_data(data)

def get_user_equipment(user_id):
    """جلب عتاد المستخدم"""
    data = load_equipment_data()
    return data.get(str(user_id), {
        "weapon": None,
        "armor": None,
        "helmet": None,
        "ring": None,
        "consumables": []
    })

def load_dungeon_cooldowns():
    """تحميل بيانات التبريد"""
    if not os.path.exists(DUNGEON_COOLDOWNS_FILE):
        return {}
    with open(DUNGEON_COOLDOWNS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dungeon_cooldowns(cooldowns):
    """حفظ بيانات التبريد"""
    with open(DUNGEON_COOLDOWNS_FILE, "w", encoding="utf-8") as f:
        json.dump(cooldowns, f, ensure_ascii=False, indent=4)

def check_dungeon_cooldown(user_id, cooldown_type, dungeon_name=None):
    """فحص تبريد محدد"""
    cooldowns = load_dungeon_cooldowns()
    user_cooldowns = cooldowns.get(str(user_id), {})
    current_time = time.time()

    # إنشاء مفتاح فريد للتبريد
    cooldown_key = f"{cooldown_type}_{dungeon_name}" if dungeon_name else cooldown_type
    last_time = user_cooldowns.get(cooldown_key, 0)

    time_passed = current_time - last_time
    required_time = DUNGEON_COOLDOWNS.get(cooldown_type, 0)

    if time_passed >= required_time:
        return True, 0
    else:
        remaining = required_time - time_passed
        return False, remaining

def update_dungeon_cooldown(user_id, cooldown_type, dungeon_name=None):
    """تحديث تبريد محدد"""
    cooldowns = load_dungeon_cooldowns()
    user_cooldowns = cooldowns.setdefault(str(user_id), {})

    cooldown_key = f"{cooldown_type}_{dungeon_name}" if dungeon_name else cooldown_type
    user_cooldowns[cooldown_key] = time.time()

    save_dungeon_cooldowns(cooldowns)

def format_cooldown_time(seconds):
    """تنسيق وقت التبريد"""
    if seconds < 60:
        return f"{int(seconds)} ثانية"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes} دقيقة و {secs} ثانية"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours} ساعة و {minutes} دقيقة"

def can_enter_dungeon(user_id, dungeon_name):
    """فحص إمكانية دخول السرداب مع نظام التبريد المتطور"""
    from data_utils import load_data

    dungeon = DUNGEONS[dungeon_name]
    user_data = load_data().get(str(user_id), {})

    # فحص المستوى المطلوب
    user_level = user_data.get("level", 1)
    if user_level < dungeon["required_level"]:
        return False, f"❌ تحتاج إلى مستوى {dungeon['required_level']} على الأقل لدخول هذا السرداب"

    # فحص تبريد الدخول العام
    can_enter, remaining = check_dungeon_cooldown(user_id, "entry")
    if not can_enter:
        time_str = format_cooldown_time(remaining)
        return False, f"⏳ يجب الانتظار {time_str} قبل دخول أي سرداب آخر"

    # فحص تبريد الزعيم المحدد
    can_fight_boss, boss_remaining = check_dungeon_cooldown(user_id, "boss_defeat", dungeon_name)
    if not can_fight_boss:
        time_str = format_cooldown_time(boss_remaining)
        return False, f"⏳ لقد هزمت هذا الزعيم مؤخراً. انتظر {time_str} لمواجهته مجدداً"

    # فحص عقوبة الموت
    can_fight_after_death, death_remaining = check_dungeon_cooldown(user_id, "death_penalty")
    if not can_fight_after_death:
        time_str = format_cooldown_time(death_remaining)
        return False, f"💀 عقوبة الهزيمة نشطة. انتظر {time_str} للتعافي"

    # فحص المحاولات اليومية المحسنة
    progress = get_user_dungeon_progress(user_id)
    today = datetime.now().strftime("%Y-%m-%d")
    daily_attempts = progress["daily_attempts"].get(today, 0)

    # حد أقصى 5 محاولات للسراديب العادية، 3 للسراديب الأسطورية
    max_attempts = 3 if dungeon.get("tier") in ["أسطوري", "ملحمي", "أسطوري+"] else 5

    if daily_attempts >= max_attempts:
        return False, f"❌ لقد استنفدت محاولاتك اليومية ({daily_attempts}/{max_attempts})"

    # فحص الماس المطلوب
    required_diamonds = dungeon["entry_cost"]["ماس"]
    user_diamonds = user_data.get("balance", {}).get("ماس", 0)

    if user_diamonds < required_diamonds:
        return False, f"❌ تحتاج إلى {required_diamonds} ماس للدخول (لديك {user_diamonds})"

    # فحص متطلبات خاصة للسراديب المتقدمة
    if dungeon["level"] >= 6:
        victories = progress["total_victories"]
        if victories < 10:
            return False, f"❌ تحتاج إلى {10 - victories} انتصارات إضافية في السراديب لفتح هذا المستوى"

    return True, f"✅ يمكنك دخول السرداب ({daily_attempts + 1}/{max_attempts} محاولات اليوم)"

def calculate_combat_stats(user_data, equipment):
    """حساب الإحصائيات القتالية"""
    specialization = user_data.get("specialization", {})
    spec_type = specialization.get("type", "محارب") if specialization else "محارب"
    spec_rank = specialization.get("rank", 1) if specialization else 1
    user_level = user_data.get("level", 1)

    # الإحصائيات الأساسية
    base_hp = 100 + (user_level * 10)
    base_attack = 20 + (user_level * 2)
    base_defense = 10 + (user_level * 1)

    # مكافآت الاختصاص
    spec_bonus = SPECIALIZATION_BONUSES.get(spec_type, SPECIALIZATION_BONUSES["محارب"])

    # تطبيق مكافآت الاختصاص
    hp = int(base_hp * spec_bonus["hp_bonus"] * (1 + (spec_rank - 1) * 0.1))
    attack = int(base_attack * spec_bonus["attack_bonus"] * (1 + (spec_rank - 1) * 0.1))
    defense = int(base_defense * spec_bonus["defense_bonus"] * (1 + (spec_rank - 1) * 0.1))

    # مكافآت العتاد
    for slot, item_name in equipment.items():
        if item_name and slot != "consumables":
            item_stats = EQUIPMENT_SHOP.get(item_name, {})
            attack += item_stats.get("attack", 0)
            defense += item_stats.get("defense", 0)

    return {
        "hp": hp,
        "max_hp": hp,
        "attack": attack,
        "defense": defense,
        "specialization": spec_type,
        "rank": spec_rank
    }

def simulate_dungeon_battle(player_stats, dungeon_name):
    """محاكاة معركة السرداب المحسنة مع قدرات الزعماء"""
    dungeon = DUNGEONS[dungeon_name]
    battle_log = []

    # إحصائيات الزعيم
    boss_hp = dungeon["boss_hp"]
    boss_max_hp = boss_hp
    boss_attack = dungeon["boss_attack"]
    boss_defense = dungeon["boss_defense"]
    boss_abilities = dungeon.get("boss_abilities", [])

    # حالات خاصة للزعيم
    boss_status = {
        "rage_mode": False,
        "shield_active": False,
        "ability_cooldown": 0
    }

    # إحصائيات اللاعب
    player_hp = player_stats["hp"]
    player_max_hp = player_hp
    player_attack = player_stats["attack"]
    player_defense = player_stats["defense"]
    spec_type = player_stats["specialization"]

    battle_log.append("⚔️ بدء المعركة!")
    battle_log.append(f"🛡️ أنت: {player_hp} HP | ⚔️ {player_attack} ATK | 🛡️ {player_defense} DEF")
    battle_log.append(f"👹 {dungeon['boss']}: {boss_hp} HP | ⚔️ {boss_attack} ATK | 🛡️ {boss_defense} DEF")
    battle_log.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    turn = 1

    while player_hp > 0 and boss_hp > 0:
        battle_log.append(f"🎯 الجولة {turn}")

        # هجوم اللاعب
        damage_to_boss = max(1, player_attack - boss_defense)

        # قدرات خاصة بالاختصاص
        special_happened = False

        if spec_type == "محارب" and random.random() < 0.15:
            damage_to_boss *= 2
            battle_log.append("💥 ضربة قاتلة! الضرر مضاعف!")
            special_happened = True
        elif spec_type == "نينجا" and random.random() < 0.25:
            damage_to_boss += max(1, (player_attack // 2) - boss_defense)
            battle_log.append("⚡ هجوم خاطف! هجمة إضافية!")
            special_happened = True
        elif spec_type == "سورا" and random.random() < 0.20:
            reflected_damage = damage_to_boss // 4
            battle_log.append(f"🔮 عكس الضرر! الزعيم تلقى {reflected_damage} ضرر إضافي!")
            damage_to_boss += reflected_damage
            special_happened = True

        boss_hp -= damage_to_boss
        battle_log.append(f"⚔️ أنت تهاجم: -{damage_to_boss} HP للزعيم (متبقي: {max(0, boss_hp)})")

        if boss_hp <= 0:
            break

        # هجوم الزعيم مع قدرات خاصة
        base_damage = max(1, boss_attack - player_defense)

        # فحص قدرات الزعيم الخاصة
        boss_used_ability = False
        if boss_abilities and boss_status["ability_cooldown"] <= 0 and random.random() < 0.3:
            ability = random.choice(boss_abilities)
            boss_status["ability_cooldown"] = 3
            boss_used_ability = True

            if "صاعقة الغضب" in ability:
                base_damage = int(base_damage * 1.5)
                battle_log.append(f"⚡ {ability}! الضرر مضاعف!")
            elif "درع مقدس" in ability:
                boss_status["shield_active"] = True
                battle_log.append(f"🛡️ {ability}! الزعيم محمي للجولات القادمة!")
            elif "نفس النار المدمر" in ability:
                base_damage = int(base_damage * 2)
                battle_log.append(f"🔥 {ability}! هجوم مدمر!")
            elif "نظرة الجنون" in ability:
                if random.random() < 0.5:
                    battle_log.append(f"👁️ {ability}! تجمدت من الرعب لجولة واحدة!")
                    player_hp -= base_damage
                    battle_log.append(f"👹 الزعيم يهاجم بلا مقاومة: -{base_damage} HP")
                    turn += 1
                    continue

        # تقليل تبريد القدرات
        if boss_status["ability_cooldown"] > 0:
            boss_status["ability_cooldown"] -= 1

        # وضع الغضب عند انخفاض الصحة
        if boss_hp < boss_max_hp * 0.3 and not boss_status["rage_mode"]:
            boss_status["rage_mode"] = True
            boss_attack = int(boss_attack * 1.3)
            battle_log.append("😡 الزعيم دخل في وضع الغضب! هجومه زاد بنسبة 30%!")

        # حساب الضرر النهائي للاعب
        final_damage = base_damage

        # تقليل الضرر إذا كان الدرع نشطاً
        if boss_status["shield_active"]:
            final_damage = int(final_damage * 0.7)
            boss_status["shield_active"] = False

        # قدرة التجنب للنينجا
        if spec_type == "نينجا" and random.random() < 0.25:
            battle_log.append("💨 تجنبت الهجوم بخفة النينجا!")
        else:
            # قدرة عكس الضرر لسورا
            if spec_type == "سورا" and random.random() < 0.30:
                reflected = final_damage // 3
                boss_hp -= reflected
                battle_log.append(f"🔮 عكست جزءاً من الضرر: -{reflected} HP للزعيم")

            player_hp -= final_damage
            battle_log.append(f"👹 الزعيم يهاجم: -{final_damage} HP لك (متبقي: {max(0, player_hp)})")

        # شفاء الشامان
        if spec_type == "شامان" and player_hp > 0:
            heal_amount = max(1, player_max_hp // 10)
            player_hp = min(player_max_hp, player_hp + heal_amount)
            battle_log.append(f"✨ شفاء ذاتي: +{heal_amount} HP")

        battle_log.append("─────────────────────────────────────────────────")
        turn += 1

        # حد أقصى للجولات لتجنب المعارك اللا نهائية
        if turn > 20:
            battle_log.append("⏰ المعركة طويلة جداً! انتهت بالتعادل.")
            break

    # تحديد النتيجة
    victory = boss_hp <= 0 and player_hp > 0

    if victory:
        battle_log.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        battle_log.append(f"🎉 **النصر!** هزمت {dungeon['boss']}!")

        # حساب المكافآت المحسنة
        rewards = {}

        # المكافآت الأساسية
        gold_reward = random.randint(*dungeon["rewards"]["ذهب"])
        dollar_reward = random.randint(*dungeon["rewards"]["دولار"])
        exp_reward = random.randint(*dungeon["rewards"].get("experience", [100, 200]))

        # مكافآت إضافية حسب الأداء
        performance_bonus = 1.0
        if player_hp > player_max_hp * 0.8:
            performance_bonus = 1.5
            battle_log.append("🌟 أداء ممتاز! مكافآت مضاعفة!")
        elif player_hp > player_max_hp * 0.5:
            performance_bonus = 1.2
            battle_log.append("⭐ أداء جيد! مكافأة إضافية!")

        rewards["ذهب"] = int(gold_reward * performance_bonus)
        rewards["دولار"] = int(dollar_reward * performance_bonus)
        rewards["experience"] = int(exp_reward * performance_bonus)

        # فرصة الحصول على قطع نادرة من السرداب
        rare_drops = dungeon.get("rare_drops", {})
        obtained_rares = []

        for item_name, drop_chance in rare_drops.items():
            if random.random() < drop_chance:
                obtained_rares.append(item_name)
                battle_log.append(f"✨ حصلت على قطعة نادرة: {item_name}!")

        if obtained_rares:
            rewards["rare_items"] = obtained_rares

        # مكافأة خاصة للسراديب عالية المستوى
        if dungeon["level"] >= 5:
            if random.random() < 0.1:
# 10% فرصة
                bonus_diamonds = random.randint(5, 15)
                rewards["ماس"] = bonus_diamonds
                battle_log.append(f"💎 مكافأة خاصة: {bonus_diamonds} ماس!")

        # مكافأة الإنجاز الأول
        progress = get_user_dungeon_progress(player_stats.get("user_id", ""))
        if dungeon_name not in progress.get("completed_dungeons", []):
            rewards["first_completion_bonus"] = True
            rewards["ذهب"] = int(rewards["ذهب"] * 2)
            battle_log.append("🎉 مكافأة الإنجاز الأول! مضاعفة الذهب!")

        battle_log.append(f"💰 المكافآت: {gold_reward} ذهب، {dollar_reward:,} دولار")

    else:
        battle_log.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        battle_log.append("💀 **الهزيمة!** لم تتمكن من هزيمة الزعيم.")
        battle_log.append("💡 حاول تحسين عتادك أو رفع مستواك.")
        rewards = None

    return victory, battle_log, rewards

def setup_dungeons_commands(bot):
    """إعداد أوامر السراديب"""

    @bot.command(name="سراديب")
    async def dungeons_command(ctx):
        await show_dungeons_menu(ctx)

async def show_dungeons_menu(ctx):
    """عرض قائمة السراديب"""
    embed = discord.Embed(
        title="🏰 سراديب المغامرات",
        description="اختر السرداب الذي تريد استكشافه:",
        color=0x8B4513
    )

    for dungeon_name, dungeon_info in DUNGEONS.items():
        embed.add_field(
            name=f"{dungeon_info['level']} {dungeon_name}",
            value=f"{dungeon_info['description']}\nالمكافآت: {dungeon_info['rewards']['ذهب']} ذهب، {dungeon_info['rewards']['دولار']} دولار",
            inline=True
        )

    #view = DungeonSelectionView() # remove this for now, not fully implemented
    await ctx.send(embed=embed) #, view=view) remove the view for now, not fully implemented
