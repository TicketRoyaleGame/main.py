import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ה-ID שלך בדיסקורד
YOUR_DISCORD_ID = 1260675229626273802

# מחלקה של כפתורי הניהול בפאנל
class AdminGamePanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="📊 ניהול שחקנים", style=discord.ButtonStyle.primary, custom_id="manage_players")
    async def manage_players_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("כאן תוכל לראות ולנהל את כל השחקנים.", ephemeral=True)

    @discord.ui.button(label="⚙️ הגדרות מערכת", style=discord.ButtonStyle.secondary, custom_id="system_settings")
    async def settings_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("הגדרות מתקדמות של הבוט.", ephemeral=True)

@bot.tree.command(name="פאנל", description="פאנל ניהול בלעדי למנהל")
async def panel(interaction: discord.Interaction):
    # בדיקה האם המשתמש שהריץ את הפקודה הוא אתה
    if interaction.user.id != YOUR_DISCORD_ID:
        # הודעה נסתרת שרואה רק מי שנסה להיכנס
        await interaction.response.send_message("אתה לא רשאי לפאנל זה!", ephemeral=True)
        
        # שליחת הודעה פרטית (DM) אליך עם פרטי המשתמש המנסה
        try:
            owner = await bot.fetch_user(YOUR_DISCORD_ID)
            embed_alert = discord.Embed(
                title="🚨 התראת אבטחה - ניסיון גישה לפאנל!",
                description="המשתמש הבא ניסה להיכנס לפאנל הניהול:",
                color=discord.Color.red()
            )
            embed_alert.add_field(name="שם משתמש", value=str(interaction.user), inline=False)
            embed_alert.add_field(name="מזהה (ID)", value=str(interaction.user.id), inline=False)
            embed_alert.add_field(name="שרת", value=interaction.guild.name if interaction.guild else "הודעה פרטית", inline=False)
            
            await owner.send(embed=embed_alert)
        except Exception as e:
            print(f"שגיאה בשליחת הודעה פרטית אליך: {e}")
        return

    # אם זה אתה - הפאנל נפתח בהצלחה!
    embed = discord.Embed(
        title="👑 פאנל ניהול ראשי - Ticket Royale",
        description="ברוך הבא למערכת הניהול שלך. בחר באחת מהאפשרויות:",
        color=discord.Color.gold()
    )
    embed.set_footer(text="מחובר כמנהל מערכת ראשי")
    
    await interaction.response.send_message(embed=embed, view=AdminGamePanel(), ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"הבוט מחובר בהצלחה בתור {bot.user}")

# משיכת הטוקן המאובטח מהשרת (מה-KEY שהגדרנו ב-Render)
TOKEN = os.getenv('DISCORD_TOKEN')

# הרצת הבוט
if TOKEN:
    bot.run(TOKEN)
else:
    print("MTU1MjA3NTQyMjI5OTIwMTU2Ng.GZ45Zo.gYxl-WVJhkwWFf_gxSzlpsR_hMEtwelhDROXWM")
