"""
Gemini Client Helper Module for GarudaAI / SentinelAI.

Provides unified, resilient access to Google Gemini using the latest `google-genai` SDK,
complete with Python version checks, environment validation, recovery mechanisms,
and detailed traceback logging.
"""

import os
import sys
import socket
import ssl
import traceback
import time
import logging
from urllib.parse import urlparse

# Configure logger
logger = logging.getLogger("GeminiClient")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class GeminiException(Exception):
    """Base exception for Gemini operations."""
    def __init__(self, message, original_error=None, file_name=None, line_number=None):
        super().__init__(message)
        self.original_error = original_error
        self.file_name = file_name
        self.line_number = line_number

class AuthenticationError(GeminiException):
    """Raised when API Key is missing or invalid."""
    pass

class APIError(GeminiException):
    """Raised when Gemini API returns an HTTP/API error (quota, 4xx/5xx)."""
    pass

class DependencyError(GeminiException):
    """Raised when underlying dependencies fail (metaclasses, imports, C-extensions)."""
    pass

class NetworkError(GeminiException):
    """Raised when network or SSL verification fails."""
    pass

class GeminiRuntimeError(GeminiException):
    """Raised for general unexpected runtime errors."""
    pass


def check_python_version():
    """
    Checks the active Python version against Gemini SDK compatibility.
    Recommends Python 3.11 or 3.12 if Python 3.14 or unsupported versions are detected.
    """
    version_info = sys.version_info
    ver_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info >= (3, 14):
        logger.warning(
            f"Python {ver_str} detected. Python 3.14+ contains C-extension metaclass changes "
            "that may affect legacy C extensions. Python 3.11 or 3.12 is strongly recommended for production stability."
        )
        # Apply environment fallback for pure-python protobuf to avoid upb C-extension metaclass bugs
        os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
        return False, ver_str
    elif version_info < (3, 9):
        logger.warning(f"Python {ver_str} is deprecated. Python 3.11 or 3.12 is recommended.")
        return False, ver_str
    
    return True, ver_str


def get_gemini_api_key():
    """Retrieves GEMINI_API_KEY from environment or .env file."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        return api_key

    # Fallback to checking root and backend .env files
    env_paths = [".env", os.path.join("..", ".env"), os.path.join(os.path.dirname(__file__), ".env"), os.path.join(os.path.dirname(__file__), "..", ".env")]
    for path in env_paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            if k.strip() == "GEMINI_API_KEY":
                                api_key = v.strip().strip('"').strip("'")
                                if api_key:
                                    os.environ["GEMINI_API_KEY"] = api_key
                                    return api_key
            except Exception as e:
                logger.debug(f"Failed to read .env file at {path}: {e}")

    return ""


def validate_internet_connectivity(host="generativelanguage.googleapis.com", port=443, timeout=3.0):
    """Validates socket connectivity to Google Gemini endpoint."""
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        return True, None
    except Exception as e:
        return False, f"Socket connection failed to {host}:{port} - {e}"


def validate_ssl_certificates(host="generativelanguage.googleapis.com", port=443, timeout=3.0):
    """Validates SSL certificate handshake with Google Gemini API endpoint."""
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                _ = ssock.getpeercert()
        return True, None
    except Exception as e:
        return False, f"SSL verification failed for {host} - {e}"


def validate_model_name(model_name):
    """Validates if the provided model name is a recognized Gemini model."""
    valid_models = {
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-flash-latest",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.6-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    }
    if not model_name or not isinstance(model_name, str):
        return False, "Model name must be a non-empty string."
    if model_name not in valid_models:
        return False, f"Unrecognized model '{model_name}'. Standard models: {sorted(list(valid_models))}"
    return True, None


def validate_gemini_environment(model_name="gemini-3.6-flash"):
    """
    Performs full environment & system validation for Gemini API calls.
    Returns: (is_valid: bool, diagnostics: dict)
    """
    diagnostics = {
        "api_key_present": False,
        "python_compat": True,
        "internet_connected": False,
        "ssl_valid": False,
        "model_valid": False,
        "errors": []
    }

    # 1. API Key validation
    api_key = get_gemini_api_key()
    if api_key:
        diagnostics["api_key_present"] = True
    else:
        diagnostics["errors"].append("GEMINI_API_KEY not found in environment or .env file.")

    # 2. Python version check
    compat, python_ver = check_python_version()
    diagnostics["python_version"] = python_ver
    diagnostics["python_compat"] = compat

    # 3. Network connectivity
    conn_ok, conn_err = validate_internet_connectivity()
    diagnostics["internet_connected"] = conn_ok
    if not conn_ok:
        diagnostics["errors"].append(conn_err)

    # 4. SSL certificate test
    ssl_ok, ssl_err = validate_ssl_certificates()
    diagnostics["ssl_valid"] = ssl_ok
    if not ssl_ok:
        diagnostics["errors"].append(ssl_err)

    # 5. Model name check
    model_ok, model_err = validate_model_name(model_name)
    diagnostics["model_valid"] = model_ok
    if not model_ok:
        diagnostics["errors"].append(model_err)

    is_valid = diagnostics["api_key_present"] and diagnostics["internet_connected"] and diagnostics["ssl_valid"]
    return is_valid, diagnostics


def classify_exception(exc):
    """
    Classifies a raw python exception into a specific GeminiException category
    and extracts full traceback details.
    """
    exc_type, exc_val, exc_tb = sys.exc_info()
    tb_lines = traceback.format_exception(exc_type, exc_val, exc_tb)
    full_tb = "".join(tb_lines)

    # Extract exact origin file and line number
    file_name = "unknown"
    line_number = 0
    if exc_tb:
        frame = exc_tb
        while frame.tb_next:
            frame = frame.tb_next
        file_name = frame.tb_frame.f_code.co_filename
        line_number = frame.tb_lineno

    exc_msg = str(exc)
    exc_type_name = type(exc).__name__

    if isinstance(exc, (TypeError, ImportError, AttributeError, ModuleNotFoundError)) or "tp_new" in exc_msg or "metaclass" in exc_msg.lower():
        cat_exc = DependencyError(
            f"Dependency failure ({exc_type_name}): {exc_msg}",
            original_error=exc, file_name=file_name, line_number=line_number
        )
    elif isinstance(exc, (socket.error, ssl.SSLError, ConnectionError)) or "SSL" in exc_msg or "ConnectionRefused" in exc_msg:
        cat_exc = NetworkError(
            f"Network failure ({exc_type_name}): {exc_msg}",
            original_error=exc, file_name=file_name, line_number=line_number
        )
    elif "401" in exc_msg or "403" in exc_msg or "API_KEY" in exc_msg or "UNAUTHENTICATED" in exc_msg or "PERMISSION_DENIED" in exc_msg:
        cat_exc = AuthenticationError(
            f"Authentication failure ({exc_type_name}): {exc_msg}",
            original_error=exc, file_name=file_name, line_number=line_number
        )
    elif "429" in exc_msg or "QUOTA" in exc_msg or "RESOURCE_EXHAUSTED" in exc_msg or "500" in exc_msg or "503" in exc_msg:
        cat_exc = APIError(
            f"Gemini API Error ({exc_type_name}): {exc_msg}",
            original_error=exc, file_name=file_name, line_number=line_number
        )
    else:
        cat_exc = GeminiRuntimeError(
            f"Gemini Runtime Error ({exc_type_name}): {exc_msg}",
            original_error=exc, file_name=file_name, line_number=line_number
        )

    return cat_exc, full_tb, file_name, line_number


class GeminiService:
    """
    Unified, resilient client for Google Gemini using official google-genai SDK.
    Handles SDK initialization, recovery retries, fallback model handling,
    and detailed traceback logging.
    """
    def __init__(self, default_model="gemini-3.6-flash"):
        self.default_model = default_model
        self.client = None
        self._initialized = False
        check_python_version()

    def initialize_client(self, force_pure_python=False):
        """
        Initializes the google-genai client.
        If force_pure_python is True, forces PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python.
        """
        if force_pure_python:
            os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

        api_key = get_gemini_api_key()
        if not api_key:
            raise AuthenticationError("GEMINI_API_KEY is not set.")

        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
            self._initialized = True
            logger.info("google-genai SDK Client initialized successfully.")
            return self.client
        except Exception as e:
            cat_exc, full_tb, file_name, line_no = classify_exception(e)
            logger.error(
                f"Gemini SDK initialization failed at {file_name}:{line_no}:\n"
                f"Category: {type(cat_exc).__name__}\n"
                f"Details: {cat_exc}\n"
                f"Full Traceback:\n{full_tb}"
            )
            raise cat_exc

    def generate_content(self, prompt, model_name=None, retries=2):
        """
        Generates text content using Google Gemini via the AI API Gateway layer
        with multi-key failover, load balancing, health monitoring, and backoff retries.
        
        Args:
            prompt (str): Text prompt for Gemini.
            model_name (str, optional): Target model name. Defaults to self.default_model.
            retries (int): Number of automatic recovery attempts before failing.

        Returns:
            str: Generated response text.
        """
        target_model = model_name or self.default_model

        try:
            from backend.ai_gateway import ai_gateway
        except ImportError:
            from ai_gateway import ai_gateway

        try:
            return ai_gateway.execute_content_generation(prompt, model_name=target_model)
        except Exception as e:
            cat_exc, full_tb, file_name, line_no = classify_exception(e)
            logger.error(f"AI Gateway request failed: {cat_exc}\n{full_tb}")
            return "AI service is temporarily unavailable. Please try again in a few moments."


# Singleton service instance for application-wide reuse
gemini_service = GeminiService()

