import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_client import get_db
from backend.trust_score import recalculate_score, SEVERITY_WEIGHTS
from backend.app import app

def run_verification():
    app.config["TESTING"] = True
    client = app.test_client()
    db = get_db()
    
    emp_id = "CEL0561"
    
    print("=== 1. CHECK SEVERITY WEIGHTS CONFIG ===")
    print("Configured SEVERITY_WEIGHTS:", SEVERITY_WEIGHTS)
    
    # Reset employee events and calculate initial baseline
    db.events.delete_many({"employee_id": emp_id, "event_id": {"$regex": "^SIM-"}})
    initial_baseline = recalculate_score(db, emp_id)
    print(f"\nInitial baseline Trust Score for {emp_id}: {initial_baseline}")
    
    scenarios = [
        ("usb_theft", "Critical", 30.0),
        ("mass_download", "High", 20.0),
        ("impossible_travel", "Critical", 30.0),
        ("privilege_escalation", "High", 20.0)
    ]
    
    print("\n=== 2. TESTING ATTACK SIMULATION SCENARIOS ===")
    for scenario, expected_sev, expected_weight in scenarios:
        # Reset SIM events to test each scenario independently
        db.events.delete_many({"employee_id": emp_id, "event_id": {"$regex": "^SIM-"}})
        recalculate_score(db, emp_id)
        
        start_score = db.employees.find_one({"employee_id": emp_id})["current_score"]
        
        res = client.post("/api/simulate", json={
            "scenario": scenario,
            "employee_id": emp_id
        })
        data = res.get_json()
        
        score_after = data.get("new_score")
        diff = round(start_score - score_after, 2)
        
        print(f"Scenario: {scenario:<20} | Severity: {data.get('threat_severity'):<8} | Weight Applied: -{data.get('weight_applied')} pts | Score Before: {start_score} | Score After: {score_after} (Diff: -{diff} pts)")
        
        assert score_after > 0, f"FAIL: Score for {scenario} dropped to 0!"
        assert data.get("threat_severity") == expected_sev, f"FAIL: Unexpected severity for {scenario}"
        assert data.get("weight_applied") == expected_weight, f"FAIL: Unexpected weight applied for {scenario}"
        
    print("\n=== VERIFICATION SUCCESSFUL: All simulations reduced score appropriately without dropping to 0! ===")

if __name__ == "__main__":
    run_verification()
