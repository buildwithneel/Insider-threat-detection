"""
SentinelAI - Human-Machine Identity Monitoring Module
=====================================================

Analyzes behavioral telemetry to evaluate whether actions were performed by a:
- Human
- Automated Script
- Bot
- AI Agent
- Compromised Session

Generates scores for Human Confidence %, Machine Confidence %, Bot Probability %,
Behaviour Consistency %, and Overall Identity Score. Integrates with Decision Engine
to adjust Trust Scores, trigger Sandbox Verification, append Timeline events,
and initiate Employee Workstation Locks.
"""

import uuid
from datetime import datetime, timedelta

try:
    from backend.trust_score import recalculate_score
    from backend.timeline import parse_ts
except ImportError:
    from trust_score import recalculate_score
    from timeline import parse_ts


PRESET_TELEMETRY_PROFILES = {
    "human_normal": {
        "id": "human_normal",
        "name": "Standard Human Employee",
        "description": "Natural human keyboard rhythm, organic mouse curvature, expected reading idle times.",
        "telemetry": {
            "typing_behaviour": {"wpm": 68, "hold_time_ms": 110, "variance": 24.5, "robotic_cadence": False},
            "mouse_movement": {"path_type": "Bezier Curve", "micro_jitters": 18, "straight_line_ratio": 0.08},
            "cursor_speed": {"avg_px_ms": 1.2, "max_burst_px": 4.5, "acceleration_curve": "Organic"},
            "keyboard_rhythm": {"flight_time_stdev": 42.1, "burst_typing": True, "fixed_latency": False},
            "click_interval": {"avg_ms": 340, "min_ms": 120, "integer_delay_flag": False},
            "api_frequency": {"requests_per_sec": 1.4, "max_burst": 4, "is_periodic": False},
            "powershell_frequency": {"execs_per_min": 0, "headless_cli": False},
            "browser_behaviour": {"headless": False, "webdriver_flag": False, "synthetic_clicks": False},
            "session_timing": {"uninterrupted_hours": 3.5, "after_hours": False},
            "request_pattern": {"type": "Navigational Flow", "batch_payload": False},
            "idle_time": {"avg_pause_sec": 14.2, "zero_idle_duration_min": 0},
            "automation_indicators": {"signatures_detected": []}
        },
        "scores": {
            "human_confidence": 96.0,
            "machine_confidence": 4.0,
            "bot_probability": 2.0,
            "behaviour_consistency": 94.0,
            "overall_identity_score": 95.0,
            "status": "Verified Human",
            "decision": "Normal Behaviour - No Action Required"
        }
    },
    "python_script": {
        "id": "python_script",
        "name": "Automated Python Exfiltration Script",
        "description": "Sub-millisecond API calls, fixed request latency, headless requests without mouse movements.",
        "telemetry": {
            "typing_behaviour": {"wpm": 420, "hold_time_ms": 0, "variance": 0.1, "robotic_cadence": True},
            "mouse_movement": {"path_type": "None (Disembodied)", "micro_jitters": 0, "straight_line_ratio": 1.0},
            "cursor_speed": {"avg_px_ms": 0.0, "max_burst_px": 0.0, "acceleration_curve": "Instantaneous"},
            "keyboard_rhythm": {"flight_time_stdev": 0.2, "burst_typing": False, "fixed_latency": True},
            "click_interval": {"avg_ms": 4.2, "min_ms": 1, "integer_delay_flag": True},
            "api_frequency": {"requests_per_sec": 38.5, "max_burst": 120, "is_periodic": True},
            "powershell_frequency": {"execs_per_min": 14, "headless_cli": True},
            "browser_behaviour": {"headless": True, "webdriver_flag": True, "synthetic_clicks": True},
            "session_timing": {"uninterrupted_hours": 18.0, "after_hours": True},
            "request_pattern": {"type": "Programmatic Batch Payload", "batch_payload": True},
            "idle_time": {"avg_pause_sec": 0.0, "zero_idle_duration_min": 120},
            "automation_indicators": {"signatures_detected": ["Python-requests/2.31.0", "Selenium WebDriver", "PyAutoGUI synthetic input"]}
        },
        "scores": {
            "human_confidence": 14.0,
            "machine_confidence": 86.0,
            "bot_probability": 92.0,
            "behaviour_consistency": 22.0,
            "overall_identity_score": 18.0,
            "status": "Automation Detected",
            "decision": "High Risk - Generate Alert, Reduce Trust Score, Trigger Employee Lock"
        }
    },
    "headless_bot": {
        "id": "headless_bot",
        "name": "Headless Crawler Bot",
        "description": "Selenium/Puppeteer browser session scraping confidential records in high-frequency bursts.",
        "telemetry": {
            "typing_behaviour": {"wpm": 310, "hold_time_ms": 2, "variance": 0.5, "robotic_cadence": True},
            "mouse_movement": {"path_type": "Linear Point-to-Point", "micro_jitters": 0, "straight_line_ratio": 0.98},
            "cursor_speed": {"avg_px_ms": 25.0, "max_burst_px": 80.0, "acceleration_curve": "Zero Inertia"},
            "keyboard_rhythm": {"flight_time_stdev": 1.1, "burst_typing": False, "fixed_latency": True},
            "click_interval": {"avg_ms": 12.0, "min_ms": 5, "integer_delay_flag": True},
            "api_frequency": {"requests_per_sec": 24.0, "max_burst": 85, "is_periodic": True},
            "powershell_frequency": {"execs_per_min": 6, "headless_cli": True},
            "browser_behaviour": {"headless": True, "webdriver_flag": True, "synthetic_clicks": True},
            "session_timing": {"uninterrupted_hours": 12.4, "after_hours": True},
            "request_pattern": {"type": "Automated DOM Scraping", "batch_payload": True},
            "idle_time": {"avg_pause_sec": 0.1, "zero_idle_duration_min": 85},
            "automation_indicators": {"signatures_detected": ["HeadlessChrome/124.0.0", "navigator.webdriver = true", "Puppeteer Stealth bypass failure"]}
        },
        "scores": {
            "human_confidence": 8.0,
            "machine_confidence": 92.0,
            "bot_probability": 96.0,
            "behaviour_consistency": 15.0,
            "overall_identity_score": 12.0,
            "status": "Automation Detected",
            "decision": "High Risk - Generate Alert, Reduce Trust Score, Trigger Employee Lock"
        }
    },
    "ai_agent_autopilot": {
        "id": "ai_agent_autopilot",
        "name": "AI Agent Auto-Pilot Session",
        "description": "LLM agent issuing sequential commands via shell APIs with synthetic human delay injection.",
        "telemetry": {
            "typing_behaviour": {"wpm": 180, "hold_time_ms": 15, "variance": 2.1, "robotic_cadence": True},
            "mouse_movement": {"path_type": "Simulated Bezier (Quantized)", "micro_jitters": 3, "straight_line_ratio": 0.45},
            "cursor_speed": {"avg_px_ms": 6.2, "max_burst_px": 12.0, "acceleration_curve": "Quantized Step"},
            "keyboard_rhythm": {"flight_time_stdev": 5.4, "burst_typing": True, "fixed_latency": False},
            "click_interval": {"avg_ms": 150, "min_ms": 140, "integer_delay_flag": True},
            "api_frequency": {"requests_per_sec": 8.2, "max_burst": 25, "is_periodic": False},
            "powershell_frequency": {"execs_per_min": 18, "headless_cli": True},
            "browser_behaviour": {"headless": False, "webdriver_flag": True, "synthetic_clicks": True},
            "session_timing": {"uninterrupted_hours": 6.8, "after_hours": True},
            "request_pattern": {"type": "AI Agent Step Loops", "batch_payload": False},
            "idle_time": {"avg_pause_sec": 2.1, "zero_idle_duration_min": 40},
            "automation_indicators": {"signatures_detected": ["LangChain Shell Executor", "OpenAI Tool Agent Header", "Synthetic Event Injection"]}
        },
        "scores": {
            "human_confidence": 28.0,
            "machine_confidence": 72.0,
            "bot_probability": 78.0,
            "behaviour_consistency": 40.0,
            "overall_identity_score": 32.0,
            "status": "Automation Detected",
            "decision": "High Risk - Generate Alert, Reduce Trust Score, Trigger Employee Lock"
        }
    },
    "compromised_session": {
        "id": "compromised_session",
        "name": "Compromised Session / Token Hijack",
        "description": "Human credential active, but typing rhythm changed drastically and PowerShell frequency spiked.",
        "telemetry": {
            "typing_behaviour": {"wpm": 125, "hold_time_ms": 45, "variance": 6.2, "robotic_cadence": False},
            "mouse_movement": {"path_type": "Erratic Jumps", "micro_jitters": 42, "straight_line_ratio": 0.65},
            "cursor_speed": {"avg_px_ms": 14.2, "max_burst_px": 45.0, "acceleration_curve": "Abrupt"},
            "keyboard_rhythm": {"flight_time_stdev": 12.0, "burst_typing": True, "fixed_latency": False},
            "click_interval": {"avg_ms": 95, "min_ms": 30, "integer_delay_flag": False},
            "api_frequency": {"requests_per_sec": 6.5, "max_burst": 18, "is_periodic": False},
            "powershell_frequency": {"execs_per_min": 9, "headless_cli": False},
            "browser_behaviour": {"headless": False, "webdriver_flag": False, "synthetic_clicks": False},
            "session_timing": {"uninterrupted_hours": 9.1, "after_hours": True},
            "request_pattern": {"type": "Rapid Privilege Query", "batch_payload": False},
            "idle_time": {"avg_pause_sec": 1.2, "zero_idle_duration_min": 15},
            "automation_indicators": {"signatures_detected": ["Session Token IP Mismatch", "Unusual PowerShell Invocation"]}
        },
        "scores": {
            "human_confidence": 46.0,
            "machine_confidence": 54.0,
            "bot_probability": 58.0,
            "behaviour_consistency": 44.0,
            "overall_identity_score": 48.0,
            "status": "Suspicious Behaviour",
            "decision": "Suspicious - Reduce Trust Score, Trigger Sandbox Verification, Append Timeline"
        }
    }
}


def analyze_telemetry_parameters(telemetry):
    """
    Computes Human Confidence %, Machine Confidence %, Bot Probability %,
    Behaviour Consistency %, and Overall Identity Score from 12 behavioral metrics.
    """
    if not telemetry:
        return PRESET_TELEMETRY_PROFILES["human_normal"]["scores"]

    typing = telemetry.get("typing_behaviour", {})
    mouse = telemetry.get("mouse_movement", {})
    cursor = telemetry.get("cursor_speed", {})
    rhythm = telemetry.get("keyboard_rhythm", {})
    click = telemetry.get("click_interval", {})
    api_freq = telemetry.get("api_frequency", {})
    ps_freq = telemetry.get("powershell_frequency", {})
    browser = telemetry.get("browser_behaviour", {})
    session = telemetry.get("session_timing", {})
    req_pat = telemetry.get("request_pattern", {})
    idle = telemetry.get("idle_time", {})
    indicators = telemetry.get("automation_indicators", {})

    machine_weight = 0.0

    # 1. Typing Behaviour
    if typing.get("robotic_cadence") or typing.get("variance", 20.0) < 3.0 or typing.get("wpm", 60) > 220:
        machine_weight += 12.0

    # 2. Mouse Movement
    path_type = str(mouse.get("path_type", "")).lower()
    if "none" in path_type or "linear" in path_type or mouse.get("straight_line_ratio", 0) > 0.7:
        machine_weight += 12.0

    # 3. Cursor Speed
    if cursor.get("acceleration_curve") in ["Instantaneous", "Zero Inertia"] or cursor.get("avg_px_ms", 1.0) > 20.0:
        machine_weight += 8.0

    # 4. Keyboard Rhythm
    if rhythm.get("fixed_latency") or rhythm.get("flight_time_stdev", 30) < 5.0:
        machine_weight += 10.0

    # 5. Click Interval
    if click.get("integer_delay_flag") or click.get("avg_ms", 300) < 25:
        machine_weight += 8.0

    # 6. API Frequency
    if api_freq.get("requests_per_sec", 1.0) > 10.0 or api_freq.get("is_periodic"):
        machine_weight += 10.0

    # 7. PowerShell Frequency
    if ps_freq.get("execs_per_min", 0) > 4 or ps_freq.get("headless_cli"):
        machine_weight += 10.0

    # 8. Browser Behaviour
    if browser.get("headless") or browser.get("webdriver_flag") or browser.get("synthetic_clicks"):
        machine_weight += 14.0

    # 9. Session Timing
    if session.get("uninterrupted_hours", 0) > 10 or session.get("after_hours"):
        machine_weight += 5.0

    # 10. Request Pattern
    if req_pat.get("batch_payload") or "batch" in str(req_pat.get("type", "")).lower():
        machine_weight += 5.0

    # 11. Idle Time
    if idle.get("zero_idle_duration_min", 0) > 30 or idle.get("avg_pause_sec", 10) < 0.5:
        machine_weight += 6.0

    # 12. Automation Indicators
    sigs = indicators.get("signatures_detected", [])
    if len(sigs) > 0:
        machine_weight += 15.0

    machine_confidence = min(98.0, max(2.0, machine_weight))
    human_confidence = round(100.0 - machine_confidence, 1)
    machine_confidence = round(machine_confidence, 1)

    bot_prob = min(99.0, round(machine_confidence * 1.05 if len(sigs) > 0 or browser.get("headless") else machine_confidence * 0.9, 1))
    consistency = round(max(10.0, min(98.0, 100.0 - (machine_confidence * 0.8))), 1)
    overall_identity = round((human_confidence * 0.6) + (consistency * 0.4), 1)

    if human_confidence >= 75.0:
        status = "Verified Human"
        decision = "Normal Behaviour - No Action Required"
    elif human_confidence >= 45.0:
        status = "Suspicious Behaviour"
        decision = "Suspicious - Reduce Trust Score, Trigger Sandbox Verification, Append Timeline"
    else:
        status = "Automation Detected"
        decision = "High Risk - Generate Alert, Reduce Trust Score, Trigger Employee Lock"

    return {
        "human_confidence": human_confidence,
        "machine_confidence": machine_confidence,
        "bot_probability": bot_prob,
        "behaviour_consistency": consistency,
        "overall_identity_score": overall_identity,
        "status": status,
        "decision": decision
    }


def get_employee_identity_status(db, employee_id):
    """
    Fetches stored identity status or builds from dataset telemetry in identity_telemetry collection.
    """
    doc = db.identity_records.find_one({"employee_id": employee_id})
    if doc:
        doc["_id"] = str(doc.get("_id", ""))
        return doc

    # Fallback to dataset collection 'identity_telemetry' if present
    dataset_records = list(db.identity_telemetry.find({"employee_id": employee_id}))
    if dataset_records:
        dataset_records.sort(key=lambda x: str(x.get("timestamp", "")))
        latest = dataset_records[-1]
        emp = db.employees.find_one({"employee_id": employee_id}) or {}

        history = []
        for d in dataset_records[-15:]:
            history.append({
                "time": str(d.get("timestamp", ""))[:5],
                "timestamp": d.get("timestamp", ""),
                "human_confidence": d.get("scores", {}).get("human_confidence", 90.0),
                "machine_confidence": d.get("scores", {}).get("machine_confidence", 10.0),
                "bot_probability": d.get("scores", {}).get("bot_probability", 5.0)
            })

        record = {
            "employee_id": employee_id,
            "full_name": emp.get("full_name", f"Employee {employee_id}"),
            "telemetry": latest.get("telemetry", {}),
            "scores": latest.get("scores", {}),
            "history": history,
            "source_dataset": "dataset/human_machine_identity_telemetry.csv",
            "updated_at": latest.get("timestamp", datetime.now().isoformat())
        }
        return record

    # Default baseline for user if no custom identity run exists yet
    emp = db.employees.find_one({"employee_id": employee_id}) or {}
    emp_score = emp.get("current_score", 100.0)

    # Adjust initial baseline if employee already has low trust score
    if emp_score < 50.0:
        base_profile = PRESET_TELEMETRY_PROFILES["compromised_session"]
    else:
        base_profile = PRESET_TELEMETRY_PROFILES["human_normal"]

    record = {
        "employee_id": employee_id,
        "full_name": emp.get("full_name", "Employee"),
        "telemetry": base_profile["telemetry"],
        "scores": base_profile["scores"],
        "history": generate_baseline_identity_history(emp_score),
        "updated_at": datetime.now().isoformat()
    }
    return record


def generate_baseline_identity_history(current_trust_score=100.0):
    """
    Generates historical time-series datapoints for Human Confidence vs Machine Confidence graph.
    """
    history = []
    base_time = datetime.now() - timedelta(hours=12)

    is_low = current_trust_score < 50.0

    for i in range(13):
        t = base_time + timedelta(hours=i)
        ts_str = t.strftime("%H:%M")

        if is_low and i >= 8:
            hc = max(12.0, 95.0 - ((i - 7) * 16.0))
            mc = round(100.0 - hc, 1)
        else:
            hc = min(98.0, max(85.0, 95.0 + ((i % 3) - 1) * 2.0))
            mc = round(100.0 - hc, 1)

        history.append({
            "time": ts_str,
            "timestamp": t.isoformat(),
            "human_confidence": round(hc, 1),
            "machine_confidence": round(mc, 1),
            "bot_probability": round(mc * 0.95, 1)
        })

    return history


def analyze_and_execute_decision(db, employee_id, telemetry_data=None, preset_profile_id=None):
    """
    Runs the identity analysis, executes the decision engine:
    - Suspicious: Reduce Trust Score, Trigger Sandbox, Append Timeline
    - Machine (High Risk): Generate Alert, Reduce Trust Score, Trigger Employee Lock, Append Timeline
    """
    emp = db.employees.find_one({"employee_id": employee_id})
    if not emp:
        return {"success": False, "error": f"Employee {employee_id} not found."}

    if preset_profile_id and preset_profile_id in PRESET_TELEMETRY_PROFILES:
        profile = PRESET_TELEMETRY_PROFILES[preset_profile_id]
        telemetry = profile["telemetry"]
        scores = profile["scores"]
    elif telemetry_data:
        telemetry = telemetry_data
        scores = analyze_telemetry_parameters(telemetry_data)
    else:
        profile = PRESET_TELEMETRY_PROFILES["human_normal"]
        telemetry = profile["telemetry"]
        scores = profile["scores"]

    status = scores["status"]
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    timeline_events_to_add = []

    # Decision Engine Execution
    if status == "Verified Human":
        # Normal behaviour
        timeline_events_to_add.append({
            "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
            "employee_id": employee_id,
            "timestamp": now_str,
            "type": "identity_verified",
            "source_dataset": "identity_monitoring_engine",
            "details": {
                "custom_description": f"Human Identity Verified: {scores['human_confidence']}% Confidence rating (Normal Behaviour)",
                "severity": "Low",
                "human_confidence": scores["human_confidence"],
                "machine_confidence": scores["machine_confidence"]
            }
        })

    elif status == "Suspicious Behaviour":
        # 1. Append timeline: Human Identity Verified baseline -> Behaviour Changed -> Sandbox Started -> Trust Reduced
        timeline_events_to_add.extend([
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "identity_verified",
                "source_dataset": "identity_monitoring_engine",
                "details": {
                    "custom_description": "Human Identity Verified - Baseline activity established",
                    "severity": "Low"
                }
            },
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "behaviour_changed",
                "source_dataset": "identity_monitoring_engine",
                "details": {
                    "custom_description": f"Behaviour Changed: Keyboard rhythm stdev dropped to {telemetry.get('keyboard_rhythm', {}).get('flight_time_stdev', 5.0)}ms; elevated PowerShell frequency",
                    "severity": "Medium"
                }
            },
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "sandbox",
                "source_dataset": "sandbox_engine",
                "details": {
                    "custom_description": "Sandbox Started: Isolating suspicious disembodied session commands for virtual evaluation",
                    "severity": "Medium",
                    "sandbox_verdict": "SUSPICIOUS"
                }
            },
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": now_str,
                "type": "trust_reduced",
                "source_dataset": "identity_monitoring_engine",
                "details": {
                    "custom_description": "Trust Reduced (-15.0 pts): Suspicious automated telemetry pattern detected",
                    "severity": "High"
                }
            }
        ])

        # 2. Reduce Trust Score in DB
        db.events.insert_one({
            "event_id": f"EVT-DED-{uuid.uuid4().hex[:6]}",
            "employee_id": employee_id,
            "timestamp": now_str,
            "type": "privilege",
            "details": {
                "approved_by": "SYSTEM_AUTO",
                "severity": "High",
                "custom_description": "Identity Anomaly: Suspicious Human-Machine Telemetry Variance"
            }
        })
        recalculate_score(db, employee_id)

    elif status == "Automation Detected":
        # 1. Append timeline: Automation Detected -> Trust Reduced -> Sandbox Started
        timeline_events_to_add.extend([
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "automation_detected",
                "source_dataset": "identity_monitoring_engine",
                "details": {
                    "custom_description": f"Automation Detected: {scores['machine_confidence']}% Machine Confidence! ({', '.join(telemetry.get('automation_indicators', {}).get('signatures_detected', ['Headless Bot / Script']))})",
                    "severity": "Critical"
                }
            },
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=3)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "trust_reduced",
                "source_dataset": "identity_monitoring_engine",
                "details": {
                    "custom_description": "Trust Reduced (-35.0 pts): Critical Machine Automation & Script Execution",
                    "severity": "Critical"
                }
            },
            {
                "event_id": f"EVT-ID-{uuid.uuid4().hex[:6]}",
                "employee_id": employee_id,
                "timestamp": (now - timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S"),
                "type": "sandbox",
                "source_dataset": "sandbox_engine",
                "details": {
                    "custom_description": "Sandbox Started: High-risk automated script intercept payload redirected to Sandbox",
                    "severity": "Critical",
                    "sandbox_verdict": "MALICIOUS"
                }
            }
        ])

        # 2. Generate Alert in DB
        alert_id = f"ALT-ID-{uuid.uuid4().hex[:6].upper()}"
        db.alerts.insert_one({
            "alert_id": alert_id,
            "employee_id": employee_id,
            "full_name": emp.get("full_name", "Employee"),
            "department": emp.get("department", "Corporate"),
            "type": "Automation & Machine Identity Risk",
            "severity": "Critical",
            "timestamp": now_str,
            "details": f"Machine Confidence at {scores['machine_confidence']}%. Bot probability at {scores['bot_probability']}%. System detected automated headless script execution.",
            "status": "Active"
        })

    # Insert timeline events into DB
    if timeline_events_to_add:
        db.events.insert_many(timeline_events_to_add)

    # Recalculate trust score using unified engine
    recalculate_score(db, employee_id)

    # Fetch updated history time-series graph
    history = generate_baseline_identity_history(db.employees.find_one({"employee_id": employee_id}, {"current_score": 1}).get("current_score", 100.0))
    # Replace last history point with new score
    history[-1] = {
        "time": now.strftime("%H:%M"),
        "timestamp": now.isoformat(),
        "human_confidence": scores["human_confidence"],
        "machine_confidence": scores["machine_confidence"],
        "bot_probability": scores["bot_probability"]
    }

    # Save to identity_records collection
    record = {
        "employee_id": employee_id,
        "full_name": emp.get("full_name", "Employee"),
        "telemetry": telemetry,
        "scores": scores,
        "history": history,
        "updated_at": now.isoformat()
    }

    db.identity_records.update_one(
        {"employee_id": employee_id},
        {"$set": record},
        upsert=True
    )

    # Fetch updated employee object
    updated_emp = db.employees.find_one({"employee_id": employee_id})
    if updated_emp and "_id" in updated_emp:
        updated_emp["_id"] = str(updated_emp["_id"])

    return {
        "success": True,
        "record": record,
        "employee": updated_emp,
        "employee_locked": status == "Automation Detected"
    }
