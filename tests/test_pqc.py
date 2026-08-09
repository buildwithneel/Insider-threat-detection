"""
Unit tests for GarudaAI Post-Quantum Cryptography (ML-KEM-768) Authentication Suite
"""

import os
import sys
import unittest

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.security import (
    generate_keypair,
    encapsulate_secret,
    decapsulate_secret,
    encrypt_password,
    decrypt_password,
    verify_pqc_password,
    PQCError,
    EncryptionError,
    DecryptionError,
)
from backend.database.auth_db import (
    create_user,
    get_user_by_email,
    verify_user_password,
)
from backend.scripts.migrate_passwords import run_password_migration


class TestGarudaPQCAuthentication(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = get_db()
        if hasattr(cls.db, "users"):
            cls.db.users.delete_many({})

    def setUp(self):
        if hasattr(self.db, "users"):
            self.db.users.delete_many({})

    def test_01_pqc_keypair_generation(self):
        """Test ML-KEM-768 keypair generation."""
        pk_b64, sk_b64 = generate_keypair()
        self.assertIsInstance(pk_b64, str)
        self.assertIsInstance(sk_b64, str)
        self.assertGreater(len(pk_b64), 50)
        self.assertGreater(len(sk_b64), 50)

    def test_02_pqc_encapsulation_and_decapsulation(self):
        """Test ML-KEM-768 shared secret encapsulation and decapsulation."""
        pk_b64, sk_b64 = generate_keypair()
        
        # Encapsulate
        ct_b64, ss1_b64 = encapsulate_secret(pk_b64)
        self.assertIsInstance(ct_b64, str)
        self.assertIsInstance(ss1_b64, str)

        # Decapsulate
        ss2_b64 = decapsulate_secret(ct_b64, sk_b64)
        
        # Both shared secrets must match exactly
        self.assertEqual(ss1_b64, ss2_b64)

    def test_03_aes_gcm_password_protection(self):
        """Test password encryption and decryption workflow (ML-KEM-768 + HKDF + AES-256-GCM)."""
        raw_password = "QuantumSafePassword2026!#$"
        pqc_payload = encrypt_password(raw_password)

        self.assertIn("encrypted_password", pqc_payload)
        self.assertIn("nonce", pqc_payload)
        self.assertIn("authentication_tag", pqc_payload)
        self.assertIn("encapsulated_secret", pqc_payload)
        self.assertIn("private_key", pqc_payload)
        self.assertIn("algorithm", pqc_payload)

        # Decrypt password
        decrypted = decrypt_password(pqc_payload)
        self.assertEqual(decrypted, raw_password)

        # Verify password function
        self.assertTrue(verify_pqc_password(pqc_payload, raw_password))
        self.assertFalse(verify_pqc_password(pqc_payload, "WrongPassword123!"))

    def test_04_invalid_ciphertext_and_nonce_error_handling(self):
        """Test decryption failure on invalid ciphertext or tampered nonce."""
        raw_password = "SecretPassword123!"
        pqc_payload = encrypt_password(raw_password)

        # Tamper ciphertext
        bad_payload = pqc_payload.copy()
        bad_payload["encrypted_password"] = "AAAA" + pqc_payload["encrypted_password"][4:]
        
        with self.assertRaises(DecryptionError):
            decrypt_password(bad_payload)

        # Tamper nonce
        bad_nonce_payload = pqc_payload.copy()
        bad_nonce_payload["nonce"] = "BBBB" + pqc_payload["nonce"][4:]
        
        with self.assertRaises(DecryptionError):
            decrypt_password(bad_nonce_payload)

    def test_05_pqc_user_registration_and_db_persistence(self):
        """Test registering a user with PQC encryption and verifying MongoDB document fields."""
        res = create_user(
            full_name="Dr. Alan Turing",
            email="alan.turing@garuda.ai",
            employee_id="GAR-PQC-001",
            department="Quantum Cryptography",
            role="Chief Scientist",
            password="UltraSecretQuantumPass2026!",
            db=self.db
        )
        self.assertTrue(res["success"])

        # Fetch stored document from MongoDB
        user_doc = get_user_by_email("alan.turing@garuda.ai", include_password=True, db=self.db)
        self.assertTrue(user_doc["success"])
        user = user_doc["user"]

        # Verify PQC fields are stored in MongoDB
        self.assertIn("encrypted_password", user)
        self.assertIn("nonce", user)
        self.assertIn("authentication_tag", user)
        self.assertIn("encapsulated_secret", user)
        self.assertIn("private_key", user)
        self.assertIn("algorithm", user)
        self.assertIn("created_at", user)

        # Verify user password decapsulation & decryption
        self.assertTrue(verify_user_password(user, "UltraSecretQuantumPass2026!"))
        self.assertFalse(verify_user_password(user, "WrongPassword!"))

    def test_06_flask_pqc_login_and_registration_endpoints(self):
        """Test Flask HTTP /api/auth/register and /api/auth/login endpoints with PQC."""
        from backend.app import app, db as app_db
        app.config["TESTING"] = True
        client = app.test_client()

        # 1. Register user via HTTP API
        res_reg = client.post("/api/auth/register", json={
            "full_name": "Post Quantum User",
            "email": "pqc.user@garuda.ai",
            "employee_id": "GAR-PQC-002",
            "department": "Security Architecture",
            "role": "PQC Architect",
            "password": "QuantumAPIAuthPassword2026!"
        })
        self.assertEqual(res_reg.status_code, 201)
        self.assertTrue(res_reg.get_json()["success"])

        # 2. Login user via HTTP API
        res_login = client.post("/api/auth/login", json={
            "email": "pqc.user@garuda.ai",
            "password": "QuantumAPIAuthPassword2026!"
        })
        self.assertEqual(res_login.status_code, 200)
        data_login = res_login.get_json()
        self.assertTrue(data_login["success"])
        self.assertEqual(data_login["user"]["email"], "pqc.user@garuda.ai")

        # 3. Invalid password HTTP login
        res_wrong = client.post("/api/auth/login", json={
            "email": "pqc.user@garuda.ai",
            "password": "IncorrectPassword!"
        })
        self.assertEqual(res_wrong.status_code, 401)
        self.assertFalse(res_wrong.get_json()["success"])

    def test_07_database_password_migration_utility(self):
        """Test migrating legacy user password documents to PQC format."""
        # Insert a legacy user document
        legacy_doc = {
            "full_name": "Legacy User",
            "email": "legacy.user@garuda.ai",
            "employee_id": "GAR-LEGACY-01",
            "department": "Legacy Operations",
            "role": "Analyst",
            "password": "scrypt:32768:8:1$legacy_hash_sample_string",
            "plain_password": "LegacyPassword123!",
            "is_active": True,
            "failed_login_attempts": 0,
            "account_locked": False
        }
        self.db.users.insert_one(legacy_doc)

        # Run migration utility
        summary = run_password_migration(db=self.db, fallback_default_password="LegacyPassword123!")
        self.assertEqual(summary["status"], "success")
        self.assertGreaterEqual(summary["migrated"], 1)

        # Verify user record was updated with PQC fields
        migrated_user = get_user_by_email("legacy.user@garuda.ai", include_password=True, db=self.db)["user"]
        self.assertIn("encapsulated_secret", migrated_user)
        self.assertIn("nonce", migrated_user)
        self.assertIn("private_key", migrated_user)

        # Verify password verification works post-migration
        self.assertTrue(verify_user_password(migrated_user, "LegacyPassword123!"))

    def test_08_pqc_change_password_endpoint(self):
        """Test changing password after login using PQC encryption."""
        from backend.app import app, db as app_db
        app.config["TESTING"] = True
        client = app.test_client()

        # 1. Create a user
        create_user(
            full_name="Change Pass User",
            email="changepass@garuda.ai",
            employee_id="GAR-CP-01",
            department="SOC",
            role="Analyst",
            password="OldPassword123!",
            db=app_db
        )

        # 2. Attempt password change with WRONG current password
        res_wrong = client.post("/api/auth/change-password", json={
            "email": "changepass@garuda.ai",
            "current_password": "WrongOldPassword!",
            "new_password": "NewQuantumPassword123!"
        })
        self.assertEqual(res_wrong.status_code, 400)
        self.assertFalse(res_wrong.get_json()["success"])

        # 3. Perform password change with CORRECT current password
        res_ok = client.post("/api/auth/change-password", json={
            "email": "changepass@garuda.ai",
            "current_password": "OldPassword123!",
            "new_password": "NewQuantumPassword123!"
        })
        self.assertEqual(res_ok.status_code, 200)
        self.assertTrue(res_ok.get_json()["success"])

        # 4. Verify login with NEW password works
        res_login_new = client.post("/api/auth/login", json={
            "email": "changepass@garuda.ai",
            "password": "NewQuantumPassword123!"
        })
        self.assertEqual(res_login_new.status_code, 200)
        self.assertTrue(res_login_new.get_json()["success"])


if __name__ == "__main__":
    unittest.main()

