# Tezkor komandalar uchun qo'shimchilar

# Bot handlers/admin.py ga qo'shing:

@router.message(Command("ultra_fast"))
async def cmd_ultra_fast(message: types.Message, lang: str):
    """Ultra tezkor rejim - 1 daqiqa"""
    if not is_super_admin_id(message.from_user.id):
        return
        
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        settings.post_frequency_hours = 1/60  # 1 daqiqa
        settings.post_duration_hours = 0.5  # 30 daqiqa
        await session.commit()
        
        await message.answer("⚡ <b>Ultra tezkor rejim yoqildi!</b>\n"
                          "📊 Har 1 daqiqada post\n"
                          "⏰ 30 daqiqa davomida", parse_mode="HTML")

@router.message(Command("fast"))
async def cmd_fast(message: types.Message, lang: str):
    """Tezkor rejim - 5 daqiqa"""
    if not is_super_admin_id(message.from_user.id):
        return
        
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        settings.post_frequency_hours = 5/60  # 5 daqiqa
        settings.post_duration_hours = 1  # 1 soat
        await session.commit()
        
        await message.answer("🚀 <b>Tezkor rejim yoqildi!</b>\n"
                          "📊 Har 5 daqiqada post\n"
                          "⏰ 1 soat davomida", parse_mode="HTML")

@router.message(Command("normal"))
async def cmd_normal(message: types.Message, lang: str):
    """Normal rejim - 30 daqiqa"""
    if not is_super_admin_id(message.from_user.id):
        return
        
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        settings.post_frequency_hours = 0.5  # 30 daqiqa
        settings.post_duration_hours = 4  # 4 soat
        await session.commit()
        
        await message.answer("🐌 <b>Normal rejim yoqildi!</b>\n"
                          "📊 Har 30 daqiqada post\n"
                          "⏰ 4 soat davomida", parse_mode="HTML")

@router.message(Command("cleanup_now"))
async def cmd_cleanup_now(message: types.Message, lang: str):
    """Darhol cleanup qilish"""
    if not is_super_admin_id(message.from_user.id):
        return
        
    from bot.utils.channel import cleanup_expired_posts
    success, count = await cleanup_expired_posts(message.bot, force_cleanup=True)
    
    await message.answer(f"🗑️ <b>Cleanup bajarildi!</b>\n"
                      f"✅ {count} ta post o'chirildi", parse_mode="HTML")

@router.message(Command("status"))
async def cmd_status(message: types.Message, lang: str):
    """Joriy statusni ko'rsatish"""
    if not is_super_admin_id(message.from_user.id):
        return
        
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if settings:
            freq_minutes = settings.post_frequency_hours * 60
            if freq_minutes < 1:
                freq_text = f"{freq_minutes*60:.0f} soniya"
            else:
                freq_text = f"{freq_minutes:.1f} daqiqa"
            
            text = (
                f"📊 <b>Bot Statusi:</b>\n\n"
                f"🔄 Post chastotasi: <code>{freq_text}</code>\n"
                f"⏰ Post davomiyligi: <code>{settings.post_duration_hours} soat</code>\n"
                f"🎯 Kanallar: <code>{', '.join(settings.target_channels or [])}</code>\n"
                f"🗑️ Cleanup vaqti: <code>{settings.cleanup_hour:02d}:{settings.cleanup_minute:02d} UTC</code>"
            )
            
            await message.answer(text, parse_mode="HTML")
