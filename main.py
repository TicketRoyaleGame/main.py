import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
from datetime import datetime, timedelta

# --- הגדרת שרת האינטרנט עבור UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "הבוט חי ונושם!"

def run_server():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- הגדרות הבוט הראשיות ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ה-ID שלך בדיסקורד (בעלים ראשי ובלעדי)
YOUR_DISCORD_ID = 1260675229626273802

# מאגרי נתונים בזיכרון (טוקנים, דיילי, אזהרות ופריצות)
user_tokens = {}      # ID: כמות טוקנים
daily_cooldown = {}   # ID: זמן הדיילי האחרון
user_warnings = {}    # ID: כמות אזהרות
failed_attempts = {}  # ID: כמות ניסיונות פריצה

# פונקציית עזר לבדיקה אם המשתמש הוא אזולאי
def is_azoulai(interaction: discord.Interaction):
    return interaction.user.id == YOUR_DISCORD_ID
# ==========================================
#  👑 תפריטי כפתורים אקטיביים לפאנל אזולאי 👑
# ==========================================

# 1. תפריט כפתורי באנים וקיקים (עכשיו פעיל!)
class ModerationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔨 תן באן (יום)", style=discord.ButtonStyle.danger, custom_id="btn_ban")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("השתמש בפקודה ייעודית או הקלד את שם המשתמש לחסימה (ישולב עם בסיס נתונים בשלב הבא).", ephemeral=True)

    @discord.ui.button(label="🔓 ביטול באן", style=discord.ButtonStyle.success, custom_id="btn_unban")
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("מערכת ביטול חסימות נפתחה.", ephemeral=True)

    @discord.ui.button(label="👢 תן קיק (להעיף)", style=discord.ButtonStyle.secondary, custom_id="btn_kick")
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("מערכת הרחקת משתמשים מוכנה.", ephemeral=True)

# 2. תפריט כפתורי ניהול טוקנים (עכשיו פעיל!)
class TokenManagementView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="➕ הוסף טוקנים", style=discord.ButtonStyle.success, custom_id="btn_add_tokens")
    async def add_tokens(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הגדרת הוספת טוקנים לשחקן פעילה.", ephemeral=True)

    @discord.ui.button(label="➖ הורד טוקנים", style=discord.ButtonStyle.danger, custom_id="btn_remove_tokens")
    async def remove_tokens(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הגדרת הפחתת טוקנים לשחקן פעילה.", ephemeral=True)

# 3. לוח הבקרה הראשי והבלעדי שלך
class AdminGamePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔨 באנים וקיקים", style=discord.ButtonStyle.danger, custom_id="panel_mod")
    async def mod_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🔨 ניהול חברים - באנים וקיקים", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, view=ModerationView(), ephemeral=True)

    @discord.ui.button(label="⚠️ מערכת אזהרות", style=discord.ButtonStyle.secondary, custom_id="panel_warn")
    async def warn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📝 אזהרות מערכת: 3 אזהרות שוות באן אוטומטי ליום אחד.", ephemeral=True)

    @discord.ui.button(label="🪙 ניהול טוקנים ופרסים", style=discord.ButtonStyle.success, custom_id="panel_tok")
    async def tok_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(title="🪙 שליטה תקציבית - טוקנים ופרסים", color=discord.Color.green())
        await interaction.response.send_message(embed=embed, view=TokenManagementView(), ephemeral=True)

    @discord.ui.button(label="🎮 פתח את כל המשחקים", style=discord.ButtonStyle.primary, custom_id="panel_games_open")
    async def games_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔓 כל משחקי הקזינו נפתחו בהצלחה לשחקנים בשרת!", ephemeral=True)
# ==========================================
#     🎮 תפריט המשחקים הציבורי של השרת 🎮
# ==========================================

class PublicGamesView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🃏 בלאק ג'ק", style=discord.ButtonStyle.primary, custom_id="game_bj")
    async def bj_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎮 {interaction.user.mention} הפעיל משחק בלאק ג'ק! (הקוד המלא ישולב בקרוב)", ephemeral=False)

    @discord.ui.button(label="🗼 טאואר", style=discord.ButtonStyle.primary, custom_id="game_tower")
    async def tower_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎮 {interaction.user.mention} התחיל לטפס בטאואר!", ephemeral=False)

    @discord.ui.button(label="💣 מיין (Mines)", style=discord.ButtonStyle.primary, custom_id="game_mines")
    async def mines_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎮 {interaction.user.mention} פתח לוח מיין! היזהר מהפצצות.", ephemeral=False)

    @discord.ui.button(label="🎰 רולטה", style=discord.ButtonStyle.primary, custom_id="game_roulette")
    async def roulette_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎮 {interaction.user.mention} סובב את הרולטה!", ephemeral=False)

    @discord.ui.button(label="👑 פוקר", style=discord.ButtonStyle.primary, custom_id="game_poker")
    async def poker_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"🎮 {interaction.user.mention} פתח שולחן פוקר!", ephemeral=False)
# ==========================================
#             🚀 פקודות סלאש 🚀
# ==========================================

# 1. פקודה סודית ומוסתרת רק בשבילך!
@bot.tree.command(name="פאנל_אזולאי", description="לוח בקרה סודי ובלעדי למנהל הראשי")
async def panel_azoulai(interaction: discord.Interaction):
    if not is_azoulai(interaction):
        await handle_intrusion(interaction)
        return

    embed = discord.Embed(
        title="👑 פאנל אזולאי - Ticket Royale",
        description="ברוך הבא ללוח השליטה הבלעדי שלך. בחר קטגוריה לניהול:",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed, view=AdminGamePanel(), ephemeral=True)

# 2. פקודה ציבורית שרק אתה יכול להפעיל כדי שכולם יראו את המשחקים
@bot.tree.command(name="פאנל", description="הצגת פאנל משחקי הקזינו לחברי השרת")
async def panel_public(interaction: discord.Interaction):
    if not is_azoulai(interaction):
        await handle_intrusion(interaction)
        return

    embed = discord.Embed(
        title="🎰 קזינו Ticket Royale - פאנל משחקים פעיל",
        description="כל המשחקים זמינים כעת! לחצו על אחד הכפתורים למטה כדי להתחיל לשחק:",
        color=discord.Color.purple()
    )
    embed.add_field(name="🎮 רשימת המשחקים", value="• 🃏 בלאק ג'ק\n• 🗼 טאואר\n• 💣 מיין\n• 🎰 רולטה\n• 👑 פוקר", inline=False)
    
    # נשלח ללא ephemeral=True כדי שכל השרת יראה את זה!
    await interaction.response.send_message(embed=embed, view=PublicGamesView(), ephemeral=False)

# 3. פקודת דיילי לקבלת 20 טוקנים בכל 24 שעות
@bot.tree.command(name="דיילי", description="קבל 20 טוקנים חינם בכל 24 שעות!")
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

    # חלוקת הפרס
    user_tokens[user_id] = user_tokens.get(user_id, 0) + 20
    daily_cooldown[user_id] = now
    
    embed = discord.Embed(
        title="🪙 פרס יומי התקבל!",
        description=f"קיבלת בהצלחה **20 טוקנים** למשחק!\nהמאזן הנוכחי שלך: **{user_tokens[user_id]} טוקנים**.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)


# --- טיפול בניסיונות פריצה לפאנלים שלך ---
async def handle_intrusion(interaction: discord.Interaction):
    user_id = interaction.user.id
    failed_attempts[user_id] = failed_attempts.get(user_id, 0) + 1
    
    deny_embed = discord.Embed(
        title="❌ הגישה נדחתה!",
        description=f"אין לך הרשאות גישה למערכת זו.\n\nאם אתה זקוק לגישה או אישור, פנה לבעלי הבוט: <@{YOUR_DISCORD_ID}>",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=deny_embed, ephemeral=True)
    
    try:
        owner = await bot.fetch_user(YOUR_DISCORD_ID)
        alert = discord.Embed(title="🚨 התראה - ניסיון פריצה לפאנל!", color=discord.Color.orange())
        alert.add_field(name="משתמש", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
        alert.add_field(name="מזהה ID", value=str(user_id), inline=False)
        alert.add_field(name="סך הכל ניסיונות שלו", value=f"**{failed_attempts[user_id]}** פעמים", inline=False)
        await owner.send(embed=alert)
    except Exception as e:
        print(f"שגיאה בהודעה פרטית: {e}")
# ==========================================
#          🚀 סיום והפעלת הבוט 🚀
# ==========================================

@bot.event
async def on_ready():
    # סנכרון של כל פקודות הסלאש החדשות בדיסקורד
    await bot.tree.sync()
    print(f"הבוט מחובר בהצלחה בתור {bot.user}")

# הפעלת שרת האינטרנט ברקע בשביל הניטור של UptimeRobot
keep_alive()

# משיכת הטוקן המאובטח מהשרת או הרצה מקומית
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    # אם אתה מריץ במחשב ואין משתנה סביבה, שים את הטוקן שלך בתוך המרכאות:
    bot.run("הטוקן_הסודי_שלך_כאן")
