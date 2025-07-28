
import json
import os
from datetime import datetime
import time

# محاولة استيراد Firebase
try:
    from firebase_config import db
    FIREBASE_AVAILABLE = db is not None
except Exception as e:
    print(f"تحذير: Firebase غير متاح: {e}")
    FIREBASE_AVAILABLE = False
    db = None

# أسماء الملفات المحلية للنسخ الاحتياطية
LOCAL_FILES = {
    "users": "users.json",
    "cooldowns": "cooldowns.json",
    "equipment_data": "equipment_data.json",
    "system_logs": "system_logs.json",
    "user_tasks": "user_tasks.json",
    "dungeon_progress": "dungeons_data.json",
    "dungeon_cooldowns": "dungeon_cooldowns.json",
    "shop_prices": "prices.json"
}

def load_from_file(filename, default=None):
    """تحميل البيانات من ملف محلي"""
    if default is None:
        default = {}
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"خطأ في تحميل {filename}: {e}")
    
    return default

def save_to_file(filename, data):
    """حفظ البيانات في ملف محلي"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"خطأ في حفظ {filename}: {e}")
        return False

def load_from_firebase(collection_name, default=None):
    """تحميل البيانات من Firebase"""
    if not FIREBASE_AVAILABLE:
        return default or {}
    
    try:
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()
        
        data = {}
        for doc in docs:
            data[doc.id] = doc.to_dict()
        
        return data
    except Exception as e:
        print(f"خطأ في تحميل {collection_name} من Firebase: {e}")
        return default or {}

def save_to_firebase(collection_name, data):
    """حفظ البيانات في Firebase"""
    if not FIREBASE_AVAILABLE:
        return False
    
    try:
        collection_ref = db.collection(collection_name)
        
        # حفظ كل مستخدم كمستند منفصل
        for user_id, user_data in data.items():
            collection_ref.document(str(user_id)).set(user_data)
        
        return True
    except Exception as e:
        print(f"خطأ في حفظ {collection_name} في Firebase: {e}")
        return False

def load_data():
    """تحميل بيانات المستخدمين من Firebase أو الملف المحلي"""
    # محاولة تحميل من Firebase أولاً
    if FIREBASE_AVAILABLE:
        data = load_from_firebase("users")
        if data:
            # حفظ نسخة احتياطية محلية
            save_to_file(LOCAL_FILES["users"], data)
            return data
    
    # في حالة فشل Firebase، استخدم الملف المحلي
    return load_from_file(LOCAL_FILES["users"], {})

def save_data(data):
    """حفظ بيانات المستخدمين في Firebase والملف المحلي"""
    success = False
    
    # حفظ في Firebase
    if FIREBASE_AVAILABLE:
        success = save_to_firebase("users", data)
    
    # حفظ نسخة احتياطية محلية دائماً
    local_success = save_to_file(LOCAL_FILES["users"], data)
    
    return success or local_success

def load_cooldowns():
    """تحميل بيانات التبريد"""
    if FIREBASE_AVAILABLE:
        data = load_from_firebase("cooldowns")
        if data:
            save_to_file(LOCAL_FILES["cooldowns"], data)
            return data
    
    return load_from_file(LOCAL_FILES["cooldowns"], {})

def save_cooldowns(data):
    """حفظ بيانات التبريد"""
    success = False
    
    if FIREBASE_AVAILABLE:
        success = save_to_firebase("cooldowns", data)
    
    local_success = save_to_file(LOCAL_FILES["cooldowns"], data)
    return success or local_success

def load_equipment_data():
    """تحميل بيانات العتاد"""
    if FIREBASE_AVAILABLE:
        data = load_from_firebase("equipment_data")
        if data:
            save_to_file(LOCAL_FILES["equipment_data"], data)
            return data
    
    return load_from_file(LOCAL_FILES["equipment_data"], {})

def save_equipment_data(data):
    """حفظ بيانات العتاد"""
    success = False
    
    if FIREBASE_AVAILABLE:
        success = save_to_firebase("equipment_data", data)
    
    local_success = save_to_file(LOCAL_FILES["equipment_data"], data)
    return success or local_success

def load_system_logs():
    """تحميل سجلات النظام"""
    if FIREBASE_AVAILABLE:
        data = load_from_firebase("system_logs")
        if data:
            save_to_file(LOCAL_FILES["system_logs"], data)
            return data
    
    return load_from_file(LOCAL_FILES["system_logs"], {})

def save_system_logs(data):
    """حفظ سجلات النظام"""
    success = False
    
    if FIREBASE_AVAILABLE:
        success = save_to_firebase("system_logs", data)
    
    local_success = save_to_file(LOCAL_FILES["system_logs"], data)
    return success or local_success

def init_user(user_id, username):
    """تهيئة مستخدم جديد"""
    data = load_data()
    
    if str(user_id) not in data:
        data[str(user_id)] = {
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
            "حوض": [],
            "created_at": datetime.now().isoformat()
        }
        save_data(data)
    
    return data[str(user_id)]

def ensure_collection_exists(collection_name):
    """التأكد من وجود المجموعة"""
    if not FIREBASE_AVAILABLE:
        print(f"⚠️ Firebase غير متاح، تخطي إنشاء مجموعة {collection_name}")
        return True
    
    try:
        # فحص بسيط لوجود المجموعة
        collection_ref = db.collection(collection_name)
        docs = list(collection_ref.limit(1).stream())
        
        if not docs:
            # إنشاء مستند تجريبي لإنشاء المجموعة
            collection_ref.document("_init").set({
                "created_at": datetime.now().isoformat(),
                "type": "initialization"
            })
            # حذف المستند التجريبي
            collection_ref.document("_init").delete()
            print(f"✅ تم إنشاء مجموعة {collection_name}")
        
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء مجموعة {collection_name}: {e}")
        return False

def init_all_collections():
    """تهيئة جميع المجموعات المطلوبة"""
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase غير متاح، تخطي إنشاء المجموعات")
        return False
    
    collections = [
        "users", "cooldowns", "equipment_data", 
        "system_logs", "user_tasks", "dungeon_progress", 
        "dungeon_cooldowns", "shop_prices"
    ]
    
    success_count = 0
    for collection in collections:
        if ensure_collection_exists(collection):
            success_count += 1
    
    print(f"✅ تم إنشاء {success_count}/{len(collections)} مجموعة بنجاح")
    return success_count == len(collections)

def sync_local_to_firebase():
    """مزامنة البيانات المحلية إلى Firebase"""
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase غير متاح للمزامنة")
        return False
    
    print("🔄 بدء مزامنة البيانات المحلية إلى Firebase...")
    
    synced = 0
    for collection_name, filename in LOCAL_FILES.items():
        if os.path.exists(filename):
            try:
                data = load_from_file(filename)
                if data and save_to_firebase(collection_name, data):
                    synced += 1
                    print(f"✅ تم مزامنة {collection_name}")
                else:
                    print(f"❌ فشل في مزامنة {collection_name}")
            except Exception as e:
                print(f"❌ خطأ في مزامنة {collection_name}: {e}")
    
    print(f"🔄 تم مزامنة {synced}/{len(LOCAL_FILES)} ملف")
    return synced > 0

def backup_firebase_to_local():
    """نسخ احتياطي من Firebase إلى الملفات المحلية"""
    if not FIREBASE_AVAILABLE:
        print("⚠️ Firebase غير متاح للنسخ الاحتياطي")
        return False
    
    print("💾 بدء النسخ الاحتياطي من Firebase...")
    
    backed_up = 0
    for collection_name, filename in LOCAL_FILES.items():
        try:
            data = load_from_firebase(collection_name)
            if data and save_to_file(filename, data):
                backed_up += 1
                print(f"✅ تم نسخ {collection_name}")
        except Exception as e:
            print(f"❌ خطأ في نسخ {collection_name}: {e}")
    
    print(f"💾 تم نسخ {backed_up}/{len(LOCAL_FILES)} مجموعة")
    return backed_up > 0
