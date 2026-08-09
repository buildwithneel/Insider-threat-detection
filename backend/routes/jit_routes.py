"""
SentinelAI JIT Access Management API Routes
===========================================

Flask Blueprint endpoints for issuing, verifying, revoking, extending JIT tokens,
retrieving append-only audit logs, and rendering dashboard analytics.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any

try:
    from backend.database.jit_db import (
        create_jit_token,
        verify_and_use_jit_token,
        revoke_jit_token,
        extend_jit_token,
        get_jit_tokens,
        get_jit_audit_logs,
        get_jit_dashboard_stats,
        ALL_JIT_PERMISSIONS
    )
    from backend.security.jit_middleware import is_rate_limited
    from backend.security.rbac_middleware import require_permission
    from backend.db_client import get_db
except ImportError:
    from database.jit_db import (
        create_jit_token,
        verify_and_use_jit_token,
        revoke_jit_token,
        extend_jit_token,
        get_jit_tokens,
        get_jit_audit_logs,
        get_jit_dashboard_stats,
        ALL_JIT_PERMISSIONS
    )
    from security.jit_middleware import is_rate_limited
    from security.rbac_middleware import require_permission
    from db_client import get_db

jit_bp = Blueprint("jit", __name__, url_prefix="/api/jit")

PRESET_DURATIONS = {
    "15 Minutes": 15,
    "15 MINUTES": 15,
    "15 MINS": 15,
    "30 Minutes": 30,
    "30 MINUTES": 30,
    "30 MINS": 30,
    "60 Minutes": 60,
    "60 MINUTES": 60,
    "60 MINS": 60,
    "1 Hour": 60,
    "1 HOUR": 60,
    "2 Hours": 120,
    "2 HOURS": 120,
    "4 Hours": 240,
    "4 HOURS": 240,
    "8 Hours": 480,
    "8 HOURS": 480,
    "12 Hours": 720,
    "12 HOURS": 720,
    "24 Hours": 1440,
    "24 HOURS": 1440,
}

def get_client_metadata() -> Dict[str, str]:
    """Helper to collect client IP, device, and browser information."""
    ua = request.user_agent
    return {
        "ip_address": request.remote_addr or request.headers.get("X-Forwarded-For", "127.0.0.1"),
        "device_info": f"{ua.platform or 'Unknown Platform'} / {ua.string[:60] if ua else 'Unknown Device'}",
        "browser": f"{ua.browser or 'Unknown Browser'} {ua.version or ''}".strip()
    }

@jit_bp.route("/permissions", methods=["GET"])
def get_permissions():
    """Returns available permissions and preset expiration duration mappings."""
    return jsonify({
        "permissions": ALL_JIT_PERMISSIONS,
        "preset_durations": PRESET_DURATIONS
    }), 200

@jit_bp.route("/tokens/issue", methods=["POST"])
@require_permission("generate_jit_tokens")
def issue_token():
    """
    Issues a new JIT Token with specified access scope, permissions, and duration.
    Payload parameters:
    - employee_id: str (Required)
    - employee_name: str (Optional)
    - department: str (Optional)
    - admin_id: str (Optional)
    - admin_name: str (Optional)
    - access_type: "Full Access" | "Limited Access" (Required)
    - granted_permissions: list of str (Required if Limited Access)
    - preset_duration: str (e.g. "1 Hour") or custom duration fields (days, hours, minutes, seconds)
    """
    data = request.get_json(silent=True) or {}

    employee_id = data.get("employee_id")
    if not employee_id:
        return jsonify({"error": "employee_id is required"}), 400

    employee_name = data.get("employee_name", f"Employee {employee_id}")
    department = data.get("department", "SOC Division")
    admin_id = data.get("admin_id", "GAR-0001")
    admin_name = data.get("admin_name", "Lead Security Administrator")

    access_type = data.get("access_type") or data.get("accessLevel") or "Full Access"

    # Strict Validation: Check for presence of both access levels (e.g. lists, arrays, or conflicting parameters)
    raw_levels = []
    if isinstance(access_type, list):
        raw_levels.extend(access_type)
    else:
        raw_levels.append(access_type)
    
    if "accessLevel" in data and data["accessLevel"] not in raw_levels:
        raw_levels.append(data["accessLevel"])
    
    levels_upper = [str(lvl).strip().upper() for lvl in raw_levels]
    has_limited = any(l in levels_upper for l in ["LIMITED", "LIMITED ACCESS"])
    has_full = any(l in levels_upper for l in ["FULL", "FULL ACCESS"])

    granted_permissions = data.get("granted_permissions", [])
    if isinstance(granted_permissions, list):
        gp_upper = [str(p).strip().upper() for p in granted_permissions]
        if "LIMITED" in gp_upper:
            has_limited = True
        if "FULL" in gp_upper:
            has_full = True

    if has_limited and has_full:
        return jsonify({"error": "Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously."}), 400

    # Normalize access_type string
    if has_limited:
        access_type_normalized = "Limited Access"
    elif has_full:
        access_type_normalized = "Full Access"
    else:
        return jsonify({"error": "access_type must be 'Full Access' or 'Limited Access' (or 'FULL' / 'LIMITED')"}), 400

    if access_type_normalized == "Limited Access" and not granted_permissions:
        return jsonify({"error": "granted_permissions must contain at least one permission when Limited Access is selected"}), 400

    # Calculate total duration in minutes
    duration_minutes = None
    preset_dur = data.get("preset_duration")
    if preset_dur:
        p_str = str(preset_dur).strip()
        p_upper = p_str.upper()
        if p_str in PRESET_DURATIONS:
            duration_minutes = float(PRESET_DURATIONS[p_str])
        elif p_upper in PRESET_DURATIONS:
            duration_minutes = float(PRESET_DURATIONS[p_upper])
        else:
            import re
            m = re.match(r"^(\d+)\s*(min|minute|minutes|hour|hours|h|m)?$", p_str, re.IGNORECASE)
            if m:
                val = float(m.group(1))
                unit = (m.group(2) or "m").lower()
                duration_minutes = val * 60.0 if unit.startswith("h") else val

    if duration_minutes is None:
        if "duration_minutes" in data and data["duration_minutes"] is not None:
            duration_minutes = float(data["duration_minutes"])
        elif "custom_duration" in data and data["custom_duration"]:
            c = data["custom_duration"]
            days = float(c.get("days", 0))
            hours = float(c.get("hours", 0))
            minutes = float(c.get("minutes", 0))
            seconds = float(c.get("seconds", 0))
            duration_minutes = (days * 1440.0) + (hours * 60.0) + minutes + (seconds / 60.0)
        else:
            duration_minutes = 60.0

    print(f"[DEBUG_JIT_ROUTES] Received Issue Request -> employee_id: {employee_id}, access_type: {access_type_normalized}, duration_minutes: {duration_minutes}, preset_duration: {preset_dur}, permissions: {granted_permissions}")

    if duration_minutes <= 0:
        return jsonify({"error": "Token duration must be greater than 0 minutes"}), 400

    meta = get_client_metadata()
    db = get_db()

    try:
        token_doc, plain_token = create_jit_token(
            employee_id=employee_id,
            employee_name=employee_name,
            department=department,
            admin_id=admin_id,
            admin_name=admin_name,
            access_type=access_type_normalized,
            granted_permissions=granted_permissions,
            duration_minutes=duration_minutes,
            ip_address=meta["ip_address"],
            device_info=meta["device_info"],
            browser=meta["browser"],
            db=db
        )
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400

    return jsonify({
        "success": True,
        "message": "JIT Token issued successfully.",
        "token": token_doc,
        "secure_token": plain_token # Plaintext returned ONCE to Admin
    }), 201

@jit_bp.route("/tokens/verify", methods=["POST"])
def verify_token():
    """
    Verifies a JIT candidate token string for workstation unlock/session authorization.
    Rate limited to 5 attempts per window.
    """
    data = request.get_json(silent=True) or {}
    plain_token = data.get("token") or data.get("jit_token")
    employee_id = data.get("employee_id")

    if not plain_token:
        return jsonify({"error": "token string is required"}), 400

    meta = get_client_metadata()
    rate_key = f"{meta['ip_address']}_{employee_id or 'anon'}"

    if is_rate_limited(rate_key):
        return jsonify({
            "success": False,
            "error": "Too many failed unlock attempts. Rate limited for 60 seconds."
        }), 429

    db = get_db()
    is_valid, token_doc, message = verify_and_use_jit_token(
        plain_token=plain_token,
        employee_id=employee_id,
        ip_address=meta["ip_address"],
        device_info=meta["device_info"],
        browser=meta["browser"],
        db=db
    )

    clean_doc = {k: v for k, v in token_doc.items() if k != "token_hash" and k != "_id"} if token_doc else None

    if is_valid:
        return jsonify({
            "success": True,
            "message": message,
            "token": clean_doc
        }), 200
    else:
        return jsonify({
            "success": False,
            "error": message,
            "token": clean_doc
        }), 400

@jit_bp.route("/tokens", methods=["GET"])
def list_tokens():
    """Admin endpoint to search and filter JIT tokens."""
    status = request.args.get("status")
    employee_id = request.args.get("employee_id")
    query = request.args.get("query")

    db = get_db()
    tokens = get_jit_tokens(status=status, employee_id=employee_id, query=query, db=db)
    return jsonify({
        "success": True,
        "count": len(tokens),
        "tokens": tokens
    }), 200

@jit_bp.route("/tokens/<token_id>", methods=["GET"])
def get_token_by_id(token_id):
    """Retrieves a single JIT token record by Token ID."""
    db = get_db()
    tokens = get_jit_tokens(query=token_id, db=db)
    target = next((t for t in tokens if t.get("token_id") == token_id), None)
    if not target:
        return jsonify({"error": "Token not found"}), 404
    return jsonify({"success": True, "token": target}), 200

@jit_bp.route("/tokens/<token_id>/revoke", methods=["POST"])
def revoke_token_endpoint(token_id):
    """Admin endpoint to immediately revoke an active token."""
    data = request.get_json(silent=True) or {}
    admin_id = data.get("admin_id", "GAR-0001")
    admin_name = data.get("admin_name", "Lead Security Administrator")
    reason = data.get("reason", "Admin manual revocation")

    meta = get_client_metadata()
    db = get_db()

    success, msg = revoke_jit_token(
        token_id=token_id,
        admin_id=admin_id,
        admin_name=admin_name,
        reason=reason,
        ip_address=meta["ip_address"],
        device_info=meta["device_info"],
        browser=meta["browser"],
        db=db
    )

    if success:
        return jsonify({"success": True, "message": msg}), 200
    else:
        return jsonify({"success": False, "error": msg}), 400

@jit_bp.route("/tokens/<token_id>/extend", methods=["POST"])
def extend_token_endpoint(token_id):
    """Admin endpoint to extend token expiration time."""
    data = request.get_json(silent=True) or {}
    additional_minutes = float(data.get("additional_minutes", 30))
    admin_id = data.get("admin_id", "GAR-0001")
    admin_name = data.get("admin_name", "Lead Security Administrator")

    if additional_minutes <= 0:
        return jsonify({"error": "additional_minutes must be greater than 0"}), 400

    meta = get_client_metadata()
    db = get_db()

    success, token_doc, msg = extend_jit_token(
        token_id=token_id,
        additional_minutes=additional_minutes,
        admin_id=admin_id,
        admin_name=admin_name,
        ip_address=meta["ip_address"],
        device_info=meta["device_info"],
        browser=meta["browser"],
        db=db
    )

    clean_doc = {k: v for k, v in token_doc.items() if k != "token_hash" and k != "_id"} if token_doc else None

    if success:
        return jsonify({"success": True, "message": msg, "token": clean_doc}), 200
    else:
        return jsonify({"success": False, "error": msg, "token": clean_doc}), 400

@jit_bp.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    """Retrieves JIT audit logs with search and filter support."""
    event_type = request.args.get("event_type")
    employee_id = request.args.get("employee_id")
    query = request.args.get("query")

    db = get_db()
    logs = get_jit_audit_logs(event_type=event_type, employee_id=employee_id, query=query, db=db)
    return jsonify({
        "success": True,
        "count": len(logs),
        "audit_logs": logs
    }), 200

@jit_bp.route("/dashboard/stats", methods=["GET"])
def get_dashboard_analytics():
    """Retrieves JIT dashboard statistics and metrics."""
    employee_id = request.args.get("employee_id")
    db = get_db()
    stats = get_jit_dashboard_stats(employee_id=employee_id, db=db)
    return jsonify({
        "success": True,
        "stats": stats
    }), 200
