from config import SUPER_ADMIN_IDS

def is_super_admin(user_id: int) -> bool:
    return int(user_id) in set(SUPER_ADMIN_IDS or [])
