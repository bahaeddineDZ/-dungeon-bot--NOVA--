
#!/usr/bin/env python3
"""
سكريبت لإصلاح مشاكل Firebase الشائعة
"""

import json
import os
import sys

def check_firebase_credentials():
    """فحص وإصلاح ملف اعتماد Firebase"""
    cred_file = "dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json"
    
    print("🔍 فحص ملف اعتماد Firebase...")
    
    if not os.path.exists(cred_file):
        print(f"❌ ملف الاعتماد غير موجود: {cred_file}")
        print("💡 قم بتحميل ملف الاعتماد من Google Cloud Console")
        return False
    
    try:
        with open(cred_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # فحص إذا كان الملف فارغ
        if not content:
            print("❌ ملف الاعتماد فارغ")
            return False
        
        # محاولة تحليل JSON
        cred_data = json.loads(content)
        
        # فحص الحقول المطلوبة
        required_fields = [
            'type', 'project_id', 'private_key_id', 
            'private_key', 'client_email', 'client_id',
            'auth_uri', 'token_uri'
        ]
        
        missing_fields = [field for field in required_fields if field not in cred_data]
        
        if missing_fields:
            print(f"❌ حقول مفقودة في ملف الاعتماد: {missing_fields}")
            return False
        
        # فحص private_key
        private_key = cred_data.get('private_key', '')
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----'):
            print("❌ مفتاح خاص غير صالح")
            return False
        
        # فحص client_email
        client_email = cred_data.get('client_email', '')
        if '@' not in client_email or not client_email.endswith('.iam.gserviceaccount.com'):
            print("❌ بريد الخدمة غير صالح")
            return False
        
        print("✅ ملف الاعتماد يبدو صحيحاً")
        
        # عرض معلومات الملف
        print(f"📋 معلومات الاعتماد:")
        print(f"   • المشروع: {cred_data.get('project_id')}")
        print(f"   • البريد: {cred_data.get('client_email')}")
        print(f"   • النوع: {cred_data.get('type')}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ خطأ في تنسيق JSON: {e}")
        print("💡 تأكد من أن الملف صالح كـ JSON")
        return False
    except Exception as e:
        print(f"❌ خطأ في قراءة الملف: {e}")
        return False

def fix_private_key():
    """إصلاح مشاكل المفتاح الخاص الشائعة"""
    cred_file = "dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json"
    
    try:
        with open(cred_file, 'r', encoding='utf-8') as f:
            cred_data = json.load(f)
        
        private_key = cred_data.get('private_key', '')
        
        # إصلاح \n في المفتاح
        if '\\n' in private_key:
            print("🔧 إصلاح تنسيق المفتاح الخاص...")
            cred_data['private_key'] = private_key.replace('\\n', '\n')
            
            # إنشاء نسخة احتياطية
            backup_file = f"{cred_file}.backup"
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(cred_data, f, indent=2)
            
            # حفظ الملف المُصحح
            with open(cred_file, 'w', encoding='utf-8') as f:
                json.dump(cred_data, f, indent=2)
            
            print(f"✅ تم إصلاح المفتاح وحفظ نسخة احتياطية في {backup_file}")
            return True
        
        print("ℹ️ المفتاح الخاص لا يحتاج إصلاح")
        return True
        
    except Exception as e:
        print(f"❌ فشل في إصلاح المفتاح: {e}")
        return False

def regenerate_credentials_guide():
    """دليل لإعادة إنشاء ملف الاعتماد"""
    print("\n📝 دليل إعادة إنشاء ملف الاعتماد:")
    print("1. اذهب إلى Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    
    print("\n2. اختر مشروعك أو أنشئ مشروع جديد")
    
    print("\n3. اذهب إلى IAM & Admin > Service Accounts:")
    print("   https://console.cloud.google.com/iam-admin/serviceaccounts")
    
    print("\n4. أنشئ حساب خدمة جديد أو استخدم الموجود")
    
    print("\n5. انقر على الحساب ثم 'Keys' > 'Add Key' > 'Create New Key'")
    
    print("\n6. اختر JSON وحمّل الملف")
    
    print("\n7. أعد تسمية الملف إلى:")
    print("   dungeon-bot--nova-firebase-adminsdk-fbsvc-f1014530c2.json")
    
    print("\n8. تأكد من تفعيل Firestore API في مشروعك")

def main():
    print("🔧 أداة إصلاح Firebase")
    print("=" * 40)
    
    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        regenerate_credentials_guide()
        return
    
    # فحص الملف
    if not check_firebase_credentials():
        print("\n❌ فشل في فحص ملف الاعتماد")
        print("💡 جرب: python fix_firebase.py guide")
        return
    
    # محاولة إصلاح المفتاح
    if not fix_private_key():
        print("❌ فشل في إصلاح المفتاح")
        return
    
    print("\n✅ تم فحص وإصلاح ملف Firebase بنجاح!")
    print("🚀 يمكنك الآن تشغيل البوت")

if __name__ == "__main__":
    main()
