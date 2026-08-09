"""
SentinelAI JIT Access Control & Security Middleware
===================================================

Provides permission validation, token expiration verification, rate limiting,
and replay attack protection middleware for Flask API endpoints.
"""

import time
import logging
from functools import wraps
from typing import Dict, List, Tuple
from flask import request, jsonify, g

try:
    from backend.database.jit_db import verify_and_use_jit_token, auto_expire_tokens, ALL_JIT_PERMISSIONS
    from backend.db_client import get_db
except ImportError:
    from database.jit_db import verify_and_use_jit_token, auto_expire_tokens, ALL_JIT_PERMISSIONS
    from db_client import get_db

logger = logging.getLogger("sentinelai.jit_middleware")

# Simple in-memory IP/Employee Rate Limiter for JIT verification attempts (Max 5 per 60 seconds)
_verification_attempts: Dict[str, List[float]] = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 60.0

def is_rate_limited(key: str) -> bool:
    """Checks if an IP or Employee ID has exceeded the JIT verification attempt rate limit."""
    now = time.time()
    attempts = _verification_attempts.get(key, [])
    # Keep attempts within sliding window
    attempts = [t for t in attempts if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _verification_attempts[key] = attempts

    if len(attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
        return True
    
    attempts.append(now)
    _verification_attempts[key] = attempts
    return False

def extract_jit_token_from_request() -> str:
    """Extracts JIT candidate token string from headers or request payload."""
    token = request.headers.get("X-JIT-Token")
    if not token:
        token = request.headers.get("X-Access-Token")
    if not token and request.is_json:
        payload = request.get_json(silent=True) or {}
        token = payload.get("jit_token") or payload.get("token")
    if not token:
        token = request.args.get("jit_token")
    return token.strip() if token else ""

def require_jit_permission(required_permission: str):
    """
    Decorator for Flask route handlers requiring specific JIT token scope.
    Validates token presence, hashing match, status, expiration, and permission inclusion.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            candidate_token = extract_jit_token_from_request()
            if not candidate_token:
                # If no JIT token header present, allow standard auth to handle unless JIT is mandatory
                return jsonify({
                    "error": f"Missing JIT Token. Scope '{required_permission}' requires an active JIT token header (X-JIT-Token)."
                }), 401

            db = get_db()
            is_valid, token_doc, msg = verify_and_use_jit_token(
                plain_token=candidate_token,
                ip_address=request.remote_addr or "127.0.0.1",
                device_info=request.user_agent.string if request.user_agent else "Unknown",
                browser=request.user_agent.browser if request.user_agent else "Unknown",
                db=db
            )

            if not is_valid:
                return jsonify({
                    "error": f"JIT Security Violation: {msg}",
                    "permission_required": required_permission
                }), 403

            # Check if required_permission is present in token's granted_permissions
            granted = token_doc.get("granted_permissions", [])
            access_type = token_doc.get("access_type", "")
            access_level = token_doc.get("accessLevel", "FULL" if access_type == "Full Access" else "LIMITED")

            if access_level == "FULL" or access_type == "Full Access":
                is_full = True
            elif access_level == "LIMITED" or access_type == "Limited Access":
                is_full = False
            else:
                return jsonify({
                    "error": "Invalid permission configuration: An employee cannot have Limited and Full Access simultaneously.",
                    "permission_required": required_permission
                }), 403

            if not is_full and required_permission not in granted:
                return jsonify({
                    "error": f"Forbidden: JIT token scope does not include required permission '{required_permission}'.",
                    "granted_permissions": granted,
                    "permission_required": required_permission
                }), 403

            # Store active JIT token context in Flask request 'g'
            g.jit_token = token_doc
            return f(*args, **kwargs)
        return decorated_function
    return decorator
