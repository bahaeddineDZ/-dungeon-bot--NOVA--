import json
import os

DATA_FILE = "users.json"

def load_data():
    """تحميل بيانات المستخدمين"""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_data(data):
    """حفظ بيانات المستخدمين"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_user(user_id, username):
    """تهيئة مستخدم جديد"""
    data = load_data()
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {
            "username": username,
            "balance": {
                "دولار": 0,
                "ذهب": 0,
                "ماس": 0
            },
            "حقيبة": [],
            "المهنة": "مواطن",
            "specialization": None,
            "level": 1,
            "experience": 0,
            "fish_pond": [],
            "مزرعة": [],
            "حوض": []
        }
        save_data(data)

    return data[user_id]

def get_user_data(user_id):
    """جلب بيانات مستخدم محدد"""
    data = load_data()
    return data.get(str(user_id))

def update_user_data(user_id, user_data):
    """تحديث بيانات مستخدم محدد"""
    data = load_data()
    data[str(user_id)] = user_data
    save_data(data)