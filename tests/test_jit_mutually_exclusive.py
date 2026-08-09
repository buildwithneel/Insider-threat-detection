import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.app import app
from backend.database.jit_db import create_jit_token, get_jit_audit_logs

class TestJitMutuallyExclusive(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.db = get_db()
        cls.test_emp_id = "EMP_JIT_MUTUAL_EXCL_TEST"
        cls.db.jit_tokens.delete_many({"employee_id": cls.test_emp_id})
        cls.db.jit_audit_logs.delete_many({"employee.id": cls.test_emp_id})

    @classmethod
    def tearDownClass(cls):
        cls.db.jit_tokens.delete_many({"employee_id": cls.test_emp_id})
        cls.db.jit_audit_logs.delete_many({"employee.id": cls.test_emp_id})

    def test_01_backend_rejection_of_dual_access_levels(self):
        """Verify API rejects requests containing both Limited Access and Full Access with exact error message."""
        payload = {
            "employee_id": self.test_emp_id,
            "employee_name": "Test Employee",
            "access_type": ["Limited Access", "Full Access"],
            "granted_permissions": ["Dashboard"]
        }
        res = self.client.post("/api/jit/tokens/issue", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(
            data.get("error"),
            "Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously."
        )

    def test_02_backend_rejection_of_dual_permissions(self):
        """Verify API rejects requests with granted_permissions specifying both LIMITED and FULL."""
        payload = {
            "employee_id": self.test_emp_id,
            "employee_name": "Test Employee",
            "access_type": "Limited Access",
            "granted_permissions": ["LIMITED", "FULL"]
        }
        res = self.client.post("/api/jit/tokens/issue", json=payload)
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertEqual(
            data.get("error"),
            "Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously."
        )

    def test_03_single_access_level_storage_limited(self):
        """Verify Limited Access token creation stores single string accessLevel 'LIMITED'."""
        token_doc, plain_token = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Test Employee",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Limited Access",
            granted_permissions=["Dashboard", "AI Investigation"],
            duration_minutes=30,
            db=self.db
        )
        self.assertEqual(token_doc["accessLevel"], "LIMITED")
        self.assertIsInstance(token_doc["accessLevel"], str)
        self.assertNotIsInstance(token_doc["accessLevel"], list)

        # Check raw DB document
        raw = self.db.jit_tokens.find_one({"token_id": token_doc["token_id"]})
        self.assertEqual(raw["accessLevel"], "LIMITED")
        self.assertNotEqual(raw["accessLevel"], ["LIMITED", "FULL"])

    def test_04_permission_assignment_and_conflict_revocation(self):
        """Verify switching access level from LIMITED to FULL revokes prior conflicting active token."""
        # 1. Issue LIMITED token
        doc1, tok1 = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Test Employee",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Limited Access",
            granted_permissions=["Dashboard"],
            duration_minutes=30,
            db=self.db
        )
        self.assertEqual(doc1["status"], "Active")

        # 2. Issue FULL token for same employee -> should revoke prior LIMITED token
        doc2, tok2 = create_jit_token(
            employee_id=self.test_emp_id,
            employee_name="Test Employee",
            department="SOC",
            admin_id="GAR-0001",
            admin_name="Admin",
            access_type="Full Access",
            granted_permissions=[],
            duration_minutes=60,
            db=self.db
        )
        self.assertEqual(doc2["status"], "Active")
        self.assertEqual(doc2["accessLevel"], "FULL")

        # Verify doc1 is now Revoked in DB
        raw1 = self.db.jit_tokens.find_one({"token_id": doc1["token_id"]})
        self.assertEqual(raw1["status"], "Revoked")

    def test_05_audit_log_single_access_level(self):
        """Verify audit log for Token Issued records only the single selected access level."""
        logs = get_jit_audit_logs(employee_id=self.test_emp_id, db=self.db)
        issued_logs = [l for l in logs if l.get("event_type") == "Token Issued"]
        self.assertGreater(len(issued_logs), 0)
        for log in issued_logs:
            notes = log.get("notes", "")
            has_limited = "LIMITED" in notes
            has_full = "FULL" in notes
            # A single issuance log must not claim both LIMITED and FULL as granted
            self.assertFalse(has_limited and has_full, f"Audit log notes contain both access levels: '{notes}'")

if __name__ == "__main__":
    unittest.main()
