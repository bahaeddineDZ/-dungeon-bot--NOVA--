import discord
from discord.ext import tasks
import datetime
import os

CHANNEL_ID = 1398718739196678245  # ✅ ID القناة
TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # 🔐 استدعاء التوكن من المتغير البيئي

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    clean_old_messages.start()

# 🔁 تنظيف تلقائي كل دقيقة
@tasks.loop(minutes=1)
async def clean_old_messages():
    await delete_old_messages()

# 🧹 تنظيف فوري عند كتابة "تنظيف2025تنظيف"
@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == CHANNEL_ID and message.content.strip() == "تنظيف2025تنظيف":
        await message.channel.send("🧹 جارٍ تنظيف الرسائل الأقدم من 30 دقيقة...")
        deleted = await delete_old_messages()
        await message.channel.send(f"✅ تم حذف {deleted} رسالة.")

# 🔨 وظيفة حذف الرسائل
async def delete_old_messages():
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ لم يتم العثور على القناة")
        return 0

    now = datetime.datetime.utcnow()
    deleted_count = 0

    async for message in channel.history(limit=200):
        age_seconds = (now - message.created_at).total_seconds()
        if age_seconds > 1800:
            try:
                await message.delete()
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ خطأ أثناء حذف رسالة: {e}")
    return deleted_count

# ✅ تشغيل البوت
if TOKEN:
    client.run(TOKEN)
else:
    print("❌ لم يتم العثور على متغير البيئة DISCORD_BOT_TOKEN")
