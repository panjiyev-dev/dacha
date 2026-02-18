# handlers/common.py
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from sqlalchemy import select

from bot.states import AuthStates
from bot.utils.i18n import i18n
from database.setup import async_session
from database.models import User, Admin, ActivationCode
from config import SUPER_ADMIN_IDS, ADMIN_CODES, SUBSCRIPTION_DAYS

router = Router()


def build_main_kb(lang: str) -> types.ReplyKeyboardMarkup:
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=i18n.get("create_ad", lang))],
            [types.KeyboardButton(text=i18n.get("my_ads", lang))]
        ],
        resize_keyboard=True
    )


async def safe_delete(msg: types.Message):
    try:
        await msg.delete()
    except:
        pass


@router.message(Command("myid"))
async def cmd_myid(message: types.Message):
    await message.answer(f"Your Telegram ID: <code>{message.from_user.id}</code>", parse_mode="HTML")


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


@router.callback_query(AuthStates.choosing_lang, F.data.startswith("lang_"))
async def language_chosen(callback: types.CallbackQuery, state: FSMContext):
    lang_code = callback.data.split("_")[1]
    user_id = callback.from_user.id

    # state'ga tilni yozib qo'yamiz (auth.py ham olishi mumkin)
    await state.update_data(language=lang_code)

    async with async_session() as session:
        # Upsert user + language
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, language=lang_code)
            session.add(user)
        else:
            user.language = lang_code

        # ✅ SUPER_ADMIN: darrov admin + subscription (va flaglarni tozalash)
        if user_id in SUPER_ADMIN_IDS:
            admin_res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not admin_res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))

            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            user.is_blocked = False
            user.draft_id = None

            await session.commit()

            await callback.message.answer(
                "✅ <b>Admin access granted!</b>\nUsage: /settings, /generate_code, /user_ads",
                reply_markup=build_main_kb(lang_code),
                parse_mode="HTML",
            )
            await safe_delete(callback.message)
            await state.clear()
            await callback.answer()
            return

        # ✅ Subscription aktiv bo'lsa — kod so'ramaymiz
        if user.subscription_end_date and user.subscription_end_date > datetime.utcnow():
            await session.commit()

            await callback.message.answer(
                i18n.get(
                    "sub_active",
                    lang_code,
                    date=user.subscription_end_date.strftime("%d.%m.%Y %H:%M")
                ),
                reply_markup=build_main_kb(lang_code),
                parse_mode="HTML",
            )
            await safe_delete(callback.message)
            await state.clear()
            await callback.answer()
            return

        await session.commit()

    # 🔽 Oddiy user: kod so'raymiz
    await callback.message.answer(i18n.get("enter_code", lang_code), parse_mode="HTML")
    await safe_delete(callback.message)
    await state.set_state(AuthStates.entering_code)
    await callback.answer()


# ✅ State ichida / komandalarni "kod" deb qabul qilmang
@router.message(AuthStates.entering_code, F.text.startswith("/"))
async def entering_code_commands(message: types.Message):
    await message.answer("ℹ️ Hozir faollashtirish kodi kutilyapti. Kodni yuboring yoki /start bosing.")


@router.message(AuthStates.entering_code)
async def process_code(message: types.Message, state: FSMContext):
    code = (message.text or "").strip()
    user_id = message.from_user.id

    data = await state.get_data()
    lang = data.get("language", "ru")

    # bo'sh / sticker / media kelib qolsa
    if not code:
        await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
        return

    # ✅ ADMIN_CODES (faqat SUPER_ADMIN ishlatsin)
    if code in ADMIN_CODES:
        if user_id not in SUPER_ADMIN_IDS:
            await message.answer(i18n.get("invalid_code", lang), parse_mode="HTML")
            return

        async with async_session() as session:
            admin_res = await session.execute(select(Admin).where(Admin.user_id == user_id))
            if not admin_res.scalar_one_or_none():
                session.add(Admin(user_id=user_id))

            user_res = await session.execute(select(User).where(User.user_id == user_id))
            user = user_res.scalar_one_or_none()
            if not user:
                user = User(user_id=user_id, language=lang)
                session.add(user)
            else:
                user.language = lang

            user.subscription_end_date = datetime.utcnow() + timedelta(days=36500)
            user.is_blocked = False
            user.draft_id = None
            await session.commit()

        await message.answer(
            "✅ Admin access granted!\nUsage: /settings, /generate_code, /user_ads",
            reply_markup=build_main_kb(lang),
        )
        await state.clear()
        return

    # ✅ Activation code
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

    await message.answer(
        i18n.get("sub_active", lang, date=end_date.strftime("%d.%m.%Y %H:%M")),
        reply_markup=build_main_kb(lang),
        parse_mode="HTML",
    )
    await state.clear()
