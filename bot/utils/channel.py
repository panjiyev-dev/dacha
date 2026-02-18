# bot/utils/channel.py
from aiogram import Bot, types
from aiogram.utils.media_group import MediaGroupBuilder
from database.setup import async_session
from database.models import Ad, ChannelPost
from sqlalchemy import select, delete, update
from datetime import datetime, timedelta
import config
from sqlalchemy import select, update
import json

def normalize_photos(raw) -> list[str]:
    """
    DB'dan keladigan photos har xil bo'lishi mumkin:
    - list: ["file_id1", ...]
    - json string: '["file_id1", ...]'
    - double json: '"[\\"file_id1\\", ...]"'
    - bo'sh / None
    Shu hammasini bir xil list[str] ko'rinishiga keltiradi.
    """
    if not raw:
        return []

    # allaqachon list bo'lsa
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, str) and x.strip()]

    # string bo'lsa parse qilamiz
    if isinstance(raw, str):
        s = raw.strip()

        # ba'zida DB ga "[]" yoki "" tushib qoladi
        if s in ("[]", '""', "''"):
            return []

        try:
            obj = json.loads(s)  # 1-marta
            # double-json bo'lsa, yana bir marta
            if isinstance(obj, str):
                obj2 = json.loads(obj)
                obj = obj2
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, str) and x.strip()]
        except Exception:
            return []

    return []

# async def post_ad_to_channel(bot: Bot, ad: Ad):
#     """Posts an ad to the configured channels and records message IDs for deletion."""
#     import html
#     from bot.utils.i18n import i18n
    
#     # Use the ad's stored language if available, fallback to ru
#     lang = getattr(ad, 'language', 'ru') or 'ru'
    
#     price_label = i18n.get("price_label", lang)
#     contact_label = i18n.get("contact_label", lang)
    
#     text = (
#         f"🌟 <b>{html.escape(ad.title or '')}</b>\n"
#         f"───────────────────\n\n"
#         f"📝 {html.escape(ad.description or '')}\n\n"
#         f"{price_label} {html.escape(ad.price or '')}\n"
#         f"{contact_label} {html.escape(ad.phone or '')}\n\n"
#         f"───────────────────\n"
#         f"🏢 #DachaLive"
#     )
    
#     async with async_session() as session:
#         # Get settings
#         from database.models import GlobalSettings
#         res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
#         settings = res.scalar_one_or_none()
        
#         target_channels = settings.target_channels if settings and settings.target_channels else [config.CHANNEL_ID]
#         duration = settings.post_duration_hours if settings else 24
        
#         for chat_id in target_channels:
#             try:
#                 # aiogram 3.x media group
#                 if ad.photos:
#                     media = MediaGroupBuilder(caption=text)
#                     for file_id in ad.photos:
#                         media.add_photo(media=file_id, parse_mode="HTML")
                    
#                     messages = await bot.send_media_group(chat_id=chat_id, media=media.build())
#                     for msg in messages:
#                         post = ChannelPost(
#                             ad_id=ad.id,
#                             message_id=msg.message_id,
#                             chat_id=chat_id,
#                             delete_at=datetime.utcnow() + timedelta(hours=duration)
#                         )
#                         session.add(post)
#                 else:
#                     msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
#                     post = ChannelPost(
#                         ad_id=ad.id,
#                         message_id=msg.message_id,
#                         chat_id=chat_id,
#                         delete_at=datetime.utcnow() + timedelta(hours=duration)
#                     )
#                     session.add(post)
                
#                 # Update last_posted_at
#                 await session.execute(update(Ad).where(Ad.id == ad.id).values(last_posted_at=datetime.utcnow()))
                
#             except Exception as e:
#                 print(f"Failed to post to channel {chat_id}: {e}")
        
#         await session.commit()

# async def post_ad_to_channel(bot: Bot, ad: Ad) -> bool:
#     """
#     Kanal(lar)ga e'lon post qiladi va ChannelPost jadvaliga message_id saqlaydi.
#     Return:
#       True  -> kamida bitta kanalga muvaffaqiyatli yuborildi
#       False -> birorta kanalga ham yuborilmadi
#     """
#     import html
#     from bot.utils.i18n import i18n
#     from database.models import GlobalSettings

#     # ad.language bo'lsa shu til, bo'lmasa ru
#     lang = getattr(ad, "language", "ru") or "ru"

#     price_label = i18n.get("price_label", lang)
#     contact_label = i18n.get("contact_label", lang)

#     text = (
#         f"🌟 <b>{html.escape(ad.title or '')}</b>\n"
#         f"───────────────────\n\n"
#         f"📝 {html.escape(ad.description or '')}\n\n"
#         f"{price_label} {html.escape(ad.price or '')}\n"
#         f"{contact_label} {html.escape(ad.phone or '')}\n\n"
#         f"───────────────────\n"
#         f"🏢 #DachaLive"
#     )

#     posted_any = False

#     async with async_session() as session:
#         # Settings -> target_channels
#         res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
#         settings = res.scalar_one_or_none()

#         target_channels = (
#             settings.target_channels
#             if settings and settings.target_channels
#             else [config.CHANNEL_ID]
#         )
#         duration = settings.post_duration_hours if settings else 24

#         for chat_id in target_channels:
#             try:
#                 if ad.photos:
#                     media = MediaGroupBuilder()
#                     # Caption faqat birinchi elementga qo'yiladi
#                     first = True
#                     for file_id in ad.photos:
#                         if first:
#                             media.add_photo(media=file_id, caption=text, parse_mode="HTML")
#                             first = False
#                         else:
#                             media.add_photo(media=file_id)

#                     messages = await bot.send_media_group(chat_id=chat_id, media=media.build())
#                     for msg in messages:
#                         session.add(ChannelPost(
#                             ad_id=ad.id,
#                             message_id=msg.message_id,
#                             chat_id=chat_id,
#                             delete_at=datetime.utcnow() + timedelta(hours=duration)
#                         ))
#                 else:
#                     msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
#                     session.add(ChannelPost(
#                         ad_id=ad.id,
#                         message_id=msg.message_id,
#                         chat_id=chat_id,
#                         delete_at=datetime.utcnow() + timedelta(hours=duration)
#                     ))

#                 posted_any = True

#             except Exception as e:
#                 print(f"Failed to post to channel {chat_id}: {e}")

#         if posted_any:
#             await session.execute(
#                 update(Ad).where(Ad.id == ad.id).values(last_posted_at=datetime.utcnow())
#             )

#         await session.commit()

#     return posted_any

async def post_ad_to_channel(bot: Bot, ad: Ad) -> bool:
    """
    Kanal(lar)ga e'lon post qiladi va ChannelPost jadvaliga message_id saqlaydi.
    Return:
      True  -> kamida bitta kanalga muvaffaqiyatli yuborildi
      False -> birorta kanalga ham yuborilmadi
    """
    import html
    from bot.utils.i18n import i18n
    from database.models import GlobalSettings

    lang = getattr(ad, "language", "ru") or "ru"

    price_label = i18n.get("price_label", lang)
    contact_label = i18n.get("contact_label", lang)

    text = (
        f"🌟 <b>{html.escape(ad.title or '')}</b>\n"
        f"───────────────────\n\n"
        f"📝 {html.escape(ad.description or '')}\n\n"
        f"{price_label} {html.escape(ad.price or '')}\n"
        f"{contact_label} {html.escape(ad.phone or '')}\n\n"
        f"───────────────────\n"
        f"🏢 #DachaLive"
    )

    posted_any = False

    # ✅ har doim list[str] bo'lib keladi va tozalanadi
    photos = normalize_photos(ad.photos)
    photos = photos[:10]  # ✅ telegram limit

    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()

        target_channels = (
            settings.target_channels
            if settings and settings.target_channels
            else [config.CHANNEL_ID]
        )
        duration = settings.post_duration_hours if settings else 24

        for chat_id in target_channels:
            try:
                if photos:
                    media = MediaGroupBuilder()
                    first = True
                    for file_id in photos:
                        if first:
                            media.add_photo(media=file_id, caption=text, parse_mode="HTML")
                            first = False
                        else:
                            media.add_photo(media=file_id)

                    messages = await bot.send_media_group(chat_id=chat_id, media=media.build())

                    for msg in messages:
                        session.add(ChannelPost(
                            ad_id=ad.id,
                            message_id=msg.message_id,
                            chat_id=chat_id,
                            delete_at=datetime.utcnow() + timedelta(hours=duration)
                        ))
                else:
                    msg = await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
                    session.add(ChannelPost(
                        ad_id=ad.id,
                        message_id=msg.message_id,
                        chat_id=chat_id,
                        delete_at=datetime.utcnow() + timedelta(hours=duration)
                    ))

                posted_any = True

            except Exception as e:
                print(f"Failed to post to channel {chat_id}: {e}")

        if posted_any:
            await session.execute(
                update(Ad).where(Ad.id == ad.id).values(last_posted_at=datetime.utcnow())
            )

        await session.commit()

    return posted_any

async def cleanup_expired_posts(bot: Bot, force_cleanup: bool = False):
    """
    Deletes posts from the channel.
    
    Args:
        bot: Bot instance
        force_cleanup: If True, deletes all posts immediately regardless of time
    """
    now = datetime.utcnow()
    current_hour = now.hour
    current_minute = now.minute
    
    # Check settings time unless force_cleanup is True
    if not force_cleanup:
        async with async_session() as session:
            from database.models import GlobalSettings
            res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
            settings = res.scalar_one_or_none()
            
            if settings and settings.cleanup_hour is not None and settings.cleanup_minute is not None:
                cleanup_hour = settings.cleanup_hour
                cleanup_minute = settings.cleanup_minute
            else:
                cleanup_hour, cleanup_minute = 19, 0  # Default 19:00 UTC
            
            # Only delete at exactly the configured time
            print(f"Time check: current={current_hour:02d}:{current_minute:02d}, target={cleanup_hour:02d}:{cleanup_minute:02d}")
            if not (current_hour == cleanup_hour and current_minute == cleanup_minute):
                print("Time mismatch - cleanup not running")
                return False, 0
            print(f"Running scheduled cleanup at {cleanup_hour:02d}:{cleanup_minute:02d} UTC")
    else:
        print(f"Running forced cleanup")
    
    async with async_session() as session:
        # Get ALL posts regardless of delete_at time
        res = await session.execute(select(ChannelPost))
        posts = res.scalars().all()
        
        if not posts:
            print(f"No posts to delete {'(forced)' if force_cleanup else 'at 19:00'}")
            return
        
        for post in posts:
            try:
                await bot.delete_message(chat_id=post.chat_id, message_id=post.message_id)
                print(f"Deleted message {post.message_id} from channel {post.chat_id}")
            except Exception as e:
                print(f"Failed to delete message {post.message_id}: {e}")
            
            await session.delete(post)
        
        await session.commit()
        print(f"Cleaned up {len(posts)} posts {'(forced)' if force_cleanup else 'at 19:00 UTC'}")
        return True, len(posts)

async def delete_ad_everywhere(bot: Bot, ad_id: int) -> tuple[bool, int]:
    """
    Ad'ni hamma joydan o'chiradi:
      1) ChannelPost jadvalidagi message'larni kanaldan delete qiladi
      2) ChannelPost yozuvlarini DB'dan o'chiradi
      3) Ad'ni DB'dan o'chiradi

    Returns: (ok, deleted_messages_count)
    """
    deleted_count = 0

    async with async_session() as session:
        # 1) Channel postlarni topamiz
        res = await session.execute(select(ChannelPost).where(ChannelPost.ad_id == ad_id))
        posts = res.scalars().all()

        # 2) Kanal(lar)dan message'larni o'chiramiz
        for post in posts:
            try:
                await bot.delete_message(chat_id=post.chat_id, message_id=post.message_id)
                deleted_count += 1
            except Exception as e:
                # message allaqachon o'chgan bo'lishi mumkin — shunda ham DB'dan tozalaymiz
                print(f"Failed to delete message {post.message_id} in {post.chat_id}: {e}")

        # 3) ChannelPost yozuvlarini DB'dan o'chiramiz
        await session.execute(delete(ChannelPost).where(ChannelPost.ad_id == ad_id))

        # 4) Ad'ni DB'dan o'chiramiz
        ad_res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad_obj = ad_res.scalar_one_or_none()
        if not ad_obj:
            await session.commit()
            return False, deleted_count

        await session.execute(delete(Ad).where(Ad.id == ad_id))
        await session.commit()

    return True, deleted_count
