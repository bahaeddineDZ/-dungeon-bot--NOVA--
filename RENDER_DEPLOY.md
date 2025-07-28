
# دليل النشر على Render

## خطوات النشر:

### 1. إعداد Firebase
1. انتقل إلى [Firebase Console](https://console.firebase.google.com)
2. إنشاء مشروع جديد أو استخدام موجود
3. انتقل إلى Project Settings > Service Accounts
4. انقر "Generate new private key"
5. احفظ الملف JSON

### 2. إعداد Render
1. اذهب إلى [Render Dashboard](https://dashboard.render.com)
2. انقر "New" > "Web Service"
3. اربط حساب GitHub وحدد المستودع
4. أعداد الخدمة:
   - **Name**: discord-bot-nova
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

### 3. إعداد متغيرات البيئة
في صفحة الخدمة على Render، أضف:

1. **DISCORD_TOKEN**
   - Value: توكن البوت من Discord Developer Portal

2. **FIREBASE_CREDENTIAL**
   - Value: محتوى ملف JSON كاملاً (انسخ النص كاملاً)

### 4. النشر
1. انقر "Create Web Service"
2. انتظر انتهاء البناء والنشر
3. تحقق من السجلات للتأكد من عدم وجود أخطاء

## استخدام أدوات المزامنة:

### رفع البيانات المحلية إلى Firebase:
```bash
python sync_data.py upload
```

### تحميل البيانات من Firebase:
```bash
python sync_data.py download
```

### فحص حالة الاتصال:
```bash
python sync_data.py status
```

## ملاحظات مهمة:
- البوت سيعمل مع الملفات المحلية إذا فشل Firebase
- البيانات تُحفظ في Firebase والملفات المحلية معاً
- يمكن استخدام أدوات المزامنة لنقل البيانات

## استكشاف الأخطاء:
- تحقق من صحة متغيرات البيئة
- تأكد من صحة ملف اعتماد Firebase
- راجع سجلات Render للتفاصيل
