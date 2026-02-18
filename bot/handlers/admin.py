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
# from bot.channel_utils import post_ad_to_channel
from bot.utils.channel import post_ad_to_channel, delete_ad_everywhere
from bot.preview_utils import send_ad_preview

from config import SUPER_ADMIN_IDS  # ✅ faqat glavni adminlar

router = Router()


def is_super_admin(user_id: int) -> bool:
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

                photos = normalize_photos(ad.photos)

                if photos:
                    await bot.send_photo(admin_id, photos[0], caption=text, reply_markup=kb, parse_mode="HTML")
                else:
                    await bot.send_message(admin_id, text, reply_markup=kb, parse_mode="HTML")

            except:
                pass


@router.callback_query(F.data.startswith("approve_"))
async def approve_ad(callback: types.CallbackQuery, lang: str):
    if not is_super_admin(callback.from_user.id):
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
            # if not ok:
            #     await callback.message.answer("⚠️ Kanalga yuborib bo‘lmadi. (post_ad_to_channel=False)")
            if ok:
                await callback.message.answer("✅ Kanalga yuborildi.")
            else:
                await callback.message.answer("⚠️ Kanalga yuborib bo‘lmadi.")
        except Exception as e:
            await callback.message.answer(f"⚠️ Kanalga yuborishda xatolik: {e}")

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(i18n.get("admin_approved", lang, id=ad_id))
    await callback.answer(i18n.get("admin_approved", lang, id=ad_id).split('.')[0])


@router.callback_query(F.data.startswith("reject_"))
async def reject_ad(callback: types.CallbackQuery, lang: str):
    if not is_super_admin(callback.from_user.id):
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
    if not is_super_admin(callback.from_user.id):
        await callback.answer("❌ Ruxsat yo‘q", show_alert=True)
        return

    ad_id = int(callback.data.split("_")[2])

    ok, deleted_msgs = await delete_ad_everywhere(callback.bot, ad_id)

    try:
        await callback.message.delete()
    except:
        pass

    if ok:
        await callback.message.answer(
            f"✅ E’lon o‘chirildi.\n🗑 Kanal message’lari: {deleted_msgs}\n🗄 DB: o‘chirildi"
        )
    else:
        await callback.message.answer(
            f"⚠️ E’lon DB’da topilmadi (yoki allaqachon o‘chgan).\n🗑 Kanal message’lari: {deleted_msgs}"
        )

    await callback.answer()


@router.message(Command("block_user"))
async def cmd_block_user(message: types.Message, command: CommandObject, lang: str):
    if not is_super_admin(message.from_user.id):
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
    if not is_super_admin(message.from_user.id):
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
    if not is_super_admin(message.from_user.id):
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
    if not is_super_admin(message.from_user.id):
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
    if not is_super_admin(uid):
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
        f"{i18n.get('settings_dur', lang, h=settings.post_duration_hours)}\n"
        f"🕐 Daily check: <code>{(settings.daily_check_hour or 9):02d}:{(settings.daily_check_minute or 0):02d} UTC</code>\n\n"
        f"───────────────────"
    )

    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=i18n.get("settings_channels", lang).split(":")[0].strip(), callback_data="set_channels")],
        [types.InlineKeyboardButton(text=i18n.get("settings_freq", lang, h="").split(":")[0].strip(), callback_data="set_freq")],
        [types.InlineKeyboardButton(text=i18n.get("settings_dur", lang, h="").split(":")[0].strip(), callback_data="set_dur")],
        [types.InlineKeyboardButton(text="🕐 Daily check time", callback_data="set_daily_check")],
        [types.InlineKeyboardButton(text="🗑️ Postlarni o'chirish", callback_data="cleanup_posts")],
        [types.InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="show_users")],
        [types.InlineKeyboardButton(text=i18n.get("main_menu", lang), callback_data="refresh_settings")]
    ])

    await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "refresh_settings")
async def refresh_settings(callback: types.CallbackQuery, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return

    await callback.message.delete()
    await cmd_settings(callback.message, lang, user_id=callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "cleanup_posts")
async def cleanup_posts_prompt(callback: types.CallbackQuery, state: FSMContext, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.answer(
        "🗑️ <b>Postlarni o'chirish</b>\n\n"
        "Barcha postlarni darhol o'chirish uchun \"Hozir\" tugmasini bosing.\n"
        "Ma'lum vaqtda o'chirish uchun vaqtni kiriting (HH:MM formatda):\n"
        "Masalan: <code>15:30</code>\n\n"
        "Yoki \"Bekor qilish\" tugmasini bosing.",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚡ Hozir o'chirish", callback_data="cleanup_now")],
            [types.InlineKeyboardButton(text="🕐 Vaqt kiritish", callback_data="cleanup_schedule")],
            [types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="refresh_settings")]
        ]),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "cleanup_now")
async def cleanup_posts_now(callback: types.CallbackQuery, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from bot.utils.channel import cleanup_expired_posts
    await cleanup_expired_posts(callback.bot, force_cleanup=True)
    
    await callback.message.answer("✅ Barcha postlar o'chirildi!", parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cleanup_schedule")
async def cleanup_posts_schedule(callback: types.CallbackQuery, state: FSMContext, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.answer(
        "🕐 <b>Vaqtni kiriting</b>\n\n"
        "Qaysi vaqtda o'chirish kerak? (HH:MM format)\n"
        "Masalan: <code>15:30</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_cleanup_time)
    await callback.answer()


@router.message(AdminStates.waiting_for_cleanup_time)
async def process_cleanup_time(message: types.Message, state: FSMContext, lang: str):
    if not is_super_admin(message.from_user.id):
        return
    
    try:
        value = message.text.strip()
        
        # Parse HH:MM format
        if ":" not in value:
            raise ValueError("Format HH:MM kerak")
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError("Format HH:MM kerak")
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Soat 0-23, daqiqa 0-59 bo'lishi kerak")
        
        # Schedule cleanup
        from bot.logic.automation import scheduler
        from bot.utils.channel import cleanup_expired_posts
        
        # Remove existing scheduled cleanup job if any
        try:
            scheduler.remove_job('scheduled_cleanup')
        except:
            pass
        
        # Store the scheduled time in database for checking
        async with async_session() as session:
            from database.models import GlobalSettings
            res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
            settings = res.scalar_one_or_none()
            
            if settings:
                settings.cleanup_hour = hour
                settings.cleanup_minute = minute
                await session.commit()
        
        # Create a simple interval job that checks every minute
        def check_and_cleanup():
            import asyncio
            from datetime import datetime
            
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def check_time():
                    now = datetime.utcnow()
                    print(f"Checking cleanup time: current={now.hour:02d}:{now.minute:02d}, target={hour:02d}:{minute:02d}")
                    if now.hour == hour and now.minute == minute:
                        await cleanup_expired_posts(message.bot, force_cleanup=True)
                
                loop.run_until_complete(check_time())
                loop.close()
            except Exception as e:
                print(f"Cleanup check error: {e}")
        
        scheduler.add_job(
            check_and_cleanup,
            'interval',
            minutes=1,
            id='scheduled_cleanup'
        )
        
        await message.answer(
            f"✅ Postlar soat {hour:02d}:{minute:02d} da o'chiriladi!",
            parse_mode="HTML"
        )
        
        # Show current scheduled jobs for debugging
        jobs = scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append(f"{job.id}: {job.next_run_time}")
        
        if job_info:
            await message.answer(f"📅 Active jobs:\n" + "\n".join(job_info))
        
    except ValueError as e:
        await message.answer(f"❌ Xatolik: {str(e)}", parse_mode="HTML")
    
    await state.clear()


@router.callback_query(F.data.in_({"set_channels", "set_freq", "set_dur", "set_daily_check"}))
async def process_setting_edit(callback: types.CallbackQuery, state: FSMContext, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return

    action = callback.data
    await state.update_data(editing_setting=action)

    prompts = {
        "set_channels": i18n.get("set_channels_prompt", lang),
        "set_freq": i18n.get("set_freq_prompt", lang),
        "set_dur": i18n.get("set_dur_prompt", lang),
        "set_daily_check": "🕐 Daily check time (format: HH:MM, UTC)\nMasalan: 14:30"
    }

    await callback.message.answer(f"🛠️ <b>{prompts[action]}</b>", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_setting_value)
    await callback.answer()


@router.message(AdminStates.waiting_for_setting_value)
async def save_setting_value(message: types.Message, state: FSMContext, lang: str):
    if not is_super_admin(message.from_user.id):
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
                val = float(value)
                if val <= 0:
                    raise ValueError
                settings.post_frequency_hours = val
                await message.answer(i18n.get("save_success_freq", lang, val=val), parse_mode="HTML")
            elif setting == "set_dur":
                val = float(value)
                if val <= 0:
                    raise ValueError
                settings.post_duration_hours = val
                await message.answer(i18n.get("save_success_dur", lang, val=val), parse_mode="HTML")
            elif setting == "set_daily_check":
                # Parse HH:MM format
                if ":" not in value:
                    raise ValueError("Format HH:MM kerak")
                parts = value.split(":")
                if len(parts) != 2:
                    raise ValueError("Format HH:MM kerak")
                
                hour = int(parts[0])
                minute = int(parts[1])
                
                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError("Soat 0-23, daqiqa 0-59 bo'lishi kerak")
                
                settings.daily_check_hour = hour
                settings.daily_check_minute = minute
                
                # Reschedule the job
                from bot.logic.automation import daily_availability_check, scheduler
                try:
                    scheduler.remove_job('daily_check')
                except:
                    pass
                
                scheduler.add_job(
                    daily_availability_check,
                    'cron',
                    hour=hour,
                    minute=minute,
                    args=[message.bot],
                    id='daily_check'
                )
                
                await message.answer(f"✅ Daily check time set to {hour:02d}:{minute:02d} UTC", parse_mode="HTML")

            await session.commit()
            await state.clear()
            await cmd_settings(message, lang)
        except ValueError as e:
            await message.answer(f"❌ Xatolik: {str(e)}", parse_mode="HTML")
            await state.clear()
            await cmd_settings(message, lang)


@router.message(Command("users"))
async def cmd_users(message: types.Message, lang: str):
    if not is_super_admin(message.from_user.id):
        return

    async with async_session() as session:
        res = await session.execute(select(User).order_by(User.user_id))
        users = res.scalars().all()
        
        if not users:
            await message.answer("❌ Foydalanuvchilar topilmadi", parse_mode="HTML")
            return

        text = f"👥 <b>Foydalanuvchilar ({len(users)} ta)</b>\n"
        text += "───────────────────\n\n"
        
        for user in users[:10]:  # Birinchi 10 ta foydalanuvchi
            status = "🟢" if not user.is_blocked else "🔴"
            lang_flag = {"ru": "🇷🇺", "uz": "🇺🇿", "en": "🇬🇧"}.get(user.language, "❓")
            sub_status = "✅" if user.subscription_end_date and user.subscription_end_date > datetime.utcnow() else "❌"
            
            text += f"{status} <code>{user.user_id}</code> {lang_flag} {sub_status}\n"
        
        if len(users) > 10:
            text += f"\n...va yana {len(users) - 10} ta foydalanuvchi"
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🗑️ Foydalanuvchini o'chirish", callback_data="delete_user_prompt")],
            [types.InlineKeyboardButton(text="🔙 Orqaga", callback_data="admin_main_menu")]
        ])
        
        await message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data == "delete_user_prompt")
async def delete_user_prompt(callback: types.CallbackQuery, state: FSMContext, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.answer(
        "🗑️ <b>Foydalanuvchini o'chirish</b>\n\n"
        "O'chirish uchun foydalanuvchi IDsini kiriting:\n"
        "Masalan: <code>123456789</code>\n\n"
        "Yoki /myid komandasi orqali o'zingizni IDingizni bilib oling:",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.waiting_for_user_delete)
    await callback.answer()


@router.message(AdminStates.waiting_for_user_delete)
async def process_user_delete(message: types.Message, state: FSMContext, lang: str):
    if not is_super_admin(message.from_user.id):
        return
    
    try:
        target_id = int(message.text.strip())
        
        # O'zini o'chirmaslik uchun tekshirish
        if target_id == message.from_user.id:
            await message.answer("❌ O'zingizni o'chira olmaysiz!", parse_mode="HTML")
            await state.clear()
            return
        
        async with async_session() as session:
            # Foydalanuvchini topish
            user_res = await session.execute(select(User).where(User.user_id == target_id))
            user = user_res.scalar_one_or_none()
            
            if not user:
                await message.answer(f"❌ Foydalanuvchi topilmadi: {target_id}", parse_mode="HTML")
                await state.clear()
                return
            
            # Foydalanuvchining e'lonlarini o'chirish
            from bot.utils.channel import delete_ad_everywhere
            ads_res = await session.execute(select(Ad).where(Ad.user_id == target_id))
            ads = ads_res.scalars().all()
            
            deleted_count = 0
            for ad in ads:
                ok, count = await delete_ad_everywhere(message.bot, ad.id)
                if ok:
                    deleted_count += count
            
            # Foydalanuvchini o'chirish
            await session.execute(delete(User).where(User.user_id == target_id))
            await session.commit()
            
            await message.answer(
                f"✅ Foydalanuvchi {target_id} o'chirildi!\n"
                f"📊 {len(ads)} ta e'lon va {deleted_count} ta xabar o'chirildi.",
                parse_mode="HTML"
            )
            
    except ValueError:
        await message.answer("❌ Noto'g'ri ID formati. Faqat raqam kiriting:", parse_mode="HTML")
    except Exception as e:
        await message.answer(f"❌ Xatolik: {str(e)}", parse_mode="HTML")
    
    await state.clear()


@router.callback_query(F.data == "admin_main_menu")
async def admin_main_menu(callback: types.CallbackQuery, lang: str):
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "⚙️ <b>Admin Panel</b>\n\n"
        "📊 /stats - Statistika\n"
        "👥 /users - Foydalanuvchilar\n"
        "⚙️ /settings - Sozlamalar\n"
        "🎫 /generate_code - Kod yaratish",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(Command("user_ads"))
async def cmd_user_ads(message: types.Message, command: CommandObject, lang: str):
    if not is_super_admin(message.from_user.id):
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


# User Management Callback Handlers
@router.callback_query(F.data == "show_users")
async def handle_show_users(callback: types.CallbackQuery, lang: str):
    """Show users list"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import show_users_menu
    await show_users_menu(callback, lang)


@router.callback_query(F.data == "refresh_users")
async def handle_refresh_users(callback: types.CallbackQuery, lang: str):
    """Refresh users list"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import show_users_menu
    await show_users_menu(callback, lang)


@router.callback_query(F.data.startswith("user_detail_"))
async def handle_user_detail(callback: types.CallbackQuery, lang: str):
    """Show user details"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import show_user_detail
    await show_user_detail(callback, lang)


@router.callback_query(F.data.startswith("block_user_"))
async def handle_block_user(callback: types.CallbackQuery, lang: str):
    """Block user"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import block_user
    await block_user(callback, lang)


@router.callback_query(F.data.startswith("unblock_user_"))
async def handle_unblock_user(callback: types.CallbackQuery, lang: str):
    """Unblock user"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import unblock_user
    await unblock_user(callback, lang)


@router.callback_query(F.data.startswith("delete_user_"))
async def handle_delete_user(callback: types.CallbackQuery, lang: str):
    """Delete user"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import delete_user
    await delete_user(callback, lang)


@router.callback_query(F.data.startswith("confirm_delete_user_"))
async def handle_confirm_delete_user(callback: types.CallbackQuery, lang: str):
    """Confirm delete user"""
    if not is_super_admin(callback.from_user.id):
        await callback.answer()
        return
    
    from user_management import confirm_delete_user
    await confirm_delete_user(callback, lang)
