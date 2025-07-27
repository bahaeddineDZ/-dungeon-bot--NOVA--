
# ================================= إعدادات المتجر =================================

# فئات العناصر وألوانها
ITEM_RARITIES = {
    "شائع": {
        "color": 0x95a5a6,
        "min_fluctuation": 0.1,
        "max_fluctuation": 0.3
    },
    "غير شائع": {
        "color": 0x3498db,
        "min_fluctuation": 0.2,
        "max_fluctuation": 0.4
    },
    "نادر": {
        "color": 0x9b59b6,
        "min_fluctuation": 0.3,
        "max_fluctuation": 0.5
    },
    "أسطوري": {
        "color": 0xf39c12,
        "min_fluctuation": 0.4,
        "max_fluctuation": 0.7
    }
}

# إعدادات الأسعار
PRICE_SETTINGS = {
    "update_interval": 6 * 60,  # 6 دقائق
    "price_precision": 5,       # مضاعفات 5
    "max_daily_changes": 10,    # أقصى تغييرات يومية
    "emergency_reset_threshold": 0.9  # إعادة تعيين الأسعار إذا تجاوزت 90% انحراف
}

# إعدادات المتجر
SHOP_SETTINGS = {
    "max_buy_quantity": 10000,    # أقصى كمية شراء
    "max_sell_quantity": 10000,   # أقصى كمية بيع
    "transaction_timeout": 300,   # مهلة المعاملة (5 دقائق)
    "price_display_format": "{:,}$",  # تنسيق عرض السعر
    "enable_bulk_operations": True,   # تفعيل العمليات المجمعة
}

# رسائل النظام
SHOP_MESSAGES = {
    "insufficient_funds": "❌ رصيدك غير كافي لإتمام هذه العملية!",
    "item_not_found": "❌ العنصر المطلوب غير موجود!",
    "transaction_success": "✅ تمت العملية بنجاح!",
    "transaction_cancelled": "❌ تم إلغاء العملية.",
    "cooldown_active": "⏳ يجب الانتظار قبل استخدام هذا الأمر مرة أخرى.",
    "market_closed": "🏪 المتجر مغلق مؤقتاً للصيانة.",
}

# إعدادات التسجيل
LOGGING_SETTINGS = {
    "log_purchases": True,
    "log_sales": True,
    "log_price_changes": True,
    "max_log_entries": 1000,
    "log_retention_days": 30
}
