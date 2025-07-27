
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Modal, TextInput
import random
import asyncio

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system
from tasks_system import tasks_system

def setup_game_commands(bot):
    """إعداد أوامر الألعاب"""
    
    @bot.command(name="حجر_ورقة_مقص")
    async def rock_paper_scissors(ctx):
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "حجر_ورقة_مقص")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
            return

        class RPSView(View):
            def __init__(self):
                super().__init__(timeout=30)
                self.user_choice = None

            @discord.ui.button(label="🪨 حجر", style=ButtonStyle.secondary)
            async def rock(self, interaction: Interaction, button: Button):
                await self.play_game(interaction, "حجر", "🪨")

            @discord.ui.button(label="📄 ورقة", style=ButtonStyle.primary)
            async def paper(self, interaction: Interaction, button: Button):
                await self.play_game(interaction, "ورقة", "📄")

            @discord.ui.button(label="✂️ مقص", style=ButtonStyle.danger)
            async def scissors(self, interaction: Interaction, button: Button):
                await self.play_game(interaction, "مقص", "✂️")

            async def play_game(self, interaction: Interaction, choice, emoji):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                bot_choices = ["حجر", "ورقة", "مقص"]
                bot_emojis = {"حجر": "🪨", "ورقة": "📄", "مقص": "✂️"}
                bot_choice = random.choice(bot_choices)

                if choice == bot_choice:
                    result = "تعادل! 🤝"
                    color = 0xFFD700
                    reward = 500
                elif (choice == "حجر" and bot_choice == "مقص") or \
                     (choice == "ورقة" and bot_choice == "حجر") or \
                     (choice == "مقص" and bot_choice == "ورقة"):
                    result = "فزت! 🎉"
                    color = 0x00FF00
                    reward = 2000
                else:
                    result = "خسرت! 😢"
                    color = 0xFF0000
                    reward = 100

                init_user(user_id, ctx.author.display_name)
                data = load_data()
                data[user_id]["balance"]["دولار"] += reward
                save_data(data)

                embed = discord.Embed(
                    title="🎮 حجر ورقة مقص",
                    description=f"{emoji} أنت اخترت: **{choice}**\n{bot_emojis[bot_choice]} البوت اختار: **{bot_choice}**\n\n{result}\n💰 ربحت: {reward} دولار",
                    color=color
                )

                logs_system.add_log(
                    "game_logs",
                    user_id,
                    ctx.author.display_name,
                    "لعب حجر ورقة مقص",
                    {"game": "حجر_ورقة_مقص", "result": result, "reward": reward}
                )
                
                if "فزت" in result:
                    completed_tasks = tasks_system.update_task_progress(user_id, "win_games", 1)
                    if completed_tasks:
                        embed.add_field(
                            name="🎯 مهام مكتملة!",
                            value=f"✅ أكملت {len(completed_tasks)} مهمة!",
                            inline=False
                        )

                update_cooldown(user_id, "حجر_ورقة_مقص")
                await interaction.response.edit_message(embed=embed, view=None)

        embed = discord.Embed(
            title="🎮 لعبة حجر ورقة مقص",
            description="اختر حركتك:",
            color=0x3498db
        )
        await ctx.send(embed=embed, view=RPSView())

    @bot.command(name="تخمين")
    async def guessing_game(ctx):
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "تخمين")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل اللعب مرة أخرى.")
            return

        secret_number = random.randint(1, 100)
        max_attempts = 15

        class GuessingView(View):
            def __init__(self, author: discord.Member, target: int):
                super().__init__(timeout=120)
                self.author = author
                self.target = target
                self.attempts_left = max_attempts
                self.message = None
                self.game_over = False
                self.result_text = f"🎯 خمن رقمًا بين 1 و 100\n📉 لديك {self.attempts_left} محاولة"

            @discord.ui.button(label="🎲 خمن", style=ButtonStyle.primary)
            async def guess_button(self, interaction: Interaction, button: Button):
                if interaction.user.id != self.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                if self.game_over:
                    await interaction.response.send_message("❌ اللعبة انتهت!", ephemeral=True)
                    return

                view = self

                class NumberModal(Modal, title="🔮 أدخل رقمك"):
                    def __init__(modal_self):
                        super().__init__()
                        modal_self.number_input = TextInput(
                            label="اكتب رقمًا من 1 إلى 100",
                            placeholder="مثلاً: 42",
                            max_length=3,
                            required=True
                        )
                        modal_self.add_item(modal_self.number_input)

                    async def on_submit(modal_self, modal_interaction: Interaction):
                        try:
                            guess = int(modal_self.number_input.value.strip())
                            if not 1 <= guess <= 100:
                                raise ValueError
                        except ValueError:
                            await modal_interaction.response.send_message("🚫 الرقم غير صالح. اختر من 1 إلى 100.", ephemeral=True)
                            return

                        init_user(user_id, ctx.author.display_name)
                        data = load_data()

                        view.attempts_left -= 1

                        if guess == view.target:
                            reward = (view.attempts_left * 500) + 8000
                            data[user_id]["balance"]["دولار"] = data[user_id]["balance"].get("دولار", 0) + reward
                            save_data(data)
                            update_cooldown(user_id, "تخمين")
                            view.result_text = f"🎉 صحيح! الرقم هو {view.target}.\n💰 ربحت {reward} دولار.\n🏆 محاولات متبقية: {view.attempts_left}"
                            view.game_over = True
                            view.disable_all_items()
                        elif view.attempts_left == 0:
                            reward = 500
                            data[user_id]["balance"]["دولار"] = data[user_id]["balance"].get("دولار", 0) + reward
                            save_data(data)
                            update_cooldown(user_id, "تخمين")
                            view.result_text = f"💥 انتهت المحاولات! الرقم الصحيح كان {view.target}.\n💸 مكافأة تشجيعية: {reward} دولار."
                            view.game_over = True
                            view.disable_all_items()
                        else:
                            hint = "🔺 أعلى" if guess < view.target else "🔻 أقل"
                            view.result_text = f"❌ خطأ! رقمك: {guess}\n{hint}\n📉 المحاولات المتبقية: {view.attempts_left}"

                        await modal_interaction.response.defer()
                        await view.update_message()

                await interaction.response.send_modal(NumberModal())

            async def update_message(self):
                embed = discord.Embed(
                    title="🔮 لعبة التخمين",
                    description=self.result_text,
                    color=discord.Color.green() if not self.game_over else (discord.Color.gold() if "🎉" in self.result_text else discord.Color.red())
                )
                if self.message:
                    await self.message.edit(embed=embed, view=self)

            def disable_all_items(self):
                for item in self.children:
                    item.disabled = True

        view = GuessingView(ctx.author, secret_number)
        embed = discord.Embed(
            title="🔮 لعبة تخمين الرقم",
            description=f"خمن رقماً بين 1 و 100!\n📉 لديك {max_attempts} محاولة.\n🏆 كلما خمنت أسرع، زادت المكافأة!",
            color=discord.Color.green()
        )
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

    # يمكن إضافة المزيد من الألعاب هنا...
