import asyncio
from database.models import Ad
from database.setup import async_session
from sqlalchemy import select

async def check_active_ads():
    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.status == 'active'))
        ads = res.scalars().all()
        
        print(f'Found {len(ads)} active ads:')
        for ad in ads:
            print(f'  Ad {ad.id}: {ad.title} (last_posted: {ad.last_posted_at})')

asyncio.run(check_active_ads())
