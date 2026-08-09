"""
JIT Security Token Pipeline Verification - User Prompt Test Cases
"""

import unittest
from datetime import datetime, timezone
from backend.database.jit_db import create_jit_token, get_jit_tokens, ALL_JIT_PERMISSIONS
from backend.db_client import get_db

class TestJitPromptCases(unittest.TestCase):
    def setUp(self):
        self.db = get_db("mongodb://localhost:27017/garudaai_test_jit")
        self.db.jit_tokens.delete_many({})
        self.db.jit_audit_logs.delete_many({})

    def test_case_1_limited_access_15_minutes(self):
        """Limited Access, 15 Minutes -> Expected: Database: Limited, 15 Min; Registry: Limited, 15 Min; Employee: Limited Access"""
        selected_perms = ["Dashboard", "AI Investigation"]
        doc, plain_token = create_jit_token(
            employee_id="EMP-TEST-001",
            employee_name="Test User 1",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Limited Access",
            granted_permissions=selected_perms,
            duration_minutes=15.0,
            db=self.db
        )

        self.assertEqual(doc["access_type"], "Limited Access")
        self.assertEqual(doc["accessLevel"], "LIMITED")
        self.assertEqual(doc["duration"], 15.0)
        self.assertEqual(doc["duration_minutes"], 15.0)
        self.assertEqual(doc["granted_permissions"], selected_perms)
        self.assertEqual(len(doc["granted_permissions"]), 2)

        # Check DB retrieval
        tokens = get_jit_tokens(employee_id="EMP-TEST-001", db=self.db)
        self.assertEqual(len(tokens), 1)
        stored = tokens[0]
        self.assertEqual(stored["access_type"], "Limited Access")
        self.assertEqual(stored["duration"], 15.0)

        # Calculate exact expiry difference
        iss = datetime.fromisoformat(stored["issued_at"])
        exp = datetime.fromisoformat(stored["expires_at"])
        diff_mins = (exp - iss).total_seconds() / 60.0
        self.assertAlmostEqual(diff_mins, 15.0, places=1)

    def test_case_2_limited_access_30_minutes(self):
        """Limited Access, 30 Minutes -> Expected: Limited, 30 Minutes"""
        selected_perms = ["Dashboard", "Alerts", "Reports"]
        doc, _ = create_jit_token(
            employee_id="EMP-TEST-002",
            employee_name="Test User 2",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Limited Access",
            granted_permissions=selected_perms,
            duration_minutes=30.0,
            db=self.db
        )

        self.assertEqual(doc["access_type"], "Limited Access")
        self.assertEqual(doc["duration"], 30.0)

        iss = datetime.fromisoformat(doc["issued_at"])
        exp = datetime.fromisoformat(doc["expires_at"])
        diff_mins = (exp - iss).total_seconds() / 60.0
        self.assertAlmostEqual(diff_mins, 30.0, places=1)

    def test_case_3_full_access_15_minutes(self):
        """Full Access, 15 Minutes -> Expected: Full, 15 Minutes"""
        doc, _ = create_jit_token(
            employee_id="EMP-TEST-003",
            employee_name="Test User 3",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Full Access",
            granted_permissions=[],
            duration_minutes=15.0,
            db=self.db
        )

        self.assertEqual(doc["access_type"], "Full Access")
        self.assertEqual(doc["accessLevel"], "FULL")
        self.assertEqual(doc["duration"], 15.0)
        self.assertEqual(len(doc["granted_permissions"]), len(ALL_JIT_PERMISSIONS))

        iss = datetime.fromisoformat(doc["issued_at"])
        exp = datetime.fromisoformat(doc["expires_at"])
        diff_mins = (exp - iss).total_seconds() / 60.0
        self.assertAlmostEqual(diff_mins, 15.0, places=1)

    def test_case_4_full_access_60_minutes(self):
        """Full Access, 60 Minutes -> Expected: Full, 60 Minutes"""
        doc, _ = create_jit_token(
            employee_id="EMP-TEST-004",
            employee_name="Test User 4",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Full Access",
            granted_permissions=[],
            duration_minutes=60.0,
            db=self.db
        )

        self.assertEqual(doc["access_type"], "Full Access")
        self.assertEqual(doc["duration"], 60.0)

        iss = datetime.fromisoformat(doc["issued_at"])
        exp = datetime.fromisoformat(doc["expires_at"])
        diff_mins = (exp - iss).total_seconds() / 60.0
        self.assertAlmostEqual(diff_mins, 60.0, places=1)

    def test_case_5_employee_specific_stats(self):
        """Verify get_jit_dashboard_stats filters tokens & permission distribution per employee_id"""
        from backend.database.jit_db import get_jit_dashboard_stats

        # Create Limited token for Employee A with 2 permissions
        create_jit_token(
            employee_id="EMP-A",
            employee_name="Emp A",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Limited Access",
            granted_permissions=["Dashboard", "Reports"],
            duration_minutes=15.0,
            db=self.db
        )

        # Create Full Access token for Employee B with 16 permissions
        create_jit_token(
            employee_id="EMP-B",
            employee_name="Emp B",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Full Access",
            granted_permissions=[],
            duration_minutes=60.0,
            db=self.db
        )

        # Fetch stats for Employee A
        stats_a = get_jit_dashboard_stats(employee_id="EMP-A", db=self.db)
        self.assertEqual(stats_a["total_tokens"], 1)
        self.assertEqual(stats_a["active_tokens"], 1)
        self.assertEqual(stats_a["permission_distribution"]["Dashboard"], 1)
        self.assertEqual(stats_a["permission_distribution"]["Reports"], 1)
        self.assertEqual(stats_a["permission_distribution"]["Analytics"], 0)

        # Fetch stats for Employee B
        stats_b = get_jit_dashboard_stats(employee_id="EMP-B", db=self.db)
        self.assertEqual(stats_b["total_tokens"], 1)
        self.assertEqual(stats_b["active_tokens"], 1)
        self.assertEqual(stats_b["permission_distribution"]["Dashboard"], 1)
        self.assertEqual(stats_b["permission_distribution"]["Analytics"], 1)

if __name__ == "__main__":
    unittest.main()
