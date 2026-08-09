"""
GarudaAI Enterprise Authentication Database Layer
=================================================

This module manages all user authentication database operations for GarudaAI,
including user creation, retrieval by email/employee_id, last login updates,
failed login attempt handling, and account locking mechanisms.

Collection: 'users'
Schema:
{
    "_id": ObjectId,
    "full_name": str,
    "email": str (Unique),
    "employee_id": str (Unique),
    "department": str,
    "role": str,
    "password": str (Hashed),
    "created_at": datetime,
    "last_login": datetime or None,
    "is_active": bool,
    "failed_login_attempts": int,
    "account_locked": bool
}
"""

import logging
from datetime import datetime, timezone
from bson import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from werkzeug.security import generate_password_hash, check_password_hash

try:
    from backend.db_client import get_db
    from backend.security.password_service import encrypt_password, verify_pqc_password, decrypt_password
except ImportError:
    from db_client import get_db
    from security.password_service import encrypt_password, verify_pqc_password, decrypt_password

# Set up module logger
logger = logging.getLogger("garudaai.auth_db")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [AuthDB] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def _resolve_db(db=None):
    """Internal helper to resolve database connection."""
    if db is not None:
        return db
    return get_db()


def serialize_user(user_doc, include_password=False):
    """
    Converts a MongoDB user document into a JSON-serializable dictionary.
    
    :param user_doc: Dict or MongoDB document.
    :param include_password: If False (default), strips password & private_key for security.
    :return: Clean JSON-serializable dictionary.
    """
    if not user_doc:
        return None

    clean_doc = {}
    for key, val in user_doc.items():
        if key in ["password", "private_key"] and not include_password:
            continue
        if isinstance(val, ObjectId):
            clean_doc[key] = str(val)
        elif isinstance(val, datetime):
            clean_doc[key] = val.isoformat()
        else:
            clean_doc[key] = val

    # Ensure required schema fields exist with defaults if missing
    clean_doc["_id"] = str(user_doc.get("_id")) if "_id" in user_doc else None
    clean_doc["full_name"] = str(user_doc.get("full_name", ""))
    clean_doc["email"] = str(user_doc.get("email", ""))
    clean_doc["employee_id"] = str(user_doc.get("employee_id", ""))
    clean_doc["department"] = str(user_doc.get("department", ""))
    clean_doc["role"] = str(user_doc.get("role", ""))
    clean_doc["is_active"] = bool(user_doc.get("is_active", True))
    clean_doc["failed_login_attempts"] = int(user_doc.get("failed_login_attempts", 0))
    clean_doc["account_locked"] = bool(user_doc.get("account_locked", False))

    if "created_at" in user_doc:
        val = user_doc["created_at"]
        clean_doc["created_at"] = val.isoformat() if isinstance(val, datetime) else str(val)
    else:
        clean_doc["created_at"] = None

    if "last_login" in user_doc and user_doc["last_login"] is not None:
        val = user_doc["last_login"]
        clean_doc["last_login"] = val.isoformat() if isinstance(val, datetime) else str(val)
    else:
        clean_doc["last_login"] = None

    return clean_doc


def init_auth_db(db=None):
    """
    Creates necessary MongoDB unique indexes on the 'users' collection for 'email' and 'employee_id'.

    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    try:
        users_coll = target_db.users
        users_coll.create_index([("email", 1)], unique=True)
        users_coll.create_index([("employee_id", 1)], unique=True)
        logger.info("Successfully verified/created unique MongoDB indexes for 'email' and 'employee_id'.")
        return {
            "success": True,
            "message": "MongoDB unique indexes created successfully for 'users' collection."
        }
    except Exception as e:
        logger.error(f"Failed to create MongoDB indexes on 'users' collection: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Database index creation error: {str(e)}"
        }


def create_user(full_name, email, employee_id, department, role, password, is_active=True, db=None):
    """
    Creates a new user document in the 'users' collection using ML-KEM-768 PQC Encryption.

    :param full_name: User's full name (str).
    :param email: Unique email address (str).
    :param employee_id: Unique employee ID (str).
    :param department: Department name (str).
    :param role: System/Org role (str).
    :param password: Plain-text password string.
    :param is_active: Initial account status (bool, default True).
    :param db: Database instance (optional).
    :return: JSON response dictionary containing created user metadata or error details.
    """
    target_db = _resolve_db(db)
    
    # Input Validation
    if not email or not isinstance(email, str) or "@" not in email:
        logger.warning("Attempted to create user with invalid email format.")
        return {"success": False, "error": "Invalid email address format."}

    if not employee_id or not str(employee_id).strip():
        logger.warning("Attempted to create user without employee_id.")
        return {"success": False, "error": "Employee ID is required."}

    if not password:
        logger.warning("Attempted to create user without password.")
        return {"success": False, "error": "Password is required."}

    clean_email = email.strip().lower()
    clean_emp_id = str(employee_id).strip()

    # Post-Quantum Cryptography Encryption Workflow (ML-KEM-768 + HKDF-SHA256 + AES-256-GCM)
    try:
        pqc_payload = encrypt_password(password)
    except Exception as e:
        logger.error(f"PQC Password Encryption error for {clean_email}: {e}", exc_info=True)
        return {"success": False, "error": f"Quantum password encryption failed: {str(e)}"}

    now = datetime.now(timezone.utc)

    user_doc = {
        "full_name": str(full_name).strip(),
        "email": clean_email,
        "employee_id": clean_emp_id,
        "department": str(department).strip(),
        "role": str(role).strip(),
        "password": pqc_payload["encrypted_password"],
        "encrypted_password": pqc_payload["encrypted_password"],
        "nonce": pqc_payload["nonce"],
        "authentication_tag": pqc_payload["authentication_tag"],
        "encapsulated_secret": pqc_payload["encapsulated_secret"],
        "private_key": pqc_payload["private_key"],
        "algorithm": pqc_payload["algorithm"],
        "created_at": now,
        "last_login": None,
        "is_active": bool(is_active),
        "failed_login_attempts": 0,
        "account_locked": False
    }

    try:
        # Ensure indexes are active before insertion
        init_auth_db(target_db)

        # Check existing user explicitly for clearer error handling
        if target_db.users.find_one({"email": clean_email}):
            logger.warning(f"User creation failed: email '{clean_email}' already exists.")
            return {"success": False, "error": f"User with email '{clean_email}' already exists."}

        if target_db.users.find_one({"employee_id": clean_emp_id}):
            logger.warning(f"User creation failed: employee_id '{clean_emp_id}' already exists.")
            return {"success": False, "error": f"User with employee ID '{clean_emp_id}' already exists."}

        result = target_db.users.insert_one(user_doc)
        inserted_id = getattr(result, "inserted_id", user_doc.get("_id"))
        user_doc["_id"] = inserted_id

        logger.info(f"User created successfully: {clean_email} (Employee ID: {clean_emp_id}, Role: {role})")
        return {
            "success": True,
            "message": "User created successfully.",
            "user": serialize_user(user_doc)
        }

    except DuplicateKeyError as dke:
        error_msg = str(dke)
        logger.warning(f"DuplicateKeyError during user creation for {clean_email}/{clean_emp_id}: {error_msg}")
        if "email" in error_msg:
            return {"success": False, "error": f"Email '{clean_email}' already exists."}
        elif "employee_id" in error_msg:
            return {"success": False, "error": f"Employee ID '{clean_emp_id}' already exists."}
        else:
            return {"success": False, "error": "Duplicate key violation for unique field."}

    except PyMongoError as pme:
        logger.error(f"PyMongo Database Error during create_user: {pme}", exc_info=True)
        return {"success": False, "error": f"Database error during user creation: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error during create_user: {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def get_user_by_email(email, include_password=False, db=None):
    """
    Retrieves a user document by unique email address.

    :param email: User email (str).
    :param include_password: Bool to include hashed password in serialization (default False).
    :param db: Database instance (optional).
    :return: JSON response dictionary with user data or error.
    """
    target_db = _resolve_db(db)

    if not email or not isinstance(email, str):
        return {"success": False, "error": "Email parameter is required."}

    clean_email = email.strip().lower()

    try:
        user_doc = target_db.users.find_one({"email": clean_email})
        if not user_doc:
            logger.debug(f"User query by email '{clean_email}': Not Found")
            return {"success": False, "error": f"User with email '{clean_email}' not found."}

        logger.debug(f"User query by email '{clean_email}': Found")
        return {
            "success": True,
            "user": serialize_user(user_doc, include_password=include_password)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in get_user_by_email({clean_email}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database query error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in get_user_by_email({clean_email}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def get_user_by_employee_id(employee_id, include_password=False, db=None):
    """
    Retrieves a user document by unique employee ID.

    :param employee_id: Employee ID (str).
    :param include_password: Bool to include hashed password in serialization (default False).
    :param db: Database instance (optional).
    :return: JSON response dictionary with user data or error.
    """
    target_db = _resolve_db(db)

    if not employee_id:
        return {"success": False, "error": "Employee ID parameter is required."}

    clean_emp_id = str(employee_id).strip()

    try:
        user_doc = target_db.users.find_one({"employee_id": clean_emp_id})
        if not user_doc:
            logger.debug(f"User query by employee_id '{clean_emp_id}': Not Found")
            return {"success": False, "error": f"User with employee ID '{clean_emp_id}' not found."}

        logger.debug(f"User query by employee_id '{clean_emp_id}': Found")
        return {
            "success": True,
            "user": serialize_user(user_doc, include_password=include_password)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in get_user_by_employee_id({clean_emp_id}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database query error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in get_user_by_employee_id({clean_emp_id}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def _build_user_query(identifier):
    """Internal helper to construct a query dict from email, employee_id, or ObjectId."""
    if isinstance(identifier, dict):
        return identifier
    if isinstance(identifier, ObjectId):
        return {"_id": identifier}
    
    identifier_str = str(identifier).strip()
    if "@" in identifier_str:
        return {"email": identifier_str.lower()}
    
    # Check if identifier is a valid 24-character ObjectId hex string
    if len(identifier_str) == 24 and ObjectId.is_valid(identifier_str):
        return {"$or": [{"_id": ObjectId(identifier_str)}, {"employee_id": identifier_str}]}
    
    return {"employee_id": identifier_str}


def update_last_login(identifier, db=None):
    """
    Updates the 'last_login' timestamp to current UTC time for the specified user.
    Also resets failed login attempts to 0.

    :param identifier: Email address, employee ID, or user ObjectId string.
    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)
    now = datetime.now(timezone.utc)

    try:
        result = target_db.users.update_one(
            query,
            {
                "$set": {
                    "last_login": now,
                    "failed_login_attempts": 0
                }
            }
        )

        matched_count = getattr(result, "matched_count", 1 if result else 0)
        if matched_count == 0:
            logger.warning(f"update_last_login failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User matching identifier '{identifier}' not found."}

        logger.info(f"Updated last_login timestamp for user '{identifier}' at {now.isoformat()}")
        
        # Fetch updated user doc
        updated_user = target_db.users.find_one(query)
        return {
            "success": True,
            "message": "Last login timestamp updated successfully.",
            "last_login": now.isoformat(),
            "user": serialize_user(updated_user)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in update_last_login({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in update_last_login({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def increment_failed_attempts(identifier, max_attempts=5, db=None):
    """
    Increments the failed login attempt counter for a user.
    If failed attempts reach or exceed max_attempts (default 5), automatically locks the account.

    :param identifier: Email address, employee ID, or user ObjectId string.
    :param max_attempts: Threshold before locking account (int, default 5).
    :param db: Database instance (optional).
    :return: JSON response dictionary containing updated attempt counts and lock status.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)

    try:
        user_doc = target_db.users.find_one(query)
        if not user_doc:
            logger.warning(f"increment_failed_attempts failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User matching identifier '{identifier}' not found."}

        current_attempts = int(user_doc.get("failed_login_attempts", 0)) + 1
        should_lock = current_attempts >= max_attempts

        update_fields = {
            "$set": {
                "failed_login_attempts": current_attempts,
                "account_locked": user_doc.get("account_locked", False) or should_lock
            }
        }

        target_db.users.update_one(query, update_fields)
        logger.warning(f"Failed login attempt #{current_attempts} logged for user '{identifier}'.")

        if should_lock and not user_doc.get("account_locked"):
            logger.critical(f"SECURITY EVENT: Account for user '{identifier}' has been LOCKED due to {current_attempts} failed login attempts!")

        updated_user = target_db.users.find_one(query)
        return {
            "success": True,
            "failed_login_attempts": current_attempts,
            "account_locked": updated_user.get("account_locked", False),
            "max_attempts": max_attempts,
            "message": f"Failed attempt recorded ({current_attempts}/{max_attempts})." + (" Account locked!" if should_lock else ""),
            "user": serialize_user(updated_user)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in increment_failed_attempts({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in increment_failed_attempts({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def reset_failed_attempts(identifier, db=None):
    """
    Resets the failed login attempt counter to 0 for a user.

    :param identifier: Email address, employee ID, or user ObjectId string.
    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)

    try:
        result = target_db.users.update_one(query, {"$set": {"failed_login_attempts": 0}})
        matched_count = getattr(result, "matched_count", 1 if result else 0)
        if matched_count == 0:
            logger.warning(f"reset_failed_attempts failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User matching identifier '{identifier}' not found."}

        logger.info(f"Reset failed login attempts to 0 for user '{identifier}'.")
        updated_user = target_db.users.find_one(query)
        return {
            "success": True,
            "message": f"Failed login attempts reset for user '{identifier}'.",
            "user": serialize_user(updated_user)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in reset_failed_attempts({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in reset_failed_attempts({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def lock_account(identifier, db=None):
    """
    Locks the user account by setting 'account_locked' to True.

    :param identifier: Email address, employee ID, or user ObjectId string.
    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)

    try:
        result = target_db.users.update_one(query, {"$set": {"account_locked": True}})
        matched_count = getattr(result, "matched_count", 1 if result else 0)
        if matched_count == 0:
            logger.warning(f"lock_account failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User matching identifier '{identifier}' not found."}

        logger.critical(f"SECURITY EVENT: Account for user '{identifier}' explicitly LOCKED by system/admin.")
        updated_user = target_db.users.find_one(query)
        return {
            "success": True,
            "account_locked": True,
            "message": f"Account '{identifier}' has been locked.",
            "user": serialize_user(updated_user)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in lock_account({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in lock_account({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def unlock_account(identifier, db=None):
    """
    Unlocks a locked user account and resets failed login attempts.

    :param identifier: Email address, employee ID, or user ObjectId string.
    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)

    try:
        result = target_db.users.update_one(
            query,
            {
                "$set": {
                    "account_locked": False,
                    "failed_login_attempts": 0
                }
            }
        )
        matched_count = getattr(result, "matched_count", 1 if result else 0)
        if matched_count == 0:
            logger.warning(f"unlock_account failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User matching identifier '{identifier}' not found."}

        logger.info(f"Account '{identifier}' has been UNLOCKED.")
        updated_user = target_db.users.find_one(query)
        return {
            "success": True,
            "account_locked": False,
            "message": f"Account '{identifier}' has been unlocked successfully.",
            "user": serialize_user(updated_user)
        }

    except PyMongoError as pme:
        logger.error(f"Database error in unlock_account({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in unlock_account({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}


def verify_user_password(user_or_hash, candidate_password):
    """
    Verifies a candidate plain-text password against a stored PQC encrypted payload or legacy hash.

    :param user_or_hash: Dict containing user PQC document fields or legacy string hash.
    :param candidate_password: Plain-text password provided during login.
    :return: bool (True if match, False otherwise).
    """
    if not user_or_hash or not candidate_password:
        return False

    try:
        # If user_or_hash is a dictionary containing user fields
        if isinstance(user_or_hash, dict):
            if "encapsulated_secret" in user_or_hash and "private_key" in user_or_hash:
                return verify_pqc_password(user_or_hash, candidate_password)
            
            stored_hash = user_or_hash.get("password") or user_or_hash.get("encrypted_password")
            if stored_hash:
                if isinstance(stored_hash, str) and (stored_hash.startswith("pbkdf2:") or stored_hash.startswith("scrypt:")):
                    return check_password_hash(stored_hash, candidate_password)
                return verify_pqc_password(user_or_hash, candidate_password)
            return False

        # If user_or_hash is a legacy password hash string
        if isinstance(user_or_hash, str):
            if user_or_hash.startswith("pbkdf2:") or user_or_hash.startswith("scrypt:"):
                return check_password_hash(user_or_hash, candidate_password)
            return False

        return False
    except Exception as e:
        logger.error(f"Error during password verification: {e}")
        return False


def change_user_password(identifier, current_password, new_password, db=None):
    """
    Changes a user's password after verifying their current password,
    encrypting the new password using ML-KEM-768 PQC encryption.

    :param identifier: Email address, employee ID, or user ObjectId.
    :param current_password: User's existing plain-text password.
    :param new_password: New plain-text password.
    :param db: Database instance (optional).
    :return: JSON response dictionary.
    """
    target_db = _resolve_db(db)
    query = _build_user_query(identifier)

    if not current_password or not new_password:
        return {"success": False, "error": "Both current_password and new_password are required."}

    if len(new_password) < 6:
        return {"success": False, "error": "New password must be at least 6 characters long."}

    try:
        user_doc = target_db.users.find_one(query)
        if not user_doc:
            logger.warning(f"change_user_password failed: User '{identifier}' not found.")
            return {"success": False, "error": f"User '{identifier}' not found."}

        # Verify current password
        if not verify_user_password(user_doc, current_password):
            logger.warning(f"change_user_password failed for '{identifier}': Invalid current password.")
            return {"success": False, "error": "Current password is incorrect."}

        # Encrypt new password using ML-KEM-768 + HKDF-SHA256 + AES-256-GCM
        pqc_payload = encrypt_password(new_password)

        update_fields = {
            "password": pqc_payload["encrypted_password"],
            "encrypted_password": pqc_payload["encrypted_password"],
            "nonce": pqc_payload["nonce"],
            "authentication_tag": pqc_payload["authentication_tag"],
            "encapsulated_secret": pqc_payload["encapsulated_secret"],
            "private_key": pqc_payload["private_key"],
            "algorithm": pqc_payload["algorithm"],
            "failed_login_attempts": 0
        }

        target_db.users.update_one(query, {"$set": update_fields})
        logger.info(f"Password changed successfully for user '{identifier}' with Post-Quantum Protection.")

        return {
            "success": True,
            "message": "Password changed successfully with Post-Quantum Cryptographic Protection."
        }

    except PyMongoError as pme:
        logger.error(f"Database error in change_user_password({identifier}): {pme}", exc_info=True)
        return {"success": False, "error": f"Database update error: {str(pme)}"}

    except Exception as e:
        logger.error(f"Unexpected error in change_user_password({identifier}): {e}", exc_info=True)
        return {"success": False, "error": f"Internal server error: {str(e)}"}

