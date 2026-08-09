import os
import sys
import unittest

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.app import app

class TestJitSimulation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()
        cls.db = get_db()
        
        # Ensure a clean baseline test employee
        cls.db.employees.delete_many({"employee_id": "EMP_TEST_JIT"})
        cls.db.employees.insert_one({
            "employee_id": "EMP_TEST_JIT",
            "full_name": "JIT Test Engineer",
            "department": "Engineering",
            "role": "DevOps",
            "is_privileged_user": True,
            "current_score": 95.0
        })

    @classmethod
    def tearDownClass(cls):
        cls.db.employees.delete_many({"employee_id": "EMP_TEST_JIT"})
        cls.db.events.delete_many({"employee_id": "EMP_TEST_JIT"})

    def test_01_add_and_fetch_jit_events(self):
        """Test custom simulated JIT event insertion and check description mapping in timeline."""
        # 1. Post a custom warning event
        res = self.client.post("/api/employees/EMP_TEST_JIT/events", json={
            "description": "Critical Trust Threshold Reached",
            "type": "jit_sim",
            "severity": "Critical"
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["success"])

        # 2. Post a workstation lock event
        res2 = self.client.post("/api/employees/EMP_TEST_JIT/events", json={
            "description": "• Employee Workstation Locked",
            "type": "jit_sim",
            "severity": "Critical"
        })
        self.assertEqual(res2.status_code, 201)

        # 3. Retrieve timeline and assert events are correctly structured and formatted
        res_timeline = self.client.get("/api/employees/EMP_TEST_JIT/timeline")
        self.assertEqual(res_timeline.status_code, 200)
        timeline = res_timeline.get_json()
        
        # We should find both events in the chronological timeline
        descriptions = [item["description"] for item in timeline]
        self.assertIn("Critical Trust Threshold Reached", descriptions)
        self.assertIn("• Employee Workstation Locked", descriptions)
        
        # The custom descriptions should map directly to descriptions
        lock_event = next(item for item in timeline if item["description"] == "• Employee Workstation Locked")
        self.assertEqual(lock_event["severity"], "Critical")
        self.assertEqual(lock_event["type"], "jit_sim")

if __name__ == "__main__":
    unittest.main()
