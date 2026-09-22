            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(content="💥 עברת את 21! הפסדת את ההימור.", embed=self.create_embed(interaction.user, finished=True), view=self)
            return
        await interaction.response.edit_message(embed=self.create_embed(interaction.user), view=self)

    @discord.ui.button(label="עמוד (Stand)", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: Button):
        # תור הדילר למשוך קלפים עד 17 לפחות
        while self.calculate_score(self.dealer_cards) < 17:
            self.dealer_cards.append(self.deck.pop())

        p_score = self.calculate_score(self.player_cards)
        d_score = self.calculate_score(self.dealer_cards)
        user_id = interaction.user.id

        for child in self.children:
            child.disabled = True

        if d_score > 21 or p_score > d_score:
            add_tokens(user_id, self.bet * 2)
            msg = f"🎉 ניצחת את הקזינו! זכית ב-{self.bet * 2} טוקנים!"
        elif p_score < d_score:
            msg = f"❌ הדילר ניצח! הפסדת {self.bet} טוקנים."
        else:
            add_tokens(user_id, self.bet)
            msg = "🤝 תיקו! הטוקנים שלך הוחזרו."

        await interaction.response.edit_message(content=msg, embed=self.create_embed(interaction.user, finished=True), view=self)


# --- משחק מכרות (Mines) ---
class MinesModal(Modal):
    def __init__(self):
        super().__init__(title="💣 משחק מכרות (Mines)")
        self.bet_input = TextInput(label="כמות טוקנים להימור", placeholder="הכנס סכום...", required=True)
        self.bombs_input = TextInput(label="כמות פצצות (1-24)", placeholder="הכנס מספר פצצות...", required=True)
        self.add_item(self.bet_input)
        self.add_item(self.bombs_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.bet_input.value)
            bombs = int(self.bombs_input.value)
        except ValueError:
            await interaction.response.send_message("❌ נא להזין מספרים שלמים בלבד.", ephemeral=True)
            return

        if bombs < 1 or bombs > 24:
            await interaction.response.send_message("❌ כמות הפצצות חייבת להיות בין 1 ל-24!", ephemeral=True)
            return

        if not remove_tokens(interaction.user.id, bet):
            await interaction.response.send_message("❌ אין לך מספיק טוקנים!", ephemeral=True)
            return

        # יצירת לוח מוסתר (25 משבצות, 1 = פצצה, 0 = יהלום)
        grid = * 25
        for pos in random.sample(range(25), bombs):
            grid[pos] = 1

        view = MinesView(bet, bombs, grid, interaction.user.id)
        embed = view.create_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

class MinesTileButton(Button):
    def __init__(self, index: int):
        super().__init__(label="❓", style=discord.ButtonStyle.secondary, row=index // 5)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: MinesView = self.view
        if interaction.user.id != view.user_id: return

        if self.label != "❓": return

        # בדיקה אם פגע בפצצה
        if view.grid[self.index] == 1:
            self.label, self.style = "💥", discord.ButtonStyle.danger
            view.reveal_all()
            for child in view.children: child.disabled = True
            embed = discord.Embed(title="💥 בום! פגעת בפצצה!", description=f"הפסדת **{view.bet}** טוקנים.", color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=view)
            return

        # מצא יהלום
        self.label, self.style = "💎", discord.ButtonStyle.success
        view.diamonds += 1

        # חישוב מכפיל עולה
        mult = 1.0
        for i in range(view.diamonds):
            mult *= (25 - i) / (25 - view.bombs - i)
        view.current_multiplier = round(mult, 2)

        await interaction.response.edit_message(embed=view.create_embed(), view=view)

class MinesView(View):
    def __init__(self, bet, bombs, grid, user_id):
        super().__init__(timeout=180)
        self.bet = bet
        self.bombs = bombs
        self.grid = grid
        self.user_id = user_id
        self.diamonds = 0
        self.current_multiplier = 1.0

        for i in range(25):
            self.add_item(MinesTileButton(i))
        self.add_item(MinesCashoutButton())

    def create_embed(self):
        embed = discord.Embed(title="💣 קזינו Ticket Royale - מכרות", color=discord.Color.purple())
        embed.add_field(name="💰 הימור", value=f"{self.bet} טוקנים", inline=True)
        embed.add_field(name="💣 פצצות", value=str(self.bombs), inline=True)
        embed.add_field(name="📈 מכפיל נוכחי", value=f"**{self.current_multiplier}x**", inline=False)
        embed.add_field(name="💎 יהלומים שנחשפו", value=str(self.diamonds), inline=True)
        return embed

    def reveal_all(self):
        for child in self.children:
            if isinstance(child, MinesTileButton):
                child.label = "💣" if self.grid[child.index] == 1 else "💎"
                child.style = discord.ButtonStyle.danger if self.grid[child.index] == 1 else discord.ButtonStyle.secondary

class MinesCashoutButton(Button):
    def __init__(self):
        super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.gold, row=4)

    async def callback(self, interaction: discord.Interaction):
        view: MinesView = self.view
        if interaction.user.id != view.user_id: return
        if view.diamonds == 0:
            await interaction.response.send_message("❌ עליך לחשוף לפחות יהלום אחד לפני המשיכה!", ephemeral=True)
            return

        winnings = int(view.bet * view.current_multiplier)
        add_tokens(view.user_id, winnings)
        view.reveal_all()
        for child in view.children: child.disabled = True
        
        embed = discord.Embed(title="💰 משיכת כסף מוצלחת!", description=f"פרשת עם מכפיל של **{view.current_multiplier}x**!\nזכית ב-**{winnings}** טוקנים.", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=view)
# --- משחק רולטה (Roulette) ---
class RouletteModal(Modal):
    def __init__(self):
        super().__init__(title="🎰 רולטה - הימור")
        self.bet_input = TextInput(label="כמות טוקנים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ נא להזין מספר תקין.", ephemeral=True)
            return

        if not remove_tokens(interaction.user.id, bet):
            await interaction.response.send_message("❌ אין לך מספיק טוקנים!", ephemeral=True)
            return

        embed = discord.Embed(title="🎰 שולחן הרולטה", description=f"הימור: **{bet}** טוקנים.\nבחר את סוג ההימור שלך למטה:", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, view=RouletteView(bet, interaction.user.id), ephemeral=True)

class RouletteView(View):
    def __init__(self, bet, user_id):
        super().__init__(timeout=60)
        self.bet = bet
        self.user_id = user_id

    async def play(self, interaction: discord.Interaction, choice: str):
        if interaction.user.id != self.user_id: return
        number = random.randint(0, 36)
        
        if number == 0: color = "ירוק"
        elif number in: color = "אדום"
        else: color = "שחור"

        win = (choice == color)
        payout = self.bet * 14 if color == "ירוק" else self.bet * 2

        for child in self.children: child.disabled = True

        embed = discord.Embed(title=f"🎰 הגלגל נחת על {number} ({color})")
        if win:
            add_tokens(self.user_id, payout)
            embed.color, embed.description = discord.Color.green(), f"🎉 כל הכבוד! זכת ב-**{payout}** טוקנים!"
        else:
            embed.color, embed.description = discord.Color.red(), f"❌ חבל, יצא {color}. הפסדת {self.bet} טוקנים."
        
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔴 אדום (x2)", style=discord.ButtonStyle.danger)
    async def red(self, interaction: discord.Interaction, b: Button): await self.play(interaction, "אדום")
    @discord.ui.button(label="⚫ שחור (x2)", style=discord.ButtonStyle.secondary)
    async def black(self, interaction: discord.Interaction, b: Button): await self.play(interaction, "שחור")
    @discord.ui.button(label="🟢 ירוק 0 (x14)", style=discord.ButtonStyle.success)
    async def green(self, interaction: discord.Interaction, b: Button): await self.play(interaction, "ירוק")


# --- משחק טאואר (Tower) ---
class TowerModal(Modal):
    def __init__(self):
        super().__init__(title="🗼 טאואר - הימור")
        self.bet_input = TextInput(label="כמות טוקנים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.bet_input.value)
        except ValueError: return
        if not remove_tokens(interaction.user.id, bet):
            await interaction.response.send_message("❌ אין לך מספיק טוקנים!", ephemeral=True)
            return

        tower_data = [random.randint(0, 2) for _ in range(5)]
        embed = discord.Embed(title="🗼 מגדל הטאואר - קומה 1", description=f"הימור: **{bet}** טוקנים.\nבחר משבצת בטוחה כדי לטפס!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=TowerView(tower_data, 0, bet, interaction.user.id), ephemeral=True)

class TowerView(View):
    multipliers = [1.3, 1.8, 2.5, 3.8, 5.5]
    def __init__(self, tower_data, floor, bet, user_id):
        super().__init__(timeout=90)
        self.tower_data, self.floor, self.bet, self.user_id = tower_data, floor, bet, user_id
        for i in range(3): self.add_item(TowerButton(i))
        if self.floor > 0: self.add_item(TowerCashout())

class TowerButton(Button):
    def __init__(self, index):
        super().__init__(label=f"❓ תא {index+1}", style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        if interaction.user.id != view.user_id: return

        if self.index == view.tower_data[view.floor]:
            embed = discord.Embed(title="💥 נפסלת! פגעת במלכודת!", description=f"הפסדת {view.bet} טוקנים.", color=discord.Color.red())
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        view.floor += 1
        if view.floor == 5:
            winnings = int(view.bet * 5.5)
            add_tokens(view.user_id, winnings)
            embed = discord.Embed(title="🏆 ניצחון מוחלט! כבשת את הטאואר!", description=f"זכית ב-**{winnings}** טוקנים!", color=discord.Color.gold())
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        embed = discord.Embed(title=f"🗼 מגדל הטאואר - קומה {view.floor + 1}", description=f"מכפיל נוכחי: **{view.multipliers[view.floor-1]}x**", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=TowerView(view.tower_data, view.floor, view.bet, view.user_id))

class TowerCashout(Button):
    def __init__(self): super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.gold, row=1)
    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        winnings = int(view.bet * view.multipliers[view.floor - 1])
        add_tokens(view.user_id, winnings)
        embed = discord.Embed(title="💰 פרשת בבטחה!", description=f"זכת ב-**{winnings}** טוקנים!", color=discord.Color.green())
        for child in view.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)


# --- משחק פוקר וידאו (Video Poker) ---
class PokerModal(Modal):
    def __init__(self):
        super().__init__(title="👑 פוקר וידאו - הימור")
        self.bet_input = TextInput(label="כמות טוקנים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        try: bet = int(self.bet_input.value)
        except ValueError: return
        if not remove_tokens(interaction.user.id, bet):
            await interaction.response.send_message("❌ אין לך מספיק טוקנים!", ephemeral=True)
            return

        suits, ranks = ['♥️', '♦️', '♣️', '♠️'], ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{r}{s}" for r in ranks for s in suits]
        random.shuffle(deck)
        player_hand = [deck.pop() for _ in range(5)]

        embed = discord.Embed(title="👑 שולחן הפוקר", description=f"היד שלך:\n`{ ' | '.join(player_hand) }` \n\nסמן קלפים שתרצה להחזיק ולחץ 'החלף קלפים':", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=PokerView(player_hand, deck, bet, interaction.user.id), ephemeral=True)

def evaluate_poker_hand(hand):
    ranks = [card[:-2] for card in hand]
    rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    values = sorted([rank_values[r] for r in ranks])
    from collections import Counter
    count_values = sorted(Counter(values).values(), reverse=True)
    if count_values ==: return "רביעייה (Four of a Kind)", 10
    if count_values ==: return "פול האוס (Full House)", 7
    if count_values ==: return "שלשה (Three of a Kind)", 3
    if count_values ==: return "זוגיים (Two Pair)", 2
    return "ללא שילוב חזק", 0

class PokerView(View):
    def __init__(self, player_hand, deck, bet, user_id):
        super().__init__(timeout=90)
        self.player_hand, self.deck, self.bet, self.user_id = player_hand, deck, bet, user_id
        self.holds = set()
        for i in range(5): self.add_item(PokerHoldButton(i))
        self.add_item(PokerDrawButton())

class PokerHoldButton(Button):
    def __init__(self, index):
        super().__init__(label=f"קלף {index+1}", style=discord.ButtonStyle.secondary, row=0)
        self.index = index
    async def callback(self, interaction: discord.Interaction):
        view: PokerView = self.view
        if self.index in view.holds:
            view.holds.remove(self.index)
            self.style, self.label = discord.ButtonStyle.secondary, f"קלף {self.index+1}"
        else:
            view.holds.add(self.index)
            self.style, self.label = discord.ButtonStyle.success, f"🔒 קלף {self.index+1}"
        await interaction.response.edit_message(view=view)

class PokerDrawButton(Button):
    def __init__(self): super().__init__(label="🃏 החלף וסיים סיבוב", style=discord.ButtonStyle.primary, row=1)
    async def callback(self, interaction: discord.Interaction):
        view: PokerView = self.view
        if interaction.user.id != view.user_id: return
        final_hand = [view.player_hand[i] if i in view.holds else view.deck.pop() for i in range(5)]
        name, mult = evaluate_poker_hand(final_hand)
        winnings = int(view.bet * mult)
        add_tokens(view.user_id, winnings)
        
        embed = discord.Embed(title="👑 תוצאות פוקר", description=f"היד הסופית:\n`{ ' | '.join(final_hand) }` \n\n📊 שילוב: {name}", color=discord.Color.green() if winnings > 0 else discord.Color.red())
        embed.set_footer(text=f"זכת ב-{winnings} טוקנים!" if winnings > 0 else f"הפסדת {view.bet} טוקנים.")
        for child in view.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)
# ==================== 6. PUBLIC LOBBY VIEW & SLASH COMMANDS ====================

class PublicGamesView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary, custom_id="lobby_bj")
    async def bj(self, interaction: discord.Interaction, b: Button): 
        await interaction.response.send_modal(BlackjackModal())

    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary, custom_id="lobby_tw")
    async def tw(self, interaction: discord.Interaction, b: Button): 
        await interaction.response.send_modal(TowerModal())

    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary, custom_id="lobby_mn")
    async def mn(self, interaction: discord.Interaction, b: Button): 
        await interaction.response.send_modal(MinesModal())

    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary, custom_id="lobby_rl")
    async def rl(self, interaction: discord.Interaction, b: Button): 
        await interaction.response.send_modal(RouletteModal())

    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary, custom_id="lobby_pk")
    async def pk(self, interaction: discord.Interaction, b: Button): 
        await interaction.response.send_modal(PokerModal())


# --- פקודות סלאש ---

@bot.tree.command(name="פאנל_אזולאי", description="לוח בקרה סודי ומורחב רק בשבילך")
async def panel_azoulai(interaction: discord.Interaction):
    if not await security_check(interaction): return
    embed = discord.Embed(title="👑 פאנל אזולאי - Ticket Royale", description="מערכת ניהול בלעדית:", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=AzoulaiAdminView(), ephemeral=True)

@bot.tree.command(name="פאנל", description="הצגת לוח משחקי הקזינו לחברי השרת")
async def panel_public(interaction: discord.Interaction):
    if not await security_check(interaction): return
    embed = discord.Embed(
        title="🎰 קזינו Ticket Royale - פאנל משחקים", 
        description="כל המשחקים פעילים! לחצו למטה כדי להמר ולשחק:", 
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=PublicGamesView(), ephemeral=False)

@bot.tree.command(name="דיילי", description="קבל 20 טוקנים חינם בכל 24 שעות")
async def daily(interaction: discord.Interaction):
    user_id = interaction.user.id
    now = datetime.now()
    
    if user_id in daily_cooldown:
        next_claim = daily_cooldown[user_id] + timedelta(hours=24)
        if now < next_claim:
            time_left = next_claim - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            await interaction.response.send_message(f"❌ כבר אספת את הדיילי שלך היום! תוכל לאסוף שוב בעוד {hours} שעות ו-{minutes} דקות.", ephemeral=True)
            return

    add_tokens(user_id, 20)
    daily_cooldown[user_id] = now
    await interaction.response.send_message(f"🪙 קיבלת **20 טוקנים**! המאזן הנוכחי שלך: **{get_tokens(user_id)}** טוקנים.")


# ==================== 7. BOT BOT STARTUP BLOCK ====================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"הבוט מחובר בהצלחה בתור {bot.user}")

# הפעלת שרת ה-Keep Alive עבור UptimeRobot
keep_alive()

TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    # אם אתה מריץ מקומית, הדבק את הטוקן בתוך הגרשיים
    bot.run("הטוקן_הסודי_שלך_כאן")
