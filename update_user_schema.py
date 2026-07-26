import sqlite3

db_path = 'instance/academic_monitoring.db'
print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE user ADD COLUMN email VARCHAR(150)")
    conn.commit()
    print("SUCCESS: Column 'email' added to 'user' table.")
except Exception as e:
    print(f"INFO: {e}")
finally:
    if conn:
        conn.close()
