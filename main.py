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

    return "Bot is alive 24/7!"



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

        embed.add_field(name="🆔 Guild ID:", value=f"`{guild.id}`", inline=True)

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

            embed = discord.Embed(title="🚀 תודה על הבוסט! 🚀", description=f"תודה רבה ל-{after.mention} על הבוסט! \nקיבלת בונוס של **{boost_reward}** טיקטים! 🎫💎", color=discord.Color.nitro_pink())

            await after.guild.system_channel.send(embed=embed)

        try: await after.send(f"🔮 **תודה על הבוסט לשרת {after.guild.name}!** קיבלת **{boost_reward}** טיקטים! 🎉")

        except: pass



@bot.event

async def on_ready(): 

    print(f"Bot connected: {bot.user}")

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

            try: role = await guild.create_role(name=role_name, color=discord.Color.gold(), reason="Casino Shop")

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

    user_scores.sort(key=lambda x: x, reverse=True); top_5 = user_scores[:5]

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

    hours_input = discord.ui.TextInput(label="לכמה שעות לחסום? (0 לקבוע)", placeholder="לדוגמה: 24", required=True)

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

class PenaltyView(discord.ui.View):

    def __init__(self, player, bet): 

        super().__init__(timeout=60.0)

        self.player = player; self.bet = bet

        self.winning_spot = random.choice(["TL", "BL", "C", "TR", "BR"])



    async def handle_kick(self, interaction: discord.Interaction, chosen_spot: str):

        if interaction.user != self.player: return

        for item in self.children: item.disabled = True

        spots = {"TL": "📐 שמאל למעלה", "BL": "👟 שמאל למטה", "C": "🎯 אמצע השער", "TR": "📐 ימין למעלה", "BR": "👟 ימין למטה"}

        if chosen_spot == self.winning_spot:

            winnings = self.bet * 4; update_tickets(self.player.id, winnings)

            embed = discord.Embed(title="⚽ גוווווול!!!! שער מטורף!! ⚽", description=f"בעטת לפינת **{spots[chosen_spot]}**.\n🏆 הרווחת **{winnings}** טיקטים! (מכפיל x4)", color=discord.Color.green())

        else: 

            embed = discord.Embed(title="🧤 השוער עצר! אין שער! 😭", description=f"בעטת לפינת **{spots[chosen_spot]}**.\nהפינה הריקה הייתה: **{spots[self.winning_spot]}**.", color=discord.Color.red())

        await interaction.response.edit_message(content="```\n🥅⚽  |   ש ע ר   כ ד ו ר ג ל   |  ⚽🥅\n```", embed=embed, view=self)

        self.stop()



    @discord.ui.button(label="📐 שמאל למעלה", style=discord.ButtonStyle.primary, row=0)

    async def t_l(self, int, b): await self.handle_kick(int, "TL")

    @discord.ui.button(label="📐 ימין למעלה", style=discord.ButtonStyle.primary, row=0)

    async def t_r(self, int, b): await self.handle_kick(int, "TR")

    @discord.ui.button(label="👟 שמאל למטה", style=discord.ButtonStyle.secondary, row=1)

    async def b_l(self, int, b): await self.handle_kick(int, "BL")

    @discord.ui.button(label="🎯 אמצע השער", style=discord.ButtonStyle.danger, row=1)

    async def cnt(self, int, b): await self.handle_kick(int, "C")

    @discord.ui.button(label="👟 ימין למטה", style=discord.ButtonStyle.secondary, row=1)

    async def b_r(self, int, b): await self.handle_kick(int, "BR")



class CrashView(discord.ui.View):

    def __init__(self, player, bet): 

        super().__init__(timeout=60.0)

        self.player = player; self.bet = bet; self.multiplier = 1.0; self.active = True

        if random.randint(1, 100) <= 50: self.crash_point = round(random.uniform(1.1, 1.8), 2)

        else: self.crash_point = round(random.uniform(1.8, 5.5), 2)



    async def run_game(self, interaction: discord.Interaction):

        while self.active:

            await asyncio.sleep(1.2)

            if not self.active: break

            self.multiplier = round(self.multiplier + random.uniform(0.1, 0.25), 2)

            if self.multiplier >= self.crash_point:

                self.active = False

                for x in self.children: x.disabled = True

                await interaction.edit_original_response(content=f"💥 **החללית התפוצצה! (CRASH)**\n📈 מכפיל: **x{self.crash_point:.2f}**\n😭 הפסדת **{self.bet}** טיקטים.", view=self)

                self.stop(); return

            try: await interaction.edit_original_response(content=f"🚀 **החללית באוויר!**\n📈 מכפיל: **x{self.multiplier:.2f}**\n💰 פוטנציאל: **{int(self.bet * self.multiplier)}** 🎫", view=self)

            except: break



    @discord.ui.button(label="💥 לפרוש (Cashout)", style=discord.ButtonStyle.success)

    async def cashout(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player or not self.active: return

        self.active = False

        for x in self.children: x.disabled = True

        winnings = int(self.bet * self.multiplier); update_tickets(self.player.id, winnings)

        await interaction.response.edit_message(content=f"💰 **פרשת בזמן!** במכפיל **x{self.multiplier:.2f}**.\n🏆 זכית ב-**{winnings}** טיקטים!", view=self)

        self.stop()

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

            if item.custom_id == "mines_cashout": item.disabled = False; item.label = f"💰 CASHOUT (x{v.multiplier:.2f})"

        embed = discord.Embed(title="💣 משחק מוקשים מותאם אישית! 💣", description=f"🎰 סוג הלוח: `{v.total_tiles}` כפתורים | 🛑 פצצות: `{v.total_mines}`\n הימור: **{v.bet}** 🎫\n💎 יהלומים שנמצאו: `{v.gems_found}`\n📈 מכפיל נוכחי: **x{v.multiplier:.2f}**\n💰 רווח נוכחי: **{int(v.bet * v.multiplier)}** 🎫", color=discord.Color.green())

        await interaction.response.edit_message(embed=embed, view=v)



class CasinoMinesView(discord.ui.View):

    def __init__(self, player, bet, total_tiles, total_mines):

        super().__init__(timeout=240.0); self.player = player; self.bet = bet; self.total_tiles = total_tiles; self.total_mines = total_mines; self.gems_found = 0; self.multiplier = 1.0; self.game_over = False

        pool = [True] * total_mines + [False] * (total_tiles - total_mines); random.shuffle(pool)

        for idx in range(total_tiles): row_idx = idx // 5; self.add_item(MinesButton(idx=idx, is_mine=pool[idx], row=row_idx))

        last_row = (total_tiles - 1) // 5 + 1

        cashout_btn = discord.ui.Button(label="💰 CASHOUT", style=discord.ButtonStyle.primary, custom_id="mines_cashout", disabled=True, row=last_row)

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

    @discord.ui.button(label="🟢 רבע לוח פצצות (סיכון נמוך | רווח רגיל)", style=discord.ButtonStyle.success)

    async def quarter_mines(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player: return

        total_mines = max(1, self.total_tiles // 4); view = CasinoMinesView(self.player, self.bet, self.total_tiles, total_mines)

        embed = discord.Embed(title="💣 המשחק התחיל! 💣", description=f"🎰 גודל הלוח: `{self.total_tiles}` כפתורים\n🛑 כמות פצצות: `{total_mines}` (רבע לוח)\n💰 הימור: **{self.bet}** 🎫\n\nלחץ על משבצות, היזהר מהפצצות ופרש כשבא לך!", color=discord.Color.blue())

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="🔥 חצי לוח פצצות (סיכון מטורף | רווח ענקי!)", style=discord.ButtonStyle.danger)

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

    @discord.ui.button(label="🧱 לוח ענקי (25 כפתורים - מקסימום!)", style=discord.ButtonStyle.secondary)

    async def size_40(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player: return

        view = MinesRiskSetupView(self.player, self.bet, total_tiles=25)

        embed = discord.Embed(title="🛑 בחר את כמות הפצצות ללוח הענקי (25):", description="חצי לוח פצצות מעניק מכפילים גבוהים בהרבה!", color=discord.Color.purple())

        await interaction.response.edit_message(embed=embed, view=view)

class DiceView(discord.ui.View):

    def __init__(self, player, bet): super().__init__(timeout=60.0); self.player = player; self.bet = bet

    async def run_dice(self, interaction: discord.Interaction, count: int):

        if interaction.user != self.player: return

        update_tickets(self.player.id, -self.bet); rolls = [random.randint(1, 6) for _ in range(count)]; total_score = sum(rolls)

        dice_emojis = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}; rolls_display = " ".join([dice_emojis[r] for r in rolls])

        needed_to_win = math.ceil(count * 4.2); multiplier = 2 if count <= 10 else (3 if count <= 20 else 5)

        if total_score >= needed_to_win:

            winnings = int(self.bet * multiplier); update_tickets(self.player.id, winnings)

            embed = discord.Embed(title="🔥 ניצחון נדיר בקוביות! 🔥", description=f"התוצאות הן:\n\n{rolls_display}\n\n📊 סך הכל: **{total_score}**\n🏆 זכת ב-**{winnings}** טיקטים!", color=discord.Color.gold())

        else: embed = discord.Embed(title="😭 הפסדת בקוביות! 😭", description=f"התוצאות הן:\n\n{rolls_display}\n\n📊 סך הכל: **{total_score}**\n🛑 נדרש לפחות **{needed_to_win}**.", color=discord.Color.red())

        for item in self.children: item.disabled = True

        await interaction.response.edit_message(content="```🎲 תוצאת משחק הקוביות:```", embed=embed, view=self); self.stop()

    @discord.ui.button(label="🎲 5 קוביות (x2)", style=discord.ButtonStyle.primary, row=0)

    async def d5(self, intr, b): await self.run_dice(intr, 5)

    @discord.ui.button(label="🎲 10 קוביות (x2)", style=discord.ButtonStyle.primary, row=0)

    async def d10(self, intr, b): await self.run_dice(intr, 10)

    @discord.ui.button(label="🎲 15 קוביות (x3)", style=discord.ButtonStyle.secondary, row=1)

    async def d15(self, intr, b): await self.run_dice(intr, 15)

    @discord.ui.button(label="🎲 20 קוביות (x3)", style=discord.ButtonStyle.secondary, row=1)

    async def d20(self, intr, b): await self.run_dice(intr, 20)

    @discord.ui.button(label="🎲 30 קוביות (x5)", style=discord.ButtonStyle.danger, row=2)

    async def d30(self, intr, b): await self.run_dice(intr, 30)



class RussianRouletteBotGame(discord.ui.View):

    def __init__(self, player, bet): super().__init__(timeout=120.0); self.player = player; self.bet = bet; self.bullet_slot = random.randint(1, 8); self.current_slot = 1

    @discord.ui.button(label="💥 לחץ על ההדק!", style=discord.ButtonStyle.danger)

    async def shoot(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player: return

        if self.current_slot == self.bullet_slot:

            for child in self.children: child.disabled = True

            embed = discord.Embed(title="💀 בוווום!!!! 💀", description=f"לחצת על ההדק בסיבוב ה-{self.current_slot} והכדור נורה!\n\n🤖 **הבוט ניצח את הדו-קרב!**\nהפסדת **{self.bet}** טיקטים. הבית תמיד מנצח! 💸", color=discord.Color.red())

            await interaction.response.edit_message(embed=embed, view=self); self.stop(); return

        self.current_slot += 1

        await interaction.response.edit_message(content="🤖 הבוט לוקח את האקדח ומכוון לראש שלו...", view=None)

        await asyncio.sleep(1.5)

        if self.current_slot == self.bullet_slot:

            winnings = self.bet * 2; update_tickets(self.player.id, winnings)

            embed = discord.Embed(title="🎉 בוווום!!!! 🤖💥", description=f"הבוט לחץ על ההדק בסיבוב ה-{self.current_slot} והתפוצץ!\n\n👑 **ניצחת את הבוט!**\n🏆 זכית ב-**{winnings}** טיקטים לקופה שלך! 🎉", color=discord.Color.green())

            await interaction.followup.edit_message(message_id=interaction.message.id, content=None, embed=embed, view=self); self.stop(); return

        self.current_slot += 1

        embed = discord.Embed(title="🎯 קליק... שניכם שרדתם! 🎯", description=f"גם אתה וגם הבוט שרדתם!\nאנחנו בסיבוב: **{self.current_slot} / 8**\nהקופה: **{self.bet * 2}** 🎫\n\n👉 האקדח חוזר אליך! לחץ על ההדק!", color=discord.Color.orange())

        await interaction.followup.edit_message(message_id=interaction.message.id, content=None, embed=embed, view=self)



class RouletteChoiceView(discord.ui.View):

    def __init__(self, player, bet): super().__init__(timeout=60.0); self.player = player; self.bet = bet

    @discord.ui.button(label="🤖 שחק נגד הבוט (מיידי)", style=discord.ButtonStyle.primary)

    async def play_bot(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player: return

        update_tickets(self.player.id, -self.bet); view = RussianRouletteBotGame(self.player, self.bet)

        embed = discord.Embed(title="🔫 דו-קרב רולטה רוסית מול הבוט! 🔫", description=f"האקדח נטען בכדור אחד מתוך 8 מקומות!\nהימור: **{self.bet}** 🎫 | קופה פוטנציאלית: **{self.bet * 2}**\n\n🎯 אתה מתחיל ראשון! לחץ על ההדק!", color=discord.Color.red())

        await interaction.response.edit_message(embed=embed, view=view)

    @discord.ui.button(label="👥 שחק נגד חבר", style=discord.ButtonStyle.secondary)

    async def play_friend(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user != self.player: return

        await interaction.response.edit_message(content=f"ℹ️ כדי לשחק נגד חבר בשרת, תסגור את החלונית הזו ותכתוב בצ'אט את הפקודה:\n`/roulette member: @שם_החבר bet: {self.bet}`", embed=None, view=None)

class RussianRouletteInvite(discord.ui.View):

    def __init__(self, p1, p2, bet): super().__init__(timeout=60.0); self.p1 = p1; self.p2 = p2; self.bet = bet

    @discord.ui.button(label="⚔️ קבל את הדו-קרב", style=discord.ButtonStyle.danger)

    async def accept(self, i: discord.Interaction, b: discord.ui.Button):

        if i.user != self.p2: return

        u2 = get_user_data(self.p2.id)

        if u2["tickets"] < self.bet: await i.response.send_message("❌ אין לך מספיק טיקטים כדי לקבל את הדו-קרב הזה!", ephemeral=True); return

        await i.response.defer(); update_tickets(self.p2.id, -self.bet)

        for child in self.children: child.disabled = True

        game_view = RussianRouletteGame(self.p1, self.p2, self.bet)

        embed = discord.Embed(title="🔫 הדו-קרב התחיל! 🔫", description=f"הנשק נטען בכדור אחד במיקום רנדומלי מתוך 8!\nהקופה: **{self.bet * 2}** 🎫\n\n🎯 תורו של: {self.p1.mention} ללחוץ על ההדק!", color=discord.Color.red())

        await i.message.edit(embed=embed, view=game_view)



class RussianRouletteGame(discord.ui.View):

    def __init__(self, p1, p2, bet): super().__init__(timeout=180.0); self.p1 = p1; self.p2 = p2; self.bet = bet; self.bullet_slot = random.randint(1, 8); self.current_slot = 1; self.current_turn = p1

    @discord.ui.button(label="💥 לחץ על ההדק!", style=discord.ButtonStyle.danger)

    async def shoot(self, i: discord.Interaction, b: discord.ui.Button):

        if i.user != self.current_turn: return

        await i.response.defer() 
# ==========================================
# 🃏 משחק בלאק ג'ק (Blackjack) מתוקן
# ==========================================

import random

def calculate_hand(hand):
    val = 0
    aces = 0
    for card in hand:
        rank = card[:-1]
        if rank in ["J", "Q", "K"]:
            val += 10
        elif rank == "A":
            aces += 1
            val += 11
        else:
            val += int(rank)
    
    while val > 21 and aces > 0:
        val -= 10
        aces -= 1
    return val

class BlackjackGame:
    def __init__(self, bet, user_id):
        self.bet = bet
        self.user_id = user_id
        suits = ["♠", "♣", "♥", "♦"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        self.deck = [f"{r}{s}" for s in suits for r in ranks]
        random.shuffle(self.deck)
        
        self.player_hand = [self.deck.pop(), self.deck.pop()]
        self.dealer_hand = [self.deck.pop(), self.deck.pop()]
        self.game_over = False

class BlackjackModal(discord.ui.Modal, title="🃏 שולחן בלאק ג'ק"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            return await interaction.response.send_message("אנא הכנס מספר תקין בלבד!", ephemeral=True)

        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0:
            return await interaction.response.send_message("אין לך מספיק טיקטים להימור זה!", ephemeral=True)

        update_tickets(interaction.user.id, -bet)
        game = BlackjackGame(bet, interaction.user.id)

        p_val = calculate_hand(game.player_hand)
        
        # בדיקת בלאק ג'ק מידי בהתחלה
        if p_val == 21:
            game.game_over = True
            winnings = int(game.bet * 2.5)
            update_tickets(game.user_id, winnings)
            embed = discord.Embed(
                title="🃏 בלאק ג'ק - ניצחון!",
                description=(
                    f"**הימור:** {game.bet} טיקטים\n"
                    f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: 21)\n"
                    f"🏆 **בלאק ג'ק מושלם!** זכית ב-**{winnings}** טיקטים!"
                ),
                color=discord.Color.gold()
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        embed = discord.Embed(
            title="🃏 שולחן בלאק ג'ק",
            description=(
                f"**הימור:** {game.bet} טיקטים\n\n"
                f"**הקלף הגלוי של הדילר:** ` {game.dealer_hand[0]} | 🎴 `\n"
                f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: {p_val})\n\n"
                f"בחר את הפעולה שלך למטה:"
            ),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(
            embed=embed,
            view=BlackjackView(game),
            ephemeral=True
        )

class BlackjackView(discord.ui.View):
    def __init__(self, game: BlackjackGame):
        super().__init__(timeout=120)
        self.game = game

        # האם ניתן לעשות Double Down (רק בהתחלה - 2 קלפים)
        can_double = len(self.game.player_hand) == 2 and not self.game.game_over
        # האם ניתן לעשות Split (שני קלפים ראשונים בעלי אותו ערך/אותה אות)
        can_split = len(self.game.player_hand) == 2 and self.game.player_hand[0][:-1] == self.game.player_hand[1][:-1] and not self.game.game_over

        # כפתור קח קלף (Hit)
        self.add_item(BlackjackActionButton("hit", "קח קלף 📥", discord.ButtonStyle.primary, self.game.game_over))
        # כפתור עמוד (Stand)
        self.add_item(BlackjackActionButton("stand", "עמוד 🛑", discord.ButtonStyle.secondary, self.game.game_over))
        # כפתור הכפל (Double) - אפור אם לא זמין
        self.add_item(BlackjackActionButton("double", "הכפל ✖️2", discord.ButtonStyle.secondary, not can_double))
        # כפתור פיצול (Split) - אפור אם לא זמין
        self.add_item(BlackjackActionButton("split", "פיצול ✂️", discord.ButtonStyle.secondary, not can_split))

class BlackjackActionButton(discord.ui.Button):
    def __init__(self, action: str, label: str, style: discord.ButtonStyle, disabled: bool):
        super().__init__(label=label, style=style, disabled=disabled)
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: BlackjackView = self.view
        game = view.game
        if interaction.user.id != game.user_id:
            return

        u = get_user_data(game.user_id)

        if self.action == "hit":
            game.player_hand.append(game.deck.pop())
            p_val = calculate_hand(game.player_hand)
            
            if p_val > 21:
                game.game_over = True
                embed = discord.Embed(
                    title="🃏 בלאק ג'ק - הפסד",
                    description=(
                        f"**הימור:** {game.bet} טיקטים\n"
                        f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: {p_val})\n"
                        f"💥 **עברת את 21!** הפסדת את ההימור."
                    ),
                    color=discord.Color.red()
                )
                return await interaction.edit_original_response(embed=embed, view=BlackjackView(game))

            embed = discord.Embed(
                title="🃏 שולחן בלאק ג'ק",
                description=(
                    f"**הימור:** {game.bet} טיקטים\n\n"
                    f"**הקלף הגלוי של הדילר:** ` {game.dealer_hand[0]} | 🎴 `\n"
                    f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: {p_val})\n\n"
                    f"בחר את הפעולה שלך למטה:"
                ),
                color=discord.Color.blue()
            )
            await interaction.edit_original_response(embed=embed, view=BlackjackView(game))

        elif self.action == "stand":
            game.game_over = True
            # תור הדילר
            dealer_val = calculate_hand(game.dealer_hand)
            while dealer_val < 17:
                game.dealer_hand.append(game.deck.pop())
                dealer_val = calculate_hand(game.dealer_hand)

            p_val = calculate_hand(game.player_hand)
            
            if dealer_val > 21 or p_val > dealer_val:
                winnings = game.bet * 2
                update_tickets(game.user_id, winnings)
                result_text = f"🏆 **ניצחת!** זכית ב-**{winnings}** טיקטים!"
                color = discord.Color.green()
            elif p_val == dealer_val:
                update_tickets(game.user_id, game.bet)
                result_text = f"🤝 **תיקו!** ההימור הוחזר אליך."
                color = discord.Color.gold()
            else:
                result_text = f"❌ **הדילר ניצח!** הפסדת את ההימור."
                color = discord.Color.red()

            embed = discord.Embed(
                title="🃏 תוצאת בלאק ג'ק",
                description=(
                    f"**הימור:** {game.bet} טיקטים\n"
                    f"**היד של הדילר:** ` {' | '.join(game.dealer_hand)} ` (סכום: {dealer_val})\n"
                    f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: {p_val})\n\n"
                    f"{result_text}"
                ),
                color=color
            )
            await interaction.edit_original_response(embed=embed, view=BlackjackView(game))

        elif self.action == "double":
            if u["tickets"] < game.bet:
                return await interaction.followup.send("אין לך מספיק טיקטים כדי להכפל את ההימור!", ephemeral=True)
            
            update_tickets(game.user_id, -game.bet)
            game.bet *= 2
            game.player_hand.append(game.deck.pop())
            game.game_over = True

            p_val = calculate_hand(game.player_hand)
            dealer_val = calculate_hand(game.dealer_hand)
            while dealer_val < 17:
                game.dealer_hand.append(game.deck.pop())
                dealer_val = calculate_hand(game.dealer_hand)

            if p_val <= 21 and (dealer_val > 21 or p_val > dealer_val):
                winnings = game.bet * 2
                update_tickets(game.user_id, winnings)
                result_text = f"🏆 **ניצחת לאחר הכפלה!** זכית ב-**{winnings}** טיקטים!"
                color = discord.Color.green()
            elif p_val <= 21 and p_val == dealer_val:
                update_tickets(game.user_id, game.bet)
                result_text = f"🤝 **תיקו לאחר הכפלה!** ההימור הוחזר."
                color = discord.Color.gold()
            else:
                result_text = f"❌ **הפסדת לאחר הכפלה!**"
                color = discord.Color.red()

            embed = discord.Embed(
                title="🃏 תוצאת בלאק ג'ק (הכפלה)",
                description=(
                    f"**הימור מעודכן:** {game.bet} טיקטים\n"
                    f"**היד של הדילר:** ` {' | '.join(game.dealer_hand)} ` (סכום: {dealer_val})\n"
                    f"**היד שלך:** ` {' | '.join(game.player_hand)} ` (סכום: {p_val})\n\n"
                    f"{result_text}"
                ),
                color=color
            )
            await interaction.edit_original_response(embed=embed, view=BlackjackView(game))
# ==========================================
# 💣 מערכת משחק Mines מלאה ומתוקנת
# ==========================================

import discord
import random

# 1. חלון ההגדרות (Modal) שנפתח בלחיצה על כפתור ה-Mines
class MinesSetupModal(discord.ui.Modal, title="💣 הגדרת משחק Mines"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(
            label="כמות טיקטים להימור", 
            placeholder="הכנס סכום...", 
            required=True
        )
        self.size_input = discord.ui.TextInput(
            label="גודל לוח (3, 4, 5, 6, 7 או 8)", 
            placeholder="לדוגמה: 5 (עבור 5x5)", 
            required=True, 
            max_length=1
        )
        self.mines_input = discord.ui.TextInput(
            label="כמות פצצות", 
            placeholder="כמות פצצות בהתאם לגודל הלוח", 
            required=True, 
            max_length=2
        )
        
        self.add_item(self.bet_input)
        self.add_item(self.size_input)
        self.add_item(self.mines_input)

    async def on_submit(self, interaction: discord.Interaction):
        # בדיקות תקינות קלט
        try:
            bet = int(self.bet_input.value)
            grid_size = int(self.size_input.value)
            bombs_count = int(self.mines_input.value)
        except ValueError:
            return await interaction.response.send_message("❌ אנא הכנס מספרים תקינים בלבד!", ephemeral=True)

        if grid_size not in [3, 4, 5, 6, 7, 8]:
            return await interaction.response.send_message("❌ גודל הלוח חייב להיות אחד מהבאים בלבד: 3, 4, 5, 6, 7 או 8!", ephemeral=True)

        total_tiles = grid_size * grid_size
        if not (1 <= bombs_count < total_tiles):
            return await interaction.response.send_message(f"❌ כמות הפצצות חייבת להיות בין 1 ל-{total_tiles - 1} בלוח בגודל {grid_size}x{grid_size}!", ephemeral=True)

        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0:
            return await interaction.response.send_message("❌ אין לך מספיק טיקטים להימור זה!", ephemeral=True)

        # הורדת הטיקטים ויצירת המיקומים של הפצצות
        update_tickets(interaction.user.id, -bet)
        bomb_positions = random.sample(range(total_tiles), bombs_count)

        embed = discord.Embed(
            title=f"🎲 Mines Game ({grid_size}x{grid_size})",
            description=(
                f"**הימור:** {bet} טיקטים\n"
                f"**פצצות:** {bombs_count}\n"
                f"**מכפיל:** x1.00\n"
                f"**נשארו לבחירה:** {total_tiles - bombs_count}\n"
                f"**סטטוס:** בחר משבצת ❓"
            ),
            color=discord.Color.dark_embed()
        )
        await interaction.response.send_message(
            embed=embed, 
            view=MinesDynamicView(bet, grid_size, bombs_count, bomb_positions, interaction.user.id), 
            ephemeral=True
        )


# 2. כפתור שמוסיפים לתפריד המשחקים הראשי שלך כדי לפתוח את ה-Modal בלי שגיאות
class OpenMinesModalButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="💣 מיין (Mines)", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        # שולח את ה-Modal מיד ובצורה ישירה למניעת Timeout
        await interaction.response.send_modal(MinesSetupModal())


# 3. הלוח הדינמי של המשחק (כפתורים ומשבצות)
class MinesDynamicView(discord.ui.View):
    def __init__(self, bet, grid_size, bombs_count, bomb_positions, user_id, revealed=None, game_over=False):
        super().__init__(timeout=180)
        self.bet = bet
        self.grid_size = grid_size
        self.bombs_count = bombs_count
        self.bomb_positions = bomb_positions
        self.user_id = user_id
        self.revealed = revealed if revealed else set()
        self.game_over = game_over
        total_tiles = grid_size * grid_size

        for i in range(total_tiles):
            row_num = i // grid_size
            if self.game_over:
                if i in self.bomb_positions:
                    label, style, disabled = "💣", discord.ButtonStyle.danger, True
                elif i in self.revealed:
                    label, style, disabled = "💎", discord.ButtonStyle.success, True
                else:
                    label, style, disabled = "❓", discord.ButtonStyle.secondary, True
            else:
                if i in self.revealed:
                    label, style, disabled = "💎", discord.ButtonStyle.success, True
                else:
                    label, style, disabled = "❓", discord.ButtonStyle.secondary, False

            self.add_item(MinesDynamicButton(i, label, style, disabled, row=row_num))

        if not self.game_over and len(self.revealed) > 0:
            self.add_item(MinesDynamicCashOut(row=grid_size - 1 if grid_size < 5 else 4))


class MinesDynamicButton(discord.ui.Button):
    def __init__(self, index, label, style, disabled, row):
        super().__init__(label=label, style=style, disabled=disabled, row=row)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: MinesDynamicView = self.view
        if interaction.user.id != view.user_id:
            return

        total_tiles = view.grid_size * view.grid_size

        # פגיעה במוקש - הפסד
        if self.index in view.bomb_positions:
            view.game_over = True
            embed = discord.Embed(
                title=f"🎲 Mines Game ({view.grid_size}x{view.grid_size})",
                description=f"**הימור:** {view.bet} טיקטים\n**סטטוס:** 💥 פגעת במוקש והפסדת את ההימור!",
                color=discord.Color.red()
            )
            new_view = MinesDynamicView(view.bet, view.grid_size, view.bombs_count, view.bomb_positions, view.user_id, view.revealed, game_over=True)
            return await interaction.edit_original_response(embed=embed, view=new_view)

        if self.index not in view.revealed:
            view.revealed.add(self.index)

        safe_picked = len(view.revealed)
        multiplier = round(1.0 + (safe_picked * 0.20 * (view.bombs_count / 3 + 1)), 2)
        potential_win = int(view.bet * multiplier)

        # ניצחון (פתיחת כל המשבצות הבטוחות)
        if safe_picked == (total_tiles - view.bombs_count):
            update_tickets(view.user_id, potential_win)
            embed = discord.Embed(
                title=f"🎲 Mines Game ({view.grid_size}x{view.grid_size})",
                description=f"**מכפיל סופי:** x{multiplier}\n🏆 זכית ב-**{potential_win}** טיקטים!",
                color=discord.Color.gold()
            )
            new_view = MinesDynamicView(view.bet, view.grid_size, view.bombs_count, view.bomb_positions, view.user_id, view.revealed, game_over=True)
            return await interaction.edit_original_response(embed=embed, view=new_view)

        embed = discord.Embed(
            title=f"🎲 Mines Game ({view.grid_size}x{view.grid_size})",
            description=(
                f"**הימור:** {view.bet} טיקטים\n"
                f"**מכפיל:** x{multiplier}\n"
                f"**זכייה פוטנציאלית:** {potential_win} טיקטים\n"
                f"**סטטוס:** בחר משבצת נוספת 💎"
            ),
            color=discord.Color.green()
        )
        new_view = MinesDynamicView(view.bet, view.grid_size, view.bombs_count, view.bomb_positions, view.user_id, view.revealed, game_over=False)
        await interaction.edit_original_response(embed=embed, view=new_view)


class MinesDynamicCashOut(discord.ui.Button):
    def __init__(self, row):
        super().__init__(label="💰 Cash Out", style=discord.ButtonStyle.success, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: MinesDynamicView = self.view
        if interaction.user.id != view.user_id:
            return

        safe_picked = len(view.revealed)
        multiplier = round(1.0 + (safe_picked * 0.20 * (view.bombs_count / 3 + 1)), 2)
        winnings = int(view.bet * multiplier)

        update_tickets(view.user_id, winnings)
        view.game_over = True

        embed = discord.Embed(
            title="🎲 Mines Game (Cash Out)",
            description=f"💰 פרשת בזמן עם מכפיל x{multiplier} וזכית ב-**{winnings}** טיקטים!",
            color=discord.Color.green()
        )
        new_view = MinesDynamicView(view.bet, view.grid_size, view.bombs_count, view.bomb_positions, view.user_id, view.revealed, game_over=True)
        await interaction.edit_original_response(embed=embed, view=new_view)
# ==========================================
#         🎰 משחק 3: רולטה (Roulette)
# ==========================================

class RouletteModal(discord.ui.Modal, title="🎰 רולטה - הימור"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try: bet = int(self.bet_input.value)
        except ValueError: return
        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0: return

        update_tickets(interaction.user.id, -bet)
        embed = discord.Embed(title="🎰 שולחן הרולטה", description=f"הימור: **{bet}** טיקטים. בחר צבע:", color=discord.Color.purple())
        await interaction.response.send_message(embed=embed, view=RouletteView(bet, interaction.user.id), ephemeral=True)

class RouletteView(discord.ui.View):
    def __init__(self, bet, user_id):
        super().__init__(timeout=60)
        self.bet, self.user_id = bet, user_id

    async def play(self, interaction: discord.Interaction, choice: str):
        if interaction.user.id != self.user_id: return
        number = random.randint(0, 36)
        
        # הגדרת מספרים אדומים
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        
        if number == 0: color = "ירוק"
        elif number in red_numbers: color = "אדום"
        else: color = "שחור"

        win = (choice == color)
        payout = self.bet * 14 if color == "ירוק" else self.bet * 2

        for child in self.children: child.disabled = True
        embed = discord.Embed(title=f"🎰 הגלגל נחת על {number} ({color})")
        if win:
            update_tickets(self.user_id, payout)
            embed.color, embed.description = discord.Color.green(), f"🎉 זכית ב-**{payout}** טיקטים!"
        else:
            embed.color, embed.description = discord.Color.red(), f"❌ הפסדת {self.bet} טיקטים."
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔴 אדום (x2)", style=discord.ButtonStyle.danger)
    async def red(self, interaction: discord.Interaction, b: discord.ui.Button): await self.play(interaction, "אדום")
    @discord.ui.button(label="⚫ שחור (x2)", style=discord.ButtonStyle.secondary)
    async def black(self, interaction: discord.Interaction, b: discord.ui.Button): await self.play(interaction, "שחור")
    @discord.ui.button(label="🟢 ירוק 0 (x14)", style=discord.ButtonStyle.success)
    async def green(self, interaction: discord.Interaction, b: discord.ui.Button): await self.play(interaction, "ירוק")
# ==========================================
# 🗼 משחק 4: טאואר (Tower)
# ==========================================

class TowerModal(discord.ui.Modal, title="🗼 משחק טאואר"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try: 
            bet = int(self.bet_input.value)
        except ValueError: 
            return
        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0: return

        update_tickets(interaction.user.id, -bet)
        # 4 תאים בכל שורה (אינדקסים 0 עד 3), מתוכם פצצה 1 אקראית
        tower_data = [random.randint(0, 3) for _ in range(5)]
        
        embed = discord.Embed(
            title="🗼 מגדל הטאואר - קומה 1", 
            description=f"הימור: **{bet}** טיקטים.\n⚠️ בכל שורה יש **פצצה אחת** מתוך 4 תאים!\nבחר תא בטוח כדי לטפס למעלה!", 
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=TowerView(tower_data, 0, bet, interaction.user.id), ephemeral=True)

class TowerView(discord.ui.View):
    multipliers = [1.3, 1.8, 2.5, 3.8, 5.5]
    def __init__(self, tower_data, floor, bet, user_id):
        super().__init__(timeout=90)
        self.tower_data, self.floor, self.bet, self.user_id = tower_data, floor, bet, user_id
        
        # יצירת 4 כפתורים במקום 3
        for i in range(4): 
            self.add_item(TowerButton(i))
            
        if self.floor > 0: 
            self.add_item(TowerCashout())

class TowerButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(label=f"❓ תא {index+1}", style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("זה לא המשחק שלך!", ephemeral=True)

        if self.index == view.tower_data[view.floor]:
            embed = discord.Embed(title="💥 המגדל קרס! פגעת במלכודת!", description=f"הפסדת {view.bet} טיקטים בקומה {view.floor + 1}.", color=discord.Color.red())
            for child in view.children: 
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        view.floor += 1
        if view.floor == 5:
            winnings = int(view.bet * 5.5)
            update_tickets(view.user_id, winnings)
            embed = discord.Embed(title="🏆 כבשת את הטאואר!", description=f"הגעת לפסגה! זכית ב-**{winnings}** טיקטים!", color=discord.Color.gold())
            for child in view.children: 
                child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        embed = discord.Embed(
            title=f"🗼 מגדל הטאואר - קומה {view.floor + 1}", 
            description=f"עלית קומה! מכפיל נוכחי: **{view.multipliers[view.floor-1]}x**\n⚠️ בכל שורה יש **פצצה אחת** מתוך 4 תאים!", 
            color=discord.Color.blue()
        )
        await interaction.response.edit_message(embed=embed, view=TowerView(view.tower_data, view.floor, view.bet, view.user_id))

class TowerCashout(discord.ui.Button):
    def __init__(self): 
        super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.success, row=1)
        
    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        if interaction.user.id != view.user_id:
            return await interaction.response.send_message("זה לא המשחק שלך!", ephemeral=True)
            
        winnings = int(view.bet * view.multipliers[view.floor - 1])
        update_tickets(view.user_id, winnings)
        embed = discord.Embed(title="💰 משיכת כסף מושלמת!", description=f"פרשת בזמן וזכית ב-**{winnings}** טיקטים!", color=discord.Color.green())
        for child in view.children: 
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)
# ==========================================
# 👑 משחק פוקר (Video Poker) מתוקן
# ==========================================

import random

# ערכות קלפים פשוטות להמחשה
SUITS = ["♠", "♣", "♥", "♦"]
VALUES = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

def deal_hand():
    deck = [f"{v}{s}" for s in SUITS for v in VALUES]
    random.shuffle(deck)
    return [deck.pop() for _ in range(5)], deck

class PokerGame:
    def __init__(self, bet, user_id):
        self.bet = bet
        self.user_id = user_id
        self.hand, self.deck = deal_hand()
        self.held = [False] * 5
        self.game_over = False

class PokerModal(discord.ui.Modal, title="👑 שולחן הפוקר"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try:
            bet = int(self.bet_input.value)
        except ValueError:
            return await interaction.response.send_message("אנא הכנס מספר תקינים בלבד!", ephemeral=True)

        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0:
            return await interaction.response.send_message("אין לך מספיק טיקטים להימור זה!", ephemeral=True)

        update_tickets(interaction.user.id, -bet)
        game = PokerGame(bet, interaction.user.id)

        cards_str = " | ".join(game.hand)
        embed = discord.Embed(
            title="👑 שולחן הפוקר",
            description=(
                f"**הימור:** {bet} טיקטים\n"
                f"**היד הראשונית שלך:**\n` {cards_str} `\n\n"
                f"סמן קלפים שברצונך לנעול 🔒 ולחץ על כפתור ההחלפה:"
            ),
            color=discord.Color.gold()
        )
        await interaction.response.send_message(
            embed=embed,
            view=PokerHoldView(game),
            ephemeral=True
        )

class PokerHoldView(discord.ui.View):
    def __init__(self, game: PokerGame):
        super().__init__(timeout=120)
        self.game = game

        # 5 כפתורים לסימון/נעילת קלפים (Hold)
        for i in range(5):
            is_held = self.game.held[i]
            label = f"קлף {i+1} (נצור 🔒)" if is_held else f"קוף {i+1}"
            style = discord.ButtonStyle.secondary if not is_held else discord.ButtonStyle.primary
            self.add_item(PokerCardButton(i, label, style))

        # כפתור החלפת קלפים בעברית
        self.add_item(PokerSwapButton())

class PokerCardButton(discord.ui.Button):
    def __init__(self, index, label, style):
        super().__init__(label=label, style=style, row=0)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: PokerHoldView = self.view
        if interaction.user.id != view.game.user_id:
            return

        # שינוי מצב נעילה (Hold / Unhold)
        view.game.held[self.index] = not view.game.held[self.index]
        
        # יצירת תצוגה מעודכנת
        new_view = PokerHoldView(view.game)
        cards_str = " | ".join([f"**{c}** (🔒)" if view.game.held[i] else c for i, c in enumerate(view.game.hand)])
        
        embed = discord.Embed(
            title="👑 שולחן הפוקר",
            description=(
                f"**הימור:** {view.game.bet} טיקטים\n"
                f"**היד שלך:**\n` {cards_str} `\n\n"
                f"סמן קלפים שברצונך לנעול 🔒 ולחץ על כפתור ההחלפה:"
            ),
            color=discord.Color.gold()
        )
        await interaction.edit_original_response(embed=embed, view=new_view)

class PokerSwapButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🔀 החלף קלפים וסיים סיבוב", style=discord.ButtonStyle.success, row=1)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: PokerHoldView = self.view
        game = view.game
        if interaction.user.id != game.user_id:
            return

        # החלפת קלפים שלא סומנו בנעילה
        for i in range(5):
            if not game.held[i]:
                game.hand[i] = game.deck.pop()

        game.game_over = True
        winnings = game.bet * 2 # דוגמה לחישוב זכייה בסיסית
        update_tickets(game.user_id, winnings)

        cards_str = " | ".join(game.hand)
        embed = discord.Embed(
            title="👑 תוצאת הפוקר",
            description=(
                f"**הימור:** {game.bet} טיקטים\n"
                f"**היד הסופית שלך:**\n` {cards_str} `\n\n"
                f"🏆 הסיבוב הסתיים! זכית ב-**{winnings}** טיקטים!"
            ),
            color=discord.Color.green()
        )
        
        # ניטרול כל הכפתורים בסיום
        for child in view.children:
            child.disabled = True

        await interaction.edit_original_response(embed=embed, view=view)

# ==========================================
#     🎮 לוח המשחקים הציבורי של השרת
# ==========================================

class CasinoPublicLobbyView(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary, custom_id="lobby_bj")
    async def bj_click(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(BlackjackModal())
    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary, custom_id="lobby_tw")
    async def tw_click(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(TowerModal())
    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary, custom_id="lobby_mn")
    async def mn_click(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(MinesModal())
    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary, custom_id="lobby_rl")
    async def rl_click(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(RouletteModal())
    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary, custom_id="lobby_pk")
    async def pk_click(self, interaction: discord.Interaction, b: discord.ui.Button): await interaction.response.send_modal(PokerModal())

# ==========================================
#        👑 פאנלים ומערכות ניהול אזולאי
# ==========================================

class AzoulaiManageModal(discord.ui.Modal):
    def __init__(self, action_type):
        super().__init__(title=f"ניהול - {action_type}")
        self.action_type = action_type
        self.user_input = discord.ui.TextInput(label="הזן מזהה משתמש (ID)", placeholder="הכנס ID...", required=True)
        self.add_item(self.user_input)
        if "טוקנים" in action_type:
            self.amount_input = discord.ui.TextInput(label="כמות טיקטים", placeholder="לדוגמה: 50")
            self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await handle_security_breach(interaction, f"Modal-{self.action_type}")
            return
        try: target_id = int(self.user_input.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ מזהה משתמש לא חוקי.", ephemeral=True)
            return
        if "טוקנים" in self.action_type:
            try: amt = int(self.amount_input.value.strip())
            except ValueError: return
            update_tickets(target_id, amt)
            await interaction.response.send_message(f"✅ נוספו {amt} טיקטים ל-<@{target_id}>.", ephemeral=True)
        else:
            try:
                member = await interaction.guild.fetch_member(target_id)
                await interaction.guild.ban(member, reason="פאנל אזולאי")
                await interaction.response.send_message(f"🔨 בוצע באן ל-{member.mention}.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ שגיאה: {e}", ephemeral=True)

class AzoulaiAdminPanelButtons(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔨 באנים וקיקים", style=discord.ButtonStyle.danger, custom_id="az_ban")
    async def b_click(self, interaction: discord.Interaction, b: discord.ui.Button):
        if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "כפתור באן"); return
        await interaction.response.send_modal(AzoulaiManageModal("באן ליום"))
    @discord.ui.button(label="🪙 ניהול טוקנים", style=discord.ButtonStyle.success, custom_id="az_tok")
    async def t_click(self, interaction: discord.Interaction, b: discord.ui.Button):
        if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "כפתור טוקנים"); return
        await interaction.response.send_modal(AzoulaiManageModal("ניהול טוקנים"))

# ==========================================
#             🚀 פקודות סלאש סופיות
# ==========================================

@bot.tree.command(name="פאנל_אזולאי", description="לוח בקרה סודי ומורחב רק בשבילך")
async def panel_azoulai(interaction: discord.Interaction):
    if interaction.user.id != OWNER_ID:
        await handle_security_breach(interaction, "/פאנל_אזולאי")
        return
    embed = discord.Embed(title="👑 פאנל אזולאי - Ticket Royale", description="מערכת ניהול בלעדית:", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed, view=AzoulaiAdminPanelButtons(), ephemeral=True)

@bot.tree.command(name="משחקים", description="הצגת לוח משחקי הקזינו לחברי השרת")
async def panel_public(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    embed = discord.Embed(title="🎰 קזינו Ticket Royale", description="כל המשחקים פעילים! לחצו למטה כדי להמר ולשחק:", color=discord.Color.purple())
    await interaction.response.send_message(embed=embed, view=CasinoPublicLobbyView(), ephemeral=False)

@bot.tree.command(name="דיילי", description="קבל 20 טיקטים חינם בכל 24 שעות")
async def daily(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    user_id = interaction.user.id
    data = load_data()
    uid_str = str(user_id)
    now = datetime.now(timezone.utc)
    
    u = get_user_data(user_id)
    if u.get("last_daily"):
        last_claim = datetime.fromisoformat(u["last_daily"]).replace(tzinfo=timezone.utc)
        if now < last_claim + timedelta(hours=24):
            tl = (last_claim + timedelta(hours=24)) - now
            h, rem = divmod(tl.seconds, 3600); m, _ = divmod(rem, 60)
            await interaction.response.send_message(f"❌ תוכל לאסוף שוב בעוד {h} שעות ו-{m} דקות.", ephemeral=True)
            return

    update_tickets(user_id, 20)
    data = load_data()
    data[uid_str]["last_daily"] = now.isoformat()
    save_data(data)
    await interaction.response.send_message(f"🪙 קיבלת **20 טיקטים** חינם! המאזן שלך: **{get_user_data(user_id)['tickets']}** טיקטים.")
# ==========================================
# 🎟️ סיסטעם פון קופאנס און דראפ (Drop)
# ==========================================

COUPONS = {} # מבנה: {"CODE": {"amount": 100, "used_by": []}}
OWNER_ID = 1260675229626273802

@app_commands.command(name="יצירת_קוד_קופון", description="שאפן א נייעם קופאן-קאוד (נאר פארן אדמיניסטראטאר)")
@app_commands.describe(code="דער קופאן-קאוד", amount="די צאָל טיקעטן")
async def create_coupon(interaction: discord.Interaction, code: str, amount: int):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ נאר דער באזיצער פונעם באט קען שאפן קופאן-קאודס!", ephemeral=True)
    
    COUPONS[code.upper()] = {"amount": amount, "used_by": []}
    await interaction.response.send_message(f"✅ דער קופאן `{code.upper()}` מיט **{amount}** טיקעטן איז ערפאלגרייך געשאפן געווארן!", ephemeral=True)

@app_commands.command(name="קוד_קופון", description="באנוצן זיך מיט א קופאן-קאוד צו באקומען טיקעטן")
@app_commands.describe(code="אריינלייגן דעם קופאן-קאוד")
async def redeem_coupon(interaction: discord.Interaction, code: str):
    code_upper = code.upper()
    if code_upper not in COUPONS:
        return await interaction.response.send_message("❌ דער קופאן-קאוד עקזיסטירט נישט אדער ער האט שוין פארלוירן זיין תוקף.", ephemeral=True)
    
    coupon = COUPONS[code_upper]
    if interaction.user.id in coupon["used_by"]:
        return await interaction.response.send_message("❌ איר האט שוין באנוצט דעם קופאן אין דער פארגאנגענהייט!", ephemeral=True)

    coupon["used_by"].append(interaction.user.id)
    update_tickets(interaction.user.id, coupon["amount"])
    
    await interaction.response.send_message(f"🎉 א גרויסן יישר כוח! איר האט ערפאלגרייך באנוצט דעם קופאן און באקומען **{coupon['amount']}** טיקעטן!", ephemeral=True)

@app_commands.command(name="drop", description="צעשפרייטן טיקעטן אינעם צימער (נאר פארן אדמיניסטראטאר)")
@app_commands.describe(amount="די צאָל טיקעטן אינעם דראפ")
async def drop_tickets(interaction: discord.Interaction, amount: int):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("❌ נאר דער באזיצער פונעם באט קען מאכן א דראפ!", ephemeral=True)

    embed = discord.Embed(
        title="🎁 א נייע טיקעטן-דראפ!",
        description=f"עמיצער האט דא צעשפרייט **{amount}** טיקעטן!\nדריקט אויף דעם קנעפל אונטן צו זיי כאפן ערשטער!",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=DropView(amount))

class DropView(discord.ui.View):
    def __init__(self, amount):
        super().__init__(timeout=None)
        self.amount = amount
        self.claimed = False

    @discord.ui.button(label="כאפּ טיקעטן 💰", style=discord.ButtonStyle.success)
    async def claim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.claimed:
            return await interaction.response.send_message("❌ די טיקעטן זענען שוין צוגענומען געווארן דורך עמיצער אנדערש!", ephemeral=True)
        
        self.claimed = True
        update_tickets(interaction.user.id, self.amount)
        
        for child in self.children:
            child.disabled = True

        embed = interaction.message.embeds[0]
        embed.description = f"🎁 דער דראפ איז ערפאלגרייך צוגענומען געווארן דורך {interaction.user.mention}! ער האט געווינען **{self.amount}** טיקעטן."
        embed.color = discord.Color.dark_gray()
        
        await interaction.response.edit_message(embed=embed, view=self)
# ==========================================
#          🤖 הפעלת הבוט המלאה
# ==========================================

keep_alive()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    bot.run("החלף_בטוקן_הסודי_האמיתי_שלך")
