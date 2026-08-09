import os
import sys

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_client import get_db
from backend.ai_assistant import generate_ai_explanation

def main():
    db = get_db()
    
    # Query one active alert from DB
    alert = db.alerts.find_one({"employee_id": "EMP055"})
    if not alert:
        print("Error: No alerts found for EMP055 in database. Please run the import pipeline first.")
        sys.exit(1)
        
    alert_id = alert["alert_id"]
    print(f"Triggering AI Investigation for Alert ID: {alert_id}")
    print(f"Target Employee: {alert['employee_id']} | Type: {alert['type']}")
    print("-" * 80)
    
    # Generate explanation (caches it internally)
    explanation = generate_ai_explanation(db, alert_id)
    
    print(explanation)
    print("-" * 80)
    
    # Verify database caching
    refreshed_alert = db.alerts.find_one({"alert_id": alert_id})
    cached_exp = refreshed_alert.get("ai_explanation")
    
    if cached_exp:
        print("SUCCESS: Incident analysis generated and cached in database successfully.")
        print(f"Cache Length: {len(cached_exp)} chars")
    else:
        print("WARNING: Caching verification failed. Explanation was not persisted.")

if __name__ == "__main__":
    main()
