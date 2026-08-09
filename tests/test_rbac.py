import os
import sys
import unittest

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.database.rbac_db import init_rbac_db, get_role_permissions, create_user_session, validate_session
from backend.app import app, limiter


class TestGarudaAIRbac(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["RATELIMIT_ENABLED"] = False
        limiter.enabled = False
        cls.client = app.test_client()
        cls.db = get_db()
        init_rbac_db(cls.db)

    def test_01_role_permission_matrices(self):
        """Verify role permissions for all 5 roles."""
        ceo_perms = get_role_permissions("CEO", self.db)
        self.assertIn("create_users", ceo_perms)
        self.assertIn("system_settings", ceo_perms)

        hr_perms = get_role_permissions("HR", self.db)
        self.assertIn("view_employees", hr_perms)
        self.assertNotIn("delete_users", hr_perms)
        self.assertNotIn("api_settings", hr_perms)

        sec_mgr_perms = get_role_permissions("Security Manager", self.db)
        self.assertIn("generate_jit_tokens", sec_mgr_perms)
        self.assertNotIn("delete_users", sec_mgr_perms)

        analyst_perms = get_role_permissions("Security Analyst", self.db)
        self.assertIn("create_investigation_report", analyst_perms)
        self.assertNotIn("generate_jit_tokens", analyst_perms)
        self.assertNotIn("unlock_employees", analyst_perms)

        auditor_perms = get_role_permissions("Auditor", self.db)
        self.assertIn("audit_logs", auditor_perms)
        self.assertNotIn("create_users", auditor_perms)

    def test_02_login_all_seed_accounts(self):
        """Test login for all 5 enterprise role seed accounts."""
        credentials = [
            ("ceo@garudaai.com", "Ceo@Garuda2026!", "CEO"),
            ("hr@garudaai.com", "Hr@Garuda2026!", "HR"),
            ("security.manager@garudaai.com", "SecManager@Garuda2026!", "Security Manager"),
            ("security.analyst@garudaai.com", "SecAnalyst@Garuda2026!", "Security Analyst"),
            ("auditor@garudaai.com", "Auditor@Garuda2026!", "Auditor"),
        ]

        for email, password, expected_role in credentials:
            res = self.client.post("/api/auth/login", json={"email": email, "password": password})
            self.assertEqual(res.status_code, 200, f"Login failed for {email}")
            data = res.get_json()
            self.assertTrue(data["success"])
            self.assertEqual(data["user"]["role"], expected_role)
            self.assertIsNotNone(data["token"])
            self.assertIn("permissions", data["user"])

    def test_03_unauthorized_access_403(self):
        """Verify Security Analyst receives 403 Access Denied when attempting unauthorized JIT token creation."""
        # 1. Login as Security Analyst
        analyst_login = self.client.post("/api/auth/login", json={
            "email": "security.analyst@garudaai.com",
            "password": "SecAnalyst@Garuda2026!"
        }).get_json()
        analyst_token = analyst_login["token"]

        # 2. Attempt JIT issue token (Requires 'generate_jit_tokens' permission)
        res = self.client.post(
            "/api/jit/tokens/issue",
            headers={"Authorization": f"Bearer {analyst_token}"},
            json={"employee_id": "GAR-0001", "access_type": "Full Access"}
        )
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data["success"])
        self.assertEqual(data["error"], "Access Denied")

    def test_04_audit_logs_logging(self):
        """Verify audit logs record action events and permission denials."""
        # Login as Auditor
        auditor_login = self.client.post("/api/auth/login", json={
            "email": "auditor@garudaai.com",
            "password": "Auditor@Garuda2026!"
        }).get_json()
        auditor_token = auditor_login["token"]

        res = self.client.get(
            "/api/rbac/audit-logs",
            headers={"Authorization": f"Bearer {auditor_token}"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["audit_logs"]), 0)


if __name__ == "__main__":
    unittest.main()
