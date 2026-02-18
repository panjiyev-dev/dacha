import asyncio
from database.setup import async_session
from database.models import User, Ad
from sqlalchemy import select, func

async def test_user_management():
    """User management funksiyalarini test qilish"""
    print("🔍 User management test boshlandi...")
    
    try:
        async with async_session() as session:
            # 1. Userlar sonini tekshirish
            users_count = await session.execute(
                select(func.count(User.user_id))
            )
            total_users = users_count.scalar()
            print(f"📊 Jami userlar: {total_users}")
            
            # 2. Active userlar soni
            active_users = await session.execute(
                select(func.count(User.user_id)).where(User.is_blocked == False)
            )
            active_count = active_users.scalar()
            print(f"🟢 Faol userlar: {active_count}")
            
            # 3. Bloklangan userlar soni
            blocked_users = await session.execute(
                select(func.count(User.user_id)).where(User.is_blocked == True)
            )
            blocked_count = blocked_users.scalar()
            print(f"🔴 Bloklangan userlar: {blocked_count}")
            
            # 4. E'lonlar statistikasi
            ads_count = await session.execute(
                select(func.count(Ad.id))
            )
            total_ads = ads_count.scalar()
            print(f"📝 Jami e'lonlar: {total_ads}")
            
            # 5. Active e'lonlar
            active_ads = await session.execute(
                select(func.count(Ad.id)).where(Ad.status == 'active')
            )
            active_ads_count = active_ads.scalar()
            print(f"✅ Active e'lonlar: {active_ads_count}")
            
            # 6. Birinchi 5 ta user ma'lumoti
            users_sample = await session.execute(
                select(User.user_id, User.is_blocked, User.created_at)
                .order_by(User.created_at.desc())
                .limit(5)
            )
            sample_users = users_sample.all()
            
            print("\n👥 Userlar namunasi:")
            for user_id, is_blocked, created_at in sample_users:
                status = "🟢" if not is_blocked else "🔴"
                print(f"  {status} User {user_id} - {created_at.strftime('%Y-%m-%d')}")
            
            print("\n✅ Test muvaffaqiyatli tugadi!")
            
    except Exception as e:
        print(f"❌ Xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(test_user_management())
