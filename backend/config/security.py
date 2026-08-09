"""
GarudaAI Post-Quantum Security Configuration
============================================

Centralized configuration for Post-Quantum Cryptography (PQC),
HKDF key derivation, AES-256-GCM authenticated encryption,
and security logging paths.
"""

import os

# PQC Algorithm Settings (NIST FIPS 203 ML-KEM-768)
PQC_ALGORITHM: str = "ML-KEM-768"

# Symmetric Encryption Settings (AES-256-GCM)
AES_KEY_LENGTH: int = 32  # 256 bits
NONCE_LENGTH: int = 12    # 96 bits (NIST standard for GCM)
TAG_LENGTH: int = 16      # 128 bits (GCM auth tag size)

# HKDF Key Derivation Function Settings (HKDF-SHA256)
HKDF_HASH_ALGORITHM: str = "sha256"
HKDF_SALT: bytes = b"GarudaAI-PQC-Salt-v1-2026"
HKDF_INFO: bytes = b"GarudaAI-PQC-Password-Derivation-Key"

# Security Audit Logging Configuration
LOG_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE_PATH: str = os.path.join(LOG_DIR, "security.log")
