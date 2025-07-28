
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import base64

def initialize_firebase():
    """تهيئة Firebase مع معالجة محسنة للأخطاء"""
    if firebase_admin._apps:
        return firestore.client()
    
    try:
        # محاولة استخدام متغير البيئة أولاً (للـ Railway/Render)
        cred_json = os.getenv("FIREBASE_CREDENTIAL")
        if cred_json:
            try:
                # إذا كان مُشفر بـ base64
                if cred_json.startswith("ey"):
                    cred_json = base64.b64decode(cred_json).decode('utf-8')
                
                # تنظيف النص من أي مسافات أو أحرف غير ضرورية
                cred_json = cred_json.strip()
                
                # التأكد من أن النص JSON صالح
                cred_dict = json.loads(cred_json)
                
                # التحقق من وجود الحقول المطلوبة
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in cred_dict]
                if missing_fields:
                    raise ValueError(f"حقول مفقودة في ملف الاعتماد: {missing_fields}")
                
                # إصلاح private_key إذا كان مكسور
                if 'private_key' in cred_dict:
                    private_key = cred_dict['private_key']
                    if '\\n' in private_key:
                        cred_dict['private_key'] = private_key.replace('\\n', '\n')
                
                cred = credentials.Certificate(cred_dict)
                print("✅ تم تحميل اعتماد Firebase من متغير البيئة")
            except json.JSONDecodeError as e:
                print(f"❌ خطأ في تحليل JSON لمتغير البيئة: {e}")
                raise
            except Exception as e:
                print(f"❌ خطأ في معالجة متغير البيئة: {e}")
                raise
        else:
            # استخدام الملف المحلي
            cred_file = "dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json"
            if os.path.exists(cred_file):
                try:
                    # قراءة وتحقق من الملف
                    with open(cred_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                    
                    cred_dict = json.loads(file_content)
                    
                    # التحقق من صحة البيانات
                    if not cred_dict.get('private_key') or not cred_dict.get('client_email'):
                        raise ValueError("ملف الاعتماد غير مكتمل")
                    
                    cred = credentials.Certificate(cred_file)
                    print("✅ تم تحميل اعتماد Firebase من الملف المحلي")
                except json.JSONDecodeError:
                    print("❌ خطأ في تنسيق ملف الاعتماد - ملف JSON غير صالح")
                    raise
                except Exception as e:
                    print(f"❌ خطأ في قراءة ملف الاعتماد: {e}")
                    raise
            else:
                raise FileNotFoundError(f"لم يتم العثور على ملف اعتماد Firebase: {cred_file}")
        
        # تهيئة Firebase مع معالجة أفضل للأخطاء
        try:
            firebase_admin.initialize_app(cred)
            client = firestore.client()
            
            # اختبار الاتصال بإجراء بسيط
            test_collection = client.collection('_connection_test')
            test_doc = test_collection.document('test')
            test_doc.set({'timestamp': firestore.SERVER_TIMESTAMP, 'status': 'connected'})
            test_doc.delete()  # حذف المستند التجريبي
            
            print("✅ تم تهيئة Firebase بنجاح واختبار الاتصال")
            return client
            
        except Exception as init_error:
            print(f"❌ فشل في تهيئة Firebase: {init_error}")
            # إعادة تعيين التطبيق في حالة الفشل
            if firebase_admin._apps:
                firebase_admin.delete_app(firebase_admin.get_app())
            raise
        
    except Exception as e:
        print(f"❌ فشل في تهيئة Firebase: {e}")
        print("💡 حلول مقترحة:")
        print("   • تحقق من صحة ملف الاعتماد")
        print("   • تأكد من أن ملف JSON غير تالف")
        print("   • جرب إنشاء مفتاح جديد من Google Cloud Console")
        print("   • تحقق من إعدادات الشبكة والحماية")
        
        # إرجاع None بدلاً من raise للسماح للبوت بالعمل بدون Firebase
        return None

# تهيئة Firebase وإنشاء مرجع قاعدة البيانات
try:
    db = initialize_firebase()
    if db:
        print("🔥 Firebase جاهز للاستخدام")
    else:
        print("⚠️ سيعمل البوت في وضع الملفات المحلية فقط")
except Exception as e:
    print(f"⚠️ تحذير: سيعمل البوت بدون Firebase: {e}")
    db = None
