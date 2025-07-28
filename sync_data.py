
#!/usr/bin/env python3
"""
نص مساعد لمزامنة البيانات بين الملفات المحلية و Firebase
"""

import sys
from data_utils import (
    sync_local_to_firebase, 
    backup_firebase_to_local,
    FIREBASE_AVAILABLE,
    init_all_collections
)

def main():
    if len(sys.argv) < 2:
        print("🔧 أداة مزامنة البيانات")
        print("الاستخدام:")
        print("  python sync_data.py upload    # رفع البيانات المحلية إلى Firebase")
        print("  python sync_data.py download  # تحميل البيانات من Firebase")
        print("  python sync_data.py init      # تهيئة مجموعات Firebase")
        print("  python sync_data.py status    # فحص حالة الاتصال")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        print("🔍 فحص حالة النظام...")
        if FIREBASE_AVAILABLE:
            print("✅ Firebase متصل ومتاح")
        else:
            print("❌ Firebase غير متاح")
            print("💡 تحقق من:")
            print("   • ملف الاعتماد")
            print("   • متغير FIREBASE_CREDENTIAL")
            print("   • الاتصال بالإنترنت")
    
    elif command == "init":
        print("🚀 تهيئة مجموعات Firebase...")
        if init_all_collections():
            print("✅ تم إنشاء جميع المجموعات بنجاح")
        else:
            print("❌ فشل في إنشاء بعض المجموعات")
    
    elif command == "upload":
        print("⬆️ رفع البيانات المحلية إلى Firebase...")
        if sync_local_to_firebase():
            print("✅ تم رفع البيانات بنجاح")
        else:
            print("❌ فشل في رفع البيانات")
    
    elif command == "download":
        print("⬇️ تحميل البيانات من Firebase...")
        if backup_firebase_to_local():
            print("✅ تم تحميل البيانات بنجاح")
        else:
            print("❌ فشل في تحميل البيانات")
    
    else:
        print(f"❌ أمر غير معروف: {command}")

if __name__ == "__main__":
    main()
