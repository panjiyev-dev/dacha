# Callback handler import test
try:
    from bot.handlers.admin import handle_show_users
    print("✅ handle_show_users import muvaffaqiyatli")
except Exception as e:
    print(f"❌ handle_show_users import xatosi: {e}")

try:
    from user_management import show_users_menu
    print("✅ show_users_menu import muvaffaqiyatli")
except Exception as e:
    print(f"❌ show_users_menu import xatosi: {e}")

# Handler ro'yxatini tekshirish
try:
    from bot.handlers.admin import router
    handlers = [handler for handler in router.handlers.handlers]
    print(f"📋 Jami handlerlar: {len(handlers)}")
    
    # User management handlerlari
    user_handlers = [h for h in handlers if 'user' in str(h.callback).lower()]
    print(f"👥 User management handlerlari: {len(user_handlers)}")
    
except Exception as e:
    print(f"❌ Handler tekshirish xatosi: {e}")
