# 🤖 Dacha Telegram Bot

## 📋 Ushbu bot nima qiladi?
- ✅ E'lonlarni avtomatik kanalga joylaydi
- ✅ Belgilangan vaqtda avtomatik o'chiradi  
- ✅ User management (bloklash, o'chirish)
- ✅ Admin paneli bilan sozlash
- ✅ Auto-posting (daqiqalarda sozlash)

## 🚀 Qanday ishga tushirish?

### 1. Virtual environment yaratish:
```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Dependencies o'rnatish:
```bash
pip install -r requirements.txt
```

### 3. Konfiguratsiya:
- `.env` faylini yarating
- `BOT_TOKEN` va `SUPER_ADMIN_IDS` ni kiriting

### 4. Botni ishga tushirish:
```bash
python main.py
```

## ⚙️ Sozlamalar:
- `/settings` - Admin paneli
- Auto-posting chastotasi: 5 daqiqa (o'zgartirish mumkin)
- Auto-cleanup: belgilangan vaqtda

## 📁 Asosiy fayllar:
- `main.py` - Botni ishga tushirish
- `bot/handlers/admin.py` - Admin handlerlari
- `bot/utils/channel.py` - Kanal funksiyalari
- `database/models.py` - Database modellari
- `user_management.py` - User boshqaruvi

## 🔑 Kalit xususiyatlar:
- 🎯 Tezkor sozlash skriptlari (`quick_settings.py`)
- 📊 Statistika va monitoring
- 🛡️ Xavfsizlik (super adminlar)
- 📱 User management paneli

## 📞 Yordam:
Agar savollar bo'lsa, menga murojaat qiling!

---
🤖 Created with ❤️ by Cascade & AI
