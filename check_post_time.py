import asyncio
from datetime import datetime, timedelta
from database.models import Ad
from database.setup import async_session
from sqlalchemy import select

async def check_post_time():
    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.id == 1))
        ad = res.scalar_one_or_none()
        if ad:
            print(f'Ad {ad.id} last_posted_at: {ad.last_posted_at}')
            print(f'Current time: {datetime.utcnow()}')
            if ad.last_posted_at:
                time_since = datetime.utcnow() - ad.last_posted_at
                print(f'Time since last post: {time_since}')
                print(f'Hours since: {time_since.total_seconds() / 3600:.2f}')

asyncio.run(check_post_time())
