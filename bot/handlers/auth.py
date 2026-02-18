# handlers/auth.py
from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from bot.states import AuthStates
from bot.utils.i18n import i18n

from database.setup import async_session
from database.models import User, ActivationCode, Admin

from sqlalchemy import select
from datetime import datetime, timedelta

from config import ADMIN_CODES, SUBSCRIPTION_DAYS, is_super_admin
from aiogram import F

router = Router()

@router.message(AuthStates.entering_code, F.text.startswith("/"))
async def entering_code_command(message: types.Message):
    await message.answer("ℹ️ Hozir faollashtirish kodi kutilyapti. Kodni yuboring yoki /start bosing.")

@router.message(AuthStates.entering_code)
async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id

    data = await state.get_data()
    lang = data.get("language", "ru")

    # ✅ Safety: Super admin hech qachon bu state'ga tushib qolsa ham — bypass
    if is_super_admin(user_id):
        async with async_session() as session:
            res = await session.execute(select(User).where(User.user_id == user_id))
            user = res.scalar_one_or_none()
            if not user:
                user = User(user_id=user_id, language=lang)
                session.add(user)
            else:
                user.language = lang

            admin_res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not admin_res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))

            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            user.is_blocked = False
            user.draft_id = None
            await session.commit()

        kb = [
            [types.KeyboardButton(text=i18n.get("create_ad", lang))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang))]
        ]
        await message.answer(
            "✅ <b>Admin access granted!</b>\nUsage: /settings, /generate_code, /user_ads",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
            parse_mode="HTML"
        )
        await state.clear()
        return

    # ✅ ADMIN_CODES: oddiy userga admin bo'lishga ruxsat bermaymiz
    if code in ADMIN_CODES:
        await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
        return

    # ✅ 1-martalik ActivationCode (subscription)
    async with async_session() as session:
        result = await session.execute(
            select(ActivationCode).where(
                ActivationCode.code == code,
                ActivationCode.is_used == False
            )
        )
        activation_code = result.scalar_one_or_none()

        if not activation_code:
            await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
            return

        # mark used
        activation_code.is_used = True
        activation_code.used_by = user_id
        activation_code.used_at = datetime.utcnow()

        # upsert user
        user_res = await session.execute(select(User).where(User.user_id == user_id))
        user = user_res.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, language=lang)
            session.add(user)
        else:
            user.language = lang

        end_date = datetime.utcnow() + timedelta(days=SUBSCRIPTION_DAYS)
        user.subscription_end_date = end_date

        await session.commit()

    kb = [
        [types.KeyboardButton(text=i18n.get("create_ad", lang))],
        [types.KeyboardButton(text=i18n.get("my_ads", lang))]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

    date_str = end_date.strftime("%d.%m.%Y %H:%M")
    await message.answer(i18n.get("sub_active", lang, date=date_str), reply_markup=keyboard, parse_mode="HTML")
    await state.clear()
