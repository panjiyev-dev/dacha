# admin.py
from aiogram import Router, types, F, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, update, delete, func
from datetime import datetime
import uuid
import html

from database.setup import async_session
from database.models import Ad, User, ActivationCode, GlobalSettings

from bot.states import AdminStates
from bot.utils.i18n import i18n
from bot.channel_utils import post_ad_to_channel
from bot.preview_utils import send_ad_preview

from config import SUPER_ADMIN_IDS  # ✅ faqat glavni adminlar

router = Router()


def is_super_admin_id(user_id: int) -> bool:
    return int(user_id) in set(SUPER_ADMIN_IDS or [])


async def notify_admins_new_ad(bot: Bot, ad_id: int):
    """
    ✅ Endi e'lon kelganda faqat SUPER_ADMIN'larga yuboriladi.
    """
    async with async_session() as session:
        ad_res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad = ad_res.scalar_one_or_none()
        if not ad:
            return

        for admin_id in (SUPER_ADMIN_IDS or []):
            admin_id = int(admin_id)

            # ❗ e'lon egasiga admin tugmalarini yubormaymiz
            if admin_id == ad.user_id:
                continue

            try:
                admin_user_res = await session.execute(
                    select(User).where(User.user_id == admin_id)
                )
                admin_user = admin_user_res.scalar_one_or_none()
                admin_lang = admin_user.language if admin_user else "uz"

                price_label = i18n.get("price_label", admin_lang)
                contact_label = i18n.get("contact_label", admin_lang)
                new_ad_label = i18n.get("admin_new_ad", admin_lang)

                text = (
                    f"{new_ad_label}\n"
                    f"───────────────────\n\n"
                    f"🌟 <b>{html.escape(ad.title or '')}</b>\n\n"
                    f"📝 {html.escape(ad.description or '')}\n\n"
                    f"{price_label} {html.escape(ad.price or '')}\n"
                    f"{contact_label} {html.escape(ad.phone or '')}\n\n"
                    f"───────────────────\n"
                    f"🆔 ID: #ad{ad.id} | User: {ad.user_id}"
                )

                kb = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=i18n.get("btn_approve", admin_lang), callback_data=f"approve_{ad.id}")],
                    [types.InlineKeyboardButton(text=i18n.get("btn_reject", admin_lang), callback_data=f"reject_{ad.id}")],
                    [types.InlineKeyboardButton(text=i18n.get("btn_delete", admin_lang), callback_data=f"delete_ad_{ad.id}")]
                ])

                await send_ad_preview(bot, admin_id, ad, kb)

                if ad.photos:
                    await bot.send_photo(admin_id, ad.photos[0], caption=text, reply_markup=kb, parse_mode="HTML")
                else:
                    await bot.send_message(admin_id, text, reply_markup=kb, parse_mode="HTML")

            except:
                pass


@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(callback: types.CallbackQuery, lang: str):
    if not is_super_admin_id(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    ad_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad = res.scalar_one_or_none()

        if not ad:
            await callback.answer("Ad topilmadi", show_alert=True)
            return

        await session.execute(update(Ad).where(Ad.id == ad_id).values(status="active"))
        await session.commit()

        # userga xabar
        from bot.handlers.ad_creation import get_user_lang
        user_lang = await get_user_lang(ad.user_id)
        try:
            await callback.bot.send_message(ad.user_id, i18n.get("ad_approved", user_lang), parse_mode="HTML")
        except:
            pass

        # kanalga post
        try:
            ok = await post_ad_to_channel(callback.bot, ad)
            if not ok:
                await callback.message.answer("⚠️ Kanalga yuborib bo‘lmadi. (post_ad_to_channel=False)")
        except Exception as e:
            await callback.message.answer(f"⚠️ Kanalga yuborishda xatolik: {e}")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(i18n.get("admin_approved", lang, id=ad_id))
    await callback.answer(i18n.get("admin_approved", lang, id=ad_id).split('.')[0])


@router.callback_query(F.data.startswith("reject_"))
async def reject_ad(callback: types.CallbackQuery, lang: str):
    if not is_super_admin_id(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    ad_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        res = await session.execute(select(Ad).where(Ad.id == ad_id))
        ad = res.scalar_one_or_none()
        if ad:
            await session.execute(update(Ad).where(Ad.id == ad_id).values(status="rejected"))
            await session.commit()

            from bot.handlers.ad_creation import get_user_lang
            user_lang = await get_user_lang(ad.user_id)
            try:
                await callback.bot.send_message(ad.user_id, i18n.get("ad_rejected", user_lang), parse_mode="HTML")
            except:
                pass

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(i18n.get("admin_rejected", lang, id=ad_id))
    await callback.answer(i18n.get("admin_rejected", lang, id=ad_id).split('.')[0])


@router.callback_query(F.data.startswith("delete_ad_"))
async def delete_ad_handler(callback: types.CallbackQuery, lang: str):
    if not is_super_admin_id(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    ad_id = int(callback.data.split("_")[2])

    async with async_session() as session:
        await session.execute(delete(Ad).where(Ad.id == ad_id))
        await session.commit()

    await callback.message.delete()
    await callback.message.answer(i18n.get("admin_deleted_db", lang, id=ad_id))
    await callback.answer(i18n.get("admin_deleted_db", lang, id=ad_id).split('.')[0])


@router.message(Command("block_user"))
async def cmd_block_user(message: types.Message, command: CommandObject, lang: str):
    if not is_super_admin_id(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /block_user <user_id>")
        return

    try:
        target_id = int(command.args)
        async with async_session() as session:
            await session.execute(update(User).where(User.user_id == target_id).values(is_blocked=True))
            await session.commit()
        await message.answer(i18n.get("admin_block_success", lang, id=target_id))
    except ValueError:
        await message.answer(i18n.get("admin_invalid_id", lang))


@router.message(Command("unblock_user"))
async def cmd_unblock_user(message: types.Message, command: CommandObject, lang: str):
    if not is_super_admin_id(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /unblock_user <user_id>")
        return

    try:
        target_id = int(command.args)
        async with async_session() as session:
            await session.execute(update(User).where(User.user_id == target_id).values(is_blocked=False))
            await session.commit()
        await message.answer(i18n.get("admin_unblock_success", lang, id=target_id))
    except ValueError:
        await message.answer(i18n.get("admin_invalid_id", lang))


@router.message(Command("generate_code"))
async def cmd_generate_code(message: types.Message, lang: str):
    """
    ✅ Faqat SUPER_ADMIN generatsiya qiladi.
    ✅ 1 martalik activation code.
    """
    if not is_super_admin_id(message.from_user.id):
        return

    code = str(uuid.uuid4())[:8].upper()

    async with async_session() as session:
        new_code = ActivationCode(
            code=code,
            created_by=message.from_user.id,
            is_used=False,
            created_at=datetime.utcnow()
        )
        session.add(new_code)
        await session.commit()

    await message.answer(
        f"{i18n.get('admin_code_label', lang)}\n"
        f"───────────────────\n\n"
        f"<code>{code}</code>\n\n"
        f"{i18n.get('admin_code_info', lang)}",
        parse_mode="HTML"
    )


@router.message(Command("stats"))
async def cmd_stats(message: types.Message, lang: str):
    if not is_super_admin_id(message.from_user.id):
        return

    async with async_session() as session:
        user_count_res = await session.execute(select(func.count(User.user_id)))
        total_users = user_count_res.scalar()

        active_subs_res = await session.execute(
            select(func.count(User.user_id)).where(User.subscription_end_date > datetime.utcnow())
        )
        active_subs = active_subs_res.scalar()

        total_ads_res = await session.execute(select(func.count(Ad.id)))
        total_ads = total_ads_res.scalar()

        active_ads_res = await session.execute(select(func.count(Ad.id)).where(Ad.status == "active"))
        active_ads = active_ads_res.scalar()

    text = (
        f"{i18n.get('stats_title', lang)}\n"
        f"───────────────────\n\n"
        f"{i18n.get('total_users', lang, count=total_users)}\n"
        f"{i18n.get('active_subs', lang, count=active_subs)}\n\n"
        f"{i18n.get('total_ads', lang, count=total_ads)}\n"
        f"{i18n.get('active_ads', lang, count=active_ads)}\n"
        f"───────────────────"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("settings"))
async def cmd_settings(message: types.Message, lang: str, user_id: int = None):
    uid = user_id or message.from_user.id
    if not is_super_admin_id(uid):
        return

    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()

        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
            await session.commit()

    text = (
        f"{i18n.get('settings_title', lang)}\n"
        f"───────────────────\n\n"
        f"{i18n.get('settings_channels', lang)} <code>{', '.join(settings.target_channels) if settings.target_channels else 'None'}</code>\n"
        f"{i18n.get('settings_freq', lang, h=settings.post_frequency_hours)}\n"
        f"{i18n.get('settings_dur', lang, h=settings.post_duration_hours)}\n\n"
        f"───────────────────"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=i18n.get("settings_channels", lang).split(":")[0].strip(), callback_data="set_channels")],
        [types.InlineKeyboardButton(text=i18n.get("settings_freq", lang, h="").split(":")[0].strip(), callback_data="set_freq")],
        [types.InlineKeyboardButton(text=i18n.get("settings_dur", lang, h="").split(":")[0].strip(), callback_data="set_dur")],
        [types.InlineKeyboardButton(text=i18n.get("main_menu", lang), callback_data="refresh_settings")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "refresh_settings")
async def refresh_settings(callback: types.CallbackQuery, lang: str):
    if not is_super_admin_id(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.delete()
    await cmd_settings(callback.message, lang, user_id=callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.in_({"set_channels", "set_freq", "set_dur"}))
async def process_setting_edit(callback: types.CallbackQuery, state: FSMContext, lang: str):
    if not is_super_admin_id(callback.from_user.id):
        await callback.answer()
        return

    action = callback.data
    await state.update_data(editing_setting=action)

    prompts = {
        "set_channels": i18n.get("set_channels_prompt", lang),
        "set_freq": i18n.get("set_freq_prompt", lang),
        "set_dur": i18n.get("set_dur_prompt", lang)
    }

    await callback.message.answer(f"🛠️ <b>{prompts[action]}</b>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_setting_value)
    await callback.answer()


@router.message(AdminStates.waiting_for_setting_value)
async def save_setting_value(message: types.Message, state: FSMContext, lang: str):
    if not is_super_admin_id(message.from_user.id):
        return

    data = await state.get_data()
    setting = data.get("editing_setting")
    value = message.text.strip()

    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one()

        try:
            if setting == "set_channels":
                channels = [c.strip() for c in value.split(",") if c.strip()]
                settings.target_channels = channels
                await message.answer(i18n.get("save_success_channels", lang, val=", ".join(channels)), parse_mode="HTML")
            elif setting == "set_freq":
                val = int(value)
                if val < 1:
                    raise ValueError
                settings.post_frequency_hours = val
                await message.answer(i18n.get("save_success_freq", lang, val=val), parse_mode="HTML")
            elif setting == "set_dur":
                val = int(value)
                if val < 1:
                    raise ValueError
                settings.post_duration_hours = val
                await message.answer(i18n.get("save_success_dur", lang, val=val), parse_mode="HTML")

            await session.commit()
            await state.clear()
            await cmd_settings(message, lang)
        except ValueError:
            await message.answer(i18n.get("save_error_int", lang), parse_mode="HTML")
            await state.clear()
            await cmd_settings(message, lang)


@router.message(Command("user_ads"))
async def cmd_user_ads(message: types.Message, command: CommandObject, lang: str):
    if not is_super_admin_id(message.from_user.id):
        return

    if not command.args:
        await message.answer("Usage: /user_ads <user_id>")
        return

    try:
        target_id = int(command.args)
        async with async_session() as session:
            res = await session.execute(select(Ad).where(Ad.user_id == target_id))
            ads = res.scalars().all()

            if not ads:
                await message.answer(i18n.get("admin_no_ads_found", lang))
                return

            await message.answer(i18n.get("admin_user_ads_title", lang, id=target_id), parse_mode="HTML")
            for ad in ads:
                status_emoji = "⏳" if ad.status == "pending" else "✅" if ad.status == "active" else "❌"
                text = (
                    f"🔹 <b>{ad.title or '---'}</b>\n"
                    f"{status_emoji} {ad.status.upper()} | 💰 {ad.price or '---'}\n"
                    f"🆔 ID: #ad{ad.id}"
                )

                kb_rows = [
                    [types.InlineKeyboardButton(text=i18n.get("btn_delete", lang), callback_data=f"delete_ad_{ad.id}")],
                ]
                if ad.status != "active":
                    kb_rows.append([types.InlineKeyboardButton(text=i18n.get("btn_approve", lang), callback_data=f"approve_{ad.id}")])

                kb = types.InlineKeyboardMarkup(inline_keyboard=kb_rows)
                await message.answer(text, reply_markup=kb, parse_mode="HTML")

    except ValueError:
        await message.answer(i18n.get("admin_invalid_id", lang))
