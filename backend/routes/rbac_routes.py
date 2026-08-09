"""
GarudaAI Enterprise RBAC Routes & Endpoints Blueprint
======================================================

Provides REST API routes for:
- Role & Permission Matrix Inspection
- User Account Management (CEO only: Create, Delete, Reset Password)
- Audit Log Inspection (Auditor / CEO / Security Manager)
- Analyst Investigation Escalation Workflow
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from flask import Blueprint, request, jsonify

try:
    from backend.db_client import get_db
    from backend.database.rbac_db import (
        ROLES_DEFINITION, get_all_audit_logs, log_audit_event, get_role_permissions
    )
    from backend.database.auth_db import (
        create_user, get_user_by_email, unlock_account, serialize_user
    )
    from backend.security.rbac_middleware import require_permission, get_current_session
    from backend.security.password_service import encrypt_password
except ImportError:
    from db_client import get_db
    from database.rbac_db import (
        ROLES_DEFINITION, get_all_audit_logs, log_audit_event, get_role_permissions
    )
    from database.auth_db import (
        create_user, get_user_by_email, unlock_account, serialize_user
    )
    from security.rbac_middleware import require_permission, get_current_session
    from security.password_service import encrypt_password

logger = logging.getLogger("garudaai.rbac_routes")

rbac_bp = Blueprint("rbac", __name__, url_prefix="/api/rbac")


@rbac_bp.route("/roles", methods=["GET"])
@require_permission("view_roles")
def get_roles():
    """Returns matrix of system roles, hierarchy levels, descriptions, and permissions."""
    return jsonify({
        "success": True,
        "roles": list(ROLES_DEFINITION.values())
    }), 200


@rbac_bp.route("/users", methods=["GET"])
@require_permission("view_users")
def get_users():
    """Fetches list of all user accounts in system."""
    db = get_db()
    try:
        users = list(db.users.find({}, {"password": 0, "private_key": 0}))
        serialized = [serialize_user(u) for u in users]
        return jsonify({
            "success": True,
            "users": serialized
        }), 200
    except Exception as e:
        logger.error(f"Error fetching users list: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rbac_bp.route("/users", methods=["POST"])
@require_permission("create_users")
def api_create_user():
    """CEO-only: Creates new enterprise user account."""
    session = get_current_session()
    db = get_db()
    data = request.json or {}
    
    full_name = data.get("full_name")
    email = data.get("email")
    employee_id = data.get("employee_id")
    department = data.get("department", "General Management")
    designation = data.get("designation", "Security Staff")
    role = data.get("role", "Security Analyst")
    password = data.get("password")

    if not full_name or not email or not employee_id or not password:
        return jsonify({
            "success": False, 
            "error": "full_name, email, employee_id, and password are required."
        }), 400

    if role not in ROLES_DEFINITION:
        return jsonify({
            "success": False,
            "error": f"Invalid role '{role}'. Allowed roles: {list(ROLES_DEFINITION.keys())}"
        }), 400

    try:
        res = create_user(
            full_name=full_name,
            email=email,
            employee_id=employee_id,
            department=department,
            role=role,
            password=password,
            db=db
        )
        if res.get("success"):
            # Update designation
            db.users.update_one({"email": email.strip().lower()}, {"$set": {"designation": designation}})
            
            log_audit_event(
                action="User Created",
                user_id=session.get("user_id") if session else "CEO",
                user_email=session.get("email") if session else "ceo@garudaai.com",
                user_role=session.get("role") if session else "CEO",
                status="SUCCESS",
                details=f"Created user '{email}' with role '{role}' in department '{department}'",
                ip_address=request.remote_addr or "127.0.0.1",
                db=db
            )
            return jsonify(res), 201
        else:
            return jsonify(res), 400
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rbac_bp.route("/users/<user_id>", methods=["DELETE"])
@require_permission("delete_users")
def api_delete_user(user_id):
    """CEO-only: Deletes user account."""
    session = get_current_session()
    db = get_db()
    
    try:
        query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"employee_id": user_id}
        user = db.users.find_one(query)
        if not user:
            return jsonify({"success": False, "error": "User account not found."}), 404
            
        target_email = user.get("email")
        
        # Prevent self-deletion of primary CEO
        if target_email == "ceo@garudaai.com" or target_email == session.get("email"):
            return jsonify({"success": False, "error": "Cannot delete primary CEO or active self account."}), 403

        db.users.delete_one(query)
        db.user_sessions.delete_many({"user_id": str(user["_id"])})
        
        log_audit_event(
            action="User Deleted",
            user_id=session.get("user_id") if session else "CEO",
            user_email=session.get("email") if session else "ceo@garudaai.com",
            user_role=session.get("role") if session else "CEO",
            status="SUCCESS",
            details=f"Deleted user account '{target_email}'",
            ip_address=request.remote_addr or "127.0.0.1",
            db=db
        )
        return jsonify({"success": True, "message": f"User account '{target_email}' successfully deleted."}), 200
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rbac_bp.route("/users/<user_id>/reset-password", methods=["POST"])
@require_permission("reset_passwords")
def api_reset_password(user_id):
    """CEO-only: Resets password for specified user account."""
    session = get_current_session()
    db = get_db()
    data = request.json or {}
    new_password = data.get("new_password")
    
    if not new_password or len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters."}), 400
        
    try:
        query = {"_id": ObjectId(user_id)} if ObjectId.is_valid(user_id) else {"employee_id": user_id}
        user = db.users.find_one(query)
        if not user:
            return jsonify({"success": False, "error": "User account not found."}), 404
            
        pqc_payload = encrypt_password(new_password)
        db.users.update_one(query, {"$set": {
            "password": pqc_payload["encrypted_password"],
            "encrypted_password": pqc_payload["encrypted_password"],
            "nonce": pqc_payload["nonce"],
            "authentication_tag": pqc_payload["authentication_tag"],
            "encapsulated_secret": pqc_payload["encapsulated_secret"],
            "private_key": pqc_payload["private_key"],
            "algorithm": pqc_payload["algorithm"],
            "failed_login_attempts": 0,
            "account_locked": False
        }})
        
        log_audit_event(
            action="Password Reset",
            user_id=session.get("user_id") if session else "CEO",
            user_email=session.get("email") if session else "ceo@garudaai.com",
            user_role=session.get("role") if session else "CEO",
            status="SUCCESS",
            details=f"Admin password reset executed for user '{user.get('email')}'",
            ip_address=request.remote_addr or "127.0.0.1",
            db=db
        )
        return jsonify({"success": True, "message": f"Password reset successfully for '{user.get('email')}'."}), 200
    except Exception as e:
        logger.error(f"Error resetting password for {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rbac_bp.route("/users/<user_id>/unlock", methods=["POST"])
@require_permission("unlock_employees")
def api_unlock_user(user_id):
    """Unlocks locked user / employee account."""
    session = get_current_session()
    db = get_db()
    try:
        res = unlock_account(user_id, db=db)
        if res.get("success"):
            log_audit_event(
                action="Unlocked Employee Account",
                user_id=session.get("user_id") if session else "ADMIN",
                user_email=session.get("email") if session else "admin@garuda.ai",
                user_role=session.get("role") if session else "Security Manager",
                status="SUCCESS",
                details=f"Unlocked user account '{user_id}'",
                ip_address=request.remote_addr or "127.0.0.1",
                db=db
            )
            return jsonify(res), 200
        else:
            return jsonify(res), 400
    except Exception as e:
        logger.error(f"Error unlocking user {user_id}: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@rbac_bp.route("/audit-logs", methods=["GET"])
@require_permission("audit_logs")
def api_get_audit_logs():
    """Returns audit log history for Auditor / CEO / Security Manager."""
    role_filter = request.args.get("role")
    status_filter = request.args.get("status")
    limit = int(request.args.get("limit", 100))
    
    db = get_db()
    logs = get_all_audit_logs(limit=limit, role_filter=role_filter, status_filter=status_filter, db=db)
    return jsonify({
        "success": True,
        "audit_logs": logs
    }), 200


@rbac_bp.route("/escalate-investigation", methods=["POST"])
@require_permission("create_investigation_report")
def api_escalate_investigation():
    """
    Security Analyst / Manager escalation endpoint.
    Creates an investigation report note and escalates it to Security Manager.
    """
    session = get_current_session()
    db = get_db()
    data = request.json or {}
    
    employee_id = data.get("employee_id")
    title = data.get("title", "Suspicious Insider Activity Report")
    summary = data.get("summary", "")
    threat_level = data.get("threat_level", "High")
    recommended_action = data.get("recommended_action", "Recommend Employee Lock & JIT Review")
    
    if not employee_id or not summary:
        return jsonify({"success": False, "error": "employee_id and summary are required."}), 400
        
    escalation_doc = {
        "report_id": f"ESC-REP-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "employee_id": employee_id,
        "title": title,
        "summary": summary,
        "threat_level": threat_level,
        "recommended_action": recommended_action,
        "escalated_by": session.get("email") if session else "security.analyst@garudaai.com",
        "escalated_by_name": session.get("full_name") if session else "Security Analyst",
        "escalated_by_role": session.get("role") if session else "Security Analyst",
        "timestamp": datetime.now(timezone.utc),
        "status": "Escalated to Security Manager",
        "assigned_to": "Security Manager"
    }
    
    db.investigation_reports.insert_one(escalation_doc)
    
    # Audit log
    log_audit_event(
        action="Escalated Investigation Report",
        user_id=session.get("user_id") if session else "ANALYST",
        user_email=session.get("email") if session else "security.analyst@garudaai.com",
        user_role=session.get("role") if session else "Security Analyst",
        status="SUCCESS",
        details=f"Escalated investigation report for employee '{employee_id}' (Threat: {threat_level}) to Security Manager",
        ip_address=request.remote_addr or "127.0.0.1",
        db=db
    )
    
    return jsonify({
        "success": True,
        "message": f"Investigation report successfully escalated to Security Manager.",
        "report": {
            "report_id": escalation_doc["report_id"],
            "employee_id": employee_id,
            "status": escalation_doc["status"],
            "timestamp": escalation_doc["timestamp"].isoformat()
        }
    }), 201
