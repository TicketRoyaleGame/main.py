import os, random
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask
import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput

# 1. Flask Keep-Alive
app = Flask('')
@app.route('/')
def home(): return "Online"
def keep_alive():
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=8080))
    t.daemon = True; t.start()

# 2. Bot & Databases
bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())
OWNER_ID = 1260675229626273802
user_tokens, daily_cooldown, failed_attempts = {}, {}, {}

def get_t(uid): return user_tokens.get(uid, 100)
def add_t(uid, amt): user_tokens[uid] = get_t(uid) + amt
def rem_t(uid, amt):
    if get_t(uid) >= amt:
        user_tokens[uid] = get_t(uid) - amt
        return True
    return False

# 3. Security
async def sec_check(i: discord.Interaction):
    if i.user.id != OWNER_ID:
        failed_attempts[i.user.id] = failed_attempts.get(i.user.id, 0) + 1
        await i.response.send_message(f"❌ אין גישה! פנה למנהל: <@{OWNER_ID}>", ephemeral=True)
        try:
            owner = await bot.fetch_user(OWNER_ID)
            await owner.send(f"🚨 ניסיון פריצה מ-{i.user} (ID: {i.user.id}), סך כשלונות: {failed_attempts[i.user.id]}")
        except: pass
        return False
    return True

# 4. Modals & Admin
class AdminModal(Modal):
    def __init__(self, t): super().__init__(title=f"ניהול - {t}"); self.t = t; self.id_in = TextInput(label="ID משתמש", required=True); self.amt_in = TextInput(label="כמות טוקנים", required=False); self.add_item(self.id_in); self.add_item(self.amt_in)
    async def on_submit(self, i):
        if not await sec_check(i): return
        uid = int(self.id_in.value.strip())
        if self.t == "tokens":
            amt = int(self.amt_in.value.strip()); add_t(uid, amt)
            await i.response.send_message(f"✅ נוספו {amt} ל-<@{uid}>.", ephemeral=True)
        else:
            await i.guild.ban(await i.guild.fetch_member(uid), reason="פאנל ניהול"); await i.response.send_message(f"🔨 בוצע באן ל-<@{uid}>.", ephemeral=True)

class AdminView(View):
    @discord.ui.button(label="🔨 באנים", style=discord.ButtonStyle.danger, custom_id="a_ban")
    async def b_cb(self, i, b): 
        if await sec_check(i): await i.response.send_modal(AdminModal("ban"))
    @discord.ui.button(label="🪙 טוקנים", style=discord.ButtonStyle.success, custom_id="a_tok")
    async def t_cb(self, i, b): 
        if await sec_check(i): await i.response.send_modal(AdminModal("tokens"))

# 5. Games Modals & Views
class BetModal(Modal):
    def __init__(self, title, callback): super().__init__(title=title); self.cb = callback; self.b = TextInput(label="הימור טוקנים", required=True); self.add_item(self.b)
    async def on_submit(self, i): await self.cb(i, int(self.b.value))

# Blackjack
class BJView(View):
    def __init__(self, bet, p, d, deck): super().__init__(timeout=60); self.bet=bet; self.p=p; self.d=d; self.deck=deck
    def score(self, cards):
        s = sum(cards); aces = cards.count(11)
        while s > 21 and aces: s -= 10; aces -= 1
        return s
    def emb(self, fin=False):
        return discord.Embed(title="🃏 בלאק ג'ק", description=f"הקלפים שלך: {self.p} (ניקוד: {self.score(self.p)})\nדילר: {self.d if fin else [self.d[0], '?']}", color=0xFFD700)
    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, i, b):
        self.p.append(self.deck.pop())
        if self.score(self.p) > 21:
            for c in self.children: c.disabled = True
            await i.response.edit_message(embed=self.emb(True), view=self)
            await i.followup.send(f"💥 עברת 21! הפסדת {self.bet}.", ephemeral=True)
        else: await i.response.edit_message(embed=self.emb(), view=self)
    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, i, b):
        while self.score(self.d) < 17: self.d.append(self.deck.pop())
        ps, ds = self.score(self.p), self.score(self.d)
        for c in self.children: c.disabled = True
        if ds > 21 or ps > ds: add_t(i.user.id, self.bet * 2); msg = f"🎉 ניצחת וזכית ב-{self.bet*2}!"
        elif ps == ds: add_t(i.user.id, self.bet); msg = "🤝 תיקו!"
        else: msg = "😢 הפסדת."
        await i.response.edit_message(embed=self.emb(True), view=self)
        await i.followup.send(msg, ephemeral=True)

# Mines
class MinesBtn(Button):
    def __init__(self, x, y): super().__init__(style=discord.ButtonStyle.secondary, label="🟦", row=x); self.x=x; self.y=y
    async def callback(self, i): await self.view.click(i, self)

class MinesView(View):
    def __init__(self, bet, mc, uid):
        super().__init__(timeout=120); self.bet=bet; self.uid=uid; self.mult=1.0; self.over=False
        self.board = [['safe']*5 for _ in range(5)]
        p = 0
        while p < mc:
            rx, ry = random.randint(0,4), random.randint(0,4)
            if self.board[rx][ry] == 'safe': self.board[rx][ry] = 'mine'; p += 1
        for r in range(5):
            for c in range(5): self.add_item(MinesBtn(r, c))
    async def click(self, i, b):
        if self.over: return
        if self.board[b.x][b.y] == 'mine':
            self.over = True; b.style = discord.ButtonStyle.danger; b.label = "💥"
            for c in self.children: c.disabled = True
            await i.response.edit_message(embed=discord.Embed(title="💥 פוצצת פצצה!", color=0xFF0000), view=self)
        else:
            b.style = discord.ButtonStyle.success; b.label = "💎"; b.disabled = True; self.mult += 0.35
            await i.response.edit_message(embed=discord.Embed(title=f"💎 יהלום! מכפיל: {self.mult:.2f}x", color=0xFFA500), view=self)
    @discord.ui.button(label="💰 Cashout", style=discord.ButtonStyle.blurple, row=4)
    async def cash(self, i, b):
        if self.over: return
        self.over = True; win = int(self.bet * self.mult); add_t(self.uid, win)
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=discord.Embed(title=f"💰 משכת {win} טוקנים!", color=0x00FF00), view=self)

# Tower
class TowerView(View):
    def __init__(self, bet, uid):
        super().__init__(timeout=120); self.bet=bet; self.uid=uid; self.fl=1; self.mults=[1.3, 1.8, 2.5, 3.8, 5.5]; self.setup()
    def setup(self):
        self.clear_items(); safe = random.randint(0,2)
        for idx, i in enumerate(range(3)): self.add_item(Button(style=discord.ButtonStyle.secondary, label=f"דלת {i+1}", custom_id=str(idx==safe)))
        self.add_item(Button(label="💰 משוך", style=discord.ButtonStyle.success, row=1, custom_id="cash"))
    async def interaction_check(self, i):
        if i.data['custom_id'] == "cash":
            win = int(self.bet * (self.mults[self.fl-2] if self.fl > 1 else 1.1))
            add_t(self.uid, win); 
            for c in self.children: c.disabled = True
            await i.response.edit_message(embed=discord.Embed(title=f"💰 משיכה: {win}", color=0x00FF00), view=self); return False
        is_safe = i.data['custom_id'] == "True"
        if is_safe:
            if self.fl == 5:
                win = int(self.bet * self.mults[4]); add_t(self.uid, win)
                for c in self.children: c.disabled = True
                await i.response.edit_message(embed=discord.Embed(title=f"👑 הגעת לפסגה! זכית ב-{win}", color=0xFFD700), view=self)
            else:
                self.fl += 1; self.setup()
                await i.response.edit_message(embed=discord.Embed(title=f"🗼 קומה {self.fl}/5", color=0x800080), view=self)
        else:
            for c in self.children: c.disabled = True
            await i.response.edit_message(embed=discord.Embed(title="💥 מלכודת!", color=0xFF0000), view=self)
        return False

# Poker
class PokerView(View):
    def __init__(self, bet, cards, uid):
        super().__init__(timeout=60); self.bet=bet; self.cards=cards; self.uid=uid; self.held=[False]*5
        for idx, c in enumerate(cards): self.add_item(Button(style=discord.ButtonStyle.secondary, label=f"קלף {idx+1} ({c})", row=0))
        self.add_item(Button(label="Draw", style=discord.ButtonStyle.primary, row=1))
    async def interaction_check(self, i):
        custom = i.data.get('custom_id') # Handle buttons
        # Simplified interaction routing for brevity
        for idx, child in enumerate(self.children[:-1]):
            if child.callback.__name__ == i.data.get('custom_id', ''): pass # handled natively if custom_id set
        return True

# Lobby
class LobbyView(View):
    @discord.ui.button(label="🃏 Blackjack", style=discord.ButtonStyle.primary, custom_id="g_bj")
    async def bj(self, i, b):
        async def cb(i, bet):
            if rem_t(i.user.id, bet):
                d = [random.randint(2,11) for _ in range(52)]; random.shuffle(d)
                await i.response.send_message(embed=BJView(bet, [d.pop(), d.pop()], [d.pop(), d.pop()], d).emb(), view=BJView(bet, [d.pop(), d.pop()], [d.pop(), d.pop()], d), ephemeral=True)
            else: await i.response.send_message("❌ אין טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("בלאק ג'ק", cb))

    @discord.ui.button(label="💣 Mines", style=discord.ButtonStyle.danger, custom_id="g_mi")
    async def mi(self, i, b):
        async def cb(i, bet):
            if rem_t(i.user.id, bet): await i.response.send_message(embed=discord.Embed(title="💣 מכרות"), view=MinesView(bet, 3, i.user.id), ephemeral=True)
            else: await i.response.send_message("❌ אין טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("מכרות", cb))

    @discord.ui.button(label="🎰 Roulette", style=discord.ButtonStyle.success, custom_id="g_ro")
    async def ro(self, i, b):
        async def cb(i, bet):
            if rem_t(i.user.id, bet):
                roll = random.randint(0,36); col = 'green' if roll==0 else ('red' if roll%2 else 'black')
                add_t(i.user.id, bet * 14 if col=='green' else bet * 2) # simplified win
                await i.response.send_message(f"🎰 תוצאה: {roll} ({col}).", ephemeral=True)
            else: await i.response.send_message("❌ אין טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("רולטה", cb))

    @discord.ui.button(label="🗼 Tower", style=discord.ButtonStyle.blurple, custom_id="g_to")
    async def to(self, i, b):
        async def cb(i, bet):
            if rem_t(i.user.id, bet): await i.response.send_message(embed=discord.Embed(title="🗼 מגדל"), view=TowerView(bet, i.user.id), ephemeral=True)
            else: await i.response.send_message("❌ אין טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("טאואר", cb))

    @discord.ui.button(label="👑 Poker", style=discord.ButtonStyle.secondary, custom_id="g_po")
    async def po(self, i, b):
        async def cb(i, bet):
            if rem_t(i.user.id, bet):
                cards = [random.randint(2,14) for _ in range(5)]
                add_t(i.user.id, bet * 2); await i.response.send_message(f"👑 פוקר קלפים: {cards}, זכייה אוטומטית!", ephemeral=True)
            else: await i.response.send_message("❌ אין טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("פוקר", cb))

# 6. Commands
@bot.tree.command(name="פאנל_אזולאי", description="ניהול מאסטר")
async def pan_az(i):
    if await sec_check(i): await i.response.send_message(embed=discord.Embed(title="👑 פאנל אזולאי", color=0xFFD700), view=AdminView(), ephemeral=True)

@bot.tree.command(name="פאנל", description="קזינו")
async def casino(i):
    if i.user.id != OWNER_ID: await i.response.send_message("❌ רק אזולאי!", ephemeral=True); return
    await i.response.send_message(embed=discord.Embed(title="🎰 קזינו Ticket Royale", color=0x800080), view=LobbyView())

@bot.tree.command(name="דיילי", description="תגמול יומי")
async def daily(i):
    uid = i.user.id; now = datetime.utcnow()
    if uid in daily_cooldown and now < daily_cooldown[uid] + timedelta(hours=24):
        rem = (daily_cooldown[uid] + timedelta(hours=24)) - now
        await i.response.send_message(f"⏳ המתן עוד {int(rem.total_seconds()//3600)} שעות.", ephemeral=True); return
    daily_cooldown[uid] = now; add_t(uid, 20)
    await i.response.send_message(f"🎁 קיבלת 20 טוקנים! יתרה: {get_t(uid)}", ephemeral=True)

# 7. Start
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"מחובר כ-{bot.user}")

    async def interaction_check(self, i):
        if i.user.id != self.uid: return False
        cid = i.data.get('custom_id')
        
        # לחיצה על כפתור Draw (החלפת קלפים)
        if i.data.get('label') == "Draw":
            for c in self.children: c.disabled = True
            deck = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"] * 4
            for idx in range(5):
                if not self.held[idx]: self.cards[idx] = random.choice(deck)
            
            # בדיקת זוגות/שילובים בסיסית וחלוקת פרס
            from collections import Counter
            counts = sorted(Counter(self.cards).values(), reverse=True)
            if counts[0] >= 3: win = self.bet * 3; msg = f"🎉 שלשה ומעלה! זכית ב-{win}"
            elif counts[0] == 2 and counts[1] == 2: win = self.bet * 2; msg = f"👥 זוגיים! זכית ב-{win}"
            elif counts[0] == 2: win = self.bet * 1; msg = f"🃏 זוג! קיבלת את ההימור בחזרה ({win})"
            else: win = 0; msg = "😢 ללא שילוב. הפסדת."
            
            if win > 0: add_t(self.uid, win)
            await i.response.edit_message(embed=discord.Embed(title="👑 תוצאות פוקר", description=f"היד הסופית: {self.cards}\n\n{msg}", color=0x00FF00 if win > 0 else 0xFF0000), view=self)
            return False

        # לחיצה על קלף כדי לסמן אותו כ-Hold
        for idx in range(5):
            if i.data.get('label', '').startswith(f"קלף {idx+1}"):
                self.held[idx] = not self.held[idx]
                self.children[idx].style = discord.ButtonStyle.success if self.held[idx] else discord.ButtonStyle.secondary
                break
        await i.response.edit_message(view=self)
        return False

# Roulette
class RouletteView(View):
    def __init__(self, bet, uid): super().__init__(timeout=60); self.bet=bet; self.uid=uid
    async def spin(self, i, choice):
        num = random.randint(0, 36)
        color = "ירוק" if num == 0 else ("אדום" if num in [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36] else "שחור")
        win = (choice == color)
        pay = self.bet * 14 if color == "ירוק" else self.bet * 2
        if win: add_t(self.uid, pay)
        for c in self.children: c.disabled = True
        await i.response.edit_message(embed=discord.Embed(title=f"🎰 תוצאה: {num} ({color})", description=f"{'🎉 זכית ב-' + str(pay) if win else '❌ הפסדת ' + str(self.bet)} טוקנים.", color=0x00FF00 if win else 0xFF0000), view=self)

    @discord.ui.button(label="🔴 אדום (x2)", style=discord.ButtonStyle.danger)
    async def r(self, i, b): await self.spin(i, "אדום")
    @discord.ui.button(label="⚫ שחור (x2)", style=discord.ButtonStyle.secondary)
    async def bl(self, i, b): await self.spin(i, "שחור")
    @discord.ui.button(label="🟢 ירוק 0 (x14)", style=discord.ButtonStyle.success)
    async def gr(self, i, b): await self.spin(i, "ירוק")


# ==================== 6. PUBLIC LOBBY & SLASH COMMANDS ====================

class LobbyView(View):
    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary)
    async def bj(self, i, b):
        async def cb(inter, bet):
            if rem_t(inter.user.id, bet):
                dk = [2,3,4,5,6,7,8,9,10,10,10,10,11]*4; random.shuffle(dk)
                v = BJView(bet, [dk.pop(), dk.pop()], [dk.pop(), dk.pop()], dk)
                await inter.response.send_message(embed=v.emb(), view=v, ephemeral=True)
            else: await inter.response.send_message("❌ אין מספיק טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("🃏 הימור בלאק ג'ק", cb))

    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary)
    async def mn(self, i, b):
        async def cb(inter, bet):
            if rem_t(inter.user.id, bet):
                await inter.response.send_message(embed=discord.Embed(title="💣 משחק מכרות התחיל! בהצלחה!"), view=MinesView(bet, 3, inter.user.id), ephemeral=True)
            else: await inter.response.send_message("❌ אין מספיק טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("💣 הימור מכרות (3 פצצות)", cb))

    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary)
    async def tw(self, i, b):
        async def cb(inter, bet):
            if rem_t(inter.user.id, bet):
                await inter.response.send_message(embed=discord.Embed(title="🗼 קומה 1/5 - בחר דלת!"), view=TowerView(bet, inter.user.id), ephemeral=True)
            else: await inter.response.send_message("❌ אין מספיק טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("🗼 הימור טאואר", cb))

    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary)
    async def rl(self, i, b):
        async def cb(inter, bet):
            if rem_t(inter.user.id, bet):
                await inter.response.send_message(embed=discord.Embed(title="🎰 בחר צבע ברולטה:"), view=RouletteView(bet, inter.user.id), ephemeral=True)
            else: await inter.response.send_message("❌ אין מספיק טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("🎰 הימור רולטה", cb))

    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary)
    async def pk(self, i, b):
        async def cb(inter, bet):
            if rem_t(inter.user.id, bet):
                dk = ["2","3","4","5","6","7","8","9","10","J","Q","K","A"]*4
                v = PokerView(bet, [random.choice(dk) for _ in range(5)], inter.user.id)
                await inter.response.send_message(embed=discord.Embed(title="👑 סמן קלפים לנעילה ולחץ Draw:"), view=v, ephemeral=True)
            else: await inter.response.send_message("❌ אין מספיק טוקנים!", ephemeral=True)
        await i.response.send_modal(BetModal("👑 הימור פוקר וידאו", cb))


# --- פקודות סלאש ---

@bot.tree.command(name="פאנל_אזולאי", description="לוח בקרה סודי ומורחב רק בשבילך")
async def p_az(i: discord.Interaction):
    if await sec_check(i): await i.response.send_message(embed=discord.Embed(title="👑 פאנל אזולאי", description="לוח השליטה הבלעדי שלך:"), view=AdminView(), ephemeral=True)

@bot.tree.command(name="פאנל", description="הצגת לוח משחקי הקזינו לחברי השרת")
async def p_pub(i: discord.Interaction):
    if await sec_check(i): await i.response.send_message(embed=discord.Embed(title="🎰 קזינו Ticket Royale", description="לוח המשחקים פעיל! לחצו כדי להמר ולשחק:"), view=LobbyView(), ephemeral=False)

@bot.tree.command(name="דיילי", description="קבל 20 טוקנים חינם בכל 24 שעות")
async def dly(i: discord.Interaction):
    uid = i.user.id; now = datetime.now()
    if uid in daily_cooldown and now < daily_cooldown[uid] + timedelta(hours=24):
        tl = (daily_cooldown[uid] + timedelta(hours=24)) - now
        h, rem = divmod(tl.seconds, 3600); m, _ = divmod(rem, 60)
        await i.response.send_message(f"❌ חזור בעוד {h} שעות ו-{m} דקות.", ephemeral=True); return
    add_t(uid, 20); daily_cooldown[uid] = now
    await i.response.send_message(f"🪙 קיבלת 20 טוקנים! מאזן נוכחי: {get_t(uid)}")


# ==================== 7. STARTUP BLOCK ====================

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Casino Bot is Online as {bot.user}")

keep_alive()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN: bot.run(TOKEN)
else: bot.run("הטוקן_הסודי_שלך_כאן")
