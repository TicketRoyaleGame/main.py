import discord
from discord import app_commands
from discord.ext import commands
import random, json, os, math, asyncio
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta, timezone

app = Flask('')
OWNER_ID = 1260675229626273802
DB_FILE = "economy.json"

@app.route('/')
def home(): 
    return "הבוט חי ופעיל 24/7!"

def run_flask(): 
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

def keep_alive(): 
    Thread(target=run_flask).start()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True 
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    if not os.path.exists(DB_FILE): 
        with open(DB_FILE, "w") as f: json.dump({}, f)
    try: 
        with open(DB_FILE, "r") as f: return json.load(f)
    except: 
        return {}

def save_data(data): 
    with open(DB_FILE, "w", encoding="utf-8") as f: 
        json.dump(data, f, indent=4)

def get_user_data(user_id):
    data = load_data()
    uid = str(user_id)
    changed = False
    if uid not in data: 
        data[uid] = {"tickets": 10, "banned_until": None, "last_daily": None}
        changed = True
    if "banned_until" not in data[uid]: 
        data[uid]["banned_until"] = None
        changed = True
    if "last_daily" not in data[uid]:
        data[uid]["last_daily"] = None
        changed = True
    if changed: 
        save_data(data)
    return data[uid]

def update_tickets(user_id, amount):
    data = load_data()
    uid = str(user_id)
    if uid not in data: 
        get_user_data(user_id)
        data = load_data()
    data[uid]["tickets"] += amount
    save_data(data)

def is_user_banned(user_id):
    u = get_user_data(user_id)
    if not u.get("banned_until"): 
        return False
    try:
        now = datetime.now(timezone.utc)
        ban_time = datetime.fromisoformat(u["banned_until"]).replace(tzinfo=timezone.utc)
        if now < ban_time: 
            return True
    except: 
        pass
    data = load_data()
    data[str(user_id)]["banned_until"] = None
    save_data(data)
    return False

@bot.event
async def on_guild_join(guild: discord.Guild):
    data = load_data()
    if "allowed_guilds" not in data:
        data["allowed_guilds"] = []
        save_data(data)

    if guild.id not in data["allowed_guilds"]:
        await guild.leave() 
        owner = await bot.fetch_user(OWNER_ID)
        embed = discord.Embed(
            title="🔒 ניסיון הוספת הבוט לשרת זר! 🔒",
            description=f"משתמש ניסה להוסיף את הבוט לשרת: **{guild.name}**.\nהבוט יצא ומחכה לאישור שלך.",
            color=discord.Color.orange(),
            timestamp=datetime.now(timezone.utc)
        )
        embed.add_field(name="🆔 מזהה שרת:", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👥 חברים:", value=f"{guild.member_count}", inline=True)
        view = GuildRequestView(guild.id, guild.name)
        await owner.send(embed=embed, view=view)

class GuildRequestView(discord.ui.View):
    def __init__(self, guild_id, guild_name):
        super().__init__(timeout=None)
        self.guild_id = guild_id
        self.guild_name = guild_name

    @discord.ui.button(label="✅ אשר שרת", style=discord.ButtonStyle.success)
    async def allow_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        if "allowed_guilds" not in data: data["allowed_guilds"] = []
        if self.guild_id not in data["allowed_guilds"]:
            data["allowed_guilds"].append(self.guild_id)
            save_data(data)
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"✅ השרת **{self.guild_name}** אושר לצמיתות בקובץ הנתונים!", view=self)

    @discord.ui.button(label="❌ חסום שרת", style=discord.ButtonStyle.danger)
    async def deny_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(content=f"❌ דחית את השרת **{self.guild_name}**.", view=self)

async def handle_security_breach(interaction: discord.Interaction, action_attempted: str):
    user = interaction.user
    guild_name = interaction.guild.name if interaction.guild else "הודעה פרטית"
    data = load_data()
    end_time = datetime.now(timezone.utc) + timedelta(days=3650)
    data[str(user.id)]["banned_until"] = end_time.isoformat()
    save_data(data)
    await interaction.response.send_message("🚨 **ניסיון פריצה זוהה!** חשבונך ננעל.", ephemeral=True)
    embed = discord.Embed(
        title="🚨 התרעת אבטחה! 🚨",
        description=f"משתמש ניסה להפעיל את: `{action_attempted}` ונחסם.",
        color=discord.Color.red(),
        timestamp=datetime.now(timezone.utc)
    )
    embed.add_field(name="👤 משתמש:", value=f"{user.name} ({user.mention})", inline=True)
    embed.add_field(name="🌐 שרת:", value=f"**{guild_name}**", inline=True)
    try:
        owner = await bot.fetch_user(OWNER_ID)
        await owner.send(embed=embed)
    except: pass

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if not before.premium_since and after.premium_since:
        boost_reward = 20
        update_tickets(after.id, boost_reward)
        if after.guild.system_channel:
            embed = discord.Embed(title="🚀 תודה על הבוסט! 🚀", description=f"תודה רבה ל-{after.mention} על הבוסט!\nקיבלת בונוס של **{boost_reward}** טיקטים! 🎫💎", color=discord.Color.nitro_pink())
            await after.guild.system_channel.send(embed=embed)
        try: await after.send(f"🔮 **תודה על הבוסט לשרת {after.guild.name}!** קיבלת **{boost_reward}** טיקטים! 🎉")
        except: pass

@bot.event
async def on_ready(): 
    print(f"הבוט התחבר בהצלחה: {bot.user}")
    data = load_data()
    if "allowed_guilds" not in data: data["allowed_guilds"] = []
    for g in bot.guilds:
        if g.id not in data["allowed_guilds"]: data["allowed_guilds"].append(g.id)
    save_data(data)
    await bot.tree.sync()

class CasinoStoreView(discord.ui.View):
    def __init__(self): super().__init__(timeout=60.0)
    @discord.ui.button(label="👑 קנה רול 'V.I.P Casino' (500 🎫)", style=discord.ButtonStyle.success, custom_id="buy_vip")
    async def buy_vip_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        if is_user_banned(interaction.user.id): return
        u = get_user_data(interaction.user.id)
        if u["tickets"] < 500:
            await interaction.response.send_message("❌ אין לך מספיק טיקטים! הרול עולה 500 טיקטים. 🎫", ephemeral=True)
            return
        role_name = "V.I.P Casino"; guild = interaction.guild
        if not guild: return
        role = discord.utils.get(guild.roles, name=role_name)
        if not role:
            try: role = await guild.create_role(name=role_name, color=discord.Color.gold(), reason="חנות קזינו")
            except:
                await interaction.response.send_message("❌ לבוט אין הרשאות ליצור רולים בשרת זה!", ephemeral=True)
                return
        if role in interaction.user.roles:
            await interaction.response.send_message("⚠️ כבר יש לך את הרול הזה בחשבון!", ephemeral=True)
            return
        try:
            await interaction.user.add_roles(role); update_tickets(interaction.user.id, -500)
            await interaction.response.send_message(f"🎉 **תתחדש!** קנית בהצלחה את הרול {role.mention}! 👑", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה בהענקת הרול.", ephemeral=True)

async def show_leaderboard(interaction: discord.Interaction):
    data = load_data(); user_scores = []
    for uid, udata in data.items():
        if uid.isdigit(): user_scores.append((uid, udata.get("tickets", 0)))
    user_scores.sort(key=lambda x: x[1], reverse=True); top_5 = user_scores[:5]
    embed = discord.Embed(title="🏆 טבלת המובילים: עשירי הקזינו! 🏆", description="חמשת השחקנים שהכי שדדו את הבית:\n", color=discord.Color.gold())
    medals = {0: "🥇", 1: "🥈", 2: "🥉", 3: "🏅", 4: "🏅"}
    for idx, (uid, tickets) in enumerate(top_5):
        try: member = await bot.fetch_user(int(uid)); name = member.name
        except: name = f"משתמש זר ({uid})"
        embed.description += f"\n{medals[idx]} **{name}** — `{tickets}` 🎫"
    await interaction.response.send_message(embed=embed, ephemeral=True)

class AdminSetTicketsModal(discord.ui.Modal, title="קביעת יתרה מדויקת"):
    amount_input = discord.ui.TextInput(label="הזן כמות מדויקת:", placeholder="לדוגמה: 13", required=True)
    def __init__(self, target_member): super().__init__(); self.target_member = target_member
    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = max(0, int(self.amount_input.value)); data = load_data(); data[str(self.target_member.id)]["tickets"] = val; save_data(data)
            await interaction.response.send_message(f"👑 עדכנת את היתרה של {self.target_member.mention} ל-**{val}** טיקטים!", ephemeral=True)
        except: await interaction.response.send_message("❌ מספר לא תקין", ephemeral=True)

class AdminBanModal(discord.ui.Modal, title="חסימת משתמש"):
    hours_input = discord.ui.TextInput(label="לכמה שעות לחסום? (0 לצמיתות)", placeholder="לדוגמה: 24", required=True)
    def __init__(self, target_member): super().__init__(); self.target_member = target_member
    async def on_submit(self, interaction: discord.Interaction):
        try:
            hours = int(self.hours_input.value); data = load_data()
            end_time = datetime.now(timezone.utc) + (timedelta(days=3650) if hours == 0 else timedelta(hours=hours))
            data[str(self.target_member.id)]["banned_until"] = end_time.isoformat(); save_data(data)
            await interaction.response.send_message(f"🚫 חסמת את {self.target_member.mention}!", ephemeral=True)
        except: await interaction.response.send_message("❌ שגיאה בהזנת הזמן", ephemeral=True)

class AdminPanelView(discord.ui.View):
    def __init__(self, target_member): super().__init__(timeout=120.0); self.target_member = target_member
    async def update_view(self, interaction):
        u = get_user_data(self.target_member.id); status = "❌ חסום" if is_user_banned(self.target_member.id) else "✅ פעיל"
        await interaction.response.edit_message(content=f"⚙️ **פאנל ניהול: {self.target_member.mention}**\n💳 יתרה: **{u['tickets']}** 🎫\n🚨 סטטוס: **{status}**", view=self)
    @discord.ui.button(label="הוסף 100 🎫", style=discord.ButtonStyle.success, row=0)
    async def add_100(self, interaction, button): update_tickets(self.target_member.id, 100); await self.update_view(interaction)
    @discord.ui.button(label="הורד 100 🎫", style=discord.ButtonStyle.danger, row=0)
    async def remove_100(self, interaction, button):
        update_tickets(self.target_member.id, -100); u = get_user_data(self.target_member.id)
        if u["tickets"] < 0: data = load_data(); data[str(self.target_member.id)]["tickets"] = 0; save_data(data)
        await self.update_view(interaction)
    @discord.ui.button(label="קבע כמות מדויקת / איפוס ✍️", style=discord.ButtonStyle.primary, row=1)
    async def set_exact(self, interaction, button): await interaction.response.send_modal(AdminSetTicketsModal(self.target_member))
    @discord.ui.button(label="🚫 חסום (BAN)", style=discord.ButtonStyle.danger, row=2)
    async def ban_user(self, interaction, button): await interaction.response.send_modal(AdminBanModal(self.target_member))
    @discord.ui.button(label="🔓 שחרר (UNBAN)", style=discord.ButtonStyle.success, row=2)
    async def unban_user(self, interaction, button):
        data = load_data(); data[str(self.target_member.id)]["banned_until"] = None; save_data(data)
        await interaction.response.send_message(f"🔓 שחררת את {self.target_member.mention}!", ephemeral=True)

@bot.tree.command(name="admin_panel", description="פתח פאנל ניהול סודי")
async def admin_panel(interaction: discord.Interaction, member: discord.Member):
    if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "/admin_panel"); return
    u = get_user_data(member.id); status = "❌ חסום" if is_user_banned(member.id) else "✅ פעיל"; view = AdminPanelView(member)
    await interaction.response.send_message(content=f"⚙️ **פאנל ניהול משתמש: {member.mention}**\n💳 יתרה: **{u['tickets']}** 🎫\n🚨 סטטוס: **{status}**", view=view, ephemeral=True)

@bot.tree.command(name="create_code", description="ייצר קוד קופון חדש (לאדמין בלבד)")
@app_commands.describe(code="הקוד", amount="כמות טיקטים", max_uses="כמות אנשים")
async def create_code(interaction: discord.Interaction, code: str, amount: int, max_uses: int):
    if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "/create_code"); return
    if amount <= 0 or max_uses <= 0: await interaction.response.send_message("❌ ערכים לא תקינים!", ephemeral=True); return
    data = load_data()
    if "promo_codes" not in data: data["promo_codes"] = {}
    clean_code = code.upper()
    data["promo_codes"][clean_code] = {"amount": amount, "max_uses": max_uses, "used_by": []}
    save_data(data)
    await interaction.response.send_message(f"👑 **קוד קופון נוצר!**\n🎫 קוד: `{clean_code}`\n💰 פרס: **{amount}** | 👥 שימושים: **{max_uses}**", ephemeral=True)

class PromoModal(discord.ui.Modal, title="🎁 מימוש קוד קופון סודי"):
    code_input = discord.ui.TextInput(label="הזן את קוד הקופון שלך:", placeholder="לדוגמה: CASINO100", required=True)
    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        if "promo_codes" not in data: data["promo_codes"] = {}
        clean_code = self.code_input.value.upper()
        if clean_code not in data["promo_codes"]: await interaction.response.send_message("❌ קוד קופון לא תקין או פג תוקף!", ephemeral=True); return
        promo_info = data["promo_codes"][clean_code]; uid = str(interaction.user.id)
        if uid in promo_info["used_by"]: await interaction.response.send_message("⚠️ כבר מימשת את קוד הקופון הזה בעבר!", ephemeral=True); return
        if len(promo_info["used_by"]) >= promo_info["max_uses"]: await interaction.response.send_message("😭 מאוחר מדי! כל השימושים של הקוד הזה נגמרו!", ephemeral=True); return
        promo_info["used_by"].append(uid); save_data(data); update_tickets(interaction.user.id, promo_info["amount"])
        await interaction.response.send_message(f"🎁 **הקוד מומש בהצלחה!** קיבלת **{promo_info['amount']}** טיקטים לחשבון! 🎉", ephemeral=True)


# ==========================================
#              1. משחק פוקר (Poker)
# ==========================================
class PokerGameView(discord.ui.View):
    def __init__(self, player, bet):
        super().__init__(timeout=60.0)
        self.player = player
        self.bet = bet
        suits = ["♠", "♥", "♦", "♣"]
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        deck = [(v, s) for v in values for s in suits]
        random.shuffle(deck)
        self.hand = [deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop()]

    def evaluate_hand(self):
        values_order = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
        vals = [card[0] for card in self.hand]
        suits = [card[1] for card in self.hand]
        val_counts = {v: vals.count(v) for v in set(vals)}
        counts = sorted(list(val_counts.values()), reverse=True)
        is_flush = len(set(suits)) == 1
        
        numeric_vals = sorted([values_order[v] for v in vals])
        is_straight = numeric_vals == list(range(numeric_vals[0], numeric_vals[0] + 5))
        if not is_straight and numeric_vals == [2, 3, 4, 5, 14]: # A-5 straight
            is_straight = True

        if is_flush and is_straight: return "סטרייט פלאש! 🔥", 20
        if 4 in counts: return "פאר (4 מסוג)! 👑", 10
        if counts == [3, 2]: return "פูล האוס (Full House)! 🌟", 6
        if is_flush: return "פלאש (Flush)! 💎", 5
        if is_straight: return "סטרייט (Straight)! 🚀", 4
        if 3 in counts: return "שלישייה (Three of a Kind)! 🎯", 3
        if counts == [2, 2, 1]: return "שני זוגות! ✌️", 2
        if 2 in counts: return "זוג גבוה! 👍", 1
        return "אין שילוב (הפסד)", 0

    @discord.ui.button(label="🔄 החלף קלפים (Draw)", style=discord.ButtonStyle.primary)
    async def redraw(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        suits = ["♠", "♥", "♦", "♣"]
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        deck = [(v, s) for v in values for s in suits]
        random.shuffle(deck)
        self.hand = [deck.pop(), deck.pop(), deck.pop(), deck.pop(), deck.pop()]
        
        for child in self.children: child.disabled = True
        rank_name, mult = self.evaluate_hand()
        winnings = self.bet * mult
        if winnings > 0: update_tickets(self.player.id, winnings)
        
        cards_str = " ".join([f"`{v}{s}`" for v, s in self.hand])
        embed = discord.Embed(
            title="🃏 תוצאת סופית בפוקר 🃏",
            description=f"הקלפים שלך:\n{cards_str}\n\n🏆 תוצאה: **{rank_name}**\n💰 זכייה: **{winnings}** 🎫",
            color=discord.Color.green() if winnings > 0 else discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


# ==========================================
#              2. משחק בלקג'ק (Blackjack)
# ==========================================
class BlackjackView(discord.ui.View):
    def __init__(self, player, bet):
        super().__init__(timeout=60.0)
        self.player = player
        self.bet = bet
        self.deck = self.create_deck()
        self.player_hand = [self.draw_card(), self.draw_card()]
        self.dealer_hand = [self.draw_card(), self.draw_card()]

    def create_deck(self):
        suits = ["♠", "♥", "♦", "♣"]
        values = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        deck = [(v, s) for v in values for s in suits]
        random.shuffle(deck)
        return deck

    def draw_card(self):
        return self.deck.pop()

    def calculate_score(self, hand):
        score = 0
        aces = 0
        for card in hand:
            v = card[0]
            if v in ["J", "Q", "K"]:
                score += 10
            elif v == "A":
                aces += 1
                score += 11
            else:
                score += int(v)
        while score > 21 and aces > 0:
            score -= 10
            aces -= 1
        return score

    @discord.ui.button(label="📥 קח קלף (Hit)", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        self.player_hand.append(self.draw_card())
        p_score = self.calculate_score(self.player_hand)
        
        if p_score > 21:
            for child in self.children: child.disabled = True
            p_cards = " ".join([f"`{v}{s}`" for v, s in self.player_hand])
            embed = discord.Embed(title="💥 התפוצצת בבלקג'ק! (Bust) 💥", description=f"הקלפים שלך: {p_cards} (סכום: {p_score})\n😭 הפסדת **{self.bet}** טיקטים.", color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        else:
            p_cards = " ".join([f"`{v}{s}`" for v, s in self.player_hand])
            embed = discord.Embed(title="🃏 שולחן בלקג'ק 🃏", description=f"הקלפים שלך: {p_cards} (סכום: **{p_score}**)\nקלף גלוי של הדילר: `{self.dealer_hand[0][0]}{self.dealer_hand[0][1]}`", color=discord.Color.blue())
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🛑 הישאר (Stand)", style=discord.ButtonStyle.success)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        for child in self.children: child.disabled = True
        
        p_score = self.calculate_score(self.player_hand)
        d_score = self.calculate_score(self.dealer_hand)
        while d_score < 17:
            self.dealer_hand.append(self.draw_card())
            d_score = self.calculate_score(self.dealer_hand)

        p_cards = " ".join([f"`{v}{s}`" for v, s in self.player_hand])
        d_cards = " ".join([f"`{v}{s}`" for v, s in self.dealer_hand])

        if d_score > 21 or p_score > d_score:
            winnings = self.bet * 2
            update_tickets(self.player.id, winnings)
            embed = discord.Embed(title="🎉 ניצחת בבלקג'ק! 🎉", description=f"הקלפים שלך: {p_cards} (**{p_score}**)\nקלפי הדילר: {d_cards} (**{d_score}**)\n\n🏆 זכית ב-**{winnings}** טיקטים!", color=discord.Color.green())
        elif p_score == d_score:
            update_tickets(self.player.id, self.bet)
            embed = discord.Embed(title="🤝 תיקו בבלקג'ק! 🤝", description=f"הקלפים שלך: {p_cards} (**{p_score}**)\nקלפי הדילר: {d_cards} (**{d_score}**)\n\nההימור הוחזר אליך.", color=discord.Color.orange())
        else:
            embed = discord.Embed(title="😢 הדילר ניצח! 😢", description=f"הקלפים שלך: {p_cards} (**{p_score}**)\nקלפי הדילר: {d_cards} (**{d_score}**)\n\nהפסדת את ההימור.", color=discord.Color.red())

        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


# ==========================================
#              3. משחק מוקשים (Mines)
# ==========================================
class MinesButton(discord.ui.Button):
    def __init__(self, idx, is_mine, row):
        super().__init__(style=discord.ButtonStyle.secondary, label="❓", row=row)
        self.idx = idx; self.is_mine = is_mine

    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user != v.player or v.game_over: return
        if self.is_mine:
            v.game_over = True; v.reveal_all()
            for child in v.children: child.disabled = True
            embed = discord.Embed(title="💥 מוקשים - פוצצת! 💥", description=f"פגעת במשבצת ממולכדת!\n😭 הפסדת **{v.bet}** טיקטים.", color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=v); v.stop(); return

        self.style = discord.ButtonStyle.success; self.label = "✓"; self.disabled = True; v.gems_found += 1
        multiplier = 1.0
        for i in range(v.gems_found): multiplier *= (v.total_tiles - i) / (v.total_tiles - v.total_mines - i)
        v.multiplier = round(multiplier, 2)
        for item in v.children:
            if item.custom_id == "mines_cashout": item.disabled = False; item.label = f"💰 פרישה (x{v.multiplier:.2f})"
        embed = discord.Embed(title="💣 משחק מוקשים מותאם אישית! 💣", description=f"🎰 סוג הלוח: `{v.total_tiles}` כפתורים | 🛑 פצצות: `{v.total_mines}`\n הימור: **{v.bet}** 🎫\n💎 יהלומים שנמצאו: `{v.gems_found}`\n📈 מכפיל נוכחי: **x{v.multiplier:.2f}**\n💰 רווח נוכחי: **{int(v.bet * v.multiplier)}** 🎫", color=discord.Color.green())
        await interaction.response.edit_message(embed=embed, view=v)

class CasinoMinesView(discord.ui.View):
    def __init__(self, player, bet, total_tiles, total_mines):
        super().__init__(timeout=240.0); self.player = player; self.bet = bet; self.total_tiles = total_tiles; self.total_mines = total_mines; self.gems_found = 0; self.multiplier = 1.0; self.game_over = False
        pool = [True] * total_mines + [False] * (total_tiles - total_mines); random.shuffle(pool)
        for idx in range(total_tiles): row_idx = idx // 5; self.add_item(MinesButton(idx=idx, is_mine=pool[idx], row=row_idx))
        last_row = (total_tiles - 1) // 5 + 1
        cashout_btn = discord.ui.Button(label="💰 פרישה", style=discord.ButtonStyle.primary, custom_id="mines_cashout", disabled=True, row=last_row)
        cashout_btn.callback = self.cashout_callback; self.add_item(cashout_btn)

    def reveal_all(self):
        for item in self.children:
            if isinstance(item, MinesButton):
                if item.is_mine: item.style = discord.ButtonStyle.danger; item.label = "✗"
                else:
                    if item.label != "✓": item.style = discord.ButtonStyle.secondary; item.label = "✓"

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user != self.player or self.game_over: return
        self.game_over = True; self.reveal_all()
        for child in self.children: child.disabled = True
        winnings = int(self.bet * self.multiplier); update_tickets(self.player.id, winnings)
        embed = discord.Embed(title="💰 משכת בהצלחה! 💰", description=f"פרשת מהמכרה בזמן עם מכפיל **x{self.multiplier:.2f}**!\n🏆 זכית ב-**{winnings}** טיקטים! 🎉", color=discord.Color.gold())
        await interaction.response.edit_message(embed=embed, view=self); self.stop()

class MinesRiskSetupView(discord.ui.View):
    def __init__(self, player, bet, total_tiles): super().__init__(timeout=60.0); self.player = player; self.bet = bet; self.total_tiles = total_tiles
    @discord.ui.button(label="🟢 רבע לוח פצצות (סיכון נמוך)", style=discord.ButtonStyle.success)
    async def quarter_mines(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        total_mines = max(1, self.total_tiles // 4); view = CasinoMinesView(self.player, self.bet, self.total_tiles, total_mines)
        embed = discord.Embed(title="💣 המשחק התחיל! 💣", description=f"🎰 גודל הלוח: `{self.total_tiles}` כפתורים\n🛑 כמות פצצות: `{total_mines}` (רבע לוח)\n💰 הימור: **{self.bet}** 🎫\n\nלחץ על משבצות, היזהר מהפצצות ופרש כשבא לך!", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="🔥 חצי לוח פצצות (סיכון מטורף)", style=discord.ButtonStyle.danger)
    async def half_mines(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        total_mines = self.total_tiles // 2; view = CasinoMinesView(self.player, self.bet, self.total_tiles, total_mines)
        embed = discord.Embed(title="🔥 סיכון מטורף - חצי לוח פצצות! 🔥", description=f"🎰 גודל הלוח: `{self.total_tiles}` כפתורים\n🛑 כמות פצצות: `{total_mines}` (חצי לוח!)\n💰 הימור: **{self.bet}** 🎫\n\nהמכפיל בשמיים! כל לחיצה שווה פי כמה! בהצלחה!", color=discord.Color.red())
        await interaction.response.edit_message(embed=embed, view=view)

class MinesSizeSetupView(discord.ui.View):
    def __init__(self, player, bet): super().__init__(timeout=60.0); self.player = player; self.bet = bet
    @discord.ui.button(label="📦 לוח קטן (10 כפתורים)", style=discord.ButtonStyle.secondary)
    async def size_10(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        view = MinesRiskSetupView(self.player, self.bet, total_tiles=10)
        embed = discord.Embed(title="🛑 בחר את כמות הפצצות ללוח הקטן (10):", description="חצי לוח פצצות מעניק מכפילים גבוהים בהרבה!", color=discord.Color.purple())
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="🖼️ לוח קלאסי (20 כפתורים)", style=discord.ButtonStyle.secondary)
    async def size_20(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        view = MinesRiskSetupView(self.player, self.bet, total_tiles=20)
        embed = discord.Embed(title="🛑 בחר את כמות הפצצות ללוח הקלאסי (20):", description="חצי לוח פצצות מעניק מכפילים גבוהים בהרבה!", color=discord.Color.purple())
        await interaction.response.edit_message(embed=embed, view=view)
    @discord.ui.button(label="🧱 לוח ענקי (25 כפתורים)", style=discord.ButtonStyle.secondary)
    async def size_40(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.player: return
        view = MinesRiskSetupView(self.player, self.bet, total_tiles=25)
        embed = discord.Embed(title="🛑 בחר את כמות הפצצות לוח הענקי (25):", description="חצי לוח פצצות מעניק מכפילים גבוהים בהרבה!", color=discord.Color.purple())
        await interaction.response.edit_message(embed=embed, view=view)


# ==========================================
#              4. משחק מגדל (Tower)
# ==========================================
class TowerGameView(discord.ui.View):
    def __init__(self, player, bet):
        super().__init__(timeout=120.0)
        self.player = player
        self.bet = bet
        self.current_row = 3  # מתחילים מלמטה (שורה 3 מתוך 0-3)
        self.game_over = False
        self.multiplier = 1.0
        self.setup_board()

    def setup_board(self):
        self.clear_items()
        # מגדל בגובה 4 שורות, בכל שורה 3 משבצות (אחת מהן פצצה)
        for r in range(4):
            safe_spot = random.randint(0, 2)
            for c in range(3):
                is_mine = (c != safe_spot)
                btn = TowerButton(row=r, col=c, is_mine=is_mine, disabled=(r != self.current_row))
                self.add_item(btn)
        
        cashout_btn = discord.ui.Button(label="💰 פרישה מהמגדל", style=discord.ButtonStyle.success, row=4, custom_id="tower_cashout", disabled=True)
        cashout_btn.callback = self.cashout_callback
        self.add_item(cashout_btn)

    async def cashout_callback(self, interaction: discord.Interaction):
        if interaction.user != self.player or self.game_over: return
        self.game_over = True
        for child in self.children: child.disabled = True
        winnings = int(self.bet * self.multiplier)
        update_tickets(self.player.id, winnings)
        embed = discord.Embed(title="🏰 מגדל האוצרות - פרישה מוצלחת! 🏰", description=f"ירדת מהמגדל עם מכפיל **x{self.multiplier:.2f}**!\n🏆 זכית ב-**{winnings}** טיקטים!", color=discord.Color.gold())
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

class TowerButton(discord.ui.Button):
    def __init__(self, row, col, is_mine, disabled):
        super().__init__(style=discord.ButtonStyle.secondary, label="🧱", row=row, disabled=disabled)
        self.target_row = row
        self.target_col = col
        self.is_mine = is_mine

    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user != v.player or v.game_over: return

        if self.is_mine:
            v.game_over = True
            for child in v.children: child.disabled = True
            self.style = discord.ButtonStyle.danger
            self.label = "💥"
            embed = discord.Embed(title="🏰 מגדל האוצרות - התמוטטות! 💥", description=f"בחרת משבצת ממולכדת בשורה {4 - v.current_row}!\n😭 הפסדת **{v.bet}** טיקטים.", color=discord.Color.red())
            await interaction.response.edit_message(embed=embed, view=v)
            v.stop()
            return

        # הצלחה בשורה
        self.style = discord.ButtonStyle.success
        self.label = "💎"
        v.multiplier = round(v.multiplier * 1.45, 2)
        v.current_row -= 1

        if v.current_row < 0:
            # הגעת לראש המגדל!
            v.game_over = True
            for child in v.children: child.disabled = True
            winnings = int(v.bet * v.multiplier)
            update_tickets(v.player.id, winnings)
            embed = discord.Embed(title="👑 כיבוש המגדל הושלם בהצלחה! 👑", description=f"הגעת לפסגת המגדל! מכפיל סופי: **x{v.multiplier:.2f}**\n🏆 זכית ב-**{winnings}** טיקטים!", color=discord.Color.gold())
            await interaction.response.edit_message(embed=embed, view=v)
            v.stop()
            return

        # עדכון השורות הבאות שפעילות
        for child in v.children:
            if isinstance(child, TowerButton):
                if child.target_row == v.current_row:
                    child.disabled = False
                else:
                    child.disabled = True
            elif child.custom_id == "tower_cashout":
                child.disabled = False
                child.label = f"💰 פרישה (x{v.multiplier:.2f})"

        embed = discord.Embed(title="🏰 טיפוס במגדל האוצרות 🏰", description=f"הימור: **{v.bet}** 🎫\n📈 מכפיל נוכחי: **x{v.multiplier:.2f}**\n💰 רווח נוכחי: **{int(v.bet * v.multiplier)}** 🎫\n\nבחר משבצת בשורה הבאה!", color=discord.Color.purple())
        await interaction.response.edit_message(embed=embed, view=v)


# ==========================================
#          5. משחק חמוד וכיף: "תפוס את החתול"
# ==========================================
class CatCatchButton(discord.ui.Button):
    def __init__(self, idx, has_cat):
        super().__init__(style=discord.ButtonStyle.secondary, label="📦", row=idx // 3)
        self.idx = idx
        self.has_cat = has_cat

    async def callback(self, interaction: discord.Interaction):
        v = self.view
        if interaction.user != v.player or v.game_over: return
        v.game_over = True

        for child in v.children:
            child.disabled = True
            if isinstance(child, CatCatchButton):
                if child.has_cat:
                    child.style = discord.ButtonStyle.success
                    child.label = "🐱"
                else:
                    child.style = discord.ButtonStyle.secondary
                    child.label = "💨"

        if self.has_cat:
            winnings = v.bet * 3
            update_tickets(v.player.id, winnings)
            embed = discord.Embed(title="🎉 מצאת את החתלתול המתוק! 🐱💖", description=f"תפסת את החתול בקופסה הנכונה!\n🏆 זכית בפי 3 מההימור: **{winnings}** טיקטים! 🎉", color=discord.Color.nitro_pink())
        else:
            self.style = discord.ButtonStyle.danger
            self.label = "📭"
            embed = discord.Embed(title="😢 פספסת את החתול...", description=f"החתול הסתתר בקופסה אחרת לגמרי!\n😭 הפסדת **{v.bet}** טיקטים.", color=discord.Color.red())

        await interaction.response.edit_message(embed=embed, view=v)
        v.stop()

class CatCatchView(discord.ui.View):
    def __init__(self, player, bet):
        super().__init__(timeout=60.0)
        self.player = player
        self.bet = bet
        self.game_over = False
        cat_pos = random.randint(0, 5) # 6 קופסאות (לוח 2x3)
        for i in range(6):
            self.add_item(CatCatchButton(idx=i, has_cat=(i == cat_pos)))


# ==========================================
#          פקודות הכלכלה והמשחקים הראשיות
# ==========================================

@bot.tree.command(name="balance", description="בדוק את יתרת הטיקטים שלך")
async def balance(interaction: discord.Interaction, member: discord.Member = None):
    target = member or interaction.user
    if is_user_banned(target.id):
        await interaction.response.send_message("❌ משתמש זה חסום מהבוט!", ephemeral=True)
        return
    u = get_user_data(target.id)
    embed = discord.Embed(
        title=f"💳 יתרת טיקטים: {target.name}",
        description=f"יש בחשבון **{u['tickets']}** טיקטים 🎫",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="daily", description="קבל את הבונוס היומי שלך")
async def daily(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    uid = str(interaction.user.id)
    u = get_user_data(interaction.user.id)
    now = datetime.now(timezone.utc)
    
    if u["last_daily"]:
        last = datetime.fromisoformat(u["last_daily"])
        if now - last < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last)
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await interaction.response.send_message(f"⏳ כבר אספת את הבונוס היומי שלך! תוכל לאסוף שוב בעוד **{hours} שעות ו-{minutes} דקות**.", ephemeral=True)
            return

    reward = 50
    update_tickets(interaction.user.id, reward)
    data = load_data()
    data[uid]["last_daily"] = now.isoformat()
    save_data(data)
    
    await interaction.response.send_message(f"🎁 **אספת את הבונוס היומי בהצלחה!** קיבלת **{reward}** טיקטים 🎫", ephemeral=True)

@bot.tree.command(name="store", description="פתח את חנות הקזינו לרכישת רולים והטבות")
async def store(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    embed = discord.Embed(
        title="🛒 חנות הקזינו הרשמית 🛒",
        description="כאן תוכל להשתמש בטיקטים שהרווחת ולרכוש רולים בלעדיים:\n\n👑 **V.I.P Casino** — 500 טיקטים 🎫\n*(מעניק רול זהב בלעדי בשרת)*",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=CasinoStoreView(), ephemeral=True)

@bot.tree.command(name="leaderboard", description="הצג את עשירי הקזינו")
async def leaderboard(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    await show_leaderboard(interaction)

@bot.tree.command(name="redeem", description="מימוש קוד קופון סודי")
async def redeem(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    await interaction.response.send_modal(PromoModal())

@bot.tree.command(name="poker", description="שחק במשחק הפוקר והשג שילובי קלפים מנצחים")
@app_commands.describe(bet="כמות הטיקטים להימור")
async def poker(interaction: discord.Interaction, bet: int):
    if is_user_banned(interaction.user.id): return
    if bet <= 0:
        await interaction.response.send_message("❌ סכום ההימור חייב להיות גדול מ-0!", ephemeral=True)
        return
    u = get_user_data(interaction.user.id)
    if u["tickets"] < bet:
        await interaction.response.send_message("❌ אין לך מספיק טיקטים בהימור זה!", ephemeral=True)
        return

    update_tickets(interaction.user.id, -bet)
    view = PokerGameView(interaction.user, bet)
    cards_str = " ".join([f"`{v}{s}`" for v, s in view.hand])
    embed = discord.Embed(
        title="🃏 משחק פוקר קזינו 🃏",
        description=f"ההימור שלך: **{bet}** 🎫\n\nהקלפים שקיבלת:\n{cards_str}\n\nלחץ על הכפתור כדי להחליף קלפים ולקבל תוצאה סופית!",
        color=discord.Color.dark_theme()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="blackjack", description="שחק בלקג'ק מול הדילר")
@app_commands.describe(bet="כמות ההימור")
async def blackjack(interaction: discord.Interaction, bet: int):
    if is_user_banned(interaction.user.id): return
    if bet <= 0:
        await interaction.response.send_message("❌ הימור לא תקין!", ephemeral=True); return
    u = get_user_data(interaction.user.id)
    if u["tickets"] < bet:
        await interaction.response.send_message("❌ אין לך מספיק טיקטים!", ephemeral=True); return

    update_tickets(interaction.user.id, -bet)
    view = BlackjackView(interaction.user, bet)
    p_score = view.calculate_score(view.player_hand)
    p_cards = " ".join([f"`{v}{s}`" for v, s in view.player_hand])
    
    embed = discord.Embed(
        title="🃏 שולחן בלקג'ק 🃏",
        description=f"הימור: **{bet}** 🎫\n\nהקלפים שלך: {p_cards} (סכום: **{p_score}**)\nקלף גלוי של הדילר: `{view.dealer_hand[0][0]}{view.dealer_hand[0][1]}`",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="mines", description="שחק במשחק המוקשים (Mines)")
@app_commands.describe(bet="כמות ההימור")
async def mines(interaction: discord.Interaction, bet: int):
    if is_user_banned(interaction.user.id): return
    if bet <= 0:
        await interaction.response.send_message("❌ הימור לא תקין!", ephemeral=True); return
    u = get_user_data(interaction.user.id)
    if u["tickets"] < bet:
        await interaction.response.send_message("❌ אין לך מספיק טיקטים!", ephemeral=True); return

    update_tickets(interaction.user.id, -bet)
    view = MinesSizeSetupView(interaction.user, bet)
    embed = discord.Embed(
        title="💣 בחר את גודל לוח המשחק:",
        description=f"הימור: **{bet}** 🎫\n\nבחר את כמות המשבצות הרצויה ללוח המוקשים:",
        color=discord.Color.dark_embed()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="tower", description="טפס במגדל האוצרות והיזהר מהפצצות")
@app_commands.describe(bet="כמות ההימור")
async def tower(interaction: discord.Interaction, bet: int):
    if is_user_banned(interaction.user.id): return
    if bet <= 0:
        await interaction.response.send_message("❌ הימור לא תקין!", ephemeral=True); return
    u = get_user_data(interaction.user.id)
    if u["tickets"] < bet:
        await interaction.response.send_message("❌ אין לך מספיק טיקטים!", ephemeral=True); return

    update_tickets(interaction.user.id, -bet)
    view = TowerGameView(interaction.user, bet)
    embed = discord.Embed(
        title="🏰 מגדל האוצרות (Tower) 🏰",
        description=f"הימור: **{bet}** 🎫\n\nבחר משבצת בשורה התחתונה כדי להתחיל לטיפוס! היזהר מהפצצות.",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="catcatch", description="משחק כיף וחמוד: מצא באיזו קופסה מסתתר החתלתול!")
@app_commands.describe(bet="כמות ההימור")
async def catcatch(interaction: discord.Interaction, bet: int):
    if is_user_banned(interaction.user.id): return
    if bet <= 0:
        await interaction.response.send_message("❌ הימור לא תקין!", ephemeral=True); return
    u = get_user_data(interaction.user.id)
    if u["tickets"] < bet:
        await interaction.response.send_message("❌ אין לך מספיק טיקטים!", ephemeral=True); return

    update_tickets(interaction.user.id, -bet)
    view = CatCatchView(interaction.user, bet)
    embed = discord.Embed(
        title="🐱 תפוס את החתול! 📦",
        description=f"הימור: **{bet}** 🎫\n\nלפניך 6 קופסאות סגורות. באחת מהן מסתתר חתלתול חמוד שיביא לך פי 3 על ההימור!\nבחר קופסה:",
        color=discord.Color.nitro_pink()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ==========================================
#              הפעלת הבוט
# ==========================================
if __name__ == "__main__":
    keep_alive()
    TOKEN = os.environ.get("DISCORD_TOKEN", "הכנס_את_הטוקן_שלך_כאן")
    bot.run(TOKEN)