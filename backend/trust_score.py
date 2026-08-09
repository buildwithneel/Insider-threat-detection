import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient

# Configurable Severity Weights (Never hardcoded throughout project)
SEVERITY_WEIGHTS = {
    "Low": 5.0,
    "Medium": 10.0,
    "High": 20.0,
    "Critical": 30.0
}

# Configuration Dictionary for Risk Deductions using Severity Weights
DEDUCTION_CONFIG = {
    "after_hours_login": SEVERITY_WEIGHTS["Low"],             # 5.0
    "unknown_device_login": SEVERITY_WEIGHTS["Medium"],       # 10.0
    "usb_connect": SEVERITY_WEIGHTS["Medium"],                # 10.0
    "unauthorized_privilege_escalation": SEVERITY_WEIGHTS["High"], # 20.0
    "confidential_file_access": SEVERITY_WEIGHTS["Medium"],   # 10.0
    "restricted_file_access": SEVERITY_WEIGHTS["Medium"],     # 10.0
    "large_file_transfer": SEVERITY_WEIGHTS["Medium"],        # 10.0
    "massive_data_transfer": SEVERITY_WEIGHTS["High"],        # 20.0
    "external_email_attachment": SEVERITY_WEIGHTS["Medium"],  # 10.0
    "unusual_domain_visit": SEVERITY_WEIGHTS["Medium"],       # 10.0
    "identity_suspicious_behaviour": SEVERITY_WEIGHTS["Medium"], # 10.0
    "identity_automation_detected": SEVERITY_WEIGHTS["Critical"] # 30.0
}

RECOVERY_RATE_PER_DAY = 0.5 # Max slow recovery per day of clean behavior

def evaluate_event_deduction(event):
    """
    Evaluates a single event and returns a list of (deduction_name, score_deduction) tuples.
    """
    deductions = []
    etype = event.get("type")
    details = event.get("details", {})

    if etype == "logon":
        if details.get("is_after_hours"):
            deductions.append(("after_hours_login", DEDUCTION_CONFIG["after_hours_login"]))
        if details.get("is_known_device") is False or "unknown" in str(details.get("location", "")).lower():
            deductions.append(("unknown_device_login", DEDUCTION_CONFIG["unknown_device_login"]))

    elif etype == "file":
        sens = details.get("file_sensitivity")
        size = details.get("file_size_mb", 0.0)
        
        if sens == "Confidential":
            deductions.append(("confidential_file_access", DEDUCTION_CONFIG["confidential_file_access"]))
        elif sens == "Restricted":
            deductions.append(("restricted_file_access", DEDUCTION_CONFIG["restricted_file_access"]))
            
        if size > 1000.0:
            deductions.append(("massive_data_transfer", DEDUCTION_CONFIG["massive_data_transfer"]))
        elif size > 100.0:
            deductions.append(("large_file_transfer", DEDUCTION_CONFIG["large_file_transfer"]))

    elif etype == "device":
        action = details.get("action", "")
        size = details.get("data_transferred_mb", 0.0)
        action_str = str(action).lower()
        
        if any(k in action_str for k in ["connect", "plugin", "usb"]):
            deductions.append(("usb_connect", DEDUCTION_CONFIG["usb_connect"]))
            
        if size > 1000.0:
            deductions.append(("massive_data_transfer", DEDUCTION_CONFIG["massive_data_transfer"]))
        elif size > 100.0 or "massive" in action_str:
            deductions.append(("large_file_transfer", DEDUCTION_CONFIG["large_file_transfer"]))

    elif etype == "email":
        domain = details.get("recipient_domain", "")
        has_att = details.get("has_attachment")
        size = details.get("attachment_size_mb", 0.0)
        
        if domain and domain not in ["dtaa.com", "company.com", "partnercorp.com", "clientnet.org"]:
            deductions.append(("unusual_domain_visit", DEDUCTION_CONFIG["unusual_domain_visit"]))
        if has_att:
            deductions.append(("external_email_attachment", DEDUCTION_CONFIG["external_email_attachment"]))
            if size > 1000.0:
                deductions.append(("massive_data_transfer", DEDUCTION_CONFIG["massive_data_transfer"]))
            elif size > 100.0:
                deductions.append(("large_file_transfer", DEDUCTION_CONFIG["large_file_transfer"]))

    elif etype == "http":
        cat = details.get("url_category", "")
        domain = details.get("domain", "")
        if cat in ["Cloud Storage", "Webmail"] or domain in ["mega.io", "gmail.com", "yahoo.com", "dropbox.com"]:
            deductions.append(("unusual_domain_visit", DEDUCTION_CONFIG["unusual_domain_visit"]))

    elif etype == "privilege":
        approved_by = details.get("approved_by")
        if approved_by == "SYSTEM_AUTO" or not details.get("approved", True):
            deductions.append(("unauthorized_privilege_escalation", DEDUCTION_CONFIG["unauthorized_privilege_escalation"]))

    elif etype == "automation_detected":
        deductions.append(("identity_automation_detected", DEDUCTION_CONFIG["identity_automation_detected"]))

    elif etype in ["trust_reduced", "behaviour_changed"]:
        deductions.append(("identity_suspicious_behaviour", DEDUCTION_CONFIG["identity_suspicious_behaviour"]))

    elif etype == "sandbox":
        verdict = details.get("sandbox_verdict", "")
        if verdict == "SUSPICIOUS":
            deductions.append(("sandbox_suspicious", SEVERITY_WEIGHTS["Medium"]))
        elif verdict == "MALICIOUS":
            deductions.append(("sandbox_malicious", SEVERITY_WEIGHTS["Critical"]))

    # Generic fallback using severity weight if provided in event details
    if not deductions and details.get("severity") in SEVERITY_WEIGHTS:
        sev = details.get("severity")
        deductions.append((f"event_{sev.lower()}_severity", SEVERITY_WEIGHTS[sev]))

    return deductions

def recalculate_score(db, employee_id):
    """
    Chronologically evaluates an employee's events to compute current trust score and logs the history.
    """
    events = list(db.events.find({"employee_id": employee_id}).sort("timestamp", 1))
    
    def parse_ts(ts):
        if isinstance(ts, datetime):
            return ts
        if isinstance(ts, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    pass
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                pass
        return datetime(2026, 4, 13, 0, 0, 0)

    initial_score = 100.0
    score = 100.0
    total_accumulated_deductions = 0.0
    history = []
    
    start_time = datetime(2026, 4, 13, 0, 0, 0)
    if events:
        first_ts = parse_ts(events[0].get("timestamp"))
        start_time = first_ts - timedelta(days=1)
        
    history.append({
        "employee_id": employee_id,
        "timestamp": start_time,
        "score": 100.0,
        "reason": "Initial Baseline"
    })
    
    last_date = start_time.date()
    
    for event in events:
        event_time = parse_ts(event.get("timestamp"))
        event_date = event_time.date()
        
        # 1. Evaluate deductions for the current event
        deductions = evaluate_event_deduction(event)
        if deductions:
            event_deduction = sum(d[1] for d in deductions)
            total_accumulated_deductions += event_deduction
            score = max(0.0, min(100.0, score - event_deduction))
            reasons = ", ".join([f"{d[0]} (-{d[1]})" for d in deductions])
            
            history.append({
                "employee_id": employee_id,
                "timestamp": event_time,
                "score": round(score, 2),
                "reason": reasons
            })
        
        # 2. Apply capped recovery (never exceeding 100 minus active non-remediated baseline)
        if event_date > last_date:
            days_diff = (event_date - last_date).days
            if days_diff > 1 and score < 100.0:
                clean_days = min(5, days_diff - 1)
                score = min(100.0, score + (clean_days * RECOVERY_RATE_PER_DAY))
                history.append({
                    "employee_id": employee_id,
                    "timestamp": datetime.combine(event_date - timedelta(days=1), datetime.min.time()),
                    "score": round(score, 2),
                    "reason": f"Recovery (+{clean_days * RECOVERY_RATE_PER_DAY:.1f} pts for clean behavior)"
                })

        last_date = event_date

    # Final score clamping safeguard (0 to 100)
    final_score = round(max(0.0, min(100.0, score)), 2)

    # Dev mode logging
    DEV_MODE = os.environ.get("DEV_MODE", "true").lower() == "true"
    if DEV_MODE:
        print(f"[DEBUG_LOG] Trust Score Engine -> Employee: {employee_id} | Initial: {initial_score} | Final Stored Value: {final_score} | Total Events Evaluated: {len(events)}")

    # Save score & reasons to employee document
    reasons_list = get_trust_score_reasons(db, employee_id)
    db.employees.update_one(
        {"employee_id": employee_id},
        {"$set": {
            "current_score": final_score,
            "score_reasons": reasons_list
        }}
    )
    
    # Refresh trust score history
    db.trust_scores.delete_many({"employee_id": employee_id})
    db.trust_scores.insert_many(history)
    
    return final_score

def get_trust_score_reasons(db, employee_id):
    """
    Returns an explainable list of reasons for an employee's current trust score.
    """
    events = list(db.events.find({"employee_id": employee_id}))
    emp = db.employees.find_one({"employee_id": employee_id}) or {}
    
    deduction_counts = {}
    total_deduction_map = {}
    
    for event in events:
        deductions = evaluate_event_deduction(event)
        for name, pts in deductions:
            deduction_counts[name] = deduction_counts.get(name, 0) + 1
            total_deduction_map[name] = total_deduction_map.get(name, 0.0) + pts

    reasons = []
    labels_map = {
        "after_hours_login": "Off-hours / weekend logins",
        "unknown_device_login": "Unrecognized device logins",
        "usb_connect": "Removable USB device connect events",
        "unauthorized_privilege_escalation": "Unsanctioned role escalations",
        "confidential_file_access": "Confidential file operations",
        "restricted_file_access": "Restricted file operations",
        "large_file_transfer": "Large file transfers (>100MB)",
        "massive_data_transfer": "Massive data transfers (>1000MB)",
        "external_email_attachment": "External emails with attachments",
        "unusual_domain_visit": "Suspicious HTTP / Webmail visits"
    }

    for name, cnt in deduction_counts.items():
        label = labels_map.get(name, name.replace("_", " ").title())
        pts = total_deduction_map.get(name, 0.0)
        reasons.append(f"{cnt} {label} (-{pts:.1f} pts)")

    psych = emp.get("psychometrics", {})
    if psych:
        n_score = psych.get("N", 0)
        c_score = psych.get("C", 0)
        a_score = psych.get("A", 0)
        if n_score > 35 or c_score < 20 or a_score < 20:
            reasons.append("High Neuroticism / Low Conscientiousness behavioral indicator (-5.0 pts)")

    if not reasons:
        reasons.append("Clean behavioral history (100% baseline rating)")

    return reasons

def run_score_engine_all_users(db):
    """
    Utility to recalculate trust scores for all employees in the system.
    """
    employees = db.employees.find({}, {"employee_id": 1})
    count = 0
    for emp in employees:
        recalculate_score(db, emp["employee_id"])
        count += 1
    print(f"Recalculated scores and history snapshots for {count} employees.")
