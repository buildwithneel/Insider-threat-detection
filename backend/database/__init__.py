"""
GarudaAI Database Layer Package
"""

from .auth_db import (
    init_auth_db,
    create_user,
    get_user_by_email,
    get_user_by_employee_id,
    update_last_login,
    increment_failed_attempts,
    reset_failed_attempts,
    lock_account,
    unlock_account,
    verify_user_password,
    change_user_password,
    serialize_user
)

__all__ = [
    "init_auth_db",
    "create_user",
    "get_user_by_email",
    "get_user_by_employee_id",
    "update_last_login",
    "increment_failed_attempts",
    "reset_failed_attempts",
    "lock_account",
    "unlock_account",
    "verify_user_password",
    "change_user_password",
    "serialize_user"
]
