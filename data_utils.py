
import firebase_admin
from firebase_admin import credentials, firestore
import time
from datetime import datetime

# تحميل بيانات الاعتماد من ملف الخدمة
if not firebase_admin._apps:
    cred = credentials.Certificate("dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json")
    firebase_admin.initialize_app(cred)

# مرجع قاعدة البيانات
db = firestore.client()

def ensure_collection_exists(collection_name, sample_data=None):
    """التأكد من وجود المجموعة وإنشاؤها إذا لم تكن موجودة"""
    try:
        # فحص وجود المجموعة
        collection_ref = db.collection(collection_name)
        docs = collection_ref.limit(1).stream()
        
        # إذا لم توجد مستندات، أنشئ المجموعة بمستند تجريبي
        if not any(docs):
            if sample_data:
                collection_ref.document("_init").set(sample_data)
                # حذف المستند التجريبي بعد الإنشاء
                collection_ref.document("_init").delete()
            else:
                # إنشاء مستند تجريبي فارغ لإنشاء المجموعة
                collection_ref.document("_init").set({"created_at": datetime.now()})
                collection_ref.document("_init").delete()
        
        print(f"✅ تم التأكد من وجود مجموعة: {collection_name}")
        return True
    except Exception as e:
        print(f"❌ خطأ في إنشاء المجموعة {collection_name}: {e}")
        return False

def init_firebase_collections():
    """تهيئة جميع المجموعات المطلوبة في Firebase"""
    collections_config = {
        "users": {
            "user_id": {
                "username": "مستخدم تجريبي",
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
        },
        "system_logs": {
            "log_id": {
                "category": "system",
                "user_id": "sample_user",
                "username": "مستخدم تجريبي",
                "action": "تسجيل تجريبي",
                "details": {},
                "timestamp": datetime.now().isoformat()
            }
        },
        "user_tasks": {
            "user_id": {
                "active_tasks": [],
                "completed_tasks": [],
                "last_update": 0
            }
        },
        "cooldowns": {
            "user_id": {
                "يومي": 0,
                "عمل": 0,
                "نهب": 0
            }
        },
        "equipment_data": {
            "user_id": {
                "weapon": None,
                "armor": None,
                "helmet": None,
                "ring": None,
                "consumables": []
            }
        },
        "dungeon_progress": {
            "user_id": {
                "total_victories": 0,
                "total_defeats": 0,
                "completed_dungeons": [],
                "daily_attempts": {}
            }
        },
        "dungeon_cooldowns": {
            "user_id": {
                "entry": 0,
                "death_penalty": 0
            }
        },
        "shop_prices": {
            "item_name": {
                "current_price": 1000,
                "base_price": 1000,
                "last_update": time.time(),
                "trend": "stable"
            }
        }
    }
    
    print("🔥 بدء تهيئة مجموعات Firebase...")
    
    for collection_name, sample_data in collections_config.items():
        ensure_collection_exists(collection_name, sample_data)
    
    print("✅ تم الانتهاء من تهيئة جميع المجموعات!")

def init_user(user_id, username):
    """تهيئة مستخدم جديد مع التأكد من وجود المجموعة"""
    user_id = str(user_id)
    
    # التأكد من وجود مجموعة المستخدمين
    ensure_collection_exists("users")
    
    users_ref = db.collection("users")
    doc_ref = users_ref.document(user_id)
    
    if not doc_ref.get().exists:
        user_data = {
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
        doc_ref.set(user_data)
        print(f"👤 تم إنشاء مستخدم جديد: {username}")
        return user_data
    else:
        return doc_ref.get().to_dict()

def get_user_data(user_id):
    """جلب بيانات مستخدم محدد"""
    ensure_collection_exists("users")
    doc = db.collection("users").document(str(user_id)).get()
    return doc.to_dict() if doc.exists else None

def update_user_data(user_id, data):
    """تحديث بيانات مستخدم"""
    ensure_collection_exists("users")
    db.collection("users").document(str(user_id)).update(data)

def save_data(data):
    """حفظ جميع بيانات المستخدمين (للتوافق مع النظام القديم)"""
    ensure_collection_exists("users")
    
    for user_id, user_data in data.items():
        db.collection("users").document(str(user_id)).set(user_data, merge=True)

def load_data():
    """تحميل جميع بيانات المستخدمين (للتوافق مع النظام القديم)"""
    ensure_collection_exists("users")
    
    users_ref = db.collection("users")
    docs = users_ref.stream()
    
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    
    return data

def save_log(category, user_id, username, action, details):
    """حفظ سجل النشاط في Firebase"""
    ensure_collection_exists("system_logs")
    
    log_data = {
        "category": category,
        "user_id": str(user_id),
        "username": username,
        "action": action,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    db.collection("system_logs").add(log_data)

def get_logs(category=None, user_id=None, limit=50):
    """جلب السجلات من Firebase"""
    ensure_collection_exists("system_logs")
    
    logs_ref = db.collection("system_logs")
    
    if category:
        logs_ref = logs_ref.where("category", "==", category)
    
    if user_id:
        logs_ref = logs_ref.where("user_id", "==", str(user_id))
    
    logs_ref = logs_ref.order_by("timestamp", direction=firestore.Query.DESCENDING).limit(limit)
    
    logs = []
    for doc in logs_ref.stream():
        log_data = doc.to_dict()
        log_data["id"] = doc.id
        logs.append(log_data)
    
    return logs

def save_user_tasks(user_id, tasks_data):
    """حفظ مهام المستخدم في Firebase"""
    ensure_collection_exists("user_tasks")
    
    db.collection("user_tasks").document(str(user_id)).set(tasks_data, merge=True)

def load_user_tasks(user_id):
    """تحميل مهام المستخدم من Firebase"""
    ensure_collection_exists("user_tasks")
    
    doc = db.collection("user_tasks").document(str(user_id)).get()
    if doc.exists:
        return doc.to_dict()
    else:
        # إنشاء مهام فارغة للمستخدم الجديد
        empty_tasks = {"active_tasks": [], "completed_tasks": [], "last_update": 0}
        save_user_tasks(user_id, empty_tasks)
        return empty_tasks

def save_cooldowns(user_id, cooldowns_data):
    """حفظ أوقات التبريد في Firebase"""
    ensure_collection_exists("cooldowns")
    
    db.collection("cooldowns").document(str(user_id)).set(cooldowns_data, merge=True)

def load_cooldowns():
    """تحميل جميع أوقات التبريد من Firebase"""
    ensure_collection_exists("cooldowns")
    
    cooldowns_ref = db.collection("cooldowns")
    docs = cooldowns_ref.stream()
    
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    
    return data

def save_equipment_data(user_id, equipment_data):
    """حفظ بيانات العتاد في Firebase"""
    ensure_collection_exists("equipment_data")
    
    db.collection("equipment_data").document(str(user_id)).set(equipment_data, merge=True)

def load_equipment_data():
    """تحميل جميع بيانات العتاد من Firebase"""
    ensure_collection_exists("equipment_data")
    
    equipment_ref = db.collection("equipment_data")
    docs = equipment_ref.stream()
    
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    
    return data

def save_shop_prices(prices_data):
    """حفظ أسعار المتجر في Firebase"""
    ensure_collection_exists("shop_prices")
    
    for item_name, price_info in prices_data.items():
        db.collection("shop_prices").document(item_name).set(price_info, merge=True)

def load_shop_prices():
    """تحميل أسعار المتجر من Firebase"""
    ensure_collection_exists("shop_prices")
    
    prices_ref = db.collection("shop_prices")
    docs = prices_ref.stream()
    
    data = {}
    for doc in docs:
        data[doc.id] = doc.to_dict()
    
    return data

# تهيئة المجموعات عند تحميل الوحدة
try:
    init_firebase_collections()
except Exception as e:
    print(f"⚠️ تحذير: لم يتم تهيئة Firebase بالكامل: {e}")
