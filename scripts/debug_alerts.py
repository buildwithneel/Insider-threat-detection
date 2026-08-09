import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.db_client import get_db, parse_date_robust

def main():
    db = get_db()
    
    # Raw JSON inspect
    import json
    filepath = "backend/mock_db/alerts.json"
    with open(filepath, "r") as f:
        data = json.load(f)
        
    print("--- Diagnostic Report ---")
    for doc in data:
        raw_ts = doc.get("timestamp")
        parsed_ts = parse_date_robust(raw_ts)
        print(f"Alert: {doc['alert_id']} | Raw TS: {raw_ts} (type: {type(raw_ts).__name__}) | Parsed TS: {parsed_ts} (type: {type(parsed_ts).__name__})")

if __name__ == "__main__":
    main()
