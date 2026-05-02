import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS stores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        is_active INTEGER NOT NULL DEFAULT 1,
        report_chat_id INTEGER,
        daily_plan INTEGER NOT NULL DEFAULT 0,
        monthly_acquiring_plan INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        username TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        store_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        username TEXT,
        report_date TEXT NOT NULL,
        month_key TEXT NOT NULL,
        gross_total INTEGER NOT NULL,
        retail_total INTEGER NOT NULL,
        wholesale_total INTEGER NOT NULL,
        acquiring_total INTEGER NOT NULL,
        cash_total INTEGER NOT NULL,
        cashbox_total INTEGER NOT NULL,
        daily_plan INTEGER NOT NULL,
        daily_plan_percent INTEGER NOT NULL,
        monthly_acquiring_plan INTEGER NOT NULL,
        monthly_acquiring_accumulated INTEGER NOT NULL,
        sent_to_chat INTEGER NOT NULL DEFAULT 0,
        sent_message_id INTEGER,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (store_id) REFERENCES stores(id)
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_store_date ON reports(store_id, report_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reports_store_month ON reports(store_id, month_key)")

    conn.commit()
    conn.close()


def get_active_stores():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stores WHERE is_active = 1 ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows


def get_store_by_id(store_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stores WHERE id = ?", (store_id,))
    row = cur.fetchone()
    conn.close()
    return row


def add_store(name: str, report_chat_id=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO stores (name, report_chat_id) VALUES (?, ?)",
        (name, report_chat_id)
    )
    conn.commit()
    conn.close()


def update_store_plans(store_id: int, daily_plan: int, monthly_acquiring_plan: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE stores
        SET daily_plan = ?, monthly_acquiring_plan = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (daily_plan, monthly_acquiring_plan, store_id))
    conn.commit()
    conn.close()


def update_store_chat(store_id: int, report_chat_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE stores
        SET report_chat_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (report_chat_id, store_id))
    conn.commit()
    conn.close()


def is_admin(user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_admin(user_id: int, username: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()
    conn.close()


def get_monthly_acquiring_sum(store_id: int, month_key: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(SUM(acquiring_total), 0) AS total
        FROM reports
        WHERE store_id = ? AND month_key = ?
    """, (store_id, month_key))
    row = cur.fetchone()
    conn.close()
    return int(row["total"])


def save_report(
    store_id: int,
    user_id: int,
    username: str | None,
    report_date: str,
    month_key: str,
    gross_total: int,
    retail_total: int,
    wholesale_total: int,
    acquiring_total: int,
    im_orders: int,
    cash_total: int,
    cashbox_total: int,
    daily_plan: int,
    daily_plan_percent: int,
    monthly_acquiring_plan: int,
    monthly_acquiring_accumulated: int,
    sent_to_chat: int = 0,
    sent_message_id: int | None = None
):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reports (
            store_id, user_id, username, report_date, month_key,
            gross_total, retail_total, wholesale_total,
            acquiring_total, im_orders, cash_total, cashbox_total,
            daily_plan, daily_plan_percent,
            monthly_acquiring_plan, monthly_acquiring_accumulated,
            sent_to_chat, sent_message_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        store_id, user_id, username, report_date, month_key,
        gross_total, retail_total, wholesale_total,
        acquiring_total, im_orders, cash_total, cashbox_total,
        daily_plan, daily_plan_percent,
        monthly_acquiring_plan, monthly_acquiring_accumulated,
        sent_to_chat, sent_message_id
    ))
    conn.commit()
    conn.close()


def get_last_reports_by_user(user_id: int, limit: int = 5):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, s.name as store_name
        FROM reports r
        JOIN stores s ON s.id = r.store_id
        WHERE r.user_id = ?
        ORDER BY r.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def add_global_role(user_id: int, role: str, username: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR REPLACE INTO global_roles (user_id, role, username) VALUES (?, ?, ?)",
        (user_id, role, username)
    )
    conn.commit()
    conn.close()


def create_store_v21(
    name: str,
    owner_user_id: int,
    daily_plan: int,
    monthly_acquiring_plan: int,
    report_chat_id: int | None,
    report_send_time: str,
    boss_user_id: int | None,
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO stores (
            name,
            owner_user_id,
            daily_plan,
            monthly_acquiring_plan,
            report_chat_id,
            report_send_time,
            boss_user_id,
            is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    """, (
        name,
        owner_user_id,
        daily_plan,
        monthly_acquiring_plan,
        report_chat_id,
        report_send_time,
        boss_user_id,
    ))

    store_id = cur.lastrowid

    cur.execute("""
        INSERT OR IGNORE INTO user_store_roles (user_id, store_id, role, username)
        VALUES (?, ?, ?, ?)
    """, (owner_user_id, store_id, "store_admin", None))

    conn.commit()
    conn.close()
    return store_id


def add_user_to_store(user_id: int, store_id: int, role: str = "employee", username: str | None = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO user_store_roles (user_id, store_id, role, username)
        VALUES (?, ?, ?, ?)
    """, (user_id, store_id, role, username))
    conn.commit()
    conn.close()


def create_store_invite(code: str, store_id: int, created_by: int, role: str = "employee"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO store_invites (code, store_id, created_by, role, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (code, store_id, created_by, role))
    conn.commit()
    conn.close()


def get_invite_by_code(code: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT si.*, s.name as store_name
        FROM store_invites si
        JOIN stores s ON s.id = si.store_id
        WHERE si.code = ? AND si.is_active = 1
    """, (code,))
    row = cur.fetchone()
    conn.close()
    return row


def get_store_by_owner(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM stores WHERE owner_user_id = ? LIMIT 1", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def set_acquiring_base(store_id: int, month_key: str, base_amount: int, comment: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO acquiring_adjustments (store_id, month_key, base_amount, comment)
        VALUES (?, ?, ?, ?)
    """, (store_id, month_key, base_amount, comment))
    conn.commit()
    conn.close()


def get_acquiring_base(store_id: int, month_key: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT base_amount FROM acquiring_adjustments
        WHERE store_id = ? AND month_key = ?
    """, (store_id, month_key))
    row = cur.fetchone()
    conn.close()
    return int(row["base_amount"]) if row else 0
