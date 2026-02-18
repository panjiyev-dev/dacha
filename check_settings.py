import asyncio
from database.models import GlobalSettings
from database.setup import async_session
from sqlalchemy import select

async def check_settings():
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        if settings:
            print(f'Post frequency: {settings.post_frequency_hours} hours')
            print(f'Post duration: {settings.post_duration_hours} hours')
            print(f'Target channels: {settings.target_channels}')
            print(f'Daily check: {settings.daily_check_hour:02d}:{settings.daily_check_minute:02d} UTC')
            print(f'Cleanup: {settings.cleanup_hour:02d}:{settings.cleanup_minute:02d} UTC')
        else:
            print('No settings found')

asyncio.run(check_settings())
