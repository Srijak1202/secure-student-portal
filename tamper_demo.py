"""
tamper_demo.py — Digital Signature Integrity Demo
===================================================
This script demonstrates how tampering with data in the database
is DETECTED by the HMAC-SHA256 signature verification system.

Usage:
  python tamper_demo.py tamper    → Change marks but keep old signature (triggers TAMPERED)
  python tamper_demo.py restore   → Restore original data and fix the signature
  python tamper_demo.py status    → Show current state of the record
"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.crypto import encrypt_data, decrypt_data, sign_data, load_or_generate_keys

DB_PATH  = os.path.join('instance', 'academic_monitoring.db')
RECORD_ID = 1   # Change this if your target record has a different ID

# ─────────────────────────────────────────────
def get_record():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, student_id, subject, marks_encrypted, risk_score_encrypted, signature FROM academic_record WHERE id=?", (RECORD_ID,))
    row = c.fetchone()
    conn.close()
    return row

def show_status():
    load_or_generate_keys()
    row = get_record()
    if not row:
        print(f"[ERROR] No record found with id={RECORD_ID}")
        return

    rec_id, student_id, subject, marks_enc, risk_enc, stored_sig = row
    marks     = decrypt_data(marks_enc)
    risk      = decrypt_data(risk_enc)
    raw_data  = f"{student_id}{subject}{marks}{risk}"
    expected  = sign_data(raw_data)

    print(f"\n{'='*50}")
    print(f"  Record ID  : {rec_id}")
    print(f"  Subject    : {subject}")
    print(f"  Marks      : {marks}")
    print(f"  Stored Sig : {stored_sig[:30]}...")
    print(f"  Expected   : {expected[:30]}...")
    match = stored_sig == expected
    print(f"\n  Status     : {'✅ VERIFIED' if match else '❌ TAMPERED — signatures do NOT match!'}")
    print(f"{'='*50}\n")

# ─────────────────────────────────────────────
def tamper():
    """
    TAMPER: Change the marks to 100 in the DB but keep the old signature.
    The dashboard will show TAMPERED because the signature no longer matches.
    """
    load_or_generate_keys()
    row = get_record()
    if not row:
        print(f"[ERROR] No record found with id={RECORD_ID}")
        return

    rec_id, student_id, subject, marks_enc, risk_enc, old_sig = row
    original_marks = decrypt_data(marks_enc)

    FAKE_MARKS = "100.0"
    new_marks_enc = encrypt_data(FAKE_MARKS)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE academic_record SET marks_encrypted=? WHERE id=?",
        (new_marks_enc, rec_id)
    )
    conn.commit()
    conn.close()

    print(f"\n[TAMPER] Subject       : {subject}")
    print(f"[TAMPER] Original Marks: {original_marks}  →  FAKE Marks: {FAKE_MARKS}")
    print(f"[TAMPER] Old Signature : {old_sig[:30]}... (LEFT UNCHANGED)")
    print("\n⚠️  Database tampered! Open the student dashboard to see the TAMPERED warning.")
    print("   Run  python tamper_demo.py restore  to fix it after the demo.\n")

# ─────────────────────────────────────────────
def restore():
    """
    RESTORE: Put the correct original marks back and regenerate the signature.
    The dashboard will show VERIFIED again.
    """
    load_or_generate_keys()
    row = get_record()
    if not row:
        print(f"[ERROR] No record found with id={RECORD_ID}")
        return

    rec_id, student_id, subject, marks_enc, risk_enc, _ = row
    # Whatever value is currently in the DB, ask the user what the real marks should be
    current_marks = decrypt_data(marks_enc)
    print(f"\nCurrent marks in DB: {current_marks}")
    real_marks = input("Enter the REAL marks to restore (press Enter to keep current): ").strip()
    if not real_marks:
        real_marks = current_marks

    risk = decrypt_data(risk_enc)
    raw_data = f"{student_id}{subject}{real_marks}{risk}"
    new_sig      = sign_data(raw_data)
    new_marks_enc = encrypt_data(real_marks)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE academic_record SET marks_encrypted=?, signature=? WHERE id=?",
        (new_marks_enc, new_sig, rec_id)
    )
    conn.commit()
    conn.close()

    print(f"\n✅ Restored! Subject: {subject}  Marks: {real_marks}")
    print(f"   New Signature: {new_sig[:30]}...")
    print("   Dashboard will show VERIFIED again.\n")

# ─────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == 'tamper':
        tamper()
    elif cmd == 'restore':
        restore()
    elif cmd == 'status':
        show_status()
    else:
        print(f"Unknown command: {cmd}")
        print("Use: tamper | restore | status")
