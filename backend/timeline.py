import os
from datetime import datetime
try:
    from backend.trust_score import evaluate_event_deduction
except ImportError:
    from trust_score import evaluate_event_deduction

def get_event_severity(deductions):
    if not deductions:
        return "Low"
    max_ded = sum(d[1] for d in deductions)
    if max_ded >= 25:
        return "Critical"
    elif max_ded >= 15:
        return "High"
    elif max_ded >= 8:
        return "Medium"
    else:
        return "Low"

def format_event_description(etype, details, is_anomaly):
    if details and "custom_description" in details:
        return details["custom_description"]
    if etype == "logon":
        loc = details.get("location", "HQ Corporate Network")
        dev = details.get("device_id", "Workstation")
        is_after = details.get("is_after_hours")
        is_known = details.get("is_known_device", True)
        
        if is_anomaly:
            reasons = []
            if is_after:
                reasons.append("after working hours")
            if not is_known or "unknown" in str(loc).lower():
                reasons.append("unrecognized device")
            reason_str = f" ({', '.join(reasons)})" if reasons else ""
            return f"Logged in {reason_str} on {dev} from {loc}"
        return f"Standard user login on {dev}"

    elif etype == "file":
        name = details.get("file_name", "document.doc")
        size = details.get("file_size_mb", 0.0)
        sens = details.get("file_sensitivity", "Internal")
        action = details.get("action", "Read")
        
        if is_anomaly:
            if action in ["Copy", "Write", "Exfiltrate"]:
                return f"Copied {sens} file '{name}' ({size} MB) to external directory"
            elif action in ["Delete", "Wipe"]:
                return f"Deleted {sens} file '{name}' ({size} MB)"
            return f"Accessed {sens} confidential file '{name}' ({size} MB)"
        return f"Accessed routine file '{name}' ({size} MB)"

    elif etype == "device":
        act = str(details.get("action", "Connect"))
        size = details.get("data_transferred_mb", 0.0)
        dev = details.get("device_type", "USB Drive")
        
        if "unplug" in act.lower() or "disconnect" in act.lower():
            return f"USB Device Removed from workstation"
        elif is_anomaly or size > 0:
            return f"USB Device Inserted - Transferred {size} MB to removable media"
        return f"USB Device Inserted"

    elif etype == "http":
        cat = details.get("url_category", "General")
        dom = details.get("domain", "web.com")
        if is_anomaly:
            return f"Visited restricted website: {dom} ({cat})"
        return f"Browsed web: {dom} ({cat})"

    elif etype == "email":
        domain = details.get("recipient_domain", "dtaa.com")
        has_att = details.get("has_attachment")
        size = details.get("attachment_size_mb", 0.0)
        att_str = f" with attachment ({size} MB)" if has_att else ""
        if is_anomaly:
            return f"Sent external email to {domain}{att_str}"
        return f"Sent internal email to {domain}{att_str}"

    elif etype == "privilege":
        prev = details.get("previous_access_level", "User")
        new = details.get("new_access_level", "Admin")
        by = details.get("approved_by", "SYSTEM")
        if is_anomaly:
            return f"CRITICAL: Role escalated from {prev} to {new} (Approved by: {by})"
        return f"Role change from {prev} to {new} (Approved by: {by})"

    elif etype == "jit_access":
        act = details.get("action", "Access Request")
        res = details.get("resource", "Sensitive Resource")
        st = details.get("status", "")
        reason = details.get("reason", "")
        if st == "revoked" or is_anomaly:
            return f"JIT PAM {act}: {res} ({reason or 'Emergency Kill-Switch Triggered'})"
        return f"JIT PAM {act}: {res} ({st.upper()})"

    elif etype == "sandbox":
        verdict = details.get("sandbox_verdict", "SAFE")
        cmd = details.get("command", "")
        if verdict == "MALICIOUS":
            return details.get("custom_description") or f"Sandbox Blocked Malicious Action: {cmd}"
        elif verdict == "SUSPICIOUS":
            return details.get("custom_description") or f"Under Observation: {cmd}"
        else:
            return details.get("custom_description") or f"Sandbox Verification Passed: {cmd}"

    elif etype in ["identity_verified", "behaviour_changed", "automation_detected", "trust_reduced", "identity"]:
        return details.get("custom_description") or f"Identity Event: {etype.replace('_', ' ').title()}"

    return f"Security activity: {etype.capitalize()}"

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
    return datetime.now()

def get_employee_timeline(db, employee_id):
    """
    Returns a sorted, deduplicated, and unified timeline for the investigator dashboard.
    """
    raw_events = list(db.events.find({"employee_id": employee_id}).sort("timestamp", 1))
    
    timeline = []
    seen_keys = set()
    
    for event in raw_events:
        etype = event["type"]
        ts = parse_ts(event.get("timestamp"))
        event["timestamp"] = ts
        details = event.get("details", {})
        
        # Check if event is anomalous
        deductions = evaluate_event_deduction(event)
        is_sandbox = etype == "sandbox"
        sandbox_verdict = details.get("sandbox_verdict")
        
        is_anomaly = len(deductions) > 0 or details.get("severity") in ["High", "Critical"] or (is_sandbox and sandbox_verdict in ["SUSPICIOUS", "MALICIOUS"])
        desc = format_event_description(etype, details, is_anomaly)
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")

        # Deduplication key based on timestamp, event type, and description
        dedup_key = f"{ts_str}_{etype}_{desc}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        # Skip zero-byte disconnect logs if an insertion anomaly was logged at the exact same minute
        if etype == "device" and not is_anomaly and details.get("data_transferred_mb", 0.0) == 0.0:
            # Check if any USB anomaly exists within 1 minute
            has_nearby_usb_anomaly = any(
                e["type"] == "device" and e.get("details", {}).get("data_transferred_mb", 0.0) > 0
                and abs((parse_ts(e.get("timestamp")) - ts).total_seconds()) < 60
                for e in raw_events
            )
            if has_nearby_usb_anomaly:
                continue

        timeline.append({
            "event_id": event.get("event_id", f"EVT-{len(timeline)}"),
            "timestamp": ts_str,
            "type": etype,
            "source_dataset": event.get("source_dataset", f"{etype}.csv" if not is_sandbox else "sandbox_engine"),
            "description": desc,
            "severity": details.get("severity") or get_event_severity(deductions),
            "is_anomaly": is_anomaly,
            "is_sandbox": is_sandbox,
            "sandbox_verdict": sandbox_verdict,
            "collapsed": False,
            "count": 1
        })

    # Sort chronologically by timestamp
    timeline.sort(key=lambda x: x["timestamp"])
    return timeline

def flush_routine_group(group):
    """
    Compresses a group of consecutive routine events into a single timeline summary card.
    """
    last_event = group[-1]
    etype = last_event["type"]
    count = len(group)
    last_ts = parse_ts(last_event["timestamp"])
    
    if count == 1:
        return {
            "event_id": last_event["event_id"],
            "timestamp": last_ts.strftime("%Y-%m-%d %H:%M:%S"),
            "type": etype,
            "description": format_event_description(etype, last_event.get("details", {}), is_anomaly=False),
            "severity": "Low",
            "is_anomaly": False,
            "collapsed": False,
            "count": 1
        }
        
    # Multi-event summary
    categories = set()
    for e in group:
        details = e.get("details", {})
        if etype == "http":
            categories.add(details.get("url_category", "General"))
        elif etype == "file":
            categories.add(details.get("action", "Access"))
        elif etype == "logon":
            categories.add(details.get("location", "Office"))
            
    cat_str = f" ({', '.join(categories)})" if categories else ""
    
    description = f"{count} routine {etype} operations{cat_str}"
    if etype == "logon":
        description = f"{count} routine logons from {', '.join(categories)}"
    elif etype == "file":
        description = f"{count} routine file operations"
    elif etype == "http":
        description = f"{count} standard web search/browse sessions"
    elif etype == "email":
        description = f"{count} standard emails sent"

    return {
        "event_id": last_event["event_id"],
        "timestamp": last_ts.strftime("%Y-%m-%d %H:%M:%S"),
        "type": etype,
        "description": description,
        "severity": "Low",
        "is_anomaly": False,
        "collapsed": True,
        "count": count
    }
