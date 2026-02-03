# bot/utils/ad_limits.py
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Ad
from config import DAILY_AD_LIMIT

# Bir vaqtda nechta e'lon "pending/active" bo'lib turishi mumkin (hozir cheksizga yaqin)
MAX_ADS_PER_USER = 999
SLOT_STATUSES = ("pending", "active")


def _start_of_today_utc() -> datetime:
    # SQLite'da timezone saqlanmaydi, shuning uchun UTC bo'yicha kesamiz
    now = datetime.utcnow()
    return datetime(now.year, now.month, now.day)


async def get_used_slots(session: AsyncSession, user_id: int) -> int:
    res = await session.execute(
        select(func.count(Ad.id)).where(
            Ad.user_id == user_id,
            Ad.status.in_(SLOT_STATUSES),
        )
    )
    return int(res.scalar() or 0)


async def has_free_slot(session: AsyncSession, user_id: int) -> bool:
    used = await get_used_slots(session, user_id)
    return used < MAX_ADS_PER_USER


async def get_today_count(session: AsyncSession, user_id: int) -> int:
    """Bugun user nechta e'lonni 'pending/active'ga yuborganini sanaydi."""
    start = _start_of_today_utc()
    res = await session.execute(
        select(func.count(Ad.id)).where(
            Ad.user_id == user_id,
            Ad.status.in_(SLOT_STATUSES),
            Ad.created_at >= start,
        )
    )
    return int(res.scalar() or 0)


async def has_daily_quota(session: AsyncSession, user_id: int) -> bool:
    """Kunlik limit (2 ta) tugamaganmi?"""
    if DAILY_AD_LIMIT <= 0:
        return True
    return (await get_today_count(session, user_id)) < DAILY_AD_LIMIT
