import os
import sys
import unittest
from datetime import datetime

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.trust_score import evaluate_event_deduction, recalculate_score
from backend.app import app, limiter

class TestGarudaAIBackend(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Configure app in testing mode
        app.config["TESTING"] = True
        app.config["RATELIMIT_ENABLED"] = False
        limiter.enabled = False
        cls.client = app.test_client()
        cls.db = get_db()

    def test_01_evaluate_event_deduction(self):
        """Test score engine point deduction evaluations."""
        # 1. Normal logon (no deductions)
        normal_logon = {
            "type": "logon",
            "details": {
                "is_after_hours": False,
                "is_known_device": True,
                "location": "New York"
            }
        }
        deductions = evaluate_event_deduction(normal_logon)
        self.assertEqual(len(deductions), 0)

        # 2. Anomalous logon (after hours + unknown device)
        bad_logon = {
            "type": "logon",
            "details": {
                "is_after_hours": True,
                "is_known_device": False,
                "location": "Beijing"
            }
        }
        deductions = evaluate_event_deduction(bad_logon)
        self.assertEqual(len(deductions), 2)
        total_deduction = sum(d[1] for d in deductions)
        self.assertEqual(total_deduction, 15.0) # 5.0 (after hours) + 10.0 (unknown)

        # 3. Restricted File Read
        restricted_file = {
            "type": "file",
            "details": {
                "file_sensitivity": "Restricted",
                "file_size_mb": 45.0,
                "action": "Read"
            }
        }
        deductions = evaluate_event_deduction(restricted_file)
        self.assertEqual(len(deductions), 1)
        self.assertEqual(deductions[0][1], 15.0) # restricted_file_access (-15)

    def test_02_recalculate_score(self):
        """Test chronological score calculation and recovery."""
        emp = self.db.employees.find_one({})
        emp_id = emp["employee_id"] if emp else "CEL0561"
        score = recalculate_score(self.db, emp_id)
        employee = self.db.employees.find_one({"employee_id": emp_id})
        
        # Verify score matches saved field
        self.assertEqual(score, employee["current_score"])

    def test_03_api_health(self):
        """Verify health check endpoint returns 200."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_04_api_get_employees(self):
        """Verify fetching employee list returns loaded dataset items."""
        res = self.client.get("/api/employees")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_05_api_get_timeline(self):
        """Verify timeline query returns 200 response."""
        emp = self.db.employees.find_one({})
        emp_id = emp["employee_id"] if emp else "CEL0561"
        res = self.client.get(f"/api/employees/{emp_id}/timeline")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)

    def test_06_api_alerts(self):
        """Verify alerts listing returns active threats."""
        res = self.client.get("/api/alerts")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIsInstance(data, list)

    def test_07_api_simulation_flow(self):
        """Verify end-to-end simulation trigger, score recalc, and alert injection."""
        emp = self.db.employees.find_one({})
        emp_id = emp["employee_id"] if emp else "CEL0561"
        
        # Trigger simulation for active dataset employee
        res = self.client.post("/api/simulate", json={
            "scenario": "mass_download",
            "employee_id": emp_id
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        
        # Verify recalculation took place
        self.assertLess(data["new_score"], 90.0)
        self.assertEqual(data["events_injected"], 30)
        
        # Verify alert was created
        alert = self.db.alerts.find_one({"alert_id": data["alert_id"]})
        self.assertIsNotNone(alert)
        self.assertEqual(alert["type"], "Mass File Download")

        # 3. Clean up simulator logs
        self.client.post("/api/reset")

    def test_08_garuda_ai_chatbot_behavior(self):
        """Verify greeting behavior and domain restrictions of Garuda AI chatbot."""
        # 1. Test Greetings
        greetings = ["Hi", "Hello", "Hey", "Good Morning", "Greetings"]
        for g in greetings:
            res = self.client.post("/api/chat", json={"message": g})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["response"], "Hi! I'm Garuda AI, your AI-powered cybersecurity and FinTech assistant. How can I help you today?")

        # 2. Test Out-of-domain queries (Rejected)
        rejected_queries = ["Recommend a good movie", "Who won the cricket match?", "What is a pizza recipe?", "Tell me about ancient history"]
        expected_reject = (
            "I'm Garuda AI, a specialized cybersecurity and FinTech assistant. "
            "I can only assist with FinTech, cybersecurity, insider threat detection, "
            "employee investigations, and features available within the Garuda AI platform. "
            "Please ask a relevant question."
        )
        for q in rejected_queries:
            res = self.client.post("/api/chat", json={"message": q})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["response"], expected_reject)

        # 3. Test Domain queries (Answered)
        domain_queries = ["What is Trust Score?", "Explain Sandbox Verification", "How does JIT Access Token work?"]
        for q in domain_queries:
            res = self.client.post("/api/chat", json={"message": q})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertIn("response", data)
            self.assertNotEqual(data["response"], expected_reject)

if __name__ == "__main__":
    unittest.main()
