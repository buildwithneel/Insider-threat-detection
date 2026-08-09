"""
SentinelAI - Import Human-Machine Identity Telemetry Dataset
=============================================================

Imports 'dataset/human_machine_identity_telemetry.csv' into MongoDB / MockDB
collections 'identity_telemetry' and creates pre-computed 'identity_records' snapshots.
"""

import os
import csv
import sys
from datetime import datetime

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from backend.db_client import get_db
    from backend.identity_monitoring import parse_ts
except ImportError:
    from db_client import get_db
    from identity_monitoring import parse_ts

MONGODB_URI = "mongodb://localhost:27017/garudaai"
if os.path.exists(".env"):
    with open(".env", "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                if key.strip() == "MONGODB_URI":
                    MONGODB_URI = val.strip().strip('"').strip("'")

db = get_db(MONGODB_URI)

def parse_bool(val):
    if not val:
        return False
    return str(val).strip().lower() in ("true", "1", "yes")

def parse_float(val):
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0

def parse_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0

def import_identity_telemetry():
    csv_path = "dataset/human_machine_identity_telemetry.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found. Run 'python scripts/generate_identity_dataset.py' first.")
        return 0

    print(f"Importing identity telemetry dataset from {csv_path}...")

    # Clear existing identity_telemetry collection
    db.identity_telemetry.delete_many({})
    
    records_by_emp = {}
    count = 0

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        docs = []
        for row in reader:
            emp_id = row["employee_id"]
            rec_id = row["record_id"]
            ts_str = row["timestamp"]
            ts = parse_ts(ts_str)

            h_conf = parse_float(row["human_confidence_pct"])
            m_conf = parse_float(row["machine_confidence_pct"])
            b_prob = parse_float(row["bot_probability_pct"])
            b_cons = parse_float(row["behaviour_consistency_pct"])
            o_score = parse_float(row["overall_identity_score"])
            label = row["identity_label"]

            sigs = [s.strip() for s in row.get("automation_signatures", "").split(";") if s.strip()]

            doc = {
                "record_id": rec_id,
                "employee_id": emp_id,
                "timestamp": ts_str,
                "session_id": row["session_id"],
                "identity_label": label,
                "scores": {
                    "human_confidence": h_conf,
                    "machine_confidence": m_conf,
                    "bot_probability": b_prob,
                    "behaviour_consistency": b_cons,
                    "overall_identity_score": o_score,
                    "status": "Verified Human" if h_conf >= 75.0 else "Suspicious Behaviour" if h_conf >= 45.0 else "Automation Detected",
                    "decision": "Normal Behaviour" if h_conf >= 75.0 else "Suspicious - Trigger Sandbox & Reduce Trust" if h_conf >= 45.0 else "High Risk - Trigger Employee Lock & Generate Alert"
                },
                "telemetry": {
                    "typing_behaviour": {
                        "wpm": parse_int(row["typing_wpm"]),
                        "hold_time_ms": parse_int(row["typing_hold_time_ms"]),
                        "variance": parse_float(row["typing_variance"]),
                        "robotic_cadence": parse_bool(row["robotic_cadence"])
                    },
                    "mouse_movement": {
                        "path_type": row["mouse_path_type"],
                        "micro_jitters": parse_int(row["mouse_micro_jitters"]),
                        "straight_line_ratio": parse_float(row["mouse_straight_line_ratio"])
                    },
                    "cursor_speed": {
                        "avg_px_ms": parse_float(row["cursor_avg_speed_px_ms"]),
                        "max_burst_px": round(parse_float(row["cursor_avg_speed_px_ms"]) * 3.5, 1),
                        "acceleration_curve": "Zero Inertia" if parse_bool(row["robotic_cadence"]) else "Organic"
                    },
                    "keyboard_rhythm": {
                        "flight_time_stdev": parse_float(row["keyboard_flight_time_stdev"]),
                        "burst_typing": not parse_bool(row["keyboard_fixed_latency"]),
                        "fixed_latency": parse_bool(row["keyboard_fixed_latency"])
                    },
                    "click_interval": {
                        "avg_ms": parse_int(row["click_avg_interval_ms"]),
                        "min_ms": max(1, int(parse_int(row["click_avg_interval_ms"]) * 0.3)),
                        "integer_delay_flag": parse_bool(row["click_integer_delay_flag"])
                    },
                    "api_frequency": {
                        "requests_per_sec": parse_float(row["api_requests_per_sec"]),
                        "max_burst": int(parse_float(row["api_requests_per_sec"]) * 3),
                        "is_periodic": parse_bool(row["api_is_periodic"])
                    },
                    "powershell_frequency": {
                        "execs_per_min": parse_int(row["powershell_execs_per_min"]),
                        "headless_cli": parse_bool(row["powershell_headless_cli"])
                    },
                    "browser_behaviour": {
                        "headless": parse_bool(row["browser_headless"]),
                        "webdriver_flag": parse_bool(row["browser_webdriver_flag"]),
                        "synthetic_clicks": parse_bool(row["browser_synthetic_clicks"])
                    },
                    "session_timing": {
                        "uninterrupted_hours": parse_float(row["session_uninterrupted_hours"]),
                        "after_hours": parse_bool(row["session_after_hours"])
                    },
                    "request_pattern": {
                        "type": row["request_pattern_type"],
                        "batch_payload": parse_bool(row["request_batch_payload"])
                    },
                    "idle_time": {
                        "avg_pause_sec": parse_float(row["idle_avg_pause_sec"]),
                        "zero_idle_duration_min": parse_int(row["idle_zero_duration_min"])
                    },
                    "automation_indicators": {
                        "signatures_detected": sigs
                    }
                }
            }

            docs.append(doc)
            count += 1

            if emp_id not in records_by_emp:
                records_by_emp[emp_id] = []
            records_by_emp[emp_id].append(doc)

    if docs:
        db.identity_telemetry.insert_many(docs)

    # Build active identity_records for each employee from dataset
    print("Building active identity snapshots for employees...")
    for emp_id, emp_docs in records_by_emp.items():
        emp = db.employees.find_one({"employee_id": emp_id}) or {}
        # Sort chronologically
        emp_docs.sort(key=lambda x: x["timestamp"])
        latest = emp_docs[-1]

        # Time-series history graph points from dataset
        history = []
        for d in emp_docs[-15:]:
            ts_obj = parse_ts(d["timestamp"])
            history.append({
                "time": ts_obj.strftime("%H:%M") if isinstance(ts_obj, datetime) else str(d["timestamp"])[:5],
                "timestamp": d["timestamp"],
                "human_confidence": d["scores"]["human_confidence"],
                "machine_confidence": d["scores"]["machine_confidence"],
                "bot_probability": d["scores"]["bot_probability"]
            })

        db.identity_records.update_one(
            {"employee_id": emp_id},
            {"$set": {
                "employee_id": emp_id,
                "full_name": emp.get("full_name", f"Employee {emp_id}"),
                "telemetry": latest["telemetry"],
                "scores": latest["scores"],
                "history": history,
                "source_dataset": "dataset/human_machine_identity_telemetry.csv",
                "updated_at": latest["timestamp"]
            }},
            upsert=True
        )

    print(f"Successfully imported {count} dataset records across {len(records_by_emp)} employees.")
    return count

if __name__ == "__main__":
    import_identity_telemetry()
