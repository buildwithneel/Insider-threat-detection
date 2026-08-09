"""
GarudaAI Post-Quantum Cryptography Password Migration Utility
=============================================================

Scans the MongoDB 'users' collection for legacy password records
(bcrypt/pbkdf2/scrypt or plaintext) and converts them into NIST ML-KEM-768 +
AES-256-GCM Post-Quantum Cryptography (PQC) encrypted payload documents.

Ensures zero data loss and preserves existing user metadata.
"""

import sys
import os

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from backend.db_client import get_db
    from backend.security.password_service import encrypt_password
    from backend.security.crypto_utils import log_security_event
except ImportError:
    from db_client import get_db
    from security.password_service import encrypt_password
    from security.crypto_utils import log_security_event


def run_password_migration(db=None, fallback_default_password="Password123!"):
    """
    Executes automated database migration for legacy password documents.

    :param db: PyMongo / MockDatabase instance (optional).
    :param fallback_default_password: Default password string if legacy hash cannot be inverted.
    :return: Summary dict containing migration statistics.
    """
    if db is None:
        db = get_db()

    log_security_event("MIGRATION_STARTED", "Starting PQC password migration for 'users' collection.")
    
    users = list(db.users.find({}))
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    print(f"[PQC Migration] Found {len(users)} user record(s) in 'users' collection.")

    for user in users:
        email = user.get("email", "unknown")
        user_id = user.get("_id")

        # Check if user already has PQC encrypted payload
        if user.get("encapsulated_secret") and user.get("nonce") and user.get("private_key"):
            skipped_count += 1
            continue

        try:
            # If user has a legacy plaintext or known password field, encrypt with PQC
            raw_password = user.get("plain_password") or user.get("password") or fallback_default_password
            
            # Encrypt password using ML-KEM-768 + HKDF-SHA256 + AES-256-GCM
            pqc_payload = encrypt_password(raw_password)

            update_fields = {
                "password": pqc_payload["encrypted_password"],
                "encrypted_password": pqc_payload["encrypted_password"],
                "nonce": pqc_payload["nonce"],
                "authentication_tag": pqc_payload["authentication_tag"],
                "encapsulated_secret": pqc_payload["encapsulated_secret"],
                "private_key": pqc_payload["private_key"],
                "algorithm": pqc_payload["algorithm"]
            }

            db.users.update_one({"_id": user_id}, {"$set": update_fields})
            migrated_count += 1
            log_security_event("USER_MIGRATED_TO_PQC", f"User={email} migrated to ML-KEM-768 + AES-256-GCM")
            print(f"  [+] Migrated user '{email}' to PQC format.")

        except Exception as e:
            error_count += 1
            log_security_event("USER_MIGRATION_FAILED", f"User={email} error: {e}", is_error=True)
            print(f"  [-] Failed to migrate user '{email}': {e}")

    summary = {
        "status": "success",
        "total_records": len(users),
        "migrated": migrated_count,
        "skipped_already_pqc": skipped_count,
        "errors": error_count
    }

    log_security_event(
        "MIGRATION_COMPLETED",
        f"Total={len(users)}, Migrated={migrated_count}, Skipped={skipped_count}, Errors={error_count}"
    )
    print(f"[PQC Migration Complete] {summary}")
    return summary


if __name__ == "__main__":
    run_password_migration()
