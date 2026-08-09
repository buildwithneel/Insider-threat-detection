"""
SentinelAI JIT Access Management Database & Persistent Storage Engine
====================================================================

Manages MongoDB collections:
1. `jit_tokens`: Stores cryptographically hashed JIT tokens with scope and expiration metadata.
2. `jit_audit_logs`: Stores permanent, append-only security audit trail records for all JIT operations.
"""

import hashlib
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from bson import ObjectId

try:
    from backend.db_client import get_db
except ImportError:
    from db_client import get_db

logger = logging.getLogger("sentinelai.jit_db")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [JIT_DB] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Master list of all available granular access permissions
ALL_JIT_PERMISSIONS = [
    "Dashboard",
    "Employee List",
    "Investigations",
    "AI Investigation",
    "Reports",
    "Analytics",
    "Activity Timeline",
    "Trust Score",
    "Alerts",
    "User Management",
    "Settings",
    "Export Data",
    "Audit Logs",
    "Model Management",
    "Dataset Upload",
    "System Configuration"
]

def hash_token(plain_token: str) -> str:
    """Hashes a plain-text token using SHA-256."""
    return hashlib.sha256(plain_token.encode('utf-8')).hexdigest()

def generate_secure_token() -> str:
    """Generates a cryptographically secure JIT token string."""
    part1 = secrets.token_hex(2).upper()
    part2 = secrets.token_hex(2).upper()
    part3 = secrets.token_hex(2).upper()
    return f"JIT-{part1}-{part2}-{part3}"

def generate_token_id() -> str:
    """Generates a unique human-readable Token ID."""
    num = secrets.randbelow(900000) + 100000
    return f"TK-{num}"

def serialize_doc(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Converts MongoDB document to JSON-serializable dictionary."""
    if not doc:
        return doc
    clean = {}
    for k, v in doc.items():
        if k == "token_hash":
            continue
        if isinstance(v, ObjectId):
            clean[k] = str(v)
        elif isinstance(v, datetime):
            clean[k] = v.isoformat()
        else:
            clean[k] = v
    return clean

def init_jit_db(db=None):
    """Initializes indexes for JIT collections."""
    if db is None:
        db = get_db()
    
    try:
        # Create indexes on jit_tokens
        db.jit_tokens.create_index("employee_id")
        db.jit_tokens.create_index("admin_id")
        db.jit_tokens.create_index("status")
        db.jit_tokens.create_index("expires_at")
        db.jit_tokens.create_index("created_at")

        # Create indexes on jit_audit_logs
        db.jit_audit_logs.create_index("employee_id")
        db.jit_audit_logs.create_index("admin_id")
        db.jit_audit_logs.create_index("event_type")
        db.jit_audit_logs.create_index("timestamp")
        logger.info("JIT MongoDB indexes initialized successfully.")
    except Exception as e:
        logger.warning(f"JIT database index initialization note: {e}")

def create_audit_log(
    event_type: str,
    employee_id: str,
    employee_name: str,
    admin_id: str,
    admin_name: str,
    token_id: str,
    ip_address: str = "127.0.0.1",
    device_info: str = "Unknown Device",
    browser: str = "Unknown Browser",
    location: str = "Security Operations Center",
    success: bool = True,
    notes: str = "",
    db=None
) -> Dict[str, Any]:
    """Writes a permanent audit log record to jit_audit_logs. Logs are NEVER auto-deleted."""
    if db is None:
        db = get_db()

    now = datetime.now(timezone.utc)
    log_doc = {
        "timestamp": now.isoformat(),
        "event_type": event_type,
        "employee_id": employee_id,
        "employee_name": employee_name,
        "admin_id": admin_id,
        "admin_name": admin_name,
        "employee": {
            "id": employee_id,
            "name": employee_name
        },
        "admin": {
            "id": admin_id,
            "name": admin_name
        },
        "token_id": token_id,
        "ip_address": ip_address,
        "device_info": device_info,
        "browser": browser,
        "location": location,
        "success": success,
        "notes": notes,
        "created_at": now.isoformat()
    }
    
    db.jit_audit_logs.insert_one(log_doc)
    return serialize_doc(log_doc)

def create_jit_token(
    employee_id: str,
    employee_name: str,
    department: str,
    admin_id: str,
    admin_name: str,
    access_type: str,
    granted_permissions: List[str],
    duration_minutes: float,
    ip_address: str = "127.0.0.1",
    device_info: str = "Unknown Device",
    browser: str = "Unknown Browser",
    db=None
) -> Tuple[Dict[str, Any], str]:
    """
    Creates and stores a new JIT token in MongoDB.
    Returns tuple: (token_document, plain_text_token)
    """
    if db is None:
        db = get_db()

    # Automatically trigger auto-expiration check on pending tokens
    auto_expire_tokens(db=db)

    # Validate access type parameter for arrays or dual selection attempts
    if isinstance(access_type, (list, tuple, set)):
        items_upper = [str(x).upper() for x in access_type]
        if ("LIMITED" in items_upper or "LIMITED ACCESS" in items_upper) and ("FULL" in items_upper or "FULL ACCESS" in items_upper):
            raise ValueError("Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously.")
        access_type = access_type[0] if access_type else "FULL"

    access_type_str = str(access_type).strip()
    access_type_upper = access_type_str.upper()

    if access_type_upper in ["FULL", "FULL ACCESS"]:
        access_level = "FULL"
        access_type_display = "Full Access"
        permissions = list(ALL_JIT_PERMISSIONS)
    elif access_type_upper in ["LIMITED", "LIMITED ACCESS"]:
        access_level = "LIMITED"
        access_type_display = "Limited Access"
        permissions = [p for p in (granted_permissions or []) if p in ALL_JIT_PERMISSIONS]
    else:
        raise ValueError(f"Invalid access level '{access_type}'. Must be 'LIMITED' or 'FULL'.")

    # Rejection check if both permissions or access levels are supplied
    if isinstance(granted_permissions, list):
        gp_upper = [str(p).upper() for p in granted_permissions]
        if "LIMITED" in gp_upper and "FULL" in gp_upper:
            raise ValueError("Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously.")

    # Remove any existing active JIT tokens with conflicting access level for this employee
    existing_active = list(db.jit_tokens.find({
        "employee_id": employee_id,
        "status": "Active"
    }))

    now_iso = datetime.now(timezone.utc).isoformat()
    for active_t in existing_active:
        prev_level = active_t.get("accessLevel") or ("FULL" if active_t.get("access_type") == "Full Access" else "LIMITED")
        if prev_level != access_level:
            db.jit_tokens.update_one(
                {"token_id": active_t["token_id"]},
                {"$set": {
                    "status": "Revoked",
                    "revoked_at": now_iso,
                    "updated_at": now_iso,
                    "revocation_reason": f"Superseded by new {access_level} access assignment"
                }}
            )
            create_audit_log(
                event_type="Token Revoked",
                employee_id=employee_id,
                employee_name=employee_name,
                admin_id=admin_id,
                admin_name=admin_name,
                token_id=active_t["token_id"],
                ip_address=ip_address,
                device_info=device_info,
                browser=browser,
                success=True,
                notes=f"Revoked existing {prev_level} token. Employee switched to {access_level} access level.",
                db=db
            )

    plain_token = generate_secure_token()
    token_hash_val = hash_token(plain_token)
    token_id = generate_token_id()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=duration_minutes)

    token_doc = {
        "token_id": token_id,
        "token_hash": token_hash_val,
        "employee_id": employee_id,
        "employeeId": employee_id,
        "employee_name": employee_name,
        "department": department or "N/A",
        "admin_id": admin_id,
        "admin_name": admin_name,
        "generated_by": admin_name,
        "access_type": access_type_display,
        "accessLevel": access_level,
        "granted_permissions": permissions,
        "duration": float(duration_minutes),
        "duration_minutes": float(duration_minutes),
        "status": "Active",
        "issued_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "revoked_at": None,
        "last_used": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat()
    }

    db.jit_tokens.insert_one(token_doc)

    logger.info(f"[DEBUG_JIT_PIPELINE] Token Created in DB -> ID: {token_id}, Employee: {employee_id}, Scope: {access_type_display}, Duration: {duration_minutes}m, Expiry: {expires_at.isoformat()}, Permissions: {len(permissions)}")

    # Permanent Audit Logging
    create_audit_log(
        event_type="Token Issued",
        employee_id=employee_id,
        employee_name=employee_name,
        admin_id=admin_id,
        admin_name=admin_name,
        token_id=token_id,
        ip_address=ip_address,
        device_info=device_info,
        browser=browser,
        success=True,
        notes=f"Issued {access_level} ({access_type_display}) token valid for {duration_minutes} minutes with {len(permissions)} permissions.",
        db=db
    )

    # Prepare user-facing return doc containing plain_token ONCE
    user_doc = serialize_doc(token_doc)
    user_doc["plain_token"] = plain_token
    return user_doc, plain_token

def verify_and_use_jit_token(
    plain_token: str,
    employee_id: Optional[str] = None,
    ip_address: str = "127.0.0.1",
    device_info: str = "Unknown Device",
    browser: str = "Unknown Browser",
    db=None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Verifies a candidate token by SHA-256 hashing and checking DB status & expiration.
    Returns tuple: (is_valid, token_document, message)
    """
    if db is None:
        db = get_db()

    auto_expire_tokens(db=db)

    token_hash_val = hash_token(plain_token.strip())
    query = {"token_hash": token_hash_val}
    if employee_id:
        query["employee_id"] = employee_id

    doc = db.jit_tokens.find_one(query)

    if not doc:
        # Log unlock attempt failure
        create_audit_log(
            event_type="Failed Unlock",
            employee_id=employee_id or "UNKNOWN",
            employee_name="Unknown Employee",
            admin_id="SYSTEM",
            admin_name="System Guard",
            token_id="UNKNOWN",
            ip_address=ip_address,
            device_info=device_info,
            browser=browser,
            success=False,
            notes="Attempted unlock with non-existent or mismatched token string.",
            db=db
        )
        return False, None, "Invalid token string or token does not match employee."

    now_iso = datetime.now(timezone.utc).isoformat()
    token_id = doc["token_id"]

    if doc["status"] == "Revoked":
        create_audit_log(
            event_type="Token Revoked",
            employee_id=doc["employee_id"],
            employee_name=doc["employee_name"],
            admin_id=doc["admin_id"],
            admin_name=doc["admin_name"],
            token_id=token_id,
            ip_address=ip_address,
            device_info=device_info,
            browser=browser,
            success=False,
            notes="Attempted unlock with a revoked token.",
            db=db
        )
        return False, serialize_doc(doc), "Token has been revoked by Administrator."

    if doc["expires_at"] <= now_iso or doc["status"] == "Expired":
        if doc["status"] != "Expired":
            db.jit_tokens.update_one(
                {"token_id": token_id},
                {"$set": {"status": "Expired", "updated_at": now_iso}}
            )
            create_audit_log(
                event_type="Token Expired",
                employee_id=doc["employee_id"],
                employee_name=doc["employee_name"],
                admin_id=doc["admin_id"],
                admin_name=doc["admin_name"],
                token_id=token_id,
                ip_address=ip_address,
                device_info=device_info,
                browser=browser,
                success=False,
                notes="Token expiration timestamp reached during verification attempt.",
                db=db
            )
        doc["status"] = "Expired"
        return False, serialize_doc(doc), "Token has expired."

    if doc["status"] != "Active":
        return False, serialize_doc(doc), f"Token status is invalid ({doc['status']})."

    # Token is valid! Update last_used
    db.jit_tokens.update_one(
        {"token_id": token_id},
        {"$set": {"last_used": now_iso, "updated_at": now_iso}}
    )
    doc["last_used"] = now_iso

    create_audit_log(
        event_type="Token Used",
        employee_id=doc["employee_id"],
        employee_name=doc["employee_name"],
        admin_id=doc["admin_id"],
        admin_name=doc["admin_name"],
        token_id=token_id,
        ip_address=ip_address,
        device_info=device_info,
        browser=browser,
        success=True,
        notes=f"Successfully verified JIT token with scope '{doc['access_type']}'.",
        db=db
    )

    create_audit_log(
        event_type="Unlock Attempt",
        employee_id=doc["employee_id"],
        employee_name=doc["employee_name"],
        admin_id=doc["admin_id"],
        admin_name=doc["admin_name"],
        token_id=token_id,
        ip_address=ip_address,
        device_info=device_info,
        browser=browser,
        success=True,
        notes="Workstation access unlocked via valid JIT token.",
        db=db
    )

    return True, serialize_doc(doc), "Token verified and JIT access granted."

def revoke_jit_token(
    token_id: str,
    admin_id: str,
    admin_name: str,
    reason: str = "Admin manual revocation",
    ip_address: str = "127.0.0.1",
    device_info: str = "Unknown Device",
    browser: str = "Unknown Browser",
    db=None
) -> Tuple[bool, str]:
    """Revokes an active JIT token immediately."""
    if db is None:
        db = get_db()

    doc = db.jit_tokens.find_one({"token_id": token_id})
    if not doc:
        return False, "Token not found."

    if doc["status"] == "Revoked":
        return False, "Token is already revoked."

    now_iso = datetime.now(timezone.utc).isoformat()
    db.jit_tokens.update_one(
        {"token_id": token_id},
        {"$set": {"status": "Revoked", "revoked_at": now_iso, "updated_at": now_iso}}
    )

    create_audit_log(
        event_type="Token Revoked",
        employee_id=doc["employee_id"],
        employee_name=doc["employee_name"],
        admin_id=admin_id,
        admin_name=admin_name,
        token_id=token_id,
        ip_address=ip_address,
        device_info=device_info,
        browser=browser,
        success=True,
        notes=f"Token revoked by admin ({admin_name}). Reason: {reason}",
        db=db
    )
    return True, "Token successfully revoked."

def extend_jit_token(
    token_id: str,
    additional_minutes: float,
    admin_id: str,
    admin_name: str,
    ip_address: str = "127.0.0.1",
    device_info: str = "Unknown Device",
    browser: str = "Unknown Browser",
    db=None
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Extends the expiration duration of an active token."""
    if db is None:
        db = get_db()

    auto_expire_tokens(db=db)

    doc = db.jit_tokens.find_one({"token_id": token_id})
    if not doc:
        return False, None, "Token not found."

    if doc["status"] != "Active":
        return False, serialize_doc(doc), f"Cannot extend token with status '{doc['status']}'."

    try:
        current_exp = datetime.fromisoformat(doc["expires_at"])
    except Exception:
        current_exp = datetime.now(timezone.utc)

    new_exp = current_exp + timedelta(minutes=additional_minutes)
    new_exp_iso = new_exp.isoformat()
    now_iso = datetime.now(timezone.utc).isoformat()

    db.jit_tokens.update_one(
        {"token_id": token_id},
        {"$set": {"expires_at": new_exp_iso, "updated_at": now_iso}}
    )

    doc["expires_at"] = new_exp_iso
    doc["updated_at"] = now_iso

    create_audit_log(
        event_type="Timer Extended",
        employee_id=doc["employee_id"],
        employee_name=doc["employee_name"],
        admin_id=admin_id,
        admin_name=admin_name,
        token_id=token_id,
        ip_address=ip_address,
        device_info=device_info,
        browser=browser,
        success=True,
        notes=f"Expiration extended by {additional_minutes} minutes to {new_exp_iso}.",
        db=db
    )

    return True, serialize_doc(doc), f"Token expiry successfully extended by {additional_minutes} minutes."

def auto_expire_tokens(db=None) -> int:
    """Scans and updates active tokens whose expires_at is past current UTC time."""
    if db is None:
        db = get_db()

    now_iso = datetime.now(timezone.utc).isoformat()
    active_tokens = list(db.jit_tokens.find({"status": "Active"}))
    expired_count = 0

    for doc in active_tokens:
        if doc.get("expires_at") and doc["expires_at"] <= now_iso:
            token_id = doc["token_id"]
            db.jit_tokens.update_one(
                {"token_id": token_id},
                {"$set": {"status": "Expired", "updated_at": now_iso}}
            )
            create_audit_log(
                event_type="Token Expired",
                employee_id=doc["employee_id"],
                employee_name=doc["employee_name"],
                admin_id=doc["admin_id"],
                admin_name=doc["admin_name"],
                token_id=token_id,
                success=True,
                notes="Token automatically marked expired past expiration timestamp.",
                db=db
            )
            expired_count += 1

    return expired_count

def get_jit_tokens(
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
    query: Optional[str] = None,
    db=None
) -> List[Dict[str, Any]]:
    """Retrieves JIT tokens matching search/filter criteria (sans sensitive token_hash)."""
    if db is None:
        db = get_db()

    auto_expire_tokens(db=db)

    filter_dict = {}
    if status and status != "All":
        filter_dict["status"] = status
    if employee_id:
        filter_dict["employee_id"] = employee_id

    tokens = list(db.jit_tokens.find(filter_dict))

    result = []
    for doc in tokens:
        clean_doc = serialize_doc(doc)
        if query:
            q_lower = query.lower()
            searchable = f"{clean_doc.get('token_id', '')} {clean_doc.get('employee_id', '')} {clean_doc.get('employee_name', '')} {clean_doc.get('admin_name', '')}".lower()
            if q_lower not in searchable:
                continue
        result.append(clean_doc)

    result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return result

def get_jit_audit_logs(
    event_type: Optional[str] = None,
    employee_id: Optional[str] = None,
    query: Optional[str] = None,
    db=None
) -> List[Dict[str, Any]]:
    """Retrieves JIT audit logs matching search/filter criteria."""
    if db is None:
        db = get_db()

    filter_dict = {}
    if event_type and event_type != "All":
        filter_dict["event_type"] = event_type
    if employee_id:
        filter_dict["employee_id"] = employee_id

    logs = list(db.jit_audit_logs.find(filter_dict))

    result = []
    for doc in logs:
        clean_doc = serialize_doc(doc)
        if query:
            q_lower = query.lower()
            emp_info = clean_doc.get("employee", {})
            admin_info = clean_doc.get("admin", {})
            searchable = f"{clean_doc.get('token_id', '')} {clean_doc.get('event_type', '')} {clean_doc.get('employee_id', '')} {emp_info.get('name', '')} {admin_info.get('name', '')} {clean_doc.get('notes', '')}".lower()
            if q_lower not in searchable:
                continue
        result.append(clean_doc)

    result.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return result

def get_jit_dashboard_stats(employee_id: Optional[str] = None, db=None) -> Dict[str, Any]:
    """Calculates comprehensive metrics for the JIT Dashboard based on Permanent Audit Trail and Tokens."""
    if db is None:
        db = get_db()

    auto_expire_tokens(db=db)

    filter_dict = {}
    if employee_id:
        filter_dict["employee_id"] = employee_id

    tokens = list(db.jit_tokens.find(filter_dict))
    logs = list(db.jit_audit_logs.find(filter_dict))

    # Derive metrics from Permanent JIT Security Audit Trail & DB tokens
    issued_logs = [l for l in logs if l.get("event_type") == "Token Issued"]
    revoked_logs = [l for l in logs if l.get("event_type") == "Token Revoked"]
    expired_logs = [l for l in logs if l.get("event_type") == "Token Expired"]

    total_tokens = len(tokens)
    active_tokens = sum(1 for t in tokens if t.get("status") == "Active")
    expired_tokens = sum(1 for t in tokens if t.get("status") == "Expired")
    revoked_tokens = sum(1 for t in tokens if t.get("status") == "Revoked")

    def get_sort_key(val):
        if not val:
            return ""
        if isinstance(val, datetime):
            return val.isoformat()
        return str(val)

    sorted_tokens = sorted(tokens, key=lambda x: get_sort_key(x.get("created_at")), reverse=True)
    recently_issued = [serialize_doc(t) for t in sorted_tokens[:5]]

    used_tokens = [t for t in tokens if t.get("last_used")]
    sorted_used = sorted(used_tokens, key=lambda x: get_sort_key(x.get("last_used")), reverse=True)
    recently_used = [serialize_doc(t) for t in sorted_used[:5]]

    perm_counts: Dict[str, int] = {p: 0 for p in ALL_JIT_PERMISSIONS}
    active_tokens_list = [t for t in tokens if t.get("status") == "Active"]

    if active_tokens_list:
        for t in active_tokens_list:
            for p in t.get("granted_permissions", []):
                if p in perm_counts:
                    perm_counts[p] += 1
    elif employee_id:
        emp_rec = db.employees.find_one({"employee_id": employee_id})
        emp_score = float(emp_rec.get("current_score", 100.0)) if emp_rec else 100.0
        if emp_score >= 30.0:
            perm_counts = {p: 1 for p in ALL_JIT_PERMISSIONS}
    else:
        perm_counts = {p: 1 for p in ALL_JIT_PERMISSIONS}

    durations = []
    for t in tokens:
        if t.get("duration") is not None:
            durations.append(float(t["duration"]))
        elif t.get("duration_minutes") is not None:
            durations.append(float(t["duration_minutes"]))
        else:
            try:
                iss = datetime.fromisoformat(t["issued_at"])
                exp = datetime.fromisoformat(t["expires_at"])
                durations.append((exp - iss).total_seconds() / 60.0)
            except Exception:
                pass

    avg_duration_min = round(sum(durations) / len(durations), 1) if durations else 0.0

    now_utc = datetime.now(timezone.utc)
    remaining_times = []
    for t in tokens:
        if t.get("status") == "Active" and t.get("expires_at"):
            try:
                exp_dt = datetime.fromisoformat(t["expires_at"])
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=timezone.utc)
                rem_min = (exp_dt - now_utc).total_seconds() / 60.0
                if rem_min > 0:
                    remaining_times.append(rem_min)
            except Exception:
                pass

    avg_remaining_min = round(sum(remaining_times) / len(remaining_times), 1) if remaining_times else 0.0

    logger.info(f"[DEBUG_JIT_PIPELINE] Dashboard Stats Calculated -> Total: {total_tokens}, Active: {active_tokens}, Expired: {expired_tokens}, Revoked: {revoked_tokens}, Avg Duration: {avg_duration_min}m, Avg Remaining: {avg_remaining_min}m")

    return {
        "total_tokens": total_tokens,
        "active_tokens": active_tokens,
        "expired_tokens": expired_tokens,
        "revoked_tokens": revoked_tokens,
        "average_session_duration_minutes": avg_duration_min,
        "average_remaining_time_minutes": avg_remaining_min,
        "recently_issued": recently_issued,
        "recently_used": recently_used,
        "permission_distribution": perm_counts,
        "total_audit_logs": len(logs)
    }
