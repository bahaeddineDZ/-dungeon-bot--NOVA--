
import os
import discord
from discord.ext import commands

def setup_bot():
    """إعداد البوت الأساسي"""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="", intents=intents)
    bot.remove_command("help")
    return bot

def get_discord_token():
    """الحصول على توكن البوت"""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("❌ خطأ: لم يتم العثور على DISCORD_TOKEN في متغيرات البيئة!")
        print("💡 تأكد من إضافة الرمز المميز في تبويب Secrets")
        exit(1)
    return token
