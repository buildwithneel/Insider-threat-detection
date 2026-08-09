"""
SentinelAI - Generate Human-Machine Identity Telemetry Dataset
===============================================================

Generates a standalone dataset 'dataset/human_machine_identity_telemetry.csv'
containing behavioral telemetry vector samples for Human vs Automated Script vs Bot vs
AI Agent vs Compromised Session detection.

DOES NOT alter any existing dataset files.
"""

import os
import csv
import random
import uuid
from datetime import datetime, timedelta

DATASET_DIR = "dataset"
OUTPUT_FILE = os.path.join(DATASET_DIR, "human_machine_identity_telemetry.csv")
EMPLOYEES_FILE = os.path.join(DATASET_DIR, "employees.csv")

START_DATE = datetime(2026, 4, 13, 8, 0, 0)
DAYS = 90

# Telemetry archetype configurations
PROFILES = {
    "Human": {
        "label": "Human",
        "weight": 0.82,
        "human_conf_range": (88.0, 98.0),
        "machine_conf_range": (2.0, 12.0),
        "bot_prob_range": (1.0, 8.0),
        "consistency_range": (85.0, 98.0),
        "typing_wpm": (55, 95),
        "hold_time_ms": (80, 140),
        "typing_variance": (18.0, 35.0),
        "robotic_cadence": False,
        "mouse_path_types": ["Bezier Curve", "Organic Arc", "Natural Curve"],
        "micro_jitters": (12, 35),
        "straight_line_ratio": (0.02, 0.15),
        "cursor_avg_speed": (0.8, 2.5),
        "flight_time_stdev": (25.0, 55.0),
        "fixed_latency": False,
        "click_avg_ms": (250, 450),
        "click_integer_flag": False,
        "api_req_sec": (0.5, 3.0),
        "api_periodic": False,
        "powershell_per_min": (0, 1),
        "powershell_headless": False,
        "browser_headless": False,
        "browser_webdriver": False,
        "browser_synthetic": False,
        "uninterrupted_hours": (1.0, 4.5),
        "after_hours": False,
        "request_pattern": "Navigational Flow",
        "batch_payload": False,
        "idle_pause_sec": (8.0, 25.0),
        "idle_zero_min": 0,
        "signatures": []
    },
    "Automated Script": {
        "label": "Automated Script",
        "weight": 0.05,
        "human_conf_range": (8.0, 25.0),
        "machine_conf_range": (75.0, 92.0),
        "bot_prob_range": (80.0, 95.0),
        "consistency_range": (15.0, 35.0),
        "typing_wpm": (350, 500),
        "hold_time_ms": (0, 2),
        "typing_variance": (0.0, 0.5),
        "robotic_cadence": True,
        "mouse_path_types": ["None (Disembodied)", "Disembodied Input"],
        "micro_jitters": (0, 1),
        "straight_line_ratio": (0.95, 1.0),
        "cursor_avg_speed": (0.0, 0.1),
        "flight_time_stdev": (0.1, 0.5),
        "fixed_latency": True,
        "click_avg_ms": (2, 8),
        "click_integer_flag": True,
        "api_req_sec": (25.0, 50.0),
        "api_periodic": True,
        "powershell_per_min": (8, 20),
        "powershell_headless": True,
        "browser_headless": True,
        "browser_webdriver": True,
        "browser_synthetic": True,
        "uninterrupted_hours": (10.0, 24.0),
        "after_hours": True,
        "request_pattern": "Programmatic Batch Payload",
        "batch_payload": True,
        "idle_pause_sec": (0.0, 0.1),
        "idle_zero_min": 120,
        "signatures": ["Python-requests/2.31.0", "PyAutoGUI synthetic input"]
    },
    "Bot": {
        "label": "Bot",
        "weight": 0.05,
        "human_conf_range": (5.0, 18.0),
        "machine_conf_range": (82.0, 95.0),
        "bot_prob_range": (85.0, 98.0),
        "consistency_range": (10.0, 25.0),
        "typing_wpm": (280, 420),
        "hold_time_ms": (1, 5),
        "typing_variance": (0.1, 1.0),
        "robotic_cadence": True,
        "mouse_path_types": ["Linear Point-to-Point", "Quantized Vector"],
        "micro_jitters": (0, 2),
        "straight_line_ratio": (0.90, 0.99),
        "cursor_avg_speed": (18.0, 35.0),
        "flight_time_stdev": (0.5, 2.0),
        "fixed_latency": True,
        "click_avg_ms": (10, 25),
        "click_integer_flag": True,
        "api_req_sec": (18.0, 40.0),
        "api_periodic": True,
        "powershell_per_min": (4, 12),
        "powershell_headless": True,
        "browser_headless": True,
        "browser_webdriver": True,
        "browser_synthetic": True,
        "uninterrupted_hours": (8.0, 18.0),
        "after_hours": True,
        "request_pattern": "Automated DOM Scraping",
        "batch_payload": True,
        "idle_pause_sec": (0.0, 0.2),
        "idle_zero_min": 90,
        "signatures": ["HeadlessChrome/124.0.0", "navigator.webdriver = true", "Puppeteer Stealth"]
    },
    "AI Agent": {
        "label": "AI Agent",
        "weight": 0.04,
        "human_conf_range": (20.0, 40.0),
        "machine_conf_range": (60.0, 80.0),
        "bot_prob_range": (65.0, 82.0),
        "consistency_range": (35.0, 55.0),
        "typing_wpm": (140, 220),
        "hold_time_ms": (10, 25),
        "typing_variance": (1.5, 4.0),
        "robotic_cadence": True,
        "mouse_path_types": ["Simulated Bezier (Quantized)", "Quantized Curve"],
        "micro_jitters": (2, 6),
        "straight_line_ratio": (0.35, 0.60),
        "cursor_avg_speed": (4.5, 9.0),
        "flight_time_stdev": (3.0, 8.0),
        "fixed_latency": False,
        "click_avg_ms": (120, 180),
        "click_integer_flag": True,
        "api_req_sec": (6.0, 12.0),
        "api_periodic": False,
        "powershell_per_min": (12, 24),
        "powershell_headless": True,
        "browser_headless": False,
        "browser_webdriver": True,
        "browser_synthetic": True,
        "uninterrupted_hours": (5.0, 10.0),
        "after_hours": True,
        "request_pattern": "AI Agent Step Loops",
        "batch_payload": False,
        "idle_pause_sec": (1.5, 3.5),
        "idle_zero_min": 45,
        "signatures": ["LangChain Shell Executor", "OpenAI Tool Agent Header"]
    },
    "Compromised Session": {
        "label": "Compromised Session",
        "weight": 0.04,
        "human_conf_range": (40.0, 55.0),
        "machine_conf_range": (45.0, 60.0),
        "bot_prob_range": (50.0, 68.0),
        "consistency_range": (35.0, 50.0),
        "typing_wpm": (110, 160),
        "hold_time_ms": (35, 60),
        "typing_variance": (4.0, 9.0),
        "robotic_cadence": False,
        "mouse_path_types": ["Erratic Jumps", "Abrupt Linear Shifts"],
        "micro_jitters": (35, 60),
        "straight_line_ratio": (0.55, 0.75),
        "cursor_avg_speed": (10.0, 18.0),
        "flight_time_stdev": (8.0, 16.0),
        "fixed_latency": False,
        "click_avg_ms": (80, 130),
        "click_integer_flag": False,
        "api_req_sec": (4.0, 9.0),
        "api_periodic": False,
        "powershell_per_min": (6, 15),
        "powershell_headless": False,
        "browser_headless": False,
        "browser_webdriver": False,
        "browser_synthetic": False,
        "uninterrupted_hours": (7.0, 14.0),
        "after_hours": True,
        "request_pattern": "Rapid Privilege Query",
        "batch_payload": False,
        "idle_pause_sec": (0.8, 2.0),
        "idle_zero_min": 20,
        "signatures": ["Session Token IP Mismatch", "Unusual PowerShell Invocation"]
    }
}


def load_employee_ids():
    """Reads employee IDs from existing dataset/employees.csv without modifying it."""
    emp_ids = []
    if os.path.exists(EMPLOYEES_FILE):
        with open(EMPLOYEES_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = row.get("employee_id") or row.get("user_id")
                if uid:
                    emp_ids.append(uid)

    if not emp_ids:
        emp_ids = [f"EMP{i:03d}" for i in range(1, 151)]

    return emp_ids


def generate_dataset():
    os.makedirs(DATASET_DIR, exist_ok=True)
    emp_ids = load_employee_ids()

    print(f"Generating Human-Machine Identity Telemetry dataset for {len(emp_ids)} employees...")

    fieldnames = [
        "record_id", "employee_id", "timestamp", "session_id", "identity_label",
        "human_confidence_pct", "machine_confidence_pct", "bot_probability_pct",
        "behaviour_consistency_pct", "overall_identity_score", "typing_wpm",
        "typing_hold_time_ms", "typing_variance", "robotic_cadence", "mouse_path_type",
        "mouse_micro_jitters", "mouse_straight_line_ratio", "cursor_avg_speed_px_ms",
        "keyboard_flight_time_stdev", "keyboard_fixed_latency", "click_avg_interval_ms",
        "click_integer_delay_flag", "api_requests_per_sec", "api_is_periodic",
        "powershell_execs_per_min", "powershell_headless_cli", "browser_headless",
        "browser_webdriver_flag", "browser_synthetic_clicks", "session_uninterrupted_hours",
        "session_after_hours", "request_pattern_type", "request_batch_payload",
        "idle_avg_pause_sec", "idle_zero_duration_min", "automation_signatures"
    ]

    records = []
    record_counter = 1

    profile_keys = list(PROFILES.keys())
    weights = [PROFILES[k]["weight"] for k in profile_keys]

    for day in range(DAYS):
        current_date = START_DATE + timedelta(days=day)

        # Select a sample of employees active each day
        active_emps = random.sample(emp_ids, min(len(emp_ids), random.randint(25, 45)))

        for emp_id in active_emps:
            # Pick profile according to weights
            p_key = random.choices(profile_keys, weights=weights, k=1)[0]
            prof = PROFILES[p_key]

            # Generate timestamps
            hour = random.randint(18, 23) if prof["after_hours"] else random.randint(8, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            ts = current_date.replace(hour=hour, minute=minute, second=second)

            h_conf = round(random.uniform(*prof["human_conf_range"]), 1)
            m_conf = round(100.0 - h_conf, 1)
            b_prob = round(random.uniform(*prof["bot_prob_range"]), 1)
            b_cons = round(random.uniform(*prof["consistency_range"]), 1)
            o_score = round((h_conf * 0.6) + (b_cons * 0.4), 1)

            wpm = random.randint(*prof["typing_wpm"])
            hold_ms = random.randint(*prof["hold_time_ms"])
            typ_var = round(random.uniform(*prof["typing_variance"]), 1)

            mouse_path = random.choice(prof["mouse_path_types"])
            jitters = random.randint(*prof["micro_jitters"])
            sl_ratio = round(random.uniform(*prof["straight_line_ratio"]), 2)
            c_speed = round(random.uniform(*prof["cursor_avg_speed"]), 1)

            flight_stdev = round(random.uniform(*prof["flight_time_stdev"]), 1)
            click_ms = random.randint(*prof["click_avg_ms"])

            api_sec = round(random.uniform(*prof["api_req_sec"]), 1)
            ps_min = random.randint(*prof["powershell_per_min"])
            session_hrs = round(random.uniform(*prof["uninterrupted_hours"]), 1)
            idle_pause = round(random.uniform(*prof["idle_pause_sec"]), 1)

            sigs = "; ".join(prof["signatures"])

            rec = {
                "record_id": f"ID-REC-{record_counter:06d}",
                "employee_id": emp_id,
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "session_id": f"SESS-{uuid.uuid4().hex[:8].upper()}",
                "identity_label": prof["label"],
                "human_confidence_pct": h_conf,
                "machine_confidence_pct": m_conf,
                "bot_probability_pct": b_prob,
                "behaviour_consistency_pct": b_cons,
                "overall_identity_score": o_score,
                "typing_wpm": wpm,
                "typing_hold_time_ms": hold_ms,
                "typing_variance": typ_var,
                "robotic_cadence": prof["robotic_cadence"],
                "mouse_path_type": mouse_path,
                "mouse_micro_jitters": jitters,
                "mouse_straight_line_ratio": sl_ratio,
                "cursor_avg_speed_px_ms": c_speed,
                "keyboard_flight_time_stdev": flight_stdev,
                "keyboard_fixed_latency": prof["fixed_latency"],
                "click_avg_interval_ms": click_ms,
                "click_integer_delay_flag": prof["click_integer_flag"],
                "api_requests_per_sec": api_sec,
                "api_is_periodic": prof["api_periodic"],
                "powershell_execs_per_min": ps_min,
                "powershell_headless_cli": prof["powershell_headless"],
                "browser_headless": prof["browser_headless"],
                "browser_webdriver_flag": prof["browser_webdriver"],
                "browser_synthetic_clicks": prof["browser_synthetic"],
                "session_uninterrupted_hours": session_hrs,
                "session_after_hours": prof["after_hours"],
                "request_pattern_type": prof["request_pattern"],
                "request_batch_payload": prof["batch_payload"],
                "idle_avg_pause_sec": idle_pause,
                "idle_zero_duration_min": prof["idle_zero_min"],
                "automation_signatures": sigs
            }

            records.append(rec)
            record_counter += 1

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully generated {len(records)} records in '{OUTPUT_FILE}'.")
    return OUTPUT_FILE

if __name__ == "__main__":
    generate_dataset()
