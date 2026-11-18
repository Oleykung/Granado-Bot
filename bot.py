
import discord
from discord.ext import commands, tasks
import datetime
import json
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
CHANNEL_ID_RAW = os.getenv("CHANNEL_ID", "0").strip()
ROLE_MENTION = os.getenv("ROLE_MENTION", "@everyone").strip()

try:
    CHANNEL_ID = int(CHANNEL_ID_RAW) if CHANNEL_ID_RAW else 0
except:
    print(f"❌ CHANNEL_ID ไม่ถูกต้อง: '{CHANNEL_ID_RAW}'")
    CHANNEL_ID = 0

# แก้บั๊ก Windows tzdata
try:
    from zoneinfo import ZoneInfo
    try:
        BANGKOK = ZoneInfo("Asia/Bangkok")
    except Exception:
        print("⚠️ ใช้ GMT+7 แทน Asia/Bangkok")
        BANGKOK = datetime.timezone(datetime.timedelta(hours=7))
except ImportError:
    BANGKOK = datetime.timezone(datetime.timedelta(hours=7))

print("🔍 ตรวจสอบ...")
print(f"TOKEN: {'✅' if TOKEN else '❌ ว่าง'} | CHANNEL: {CHANNEL_ID}")
print(f"TIMEZONE: {BANGKOK}")

# โหลด config
try:
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    BOSSES = cfg.get("bosses", [])
    print(f"👹 โหลดบอส {len(BOSSES)} ตัว")
except Exception as e:
    print(f"❌ โหลด config ไม่ได้: {e}")
    BOSSES = []

intents = discord.Intents.default()
intents.message_content = True  # ต้องเปิดสำหรับคำสั่ง ! 
bot = commands.Bot(command_prefix=["!", "บ!", "."], intents=intents, help_command=None)

def parse_time(t_str):
    try:
        h, m = map(int, t_str.split(":"))
        return h, m
    except:
        return 0,0

def get_offset_time(base_time_str, offset_min):
    h, m = parse_time(base_time_str)
    now = datetime.datetime.now(BANGKOK)
    dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
    dt = dt + datetime.timedelta(minutes=offset_min)
    return dt.strftime("%H:%M")

def get_next_bosses(limit=10):
    """หาบอสที่จะเกิดต่อจากนี้"""
    now = datetime.datetime.now(BANGKOK)
    upcoming = []
    # เช็ค 24 ชม. ข้างหน้า
    for minutes_ahead in range(0, 24*60):
        check_time = now + datetime.timedelta(minutes=minutes_ahead)
        check_str = check_time.strftime("%H:%M")
        for boss in BOSSES:
            if check_str in boss.get("times", []):
                diff = minutes_ahead
                if diff == 0:
                    upcoming.append((boss, check_str, "ตอนนี้!", diff))
                else:
                    upcoming.append((boss, check_str, f"อีก {diff} นาที", diff))
        if len(upcoming) >= limit:
            break
    return upcoming

# ==================== AUTO ALERT LOOP ====================
@tasks.loop(seconds=60)
async def boss_checker():
    now = datetime.datetime.now(BANGKOK)
    now_str = now.strftime("%H:%M")
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        if now.second == 0:
            print(f"⚠️ หาห้อง {CHANNEL_ID} ไม่เจอ")
        return

    for boss in BOSSES:
        for b_time in boss.get("times", []):
            pre10 = get_offset_time(b_time, -10)
            pre5 = get_offset_time(b_time, -5)
            embed = None
            if now_str == pre10:
                embed = discord.Embed(
                    title=f"⏰ อีก 10 นาที {boss['name']} จะเกิด!",
                    description=f"{boss.get('desc','')}\nเวลาเกิด: **{b_time} น.** (ไทย)",
                    color=int(boss.get("color","FF0000"), 16)
                )
                embed.add_field(name="📍 เตรียมตัว", value="วาร์ปไปรอได้เลย", inline=False)
            elif now_str == pre5:
                embed = discord.Embed(
                    title=f"⚠️ อีก 5 นาที {boss['name']} จะเกิด!",
                    description=f"{boss.get('desc','')}\nเวลาเกิด: **{b_time} น.**",
                    color=0xFFFF00
                )
            elif now_str == b_time:
                embed = discord.Embed(
                    title=f"🔥 {boss['name']} เกิดแล้ว!",
                    description=f"{boss.get('desc','')}\nรีบไปตีเลย!",
                    color=0x00FF00
                )
            if embed:
                embed.set_footer(text="Granado Espada M TH | GMT+7")
                try:
                    content = ROLE_MENTION if ROLE_MENTION else None
                    await channel.send(content=content, embed=embed)
                    print(f"[{now_str}] แจ้ง {boss['name']} {b_time}")
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"❌ ส่งไม่ได้: {e}")

# ==================== BOT COMMANDS ====================
@bot.event
async def on_message(message):
    # Debug: โชว์ทุกข้อความที่บอทเห็น (ช่วยเช็คว่า MESSAGE CONTENT INTENT เปิดรึยัง)
    if message.author == bot.user:
        return
    print(f"📩 เห็นข้อความ: '{message.content}' จาก {message.author} ใน #{message.channel.name}")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"\n✅✅✅ บอทออนไลน์: {bot.user} ✅✅✅")
    print(f"⏰ เวลาไทย: {datetime.datetime.now(BANGKOK).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📢 ห้องแจ้งเตือน: {CHANNEL_ID}")
    print(f"📜 คำสั่ง: !บอส, !ต่อไป, !เวลา, !ทดสอบ, !ช่วย")
    if not boss_checker.is_running():
        boss_checker.start()

@bot.command(name="บอส", aliases=["boss", "bosslist", "บอสทั้งหมด", "ลิสบอส"])
async def boss_list(ctx):
    """ดูบอสทั้งหมด"""
    embed = discord.Embed(title="👹 รายชื่อบอส Granado Espada M TH", description="เวลาไทย GMT+7", color=0x3498db)
    for boss in BOSSES:
        times = " / ".join(boss.get("times", []))
        embed.add_field(name=f"{boss['name']}", value=f"⏰ {times}\n{ boss.get('desc','')}", inline=False)
    embed.set_footer(text=f"ใช้ !ต่อไป เพื่อดูบอสที่ใกล้เกิด | เวลาตอนนี้ {datetime.datetime.now(BANGKOK).strftime('%H:%M')}")
    await ctx.send(embed=embed)

@bot.command(name="ต่อไป", aliases=["next", "nextboss", "บอสต่อไป", "ต่อ", "บอสต่อ"])
async def next_boss(ctx):
    """ดูบอสที่จะเกิดต่อไป"""
    upcoming = get_next_bosses(10)
    if not upcoming:
        await ctx.send("ไม่เจอบอสใน 24 ชม. ข้างหน้า (เช็ค config.json)")
        return
    
    embed = discord.Embed(title="🔥 บอสที่ใกล้จะเกิด", description=f"เวลาปัจจุบัน: **{datetime.datetime.now(BANGKOK).strftime('%H:%M:%S')}** น. (ไทย)", color=0xff0000)
    for boss, b_time, when, diff in upcoming:
        if diff == 0:
            embed.add_field(name=f"🔴 {boss['name']} - ตอนนี้!", value=f"⏰ {b_time} | {boss.get('desc','')}", inline=False)
        else:
            embed.add_field(name=f"{boss['name']}", value=f"⏰ {b_time} ({when}) | {boss.get('desc','')}", inline=False)
    embed.set_footer(text="Granado Espada M TH | อัปเดตทุกนาที")
    await ctx.send(embed=embed)

@bot.command(name="เวลา", aliases=["time", "now", "เวลาตอนนี้", "เช็คเวลา"])
async def current_time(ctx):
    now = datetime.datetime.now(BANGKOK)
    embed = discord.Embed(title="⏰ เวลาเซิร์ฟเวอร์", color=0x00ff00)
    embed.add_field(name="เวลาไทย (GMT+7)", value=f"**{now.strftime('%Y-%m-%d %H:%M:%S')}**", inline=False)
    embed.add_field(name="บอสต่อไป", value="พิมพ์ `!ต่อไป` เพื่อดูบอสที่ใกล้เกิด", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="ทดสอบ", aliases=["test", "เทส", "ทดสอบแจ้งเตือน"])
async def test_alert(ctx):
    """ทดสอบส่งแจ้งเตือน"""
    embed = discord.Embed(title="✅ ทดสอบบอทสำเร็จ!", description=f"บอททำงานปกติ\nห้องนี้: {ctx.channel.id}\nเวลาไทย: {datetime.datetime.now(BANGKOK).strftime('%H:%M:%S')}", color=0x00ff00)
    embed.add_field(name="ROLE_MENTION", value=ROLE_MENTION, inline=False)
    embed.set_footer(text="ถ้าเห็นข้อความนี้ = บอทพร้อมแจ้งเตือนบอสแล้ว!")
    await ctx.send(content=ROLE_MENTION if ROLE_MENTION else None, embed=embed)

@bot.command(name="ช่วย", aliases=["help", "คำสั่ง", "วิธีใช้"])
async def help_cmd(ctx):
    embed = discord.Embed(title="📜 คำสั่งบอท Granado Espada M TH", description="ใช้ได้ทุกห้องที่บอทอยู่", color=0x3498db)
    embed.add_field(name="👹 !บอส / !boss", value="ดูบอสทั้งหมดและเวลาทั้งวัน", inline=False)
    embed.add_field(name="🔥 !ต่อไป / !next", value="ดูบอส 10 ตัวที่ใกล้จะเกิดต่อจากนี้", inline=False)
    embed.add_field(name="⏰ !เวลา / !time", value="เช็คเวลาไทยปัจจุบัน", inline=False)
    embed.add_field(name="✅ !ทดสอบ / !test", value="ทดสอบว่าบอทแจ้งเตือนได้ไหม", inline=False)
    embed.add_field(name="📢 ระบบอัตโนมัติ", value="บอทจะแจ้งเตือนเองที่ห้องที่ตั้งไว้\n- ก่อนเกิด 10 นาที\n- ก่อนเกิด 5 นาที\n- ตอนบอสเกิด", inline=False)
    embed.set_footer(text="Prefix: !  .  บ! | ตัวอย่าง: !บอส")
    await ctx.send(embed=embed)

@bot.command(name="worldboss", aliases=["world", "เวิลบอส", "บอสโลก"])
async def world_boss(ctx):
    for boss in BOSSES:
        if "World" in boss["name"]:
            times = " / ".join(boss.get("times", []))
            embed = discord.Embed(title=f"{boss['name']}", description=f"⏰ เวลา: {times}\n{ boss.get('desc','')} ", color=int(boss.get("color","FF0000"),16))
            embed.set_footer(text=f"เวลาตอนนี้ {datetime.datetime.now(BANGKOK).strftime('%H:%M')}")
            await ctx.send(embed=embed)
            return
    await ctx.send("ไม่เจอ World Boss ใน config.json")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error {event}: {args}")

# Keep Alive
try:
    from flask import Flask
    from threading import Thread
    app = Flask(__name__)
    @app.route('/')
    def home():
        return f"Bot {bot.user if hasattr(bot, 'user') and bot.user else 'Loading'} is Online! Time: {datetime.datetime.now(BANGKOK)}"
    @app.route('/health')
    def health():
        return "OK", 200
    def run_flask():
        port = int(os.environ.get("PORT", 8080))
        app.run(host='0.0.0.0', port=port)
    Thread(target=run_flask, daemon=True).start()
    print("✅ Flask Keep-Alive เปิดแล้ว")
except ImportError:
    print("ℹ️ ไม่มี Flask")

if __name__ == "__main__":
    if not TOKEN:
        print("\n❌ ไม่เจอ DISCORD_TOKEN ใส่ใน .env ก่อน!")
    elif CHANNEL_ID == 0:
        print("\n❌ CHANNEL_ID เป็น 0")
    else:
        try:
            bot.run(TOKEN)
        except discord.errors.LoginFailure:
            print("\n❌ TOKEN ผิด! Reset ใหม่")
        except Exception as e:
            import traceback
            traceback.print_exc()
