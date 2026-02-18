import asyncio
from database.setup import async_session, engine
from database.models import User
from sqlalchemy import text
from datetime import datetime

async def add_created_at_column():
    """User jadvalida created_at ustunini qo'shish"""
    print("🔧 created_at ustuni qo'shilmoqda...")
    
    try:
        async with engine.begin() as conn:
            # created_at ustunini qo'shish (default siz)
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN created_at DATETIME")
            )
            print("✅ created_at ustuni muvaffaqiyatli qo'shildi!")
            
            # Mavjud userlar uchun created_at ni to'ldirish
            current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            await conn.execute(
                text(f"UPDATE users SET created_at = '{current_time}' WHERE created_at IS NULL")
            )
            print("✅ Mavjud userlar uchun created_at to'ldirildi!")
            
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        print("Ehtimol ustun allaqachon mavjud")

if __name__ == "__main__":
    asyncio.run(add_created_at_column())
