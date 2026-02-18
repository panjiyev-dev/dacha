import asyncio
from aiogram import Bot
from bot.logic.automation import auto_post_scheduler_task
from config import BOT_TOKEN

async def test_auto_post():
    bot = Bot(token=BOT_TOKEN)
    print("Testing auto-post scheduler task...")
    await auto_post_scheduler_task(bot)
    print("Auto-post test completed")

asyncio.run(test_auto_post())
