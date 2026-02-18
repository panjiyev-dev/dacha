import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select

async def change_post_settings():
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        # Post chastotasini o'zgartirish (daqiqalarda)
        # 30 daqiqa = 0.5 soat
        # 15 daqiqa = 0.25 soat
        # 2 soat = 2.0 soat
        settings.post_frequency_hours = 0.5  # 30 daqiqa
        
        # Post kanalda qolish vaqti (soatda)
        settings.post_duration_hours = 2  # 2 soat
        
        # Target kanallar
        settings.target_channels = ['@test_uchun_2']
        
        await session.commit()
        
        print(f'Post frequency: {settings.post_frequency_hours} hours ({settings.post_frequency_hours*60} minutes)')
        print(f'Post duration: {settings.post_duration_hours} hours')
        print(f'Target channels: {settings.target_channels}')

asyncio.run(change_post_settings())
