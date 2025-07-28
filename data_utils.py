import firebase_admin
from firebase_admin import credentials, firestore

# تحميل بيانات الاعتماد من ملف الخدمة
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# مرجع قاعدة البيانات
db = firestore.client()
users_ref = db.collection("users")

def init_user(user_id, username):
    """تهيئة مستخدم جديد"""
    user_id = str(user_id)
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
            "حوض": []
        }
        doc_ref.set(user_data)
        return user_data
    else:
        return doc_ref.get().to_dict()

def get_user_data(user_id):
    """جلب بيانات مستخدم محدد"""
    doc = users_ref.document(str(user_id)).get()
    return doc.to_dict() if doc.exists else None

def update_user_data(user_id, user_data):
    """تحديث بيانات مستخدم محدد"""
    users_ref.document(str(user_id)).set(user_data, merge=True)
