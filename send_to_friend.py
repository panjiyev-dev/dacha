# Sherigiga yuborish uchun tayyorlov skripti
import os
import zipfile
from datetime import datetime

def create_project_zip():
    """Butun loyiha zip arxivini yaratish"""
    
    # Zip fayl nomi
    zip_name = f"dacha_tg_bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    
    # Zip qilinmaydigan fayllar va papkalar
    exclude_files = {
        '.git', '__pycache__', '.vscode', 'venv', 
        '*.pyc', '*.log', '.env', 'db.sqlite3'
    }
    
    exclude_dirs = {'__pycache__', '.git', 'venv', '.vscode'}
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Papkalarni yurib chiqish
        for root, dirs, files in os.walk('.'):
            # Exclude papkalarni olib tashlash
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Exclude fayllarni tekshirish
                if any(file.endswith(ext) for ext in ['.pyc', '.log']):
                    continue
                if file in ['.env', 'db.sqlite3']:
                    continue
                
                # Zip ga qo'shish
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
    
    print(f"✅ Zip arxiv yaratildi: {zip_name}")
    print(f"📊 Hajmi: {os.path.getsize(zip_name) / 1024 / 1024:.2f} MB")
    return zip_name

def create_readme_for_friend():
    """Sherigi uchun README yaratish"""
    readme_content = """# 🤖 Dacha Telegram Bot

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
venv\\Scripts\\activate
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
"""
    
    with open("README_FOR_FRIEND.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ README_FOR_FRIEND.md yaratildi")

if __name__ == "__main__":
    print("📦 Sherigiga yuborish uchun arxiv tayyorlanmoqda...")
    
    # README yaratish
    create_readme_for_friend()
    
    # Zip arxiv yaratish
    zip_file = create_project_zip()
    
    print(f"\n🎉 Tayyor!")
    print(f"📤 Telegramga yuboring: {zip_file}")
    print(f"📄 Qo'shimcha: README_FOR_FRIEND.md")
