import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select, update

async def set_frequency():
    async with async_session() as session:
        # Get current settings
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        # Set frequency to 1 minute
        settings.post_frequency_hours = 1/60  # 1 minute = 1/60 hours
        
        await session.commit()
        
        print(f'Post frequency set to 1 minute')
        print(f'Current value: {settings.post_frequency_hours} hours')

asyncio.run(set_frequency())
