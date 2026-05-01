from db import get_connection


def get_global_role(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM global_roles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["role"] if row else None


def get_user_store_role(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT usr.role, s.*
        FROM user_store_roles usr
        JOIN stores s ON s.id = usr.store_id
        WHERE usr.user_id = ?
        LIMIT 1
    """, (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def is_super_admin(user_id: int) -> bool:
    return get_global_role(user_id) == "super_admin"


def is_boss(user_id: int) -> bool:
    return get_global_role(user_id) == "boss"


def get_user_store(user_id: int):
    row = get_user_store_role(user_id)
    return row if row else None


def user_has_any_access(user_id: int) -> bool:
    return get_global_role(user_id) is not None or get_user_store_role(user_id) is not None
