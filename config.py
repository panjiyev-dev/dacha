# config.py
import os
from dotenv import load_dotenv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ .env ni aynan shu papkadan o‘qiymiz
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# ====== Access policy ======
DAILY_AD_LIMIT = int(os.getenv('DAILY_AD_LIMIT', '99'))  # oddiy user uchun kunlik limit
SUBSCRIPTION_DAYS = int(os.getenv('SUBSCRIPTION_DAYS', '36500'))  # kod bilan kirgan userga qancha kun

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()  # "@test_uchun_2" yoki "-100123..."

# ✅ Admin codes: None bo‘lsa ham ro‘yxatga kirmasin
ADMIN_CODES = [
    code.strip()
    for code in [os.getenv("ADMIN_CODE_1"), os.getenv("ADMIN_CODE_2")]
    if code and code.strip()
]

SUPER_ADMIN_IDS = [
    int(x.strip())
    for x in os.getenv("SUPER_ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
]

DB_USER = os.getenv("DB_USER", "postgres").strip()
DB_PASS = os.getenv("DB_PASS", "postgres").strip()
DB_NAME = os.getenv("DB_NAME", "dacha_bot").strip()
DB_HOST = os.getenv("DB_HOST", "localhost").strip()
DB_PORT = os.getenv("DB_PORT", "5432").strip()

# ✅ SQLite DB path (senda shunday ekan)
# DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'dacha_bot.db')}"
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'villa_bot.db')}"

# ✅ Minimal tekshiruvlar (xatoni darrov ko‘rasan)
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. .env ni tekshir: BOT_TOKEN=...")
def is_super_admin(user_id: int) -> bool:
    return user_id in SUPER_ADMIN_IDS


# Kanalga darhol post qilishni yoqayotgan bo‘lsang, buni ham tekshirgan yaxshi:
# (Hozircha xohlasang commentda qoldir)
# if not CHANNEL_ID:
#     raise ValueError("CHANNEL_ID topilmadi. .env ni tekshir: CHANNEL_ID=@channel yoki -100...")