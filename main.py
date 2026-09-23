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
#         🃏 משחק 1: בלאק ג'ק (Blackjack)
# ==========================================

class BlackjackModal(discord.ui.Modal, title="🃏 בלאק ג'ק - הימור"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.add_item(self.bet_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try: bet = int(self.bet_input.value)
        except ValueError:
            await interaction.response.send_message("❌ נא להזין מספר תקין.", ephemeral=True)
            return

        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0:
            await interaction.response.send_message(f"❌ אין לך מספיק טיקטים! (יש לך {u['tickets']})", ephemeral=True)
            return

        update_tickets(interaction.user.id, -bet)
        deck = [2,3,4,5,6,7,8,9,10,10,10,10,11] * 4
        random.shuffle(deck)
        player_cards = [deck.pop(), deck.pop()]
        dealer_cards = [deck.pop(), deck.pop()]

        view = BlackjackView(bet, player_cards, dealer_cards, deck)
        await interaction.response.send_message(embed=view.create_embed(interaction.user), view=view, ephemeral=True)

class BlackjackView(discord.ui.View):
    def __init__(self, bet, player_cards, dealer_cards, deck):
        super().__init__(timeout=60)
        self.bet, self.player_cards, self.dealer_cards, self.deck = bet, player_cards, dealer_cards, deck

    def calculate_score(self, cards):
        score = sum(cards)
        aces = cards.count(11)
        while score > 21 and aces: score -= 10; aces -= 1
        return score

    def create_embed(self, user, finished=False):
        p_score = self.calculate_score(self.player_cards)
        embed = discord.Embed(title="🃏 קזינו Ticket Royale - בלאק ג'ק", color=discord.Color.dark_gold())
        embed.add_field(name="הקלפים שלך", value=f"{self.player_cards} (ניקוד: {p_score})", inline=False)
        embed.add_field(name="הקלפים של הדילר", value=f"{self.dealer_cards if finished else [self.dealer_cards[0], '?']}", inline=False)
        return embed

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player_cards.append(self.deck.pop())
        if self.calculate_score(self.player_cards) > 21:
            for child in self.children: child.disabled = True
            await interaction.response.edit_message(content="💥 עברת את 21! הפסדת.", embed=self.create_embed(interaction.user, True), view=self)
        else:
            await interaction.response.edit_message(embed=self.create_embed(interaction.user), view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        while self.calculate_score(self.dealer_cards) < 17: self.dealer_cards.append(self.deck.pop())
        ps, ds = self.calculate_score(self.player_cards), self.calculate_score(self.dealer_cards)
        for child in self.children: child.disabled = True
        
        if ds > 21 or ps > ds:
            update_tickets(interaction.user.id, self.bet * 2)
            msg = f"🎉 ניצחת! זכית ב-{self.bet * 2} טיקטים!"
        elif ps == ds:
            update_tickets(interaction.user.id, self.bet)
            msg = "🤝 תיקו! הטיקטים הוחזרו."
        else:
            msg = f"❌ הפסדת {self.bet} טיקטים."
        await interaction.response.edit_message(content=msg, embed=self.create_embed(interaction.user, True), view=self)
# ==========================================
#         💣 משחק 2: מכרות (Mines)
# ==========================================

class MinesModal(discord.ui.Modal, title="💣 משחק מכרות (Mines)"):
    def __init__(self):
        super().__init__()
        self.bet_input = discord.ui.TextInput(label="כמות טיקטים להימור", placeholder="הכנס סכום...", required=True)
        self.bombs_input = discord.ui.TextInput(label="כמות פצצות (1-24)", placeholder="הכנס מספר פצצות...", required=True)
        self.add_item(self.bet_input)
        self.add_item(self.bombs_input)

    async def on_submit(self, interaction: discord.Interaction):
        if is_user_banned(interaction.user.id): return
        try:
            bet = int(self.bet_input.value)
            bombs = int(self.bombs_input.value)
        except ValueError: return
        if bombs < 1 or bombs > 24: return
        
        u = get_user_data(interaction.user.id)
        if u["tickets"] < bet or bet <= 0: return

        update_tickets(interaction.user.id, -bet)
        grid = [0] * 25
        for pos in random.sample(range(25), bombs): grid[pos] = 1

        view = MinesView(bet, bombs, grid, interaction.user.id)
        await interaction.response.send_message(embed=view.create_embed(), view=view, ephemeral=True)

class MinesTileButton(discord.ui.Button):
    def __init__(self, index: int):
        super().__init__(label="❓", style=discord.ButtonStyle.secondary, row=index // 5)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: MinesView = self.view
        if interaction.user.id != view.user_id or self.label != "❓": return

        if view.grid[self.index] == 1:
            self.label, self.style = "💥", discord.ButtonStyle.danger
            view.reveal_all()
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=discord.Embed(title="💥 בום! פגעת בפצצה!", description=f"הפסדת **{view.bet}** טיקטים.", color=discord.Color.red()), view=view)
            return

        self.label, self.style = "💎", discord.ButtonStyle.success
        view.diamonds += 1
        mult = 1.0
        for i in range(view.diamonds): mult *= (25 - i) / (25 - view.bombs - i)
        view.current_multiplier = round(mult, 2)
        await interaction.response.edit_message(embed=view.create_embed(), view=view)

class MinesView(discord.ui.View):
    def __init__(self, bet, bombs, grid, user_id):
        super().__init__(timeout=180)
        self.bet, self.bombs, self.grid, self.user_id, self.diamonds, self.current_multiplier = bet, bombs, grid, user_id, 0, 1.0
        for i in range(25): self.add_item(MinesTileButton(i))
        self.add_item(MinesCashoutButton())

    def create_embed(self):
        embed = discord.Embed(title="💣 קזינו Ticket Royale - מכרות", color=discord.Color.purple())
        embed.add_field(name="💰 הימור", value=f"{self.bet} טיקטים", inline=True)
        embed.add_field(name="📈 מכפיל נוכחי", value=f"**{self.current_multiplier}x**", inline=False)
        return embed

    def reveal_all(self):
        for child in self.children:
            if isinstance(child, MinesTileButton):
                child.label = "💣" if self.grid[child.index] == 1 else "💎"
                child.style = discord.ButtonStyle.danger if self.grid[child.index] == 1 else discord.ButtonStyle.secondary

class MinesCashoutButton(discord.ui.Button):
    def __init__(self): super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.gold, row=4)
    async def callback(self, interaction: discord.Interaction):
        view: MinesView = self.view
        if interaction.user.id != view.user_id or view.diamonds == 0: return
        winnings = int(view.bet * view.current_multiplier)
        update_tickets(view.user_id, winnings)
        view.reveal_all()
        for child in view.children: child.disabled = True
        await interaction.response.edit_message(embed=discord.Embed(title="💰 משיכת כסף מוצלחת!", description=f"זכת ב-**{winnings}** טיקטים.", color=discord.Color.green()), view=view)
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
#         🗼 משחק 4: טאואר (Tower)
# ==========================================

class TowerModal(discord.ui.Modal, title="🗼 משחק טאואר"):
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
        tower_data = [random.randint(0, 2) for _ in range(5)]
        embed = discord.Embed(title="🗼 מגדל הטאואר - קומה 1", description=f"הימור: **{bet}** טיקטים.\nבחר תא בטוח כדי לטפס למעלה!", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, view=TowerView(tower_data, 0, bet, interaction.user.id), ephemeral=True)

class TowerView(discord.ui.View):
    multipliers = [1.3, 1.8, 2.5, 3.8, 5.5]
    def __init__(self, tower_data, floor, bet, user_id):
        super().__init__(timeout=90)
        self.tower_data, self.floor, self.bet, self.user_id = tower_data, floor, bet, user_id
        for i in range(3): self.add_item(TowerButton(i))
        if self.floor > 0: self.add_item(TowerCashout())

class TowerButton(discord.ui.Button):
    def __init__(self, index):
        super().__init__(label=f"❓ תא {index+1}", style=discord.ButtonStyle.primary)
        self.index = index

    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        if interaction.user.id != view.user_id: return

        if self.index == view.tower_data[view.floor]:
            embed = discord.Embed(title="💥 המגדל קרס! פגעת במלכודת!", description=f"הפסדת {view.bet} טיקטים בקומה {view.floor + 1}.", color=discord.Color.red())
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        view.floor += 1
        if view.floor == 5:
            winnings = int(view.bet * 5.5)
            update_tickets(view.user_id, winnings)
            embed = discord.Embed(title="🏆 כבשת את הטאואר!", description=f"הגעת לפסגה! זכת ב-**{winnings}** טיקטים!", color=discord.Color.gold())
            for child in view.children: child.disabled = True
            await interaction.response.edit_message(embed=embed, view=view)
            return

        embed = discord.Embed(title=f"🗼 מגדל הטאואר - קומה {view.floor + 1}", description=f"עלית קומה! מכפיל נוכחי: **{view.multipliers[view.floor-1]}x**", color=discord.Color.blue())
        await interaction.response.edit_message(embed=embed, view=TowerView(view.tower_data, view.floor, view.bet, view.user_id))

class TowerCashout(discord.ui.Button):
    def __init__(self): super().__init__(label="💰 משוך כסף", style=discord.ButtonStyle.gold, row=1)
    async def callback(self, interaction: discord.Interaction):
        view: TowerView = self.view
        if interaction.user.id != view.user_id: return
        winnings = int(view.bet * view.multipliers[view.current_floor - 1] if hasattr(view, 'current_floor') else view.bet * view.multipliers[view.floor - 1])
        update_tickets(view.user_id, winnings)
        embed = discord.Embed(title="💰 משיכת כסף מושלמת!", description=f"פרשת בזמן וזכת ב-**{winnings}** טיקטים!", color=discord.Color.green())
        for child in view.children: child.disabled = True
        await interaction.response.edit_message(embed=embed, view=view)
# ==========================================
#         👑 משחק 5: פוקר וידאו (Poker)
# ==========================================

class PokerModal(discord.ui.Modal, title="👑 הימור פוקר וידאו"):
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
        suits, ranks = ['♥️', '♦️', '♣️', '♠️'], ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{r}{s}" for r in ranks for s in suits]
        random.shuffle(deck)
        player_hand = [deck.pop() for _ in range(5)]

        embed = discord.Embed(title="👑 שולחן הפוקר", description=f"היד הראשונית שלך:\n`{ ' | '.join(player_hand) }` \n\nסמן קלפים שברצונך לנעול (🔒 Hold) ולחץ על כפתור ההחלפה:", color=discord.Color.gold())
        await interaction.response.send_message(embed=embed, view=PokerView(player_hand, deck, bet, interaction.user.id), ephemeral=True)

def evaluate_poker_hand(hand):
    ranks = [card[:-2] for card in hand]
    rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, '10':10, 'J':11, 'Q':12, 'K':13, 'A':14}
    values = sorted([rank_values[r] for r in ranks])
    from collections import Counter
    count_values = sorted(Counter(values).values(), reverse=True)
    if count_values ==: return "רביעייה (Four of a Kind) 💎", 10
    if count_values ==: return "פול האוס (Full House) 🏠", 7
    if count_values ==: return "שלשה (Three of a Kind) 🥉", 3
    if count_values ==: return "זוגיים (Two Pair) 👥", 2
    return "ללא שילוב גבוה", 0

class PokerView(discord.ui.View):
    def __init__(self, player_hand, deck, bet, user_id):
        super().__init__(timeout=90)
        self.player_hand, self.deck, self.bet, self.user_id = player_hand, deck, bet, user_id
        self.holds = set()
        for i in range(5): self.add_item(PokerHoldButton(i))
        self.add_item(PokerDrawButton())

class PokerHoldButton(discord.ui.Button):
    def __init__(self, index): super().__init__(label=f"קלף {index+1}", style=discord.ButtonStyle.secondary, row=0)
    async def callback(self, interaction: discord.Interaction):
        view: PokerView = self.view
        if interaction.user.id != view.user_id: return
        if self.index in view.holds:
            view.holds.remove(self.index)
            self.style, self.label = discord.ButtonStyle.secondary, f"קלף {self.index+1}"
        else:
            view.holds.add(self.index)
            self.style, self.label = discord.ButtonStyle.success, f"🔒 קלף {self.index+1}"
        await interaction.response.edit_message(view=view)

class PokerDrawButton(discord.ui.Button):
    def __init__(self): super().__init__(label="🃏 החלף קלפים וסיים סיבוב", style=discord.ButtonStyle.primary, row=1)
    async def callback(self, interaction: discord.Interaction):
        view: PokerView = self.view
        if interaction.user.id != view.user_id: return
        final_hand = [view.player_hand[i] if i in view.holds else view.deck.pop() for i in range(5)]
        name, mult = evaluate_poker_hand(final_hand)
        winnings = int(view.bet * mult)
        
        if winnings > 0: update_tickets(view.user_id, winnings)
        for child in view.children: child.disabled = True
        
        embed = discord.Embed(title="👑 תוצאות פוקר", description=f"היד הסופית שלך:\n`{ ' | '.join(final_hand) }` \n\n📊 שילוב שהתקבל: **{name}**", color=discord.Color.green() if winnings > 0 else discord.Color.red())
        embed.set_footer(text=f"זכת ב-{winnings} טיקטים!" if winnings > 0 else f"הפסדת {view.bet} טיקטים.")
        await interaction.response.edit_message(embed=embed, view=view)
# ==========================================
#     🎮 לוח המשחקים הציבורי של השרת
# ==========================================

class CasinoPublicLobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary, custom_id="lobby_bj")
    async def bj_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BlackjackModal())

    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary, custom_id="lobby_tw")
    async def tw_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TowerModal())

    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary, custom_id="lobby_mn")
    async def mn_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(MinesModal())

    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary, custom_id="lobby_rl")
    async def rl_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(RouletteModal())

    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary, custom_id="lobby_pk")
    async def pk_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PokerModal())
# ==========================================
#        👑 פאנלים ומערכות ניהול אזולאי
# ==========================================

class AzoulaiManageModal(discord.ui.Modal):
    def __init__(self, action_type):
        super().__init__(title=f"ניהול מנהל - {action_type}")
        self.action_type = action_type
        self.user_input = discord.ui.TextInput(label="הזן שם משתמש או מזהה (ID)", placeholder="הכנס ID של המשתמש...", required=True)
        self.add_item(self.user_input)
        if "טוקנים" in action_type:
            self.amount_input = discord.ui.TextInput(label="כמות טיקטים", placeholder="לדוגמה: 50", min_length=1)
            self.add_item(self.amount_input)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await handle_security_breach(interaction, f"AzoulaiManageModal - {self.action_type}")
            return
        
        try: target_id = int(self.user_input.value.strip())
        except ValueError:
            await interaction.response.send_message("❌ מזהה משתמש שגוי.", ephemeral=True)
            return

        if "טוקנים" in self.action_type:
            try: amt = int(self.amount_input.value.strip())
            except ValueError: return
            update_tickets(target_id, amt)
            await interaction.response.send_message(f"✅ נוספו בהצלחה {amt} טיקטים למשתמש <@{target_id}>.", ephemeral=True)
        else:
            try:
                member = await interaction.guild.fetch_member(target_id)
                await interaction.guild.ban(member, reason="הושעה דרך פאנל הניהול של אזולאי")
                await interaction.response.send_message(f"🔨 המשתמש {member.mention} קיבל באן בהצלחה.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ שגיאה בביצוע הבאן: {e}", ephemeral=True)

class AzoulaiAdminPanelButtons(discord.ui.View):
    def __init__(self): super().__init__(timeout=None)
    @discord.ui.button(label="🔨 באנים וקיקים", style=discord.ButtonStyle.danger, custom_id="az_ban")
    async def b_click(self, interaction: discord.Interaction, b: discord.ui.Button):
        if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "פאנל אזולאי - כפתור באן"); return
        await interaction.response.send_modal(AzoulaiManageModal("באן ליום"))
    @discord.ui.button(label="🪙 ניהול טוקנים", style=discord.ButtonStyle.success, custom_id="az_tok")
    async def t_click(self, interaction: discord.Interaction, b: discord.ui.Button):
        if interaction.user.id != OWNER_ID: await handle_security_breach(interaction, "פאנל אזולאי - כפתור טוקנים"); return
        await interaction.response.send_modal(AzoulaiManageModal("הוספת טוקנים"))


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

@bot.tree.command(name="פאנל", description="הצגת לוח משחקי הקזינו לחברי השרת")
async def panel_public(interaction: discord.Interaction):
    if is_user_banned(interaction.user.id): return
    if interaction.user.id != OWNER_ID:
        await handle_security_breach(interaction, "/פאנל ציבורי")
        return
    embed = discord.Embed(title="🎰 קזינו Ticket Royale - פאנל משחקים", description="כל המשחקים פעילים! לחצו למטה כדי להמר ולשחק:", color=discord.Color.purple())
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
            time_left = (last_claim + timedelta(hours=24)) - now
            hours, remainder = divmod(time_left.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            await interaction.response.send_message(f"❌ תוכל לאסוף שוב בעוד {hours} שעות ו-{minutes} דקות.", ephemeral=True)
            return

    update_tickets(user_id, 20)
    data = load_data()
    data[uid_str]["last_daily"] = now.isoformat()
    save_data(data)
    await interaction.response.send_message(f"🪙 קיבלת **20 טיקטים** חינם! המאזן שלך: **{get_user_data(user_id)['tickets']}** טיקטים. 🎫")


# ==========================================
#          🤖 הפעלת הבוט המלאה
# ==========================================

keep_alive()
TOKEN = os.getenv('DISCORD_TOKEN')
if TOKEN:
    bot.run(TOKEN)
else:
    bot.run("הטוקן_הסודי_שלך_כאן")
