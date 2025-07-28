import firebase_admin
from firebase_admin import credentials, firestore

# تحميل بيانات الاعتماد (ضع اسم ملفك المفتاح هنا)
cred = credentials.Certificate("dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json")

# تهيئة التطبيق (مرة واحدة فقط)
firebase_admin.initialize_app(cred)

# إنشاء مرجع إلى قاعدة بيانات Firestore
db = firestore.client()
