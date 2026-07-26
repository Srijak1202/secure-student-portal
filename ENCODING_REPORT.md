# Security Techniques Report — AcadPortal

## Overview
This report documents all cryptographic and security mechanisms implemented in the Academic Student Portal.

---

## 1. Authentication & Multi-Factor Authentication (MFA)
- **Factor 1**: Username + Email + Password (verified via PBKDF2 salted hash)
- **Factor 2**: 6-digit OTP sent to registered email (expires in 5 min, single-use)
- **Account Lockout**: 5 failed attempts → locked for 15 minutes
- **Session Timeout**: 20 min inactivity → auto logout
- **Back-Button Prevention**: `history.pushState` + `Cache-Control: no-store` headers
- **RBAC**: Route-level access control via `@role_required()` decorator

## 2. Hashing & Salted Hashing (Password Storage)
- **Algorithm**: PBKDF2-SHA256 (260,000 iterations)
- **Salt**: Unique random salt per password (stored alongside hash)
- **Reversible**: ❌ No — one-way by design
- **Purpose**: Passwords are never stored in plaintext; only hashes are compared during login
- **Defense against**: Rainbow table attacks (salt), brute-force (key stretching)

## 3. Encryption (Academic Data Protection)
- **Algorithm**: AES-128-CBC via Fernet (Python `cryptography` library)
- **Key Storage**: PEM format (`secret.pem`) with `-----BEGIN ENCRYPTION KEY-----` headers
- **Key Type**: Symmetric — same key for encrypt/decrypt
- **Reversible**: ✅ Yes, with the correct key
- **Used for**: `marks_encrypted` and `risk_score_encrypted` fields in `academic_record` table
- **Process**: `plaintext → AES encrypt → Base64-encoded ciphertext → stored in DB`

## 4. Digital Signature (Data Integrity)
- **Algorithm**: HMAC-SHA256
- **Key Storage**: PEM format (`signing.pem`) — separate from encryption key
- **Timing-Safe**: Uses `hmac.compare_digest()` to prevent side-channel attacks
- **Reversible**: N/A — verification only
- **Used for**: Each academic record has a signature; dashboard shows ✅ Verified or ❌ TAMPERED
- **Process**: `student_id + subject + marks + risk → HMAC-SHA256 → signature stored alongside record`

## 5. Encoding Techniques (Base64)
- **Algorithm**: Base64 (RFC 4648)
- **Reversible**: ✅ Yes — **without any key** (zero security)
- **Purpose**: Data format conversion for safe transport, NOT confidentiality
- **Used for**:
  1. "Export Encoded Profile" feature (student JSON → Base64 download)
  2. PEM key files (keys are Base64-wrapped with BEGIN/END headers)

### Risks
1. **False Sense of Security**: Encoding ≠ Encryption. Decoded trivially.
2. **Data Bloat**: Base64 increases size by ~33%.
3. **WAF Evasion**: Attackers encode XSS payloads to bypass filters.
4. **IDOR**: Encoded IDs in URLs can be enumerated.

## Comparison Table

| Concept | Reversible? | Needs Key? | Purpose | Algorithm |
|---|---|---|---|---|
| Hashing | ❌ No | Salt (auto) | Password storage | PBKDF2-SHA256 |
| Encryption | ✅ Yes | secret.pem | Protect marks at rest | AES-128 (Fernet) |
| Digital Signature | Verify only | signing.pem | Detect tampering | HMAC-SHA256 |
| Encoding | ✅ Yes | No key | Data format/transport | Base64 |

## Mitigation Strategy
- Sensitive data (marks, risk) is **encrypted** with AES before storage
- Passwords are **hashed** with PBKDF2 + salt — never stored in plaintext
- Data integrity is verified via **HMAC signatures** on every academic record
- Encoding is used **only** for data formatting (profile export, PEM files), never for security
- Keys are stored in **PEM format** files, not hardcoded in source code
