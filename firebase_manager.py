
"""
نظام إدارة Firebase المتكامل
يتضمن إنشاء المجموعات تلقائياً وإدارة البيانات
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import time

class FirebaseManager:
    def __init__(self):
        """تهيئة مدير Firebase"""
        if not firebase_admin._apps:
            try:
                cred = credentials.Certificate("dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json")
                firebase_admin.initialize_app(cred)
                print("✅ تم تهيئة Firebase بنجاح")
            except Exception as e:
                print(f"❌ فشل في تهيئة Firebase: {e}")
                raise
        
        self.db = firestore.client()
        self.collections_initialized = set()
    
    def ensure_collection_exists(self, collection_name, force_create=False):
        """التأكد من وجود المجموعة وإنشاؤها إذا لزم الأمر"""
        if collection_name in self.collections_initialized and not force_create:
            return True
        
        try:
            collection_ref = self.db.collection(collection_name)
            
            # فحص وجود مستندات في المجموعة
            docs = list(collection_ref.limit(1).stream())
            
            if not docs or force_create:
                print(f"📁 إنشاء مجموعة: {collection_name}")
                
                # إنشاء مستند تجريبي لإنشاء المجموعة
                init_doc = {
                    "collection_created": datetime.now(),
                    "created_by": "firebase_manager",
                    "version": "1.0"
                }
                
                doc_ref = collection_ref.document("_collection_init")
                doc_ref.set(init_doc)
                
                # حذف المستند التجريبي فوراً
                doc_ref.delete()
                
                print(f"✅ تم إنشاء مجموعة: {collection_name}")
            
            self.collections_initialized.add(collection_name)
            return True
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء المجموعة {collection_name}: {e}")
            return False
    
    def init_all_collections(self):
        """إنشاء جميع المجموعات المطلوبة للبوت"""
        collections = [
            "users",
            "system_logs", 
            "user_tasks",
            "cooldowns",
            "equipment_data",
            "dungeon_progress",
            "dungeon_cooldowns",
            "shop_prices"
        ]
        
        print("🔥 بدء إنشاء مجموعات Firebase...")
        
        for collection in collections:
            self.ensure_collection_exists(collection)
        
        print("✅ تم إنشاء جميع المجموعات بنجاح!")
    
    def add_sample_data(self):
        """إضافة بيانات تجريبية للمجموعات الفارغة"""
        sample_data = {
            "users": {
                "sample_user": {
                    "username": "مستخدم تجريبي",
                    "balance": {"دولار": 0, "ذهب": 0, "ماس": 0},
                    "حقيبة": [],
                    "المهنة": "مواطن",
                    "specialization": None,
                    "level": 1,
                    "experience": 0,
                    "created_at": datetime.now().isoformat()
                }
            },
            "system_logs": {
                "sample_log": {
                    "category": "system",
                    "user_id": "sample_user",
                    "username": "النظام", 
                    "action": "تهيئة البيانات التجريبية",
                    "details": {"status": "success"},
                    "timestamp": datetime.now().isoformat()
                }
            },
            "shop_prices": {
                "sample_item": {
                    "current_price": 1000,
                    "base_price": 1000,
                    "last_update": time.time(),
                    "trend": "stable"
                }
            }
        }
        
        print("📊 إضافة البيانات التجريبية...")
        
        for collection_name, data in sample_data.items():
            self.ensure_collection_exists(collection_name)
            
            for doc_id, doc_data in data.items():
                self.db.collection(collection_name).document(doc_id).set(doc_data)
                print(f"✅ تم إضافة بيانات تجريبية في {collection_name}: {doc_id}")
    
    def get_collection_info(self):
        """الحصول على معلومات المجموعات"""
        collections_info = {}
        
        for collection_name in ["users", "system_logs", "user_tasks", "cooldowns", 
                              "equipment_data", "dungeon_progress", "dungeon_cooldowns", "shop_prices"]:
            try:
                collection_ref = self.db.collection(collection_name)
                docs = list(collection_ref.limit(10).stream())
                
                collections_info[collection_name] = {
                    "exists": len(docs) > 0,
                    "document_count": len(docs),
                    "sample_docs": [doc.id for doc in docs[:3]]
                }
            except Exception as e:
                collections_info[collection_name] = {
                    "exists": False,
                    "error": str(e)
                }
        
        return collections_info
    
    def cleanup_sample_data(self):
        """تنظيف البيانات التجريبية"""
        sample_docs = [
            ("users", "sample_user"),
            ("system_logs", "sample_log"), 
            ("shop_prices", "sample_item")
        ]
        
        print("🧹 تنظيف البيانات التجريبية...")
        
        for collection_name, doc_id in sample_docs:
            try:
                self.db.collection(collection_name).document(doc_id).delete()
                print(f"🗑️ تم حذف: {collection_name}/{doc_id}")
            except Exception as e:
                print(f"⚠️ لم يتم حذف {collection_name}/{doc_id}: {e}")

# إنشاء مثيل عام للمدير
firebase_manager = FirebaseManager()

# دالة للاستخدام السريع
def init_firebase():
    """دالة سريعة لتهيئة Firebase"""
    try:
        firebase_manager.init_all_collections()
        return True
    except Exception as e:
        print(f"❌ فشل في تهيئة Firebase: {e}")
        return False

if __name__ == "__main__":
    # تشغيل التهيئة عند تشغيل الملف مباشرة
    print("🚀 تشغيل إعداد Firebase...")
    
    if init_firebase():
        print("📊 عرض معلومات المجموعات:")
        info = firebase_manager.get_collection_info()
        
        for collection, details in info.items():
            if details.get("exists"):
                print(f"✅ {collection}: {details['document_count']} مستندات")
            else:
                print(f"❌ {collection}: غير موجود")
        
        # إضافة بيانات تجريبية إذا لم تكن موجودة
        choice = input("\n❓ هل تريد إضافة بيانات تجريبية؟ (y/n): ")
        if choice.lower() == 'y':
            firebase_manager.add_sample_data()
            print("✅ تم إنشاء البيانات التجريبية")
            
            cleanup_choice = input("❓ هل تريد حذف البيانات التجريبية فوراً؟ (y/n): ")
            if cleanup_choice.lower() == 'y':
                firebase_manager.cleanup_sample_data()
    else:
        print("❌ فشل في إعداد Firebase")
