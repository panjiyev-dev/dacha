# 📋 Sherigiga yuborish uchun muhim fayllar ro'yxati

## 🎯 Asosiy fayllar (kerakli):
```
📁 bot/
  ├── handlers/
  │   └── admin.py          # Admin paneli
  ├── logic/
  │   └── automation.py     # Auto-posting/cleanup
  └── utils/
      ├── channel.py        # Kanal funksiyalari
      └── auth.py          # Auth funksiyalari

📁 database/
  ├── models.py            # Database modellari
  └── setup.py             # DB sozlamalari

📄 main.py                 # Botni ishga tushirish
📄 config.py              # Konfiguratsiya
📄 requirements.txt       # Dependencies
📄 user_management.py     # User boshqaruvi
📄 quick_settings.py      # Tezkor sozlash
```

## 📱 Telegram orqali yuborish tartibi:

### 1️⃣ **Eng oson usul - Zip arxiv:**
- 📦 `dacha_tg_bot_20260218_104253.zip` (11 MB)
- 📄 `README_FOR_FRIEND.md`

### 2️⃣ **Papka bo'yicha yuborish:**
- 📁 `bot/` papkasini yuboring
- 📁 `database/` papkasini yuboring  
- 📄 Asosiy fayllarni yuboring

### 3️⃣ **GitHub orqali:**
- Repositoryga yuklang
- Link yuboring

## 📝 Xabar matni (sherigiga yuborish uchun):

```
🤖 Salom! Dacha Telegram Bot manba kodlari

📦 Zip arxiv:
dacha_tg_bot_20260218_104253.zip

📋 Qanday ishga tushirish:
1. Virtual environment: python -m venv venv
2. Activate: venv\Scripts\activate  
3. Install: pip install -r requirements.txt
4. .env faylini yarating (BOT_TOKEN, SUPER_ADMIN_IDS)
5. Run: python main.py

⚙️ Asosiy xususiyatlar:
✅ Auto-posting (daqiqalarda sozlash)
✅ Auto-cleanup (belgilangan vaqtda)
✅ User management paneli
✅ Admin paneli
✅ Tezkor sozlash skriptlari

📞 Savollar bo'lsa, yozing! 👍
```

## 🔐 Maxfiylik eslatma:
- `.env` faylini yubormang
- `db.sqlite3` ni yubormang
- `BOT_TOKEN` ni alohida yuboring
