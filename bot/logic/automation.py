# logic/automation.py
from aiogram import Bot, types
from database.setup import async_session
from database.models import Ad, User, ChannelPost
from bot.utils.channel import post_ad_to_channel, cleanup_expired_posts
from sqlalchemy import select, update
from datetime import datetime
from bot.services.scheduler import scheduler

async def daily_availability_check(bot: Bot):
    """Asks users if their villas are free today."""
    async with async_session() as session:
        # Find users with active, approved ads
        res = await session.execute(
            select(User).join(Ad).where(Ad.status == 'active', User.is_blocked == False)
        )
        users = res.scalars().unique().all()

        for user in users:
            from bot.utils.i18n import i18n
            lang = user.language or 'ru'

            text = i18n.get("check_text", lang)
            btn_yes = i18n.get("check_btn_yes", lang)
            btn_no = i18n.get("check_btn_no", lang)

            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=btn_yes, callback_data="villa_free_yes")],
                [types.InlineKeyboardButton(text=btn_no, callback_data="villa_free_no")]
            ])

            try:
                await bot.send_message(user.user_id, text, reply_markup=kb, parse_mode="HTML")
            except Exception as e:
                import logging
                logging.error(f"Failed to send daily check to {user.user_id}: {e}")

async def auto_post_scheduler_task(bot: Bot):
    """Logic to auto-post active ads based on global frequency."""
    async with async_session() as session:
        from database.models import GlobalSettings
        from datetime import timedelta

        now = datetime.utcnow()

        # Get frequency
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        freq = settings.post_frequency_hours if settings else 4

        # Only post ads marked as 'active'
        # AND (last_posted_at is None OR last_posted_at + freq <= now)
        # AND user is NOT blocked
        res = await session.execute(
            select(Ad).join(User).where(
                Ad.status == 'active',
                User.is_blocked == False
            )
        )
        ads = res.scalars().all()

        print(f"DEBUG: Auto-post check - Found {len(ads)} active ads (freq={freq}h)")
        posted_count = 0
        
        for ad in ads:
            should_post = False
            if not ad.last_posted_at:
                should_post = True
                print(f"DEBUG: Ad {ad.id} never posted, posting now")
            elif ad.last_posted_at + timedelta(hours=freq) <= now:
                should_post = True
                print(f"DEBUG: Ad {ad.id} last posted {ad.last_posted_at}, freq passed, posting now")
            else:
                time_until_post = ad.last_posted_at + timedelta(hours=freq) - now
                print(f"DEBUG: Ad {ad.id} waiting {time_until_post}")

            if should_post:
                try:
                    success = await post_ad_to_channel(bot, ad)
                    if success:
                        posted_count += 1
                        print(f"DEBUG: Successfully posted ad {ad.id}")
                    else:
                        print(f"DEBUG: Failed to post ad {ad.id}")
                except Exception as e:
                    print(f"DEBUG: Error posting ad {ad.id}: {e}")
        
        if posted_count > 0:
            print(f"DEBUG: Auto-post completed - {posted_count} ads posted")

async def subscription_expiry_monitor(bot: Bot):
    """Notifies users when their subscription is about to end or has ended."""
    async with async_session() as session:
        from datetime import timedelta
        now = datetime.utcnow()

        # Find users whose sub ended in the last hour to notify them once
        res = await session.execute(
            select(User).where(User.subscription_end_date <= now, User.subscription_end_date >= now - timedelta(hours=1))
        )
        users = res.scalars().all()
        for user in users:
            try:
                from bot.utils.i18n import i18n
                lang = user.language or 'ru'
                await bot.send_message(user.user_id, i18n.get("sub_expired", lang), parse_mode="HTML")
            except:
                pass

def start_jobs(bot: Bot):
    # Cleanup task daily at 03:16 UTC (current time + 1 minute for testing)
    scheduler.add_job(cleanup_expired_posts, 'cron', hour=3, minute=16, args=[bot], id='daily_cleanup')
    print("Daily cleanup scheduled for 03:16 UTC (test)")
    
    # Cleanup task daily at settings time
    async def schedule_cleanup():
        async with async_session() as session:
            from database.models import GlobalSettings
            res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
            settings = res.scalar_one_or_none()
            
            if settings and settings.cleanup_hour is not None and settings.cleanup_minute is not None:
                hour = settings.cleanup_hour
                minute = settings.cleanup_minute
            else:
                hour, minute = 19, 0  # Default 19:00 UTC
            
            # Remove existing job if any
            try:
                scheduler.remove_job('daily_cleanup')
            except:
                pass
            
            # Add new job with settings time
            scheduler.add_job(
                cleanup_expired_posts, 
                'cron', 
                hour=hour, 
                minute=minute, 
                args=[bot],
                id='daily_cleanup'
            )
            print(f"Daily cleanup scheduled for {hour:02d}:{minute:02d} UTC")
    
    # Schedule the cleanup
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.create_task(schedule_cleanup())
    else:
        loop.run_until_complete(schedule_cleanup())

    # Expiry monitor every hour
    scheduler.add_job(
        subscription_expiry_monitor,
        'interval',
        hours=1,
        args=[bot]
    )

    # Daily check with dynamic time from settings
    async def schedule_daily_check():
        async with async_session() as session:
            from database.models import GlobalSettings
            res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
            settings = res.scalar_one_or_none()
            
            if settings:
                hour = settings.daily_check_hour or 9
                minute = settings.daily_check_minute or 0
            else:
                hour, minute = 9, 0
            
            # Remove existing job if any
            try:
                scheduler.remove_job('daily_check')
            except:
                pass
            
            # Add new job with settings time
            scheduler.add_job(
                daily_availability_check, 
                'cron', 
                hour=hour, 
                minute=minute, 
                args=[bot],
                id='daily_check'
            )
            print(f"Daily check scheduled for {hour:02d}:{minute:02d} UTC")

    # Schedule the daily check
    import asyncio
    asyncio.create_task(schedule_daily_check())

    # Auto-post check (more frequent so 1h interval works reliably)
    scheduler.add_job(auto_post_scheduler_task, 'interval', minutes=1, args=[bot])
