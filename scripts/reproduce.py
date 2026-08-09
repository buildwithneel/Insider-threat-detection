import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app import app

def main():
    app.config["TESTING"] = True
    client = app.test_client()
    
    print("--- 1. Resetting database ---")
    client.post("/api/reset")
    
    print("--- 2. Triggering simulation 1 (usb_theft for EMP032) ---")
    client.post("/api/simulate", json={
        "scenario": "usb_theft",
        "employee_id": "EMP032"
    })
    
    print("--- 3. Triggering simulation 2 (impossible_travel for EMP015) ---")
    client.post("/api/simulate", json={
        "scenario": "impossible_travel",
        "employee_id": "EMP015"
    })
    
    print("--- 4. Fetching /api/alerts ---")
    res = client.get("/api/alerts")
    print(f"Status Code: {res.status_code}")
    print(res.get_json())

if __name__ == "__main__":
    main()
