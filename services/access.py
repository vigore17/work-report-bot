from db import get_connection


def get_global_role(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM global_roles WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row["role"] if row else None


def is_super_admin(user_id: int) -> bool:
    return get_global_role(user_id) == "super_admin"


def is_boss(user_id: int) -> bool:
    return get_global_role(user_id) == "boss"


def get_user_stores(user_id: int):
    conn = get_connection()
    cur = conn.cursor()

    if is_super_admin(user_id):
        cur.execute("SELECT * FROM stores WHERE is_active = 1 ORDER BY name")
    else:
        cur.execute("""
            SELECT s.*, usr.role
            FROM user_store_roles usr
            JOIN stores s ON s.id = usr.store_id
            WHERE usr.user_id = ?
              AND s.is_active = 1
            ORDER BY s.name
        """, (user_id,))

    rows = cur.fetchall()
    conn.close()
    return rows


def get_user_store(user_id: int):
    stores = get_user_stores(user_id)
    return stores[0] if len(stores) == 1 else None


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


def user_has_any_access(user_id: int) -> bool:
    return get_global_role(user_id) is not None or len(get_user_stores(user_id)) > 0
