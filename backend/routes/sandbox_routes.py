"""
SentinelAI Sandbox Verification API Routes
==========================================

Flask Blueprint endpoints for Sandbox analysis evaluations, presets retrieval,
and execution history logging.
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any

try:
    from backend.sandbox import (
        execute_sandbox_workflow,
        get_sandbox_history,
        HIGH_RISK_TRIGGER_CATEGORIES,
        PRESET_SANDBOX_COMMANDS
    )
    from backend.db_client import get_db
except ImportError:
    from sandbox import (
        execute_sandbox_workflow,
        get_sandbox_history,
        HIGH_RISK_TRIGGER_CATEGORIES,
        PRESET_SANDBOX_COMMANDS
    )
    from db_client import get_db

sandbox_bp = Blueprint("sandbox", __name__, url_prefix="/api/sandbox")


@sandbox_bp.route("/presets", methods=["GET"])
def get_presets():
    """Returns list of high-risk trigger categories and preset test commands."""
    return jsonify({
        "categories": HIGH_RISK_TRIGGER_CATEGORIES,
        "presets": PRESET_SANDBOX_COMMANDS
    }), 200


@sandbox_bp.route("/history", methods=["GET"])
def get_history():
    """Retrieves recent sandbox evaluation history logs."""
    employee_id = request.args.get("employee_id")
    limit = int(request.args.get("limit", 30))
    try:
        db = get_db()
        history = get_sandbox_history(db, employee_id=employee_id, limit=limit)
        return jsonify({"success": True, "history": history}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@sandbox_bp.route("/evaluate", methods=["POST"])
def evaluate_action():
    """
    Evaluates a command or employee action inside the Virtual Sandbox.
    Parameters:
    - employee_id: str (Required)
    - action_type: str (Required)
    - command_name: str (Required)
    - details: dict (Optional)
    - critical_threshold: int (Optional, default 30)
    """
    data = request.get_json(silent=True) or {}
    employee_id = data.get("employee_id")
    action_type = data.get("action_type", "Opening executable files")
    command_name = data.get("command_name", "")
    details = data.get("details", {})
    critical_threshold = int(data.get("critical_threshold", 30))

    if not employee_id:
        return jsonify({"success": False, "error": "employee_id is required"}), 400
    if not command_name:
        return jsonify({"success": False, "error": "command_name is required"}), 400

    try:
        db = get_db()
        report = execute_sandbox_workflow(
            db=db,
            employee_id=employee_id,
            action_type=action_type,
            command_name=command_name,
            details=details,
            critical_threshold=critical_threshold
        )
        return jsonify({"success": True, "report": report}), 200
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": f"Sandbox execution error: {str(e)}"}), 500
