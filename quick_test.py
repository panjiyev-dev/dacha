import asyncio
from aiogram import Bot
from bot.utils.channel import post_ad_to_channel, cleanup_expired_posts
from config import BOT_TOKEN
from database.setup import async_session
from sqlalchemy import select
from database.models import Ad

async def quick_test():
    bot = Bot(token=BOT_TOKEN)
    
    # Get ad object
    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.id == 1))
        ad = res.scalar_one_or_none()
    
    if not ad:
        print("No ad found with id=1")
        return
    
    # 1. Auto-post test
    print("Testing auto-post...")
    success, message_id = await post_ad_to_channel(bot, ad)
    print(f"Auto-post result: success={success}, message_id={message_id}")
    
    # 2. Cleanup test (force)
    print("\nTesting cleanup...")
    success, deleted_count = await cleanup_expired_posts(bot, force_cleanup=True)
    print(f"Cleanup result: success={success}, deleted_count={deleted_count}")

asyncio.run(quick_test())
