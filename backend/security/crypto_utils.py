"""
GarudaAI Cryptographic Utilities & Custom Exceptions
====================================================

Contains custom exceptions, HKDF-SHA256 key derivation,
AES-256-GCM authenticated encryption/decryption functions,
Base64 helpers, and dedicated security event logging.
"""

import os
import logging
import base64
from typing import Tuple
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

try:
    from backend.config.security import (
        AES_KEY_LENGTH,
        NONCE_LENGTH,
        HKDF_SALT,
        HKDF_INFO,
        LOG_DIR,
        LOG_FILE_PATH,
    )
except ImportError:
    from config.security import (
        AES_KEY_LENGTH,
        NONCE_LENGTH,
        HKDF_SALT,
        HKDF_INFO,
        LOG_DIR,
        LOG_FILE_PATH,
    )

# --- Custom Exception Classes ---

class PQCError(Exception):
    """Base exception for all Post-Quantum Cryptography operations."""
    pass


class KeyGenerationError(PQCError):
    """Raised when keypair generation fails."""
    pass


class EncryptionError(PQCError):
    """Raised when password encryption or KEM encapsulation fails."""
    pass


class DecryptionError(PQCError):
    """Raised when password decryption or KEM decapsulation fails."""
    pass


# --- Security Logger Setup ---

os.makedirs(LOG_DIR, exist_ok=True)
security_logger = logging.getLogger("garudaai.security")
security_logger.setLevel(logging.INFO)

if not security_logger.handlers:
    # File Handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [SECURITY_AUDIT] %(message)s")
    file_handler.setFormatter(file_formatter)
    security_logger.addHandler(file_handler)

    # Stream Handler for console output
    stream_handler = logging.StreamHandler()
    stream_formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [SECURITY] %(message)s")
    stream_handler.setFormatter(stream_formatter)
    security_logger.addHandler(stream_handler)


def log_security_event(event_type: str, details: str, is_warning: bool = False, is_error: bool = False):
    """
    Logs security events without ever recording plain-text passwords or secret keys.
    """
    msg = f"EVENT={event_type} | DETAILS={details}"
    if is_error:
        security_logger.error(msg)
    elif is_warning:
        security_logger.warning(msg)
    else:
        security_logger.info(msg)


# --- Base64 Utilities ---

def encode_b64(data: bytes) -> str:
    """Encodes raw bytes to Base64 string."""
    if not isinstance(data, bytes):
        raise TypeError("Data must be bytes")
    return base64.b64encode(data).decode("utf-8")


def decode_b64(data_str: str) -> bytes:
    """Decodes Base64 string to raw bytes."""
    if not isinstance(data_str, str):
        raise TypeError("Data must be a Base64 string")
    return base64.b64decode(data_str.encode("utf-8"))


# --- Cryptographic Helper Functions ---

def derive_aes_key(shared_secret: bytes) -> bytes:
    """
    Derives a 256-bit AES key from a Post-Quantum shared secret using HKDF-SHA256.

    :param shared_secret: Raw shared secret bytes produced by ML-KEM.
    :return: 32-byte (256-bit) AES key.
    """
    if not isinstance(shared_secret, bytes) or len(shared_secret) == 0:
        raise EncryptionError("Invalid shared secret for HKDF key derivation.")
    
    try:
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=AES_KEY_LENGTH,
            salt=HKDF_SALT,
            info=HKDF_INFO,
        )
        return hkdf.derive(shared_secret)
    except Exception as e:
        log_security_event("HKDF_DERIVATION_FAILED", str(e), is_error=True)
        raise EncryptionError(f"HKDF-SHA256 key derivation failed: {str(e)}") from e


def aes_gcm_encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypts plaintext using AES-256-GCM.

    :param key: 256-bit AES key.
    :param plaintext: Plaintext bytes.
    :return: Tuple of (ciphertext, nonce, authentication_tag).
    """
    if not isinstance(key, bytes) or len(key) != AES_KEY_LENGTH:
        raise EncryptionError(f"AES key must be exactly {AES_KEY_LENGTH} bytes.")
    
    try:
        nonce = os.urandom(NONCE_LENGTH)
        aesgcm = AESGCM(key)
        # AESGCM.encrypt appends 16-byte GCM tag to the ciphertext
        ct_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data=None)
        
        ciphertext = ct_with_tag[:-16]
        auth_tag = ct_with_tag[-16:]
        return ciphertext, nonce, auth_tag
    except Exception as e:
        log_security_event("AES_GCM_ENCRYPTION_FAILED", str(e), is_error=True)
        raise EncryptionError(f"AES-256-GCM encryption failed: {str(e)}") from e


def aes_gcm_decrypt(key: bytes, ciphertext: bytes, nonce: bytes, auth_tag: bytes) -> bytes:
    """
    Decrypts ciphertext using AES-256-GCM.

    :param key: 256-bit AES key.
    :param ciphertext: Ciphertext bytes.
    :param nonce: 96-bit nonce.
    :param auth_tag: 128-bit authentication tag.
    :return: Plaintext bytes.
    """
    if not isinstance(key, bytes) or len(key) != AES_KEY_LENGTH:
        raise DecryptionError(f"AES key must be exactly {AES_KEY_LENGTH} bytes.")
    if not isinstance(nonce, bytes) or len(nonce) != NONCE_LENGTH:
        raise DecryptionError(f"Nonce must be exactly {NONCE_LENGTH} bytes.")
    if not isinstance(auth_tag, bytes) or len(auth_tag) != 16:
        raise DecryptionError("Authentication tag must be exactly 16 bytes.")
        
    try:
        aesgcm = AESGCM(key)
        ct_with_tag = ciphertext + auth_tag
        return aesgcm.decrypt(nonce, ct_with_tag, associated_data=None)
    except Exception as e:
        log_security_event("AES_GCM_DECRYPTION_FAILED", str(e), is_error=True)
        raise DecryptionError(f"AES-256-GCM decryption failed: {str(e)}") from e
