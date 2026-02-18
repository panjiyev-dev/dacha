import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select

async def fix_frequency():
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        # Daqiqalarda frequency o'rnatish
        # 5 daqiqa = 5/60 = 0.083333
        # 10 daqiqa = 10/60 = 0.166667
        # 15 daqiqa = 15/60 = 0.25
        # 30 daqiqa = 30/60 = 0.5
        # 1 daqiqa = 1/60 = 0.016667
        
        settings.post_frequency_hours = 0.083333  # 5 daqiqa
        settings.post_duration_hours = 1  # 1 soat
        
        await session.commit()
        
        print(f'✅ Post frequency: {settings.post_frequency_hours} hours ({settings.post_frequency_hours*60:.1f} minutes)')
        print(f'✅ Post duration: {settings.post_duration_hours} hours')

asyncio.run(fix_frequency())
