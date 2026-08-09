"""
GarudaAI Quantum-Safe Password Protection Service
=================================================

Provides PQC password protection workflow using NIST ML-KEM-768,
HKDF-SHA256, and AES-256-GCM.

Workflow:
1. Generate ML-KEM-768 Keypair (Public Key, Private Key).
2. Encapsulate Shared Secret using Public Key -> (Encapsulated Secret, Shared Secret).
3. Derive 256-bit AES Key from Shared Secret using HKDF-SHA256.
4. Encrypt password with AES-256-GCM -> (Ciphertext, Nonce, Auth Tag).
5. Return JSON-compatible dictionary with Base64 fields.
"""

from typing import Dict, Any

try:
    from backend.config.security import PQC_ALGORITHM
    from backend.security.pqc import (
        generate_keypair,
        encapsulate_secret,
        decapsulate_secret,
    )
    from backend.security.crypto_utils import (
        derive_aes_key,
        aes_gcm_encrypt,
        aes_gcm_decrypt,
        encode_b64,
        decode_b64,
        EncryptionError,
        DecryptionError,
        log_security_event,
    )
except ImportError:
    from config.security import PQC_ALGORITHM
    from security.pqc import (
        generate_keypair,
        encapsulate_secret,
        decapsulate_secret,
    )
    from security.crypto_utils import (
        derive_aes_key,
        aes_gcm_encrypt,
        aes_gcm_decrypt,
        encode_b64,
        decode_b64,
        EncryptionError,
        DecryptionError,
        log_security_event,
    )


def encrypt_password(password: str) -> Dict[str, Any]:
    """
    Encrypts a plain-text password using ML-KEM-768 + HKDF-SHA256 + AES-256-GCM.

    :param password: Plain-text password string.
    :return: Dictionary containing Base64 encrypted parameters ready for MongoDB.
    """
    if not password or not isinstance(password, str):
        raise EncryptionError("Password parameter must be a non-empty string.")

    try:
        # 1. Generate ML-KEM-768 keypair
        pk_b64, sk_b64 = generate_keypair()

        # 2. Encapsulate shared secret using recipient public key
        ct_kem_b64, ss_b64 = encapsulate_secret(pk_b64)

        # 3. Derive 256-bit AES key via HKDF-SHA256 from shared secret
        shared_secret_bytes = decode_b64(ss_b64)
        aes_key = derive_aes_key(shared_secret_bytes)

        # 4. Encrypt password using AES-256-GCM
        password_bytes = password.encode("utf-8")
        ciphertext_bytes, nonce_bytes, auth_tag_bytes = aes_gcm_encrypt(aes_key, password_bytes)

        log_security_event(
            "PASSWORD_PQC_ENCRYPTED",
            f"Algorithm={PQC_ALGORITHM} + AES-256-GCM"
        )

        return {
            "encrypted_password": encode_b64(ciphertext_bytes),
            "nonce": encode_b64(nonce_bytes),
            "authentication_tag": encode_b64(auth_tag_bytes),
            "encapsulated_secret": ct_kem_b64,
            "private_key": sk_b64,
            "algorithm": f"{PQC_ALGORITHM} + HKDF-SHA256 + AES-256-GCM"
        }

    except EncryptionError:
        raise
    except Exception as e:
        log_security_event("PASSWORD_PQC_ENCRYPTION_FAILED", str(e), is_error=True)
        raise EncryptionError(f"Quantum password encryption failed: {str(e)}") from e


def decrypt_password(pqc_data: Dict[str, Any]) -> str:
    """
    Decrypts a PQC-encrypted password payload using ML-KEM-768 decapsulation and AES-256-GCM.

    :param pqc_data: Dictionary containing Base64 PQC encryption fields.
    :return: Plain-text password string.
    """
    if not isinstance(pqc_data, dict):
        raise DecryptionError("PQC payload must be a dictionary.")

    required_fields = ["encrypted_password", "nonce", "authentication_tag", "encapsulated_secret", "private_key"]
    for field in required_fields:
        if not pqc_data.get(field):
            raise DecryptionError(f"Missing required PQC payload field: '{field}'")

    try:
        ct_kem_b64 = pqc_data["encapsulated_secret"]
        sk_b64 = pqc_data["private_key"]
        ciphertext_bytes = decode_b64(pqc_data["encrypted_password"])
        nonce_bytes = decode_b64(pqc_data["nonce"])
        auth_tag_bytes = decode_b64(pqc_data["authentication_tag"])

        # 1. Recover shared secret using ML-KEM-768 decapsulation
        ss_b64 = decapsulate_secret(ct_kem_b64, sk_b64)

        # 2. Derive 256-bit AES key via HKDF-SHA256
        shared_secret_bytes = decode_b64(ss_b64)
        aes_key = derive_aes_key(shared_secret_bytes)

        # 3. Decrypt ciphertext using AES-256-GCM
        plaintext_bytes = aes_gcm_decrypt(aes_key, ciphertext_bytes, nonce_bytes, auth_tag_bytes)
        
        log_security_event("PASSWORD_PQC_DECRYPTED", f"Algorithm={PQC_ALGORITHM} + AES-256-GCM")
        return plaintext_bytes.decode("utf-8")

    except DecryptionError:
        raise
    except Exception as e:
        log_security_event("PASSWORD_PQC_DECRYPTION_FAILED", str(e), is_error=True)
        raise DecryptionError(f"Quantum password decryption failed: {str(e)}") from e


def verify_pqc_password(pqc_data: Dict[str, Any], candidate_password: str) -> bool:
    """
    Verifies a candidate password against a PQC-encrypted password payload.

    :param pqc_data: PQC encrypted payload dictionary.
    :param candidate_password: Plain-text password provided during authentication.
    :return: bool (True if match, False otherwise).
    """
    if not pqc_data or not candidate_password:
        return False

    try:
        decrypted_password = decrypt_password(pqc_data)
        return decrypted_password == candidate_password
    except Exception as e:
        log_security_event("PASSWORD_VERIFICATION_FAILED", f"Decryption error: {str(e)}", is_warning=True)
        return False
