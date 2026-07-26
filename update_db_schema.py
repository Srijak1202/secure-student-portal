import sqlite3

db_path = 'instance/academic_monitoring.db'
print(f"Connecting to {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE student_profile ADD COLUMN section VARCHAR(10)")
    conn.commit()
    print("SUCCESS: Column 'section' added to 'student_profile' table.")
except Exception as e:
    print(f"INFO: {e}")
finally:
    if conn:
        conn.close()
