
#!/usr/bin/env python3
"""
أمر إعداد Firebase
يمكن تشغيله بشكل منفصل لإعداد قاعدة البيانات
"""

from firebase_manager import firebase_manager
import sys

def main():
    print("🚀 مرحباً بك في أداة إعداد Firebase")
    print("=" * 50)
    
    try:
        # تهيئة المجموعات
        print("1️⃣ إنشاء المجموعات...")
        firebase_manager.init_all_collections()
        
        # عرض حالة المجموعات
        print("\n2️⃣ فحص حالة المجموعات...")
        info = firebase_manager.get_collection_info()
        
        for collection, details in info.items():
            if details.get("exists"):
                print(f"   ✅ {collection}: موجود ({details.get('document_count', 0)} مستندات)")
            else:
                print(f"   ❌ {collection}: غير موجود")
        
        # خيار إضافة بيانات تجريبية
        print("\n3️⃣ خيارات إضافية:")
        print("   a) إضافة بيانات تجريبية")
        print("   b) حذف البيانات التجريبية")
        print("   c) إعادة إنشاء المجموعات بالقوة")
        print("   d) تخطي")
        
        choice = input("\n❓ اختر خياراً (a/b/c/d): ").lower()
        
        if choice == 'a':
            firebase_manager.add_sample_data()
            print("✅ تم إنشاء البيانات التجريبية")
            
        elif choice == 'b':
            firebase_manager.cleanup_sample_data()
            print("✅ تم حذف البيانات التجريبية")
            
        elif choice == 'c':
            print("🔄 إعادة إنشاء المجموعات...")
            collections = ["users", "system_logs", "user_tasks", "cooldowns", 
                          "equipment_data", "dungeon_progress", "dungeon_cooldowns", "shop_prices"]
            
            for collection in collections:
                firebase_manager.ensure_collection_exists(collection, force_create=True)
            
            print("✅ تم إعادة إنشاء جميع المجموعات")
        
        print(f"\n🎉 تم الانتهاء من إعداد Firebase بنجاح!")
        print("💡 يمكنك الآن تشغيل البوت بأمان")
        
    except Exception as e:
        print(f"\n❌ حدث خطأ أثناء الإعداد: {e}")
        print("💡 تأكد من:")
        print("   • وجود ملف المفتاح الصحيح")
        print("   • صحة إعدادات Firebase")
        print("   • الاتصال بالإنترنت")
        sys.exit(1)

if __name__ == "__main__":
    main()
