
import discord
from discord.ext import commands
from discord import Embed
import random

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system
from tasks_system import tasks_system

def setup_job_commands(bot):
    """إعداد أوامر الوظائف"""
    
    @bot.command(name="مهنتي")
    async def my_job(ctx):
        user_id = str(ctx.author.id)
        init_user(user_id, ctx.author.display_name)
        data = load_data()
        job = data[user_id].get("المهنة", "مواطن")
        await ctx.send(f"👷 وظيفتك الحالية: **{job}**")

    @bot.command(name="عمل")
    async def work(ctx):
        user_id = str(ctx.author.id)

        allowed, time_left = check_cooldown(user_id, "عمل")
        if not allowed:
            await ctx.send(f"⏳ يمكنك العمل مرة أخرى بعد {time_left}.")
            return

        update_cooldown(user_id, "عمل")

        init_user(user_id, ctx.author.display_name)
        data = load_data()

        current_job = data[user_id].get("المهنة", "مواطن")

        job_ranks = {
            "مواطن": 1, "رسام": 2, "طبيب": 3, "مقدم": 4,
            "جنيرال": 5, "وزير": 6, "ملك": 7, "إمبراطور": 8
        }

        rank = job_ranks.get(current_job, 1)

        dollars = 0
        gold = 0

        if rank >= 7:
            gold = random.randint(20, 40)
        elif rank >= 4:
            gold = random.randint(10, 20)
            dollars = random.randint(40_000, 60_000)
        else:
            dollars = random.randint(60_000, 90_000)

        data[user_id]["balance"]["دولار"] += dollars
        data[user_id]["balance"]["ذهب"] += gold
        save_data(data)

        total_earned = dollars + (gold * 50)
        logs_system.add_log(
            "work_logs", 
            user_id,
            ctx.author.display_name,
            f"عمل في وظيفة {current_job}",
            {"job": current_job, "earned": total_earned, "dollars": dollars, "gold": gold}
        )
        
        if gold > 0:
            completed_tasks = tasks_system.update_task_progress(user_id, "collect_gold", gold)

        msg = f"💼 مهنتك الحالية: {current_job}\n👏 عملت وربحت اليوم:\n"
        if dollars:
            msg += f"💵 {dollars}$\n"
        if gold:
            msg += f"🪙 {gold} ذهب\n"

        await ctx.send(msg)

    @bot.command(name="ترقية")
    async def upgrade(ctx):
        user_id = str(ctx.author.id)

        allowed, remaining = check_cooldown(user_id, "upgrade")
        if not allowed:
            await ctx.send(f"⏳ الرجاء الانتظار {remaining} قبل استخدام الأمر مرة أخرى.")
            return

        data = load_data()
        if user_id not in data:
            await ctx.send("❌ يجب أن تبدأ باستخدام الأمر 'بدء' أولاً.")
            return

        current_job = data[user_id].get("المهنة", "مواطن")

        jobs_order = ["مواطن", "رسام", "مدرب", "مقدم", "جنيرال", "وزير", "ملك"]
        upgrade_costs = {
            "مواطن": {"ذهب": 100, "دولار": 10},
            "رسام": {"ذهب": 200, "دولار": 20},
            "مدرب": {"ذهب": 300, "دولار": 30},
            "مقدم": {"ذهب": 500, "دولار": 50},
            "جنيرال": {"ذهب": 800, "دولار": 80},
            "وزير": {"ذهب": 1200, "دولار": 120}
        }

        if current_job == "ملك":
            await ctx.send("👑 لقد وصلت إلى أعلى رتبة!")
            return

        try:
            next_job_index = jobs_order.index(current_job) + 1
            next_job = jobs_order[next_job_index]
        except (ValueError, IndexError):
            await ctx.send("❌ المهنة الحالية غير صالحة.")
            return

        cost = upgrade_costs.get(current_job)
        if not cost:
            await ctx.send("❌ لا توجد تكلفة معرفة لهذه الترقية.")
            return

        user_gold = data[user_id]["balance"].get("ذهب", 0)
        user_dollar = data[user_id]["balance"].get("دولار", 0)

        if user_gold >= cost["ذهب"] and user_dollar >= cost["دولار"]:
            data[user_id]["balance"]["ذهب"] -= cost["ذهب"]
            data[user_id]["balance"]["دولار"] -= cost["دولار"]
            data[user_id]["المهنة"] = next_job
            save_data(data)
            update_cooldown(user_id, "upgrade")
            await ctx.send(f"✅ تمت ترقيتك إلى **{next_job}**!")
        else:
            await ctx.send(
                f"❌ لا تملك ما يكفي من الموارد للترقية إلى **{next_job}**.\n"
                f"🔸 تحتاج إلى: {cost['ذهب']} ذهب و {cost['دولار']} دولار."
            )

    @bot.command(name="يومي")
    async def daily(ctx):
        user_id = str(ctx.author.id)
        
        allowed, time_left = check_cooldown(user_id, "يومي")
        if not allowed:
            await ctx.send(f"⏳ يمكنك العمل مرة أخرى بعد {time_left}.")
            return

        init_user(user_id, ctx.author.display_name)
        data = load_data()
        data[user_id]["balance"]["دولار"] += 100_000
        data[user_id]["balance"]["ذهب"] += 10
        data[user_id]["balance"]["ماس"] += 1
        save_data(data)

        logs_system.add_log(
            "daily_logs",
            user_id,
            ctx.author.display_name,
            "حصل على المكافأة اليومية",
            {"dollars": 100000, "gold": 25, "diamonds": 1}
        )

        update_cooldown(user_id, "يومي")

        await ctx.send("🎁 حصلت على مكافأتك اليومية:\n💵 100 ألف دولار\n🪙 25 ذهب\n💎 1 ماس")
