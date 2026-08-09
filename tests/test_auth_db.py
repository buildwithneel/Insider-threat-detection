"""
Unit tests for GarudaAI Enterprise Authentication Database Layer (auth_db.py)
"""

import os
import sys
import unittest
from datetime import datetime

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.database.auth_db import (
    init_auth_db,
    create_user,
    get_user_by_email,
    get_user_by_employee_id,
    update_last_login,
    increment_failed_attempts,
    reset_failed_attempts,
    lock_account,
    unlock_account,
    verify_user_password
)


class TestGarudaAuthDB(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db = get_db()
        # Clean test users if any
        if hasattr(cls.db, "users"):
            cls.db.users.delete_many({})

    def setUp(self):
        # Clean users collection before each test
        if hasattr(self.db, "users"):
            self.db.users.delete_many({})

    def test_01_init_auth_db(self):
        """Test index creation function on users collection."""
        res = init_auth_db(self.db)
        self.assertTrue(res["success"])
        self.assertIn("indexes created", res["message"])

    def test_02_create_user_and_schema_validation(self):
        """Test user creation and document schema fields."""
        res = create_user(
            full_name="Alice Smith",
            email="alice.smith@garuda.ai",
            employee_id="GAR-1001",
            department="Cybersecurity",
            role="SOC Analyst",
            password="SuperSecretPassword123!",
            db=self.db
        )
        self.assertTrue(res["success"])
        self.assertIn("user", res)

        user = res["user"]
        self.assertIsNotNone(user["_id"])
        self.assertEqual(user["full_name"], "Alice Smith")
        self.assertEqual(user["email"], "alice.smith@garuda.ai")
        self.assertEqual(user["employee_id"], "GAR-1001")
        self.assertEqual(user["department"], "Cybersecurity")
        self.assertEqual(user["role"], "SOC Analyst")
        self.assertTrue(user["is_active"])
        self.assertEqual(user["failed_login_attempts"], 0)
        self.assertFalse(user["account_locked"])
        self.assertIsNotNone(user["created_at"])
        self.assertIsNone(user["last_login"])

    def test_03_create_user_duplicate_email_and_employee_id(self):
        """Test unique constraint enforcement for email and employee_id."""
        create_user(
            full_name="Bob Jones",
            email="bob.jones@garuda.ai",
            employee_id="GAR-1002",
            department="Finance",
            role="Analyst",
            password="Password123!",
            db=self.db
        )

        # Duplicate email
        res1 = create_user(
            full_name="Bob Duplicate",
            email="bob.jones@garuda.ai",
            employee_id="GAR-9999",
            department="Finance",
            role="Analyst",
            password="Password123!",
            db=self.db
        )
        self.assertFalse(res1["success"])
        self.assertIn("already exists", res1["error"])

        # Duplicate employee_id
        res2 = create_user(
            full_name="Bob Unique Email",
            email="bob.unique@garuda.ai",
            employee_id="GAR-1002",
            department="Finance",
            role="Analyst",
            password="Password123!",
            db=self.db
        )
        self.assertFalse(res2["success"])
        self.assertIn("already exists", res2["error"])

    def test_04_get_user_by_email_and_employee_id(self):
        """Test fetching users by email and employee ID."""
        create_user(
            full_name="Charlie Brown",
            email="charlie@garuda.ai",
            employee_id="GAR-1003",
            department="IT Operations",
            role="Admin",
            password="Password123!",
            db=self.db
        )

        # Fetch by email
        res_email = get_user_by_email("charlie@garuda.ai", db=self.db)
        self.assertTrue(res_email["success"])
        self.assertEqual(res_email["user"]["employee_id"], "GAR-1003")

        # Fetch by employee_id
        res_emp = get_user_by_employee_id("GAR-1003", db=self.db)
        self.assertTrue(res_emp["success"])
        self.assertEqual(res_emp["user"]["email"], "charlie@garuda.ai")

        # Non-existent queries
        self.assertFalse(get_user_by_email("nonexistent@garuda.ai", db=self.db)["success"])
        self.assertFalse(get_user_by_employee_id("GAR-9999", db=self.db)["success"])

    def test_05_update_last_login(self):
        """Test updating last login timestamp."""
        create_user(
            full_name="Diana Prince",
            email="diana@garuda.ai",
            employee_id="GAR-1004",
            department="Executive",
            role="Director",
            password="Password123!",
            db=self.db
        )

        res = update_last_login("diana@garuda.ai", db=self.db)
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["user"]["last_login"])

    def test_06_increment_and_reset_failed_attempts(self):
        """Test incrementing failed login attempts and auto-locking at 5 attempts."""
        create_user(
            full_name="Eve Adams",
            email="eve@garuda.ai",
            employee_id="GAR-1005",
            department="HR",
            role="Specialist",
            password="Password123!",
            db=self.db
        )

        # 4 failed attempts -> not locked yet
        for i in range(1, 5):
            res = increment_failed_attempts("eve@garuda.ai", max_attempts=5, db=self.db)
            self.assertTrue(res["success"])
            self.assertEqual(res["failed_login_attempts"], i)
            self.assertFalse(res["account_locked"])

        # 5th failed attempt -> auto-locks account
        res5 = increment_failed_attempts("eve@garuda.ai", max_attempts=5, db=self.db)
        self.assertTrue(res5["success"])
        self.assertEqual(res5["failed_login_attempts"], 5)
        self.assertTrue(res5["account_locked"])

        # Reset failed attempts
        res_reset = reset_failed_attempts("eve@garuda.ai", db=self.db)
        self.assertTrue(res_reset["success"])
        self.assertEqual(res_reset["user"]["failed_login_attempts"], 0)

    def test_07_lock_and_unlock_account(self):
        """Test manual lock and unlock account functions."""
        create_user(
            full_name="Frank Wright",
            email="frank@garuda.ai",
            employee_id="GAR-1006",
            department="Engineering",
            role="Lead Developer",
            password="Password123!",
            db=self.db
        )

        # Lock account
        res_lock = lock_account("frank@garuda.ai", db=self.db)
        self.assertTrue(res_lock["success"])
        self.assertTrue(res_lock["account_locked"])

        # Unlock account
        res_unlock = unlock_account("frank@garuda.ai", db=self.db)
        self.assertTrue(res_unlock["success"])
        self.assertFalse(res_unlock["account_locked"])

    def test_08_password_hashing_and_verification(self):
        """Test password verification helper function."""
        raw_password = "MySecurePassword2026!"
        res = create_user(
            full_name="Grace Hopper",
            email="grace@garuda.ai",
            employee_id="GAR-1007",
            department="R&D",
            role="Architect",
            password=raw_password,
            db=self.db
        )
        self.assertTrue(res["success"])

        # Retrieve hashed password from database
        user_db_doc = get_user_by_email("grace@garuda.ai", include_password=True, db=self.db)
        hashed = user_db_doc["user"]["password"]

        # Password should be hashed (not equal to raw password)
        self.assertNotEqual(hashed, raw_password)

        # Verify correct and incorrect passwords using PQC user document
        self.assertTrue(verify_user_password(user_db_doc["user"], raw_password))
        self.assertFalse(verify_user_password(user_db_doc["user"], "WrongPassword123!"))

    def test_09_api_auth_login_endpoint(self):
        """Test Flask HTTP /api/auth/login endpoint."""
        from backend.app import app, db as app_db
        app.config["TESTING"] = True
        client = app.test_client()

        # 1. Create a user
        create_user(
            full_name="Test API User",
            email="apiuser@garuda.ai",
            employee_id="GAR-9001",
            department="SOC",
            role="Analyst",
            password="CorrectPassword123!",
            db=app_db
        )

        # 2. Test successful HTTP login
        res_ok = client.post("/api/auth/login", json={
            "email": "apiuser@garuda.ai",
            "password": "CorrectPassword123!"
        })
        self.assertEqual(res_ok.status_code, 200)
        data_ok = res_ok.get_json()
        self.assertTrue(data_ok["success"])
        self.assertEqual(data_ok["user"]["email"], "apiuser@garuda.ai")

        # 3. Test incorrect password HTTP login
        res_fail = client.post("/api/auth/login", json={
            "email": "apiuser@garuda.ai",
            "password": "WrongPassword!"
        })
        self.assertEqual(res_fail.status_code, 401)
        data_fail = res_fail.get_json()
        self.assertFalse(data_fail["success"])


if __name__ == "__main__":
    unittest.main()

