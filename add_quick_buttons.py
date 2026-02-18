# Bot handlers/admin.py ga qo'shish uchun kod

# cmd_settings funksiyasiga quyidagilarni qo'shing:

# Settings textiga qo'shimcha:
text += (
    f"\n⚡ <b>TEZKOR SOZLAMALAR:</b>\n"
    f"🔥 1 daqiqa: <code>/set_freq 0.0167</code>\n"
    f"🚀 5 daqiqa: <code>/set_freq 0.0833</code>\n"
    f"⚡ 10 daqiqa: <code>/set_freq 0.1667</code>\n"
    f"🐢 15 daqiqa: <code>/set_freq 0.25</code>\n"
    f"🐌 30 daqiqa: <code>/set_freq 0.5</code>\n"
    f"🦥 1 soat: <code>/set_freq 1</code>\n\n"
)

# Inline tugmalar qo'shish:
kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text="⚡ 1 daqiqa", callback_data="set_freq_0.0167")],
    [types.InlineKeyboardButton(text="🚀 5 daqiqa", callback_data="set_freq_0.0833")],
    [types.InlineKeyboardButton(text="⚡ 10 daqiqa", callback_data="set_freq_0.1667")],
    [types.InlineKeyboardButton(text="🐢 15 daqiqa", callback_data="set_freq_0.25")],
    [types.InlineKeyboardButton(text="🐌 30 daqiqa", callback_data="set_freq_0.5")],
    [types.InlineKeyboardButton(text="🦥 1 soat", callback_data="set_freq_1")],
    [types.InlineKeyboardButton(text="⚙️ O'zim kiritaman", callback_data="set_freq_custom")],
    [types.InlineKeyboardButton(text=i18n.get("main_menu", lang), callback_data="refresh_settings")]
])

# Callback handler qo'shish:
@router.callback_query(F.data.startswith("set_freq_"))
async def handle_quick_freq(callback: types.CallbackQuery, lang: str):
    freq_str = callback.data.split("_")[2]
    freq = float(freq_str)
    
    async with async_session() as session:
        res = await session.execute(select(GlobalSettings).where(GlobalSettings.id == 1))
        settings = res.scalar_one_or_none()
        
        if not settings:
            settings = GlobalSettings(id=1)
            session.add(settings)
        
        settings.post_frequency_hours = freq
        await session.commit()
        
        minutes = freq * 60
        if minutes < 1:
            time_text = f"{minutes*60:.0f} soniya"
        else:
            time_text = f"{minutes:.1f} daqiqa"
        
        await callback.message.edit_text(
            f"✅ Post chastotasi {time_text} ga o'rnatildi!\n\n"
            f"Endi har {time_text} da yangi post yuboriladi.",
            parse_mode="HTML"
        )
