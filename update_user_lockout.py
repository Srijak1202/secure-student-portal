import sqlite3
import os

DB_PATH = 'instance/academic_monitoring.db'

def update_schema():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if columns exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [info[1] for info in cursor.fetchall()]

        if 'failed_login_attempts' not in columns:
            print("Adding failed_login_attempts column...")
            cursor.execute("ALTER TABLE user ADD COLUMN failed_login_attempts INTEGER DEFAULT 0")
        else:
            print("failed_login_attempts column already exists.")

        if 'lockout_until' not in columns:
            print("Adding lockout_until column...")
            cursor.execute("ALTER TABLE user ADD COLUMN lockout_until TIMESTAMP")
        else:
            print("lockout_until column already exists.")

        conn.commit()
        print("Schema update successful.")

    except Exception as e:
        print(f"Error updating schema: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_schema()
