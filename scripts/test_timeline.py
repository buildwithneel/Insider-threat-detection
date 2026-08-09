import os
import sys

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_client import get_db
from backend.timeline import get_employee_timeline

def main():
    db = get_db()
    
    # Test Employee: EMP055 (Impossible Travel exfiltration scenario)
    emp_id = "EMP055"
    employee = db.employees.find_one({"employee_id": emp_id})
    if not employee:
        print(f"Error: Employee {emp_id} not found.")
        sys.exit(1)
        
    print(f"Analyzing Timeline for: {employee['full_name']} ({emp_id})")
    print(f"Current Trust Score: {employee['current_score']}/100")
    print("-" * 80)
    
    timeline = get_employee_timeline(db, emp_id)
    
    anomalies_count = 0
    routine_collapsed_count = 0
    
    for entry in timeline:
        tag = "[ANOMALY]" if entry["is_anomaly"] else "[ROUTINE]"
        severity = f"| Severity: {entry['severity']:8}"
        collapsed = f"| Collapsed ({entry['count']} logs)" if entry["collapsed"] else ""
        
        print(f"{entry['timestamp']} {tag} {severity} | {entry['description']} {collapsed}")
        
        if entry["is_anomaly"]:
            anomalies_count += 1
        elif entry["collapsed"]:
            routine_collapsed_count += entry["count"]
            
    print("-" * 80)
    print(f"Timeline Summary: Total events processed: {sum([e['count'] for e in timeline])}")
    print(f"Rendered Timeline rows: {len(timeline)} (Collapsing routine logs: {routine_collapsed_count} events saved space)")
    print(f"Total Anomalous Actions Highlighted: {anomalies_count}")

if __name__ == "__main__":
    main()
