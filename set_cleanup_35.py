import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select, update

async def set_cleanup_time():
    async with async_session() as session:
        # Get current settings
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        # Set cleanup time to 03:35 UTC
        settings.cleanup_hour = 3
        settings.cleanup_minute = 35
        
        await session.commit()
        
        print(f'Cleanup time set to 03:35 UTC')

asyncio.run(set_cleanup_time())
