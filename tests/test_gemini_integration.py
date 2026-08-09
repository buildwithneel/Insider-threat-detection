"""
Unit and Integration Tests for Gemini SDK Integration & Error Recovery.
Verifies:
- Absence of metaclass errors
- Environment validation and connectivity checks
- Error classification and full traceback logging
- Automatic pure-python recovery mechanism
- Keyword fallback trigger behavior
- Python version compatibility checks
"""

import os
import sys
import pytest
from unittest.mock import MagicMock, patch

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from gemini_client import (
    GeminiService,
    GeminiException,
    AuthenticationError,
    APIError,
    DependencyError,
    NetworkError,
    GeminiRuntimeError,
    check_python_version,
    validate_gemini_environment,
    get_gemini_api_key,
    classify_exception
)


def test_python_version_check():
    """Verify python version check detects Python version and logs warning for 3.14+."""
    compat, ver_str = check_python_version()
    assert isinstance(ver_str, str)
    if sys.version_info >= (3, 14):
        assert compat is False
        assert os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION") == "python"
    else:
        assert compat is True


def test_environment_validation():
    """Verify environment validator returns expected diagnostic dictionary."""
    is_valid, diagnostics = validate_gemini_environment()
    assert "api_key_present" in diagnostics
    assert "python_compat" in diagnostics
    assert "internet_connected" in diagnostics
    assert "ssl_valid" in diagnostics
    assert "model_valid" in diagnostics
    assert "errors" in diagnostics


def test_no_metaclass_error_on_import():
    """Ensure importing google.genai does not trigger metaclass tp_new errors."""
    try:
        from google import genai
        assert genai is not None
    except Exception as e:
        pytest.fail(f"Importing google.genai raised unexpected exception: {e}")


def test_exception_classification():
    """Test error categorization logic and traceback extraction."""
    # Dependency Error (e.g. metaclass / tp_new)
    try:
        raise TypeError("Metaclasses with custom tp_new are not supported.")
    except Exception as e:
        cat_exc, tb_str, file_name, line_no = classify_exception(e)
        assert isinstance(cat_exc, DependencyError)
        assert "tp_new" in str(cat_exc)
        assert line_no > 0

    # Authentication Error
    try:
        raise Exception("401 UNAUTHENTICATED: Invalid API Key")
    except Exception as e:
        cat_exc, tb_str, file_name, line_no = classify_exception(e)
        assert isinstance(cat_exc, AuthenticationError)

    # API Error (Rate limit 429)
    try:
        raise Exception("429 RESOURCE_EXHAUSTED: Quota exceeded")
    except Exception as e:
        cat_exc, tb_str, file_name, line_no = classify_exception(e)
        assert isinstance(cat_exc, APIError)


def test_recovery_mechanism_on_dependency_error():
    """Verify GeminiService recovers from a C-extension/metaclass error by enforcing pure-python protobuf."""
    service = GeminiService()
    
    mock_genai_client = MagicMock()
    mock_genai_client._is_mock = True
    mock_response = MagicMock()
    mock_response.text = "Recovery response generated successfully."

    attempt_counter = 0

    def mock_generate(*args, **kwargs):
        nonlocal attempt_counter
        attempt_counter += 1
        if attempt_counter == 1:
            raise TypeError("Metaclasses with custom tp_new are not supported.")
        return mock_response

    mock_genai_client.models.generate_content.side_effect = mock_generate
    service.client = mock_genai_client
    service._initialized = True

    result = service.generate_content("Test recovery prompt", retries=1)
    assert result == "Recovery response generated successfully."
    assert os.environ.get("PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION") == "python"


def test_keyword_fallback_triggers_only_on_unrecoverable_failure(monkeypatch):
    """Verify keyword fallback triggers when Gemini service raises an exception."""
    import ai_assistant
    from ai_assistant import generate_ai_explanation

    mock_db = MagicMock()
    mock_db.alerts.find_one.return_value = {
        "alert_id": "ALT-999",
        "employee_id": "EMP-100",
        "type": "USB Theft",
        "severity": "CRITICAL",
        "description": "Unauthorized data transfer to USB drive"
    }
    mock_db.employees.find_one.return_value = {
        "employee_id": "EMP-100",
        "full_name": "Test User",
        "role": "Analyst",
        "department": "IT",
        "current_score": 45.0
    }
    mock_db.events.find.return_value.sort.return_value = []

    # Mock gemini_service to raise an unrecoverable exception
    def failing_generate(*args, **kwargs):
        raise APIError("Gemini API service unavailable.")

    monkeypatch.setattr(ai_assistant, "gemini_available", True)
    monkeypatch.setattr(ai_assistant.gemini_service, "generate_content", failing_generate)

    result = generate_ai_explanation(mock_db, "ALT-999")
    assert "Investigation details for Test User" in result or "Incident Narrative" in result
    mock_db.alerts.update_one.assert_called()

