import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select

async def quick_settings():
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        print("🎯 TEZKOR SOZLAMALAR MENYUSI:")
        print("1. ⚡ Ultra tez (1 daqiqa)")
        print("2. 🚀 Tez (5 daqiqa)") 
        print("3. 🐢 O'rtacha (15 daqiqa)")
        print("4. 🐌 Sekin (30 daqiqa)")
        print("5. 🦥 Juda sekin (1 soat)")
        print("6. ⚙️ O'zim kiritaman")
        
        choice = input("Tanlang (1-6): ").strip()
        
        if choice == "1":
            settings.post_frequency_hours = 1/60    # 1 daqiqa
            settings.post_duration_hours = 0.5        # 30 daqiqa
            print("✅ Ultra tez rejim: 1 daqiqa")
        elif choice == "2":
            settings.post_frequency_hours = 5/60    # 5 daqiqa
            settings.post_duration_hours = 1          # 1 soat
            print("✅ Tez rejim: 5 daqiqa")
        elif choice == "3":
            settings.post_frequency_hours = 15/60   # 15 daqiqa
            settings.post_duration_hours = 2          # 2 soat
            print("✅ O'rtacha rejim: 15 daqiqa")
        elif choice == "4":
            settings.post_frequency_hours = 30/60   # 30 daqiqa
            settings.post_duration_hours = 4          # 4 soat
            print("✅ Sekin rejim: 30 daqiqa")
        elif choice == "5":
            settings.post_frequency_hours = 1        # 1 soat
            settings.post_duration_hours = 8          # 8 soat
            print("✅ Juda sekin rejim: 1 soat")
        elif choice == "6":
            freq = input("Post chastotasi (daqiqada): ")
            dur = input("Post davomiyligi (soatda): ")
            settings.post_frequency_hours = float(freq) / 60
            settings.post_duration_hours = float(dur)
            print(f"✅ O'z rejim: {freq} daqiqa")
        else:
            print("❌ Noto'g'ri tanlov!")
            return
        
        await session.commit()
        print(f"🎉 Sozlandi: Har {settings.post_frequency_hours*60:.1f} daqiqada, {settings.post_duration_hours} soat davomida")

if __name__ == "__main__":
    asyncio.run(quick_settings())
