# Granado Espada M TH - 24H Bot

## รัน 24 ชม. ฟรี - วิธีที่ง่ายสุด (Render + UptimeRobot)

### ขั้นตอน 1: อัปโหลดขึ้น GitHub
1. สร้าง GitHub repo ใหม่ (ตั้งชื่อ granado-boss-bot)
2. อัปโหลดไฟล์ทั้งหมดในโฟลเดอร์นี้ขึ้นไป (ยกเว้น .env)

### ขั้นตอน 2: เอาไปรันบน Render.com ฟรี
1. ไป https://dashboard.render.com -> New + -> Web Service
2. Connect GitHub repo ที่เพิ่งสร้าง
3. ตั้งค่า:
   - Build Command: pip install -r requirements.txt
   - Start Command: python bot.py
4. ไปที่ Environment -> Add:
   - DISCORD_TOKEN = Token บอท
   - CHANNEL_ID = ID ห้อง
   - ROLE_MENTION = @everyone
5. กด Create Web Service -> รอ 2 นาที บอทออนไลน์!

### ขั้นตอน 3: กันบอทหลับ (สำคัญ!)
Render ฟรีจะหลับหลัง 15 นาทีถ้าไม่มีคนเข้า ต้องใช้ UptimeRobot ปลุก
1. ไป https://uptimerobot.com สมัครฟรี
2. Add New Monitor -> Type: HTTP(s)
3. URL: ใส่ URL ที่ Render ให้มา (เช่น https://granado-boss-bot.onrender.com)
4. Interval: 5 minutes
5. Create -> เสร็จ! บอทจะไม่หลับอีกเลย = 24 ชม. แท้

### เช็คว่าออนไลน์ไหม?
เข้า URL ของ Render จะเห็น "Bot is Online! Time: ..."

บอสทั้งหมดเวลาไทย GMT+7
