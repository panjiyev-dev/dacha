# User management uchun handlerlar

from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, delete
from datetime import datetime
from database.setup import async_session
from database.models import User, Ad
from bot.utils.i18n import i18n
from bot.utils.auth import is_super_admin

class UserManagementStates(StatesGroup):
    managing_user = State()

async def show_users_menu(callback: types.CallbackQuery, lang: str, user_id: int = None):
    """Userlarni ko'rsatish menyusi"""
    uid = user_id or callback.from_user.id
    if not is_super_admin(uid):
        return
    
    try:
        async with async_session() as session:
            # Faqat kerakli ma'lumotlarni olish (optimizatsiya)
            res = await session.execute(
                select(User.user_id, User.is_blocked, User.created_at)
                .order_by(User.created_at.desc())
                .limit(20)  # Faqat 20 ta user
            )
            users_data = res.all()
            
            if not users_data:
                await callback.message.edit_text(
                    "👥 <b>Foydalanuvchilar yo'q</b>",
                    parse_mode="HTML"
                )
                return
            
            # Userlarni ro'yxatini tayyorlash
            text = "👥 <b>Foydalanuvchilar ro'yxati:</b>\n\n"
            
            user_buttons = []
            for user_data in users_data:
                user_id, is_blocked, created_at = user_data
                
                # Active e'lonlar soni (tezroq usul)
                ads_res = await session.execute(
                    select(Ad.id).where(Ad.user_id == user_id, Ad.status == 'active')
                )
                active_ads = len(ads_res.scalars().all())
                
                status_emoji = "🟢" if not is_blocked else "🔴"
                
                text += f"{status_emoji} <b>{user_id}</b> "
                text += f"({active_ads} ta active e'lon)\n"
                
                user_buttons.append([
                    types.InlineKeyboardButton(
                        text=f"{status_emoji} {user_id} ({active_ads} ads)",
                        callback_data=f"user_detail_{user_id}"
                    )
                ])
            
            # Tugmalar
            user_buttons.append([
                types.InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_users"),
                types.InlineKeyboardButton(text="⬅️ Orqaga", callback_data="refresh_settings")
            ])
            
            kb = types.InlineKeyboardMarkup(inline_keyboard=user_buttons)
            
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
            
    except Exception as e:
        print(f"Error in show_users_menu: {e}")
        await callback.message.edit_text(
            "❌ <b>Xatolik yuz berdi</b>\n\n"
            "Iltimos, qayta urinib ko'ring.",
            parse_mode="HTML"
        )

async def show_user_detail(callback: types.CallbackQuery, lang: str):
    """User haqida batafsil ma'lumot"""
    user_id = int(callback.data.split("_")[2])
    
    if not is_super_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        # User ma'lumotlari
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        
        if not user:
            await callback.answer("❌ User topilmadi")
            return
        
        # User e'lonlari
        ads_res = await session.execute(
            select(Ad).where(Ad.user_id == user_id).order_by(Ad.created_at.desc())
        )
        ads = ads_res.scalars().all()
        
        # Text tayyorlash
        status = "🟢 Faol" if not user.is_blocked else "🔴 Bloklangan"
        sub_status = "✅ Aktiv" if user.subscription_end_date and user.subscription_end_date > datetime.utcnow() else "❌ Muddati o'tgan"
        
        text = (
            f"👤 <b>User #{user.user_id}</b>\n\n"
            f"📊 Status: {status}\n"
            f"📅 Obuna: {sub_status}\n"
            f"📝 Til: {user.language or 'unknown'}\n"
            f"🕐 Ro'yxatdan o'tgan: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"📋 E'lonlari ({len(ads)} ta):\n"
        )
        
        # E'lonlar ro'yxati
        for ad in ads[:5]:  # Birinchi 5 ta e'lon
            ad_status = "✅" if ad.status == 'active' else "📝" if ad.status == 'draft' else "❌"
            text += f"{ad_status} {ad.title[:30]}... (ID: {ad.id})\n"
        
        if len(ads) > 5:
            text += f"... va yana {len(ads) - 5} ta e'lon"
        
        # Tugmalar
        buttons = []
        if not user.is_blocked:
            buttons.append([
                types.InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"block_user_{user_id}")
            ])
        else:
            buttons.append([
                types.InlineKeyboardButton(text="✅ Blokdan chiqarish", callback_data=f"unblock_user_{user_id}")
            ])
        
        buttons.append([
            types.InlineKeyboardButton(text="🗑️ Userni o'chirish", callback_data=f"delete_user_{user_id}")
        ])
        buttons.append([
            types.InlineKeyboardButton(text="⬅️ Orqaga", callback_data="show_users"),
            types.InlineKeyboardButton(text="🔄 Yangilash", callback_data=f"user_detail_{user_id}")
        ])
        
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

async def block_user(callback: types.CallbackQuery, lang: str):
    """Userni bloklash"""
    user_id = int(callback.data.split("_")[2])
    
    if not is_super_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        
        if user:
            user.is_blocked = True
            await session.commit()
            await callback.answer(f"✅ User #{user_id} bloklandi")
            
            # User detailga qaytish
            await show_user_detail(callback, lang)
        else:
            await callback.answer("❌ User topilmadi")

async def unblock_user(callback: types.CallbackQuery, lang: str):
    """Userni blokdan chiqarish"""
    user_id = int(callback.data.split("_")[2])
    
    if not is_super_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        res = await session.execute(select(User).where(User.user_id == user_id))
        user = res.scalar_one_or_none()
        
        if user:
            user.is_blocked = False
            await session.commit()
            await callback.answer(f"✅ User #{user_id} blokdan chiqarildi")
            
            # User detailga qaytish
            await show_user_detail(callback, lang)
        else:
            await callback.answer("❌ User topilmadi")

async def delete_user(callback: types.CallbackQuery, lang: str):
    """Userni o'chirish (diqqat bilan!)"""
    user_id = int(callback.data.split("_")[2])
    
    if not is_super_admin(callback.from_user.id):
        return
    
    # Tasdiqlash tugmalari
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="❌ Ha, o'chirish", callback_data=f"confirm_delete_user_{user_id}"),
            types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"user_detail_{user_id}")
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ <b>Diqqat!</b>\n\n"
        f"User #{user_id} ni o'chirishga ishonchingiz komilmi?\n"
        f"Barcha e'lonlari ham o'chiriladi!",
        reply_markup=kb,
        parse_mode="HTML"
    )

async def confirm_delete_user(callback: types.CallbackQuery, lang: str):
    """Userni o'chirishni tasdiqlash"""
    user_id = int(callback.data.split("_")[3])
    
    if not is_super_admin(callback.from_user.id):
        return
    
    async with async_session() as session:
        # User e'lonlarini o'chirish
        await session.execute(delete(Ad).where(Ad.user_id == user_id))
        
        # Userni o'chirish
        await session.execute(delete(User).where(User.user_id == user_id))
        
        await session.commit()
        
        await callback.answer(f"✅ User #{user_id} va barcha e'lonlari o'chirildi")
        
        # Userlar ro'yxatiga qaytish
        await show_users_menu(callback, lang)
