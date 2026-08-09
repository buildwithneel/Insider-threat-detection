import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app import app

def main():
    app.config["TESTING"] = True
    client = app.test_client()
    
    print("--- Fetching /api/alerts (No Reset) ---")
    res = client.get("/api/alerts")
    print(f"Status Code: {res.status_code}")
    print(res.get_json())

if __name__ == "__main__":
    main()
