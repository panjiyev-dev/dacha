# common.py
import json
import os
from datetime import datetime, timedelta

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states import AuthStates
from bot.utils.i18n import i18n

from database.setup import async_session
from database.models import User, Admin, ActivationCode
from sqlalchemy import select

from config import SUPER_ADMIN_IDS, ADMIN_CODES, SUBSCRIPTION_DAYS

router = Router()


# Simple locale loader (optional)
def load_locale(lang_code: str):
    try:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "locales", f"{lang_code}.json")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()

    kb = [
        [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

    welcome_text = (
        "🌟 <b>Welcome to Dacha Live!</b>\n"
        "───────────────────\n\n"
        "Пожалуйста, выберите язык:\n"
        "Iltimos, tilni tanlang:\n"
        "Please choose your language:"
    )

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode="HTML")
    await state.set_state(AuthStates.choosing_lang)


@router.message(Command("language"))
async def cmd_language(message: types.Message, state: FSMContext):
    await state.clear()

    kb = [
        [types.InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")],
        [types.InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
        [types.InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")],
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=kb)

    await message.answer(
        "🌐 <b>Select Language / Выберите язык / Tilni tanlang:</b>",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AuthStates.choosing_lang)
    await state.update_data(updating_lang=True)


@router.callback_query(AuthStates.choosing_lang, F.data.startswith("lang_"))
async def language_chosen(callback: types.CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id

    data = await state.get_data()
    is_updating = data.get("updating_lang", False)

    async with async_session() as session:
        # Upsert user + language
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, language=lang_code)
            session.add(user)
        else:
            user.language = lang_code

        # ✅ SUPER ADMIN: avtomatik admin + 100 yil subscription
        if user_id in SUPER_ADMIN_IDS:
            admin_res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not admin_res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))

            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            await session.commit()

            kb = [
                [types.KeyboardButton(text=i18n.get("create_ad", lang_code))],
                [types.KeyboardButton(text=i18n.get("my_ads", lang_code))],
            ]

            await callback.message.answer(
                "✅ <b>Admin access granted!</b>\n"
                "Usage: /settings, /generate_code, /user_ads",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=kb,
                    resize_keyboard=True
                ),
                parse_mode="HTML",
            )

            await callback.message.delete()
            await state.clear()
            return
        await session.commit()

    # 🔽 Tilni o‘zgartirish bo‘lsa
    if is_updating:
        kb = [
            [types.KeyboardButton(text=i18n.get("create_ad", lang_code))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang_code))],
        ]
        await callback.message.answer(
            i18n.get("lang_updated", lang_code),
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
        )
        await callback.message.delete()
        await state.clear()
        return

    # 🔽 Oddiy user: kod kiritishga o‘tkazamiz
    await state.update_data(language=lang_code)
    await callback.message.answer(i18n.get("enter_code", lang_code), parse_mode="HTML")
    await callback.message.delete()
    await state.set_state(AuthStates.entering_code)


@router.message(AuthStates.entering_code)
async def process_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    user_id = message.from_user.id

    data = await state.get_data()
    lang = data.get("language", "ru")

    # ✅ ADMIN_CODES (masalan admin123) faqat SUPER_ADMIN ishlatsin
    if code in ADMIN_CODES:
        if user_id not in SUPER_ADMIN_IDS:
            await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
            return

        async with async_session() as session:
            # Admin jadvaliga upsert
            res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))

            # User jadvaliga upsert
            user_res = await session.execute(select(User).where(User.user_id == user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                user = User(user_id=user_id, language=lang)
                session.add(user)
            else:
                user.language = lang

            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            await session.commit()

        kb = [
            [types.KeyboardButton(text=i18n.get("create_ad", lang))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang))],
        ]

        # ✅ “Usage ...” faqat SUPER_ADMIN ko‘radi
        await message.answer(
            "✅ Admin access granted!\nUsage: /settings, /generate_code, /user_ads",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True),
        )
        await state.clear()
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

        if activation_code:
            activation_code.is_used = True
            activation_code.used_by = user_id
            activation_code.used_at = datetime.utcnow()

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
                [types.KeyboardButton(text=i18n.get("my_ads", lang))],
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

            date_str = end_date.strftime("%d.%m.%Y %H:%M")
            await message.answer(
                i18n.get("sub_active", lang, date=date_str),
                reply_markup=keyboard,
                parse_mode="HTML",
            )
            await state.clear()
            return

    # ❌ Noto‘g‘ri kod
    await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    from bot.handlers.ad_creation import get_user_lang, is_admin

    user_id = message.from_user.id
    lang = await get_user_lang(user_id)

    text = i18n.get("help_user", lang)
    if await is_admin(user_id):
        text += f"\n\n{i18n.get('help_admin', lang)}"

    await message.answer(text, parse_mode="HTML")
