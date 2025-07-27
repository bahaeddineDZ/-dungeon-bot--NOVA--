
from flask import Flask
from threading import Thread
import time

app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح! 🚀"

@app.route('/status')
def status():
    return {
        "status": "online",
        "message": "Discord Bot is running",
        "timestamp": time.time()
    }

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "uptime": time.time(),
        "message": "Bot is running smoothly"
    }

def run():
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"خطأ في تشغيل خادم Flask: {e}")

def keep_alive():
    try:
        t = Thread(target=run)
        t.daemon = True
        t.start()
        print("✅ تم تشغيل خادم المراقبة على المنفذ 5000")
    except Exception as e:
        print(f"خطأ في تشغيل المراقبة: {e}")
