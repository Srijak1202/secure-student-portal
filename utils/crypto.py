import os
import base64
import hashlib
import hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

# Global key storage
_CIPHER_KEY = None
_SIGNING_KEY = None

# ============================================================
# PEM Helpers (for signing key)
# ============================================================
def _read_pem(filepath, header):
    """Read a symmetric key from a custom PEM-formatted file."""
    with open(filepath, 'r') as f:
        content = f.read()
    lines = content.strip().split('\n')
    b64_data = ''.join(line for line in lines if not line.startswith('-----'))
    return base64.b64decode(b64_data)

def _write_pem(filepath, key_bytes, label):
    """Write a symmetric key to a custom PEM-formatted file."""
    b64_data = base64.b64encode(key_bytes).decode('utf-8')
    with open(filepath, 'w') as f:
        f.write(f"-----BEGIN {label}-----\n")
        f.write(f"{b64_data}\n")
        f.write(f"-----END {label}-----\n")

# ============================================================
# RSA Key Management (Hybrid Encryption)
# ============================================================
def _generate_rsa_keypair():
    """
    Generate a 2048-bit RSA key pair and save to PEM files.
    Satisfies Requirement: Key Generation (Asymmetric)
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Save private key
    with open('rsa_private.pem', 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Save public key
    public_key = private_key.public_key()
    with open('rsa_public.pem', 'wb') as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    print("[CRYPTO LOG] RSA 2048-bit key pair generated → rsa_private.pem, rsa_public.pem")
    return private_key, public_key

def _load_rsa_private_key():
    """Load RSA private key from PEM file."""
    with open('rsa_private.pem', 'rb') as f:
        return serialization.load_pem_private_key(f.read(), password=None)

def _load_rsa_public_key():
    """Load RSA public key from PEM file."""
    with open('rsa_public.pem', 'rb') as f:
        return serialization.load_pem_public_key(f.read())

def _rsa_encrypt(public_key, plaintext_bytes):
    """Encrypt data with RSA public key using OAEP padding."""
    return public_key.encrypt(
        plaintext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def _rsa_decrypt(private_key, ciphertext_bytes):
    """Decrypt data with RSA private key using OAEP padding."""
    return private_key.decrypt(
        ciphertext_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

# ============================================================
# Key Loading (Hybrid: RSA wraps AES key)
# ============================================================
def load_or_generate_keys():
    """
    Hybrid Encryption Key Management:
    1. Generate/load RSA 2048-bit key pair
    2. AES key is encrypted with RSA public key (key wrapping)
    3. On load, AES key is decrypted with RSA private key
    
    Satisfies Requirement: Key Generation, Key Exchange, Hybrid Approach
    """
    global _CIPHER_KEY, _SIGNING_KEY
    
    encrypted_aes_file = 'aes_key_encrypted.pem'
    sign_key_file = 'signing.pem'
    
    # --- Step 1: RSA Key Pair ---
    if os.path.exists('rsa_private.pem') and os.path.exists('rsa_public.pem'):
        private_key = _load_rsa_private_key()
        public_key = _load_rsa_public_key()
        print("[CRYPTO LOG] RSA key pair loaded from PEM files.")
    else:
        private_key, public_key = _generate_rsa_keypair()
    
    # --- Step 2: AES Key (wrapped by RSA) ---
    if os.path.exists(encrypted_aes_file):
        # Read RSA-encrypted AES key and decrypt it
        with open(encrypted_aes_file, 'rb') as f:
            encrypted_aes_key = f.read()
        _CIPHER_KEY = _rsa_decrypt(private_key, encrypted_aes_key)
        print("[CRYPTO LOG] AES key decrypted using RSA private key.")
    else:
        # Generate new AES key, then encrypt it with RSA public key
        _CIPHER_KEY = Fernet.generate_key()
        encrypted_aes_key = _rsa_encrypt(public_key, _CIPHER_KEY)
        with open(encrypted_aes_file, 'wb') as f:
            f.write(encrypted_aes_key)
        print("[CRYPTO LOG] New AES key generated and encrypted with RSA public key → aes_key_encrypted.pem")
    
    # --- Step 3: Signing Key (unchanged) ---
    if os.path.exists(sign_key_file):
        _SIGNING_KEY = _read_pem(sign_key_file, 'SIGNING KEY')
    else:
        _SIGNING_KEY = os.urandom(32)
        _write_pem(sign_key_file, _SIGNING_KEY, 'SIGNING KEY')

    print(f"\n[CRYPTO LOG] Hybrid key system ready:")
    print(f"  - RSA: 2048-bit (rsa_private.pem / rsa_public.pem)")
    print(f"  - AES: Fernet key (encrypted at rest in aes_key_encrypted.pem)")
    print(f"  - HMAC: signing.pem")

# ============================================================
# AES Encryption / Decryption (unchanged)
# ============================================================
def get_cipher_suite():
    if _CIPHER_KEY is None:
        load_or_generate_keys()
    return Fernet(_CIPHER_KEY)

def encrypt_data(data: str) -> str:
    """
    Encrypts a string using AES (Fernet).
    The AES key itself is protected by RSA encryption (hybrid approach).
    Satisfies Requirement: Encryption
    """
    if not data:
        return ""
    f = get_cipher_suite()
    encrypted_bytes = f.encrypt(data.encode('utf-8'))
    result = encrypted_bytes.decode('utf-8')
    print(f"\n[CRYPTO LOG] AES Encrypting: '{data}' -> '{result[:30]}...'")
    return result

def decrypt_data(encrypted_data: str) -> str:
    """
    Decrypts an encrypted string using AES (Fernet).
    Satisfies Requirement: Encryption
    """
    if not encrypted_data:
        return ""
    f = get_cipher_suite()
    try:
        decrypted_bytes = f.decrypt(encrypted_data.encode('utf-8'))
        result = decrypted_bytes.decode('utf-8')
        print(f"\n[CRYPTO LOG] AES Decrypting: '{encrypted_data[:20]}...' -> '{result}'")
        return result
    except Exception as e:
        print(f"[SECURITY ERROR] Decryption failed: {e}")
        return "[DECRYPTION FAILED]"

# ============================================================
# Digital Signature (HMAC-SHA256) — unchanged
# ============================================================
def sign_data(data: str) -> str:
    """
    Generates a HMAC-SHA256 signature for the data.
    Satisfies Requirement: Hashing & Digital Signature
    """
    if _SIGNING_KEY is None:
        load_or_generate_keys()
    
    h = hmac.new(_SIGNING_KEY, data.encode('utf-8'), hashlib.sha256)
    signature = h.hexdigest()
    print(f"\n[CRYPTO LOG] Signing Data: '{data}' -> Signature: '{signature}'")
    return signature

def verify_signature(data: str, signature: str) -> bool:
    """
    Verifies the HMAC-SHA256 signature.
    Satisfies Requirement: Hashing & Digital Signature
    """
    expected_signature = sign_data(data)
    return hmac.compare_digest(expected_signature, signature)

# ============================================================
# Base64 Encoding / Decoding — unchanged
# ============================================================
def encode_base64(data: str) -> str:
    """
    Encodes string to Base64.
    Satisfies Requirement: Encoding Techniques
    """
    encoded = base64.b64encode(data.encode('utf-8')).decode('utf-8')
    print(f"\n[CRYPTO LOG] Base64 Encoding: '{data}' -> '{encoded}'")
    return encoded

def decode_base64(encoded_data: str) -> str:
    """
    Decodes Base64 string.
    Satisfies Requirement: Encoding Techniques
    """
    try:
        decoded = base64.b64decode(encoded_data.encode('utf-8')).decode('utf-8')
        print(f"\n[CRYPTO LOG] Base64 Decoding: '{encoded_data}' -> '{decoded}'")
        return decoded
    except Exception as e:
        print(f"[DECODE ERROR: {e}]")
        return f"[DECODE ERROR: {e}]"
