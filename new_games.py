
import discord
from discord.ext import commands
from discord import Embed, ButtonStyle, Interaction
from discord.ui import View, Button, Select
import random
import asyncio

from data_utils import load_data, save_data, init_user
from cooldown import check_cooldown, update_cooldown
from logs_system import logs_system

def setup_new_games(bot):
    """إعداد الألعاب الجديدة"""

    @bot.command(name="لوتو")
    async def lottery_game(ctx):
        """لعبة اللوتو بأرقام محظوظة"""
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "لوتو")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل لعب اللوتو مرة أخرى.")
            return

        init_user(user_id, ctx.author.display_name)
        data = load_data()
        user = data[user_id]
        
        # تكلفة اللعب
        ticket_cost = 5000
        if user["balance"].get("دولار", 0) < ticket_cost:
            await ctx.send(f"❌ تحتاج إلى {ticket_cost:,} دولار لشراء تذكرة لوتو!")
            return

        class LotteryView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.selected_numbers = []
                self.max_numbers = 6

            @discord.ui.button(label="🎲 اختيار عشوائي", style=ButtonStyle.primary)
            async def random_pick(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                self.selected_numbers = random.sample(range(1, 50), self.max_numbers)
                await self.play_lottery(interaction)

            @discord.ui.button(label="🔢 اختيار يدوي", style=ButtonStyle.secondary)
            async def manual_pick(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                class NumberModal(discord.ui.Modal, title="اختر 6 أرقام"):
                    def __init__(self):
                        super().__init__()
                        self.numbers_input = discord.ui.TextInput(
                            label="أدخل 6 أرقام من 1-49 مفصولة بمسافات",
                            placeholder="مثال: 7 14 21 28 35 42",
                            required=True
                        )
                        self.add_item(self.numbers_input)

                    async def on_submit(self, modal_interaction: Interaction):
                        try:
                            numbers = [int(x.strip()) for x in self.numbers_input.value.split()]
                            if len(numbers) != 6:
                                raise ValueError("يجب إدخال 6 أرقام بالضبط")
                            if not all(1 <= n <= 49 for n in numbers):
                                raise ValueError("الأرقام يجب أن تكون بين 1 و 49")
                            if len(set(numbers)) != 6:
                                raise ValueError("لا يمكن تكرار الأرقام")
                            
                            view.selected_numbers = numbers
                            await view.play_lottery(modal_interaction)
                        except ValueError as e:
                            await modal_interaction.response.send_message(f"❌ خطأ: {e}", ephemeral=True)

                await interaction.response.send_modal(NumberModal())

            async def play_lottery(self, interaction: Interaction):
                # خصم تكلفة التذكرة
                user["balance"]["دولار"] -= ticket_cost
                
                # أرقام الفوز العشوائية
                winning_numbers = random.sample(range(1, 50), 6)
                
                # حساب الأرقام المطابقة
                matches = len(set(self.selected_numbers) & set(winning_numbers))
                
                # تحديد الجوائز
                prizes = {
                    6: 1000000,  # المليون!
                    5: 100000,
                    4: 25000,
                    3: 10000,
                    2: 5000,
                    1: 1000,
                    0: 500  # جائزة تشجيعية
                }
                
                prize = prizes.get(matches, 500)
                user["balance"]["دولار"] += prize
                save_data(data)
                
                # إنشاء النتيجة
                embed = Embed(
                    title="🎰 نتائج اللوتو!",
                    color=0xffd700 if matches >= 4 else 0x3498db
                )
                
                embed.add_field(
                    name="🎯 أرقامك",
                    value=" - ".join(map(str, sorted(self.selected_numbers))),
                    inline=False
                )
                
                embed.add_field(
                    name="🏆 الأرقام الفائزة",
                    value=" - ".join(map(str, sorted(winning_numbers))),
                    inline=False
                )
                
                embed.add_field(
                    name="✨ النتيجة",
                    value=f"🎯 {matches} أرقام مطابقة\n💰 ربحت: {prize:,} دولار",
                    inline=True
                )
                
                if matches == 6:
                    embed.add_field(
                        name="🎊 مبروك!",
                        value="🏆 **جائزة المليون!** 🏆",
                        inline=True
                    )
                elif matches >= 4:
                    embed.add_field(
                        name="🎉 ممتاز!",
                        value="💎 جائزة كبيرة!",
                        inline=True
                    )
                
                # تسجيل النشاط
                logs_system.add_log(
                    "game_logs",
                    user_id,
                    ctx.author.display_name,
                    "لعب اللوتو",
                    {"matches": matches, "prize": prize, "cost": ticket_cost}
                )
                
                update_cooldown(user_id, "لوتو")
                
                if hasattr(interaction, 'response'):
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    await interaction.edit_original_response(embed=embed, view=None)

        embed = Embed(
            title="🎰 لعبة اللوتو الكبرى",
            description=f"🎟️ **تكلفة التذكرة:** {ticket_cost:,} دولار\n🎯 **اختر 6 أرقام من 1 إلى 49**\n\n🏆 **الجوائز:**\n6 مطابقات: 1,000,000$ 💎\n5 مطابقات: 100,000$ 🥇\n4 مطابقات: 25,000$ 🥈\n3 مطابقات: 10,000$ 🥉",
            color=0xffd700
        )
        
        await ctx.send(embed=embed, view=LotteryView())

    @bot.command(name="روليت")
    async def roulette_game(ctx):
        """لعبة الروليت الأوروبية"""
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "روليت")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل لعب الروليت مرة أخرى.")
            return

        class RouletteView(View):
            def __init__(self):
                super().__init__(timeout=120)
                self.bet_amount = 0
                self.bet_type = None
                self.bet_value = None

            @discord.ui.button(label="🔴 أحمر", style=ButtonStyle.danger)
            async def bet_red(self, interaction: Interaction, button: Button):
                await self.set_bet(interaction, "color", "red", "🔴 أحمر")

            @discord.ui.button(label="⚫ أسود", style=ButtonStyle.secondary)
            async def bet_black(self, interaction: Interaction, button: Button):
                await self.set_bet(interaction, "color", "black", "⚫ أسود")

            @discord.ui.button(label="🟢 صفر", style=ButtonStyle.success)
            async def bet_zero(self, interaction: Interaction, button: Button):
                await self.set_bet(interaction, "number", 0, "🟢 صفر")

            @discord.ui.button(label="🔢 رقم محدد", style=ButtonStyle.primary)
            async def bet_number(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                class NumberModal(discord.ui.Modal, title="اختر رقم للمراهنة"):
                    def __init__(self):
                        super().__init__()
                        self.number_input = discord.ui.TextInput(
                            label="أدخل رقم من 1 إلى 36",
                            placeholder="مثال: 17",
                            max_length=2
                        )
                        self.add_item(self.number_input)

                    async def on_submit(self, modal_interaction: Interaction):
                        try:
                            number = int(self.number_input.value)
                            if not 1 <= number <= 36:
                                raise ValueError
                            await view.set_bet(modal_interaction, "number", number, f"🔢 الرقم {number}")
                        except ValueError:
                            await modal_interaction.response.send_message("❌ أدخل رقماً من 1 إلى 36!", ephemeral=True)

                await interaction.response.send_modal(NumberModal())

            async def set_bet(self, interaction: Interaction, bet_type, bet_value, display_name):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                self.bet_type = bet_type
                self.bet_value = bet_value

                class AmountModal(discord.ui.Modal, title="مبلغ المراهنة"):
                    def __init__(self):
                        super().__init__()
                        self.amount_input = discord.ui.TextInput(
                            label="أدخل مبلغ المراهنة",
                            placeholder="مثال: 10000",
                            required=True
                        )
                        self.add_item(self.amount_input)

                    async def on_submit(self, amount_interaction: Interaction):
                        try:
                            amount = int(self.amount_input.value)
                            if amount <= 0:
                                raise ValueError
                            
                            init_user(user_id, ctx.author.display_name)
                            data = load_data()
                            user = data[user_id]
                            
                            if user["balance"].get("دولار", 0) < amount:
                                await amount_interaction.response.send_message("❌ لا تملك ما يكفي من المال!", ephemeral=True)
                                return
                            
                            view.bet_amount = amount
                            await view.spin_roulette(amount_interaction, display_name)
                            
                        except ValueError:
                            await amount_interaction.response.send_message("❌ أدخل مبلغاً صحيحاً!", ephemeral=True)

                if hasattr(interaction, 'response'):
                    await interaction.response.send_modal(AmountModal())
                else:
                    await interaction.followup.send_modal(AmountModal())

            async def spin_roulette(self, interaction: Interaction, bet_display):
                # دوران الروليت
                winning_number = random.randint(0, 36)
                
                # تحديد لون الرقم الفائز
                if winning_number == 0:
                    winning_color = "green"
                    color_emoji = "🟢"
                elif winning_number in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]:
                    winning_color = "red"
                    color_emoji = "🔴"
                else:
                    winning_color = "black"
                    color_emoji = "⚫"
                
                # حساب الفوز
                won = False
                multiplier = 0
                
                if self.bet_type == "color":
                    if self.bet_value == winning_color:
                        won = True
                        multiplier = 2  # ضعف المبلغ
                elif self.bet_type == "number":
                    if self.bet_value == winning_number:
                        won = True
                        multiplier = 36 if winning_number == 0 else 35  # الصفر يدفع 36:1
                
                # تطبيق النتيجة
                data = load_data()
                user = data[user_id]
                user["balance"]["دولار"] -= self.bet_amount
                
                if won:
                    winnings = self.bet_amount * multiplier
                    user["balance"]["دولار"] += winnings
                    profit = winnings - self.bet_amount
                else:
                    profit = -self.bet_amount
                
                save_data(data)
                
                # إنشاء النتيجة
                embed = Embed(
                    title="🎰 نتائج الروليت!",
                    color=0x00ff00 if won else 0xff0000
                )
                
                embed.add_field(
                    name="🎯 مراهنتك",
                    value=f"{bet_display}\n💰 {self.bet_amount:,} دولار",
                    inline=True
                )
                
                embed.add_field(
                    name="🏆 الرقم الفائز",
                    value=f"{color_emoji} **{winning_number}**",
                    inline=True
                )
                
                if won:
                    embed.add_field(
                        name="🎉 ربحت!",
                        value=f"💰 +{profit:,} دولار\n🎊 مضاعف: {multiplier}x",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="💔 خسرت",
                        value=f"💸 -{self.bet_amount:,} دولار",
                        inline=True
                    )
                
                # تسجيل النشاط
                logs_system.add_log(
                    "game_logs",
                    user_id,
                    ctx.author.display_name,
                    "لعب الروليت",
                    {"bet_type": self.bet_type, "bet_value": self.bet_value, "winning_number": winning_number, "profit": profit}
                )
                
                update_cooldown(user_id, "روليت")
                
                if hasattr(interaction, 'response'):
                    await interaction.response.edit_message(embed=embed, view=None)
                else:
                    await interaction.edit_original_response(embed=embed, view=None)

        embed = Embed(
            title="🎰 روليت الكازينو الأوروبية",
            description="🎯 **اختر نوع المراهنة:**\n\n🔴 **أحمر:** مضاعف 2x\n⚫ **أسود:** مضاعف 2x\n🟢 **صفر:** مضاعف 36x\n🔢 **رقم محدد:** مضاعف 35x",
            color=0xffd700
        )
        
        embed.set_footer(text="💡 الأرقام من 1-36 + الصفر")
        
        await ctx.send(embed=embed, view=RouletteView())

    @bot.command(name="بلاك_جاك")
    async def blackjack_game(ctx):
        """لعبة البلاك جاك"""
        user_id = str(ctx.author.id)
        can_use, time_left = check_cooldown(user_id, "بلاك_جاك")
        if not can_use:
            await ctx.send(f"⏳ يجب الانتظار {time_left} قبل لعب البلاك جاك مرة أخرى.")
            return

        # الأوراق
        suits = ['♠️', '♥️', '♦️', '♣️']
        ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
        
        def create_deck():
            return [(rank, suit) for suit in suits for rank in ranks]
        
        def card_value(rank):
            if rank in ['J', 'Q', 'K']:
                return 10
            elif rank == 'A':
                return 11  # سيتم تعديلها لاحقاً
            else:
                return int(rank)
        
        def hand_value(hand):
            value = sum(card_value(card[0]) for card in hand)
            aces = sum(1 for card in hand if card[0] == 'A')
            
            while value > 21 and aces:
                value -= 10
                aces -= 1
            
            return value
        
        def format_hand(hand):
            return ' '.join(f"{card[0]}{card[1]}" for card in hand)

        class BlackjackView(View):
            def __init__(self, bet_amount):
                super().__init__(timeout=180)
                self.bet_amount = bet_amount
                self.deck = create_deck()
                random.shuffle(self.deck)
                
                # توزيع البطاقات الأولى
                self.player_hand = [self.deck.pop(), self.deck.pop()]
                self.dealer_hand = [self.deck.pop(), self.deck.pop()]
                self.game_over = False

            @discord.ui.button(label="🃏 سحب بطاقة", style=ButtonStyle.primary)
            async def hit(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id or self.game_over:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                self.player_hand.append(self.deck.pop())
                player_value = hand_value(self.player_hand)
                
                if player_value > 21:
                    await self.end_game(interaction, "bust")
                else:
                    await self.update_game(interaction)

            @discord.ui.button(label="🛑 توقف", style=ButtonStyle.secondary)
            async def stand(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id or self.game_over:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return

                await self.dealer_turn(interaction)

            async def update_game(self, interaction):
                player_value = hand_value(self.player_hand)
                
                embed = Embed(title="🃏 لعبة البلاك جاك", color=0x3498db)
                
                embed.add_field(
                    name="🎯 أوراقك",
                    value=f"{format_hand(self.player_hand)}\n**القيمة:** {player_value}",
                    inline=True
                )
                
                embed.add_field(
                    name="🤖 أوراق الموزع",
                    value=f"{self.dealer_hand[0][0]}{self.dealer_hand[0][1]} ❓\n**القيمة:** {card_value(self.dealer_hand[0][0])} + ❓",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 المراهنة",
                    value=f"{self.bet_amount:,} دولار",
                    inline=True
                )
                
                embed.set_footer(text="🃏 سحب بطاقة أو توقف؟")
                
                await interaction.response.edit_message(embed=embed, view=self)

            async def dealer_turn(self, interaction):
                dealer_value = hand_value(self.dealer_hand)
                
                while dealer_value < 17:
                    self.dealer_hand.append(self.deck.pop())
                    dealer_value = hand_value(self.dealer_hand)
                
                if dealer_value > 21:
                    await self.end_game(interaction, "dealer_bust")
                else:
                    player_value = hand_value(self.player_hand)
                    if player_value > dealer_value:
                        await self.end_game(interaction, "win")
                    elif player_value < dealer_value:
                        await self.end_game(interaction, "lose")
                    else:
                        await self.end_game(interaction, "tie")

            async def end_game(self, interaction, result):
                self.game_over = True
                
                player_value = hand_value(self.player_hand)
                dealer_value = hand_value(self.dealer_hand)
                
                data = load_data()
                user = data[user_id]
                
                # حساب النتيجة
                if result == "bust":
                    outcome = "💥 تجاوزت 21! خسرت"
                    user["balance"]["دولار"] -= self.bet_amount
                    profit = -self.bet_amount
                elif result == "dealer_bust":
                    outcome = "🎉 الموزع تجاوز 21! ربحت"
                    user["balance"]["دولار"] += self.bet_amount
                    profit = self.bet_amount
                elif result == "win":
                    outcome = "🏆 ربحت!"
                    user["balance"]["دولار"] += self.bet_amount
                    profit = self.bet_amount
                elif result == "lose":
                    outcome = "💔 خسرت"
                    user["balance"]["دولار"] -= self.bet_amount
                    profit = -self.bet_amount
                else:  # tie
                    outcome = "🤝 تعادل"
                    profit = 0
                
                save_data(data)
                
                embed = Embed(
                    title="🃏 نتائج البلاك جاك",
                    description=outcome,
                    color=0x00ff00 if profit >= 0 else 0xff0000
                )
                
                embed.add_field(
                    name="🎯 أوراقك",
                    value=f"{format_hand(self.player_hand)}\n**القيمة:** {player_value}",
                    inline=True
                )
                
                embed.add_field(
                    name="🤖 أوراق الموزع",
                    value=f"{format_hand(self.dealer_hand)}\n**القيمة:** {dealer_value}",
                    inline=True
                )
                
                embed.add_field(
                    name="💰 النتيجة المالية",
                    value=f"الربح/الخسارة: {profit:+,} دولار",
                    inline=True
                )
                
                # تسجيل النشاط
                logs_system.add_log(
                    "game_logs",
                    user_id,
                    ctx.author.display_name,
                    "لعب البلاك جاك",
                    {"result": result, "player_value": player_value, "dealer_value": dealer_value, "profit": profit}
                )
                
                update_cooldown(user_id, "بلاك_جاك")
                
                # إزالة الأزرار
                for item in self.children:
                    item.disabled = True
                
                await interaction.response.edit_message(embed=embed, view=self)

        # طلب مبلغ المراهنة
        class BetModal(discord.ui.Modal, title="مبلغ المراهنة"):
            def __init__(self):
                super().__init__()
                self.amount_input = discord.ui.TextInput(
                    label="أدخل مبلغ المراهنة",
                    placeholder="مثال: 10000",
                    required=True
                )
                self.add_item(self.amount_input)

            async def on_submit(self, modal_interaction: Interaction):
                try:
                    amount = int(self.amount_input.value)
                    if amount <= 0:
                        raise ValueError
                    
                    init_user(user_id, ctx.author.display_name)
                    data = load_data()
                    user = data[user_id]
                    
                    if user["balance"].get("دولار", 0) < amount:
                        await modal_interaction.response.send_message("❌ لا تملك ما يكفي من المال!", ephemeral=True)
                        return
                    
                    # بدء اللعبة
                    view = BlackjackView(amount)
                    await view.update_game(modal_interaction)
                    
                except ValueError:
                    await modal_interaction.response.send_message("❌ أدخل مبلغاً صحيحاً!", ephemeral=True)

        class StartBlackjackView(View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="🃏 ابدأ اللعب", style=ButtonStyle.success)
            async def start_game(self, interaction: Interaction, button: Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ هذه ليست لعبتك!", ephemeral=True)
                    return
                await interaction.response.send_modal(BetModal())

        embed = Embed(
            title="🃏 البلاك جاك - لعبة 21",
            description="🎯 **الهدف:** احصل على 21 أو اقترب منها دون تجاوزها\n\n🃏 **قواعد:**\n• A = 11 أو 1\n• J, Q, K = 10\n• الأرقام = قيمتها\n\n🏆 **اربح مثل مراهنتك!**",
            color=0x2c3e50
        )
        
        await ctx.send(embed=embed, view=StartBlackjackView())

    return True
