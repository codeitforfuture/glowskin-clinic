import os
import sqlite3

DATABASE_URL = os.environ.get('DATABASE_URL')
IS_POSTGRES = DATABASE_URL is not None


class DBWrapper:
    """Wraps SQLite or PostgreSQL so app.py uses the same code for both."""
    def __init__(self, conn, is_postgres):
        self.conn = conn
        self.is_postgres = is_postgres

    def execute(self, sql, params=None):
        if self.is_postgres:
            sql = sql.replace('?', '%s')
        cur = self.conn.cursor()
        if params is not None:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


def get_db_connection():
    if IS_POSTGRES:
        import psycopg2
        import psycopg2.extras
        url = DATABASE_URL
        if url.startswith('postgres://'):
            url = url.replace('postgres://', 'postgresql://', 1)
        conn = psycopg2.connect(url, cursor_factory=psycopg2.extras.DictCursor)
        return DBWrapper(conn, True)
    else:
        db_path = os.path.join(os.path.dirname(__file__), 'data', 'clinic.db')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return DBWrapper(conn, False)


def init_db():
    conn = get_db_connection()

    users_id = 'SERIAL PRIMARY KEY' if IS_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'
    appt_id = 'SERIAL PRIMARY KEY' if IS_POSTGRES else 'INTEGER PRIMARY KEY AUTOINCREMENT'

    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {users_id},
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute(f'''
        CREATE TABLE IF NOT EXISTS appointments (
            id {appt_id},
            reference_code TEXT UNIQUE,
            user_id INTEGER,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            service TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Auto-migrate: add missing columns for older SQLite databases
    if not IS_POSTGRES:
        try:
            cols = [r['name'] for r in conn.execute("PRAGMA table_info(appointments)").fetchall()]
            if 'reference_code' not in cols:
                conn.execute('ALTER TABLE appointments ADD COLUMN reference_code TEXT')
            if 'user_id' not in cols:
                conn.execute('ALTER TABLE appointments ADD COLUMN user_id INTEGER')
            if 'email' not in cols:
                conn.execute('ALTER TABLE appointments ADD COLUMN email TEXT')
            if 'notes' not in cols:
                conn.execute('ALTER TABLE appointments ADD COLUMN notes TEXT')
        except Exception as e:
            print(f"Migration note: {e}")

    conn.commit()
    conn.close()
    print("✅ Database ready.")
