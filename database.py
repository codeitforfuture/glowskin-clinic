import sqlite3
import os

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'clinic.db')


def get_db_connection():
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _table_columns(conn, table):
    """Get list of column names for a table."""
    try:
        rows = conn.execute(f'PRAGMA table_info({table})').fetchall()
        return [r['name'] for r in rows]
    except Exception:
        return []


def _table_exists(conn, table):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return row is not None


def init_db():
    conn = get_db_connection()

    # ---- USERS TABLE ----
    if not _table_exists(conn, 'users'):
        conn.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    conn.commit()

    # ---- APPOINTMENTS TABLE ----
    if not _table_exists(conn, 'appointments'):
        conn.execute('''
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
    else:
        # Auto-migrate: add missing columns if they don't exist
        existing_cols = _table_columns(conn, 'appointments')
        migrations = [
            ('reference_code', 'ALTER TABLE appointments ADD COLUMN reference_code TEXT'),
            ('user_id',        'ALTER TABLE appointments ADD COLUMN user_id INTEGER'),
            ('email',          'ALTER TABLE appointments ADD COLUMN email TEXT'),
            ('notes',          'ALTER TABLE appointments ADD COLUMN notes TEXT'),
        ]
        for col_name, sql in migrations:
            if col_name not in existing_cols:
                try:
                    conn.execute(sql)
                    print(f"✅ Migrated: added column '{col_name}' to appointments table")
                except Exception as e:
                    print(f"⚠️ Migration skipped ({col_name}): {e}")

        # Backfill reference codes for old rows that don't have one
        try:
            rows = conn.execute(
                "SELECT id FROM appointments WHERE reference_code IS NULL"
            ).fetchall()
            import random, string
            for r in rows:
                ref = 'GS-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                conn.execute(
                    "UPDATE appointments SET reference_code = ? WHERE id = ?",
                    (ref, r['id'])
                )
            if rows:
                print(f"✅ Backfilled {len(rows)} reference codes")
        except Exception as e:
            print(f"⚠️ Backfill skipped: {e}")

        conn.commit()

    conn.close()
    print("✅ Database ready.")


if __name__ == '__main__':
    init_db()