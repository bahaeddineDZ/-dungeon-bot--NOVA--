
from flask import Flask
from threading import Thread
import os

app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل بنجاح! 🤖"

@app.route('/status')
def status():
    return {"status": "active", "message": "Discord Bot is running"}

def run():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    """تشغيل خادم Flask في thread منفصل للحفاظ على البوت نشطاً"""
    t = Thread(target=run)
    t.daemon = True
    t.start()
    print(f"🌐 خادم Flask يعمل على المنفذ {os.environ.get('PORT', 5000)}")
