import json
import os
import time
from datetime import datetime
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select
from discord import SelectOption

LOGS_FILE = "system_logs.json"

class LogsSystem:
    def __init__(self):
        self.logs_file = LOGS_FILE

    def load_logs(self):
        """تحميل السجلات"""
        if not os.path.exists(self.logs_file):
            return {}
        try:
            with open(self.logs_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def save_logs(self, logs):
        """حفظ السجلات"""
        with open(self.logs_file, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)

    def add_log(self, category, user_id, username, action, details=None):
        """إضافة سجل جديد"""
        logs = self.load_logs()

        if category not in logs:
            logs[category] = []

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": str(user_id),
            "username": username,
            "action": action,
            "details": details or {}
        }

        logs[category].append(log_entry)

        # الاحتفاظ بآخر 1000 سجل فقط لكل فئة
        if len(logs[category]) > 1000:
            logs[category] = logs[category][-1000:]

        self.save_logs(logs)

    def get_user_logs(self, user_id, limit=50):
        """جلب سجلات مستخدم محدد"""
        logs = self.load_logs()
        user_logs = []

        for category_logs in logs.values():
            for log in category_logs:
                if log["user_id"] == str(user_id):
                    user_logs.append(log)

        # ترتيب حسب التاريخ
        user_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return user_logs[:limit]

    def get_category_logs(self, category, limit=50):
        """جلب سجلات فئة محددة"""
        logs = self.load_logs()
        category_logs = logs.get(category, [])
        return sorted(category_logs, key=lambda x: x["timestamp"], reverse=True)[:limit]

class LeaderboardView(View):
    def __init__(self, bot, guild):
        super().__init__(timeout=120)
        self.bot = bot
        self.guild = guild

    @discord.ui.button(label="💰 أغنى اللاعبين", style=ButtonStyle.success)
    async def richest_players(self, interaction: Interaction, button: Button):
        from data_utils import load_data

        data = load_data()
        wealth_list = []

        for user_id, user_data in data.items():
            if isinstance(user_data, dict):
                balance = user_data.get("balance", {})
                if isinstance(balance, dict):
                    total_wealth = balance.get("دولار", 0) + (balance.get("ذهب", 0) * 50) + (balance.get("ماس", 0) * 100)
                    wealth_list.append({
                        "user_id": user_id,
                        "username": user_data.get("username", "مجهول"),
                        "wealth": total_wealth
                    })

        wealth_list.sort(key=lambda x: x["wealth"], reverse=True)

        embed = Embed(title="💰 قائمة أغنى اللاعبين", color=0xffd700)
        description = ""

        for i, player in enumerate(wealth_list[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description += f"{medal} **{player['username']}** - {player['wealth']:,} نقطة ثروة\n"

        embed.description = description or "لا توجد بيانات متاحة"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="⚔️ أفضل المحاربين", style=ButtonStyle.danger)
    async def best_fighters(self, interaction: Interaction, button: Button):
        from dungeons_system import load_dungeons_data

        dungeons_data = load_dungeons_data()
        fighters_list = []

        for user_id, progress in dungeons_data.items():
            victories = progress.get("total_victories", 0)
            defeats = progress.get("total_defeats", 0)
            total_battles = victories + defeats
            win_rate = (victories / total_battles * 100) if total_battles > 0 else 0

            if victories > 0:
                fighters_list.append({
                    "user_id": user_id,
                    "victories": victories,
                    "win_rate": win_rate
                })

        fighters_list.sort(key=lambda x: (x["victories"], x["win_rate"]), reverse=True)

        embed = Embed(title="⚔️ قائمة أفضل المحاربين", color=0xff0000)
        description = ""

        for i, fighter in enumerate(fighters_list[:10], 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            description += f"{medal} مستخدم {fighter['user_id'][:8]} - {fighter['victories']} انتصار ({fighter['win_rate']:.1f}%)\n"

        embed.description = description or "لا توجد بيانات متاحة"
        await interaction.response.send_message(embed=embed, ephemeral=True)

class LogsView(View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=120)
        self.bot = bot
        self.user_id = user_id

    @discord.ui.button(label="🛒 سجلات المتجر", style=ButtonStyle.primary)
    async def shop_logs(self, interaction: Interaction, button: Button):
        logs = logs_system.get_category_logs("shop_logs", 20)

        embed = Embed(title="🛒 سجلات المتجر", color=0x3498db)
        description = ""

        for log in logs:
            time_obj = datetime.fromisoformat(log["timestamp"])
            time_str = time_obj.strftime("%m/%d %H:%M")
            description += f"🕒 {time_str} - {log['username']}: {log['action']}\n"

        embed.description = description or "لا توجد سجلات"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💰 سجلات التداول", style=ButtonStyle.success)
    async def trade_logs(self, interaction: Interaction, button: Button):
        logs = logs_system.get_category_logs("trade_logs", 20)

        embed = Embed(title="💰 سجلات التداول", color=0x00ff00)
        description = ""

        for log in logs:
            time_obj = datetime.fromisoformat(log["timestamp"])
            time_str = time_obj.strftime("%m/%d %H:%M")
            description += f"🕒 {time_str} - {log['username']}: {log['action']}\n"

        embed.description = description or "لا توجد سجلات"
        await interaction.response.send_message(embed=embed, ephemeral=True)

# إنشاء كائن عام للنظام
logs_system = LogsSystem()