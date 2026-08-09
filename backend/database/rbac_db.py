"""
GarudaAI Enterprise Role-Based Access Control (RBAC) Database Layer
====================================================================

This module manages all collections required for enterprise RBAC:
- 'roles': System role definitions and hierarchy levels
- 'permissions': Granular system permissions
- 'role_permissions': Mapping between roles and permission lists
- 'user_sessions': Active session tracking with inactivity auto-expiry
- 'audit_logs': Immutable action and access audit trails
"""

import logging
import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from pymongo.errors import PyMongoError

try:
    from backend.db_client import get_db
    from backend.database.auth_db import create_user, verify_user_password, get_user_by_email
except ImportError:
    from db_client import get_db
    from database.auth_db import create_user, verify_user_password, get_user_by_email

logger = logging.getLogger("garudaai.rbac_db")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [RBAC_DB] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Master Definition of Roles & System Permissions
ROLES_DEFINITION = {
    "CEO": {
        "role_id": "role_ceo",
        "name": "CEO",
        "description": "Highest Privilege. Complete unrestricted access across all platform modules & system settings.",
        "level": 1,
        "permissions": [
            "view_dashboard", "view_employees", "view_timeline", "view_trust_score",
            "view_ai_investigation", "view_sandbox", "view_hmi", "view_db_protection",
            "view_reports", "view_employee_monitoring", "generate_jit_tokens",
            "unlock_employees", "lock_employees", "edit_employee", "delete_employee",
            "modify_trust_score", "create_notes", "escalate_case", "delete_users",
            "modify_system_settings", "manage_api_keys", "user_management",
            "database_settings", "security_config", "ai_chatbot"
        ]
    },
    "HR": {
        "role_id": "role_hr",
        "name": "HR",
        "description": "Human Resources Role. Access to employee profiles, directory, trust scores, timelines, reports, and AI chatbot.",
        "level": 2,
        "permissions": [
            "view_employees", "view_timeline", "view_trust_score", "view_reports", "ai_chatbot"
        ]
    },
    "Security Manager": {
        "role_id": "role_sec_mgr",
        "name": "Security Manager",
        "description": "SOC Security Operations. Full threat dashboard, AI investigation, JIT token issuance, and employee unlock authority.",
        "level": 2,
        "permissions": [
            "view_dashboard", "view_employees", "view_timeline", "view_trust_score",
            "view_ai_investigation", "view_sandbox", "view_hmi", "view_db_protection",
            "view_reports", "view_employee_monitoring", "generate_jit_tokens",
            "unlock_employees", "lock_employees", "create_notes", "escalate_case", "ai_chatbot"
        ]
    },
    "Security Analyst": {
        "role_id": "role_sec_analyst",
        "name": "Security Analyst",
        "description": "Read-only Investigation Role. Investigates threats, inspects telemetry, creates notes, escalates cases, and views reports.",
        "level": 3,
        "permissions": [
            "view_dashboard", "view_employees", "view_timeline", "view_trust_score",
            "view_ai_investigation", "view_sandbox", "view_hmi", "view_reports",
            "create_notes", "escalate_case", "ai_chatbot"
        ]
    }
}

SEED_USERS = [
    {
        "full_name": "Chief Executive Officer",
        "email": "ceo@garudaai.com",
        "employee_id": "GAR-CEO-001",
        "department": "Executive Board",
        "designation": "Chief Executive Officer",
        "role": "CEO",
        "password": "Ceo@Garuda2026!"
    },
    {
        "full_name": "Lead Security Administrator",
        "email": "admin@garuda.ai",
        "employee_id": "GAR-0001",
        "department": "SOC Executive",
        "designation": "System Administrator",
        "role": "CEO",
        "password": "password123"
    },
    {
        "full_name": "Eleanor Vance (HR Manager)",
        "email": "hr@garudaai.com",
        "employee_id": "GAR-HR-002",
        "department": "Human Resources",
        "designation": "HR Security Liaison",
        "role": "HR",
        "password": "Hr@Garuda2026!"
    },
    {
        "full_name": "Marcus Vance (Security Lead)",
        "email": "security.manager@garudaai.com",
        "employee_id": "GAR-SEC-003",
        "department": "SOC & Incident Response",
        "designation": "Security Manager",
        "role": "Security Manager",
        "password": "SecManager@Garuda2026!"
    },
    {
        "full_name": "Sarah Connor (SOC Analyst)",
        "email": "security.analyst@garudaai.com",
        "employee_id": "GAR-SEC-004",
        "department": "Cyber Threat Intelligence",
        "designation": "Senior Security Analyst",
        "role": "Security Analyst",
        "password": "SecAnalyst@Garuda2026!"
    }
]

SESSION_TIMEOUT_MINUTES = 60  # Automatic expiry after 60 mins of inactivity


def _resolve_db(db=None):
    if db is not None:
        return db
    return get_db()


def init_rbac_db(db=None):
    """
    Initializes RBAC collections, creates Mongo indexes, and seeds default roles and user accounts.
    """
    target_db = _resolve_db(db)
    try:
        # Create indexes
        target_db.roles.create_index([("name", 1)], unique=True)
        target_db.user_sessions.create_index([("session_id", 1)], unique=True)
        target_db.user_sessions.create_index([("expires_at", 1)])
        target_db.audit_logs.create_index([("timestamp", -1)])
        target_db.audit_logs.create_index([("user_email", 1)])

        # Seed Roles & Permissions
        for role_name, role_data in ROLES_DEFINITION.items():
            target_db.roles.update_one(
                {"name": role_name},
                {"$set": {
                    "role_id": role_data["role_id"],
                    "name": role_data["name"],
                    "description": role_data["description"],
                    "level": role_data["level"],
                    "permissions": role_data["permissions"],
                    "updated_at": datetime.now(timezone.utc)
                }},
                upsert=True
            )

        # Seed Users
        for user_info in SEED_USERS:
            existing = target_db.users.find_one({"email": user_info["email"]})
            if not existing:
                create_user(
                    full_name=user_info["full_name"],
                    email=user_info["email"],
                    employee_id=user_info["employee_id"],
                    department=user_info["department"],
                    role=user_info["role"],
                    password=user_info["password"],
                    db=target_db
                )
            # Ensure designation field & role are updated
            target_db.users.update_one(
                {"email": user_info["email"]},
                {"$set": {
                    "designation": user_info["designation"],
                    "role": user_info["role"],
                    "mfa_enabled": False,
                    "is_active": True,
                    "account_locked": False
                }}
            )

        logger.info("Successfully initialized RBAC database, roles matrix, and seed user accounts.")
        return {"success": True, "message": "RBAC system database initialized."}
    except Exception as e:
        logger.error(f"Error during init_rbac_db: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_role_permissions(role_name, db=None):
    """Returns permission list for a given role name."""
    target_db = _resolve_db(db)
    if role_name in ROLES_DEFINITION:
        return ROLES_DEFINITION[role_name]["permissions"]
    
    role_doc = target_db.roles.find_one({"name": role_name})
    if role_doc and "permissions" in role_doc:
        return role_doc["permissions"]
    return []


def create_user_session(user_doc, ip_address="127.0.0.1", db=None):
    """
    Creates an active session in 'user_sessions' collection for an authenticated user.
    """
    target_db = _resolve_db(db)
    session_id = f"garuda-session-{uuid.uuid4().hex}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    
    role = user_doc.get("role", "Security Analyst")
    permissions = get_role_permissions(role, target_db)

    session_doc = {
        "session_id": session_id,
        "user_id": str(user_doc.get("_id")),
        "email": user_doc.get("email"),
        "employee_id": user_doc.get("employee_id"),
        "full_name": user_doc.get("full_name"),
        "department": user_doc.get("department"),
        "designation": user_doc.get("designation", user_doc.get("role")),
        "role": role,
        "permissions": permissions,
        "login_time": now,
        "last_activity": now,
        "expires_at": expires_at,
        "is_active": True,
        "ip_address": ip_address
    }

    try:
        # Invalidate old sessions for this user
        target_db.user_sessions.update_many(
            {"user_id": str(user_doc.get("_id")), "is_active": True},
            {"$set": {"is_active": False}}
        )
        target_db.user_sessions.insert_one(session_doc)
        
        # Audit Log
        log_audit_event(
            action="User Login",
            user_id=str(user_doc.get("_id")),
            user_email=user_doc.get("email"),
            user_role=role,
            status="SUCCESS",
            details=f"Successful authentication for {user_doc.get('email')} ({role})",
            ip_address=ip_address,
            db=target_db
        )
        return session_doc
    except Exception as e:
        logger.error(f"Error creating user session for {user_doc.get('email')}: {e}")
        return None


def validate_session(session_id_or_token, db=None):
    """
    Validates session ID or token, updates last_activity, and checks expiry.
    Returns session doc dict if valid, else None.
    """
    if not session_id_or_token:
        return None

    target_db = _resolve_db(db)
    
    # Clean up bearer prefix
    clean_id = session_id_or_token.replace("Bearer ", "").replace("garuda-token-", "garuda-session-").strip()
    
    session = target_db.user_sessions.find_one({"session_id": clean_id, "is_active": True})
    
    if not session and clean_id.startswith("garuda-token-"):
        uid = clean_id.replace("garuda-token-", "")
        session = target_db.user_sessions.find_one({"user_id": uid, "is_active": True})

    if not session:
        # Fallback check users table directly for backward compatibility
        raw_uid = session_id_or_token.replace("Bearer ", "").replace("garuda-token-", "").strip()
        if ObjectId.is_valid(raw_uid):
            user = target_db.users.find_one({"_id": ObjectId(raw_uid)})
            if user:
                role = user.get("role", "Security Analyst")
                perms = get_role_permissions(role, target_db)
                return {
                    "session_id": f"garuda-session-{raw_uid}",
                    "user_id": str(user["_id"]),
                    "email": user.get("email"),
                    "employee_id": user.get("employee_id"),
                    "full_name": user.get("full_name"),
                    "department": user.get("department"),
                    "designation": user.get("designation", role),
                    "role": role,
                    "permissions": perms,
                    "is_active": True
                }
        return None

    now = datetime.now(timezone.utc)
    
    # Check inactivity timeout expiry
    last_act = session.get("last_activity")
    if isinstance(last_act, datetime):
        if last_act.tzinfo is None:
            last_act = last_act.replace(tzinfo=timezone.utc)
        if (now - last_act) > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            target_db.user_sessions.update_one({"_id": session["_id"]}, {"$set": {"is_active": False}})
            logger.info(f"Session {clean_id} expired due to inactivity.")
            return None

    # Refresh activity timestamp
    new_expires = now + timedelta(minutes=SESSION_TIMEOUT_MINUTES)
    target_db.user_sessions.update_one(
        {"_id": session["_id"]},
        {"$set": {"last_activity": now, "expires_at": new_expires}}
    )
    
    session["last_activity"] = now
    session["expires_at"] = new_expires
    return session


def log_audit_event(action, user_id="SYSTEM", user_email="system@garuda.ai", user_role="SYSTEM", status="SUCCESS", details="", ip_address="127.0.0.1", db=None):
    """
    Inserts a new structured audit log record in 'audit_logs' collection.
    """
    target_db = _resolve_db(db)
    now = datetime.now(timezone.utc)
    
    audit_doc = {
        "log_id": f"AUD-{uuid.uuid4().hex[:10].upper()}",
        "timestamp": now,
        "action": action,
        "user_id": str(user_id),
        "user_email": str(user_email),
        "user_role": str(user_role),
        "status": status,
        "details": details,
        "ip_address": ip_address
    }
    try:
        target_db.audit_logs.insert_one(audit_doc)
        logger.info(f"AUDIT LOG [{status}] {action} by {user_email} ({user_role}): {details}")
        return audit_doc
    except Exception as e:
        logger.error(f"Failed to record audit log: {e}")
        return None


def get_all_audit_logs(limit=100, role_filter=None, status_filter=None, db=None):
    """Retrieves list of audit logs with optional filters."""
    target_db = _resolve_db(db)
    query = {}
    if role_filter and role_filter != "All":
        query["user_role"] = role_filter
    if status_filter and status_filter != "All":
        query["status"] = status_filter
        
    try:
        cursor = target_db.audit_logs.find(query, {"_id": 0})
        if hasattr(cursor, "sort"):
            try:
                cursor = cursor.sort("timestamp", -1)
            except Exception:
                pass
        if hasattr(cursor, "limit"):
            try:
                cursor = cursor.limit(limit)
            except Exception:
                pass
        
        logs = list(cursor)
        if isinstance(logs, list):
            logs.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
            logs = logs[:limit]

        for l in logs:
            if "_id" in l:
                l["_id"] = str(l["_id"])
            if isinstance(l.get("timestamp"), datetime):
                l["timestamp"] = l["timestamp"].isoformat()
        return logs
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        return []
