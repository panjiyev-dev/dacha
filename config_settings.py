# config_settings.py - Bot konfiguratsiyasi
# Bu faylni o'zgartirib, qayta ishga tushiring

# 🎯 POST SOZLAMALARI
POST_SETTINGS = {
    "test_mode": {           # Test rejimi
        "frequency_minutes": 5,      # 5 daqiqada
        "duration_hours": 1,          # 1 soat davomida
        "channels": ["@test_uchun_2"]
    },
    "production": {        # Ishlab chiqarish rejimi
        "frequency_minutes": 30,     # 30 daqiqada
        "duration_hours": 4,          # 4 soat davomida
        "channels": ["@asosiy_kanal"]
    },
    "ultra_fast": {        # Ultra tezkor rejim
        "frequency_minutes": 1,       # 1 daqiqada
        "duration_hours": 0.5,        # 30 daqiqa
        "channels": ["@test_uchun_2"]
    }
}

# 🕐 CLEANUP SOZLAMALARI  
CLEANUP_SETTINGS = {
    "test": {
        "hour": 3,
        "minute": 0,  # Har soatning 0-daqiqasida
        "auto_cleanup": True
    },
    "daily": {
        "hour": 19,
        "minute": 0,  # Har kuni 19:00 da
        "auto_cleanup": True
    }
}

# Qaysi rejimni ishlatish kerak?
CURRENT_MODE = "test_mode"  # "test_mode", "production", "ultra_fast"

# 🚀 Avtomatik sozlash funksiyasi
import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select

async def apply_settings():
    """Config fayldagi sozlamalarni qo'llaydi"""
    
    # Post sozlamalari
    post_config = POST_SETTINGS[CURRENT_MODE]
    freq_hours = post_config["frequency_minutes"] / 60
    duration_hours = post_config["duration_hours"]
    channels = post_config["channels"]
    
    # Cleanup sozlamalari  
    cleanup_config = CLEANUP_SETTINGS["test"]
    cleanup_hour = cleanup_config["hour"]
    cleanup_minute = cleanup_config["minute"]
    
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        # Post sozlamalari
        settings.post_frequency_hours = freq_hours
        settings.post_duration_hours = duration_hours
        settings.target_channels = channels
        
        # Cleanup sozlamalari
        settings.cleanup_hour = cleanup_hour
        settings.cleanup_minute = cleanup_minute
        
        await session.commit()
        
        print(f"🎉 {CURRENT_MODE} rejimi o'rnatildi:")
        print(f"📊 Post chastotasi: {post_config['frequency_minutes']} daqiqa")
        print(f"⏰ Post davomiyligi: {duration_hours} soat")
        print(f"🎯 Kanallar: {', '.join(channels)}")
        print(f"🗑️ Cleanup vaqti: {cleanup_hour:02d}:{cleanup_minute:02d} UTC")

if __name__ == "__main__":
    asyncio.run(apply_settings())
