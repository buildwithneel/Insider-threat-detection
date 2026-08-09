import os
import sys

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_client import get_db
from backend.trust_score import run_score_engine_all_users

def main():
    db = get_db()
    
    print("Recalculating all behavior trust scores...")
    run_score_engine_all_users(db)
    
    print("\n--- Validation Report against Ground Truth Labels ---")
    
    # Query ground truth labels
    ground_truth = list(db.employees.find({}, {"_id": 0}))
    
    threat_scores = []
    normal_scores = []
    
    # Load ground truth threats from dataset file to verify against current scores
    threat_ids = {}
    with open("dataset/ground_truth_labels.csv", mode="r", encoding="utf-8") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            if row["is_insider_threat"].lower() in ("true", "1", "yes"):
                threat_ids[row["employee_id"]] = {
                    "pattern": row["threat_pattern"],
                    "notes": row["notes"]
                }
                
    for emp in ground_truth:
        emp_id = emp["employee_id"]
        score = emp.get("current_score", 100.0)
        
        if emp_id in threat_ids:
            threat_scores.append((emp_id, emp["full_name"], threat_ids[emp_id]["pattern"], score))
        else:
            normal_scores.append(score)
            
    print("\n[GROUND TRUTH THREAT PROFILES]")
    for tid, name, pattern, score in threat_scores:
        print(f"Employee: {tid} | Name: {name:20} | Threat: {pattern:20} | Score: {score}")
        
    avg_normal = sum(normal_scores) / len(normal_scores) if normal_scores else 100.0
    avg_threat = sum([t[3] for t in threat_scores]) / len(threat_scores) if threat_scores else 0.0
    
    print(f"\nAverage Normal Employee Score: {avg_normal:.2f}/100")
    print(f"Average Threat Employee Score: {avg_threat:.2f}/100")
    
    # Assert that threat employees score visibly lower than normal employees
    success = avg_normal > 90.0 and avg_threat < 60.0
    if success:
        print("\nSUCCESS: Threat profiles score significantly lower than baseline employees. Trust Engine is calibrated.")
    else:
        print("\nWARNING: Verification failed. Review deductions config and recovery rates.")

if __name__ == "__main__":
    main()
