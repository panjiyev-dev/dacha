# # bot/channel_utils.py
# from telegram import InputMediaPhoto
# from telegram.ext import ContextTypes
# from config import CHANNEL_ID
# from database import Ad, get_user, update_ad_posted_time
# from datetime import datetime
# import logging

# logger = logging.getLogger(__name__)

# async def post_ad_to_channel(context: ContextTypes.DEFAULT_TYPE, ad: Ad):
#     """Post an ad to the configured channel."""
#     try:
#         user = get_user(ad.owner_id)
#         contact_info = f"@{user.username}" if user and user.username else "N/A"
        
#         caption = f"🏡 *{ad.title}*\n\n{ad.description}\n\n💰 Price: {ad.price}\n📍 Location: {ad.location}\n\n📞 Contact: {contact_info}"
        
#         media = []
#         if ad.video:
#              from telegram import InputMediaVideo
#              media.append(InputMediaVideo(media=ad.video, caption=caption, parse_mode='Markdown'))
             
#         if ad.photos:
#             for p in ad.photos:
#                  # If video exists, it took the caption.
#                  # If no video, first photo takes caption.
#                  has_caption = len(media) > 0
#                  media.append(InputMediaPhoto(media=p, caption=caption if not has_caption else None, parse_mode='Markdown'))
        
#         if media:
#              if len(media) == 1:
#                   # Single item (video or photo)
#                   if ad.video:
#                       await context.bot.send_video(chat_id=CHANNEL_ID, video=ad.video, caption=caption, parse_mode='Markdown')
#                   else:
#                       await context.bot.send_photo(chat_id=CHANNEL_ID, photo=ad.photos[0], caption=caption, parse_mode='Markdown')
#              else:
#                   await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)

#         else:
#             await context.bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode='Markdown')
            
#         update_ad_posted_time(ad.id, datetime.now().isoformat())
#         logger.info(f"Immediately posted ad {ad.id}")
#         return True
#     except Exception as e:
#         logger.error(f"Failed to post ad {ad.id}: {e}")
#         return False

############################ NEW CODE BELOW ####################################### 

# bot/channel_utils.py
import json
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from sqlalchemy import select

from database.setup import async_session
from database.models import GlobalSettings, ChannelPost

def normalize_photos(raw) -> list[str]:
    """
    DB'dagi photos maydoni:
    - list bo'lishi kerak (ideal)
    - eski xatolar sabab str bo'lib qolgan bo'lishi mumkin
    Shu funksiyada hammasini list[str] ko'rinishiga keltiramiz.
    """
    if not raw:
        return []

    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, str) and x.strip()]

    if isinstance(raw, str):
        s = raw.strip()

        # 1) Birinchi urinish: oddiy json.loads
        try:
            obj = json.loads(s)
            # agar double-dumps bo'lsa: obj yana str bo'ladi
            if isinstance(obj, str):
                obj = json.loads(obj)
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, str) and x.strip()]
        except Exception:
            pass

        # 2) Ikkinchi urinish: "" -> " qilib tozalash
        try:
            s2 = s.strip('"').replace('""', '"')
            obj = json.loads(s2)
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, str) and x.strip()]
        except Exception:
            return []

    return []
