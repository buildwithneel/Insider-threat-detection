"""
Unit Test Suite for SentinelAI Virtual Sandbox Engine
=====================================================
"""

import sys
import os
import unittest
from datetime import datetime

# Ensure root directory is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.db_client import get_db
from backend.sandbox import (
    is_high_risk_action,
    perform_sandbox_analysis,
    execute_sandbox_workflow,
    get_sandbox_history,
    HIGH_RISK_TRIGGER_CATEGORIES,
    PRESET_SANDBOX_COMMANDS
)

class TestSandboxEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = get_db()
        cls.employee_id = "EMP-TEST-SBX"

        # Cleanup existing test records
        cls.db.employees.delete_many({"employee_id": cls.employee_id})
        cls.db.events.delete_many({"employee_id": cls.employee_id})
        cls.db.alerts.delete_many({"employee_id": cls.employee_id})
        cls.db.sandbox_runs.delete_many({"employee_id": cls.employee_id})

        # Seed mock employee
        cls.db.employees.insert_one({
            "employee_id": cls.employee_id,
            "full_name": "Test Security User",
            "department": "Engineering",
            "role": "Software Developer",
            "current_score": 100.0,
            "account_locked": False
        })

    @classmethod
    def tearDownClass(cls):
        cls.db.employees.delete_many({"employee_id": cls.employee_id})
        cls.db.events.delete_many({"employee_id": cls.employee_id})
        cls.db.alerts.delete_many({"employee_id": cls.employee_id})
        cls.db.sandbox_runs.delete_many({"employee_id": cls.employee_id})

    def test_01_high_risk_triggers(self):
        """Verify high-risk category detection for all 10 triggers."""
        self.assertTrue(is_high_risk_action("Opening executable files"))
        self.assertTrue(is_high_risk_action("USB insertion"))
        self.assertTrue(is_high_risk_action("File deletion"))
        self.assertTrue(is_high_risk_action("Privilege escalation"))
        self.assertTrue(is_high_risk_action("Registry modification"))
        self.assertTrue(is_high_risk_action("PowerShell execution"))
        self.assertTrue(is_high_risk_action("Bulk file copy"))
        self.assertTrue(is_high_risk_action("Database export"))
        self.assertTrue(is_high_risk_action("Unknown executable"))
        self.assertTrue(is_high_risk_action("Mass downloads"))

    def test_02_verdict_evaluations(self):
        """Test sandbox 8-check analysis for Safe, Suspicious, and Malicious commands."""
        # Safe command
        safe_analysis = perform_sandbox_analysis("Opening executable files", "git pull origin main")
        self.assertEqual(safe_analysis["verdict"], "SAFE")
        self.assertLess(safe_analysis["risk_score"], 40)

        # Suspicious command
        susp_analysis = perform_sandbox_analysis("Database export", "mysqldump -u root -p raw_data.sql")
        self.assertEqual(susp_analysis["verdict"], "SUSPICIOUS")
        self.assertTrue(40 <= susp_analysis["risk_score"] < 70)

        # Malicious command
        mal_analysis = perform_sandbox_analysis("PowerShell execution", "powershell.exe -ExecutionPolicy Bypass -EncodedCommand SQBFA...")
        self.assertEqual(mal_analysis["verdict"], "MALICIOUS")
        self.assertGreaterEqual(mal_analysis["risk_score"], 70)

    def test_03_workflow_safe_verdict(self):
        """SAFE verdict workflow test."""
        report = execute_sandbox_workflow(
            db=self.db,
            employee_id=self.employee_id,
            action_type="Opening executable files",
            command_name="git pull && npm run build"
        )
        self.assertEqual(report["verdict"], "SAFE")
        self.assertEqual(report["display_status"], "Sandbox Passed")

        # Check timeline event created
        event = self.db.events.find_one({"employee_id": self.employee_id, "type": "sandbox"})
        self.assertIsNotNone(event)
        self.assertEqual(event["details"]["sandbox_verdict"], "SAFE")

    def test_04_workflow_suspicious_verdict(self):
        """SUSPICIOUS verdict workflow test."""
        report = execute_sandbox_workflow(
            db=self.db,
            employee_id=self.employee_id,
            action_type="Database export",
            command_name="mysqldump -u root -p customer_ledgers.sql"
        )
        self.assertEqual(report["verdict"], "SUSPICIOUS")
        self.assertEqual(report["display_status"], "Under Observation")
        self.assertLess(report["score_after"], 100.0)

    def test_05_workflow_malicious_verdict_and_employee_lock(self):
        """MALICIOUS verdict workflow test with security alert & employee lock."""
        # Seed events to bring employee trust score down near threshold before malicious sandbox action
        self.db.events.delete_many({"employee_id": self.employee_id})
        self.db.events.insert_one({
            "event_id": "TEST-PRE-LOCK-1",
            "employee_id": self.employee_id,
            "timestamp": datetime.now(),
            "type": "automation_detected",
            "details": {}
        })
        self.db.events.insert_one({
            "event_id": "TEST-PRE-LOCK-2",
            "employee_id": self.employee_id,
            "timestamp": datetime.now(),
            "type": "automation_detected",
            "details": {}
        })

        report = execute_sandbox_workflow(
            db=self.db,
            employee_id=self.employee_id,
            action_type="PowerShell execution",
            command_name="powershell.exe -ExecutionPolicy Bypass -EncodedCommand SQBFA...",
            critical_threshold=30
        )

        self.assertEqual(report["verdict"], "MALICIOUS")
        self.assertEqual(report["display_status"], "Execution Blocked")
        self.assertEqual(report["score_after"], 10.0) # 100 - 30 - 30 - 30 = 10.0
        self.assertTrue(report["lock_triggered"])

        # Check security alert created
        alert = self.db.alerts.find_one({"employee_id": self.employee_id})
        self.assertIsNotNone(alert)
        self.assertEqual(alert["severity"], "Critical")

        # Check employee account locked in DB
        emp = self.db.employees.find_one({"employee_id": self.employee_id})
        self.assertTrue(emp["account_locked"])

if __name__ == "__main__":
    unittest.main()
