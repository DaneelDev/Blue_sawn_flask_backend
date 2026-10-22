import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
PORT = int(os.getenv("PORT", 3001))

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не найден в .env")

if not ENCRYPTION_KEY or len(ENCRYPTION_KEY) != 64:
    raise RuntimeError("ENCRYPTION_KEY должен быть ровно 64 HEX-символа (32 байта)")
