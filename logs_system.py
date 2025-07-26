import json
import os
import time
from datetime import datetime
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle
from discord.ui import View, Button, Select
from discord import SelectOption

LOGS_FILE = "system_logs.json"

class LogsSystem:
    def __init__(self):
        self.logs_file = LOGS_FILE

    def load_logs(self):
        if not os.path.exists(self.logs_file):
            return {
                "work_logs": [],
                "theft_logs": [],
                "trade_logs": [],
                "investment_logs": [],
                "daily_logs": [],
                "shop_logs": [],
                "game_logs": [],
                "farm_logs": [],
                "fish_logs": []
            }
        with open(self.logs_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_logs(self, logs):
        with open(self.logs_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

    def add_log(self, log_type, user_id, username, action, details):
        logs = self.load_logs()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": str(user_id),
            "username": username,
            "action": action,
            "details": details
        }

        if log_type not in logs:
            logs[log_type] = []

        logs[log_type].append(log_entry)

        # الاحتفاظ بآخر 1000 سجل فقط لكل نوع
        if len(logs[log_type]) > 1000:
            logs[log_type] = logs[log_type][-1000:]

        self.save_logs(logs)

    def get_recent_logs(self, log_type, limit=50):
        logs = self.load_logs()
        return logs.get(log_type, [])[-limit:]

    def get_user_logs(self, user_id, log_type=None, limit=50):
        logs = self.load_logs()
        user_logs = []

        if log_type:
            for log in logs.get(log_type, []):
                if log["user_id"] == str(user_id):
                    user_logs.append(log)
        else:
            for log_category in logs.values():
                for log in log_category:
                    if log["user_id"] == str(user_id):
                        user_logs.append(log)

        # ترتيب حسب الوقت (الأحدث أولاً)
        user_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return user_logs[:limit]

# إنشاء مثيل من نظام السجلات
logs_system = LogsSystem()

def get_username(user_id, bot=None, guild=None):
    """دالة مساعدة لجلب اسم المستخدم"""
    from data_utils import load_data
    data = load_data()

    # أولاً: البحث في البيانات المحفوظة
    username = data.get(str(user_id), {}).get("username")
    if username and username != "مستخدم مجهول":
        return username

    # ثانياً: البحث في Discord
    if bot:
        try:
            user = bot.get_user(int(user_id))
            if user:
                return user.display_name
        except:
            pass

    if guild:
        try:
            member = guild.get_member(int(user_id))
            if member:
                return member.display_name
        except:
            pass

    # في النهاية: عرض مجهول
    return f"مستخدم {str(user_id)[:8]}"

# ======= قوائم الترتيب =======
def get_top_players_by_wealth(data, limit=10):
    """حساب أغنى اللاعبين"""
    def calculate_wealth(user_data):
        if not isinstance(user_data, dict):
            return 0
        balance = user_data.get("balance", {})
        if isinstance(balance, int):
            balance = {"دولار": balance, "ذهب": 0, "ماس": 0}
        if not isinstance(balance, dict):
            return 0

        dollars = balance.get("دولار", 0)
        gold = balance.get("ذهب", 0)
        diamonds = balance.get("ماس", 0)

        return dollars + (gold * 50) + (diamonds * 100)

    wealth_list = []
    for user_id, user_data in data.items():
        wealth = calculate_wealth(user_data)
        wealth_list.append((user_id, wealth, user_data))

    wealth_list.sort(key=lambda x: x[1], reverse=True)
    return wealth_list[:limit]

def get_top_thieves(limit=10):
    """أكثر اللاعبين نهباً"""
    logs = logs_system.load_logs()
    theft_counts = {}

    for log in logs.get("theft_logs", []):
        user_id = log["user_id"]
        theft_counts[user_id] = theft_counts.get(user_id, 0) + 1

    sorted_thieves = sorted(theft_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_thieves[:limit]

def get_top_workers(limit=10):
    """أكثر اللاعبين عملاً"""
    logs = logs_system.load_logs()
    work_counts = {}

    for log in logs.get("work_logs", []):
        user_id = log["user_id"]
        work_counts[user_id] = work_counts.get(user_id, 0) + 1

    sorted_workers = sorted(work_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_workers[:limit]

def get_top_traders(limit=10):
    """أكثر اللاعبين تداولاً"""
    logs = logs_system.load_logs()
    trade_counts = {}
    trade_profits = {}

    for log in logs.get("trade_logs", []):
        user_id = log["user_id"]
        trade_counts[user_id] = trade_counts.get(user_id, 0) + 1
        profit = log["details"].get("profit", 0)
        trade_profits[user_id] = trade_profits.get(user_id, 0) + profit

    # ترتيب حسب الأرباح
    sorted_traders = sorted(trade_profits.items(), key=lambda x: x[1], reverse=True)
    return sorted_traders[:limit]

def get_top_farmers(limit=10):
    """أكثر اللاعبين زراعة"""
    logs = logs_system.load_logs()
    farm_counts = {}

    for log in logs.get("farm_logs", []):
        user_id = log["user_id"]
        farm_counts[user_id] = farm_counts.get(user_id, 0) + 1

    sorted_farmers = sorted(farm_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_farmers[:limit]

def get_top_gamers(limit=10):
    """أكثر اللاعبين لعباً للألعاب"""
    logs = logs_system.load_logs()
    game_counts = {}

    for log in logs.get("game_logs", []):
        user_id = log["user_id"]
        game_counts[user_id] = game_counts.get(user_id, 0) + 1

    sorted_gamers = sorted(game_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_gamers[:limit]

# ======= واجهات قوائم الترتيب =======
class LeaderboardView(View):
    def __init__(self, bot, guild):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild

    @discord.ui.button(label="👑 الأثرياء", style=ButtonStyle.primary, emoji="💰")
    async def wealth_leaderboard(self, interaction: discord.Interaction, button: Button):
        from data_utils import load_data
        data = load_data()
        top_wealthy = get_top_players_by_wealth(data)

        embed = Embed(title="👑 قائمة الأثرياء", color=0xFFD700)
        description = "🏆 أغنى 10 لاعبين في النظام:\n\n"

        for i, (user_id, wealth, user_data) in enumerate(top_wealthy, 1):
            # استخدام الاسم المحفوظ في البيانات أولاً
            name = user_data.get("username", f"مستخدم {user_id[:8]}")
            if name == "مستخدم مجهول":
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        name = user.display_name
                    else:
                        member = self.guild.get_member(int(user_id))
                        name = member.display_name if member else f"مستخدم {user_id[:8]}"
                except:
                    name = f"مستخدم {user_id[:8]}"
            balance = user_data.get("balance", {})
            if isinstance(balance, int):
                balance = {"دولار": balance, "ذهب": 0, "ماس": 0}

            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            description += f"{emoji} **{name}**\n"
            description += f"💰 {wealth:,} نقطة ثروة\n"
            description += f"💵 {balance.get('دولار', 0):,} | 🪙 {balance.get('ذهب', 0):,} | 💎 {balance.get('ماس', 0):,}\n\n"

        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🦹 النهابين", style=ButtonStyle.danger, emoji="⚔️")
    async def thieves_leaderboard(self, interaction: discord.Interaction, button: Button):
        top_thieves = get_top_thieves()

        embed = Embed(title="🦹 قائمة أشهر النهابين", color=0xFF4444)
        description = "⚔️ أكثر 10 لاعبين نهباً:\n\n"

        for i, (user_id, count) in enumerate(top_thieves, 1):
            # البحث عن الاسم في البيانات المحفوظة أولاً
            from data_utils import load_data
            data = load_data()
            name = data.get(user_id, {}).get("username", f"مستخدم {user_id[:8]}")
            if name == "مستخدم مجهول":
                try:
                    user = self.bot.get_user(int(user_id))
                    if user:
                        name = user.display_name
                    else:
                        member = self.guild.get_member(int(user_id))
                        name = member.display_name if member else f"مستخدم {user_id[:8]}"
                except:
                    name = f"مستخدم {user_id[:8]}"

            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            description += f"{emoji} **{name}**\n"
            description += f"⚔️ {count} عملية نهب\n\n"

        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="👷 العمال", style=ButtonStyle.success, emoji="💼")
    async def workers_leaderboard(self, interaction: discord.Interaction, button: Button):
        top_workers = get_top_workers()

        embed = Embed(title="👷 قائمة أنشط العمال", color=0x44FF44)
        description = "💼 أكثر 10 لاعبين عملاً:\n\n"

        for i, (user_id, count) in enumerate(top_workers, 1):
            name = get_username(user_id, self.bot, self.guild)

            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            description += f"{emoji} **{name}**\n"
            description += f"💼 {count} يوم عمل\n\n"

        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="📈 المتداولين", style=ButtonStyle.secondary, emoji="💹")
    async def traders_leaderboard(self, interaction: discord.Interaction, button: Button):
        top_traders = get_top_traders()

        embed = Embed(title="📈 قائمة أنجح المتداولين", color=0x4444FF)
        description = "💹 أكثر 10 لاعبين ربحاً من التداول:\n\n"

        for i, (user_id, profit) in enumerate(top_traders, 1):
            name = get_username(user_id, self.bot, self.guild)

            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            description += f"{emoji} **{name}**\n"
            description += f"💹 {profit:,} ربح إجمالي\n\n"

        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🌾 المزارعين", style=ButtonStyle.success, emoji="🚜")
    async def farmers_leaderboard(self, interaction: discord.Interaction, button: Button):
        top_farmers = get_top_farmers()

        embed = Embed(title="🌾 قائمة أنشط المزارعين", color=0x44AA44)
        description = "🚜 أكثر 10 لاعبين زراعة:\n\n"

        for i, (user_id, count) in enumerate(top_farmers, 1):
            name = get_username(user_id, self.bot, self.guild)

            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            description += f"{emoji} **{name}**\n"
            description += f"🌾 {count} عملية زراعة\n\n"

        embed.description = description
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ======= واجهة السجلات =======
class LogsView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="📊 سجلي الشخصي", style=ButtonStyle.primary)
    async def personal_logs(self, interaction: discord.Interaction, button: Button):
        user_logs = logs_system.get_user_logs(self.user_id, limit=20)

        embed = Embed(title="📊 سجلك الشخصي", color=0x3498db)

        if not user_logs:
            embed.description = "لا توجد سجلات متاحة."
        else:
            description = "آخر 20 نشاط:\n\n"
            for log in user_logs[:10]:  # عرض آخر 10 فقط لتجنب الرسالة الطويلة
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%m/%d %H:%M")
                description += f"🕒 {time_str} | {log['action']}\n"

            embed.description = description

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚔️ سجلات النهب", style=ButtonStyle.danger)
    async def theft_logs(self, interaction: discord.Interaction, button: Button):
        theft_logs = logs_system.get_recent_logs("theft_logs", 15)

        embed = Embed(title="⚔️ آخر عمليات النهب", color=0xe74c3c)

        if not theft_logs:
            embed.description = "لا توجد عمليات نهب مسجلة."
        else:
            description = ""
            for log in theft_logs[-10:]:  # آخر 10 عمليات
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%m/%d %H:%M")
                amount = log["details"].get("amount", 0)
                target = log["details"].get("target", "مجهول")
                description += f"🕒 {time_str} | {log['username']} نهب {amount}$ من {target}\n"

            embed.description = description

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💼 سجلات العمل", style=ButtonStyle.success)
    async def work_logs(self, interaction: discord.Interaction, button: Button):
        work_logs = logs_system.get_recent_logs("work_logs", 15)

        embed = Embed(title="💼 آخر أنشطة العمل", color=0x2ecc71)

        if not work_logs:
            embed.description = "لا توجد أنشطة عمل مسجلة."
        else:
            description = ""
            for log in work_logs[-10:]:
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%m/%d %H:%M")
                earned = log["details"].get("earned", 0)
                job = log["details"].get("job", "مواطن")
                description += f"🕒 {time_str} | {log['username']} ({job}) ربح {earned}$\n"

            embed.description = description

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎮 سجلات الألعاب", style=ButtonStyle.secondary)
    async def game_logs(self, interaction: discord.Interaction, button: Button):
        game_logs = logs_system.get_recent_logs("game_logs", 15)

        embed = Embed(title="🎮 آخر أنشطة الألعاب", color=0x9b59b6)

        if not game_logs:
            embed.description = "لا توجد أنشطة ألعاب مسجلة."
        else:
            description = ""
            for log in game_logs[-10:]:
                time_str = datetime.fromisoformat(log["timestamp"]).strftime("%m/%d %H:%M")
                game = log["details"].get("game", "لعبة")
                result = log["details"].get("result", "لعب")
                description += f"🕒 {time_str} | {log['username']} لعب {game} - {result}\n"

            embed.description = description

        await interaction.response.send_message(embed=embed, ephemeral=True)