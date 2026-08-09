import os
import sys
import time
import unittest
from datetime import datetime, timezone, timedelta

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.app import app
from backend.database.jit_db import (
    create_jit_token,
    verify_and_use_jit_token,
    revoke_jit_token,
    extend_jit_token,
    auto_expire_tokens,
    get_jit_tokens,
    get_jit_audit_logs,
    get_jit_dashboard_stats,
    hash_token,
    ALL_JIT_PERMISSIONS
)
from backend.security.jit_middleware import require_jit_permission

class TestJitPersistentStorage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.db = get_db()

        # Clean baseline JIT collections for test employee
        cls.test_emp_id = "EMP_JIT_PERSIST_001"
        cls.db.jit_tokens.delete_many({"employee_id": cls.test_emp_id})
        cls.db.jit_audit_logs.delete_many({"employee.id": cls.test_emp_id})

    @classmethod
    def tearDownClass(cls):
        cls.db.jit_tokens.delete_many({"employee_id": cls.test_emp_id})
        cls.db.jit_audit_logs.delete_many({"employee.id": cls.test_emp_id})

    def test_01_token_creation_and_sha256_hashing(self):
        """Verify token is stored hashed in MongoDB and plain token is never persisted."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Full Access",
            granted_permissions=ALL_JIT_PERMISSIONS,
            duration_minutes=60,
            db=self.db
        )

        self.assertIsNotNone(plain_token)
        self.assertTrue(plain_token.startswith("JIT-"))
        self.assertEqual(token_doc["employee_id"], self.test_emp_id)
        self.assertEqual(token_doc["access_type"], "Full Access")
        self.assertEqual(len(token_doc["granted_permissions"]), 16)
        self.assertEqual(token_doc["status"], "Active")

        # Verify raw collection doc in MongoDB
        raw_doc = self.db.jit_tokens.find_one({"token_id": token_doc["token_id"]})
        self.assertIsNotNone(raw_doc)
        self.assertNotIn("plain_token", raw_doc)
        self.assertNotIn(plain_token, str(raw_doc))
        self.assertEqual(raw_doc["token_hash"], hash_token(plain_token))

        # Verify audit log
        logs = get_jit_audit_logs(employee_id=self.test_emp_id, db=self.db)
        issued_logs = [l for l in logs if l["event_type"] == "Token Issued"]
        self.assertGreaterEqual(len(issued_logs), 1)

    def test_02_access_level_selection_limited(self):
        """Verify Limited Access token creation with subset of permissions."""
        limited_perms = ["Dashboard", "Alerts", "Reports"]
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Limited Access",
            granted_permissions=limited_perms,
            duration_minutes=30,
            db=self.db
        )

        self.assertEqual(token_doc["access_type"], "Limited Access")
        self.assertEqual(token_doc["granted_permissions"], limited_perms)
        self.assertNotIn("Settings", token_doc["granted_permissions"])

    def test_03_token_verification_and_usage(self):
        """Verify verification of plain token against stored hash."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Full Access",
            granted_permissions=ALL_JIT_PERMISSIONS,
            duration_minutes=60,
            db=self.db
        )

        is_valid, doc, msg = verify_and_use_jit_token(
            plain_token=plain_token,
            employee_id=self.test_emp_id,
            db=self.db
        )

        self.assertTrue(is_valid)
        self.assertIsNotNone(doc["last_used"])
        self.assertEqual(msg, "Token verified and JIT access granted.")

        # Check audit logs for Token Used
        logs = get_jit_audit_logs(employee_id=self.test_emp_id, db=self.db)
        used_logs = [l for l in logs if l["event_type"] == "Token Used"]
        self.assertGreaterEqual(len(used_logs), 1)

    def test_04_token_expiration_handling(self):
        """Verify tokens past expiration become invalid and update status."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Full Access",
            granted_permissions=ALL_JIT_PERMISSIONS,
            duration_minutes=-5, # Past expiration
            db=self.db
        )

        auto_expire_tokens(db=self.db)

        is_valid, doc, msg = verify_and_use_jit_token(
            plain_token=plain_token,
            employee_id=self.test_emp_id,
            db=self.db
        )

        self.assertFalse(is_valid)
        self.assertIn("expired", msg.lower())

    def test_05_admin_token_extension(self):
        """Verify extending expiration timer updates expires_at and logs event."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Full Access",
            granted_permissions=ALL_JIT_PERMISSIONS,
            duration_minutes=30,
            db=self.db
        )

        success, updated_doc, msg = extend_jit_token(
            token_id=token_doc["token_id"],
            additional_minutes=45,
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            db=self.db
        )

        self.assertTrue(success)
        self.assertIn("successfully extended", msg)

        logs = get_jit_audit_logs(employee_id=self.test_emp_id, db=self.db)
        extended_logs = [l for l in logs if l["event_type"] == "Timer Extended"]
        self.assertGreaterEqual(len(extended_logs), 1)

    def test_06_admin_token_revocation(self):
        """Verify revoking token instantly invalidates it."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Alice Security Engineer",
            department="SOC Ops",
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            access_type="Full Access",
            granted_permissions=ALL_JIT_PERMISSIONS,
            duration_minutes=60,
            db=self.db
        )

        success, msg = revoke_jit_token(
            token_id=token_doc["token_id"],
            admin_id="GAR-0001",
            admin_name="Lead Administrator",
            reason="Security Audit Precaution",
            db=self.db
        )

        self.assertTrue(success)

        is_valid, doc, msg_verify = verify_and_use_jit_token(
            plain_token=plain_token,
            employee_id=self.test_emp_id,
            db=self.db
        )

        self.assertFalse(is_valid)
        self.assertIn("revoked", msg_verify.lower())

    def test_07_api_endpoints_integration(self):
        """Test Flask REST API routes for JIT management."""
        # 1. Issue Token via REST API
        issue_res = self.client.post("/api/jit/tokens/issue", json={
            "employee_id": self.test_emp_id,
            "employee_name": "Alice Security Engineer",
            "department": "SOC Ops",
            "access_type": "Limited Access",
            "granted_permissions": ["Dashboard", "Analytics"],
            "preset_duration": "30 Minutes"
        })
        self.assertEqual(issue_res.status_code, 201)
        issue_data = issue_res.get_json()
        self.assertTrue(issue_data["success"])
        plain_tok = issue_data["secure_token"]
        tok_id = issue_data["token"]["token_id"]

        # 2. Verify Token via REST API
        verify_res = self.client.post("/api/jit/tokens/verify", json={
            "token": plain_tok,
            "employee_id": self.test_emp_id
        })
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.get_json()["success"])

        # 3. List Tokens via REST API
        list_res = self.client.get(f"/api/jit/tokens?employee_id={self.test_emp_id}")
        self.assertEqual(list_res.status_code, 200)
        self.assertGreaterEqual(list_res.get_json()["count"], 1)

        # 4. Extend Expiry via REST API
        extend_res = self.client.post(f"/api/jit/tokens/{tok_id}/extend", json={
            "additional_minutes": 60
        })
        self.assertEqual(extend_res.status_code, 200)

        # 5. Revoke Token via REST API
        revoke_res = self.client.post(f"/api/jit/tokens/{tok_id}/revoke", json={
            "reason": "Test Revocation"
        })
        self.assertEqual(revoke_res.status_code, 200)

        # 6. Audit Logs Endpoint
        log_res = self.client.get(f"/api/jit/audit-logs?employee_id={self.test_emp_id}")
        self.assertEqual(log_res.status_code, 200)
        self.assertGreaterEqual(log_res.get_json()["count"], 1)

        # 7. Dashboard Stats Endpoint
        stats_res = self.client.get("/api/jit/dashboard/stats")
        self.assertEqual(stats_res.status_code, 200)
        self.assertTrue("stats" in stats_res.get_json())

if __name__ == "__main__":
    unittest.main()
