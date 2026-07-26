import sys
import os

# Ensure we can import from the application
sys.path.append(os.getcwd())

from utils.auth import hash_password, verify_password
from utils.crypto import encrypt_data, decrypt_data, sign_data, verify_signature, encode_base64, decode_base64

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def main():
    print("=== SECURE ACADEMIC PORTAL - CRYPTO DEMO ===")

    # --- 1. Password Hashing (Salt + Hash) ---
    print_header("1. HASHING (Password Storage)")
    password = "my_secure_password_123"
    print(f"Raw Password:  '{password}'")
    
    hashed = hash_password(password)
    print(f"\n[Action] Hashing using PBKDF2-SHA256 with Salt...")
    print(f"Stored Hash:   {hashed}")
    print(f"(Notice the format: method$salt$hash)")

    # --- 2. Encryption (AES) ---
    print_header("2. ENCRYPTION (Confidentiality)")
    secret_data = "Midterm Marks: 98/100"
    print(f"Original Data: '{secret_data}'")
    
    encrypted = encrypt_data(secret_data)
    print(f"\n[Action] Encrypting using AES (Fernet)...")
    print(f"Encrypted:     {encrypted}")
    
    decrypted = decrypt_data(encrypted)
    print(f"\n[Action] Decrypting...")
    print(f"Decrypted:     '{decrypted}'")

    # --- 3. Digital Signature (Integrity) ---
    print_header("3. DIGITAL SIGNATURE (Integrity)")
    data_to_sign = "Grade: A+"
    print(f"Data:          '{data_to_sign}'")
    
    signature = sign_data(data_to_sign)
    print(f"\n[Action] Signing using HMAC-SHA256...")
    print(f"Signature:     {signature}")
    
    is_valid = verify_signature(data_to_sign, signature)
    print(f"\n[Action] Verifying signature...")
    print(f"Verification:  {'[VALID]' if is_valid else '[INVALID]'}")

    # --- 4. Encoding (Base64) ---
    print_header("4. ENCODING (Base64 Representation)")
    raw_text = "Hello World"
    print(f"Raw Text:      '{raw_text}'")
    
    encoded = encode_base64(raw_text)
    print(f"\n[Action] Encoding to Base64...")
    print(f"Encoded:       {encoded}")
    
    decoded = decode_base64(encoded)
    print(f"\n[Action] Decoding back...")
    print(f"Decoded:       '{decoded}'")

if __name__ == "__main__":
    main()
