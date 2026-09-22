import os
import discord
from discord.ext import commands
from flask import Flask
from threading import Thread

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

# ה-ID שלך בדיסקורד (בעלים ראשי)
YOUR_DISCORD_ID = 1260675229626273802

# מילון לשמירת כמות הניסיונות של פולשים שניסו להיכנס לפאנל
failed_attempts = {}

# --- מחלקת כפתורי לוח הבקרה הראשי ("פאנל אזולאי") ---
class AdminGamePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔨 באנים וקיקים", style=discord.ButtonStyle.danger, custom_id="panel_moderation")
    async def moderation_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚙️ פקודות ניהול: השתמש בפקודות המובנות או בכפתורי הרחבה שיתווספו בהמשך.", ephemeral=True)

    @discord.ui.button(label="⚠️ מערכת אזהרות", style=discord.ButtonStyle.secondary, custom_id="panel_warnings")
    async def warnings_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("📝 כאן תוכל לצפות באזהרות (3 אזהרות = באן ליום).", ephemeral=True)

    @discord.ui.button(label="🪙 ניהול טוקנים ופרסים", style=discord.ButtonStyle.success, custom_id="panel_tokens")
    async def tokens_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("💰 כאן תוכל להוסיף טוקנים, להוריד טוקנים או לקבוע פרסי זכייה.", ephemeral=True)

    @discord.ui.button(label="🎮 פתח את כל המשחקים", style=discord.ButtonStyle.primary, custom_id="panel_open_games")
    async def open_games_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔓 כל משחקי הקזינו נפתחו בהצלחה לשחקנים בשרת!", ephemeral=True)


# --- פקודת פאנל הניהול הסודית ---
@bot.tree.command(name="פאנל", description="פאנל ניהול בלעדי למנהל הראשי")
async def panel(interaction: discord.Interaction):
    user_id = interaction.user.id
    
    # 🚨 בדיקת אבטחה: אם המשתמש הוא לא אתה
    if user_id != YOUR_DISCORD_ID:
        # עדכון מונה הניסיונות של המשתמש הספציפי הזה
        failed_attempts[user_id] = failed_attempts.get(user_id, 0) + 1
        current_attempts = failed_attempts[user_id]
        
        # 1. הודעה למשתמש הפולש - דחיית גישה והפנייה אלייך
        deny_embed = discord.Embed(
            title="❌ הגישה נדחתה!",
            description=f"אין לך הרשאות גישה ל**פאנל אזולאי**.\n\nאם אתה זקוק לגישה, יש לפנות לבעלי הבוט: <@{YOUR_DISCORD_ID}>",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=deny_embed, ephemeral=True)
        
        # 2. שליחת התראה סודית ומפורטת ישירות אלייך לפרטי (DM)
        try:
            owner = await bot.fetch_user(YOUR_DISCORD_ID)
            alert_embed = discord.Embed(
                title="🚨 התראת אבטחה - ניסיון פריצה לפאנל!",
                description="משתמש ללא הרשאות ניסה להפעיל את הלוח שלך.",
                color=discord.Color.orange()
            )
            alert_embed.add_field(name="שם משתמש", value=f"{interaction.user} ({interaction.user.mention})", inline=False)
            alert_embed.add_field(name="מזהה משתמש (ID)", value=str(user_id), inline=False)
            alert_embed.add_field(name="שרת שבו זה קרה", value=interaction.guild.name if interaction.guild else "הודעה פרטית", inline=False)
            alert_embed.add_field(name="📊 סך הכל ניסיונות שלו", value=f"**{current_attempts}** פעמים", inline=False)
            
            await owner.send(embed=alert_embed)
        except Exception as e:
            print(f"שגיאה בשליחת הודעה פרטית לבעלים: {e}")
        return

    # 👑 אם זה אתה (אזולאי המנהל) - הפאנל נפתח בהצלחה!
    embed = discord.Embed(
        title="👑 פאנל אזולאי - Ticket Royale",
        description="ברוך הבא למערכת השליטה והניהול המלאה של הקזינו והמשחקים:",
        color=discord.Color.gold()
    )
    embed.add_field(name="🌐 סטטוס מערכת", value="🟢 כל המערכות פועלות כסדרן", inline=True)
    embed.set_footer(text="מחובר כמנהל מערכת ראשי ובלעדי")
    
    await interaction.response.send_message(embed=embed, view=AdminGamePanel(), ephemeral=True)


# --- 🎮 פקודת משחק: בלאק ג'ק ---
@bot.tree.command(name="בלאקגק", description="שחק משחק בלאק ג'ק נגד הקזינו!")
async def blackjack(interaction: discord.Interaction):
    # כאן יבוא בהמשך קוד חלוקת הקלפים המלא, כרגע החזרת הודעת בדיקה
    bj_embed = discord.Embed(
        title="🃏 משחק בלאק ג'ק - Ticket Royale",
        description=f"המשחק של {interaction.user.mention} מתחיל עכשיו!\n(קוד חלוקת הקלפים והימורי הטוקנים ייבנה בשלב הבא)",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=bj_embed)


# --- אירוע חיבור הבוט ---
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"הבוט מחובר בהצלחה בתור {bot.user}")

# הפעלת שרת האינטרנט המובנה ברקע בשביל UptimeRobot
keep_alive()

# משיכת הטוקן המאובטח (מ-Render או הרצה מקומית)
TOKEN = os.getenv('DISCORD_TOKEN')

if TOKEN:
    bot.run(TOKEN)
else:
    # אם אתה מריץ במחשב ואין משתנה סביבה, שים את הטוקן שלך כאן במקום הכתב הריק
    bot.run("הטוקן_הסודי_שלך_כאן")
