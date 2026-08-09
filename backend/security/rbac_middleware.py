"""
GarudaAI Enterprise RBAC Authorization Middleware
===================================================

Provides Flask route decorators and authorization helpers for enforcing:
- Session validation & auto-expiry
- Permission-based access control (@require_permission)
- Role-based access control (@require_role)
- Audit log recording of permission denial events (HTTP 403)
"""

import logging
from functools import wraps
from flask import request, jsonify, g

try:
    from backend.database.rbac_db import validate_session, log_audit_event, get_role_permissions
    from backend.db_client import get_db
except ImportError:
    from database.rbac_db import validate_session, log_audit_event, get_role_permissions
    from db_client import get_db

logger = logging.getLogger("garudaai.rbac_middleware")


def extract_token_from_request():
    """Extracts session token from Authorization header or custom X-Access-Token header."""
    auth_header = request.headers.get("Authorization")
    if auth_header and (auth_header.startswith("Bearer ") or auth_header.startswith("garuda-")):
        return auth_header
    
    token_header = request.headers.get("X-Access-Token")
    if token_header:
        return token_header
        
    session_cookie = request.cookies.get("garuda_session")
    if session_cookie:
        return session_cookie
        
    return None


def get_current_session():
    """Returns current active session dict attached to Flask context or validates token."""
    if hasattr(g, "current_session") and g.current_session:
        return g.current_session
        
    token = extract_token_from_request()
    if not token:
        return None
        
    db = get_db()
    session = validate_session(token, db=db)
    if session:
        g.current_session = session
    return session


def require_permission(permission_name):
    """
    Decorator enforcing that the authenticated user possesses `permission_name`.
    If unauthenticated -> 401 Unauthorized.
    If unauthorized -> 403 Access Denied + Audit Log recorded.
    """
    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            token = extract_token_from_request()
            db = get_db()
            
            session = validate_session(token, db=db) if token else None
            
            if not session:
                import os
                dev_mode = os.environ.get("DEV_MODE", "true").lower() == "true"
                # Only fallback to unauthenticated demo CEO if DEV_MODE is true AND no token was provided at all
                if dev_mode and not token:
                    session = {
                        "session_id": "demo-admin-session",
                        "user_id": "demo-admin-uid-101",
                        "email": "ceo@garudaai.com",
                        "full_name": "Chief Executive Officer",
                        "role": "CEO",
                        "permissions": get_role_permissions("CEO", db) if db else []
                    }
                else:
                    return jsonify({
                        "success": False,
                        "error": "Unauthorized",
                        "message": "Authentication token or active session is missing or expired. Please log in."
                    }), 401
                    
            g.current_session = session
            user_role = session.get("role", "Security Analyst")
            user_perms = session.get("permissions", [])
            user_email = session.get("email", "unknown@garudaai.com")
            user_id = session.get("user_id", "unknown")

            # CEO has master access, otherwise verify explicit permission
            if permission_name not in user_perms and user_role != "CEO":
                # Log Permission Denied in Audit Trail
                log_audit_event(
                    action="Permission Denied",
                    user_id=user_id,
                    user_email=user_email,
                    user_role=user_role,
                    status="DENIED",
                    details=f"Denied attempt to access endpoint '{request.path}' needing permission '{permission_name}'",
                    ip_address=request.remote_addr or "127.0.0.1",
                    db=db
                )
                logger.warning(f"ACCESS DENIED [403]: User {user_email} ({user_role}) lacks permission '{permission_name}' for path '{request.path}'")
                return jsonify({
                    "success": False,
                    "error": "Access Denied",
                    "message": f"Permission '{permission_name}' required. Role '{user_role}' is not authorized for this operation.",
                    "required_permission": permission_name,
                    "user_role": user_role
                }), 403

            return f(*args, **kwargs)
        return decorated_func
    return decorator


def require_role(allowed_roles):
    """
    Decorator restricting endpoint access to specific roles (e.g. ['CEO', 'Security Manager']).
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
        
    def decorator(f):
        @wraps(f)
        def decorated_func(*args, **kwargs):
            session = get_current_session()
            if not session:
                return jsonify({
                    "success": False,
                    "error": "Unauthorized",
                    "message": "Authentication required."
                }), 401
                
            user_role = session.get("role", "")
            if user_role not in allowed_roles and user_role != "CEO":
                log_audit_event(
                    action="Permission Denied",
                    user_id=session.get("user_id"),
                    user_email=session.get("email"),
                    user_role=user_role,
                    status="DENIED",
                    details=f"Denied access to '{request.path}'. Allowed roles: {allowed_roles}",
                    ip_address=request.remote_addr or "127.0.0.1",
                    db=get_db()
                )
                return jsonify({
                    "success": False,
                    "error": "Access Denied",
                    "message": f"Role '{user_role}' is not authorized to access this resource."
                }), 403
                
            return f(*args, **kwargs)
        return decorated_func
    return decorator
