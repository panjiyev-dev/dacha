import asyncio
from database.setup import async_session
from database.models import User, Ad
from sqlalchemy import select, func

async def debug_user_menu():
    """User menu debug qilish"""
    print("🔍 User menu debug boshlandi...")
    
    try:
        async with async_session() as session:
            # 1. Userlar soni
            users_count = await session.execute(
                select(func.count(User.user_id))
            )
            total_users = users_count.scalar()
            print(f"📊 Jami userlar: {total_users}")
            
            # 2. Userlar ma'lumotlari
            users_data = await session.execute(
                select(User.user_id, User.is_blocked, User.created_at)
                .order_by(User.created_at.desc())
                .limit(20)
            )
            users = users_data.all()
            
            print(f"📋 Userlar ro'yxati ({len(users)} ta):")
            for user_id, is_blocked, created_at in users:
                # Active e'lonlar soni
                ads_res = await session.execute(
                    select(Ad.id).where(Ad.user_id == user_id, Ad.status == 'active')
                )
                active_ads = len(ads_res.scalars().all())
                
                status_emoji = "🟢" if not is_blocked else "🔴"
                print(f"  {status_emoji} User {user_id} ({active_ads} ta active e'lon)")
            
            # 3. Callback data formatini tekshirish
            print("\n🎯 Callback data formatlari:")
            for user_id, is_blocked, created_at in users:
                ads_res = await session.execute(
                    select(Ad.id).where(Ad.user_id == user_id, Ad.status == 'active')
                )
                active_ads = len(ads_res.scalars().all())
                
                callback_data = f"user_detail_{user_id}"
                button_text = f"{'🟢' if not is_blocked else '🔴'} {user_id} ({active_ads} ads)"
                print(f"  {button_text} -> {callback_data}")
            
            print("\n✅ Debug tugadi!")
            
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_user_menu())
