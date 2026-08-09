# Post-Quantum Cryptography (PQC) Authentication Suite for GarudaAI

This document details the Post-Quantum Cryptography (PQC) upgrade integrated into the **GarudaAI Insider Threat Detection Platform**, protecting user authentication and credentials against quantum computing threats.

---

## 🛡️ Executive Summary & Objectives

Quantum computers leveraging Shor's algorithm threaten traditional public-key cryptography (RSA, ECC, Diffie-Hellman). To ensure future-proof quantum resilience, GarudaAI implements the **NIST FIPS 203 standardized Module-Lattice-Based Key Encapsulation Mechanism (ML-KEM-768)** combined with **HKDF-SHA256** and **AES-256-GCM** authenticated payload encryption.

---

## 🔬 Cryptographic Architecture & Flow

```
[Plain Password]
       │
       ▼
[ML-KEM-768 Key Encapsulation] ──(Generates Shared Secret & Encapsulated Secret)
       │
       ▼
[HKDF-SHA256 Derivation] ───────(Derives 256-bit Symmetric Key)
       │
       ▼
[AES-256-GCM Encryption] ────────(Encrypts Password Payload)
       │
       ▼
[MongoDB Storage] ──────────────(Stores ciphertext, nonce, tag, encapsulated secret, algorithm)
```

### 1. Key Encapsulation Mechanism (ML-KEM-768)
- **Standard**: NIST FIPS 203 (ML-KEM-768 / Kyber768).
- **Public Key Size**: 1,184 bytes.
- **Private Key Size**: 2,400 bytes.
- **Ciphertext Size**: 1,088 bytes.
- **Shared Secret Size**: 32 bytes (256 bits).
- **Library**: `liboqs-python` (Open Quantum Safe) with native FIPS 203 mathematical engine fallback.

### 2. Key Derivation Function (HKDF-SHA256)
- **Standard**: RFC 5869 HKDF-SHA256.
- **Input**: 32-byte ML-KEM shared secret.
- **Output**: 256-bit (32-byte) AES key.

### 3. Authenticated Symmetric Encryption (AES-256-GCM)
- **Algorithm**: AES-256-GCM (Galois/Counter Mode).
- **Key Length**: 256 bits (32 bytes).
- **Nonce Length**: 96 bits (12 bytes).
- **Authentication Tag**: 128 bits (16 bytes).

---

## 🗄️ MongoDB Document Schema (`users` Collection)

Each user document in MongoDB stores the following fields:

```json
{
    "_id": "ObjectId",
    "full_name": "Dr. Alan Turing",
    "email": "alan.turing@garuda.ai",
    "employee_id": "GAR-PQC-001",
    "department": "Quantum Cryptography",
    "role": "Chief Scientist",
    "password": "Base64(AES_Ciphertext)",
    "encrypted_password": "Base64(AES_Ciphertext)",
    "nonce": "Base64(AES_Nonce_96bit)",
    "authentication_tag": "Base64(AES_Tag_128bit)",
    "encapsulated_secret": "Base64(ML_KEM_Ciphertext)",
    "private_key": "Base64(ML_KEM_Private_Key)",
    "algorithm": "ML-KEM-768 + HKDF-SHA256 + AES-256-GCM",
    "created_at": "ISODate",
    "last_login": "ISODate or null",
    "is_active": true,
    "failed_login_attempts": 0,
    "account_locked": false
}
```

> [!IMPORTANT]
> Plain-text passwords are **NEVER** stored or logged.

---

## 📥 Installation & Setup

### 1. Requirements Installation
Ensure the following packages are present in your Python environment:

```bash
pip install liboqs-python cryptography hkdf Flask pymongo
```

### 2. Windows Installation Note for `liboqs` C Binaries
If `liboqs-python` requires C library compilation on Windows:
- Install `cmake` and MSVC Build Tools (`Visual Studio C++ Build Tools`), or
- The GarudaAI engine automatically detects missing C binaries and activates the standard FIPS 203 ML-KEM-768 mathematical encapsulation engine so all operations run cleanly without C compiler dependencies.

---

## 🚀 API Endpoints & Usage

### 1. User Registration (`POST /api/auth/register`)
**Request Body**:
```json
{
  "full_name": "Alice Smith",
  "email": "alice.smith@garuda.ai",
  "employee_id": "GAR-2001",
  "department": "SOC Operations",
  "role": "Analyst",
  "password": "MySuperSecretPassword123!"
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "message": "User created successfully.",
  "user": {
    "_id": "6a608a83be19976b31b33d31",
    "full_name": "Alice Smith",
    "email": "alice.smith@garuda.ai",
    "employee_id": "GAR-2001",
    "department": "SOC Operations",
    "role": "Analyst",
    "is_active": true,
    "failed_login_attempts": 0,
    "account_locked": false
  }
}
```

---

### 2. Quantum-Safe Login (`POST /api/auth/login`)
**Request Body**:
```json
{
  "email": "alice.smith@garuda.ai",
  "password": "MySuperSecretPassword123!"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Authentication successful.",
  "user": {
    "uid": "6a608a83be19976b31b33d31",
    "email": "alice.smith@garuda.ai",
    "displayName": "Alice Smith",
    "employee_id": "GAR-2001",
    "department": "SOC Operations",
    "role": "Analyst"
  },
  "token": "garuda-token-6a608a83be19976b31b33d31"
}
```

---

## 🔄 Legacy Password Migration Script

To convert legacy bcrypt/pbkdf2 user records into PQC format:

```bash
python backend/scripts/migrate_passwords.py
```

---

## 🧪 Testing Suite

Run the full Post-Quantum Cryptography test suite:

```bash
python -m unittest tests/test_pqc.py
```
