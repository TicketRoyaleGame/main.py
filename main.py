import random

# פונקציה פשוטה לחישוב ערך היד בבלאק ג'ק
def calculate_hand(hand):
    value = 0
    aces = 0
    for card in hand:
        if card in ['J', 'Q', 'K']:
            value += 10
        elif card == 'A':
            aces += 1
            value += 11
        else:
            value += int(card)
    while value > 21 and aces:
        value -= 10
        aces -= 1
    return value

# חלון קופץ לבחירת סכום ההימור בבלאק ג'ק
class BlackjackBetModal(discord.ui.Modal, title="🃏 הימור בלאק ג'ק"):
    bet_input = discord.ui.TextInput(label="כמה טוקנים תרצה להמר?", placeholder="לדוגמה: 5", min_length=1, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ חובה להזין מספר שלם ותקין!", ephemeral=True)
            return

        # בדיקה אם יש למשתמש מספיק טוקנים
        current_tokens = user_tokens.get(user_id, 0)
        if bet > current_tokens:
            await interaction.response.send_message(f"❌ אין לך מספיק טוקנים! יש לך כרגע **{current_tokens}** טוקנים. השתמש ב-/דיילי", ephemeral=True)
            return
        if bet <= 0:
            await interaction.response.send_message("❌ סכום ההימור חייב להיות גדול מ-0!", ephemeral=True)
            return

        # הורדת הטוקנים של ההימור
        user_tokens[user_id] -= bet

        # חלוקת קלפים ראשונית
        deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
        player_hand = [random.choice(deck), random.choice(deck)]
        dealer_hand = [random.choice(deck), random.choice(deck)]

        player_val = calculate_hand(player_hand)
        dealer_val = calculate_hand(dealer_hand)

        embed = discord.Embed(title="🃏 משחק בלאק ג'ק פעיל", color=discord.Color.blue())
        embed.add_field(name="💰 הימור", value=f"**{bet}** טוקנים", inline=False)
        embed.add_field(name="👤 היד שלך", value=f"קלפים: {', '.join(player_hand)} (ערך: **{player_val}**)", inline=True)
        embed.add_field(name="🤖 היד של הדילר", value=f"קלפים: {dealer_hand[0]}, ❓", inline=True)

        # יצירת כפתורי המשחק (עוד קלף / עצור)
        view = BlackjackGameView(player_hand, dealer_hand, deck, bet, user_id)
        await interaction.response.send_message(embed=embed, view=view)
class BlackjackGameView(discord.ui.View):
    def __init__(self, player_hand, dealer_hand, deck, bet, user_id):
        super().__init__(timeout=60)
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck
        self.bet = bet
        self.user_id = user_id

    @discord.ui.button(label="🃏 עוד קלף (Hit)", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        self.player_hand.append(random.choice(self.deck))
        player_val = calculate_hand(self.player_hand)

        if player_val > 21:
            embed = discord.Embed(title="💥 הפסדת! עברת את 21", color=discord.Color.red())
            embed.add_field(name="👤 היד שלך", value=f"{', '.join(self.player_hand)} (ערך: **{player_val}**)", inline=True)
            embed.add_field(name="🤖 היד של הדילר", value=f"{', '.join(self.dealer_hand)} (ערך: **{calculate_hand(self.dealer_hand)}**)", inline=True)
            embed.set_footer(text=f"הפסדת {self.bet} טוקנים.")
            # מנטרל כפתורים בסיום
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=self)
            return

        embed = discord.Embed(title="🃏 משחק בלאק ג'ק פעיל", color=discord.Color.blue())
        embed.add_field(name="👤 היד שלך", value=f"{', '.join(self.player_hand)} (ערך: **{player_val}**)", inline=True)
        embed.add_field(name="🤖 היד של הדילר", value=f"{self.dealer_hand[0]}, ❓", inline=True)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛑 עצור (Stand)", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        player_val = calculate_hand(self.player_hand)
        dealer_val = calculate_hand(self.dealer_hand)

        # הדילר מושך קלפים עד שהוא מגיע ל-17 לפחות
        while dealer_val < 17:
            self.dealer_hand.append(random.choice(self.deck))
            dealer_val = calculate_hand(self.dealer_hand)

        embed = discord.Embed(title="🏁 תוצאות המשחק", zip=True)
        
        if dealer_val > 21 or player_val > dealer_val:
            embed.title = "🎉 ניצחת את הקזינו!"
            embed.color = discord.Color.green()
            winnings = self.bet * 2
            user_tokens[self.user_id] = user_tokens.get(self.user_id, 0) + winnings
            embed.set_footer(text=f"זכית ב-{winnings} טוקנים!")
        elif player_val < dealer_val:
            embed.title = "❌ הדילר ניצח!"
            embed.color = discord.Color.red()
            embed.set_footer(text=f"הפסדת {self.bet} טוקנים.")
        else:
            embed.title = "🤝 תיקו (Push)!"
            embed.color = discord.Color.orange()
            user_tokens[self.user_id] = user_tokens.get(self.user_id, 0) + self.bet
            embed.set_footer(text="הטוקנים שלך הוחזרו אליך.")

        embed.add_field(name="👤 היד שלך", value=f"{', '.join(self.player_hand)} (ערך: **{player_val}**)", inline=True)
        embed.add_field(name="🤖 היד של הדילר", value=f"{', '.join(self.dealer_hand)} (ערך: **{dealer_val}**)", inline=True)

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
# חלון קופץ להזנת משתמש לניהול בפאנל אזולאי
class AzoulaiActionModal(discord.ui.Modal):
    def __init__(self, action_type):
        super().__init__(title=f"👑 ביצוע פעולת ניהול: {action_type}")
        self.action_type = action_type
        self.user_input = discord.ui.TextInput(label="הזן שם משתמש או מזהה (ID)", placeholder="לדוגמה: 1260675229626273802", min_length=2)
        self.add_item(self.user_input)
        
        if "טוקנים" in action_type:
            self.amount_input = discord.ui.TextInput(label="כמות טוקנים", placeholder="לדוגמה: 50", min_length=1)
            self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        target = self.user_input.value
        
        if "טוקנים" in self.action_type:
            amount = self.amount_input.value
            await interaction.response.send_message(f"✅ הפעולה בוצעה: הוחל על `{target}` שינוי של `{amount}` טוקנים בהצלחה!", ephemeral=True)
        else:
            await interaction.response.send_message(f"✅ הפעולה `{self.action_type}` הוחלה על המשתמש `{target}` בהצלחה!", ephemeral=True)
    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary, custom_id="game_bj")
    async def bj_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        # במקום הודעת טקסט - פותח את חלון הזנת ההימור!
        await interaction.response.send_modal(BlackjackBetModal())
# בתוך ModerationView:
    @discord.ui.button(label="🔨 תן באן (יום)", style=discord.ButtonStyle.danger, custom_id="btn_ban")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AzoulaiActionModal("חסימה (Ban)"))

# בתוך TokenManagementView:
    @discord.ui.button(label="➕ הוסף טוקנים", style=discord.ButtonStyle.success, custom_id="btn_add_tokens")
    async def add_tokens(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AzoulaiActionModal("הוספת טוקנים"))
# חלון קופץ להזנת הימור וכמות פצצות במשחק מיין (Mines)
class MinesBetModal(discord.ui.Modal, title="💣 משחק מכרות (Mines)"):
    bet_input = discord.ui.TextInput(label="כמה טוקנים תרצה להמר?", placeholder="לדוגמה: 10", min_length=1, max_length=5)
    bombs_input = discord.ui.TextInput(label="כמה פצצות לשים על הלוח? (בין 1 ל-24)", placeholder="לדוגמה: 3", min_length=1, max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        # 1. בדיקת תקינות הקלטים
        try:
            bet = int(self.bet_input.value)
            bombs_count = int(self.bombs_input.value)
        except ValueError:
            await interaction.response.send_message("❌ חובה להזין מספרים שלמים בלבד!", ephemeral=True)
            return

        if bombs_count < 1 or bombs_count > 24:
            await interaction.response.send_message("❌ כמות הפצצות חייבת להיות בין 1 ל-24!", ephemeral=True)
            return

        current_tokens = user_tokens.get(user_id, 0)
        if bet > current_tokens:
            await interaction.response.send_message(f"❌ אין לך מספיק טוקנים! יש לך {current_tokens} טוקנים כרגע.", ephemeral=True)
            return
        if bet <= 0:
            await interaction.response.send_message("❌ סכום ההימור חייב להיות גדול מ-0!", ephemeral=True)
            return

        # 2. הורדת הטוקנים של ההימור מהשחקן
        user_tokens[user_id] -= bet

        # 3. יצירת לוח משחק סודי (25 משבצות: 0 = יהלום, 1 = פצצה)
        grid = [0] * 25
        bomb_positions = random.sample(range(25), bombs_count)
        for pos in bomb_positions:
            grid[pos] = 1

        # 4. פתיחת הלוח האינטראקטיבי לשחקן
        embed = discord.Embed(
            title="💣 משחק מכרות פעיל - Ticket Royale",
            description=f"הימור: **{bet}** טוקנים | פצצות על הלוח: **{bombs_count}**\nלחץ על המשבצות למטה כדי לחשוף יהלומים! לחץ על 'משוך כסף' בכל שלב כדי לזכות.",
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="📈 מכפיל נוכחי", value="**1.00x**", inline=True)
        embed.add_field(name="💎 יהלומים שנחשפו", value="**0**", inline=True)

        view = MinesGameView(grid, bombs_count, bet, user_id)
        await interaction.response.send_message(embed=embed, view=view)
# כפתור בודד בלוח המכרות
class MinesButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(label="❓", style=discord.ButtonStyle.secondary, row=index // 5)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: MinesGameView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        # אם המשבצת כבר נחשפה
        if self.label != "❓":
            await interaction.response.send_message("❌ משבצת זו כבר נחשפה!", ephemeral=True)
            return

        # בדיקה אם השחקן פגע בפצצה (1 = פצצה, 0 = יהלום)
        if view.grid[self.index] == 1:
            # פיצוץ! השחקן הפסיד
            self.label = "💥"
            self.style = discord.ButtonStyle.danger
            view.reveal_all_bombs()
            
            embed = discord.Embed(
                title="💥 בום! פגעת בפצצה!",
                description=f"הפסדת **{view.bet}** טוקנים. מוטב להתרכז בסיבוב הבא!",
                color=discord.Color.red()
            )
            await view.disable_game(interaction, embed)
            return
        
        # השחקן מצא יהלום!
        self.label = "💎"
        self.style = discord.ButtonStyle.success
        view.diamonds_found += 1
        
        # חישוב מכפיל מתמטי פשוט מבוסס סיכויים
        total_slots = 25
        remaining_slots = total_slots - view.diamonds_found
        remaining_bombs = view.bombs_count
        
        # נוסחת מכפיל בסיסית שמטפסת ככל שיש יותר פצצות ופחות משבצות
        multiplier = 1.0
        for i in range(view.diamonds_found):
            multiplier *= (total_slots - i) / (total_slots - view.bombs_count - i)
        
        view.current_multiplier = round(multiplier, 2)
        
        # עדכון הסטטוס ב-Embed
        embed = discord.Embed(
            title="💣 משחק מכרות פעיל - Ticket Royale",
            description=f"הימור: **{view.bet}** טוקנים | פצצות על הלוח: **{view.bombs_count}**\nהמשך לחשוף או לחץ על '💰 משוך כסף' כדי לקחת את הזכייה!",
            color=discord.Color.dark_purple()
        )
        embed.add_field(name="📈 מכפיל נוכחי", value=f"**{view.current_multiplier}x**", inline=True)
        embed.add_field(name="💎 יהלומים שנחשפו", value=f"**{view.diamonds_found}**", inline=True)
        
        # בדיקה אם השחקן ניקה את כל הלוח מיהלומים!
        if view.diamonds_found == (25 - view.bombs_count):
            winnings = int(view.bet * view.current_multiplier)
            user_tokens[view.user_id] = user_tokens.get(view.user_id, 0) + winnings
            view.reveal_all_bombs()
            embed.title = "🏆 ניצחון מוחלט! ניקית את הלוח!"
            embed.color = discord.Color.gold()
            embed.set_footer(text=f"זכית ב-{winnings} טוקנים!")
            await view.disable_game(interaction, embed)
            return

        await interaction.response.edit_message(embed=embed, view=view)


# לוח המשחק המלא של המכרות + כפתור משיכה
class MinesGameView(discord.ui.View):
    def __init__(self, grid, bombs_count, bet, user_id):
        super().__init__(timeout=120)
        self.grid = grid
        self.bombs_count = bombs_count
        self.bet = bet
        self.user_id = user_id
        self.diamonds_found = 0
        self.current_multiplier = 1.0

        # יצירת 25 כפתורי משבצות ללוח
        for i in range(25):
            self.add_item(MinesButton(i))

    def reveal_all_bombs(self):
        for child in self.children:
            if isinstance(child, MinesButton):
                if self.grid[child.index] == 1:
                    child.label = "💣"
                    child.style = discord.ButtonStyle.danger
                elif child.label == "❓":
                    child.label = "💎"
                    child.style = discord.ButtonStyle.secondary

    async def disable_game(self, interaction: discord.Interaction, embed):
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    # כפתור פרישה ולקיחת הכסף
    @discord.ui.button(label="💰 משוך כסף (Cashout)", style=discord.ButtonStyle.gold, row=4)
    async def cashout(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        if self.diamonds_found == 0:
            await interaction.response.send_message("❌ אתה חייב לחשוף לפחות יהלום אחד לפני משיכת הכסף!", ephemeral=True)
            return

        winnings = int(self.bet * self.current_multiplier)
        user_tokens[self.user_id] = user_tokens.get(self.user_id, 0) + winnings
        self.reveal_all_bombs()

        embed = discord.Embed(
            title="💰 משיכת כסף מוצלחת!",
            description=f"פרשת בזמן עם מכפיל של **{self.current_multiplier}x**.\nהמאזן החדש שלך: **{user_tokens[self.user_id]}** טוקנים.",
            color=discord.Color.green()
        )
        embed.add_field(name="💎 יהלומים שמצאת", value=str(self.diamonds_found), inline=True)
        embed.add_field(name="💵 סך הכל רווח", value=f"**{winnings}** טוקנים", inline=True)

        await self.disable_game(interaction, embed)
    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary, custom_id="game_mines")
    async def mines_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        # מפעיל את חלון הזנת ההימור וכמות הפצצות!
        await interaction.response.send_modal(MinesBetModal())

# חלון קופץ להזנת הימור ברולטה
class RouletteBetModal(discord.ui.Modal, title="🎰 הימור רולטה"):
    bet_input = discord.ui.TextInput(label="כמה טוקנים תרצה להמר?", placeholder="לדוגמה: 20", min_length=1, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ חובה להזין מספר שלם ותקין!", ephemeral=True)
            return

        current_tokens = user_tokens.get(user_id, 0)
        if bet > current_tokens or bet <= 0:
            await interaction.response.send_message("❌ סכום הימור לא תקין או שאין לך מספיק טוקנים!", ephemeral=True)
            return

        user_tokens[user_id] -= bet

        embed = discord.Embed(
            title="🎰 שולחן הרולטה - Ticket Royale",
            description=f"הימור: **{bet}** טוקנים.\n\nבחר את סוג ההימור שלך באמצעות הכפתורים למטה:",
            color=discord.Color.purple()
        )
        view = RouletteGameView(bet, user_id)
        await interaction.response.send_message(embed=embed, view=view)

# כפתורי בחירת ההימור ברולטה והרצה
class RouletteGameView(discord.ui.View):
    def __init__(self, bet, user_id):
        super().__init__(timeout=60)
        self.bet = bet
        self.user_id = user_id

    async def spin_wheel(self, interaction: discord.Interaction, player_choice):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        # הגרלת מספר רולטה (0-36) וצבע
        number = random.randint(0, 36)
        if number == 0:
            color = "ירוק"
            emoji = "🟢"
        elif number in:
            color = "אדום"
            emoji = "🔴"
        else:
            color = "שחור"
            emoji = "⚫"

        is_win = False
        payout = 0

        if player_choice == color:
            is_win = True
            if color == "ירוק":
                payout = self.bet * 14
            else:
                payout = self.bet * 2

        embed = discord.Embed(title="🎰 הגלגל מסתובב...", color=discord.Color.gold())
        embed.description = f"הכדור נחת על: {emoji} **{number} ({color})**\n\n"

        if is_win:
            user_tokens[self.user_id] = user_tokens.get(self.user_id, 0) + payout
            embed.title = "🎉 זכייה ברולטה!"
            embed.color = discord.Color.green()
            embed.description += f"כל הכבוד! הימרת על **{player_choice}** וזכית ב-**{payout}** טוקנים!"
        else:
            embed.title = "❌ הפסדת ברולטה"
            embed.color = discord.Color.red()
            embed.description += f"חבל! הימרת על **{player_choice}** אבל יצא {color}. הפסדת {self.bet} טוקנים."

        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔴 אדום (x2)", style=discord.ButtonStyle.danger)
    async def red_choice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spin_wheel(interaction, "אדום")

    @discord.ui.button(label="⚫ שחור (x2)", style=discord.ButtonStyle.secondary)
    async def black_choice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spin_wheel(interaction, "שחור")

    @discord.ui.button(label="🟢 ירוק 0 (x14)", style=discord.ButtonStyle.success)
    async def green_choice(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.spin_wheel(interaction, "ירוק")
# חלון קופץ להזנת הימור בטאואר
class TowerBetModal(discord.ui.Modal, title="🗼 משחק טאואר (Tower)"):
    bet_input = discord.ui.TextInput(label="כמה טוקנים תרצה להמר?", placeholder="לדוגמה: 15", min_length=1, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ מספר לא תקין!", ephemeral=True)
            return

        current_tokens = user_tokens.get(user_id, 0)
        if bet > current_tokens or bet <= 0:
            await interaction.response.send_message("❌ אין לך מספיק טוקנים!", ephemeral=True)
            return

        user_tokens[user_id] -= bet

        # הגדרת המגדל: 5 קומות, בכל קומה מספר בין 0 ל-2 הוא המלכודת
        tower_data = [random.randint(0, 2) for _ in range(5)]
        
        embed = discord.Embed(
            title="🗼 מגדל הטאואר - קומה 1",
            description=f"הימור: **{bet}** טוקנים | מכפיל נוכחי: **1.00x**\nבחר את אחת משלוש המשבצות למטה כדי לטפס לקומה הבאה!",
            color=discord.Color.blue()
        )
        
        view = TowerGameView(tower_data, 0, bet, user_id)
        await interaction.response.send_message(embed=embed, view=view)

# ניהול קומות וכפתורים בטאואר
class TowerGameView(discord.ui.View):
    multipliers = [1.3, 1.8, 2.5, 3.8, 5.5] # מכפיל לכל קומה שמושלמת

    def __init__(self, tower_data, current_floor, bet, user_id):
        super().__init__(timeout=90)
        self.tower_data = tower_data
        self.current_floor = current_floor
        self.bet = bet
        self.user_id = user_id
        
        # יצירת 3 כפתורים לקומה הנוכחית
        for i in range(3):
            self.add_item(TowerFloorButton(i))
            
        # הוספת כפתור משוך כסף אם הוא עבר לפחות קומה אחת
        if self.current_floor > 0:
            self.add_item(TowerCashoutButton())

class TowerFloorButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(label=f"❓ משבצת {index+1}", style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: TowerGameView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        # בדיקה אם פגע במלכודת
        trap_index = view.tower_data[view.current_floor]
        if self.index == trap_index:
            # הפסד!
            embed = discord.Embed(
                title="💥 המגדל קרס! פגעת במלכודת!",
                description=f"נפסלת בקומה **{view.current_floor + 1}**. הפסדת **{view.bet}** טוקנים.",
                color=discord.Color.red()
            )
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        # הצלחה! עובר קומה
        view.current_floor += 1
        current_mult = view.multipliers[view.current_floor - 1]

        if view.current_floor == 5:
            # ניצחון מוחלט בסיום כל הקומות!
            winnings = int(view.bet * 5.5)
            user_tokens[view.user_id] = user_tokens.get(view.user_id, 0) + winnings
            embed = discord.Embed(
                title="🏆 ניצחון מושלם! כבשת את הטאואר!",
                description=f"הגעת לקומה האחרונה! זכית במכפיל מקסימלי של **5.50x**.\n\n💵 סך הכל זכייה: **{winnings}** טוקנים!",
                color=discord.Color.gold()
            )
            for child in view.children:
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        # מעבר לקומה הבאה - יצירת View חדש לקומה החדשה
        next_mult = view.multipliers[view.current_floor]
        embed = discord.Embed(
            title=f"🗼 מגדל הטאואר - קומה {view.current_floor + 1}",
            description=f"עלית בהצלחה! מכפיל נוכחי: **{current_mult}x**\nהקומה הבאה שווה מכפיל של **{next_mult}x**!\n\nבחר משבצת או משוך את הכסף הנוכחי שלך:",
            color=discord.Color.blue()
        )
        next_view = TowerGameView(view.tower_data, view.current_floor, view.bet, view.user_id)
        await interaction.response.edit_message(embed=embed, view=next_view)

class TowerCashoutButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.gold, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: TowerGameView = self.view
        if interaction.user.id != view.user_id:
            return

        current_mult = view.multipliers[view.current_floor - 1]
        winnings = int(view.bet * current_mult)
        user_tokens[view.user_id] = user_tokens.get(view.user_id, 0) + winnings

        embed = discord.Embed(
            title="💰 משיכת כסף מושלמת מהטאואר!",
            description=f"פרשת בקומה **{view.current_floor}** עם מכפיל של **{current_mult}x**.\n\n💵 סך הכל רווח: **{winnings}** טוקנים!",
            color=discord.Color.green()
        )
        for child in view.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary, custom_id="game_tower")
    async def tower_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TowerBetModal())

    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary, custom_id="game_roulette")
    async def roulette_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RouletteBetModal())
# חלון קופץ לבחירת סכום ההימור בפוקר
class PokerBetModal(discord.ui.Modal, title="👑 הימור פוקר (Video Poker)"):
    bet_input = discord.ui.TextInput(label="כמה טוקנים תרצה להמר?", placeholder="לדוגמה: 25", min_length=1, max_length=5)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ חובה להזין מספר שלם ותקין!", ephemeral=True)
            return

        current_tokens = user_tokens.get(user_id, 0)
        if bet > current_tokens or bet <= 0:
            await interaction.response.send_message("❌ אין לך מספיק טוקנים או שסכום ההימור לא תקין!", ephemeral=True)
            return

        user_tokens[user_id] -= bet

        # יצירת חפיסת קלפים מלאה (מספר + צורה)
        suits = ['♥️', '♦️', '♣️', '♠️']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{rank}{suit}" for rank in ranks for suit in suits]
        random.shuffle(deck)

        # חלוקת 5 קלפים ראשונים לשחקן
        player_hand = [deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop()]

        embed = discord.Embed(
            title="👑 שולחן הפוקר - Ticket Royale",
            description=f"הימור: **{bet}** טוקנים.\n\n**היד הנוכחית שלך:**\n{ ' | '.join(player_hand) }\n\nלחץ על כפתורי המספרים למטה כדי לבחור אילו קלפים **להחזיק (Hold)**, ואז לחץ על 'החלף קלפים'!",
            color=discord.Color.gold()
        )

        view = PokerGameView(player_hand, deck, bet, user_id)
        await interaction.response.send_message(embed=embed, view=view)

# פונקציית עזר לבדיקת חוזק היד בפוקר וחישוב המכפיל
def evaluate_poker_hand(hand):
    ranks = [card[:-2] for card in hand]
    suits = [card[-2:] for card in hand]
    
    # המרת נסיך, מלכה, מלך, אס למספרים בשביל מיון תקין
    rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    values = sorted([rank_values[r] for r in ranks])
    
    # ספירת חזרות של קלפים
    from collections import Counter
    counts = Counter(values)
    count_values = sorted(counts.values(), reverse=True)
    
    is_flush = len(set(suits)) == 1
    is_straight = len(set(values)) == 5 and (values[-1] - values[0] == 4)

    # בדיקת שילובים מהחזק לחלש
    if is_flush and is_straight and values[-1] == 14:
        return "רויל פלאש (Royal Flush) 👑", 50
    if is_flush and is_straight:
        return "סטרייט פלאש (Straight Flush) 📜", 20
    if count_values ==:
        return "רביעייה (Four of a Kind) 💎", 10
    if count_values ==:
        return "פול האוס (Full House) 🏠", 7
    if is_flush:
        return "פלאש (Flush) 🎨", 5
    if is_straight:
        return "סטרייט (Straight) 📏", 4
    if count_values ==:
        return "שלשה (Three of a Kind) 🥉", 3
    if count_values ==:
        return "זוגיים (Two Pair) 👥", 2
    if count_values ==:
        # בדיקה אם זה זוג גבוה (נסיך ומעלה) בשביל לקבל החזר
        pair_rank = [k for k, v in counts.items() if v == 2][0]
        if pair_rank >= 11:
            return "זוג גבוה (Jacks or Better) 🃏", 1
    return "ללא שילוב (High Card) 💨", 0
class PokerGameView(discord.ui.View):
    def __init__(self, player_hand, deck, bet, user_id):
        super().__init__(timeout=90)
        self.player_hand = player_hand
        self.deck = deck
        self.bet = bet
        self.user_id = user_id
        # רשימה לשמירת המיקומים של הקלפים שהשחקן רוצה להחזיק (0 עד 4)
        self.holds = set()

        # הוספת כפתורי החזקה ל-5 הקלפים
        for i in range(5):
            self.add_item(PokerHoldButton(i))
        # הוספת כפתור ההחלפה הסופי
        self.add_item(PokerDrawButton())

class PokerHoldButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(label=f"קלף {index+1}", style=discord.ButtonStyle.secondary, row=0)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: PokerGameView = self.view
        if interaction.user.id != view.user_id:
            return

        # שינוי מצב כפתור: אם לא מוחזק - נהפוך למוחזק (ירוק), ולהפך
        if self.index in view.holds:
            view.holds.remove(self.index)
            self.style = discord.ButtonStyle.secondary
            self.label = f"קלף {self.index+1}"
        else:
            view.holds.add(self.index)
            self.style = discord.ButtonStyle.success
            self.label = f"🔒 קלף {self.index+1}"

        await interaction.response.edit_message(view=view)

class PokerDrawButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🃏 החלף קלפים וסיים סיבוב", style=discord.ButtonStyle.primary, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: PokerGameView = self.view
        if interaction.user.id != view.user_id:
            await interaction.response.send_message("❌ זה לא המשחק שלך!", ephemeral=True)
            return

        # החלפת כל הקלפים שהשחקן לא סימן עליהם Hold (לא שמר אותם)
        final_hand = []
        for i in range(5):
            if i in view.holds:
                final_hand.append(view.player_hand[i])
            else:
                final_hand.append(view.deck.pop())

        # בדיקת השילוב הסופי שיוצא לשחקן
        combination_name, multiplier = evaluate_poker_hand(final_hand)
        winnings = int(view.bet * multiplier)

        embed = discord.Embed(title="👑 תוצאות משחק הפוקר", color=discord.Color.red())

        if winnings > 0:
            user_tokens[view.user_id] = user_tokens.get(view.user_id, 0) + winnings
            embed.title = "🎉 זכייה בפוקר!"
            embed.color = discord.Color.green()
            embed.set_footer(text=f"השילוב העניק לך מכפיל של {multiplier}x! זכת ב-{winnings} טוקנים.")
        else:
            embed.title = "❌ הפסדת בסיבוב"
            embed.color = discord.Color.red()
            embed.set_footer(text=f"לא יצא שילוב זוכה. הפסדת {view.bet} טוקנים.")

        embed.description = f"**היד הסופית שלך:**\n{ ' | '.join(final_hand) }\n\n📊 **שילוב שהתקבל:** {combination_name}"

        # ניטרול כל הכפתורים בסיום
        for child in view.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary, custom_id="game_poker")
    async def poker_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        # מפעיל את חלון הזנת ההימור של הפוקר!
        await interaction.response.send_modal(PokerBetModal())
bot.run("MTU1...הטוקן האמיתי שלך...")
