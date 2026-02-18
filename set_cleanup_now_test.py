import asyncio
from datetime import datetime
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
        
        # Set cleanup time to current time + 1 minute
        now = datetime.utcnow()
        cleanup_hour = now.hour
        cleanup_minute = now.minute + 1
        
        # Handle minute overflow
        if cleanup_minute >= 60:
            cleanup_minute -= 60
            cleanup_hour += 1
            if cleanup_hour >= 24:
                cleanup_hour -= 24
        
        settings.cleanup_hour = cleanup_hour
        settings.cleanup_minute = cleanup_minute
        
        await session.commit()
        
        print(f'Cleanup time set to {cleanup_hour:02d}:{cleanup_minute:02d} UTC')
        print(f'Current time: {now.hour:02d}:{now.minute:02d} UTC')

asyncio.run(set_cleanup_time())
