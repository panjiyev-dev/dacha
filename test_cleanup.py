import asyncio
from aiogram import Bot
from bot.utils.channel import cleanup_expired_posts
from config import BOT_TOKEN

async def test_cleanup():
    bot = Bot(token=BOT_TOKEN)
    print("Testing forced cleanup...")
    success, deleted_count = await cleanup_expired_posts(bot, force_cleanup=True)
    print(f"Cleanup result: success={success}, deleted_count={deleted_count}")

asyncio.run(test_cleanup())
