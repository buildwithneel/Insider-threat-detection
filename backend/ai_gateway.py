"""
SentinelAI - AI API Gateway & Multi-Key Manager Module
======================================================

Provides a highly available, resilient AI API Gateway layer for Google Gemini API.
Features:
- Multi-Key API Pool management from env vars (GEMINI_API_KEY_1, GEMINI_API_KEY_2, ...)
- Configurable Load Balancing Routing Strategies:
  * Round Robin (default)
  * Least Recently Used (LRU)
  * Least Request Count
  * Priority Based
  * Weighted Round Robin
- Automatic Failover & Exponential Backoff Retries on HTTP 429, Rate Limit, Quota, Timeout, 5xx
- Health Monitoring & Cooldown Management with auto-restoration
- Key Masking (AIza************7Hx) for logging and security
- Telemetry & Metrics Tracking
"""

import os
import sys
import time
import math
import logging
import threading
import traceback
from datetime import datetime, timedelta

# Configure logger for AI Gateway
logger = logging.getLogger("AIGateway")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [AIGateway] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def mask_api_key(api_key):
    """Masks an API key string for logging and UI security (e.g. AIza************7Hx)."""
    if not api_key or not isinstance(api_key, str):
        return "UNKNOWN_KEY"
    api_key = api_key.strip()
    if len(api_key) <= 8:
        return api_key[:2] + "****" + api_key[-2:]
    return api_key[:4] + "*" * (len(api_key) - 7) + api_key[-3:]


class KeyStatus:
    HEALTHY = "Healthy"
    BUSY = "Busy"
    COOLING_DOWN = "Cooling Down"
    UNAVAILABLE = "Unavailable"


class KeyMetrics:
    def __init__(self, key_id, api_key, priority=1, weight=10):
        self.key_id = key_id
        self.api_key = api_key
        self.masked_key = mask_api_key(api_key)
        self.priority = priority
        self.weight = weight
        self.status = KeyStatus.HEALTHY
        self.request_count = 0
        self.success_count = 0
        self.error_count = 0
        self.consecutive_failures = 0
        self.last_used_ts = None
        self.total_response_time_ms = 0.0
        self.avg_response_time_ms = 0.0
        self.cooldown_until = None
        self.last_error_reason = None

    def mark_used(self):
        self.request_count += 1
        self.last_used_ts = time.time()

    def record_success(self, response_time_ms):
        self.success_count += 1
        self.consecutive_failures = 0
        self.total_response_time_ms += response_time_ms
        self.avg_response_time_ms = round(self.total_response_time_ms / max(1, self.success_count), 1)
        if self.status != KeyStatus.UNAVAILABLE:
            self.status = KeyStatus.HEALTHY

    def record_failure(self, error_reason, cooldown_duration_sec=60):
        self.error_count += 1
        self.consecutive_failures += 1
        self.last_error_reason = str(error_reason)

        err_str = str(error_reason).lower()
        if any(term in err_str for term in ["429", "quota", "rate limit", "resource_exhausted", "503", "500"]):
            self.status = KeyStatus.COOLING_DOWN
            self.cooldown_until = time.time() + cooldown_duration_sec
            logger.warning(
                f"Key {self.key_id} ({self.masked_key}) placed in COOLING DOWN for {cooldown_duration_sec}s. Reason: {error_reason}"
            )
        elif self.consecutive_failures >= 5:
            self.status = KeyStatus.UNAVAILABLE
            logger.error(
                f"Key {self.key_id} ({self.masked_key}) marked UNAVAILABLE due to {self.consecutive_failures} consecutive failures."
            )

    def check_auto_recovery(self):
        if self.status == KeyStatus.COOLING_DOWN and self.cooldown_until:
            if time.time() >= self.cooldown_until:
                self.status = KeyStatus.HEALTHY
                self.cooldown_until = None
                self.consecutive_failures = 0
                logger.info(f"Key {self.key_id} ({self.masked_key}) auto-restored from cooldown to HEALTHY.")
                return True
        return False

    def to_dict(self):
        self.check_auto_recovery()
        cooldown_rem = max(0, int(self.cooldown_until - time.time())) if self.cooldown_until else 0
        return {
            "key_id": self.key_id,
            "masked_key": self.masked_key,
            "status": self.status,
            "priority": self.priority,
            "weight": self.weight,
            "request_count": self.request_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "consecutive_failures": self.consecutive_failures,
            "avg_response_time_ms": self.avg_response_time_ms,
            "last_used_timestamp": datetime.fromtimestamp(self.last_used_ts).isoformat() if self.last_used_ts else None,
            "cooldown_remaining_sec": cooldown_rem,
            "last_error_reason": self.last_error_reason
        }


class AIGateway:
    """
    Intelligent AI API Gateway managing Google Gemini API key pool.
    Supports load balancing strategies, automatic failover, retries with backoff,
    key health monitoring, and security masking.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self.keys = []  # List of KeyMetrics
        self.round_robin_idx = 0
        self.weighted_idx = 0

        # Configuration options
        self.strategy = os.environ.get("LOAD_BALANCING_STRATEGY", "Round Robin").strip()
        self.max_retries = int(os.environ.get("MAX_RETRIES", "2"))
        self.cooldown_time_sec = int(os.environ.get("COOLDOWN_TIME", "60"))

        self.discover_keys()

    def discover_keys(self):
        """Discovers all GEMINI_API_KEY_1, GEMINI_API_KEY_2, ..., GEMINI_API_KEY from environment and .env."""
        with self._lock:
            key_map = {}

            # Read from os.environ first
            for k, v in os.environ.items():
                if k.startswith("GEMINI_API_KEY") and v.strip():
                    key_map[k] = v.strip()

            # Fallback to .env file checking if empty or only 1 found
            env_paths = [".env", os.path.join("..", ".env"), os.path.join(os.path.dirname(__file__), ".env"), os.path.join(os.path.dirname(__file__), "..", ".env")]
            for p in env_paths:
                if os.path.exists(p):
                    try:
                        with open(p, "r") as f:
                            for line in f:
                                line = line.strip()
                                if line and not line.startswith("#") and "=" in line:
                                    key_name, key_val = line.split("=", 1)
                                    key_name = key_name.strip()
                                    key_val = key_val.strip().strip('"').strip("'")
                                    if key_name.startswith("GEMINI_API_KEY") and key_val:
                                        key_map[key_name] = key_val
                    except Exception as e:
                        logger.debug(f"Failed reading .env at {p}: {e}")

            # Build keys pool list
            self.keys = []
            sorted_key_names = sorted(key_map.keys())

            # If no numbered keys exist but single GEMINI_API_KEY exists, make it KEY_1
            if not sorted_key_names and os.environ.get("GEMINI_API_KEY"):
                key_map["GEMINI_API_KEY_1"] = os.environ.get("GEMINI_API_KEY")
                sorted_key_names = ["GEMINI_API_KEY_1"]

            for idx, k_name in enumerate(sorted_key_names, start=1):
                val = key_map[k_name]
                # Assign default priorities & weights for fallback demo testing if needed
                prio = 1 if idx <= 2 else 2
                weight = 20 if idx == 1 else 10
                km = KeyMetrics(key_id=f"KEY_{idx}", api_key=val, priority=prio, weight=weight)
                self.keys.append(km)

            # If still no valid key discovered, add placeholder dummy key to prevent crashes
            if not self.keys:
                dummy_val = os.environ.get("GEMINI_API_KEY", "") or "AIzaSyDummyKeyPlaceholderForGatewayTesting"
                km = KeyMetrics(key_id="KEY_1", api_key=dummy_val, priority=1, weight=10)
                self.keys.append(km)

            logger.info(f"AI Gateway Key Pool initialized with {len(self.keys)} API Key(s). Strategy: '{self.strategy}'.")

    def get_available_keys(self):
        """Returns list of currently healthy or auto-recovered keys."""
        available = []
        for k in self.keys:
            k.check_auto_recovery()
            if k.status == KeyStatus.HEALTHY:
                available.append(k)
        return available

    def select_key(self):
        """Selects an API key according to the active Load Balancing Strategy."""
        with self._lock:
            available = self.get_available_keys()

            # If no healthy keys exist, attempt auto-recovery on any cooling key
            if not available:
                for k in self.keys:
                    if k.status == KeyStatus.COOLING_DOWN:
                        k.status = KeyStatus.HEALTHY
                        k.cooldown_until = None
                        available.append(k)

            if not available:
                # Return the least bad key if all are cooling down or disabled
                available = sorted(self.keys, key=lambda x: x.consecutive_failures)

            target_key = None
            strat = self.strategy.lower()

            if "least recently used" in strat or "lru" in strat:
                # Select key with oldest (smallest) last_used_ts
                target_key = min(available, key=lambda k: k.last_used_ts or 0)

            elif "least request" in strat or "least request count" in strat:
                # Select key with lowest request_count
                target_key = min(available, key=lambda k: k.request_count)

            elif "priority" in strat:
                # Select key with lowest priority index (1 is highest priority)
                target_key = min(available, key=lambda k: (k.priority, k.request_count))

            elif "weighted" in strat:
                # Weighted round-robin selection
                total_weight = sum(k.weight for k in available)
                if total_weight > 0:
                    self.weighted_idx = (self.weighted_idx + 1) % total_weight
                    acc = 0
                    for k in available:
                        acc += k.weight
                        if self.weighted_idx < acc:
                            target_key = k
                            break
                if not target_key:
                    target_key = available[0]

            else:
                # Round Robin (default)
                idx = self.round_robin_idx % len(available)
                target_key = available[idx]
                self.round_robin_idx = (self.round_robin_idx + 1) % len(available)

            target_key.mark_used()
            return target_key

    def execute_content_generation(self, prompt, model_name="gemini-3.6-flash"):
        """
        Executes Gemini API generation via AI Gateway with automatic failover,
        exponential backoff retries, and masked logging.
        """
        attempt = 0
        retries = max(1, min(5, self.max_retries))
        last_error = None
        key_switches = 0
        start_global_time = time.time()

        from google import genai

        while attempt <= retries:
            attempt += 1
            key_obj = self.select_key()
            masked_key = key_obj.masked_key
            
            logger.info(
                f"[Gateway Request] Attempt {attempt}/{retries+1} using Key {key_obj.key_id} ({masked_key}) "
                f"via strategy '{self.strategy}'"
            )

            start_req_time = time.time()
            try:
                # Initialize google-genai client with the selected key
                client = genai.Client(api_key=key_obj.api_key)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                resp_time_ms = round((time.time() - start_req_time) * 1000, 1)

                if response and hasattr(response, "text") and response.text:
                    key_obj.record_success(resp_time_ms)
                    logger.info(
                        f"[Gateway Success] Key {key_obj.key_id} ({masked_key}) responded in {resp_time_ms}ms "
                        f"(Retries: {attempt - 1}, Key Switches: {key_switches})"
                    )
                    return response.text
                elif response and hasattr(response, "candidates") and response.candidates:
                    res_txt = str(response.candidates[0])
                    key_obj.record_success(resp_time_ms)
                    return res_txt
                else:
                    raise Exception("Gemini API returned an empty response.")

            except Exception as e:
                resp_time_ms = round((time.time() - start_req_time) * 1000, 1)
                err_msg = str(e)
                key_obj.record_failure(err_msg, cooldown_duration_sec=self.cooldown_time_sec)
                last_error = e

                logger.warning(
                    f"[Gateway Failover Triggered] Key {key_obj.key_id} ({masked_key}) failed after {resp_time_ms}ms: {err_msg}"
                )

                if attempt <= retries:
                    key_switches += 1
                    # Exponential Backoff calculation: 1s, 2s, 4s...
                    backoff_sec = 2 ** (attempt - 1)
                    logger.info(f"[Exponential Backoff] Sleeping {backoff_sec}s before switching keys for retry {attempt+1}...")
                    time.sleep(backoff_sec)

        # If all retries & keys fail, log failure and return friendly message
        logger.error(f"[Gateway Exhausted] All retries ({retries}) failed across API keys pool. Last error: {last_error}")
        return "AI service is temporarily unavailable. Please try again in a few moments."

    def get_status(self):
        """Returns JSON status dictionary for Admin Dashboard."""
        with self._lock:
            key_dicts = [k.to_dict() for k in self.keys]
            active_keys = [k for k in self.keys if k.status == KeyStatus.HEALTHY]
            cooling_keys = [k for k in self.keys if k.status == KeyStatus.COOLING_DOWN]
            disabled_keys = [k for k in self.keys if k.status == KeyStatus.UNAVAILABLE]

            total_requests = sum(k.request_count for k in self.keys)
            total_success = sum(k.success_count for k in self.keys)
            total_errors = sum(k.error_count for k in self.keys)
            avg_resp = round(
                sum(k.avg_response_time_ms for k in self.keys if k.success_count > 0) / max(1, len([k for k in self.keys if k.success_count > 0])),
                1
            )

            current_active = active_keys[0].masked_key if active_keys else (self.keys[0].masked_key if self.keys else "NONE")

            return {
                "total_keys": len(self.keys),
                "active_keys_count": len(active_keys),
                "cooling_keys_count": len(cooling_keys),
                "disabled_keys_count": len(disabled_keys),
                "current_active_key_masked": current_active,
                "total_requests_served": total_requests,
                "total_success_count": total_success,
                "total_error_count": total_errors,
                "success_rate_pct": round((total_success / max(1, total_requests)) * 100.0, 1) if total_requests > 0 else 100.0,
                "avg_response_time_ms": avg_resp,
                "load_balancing_strategy": self.strategy,
                "max_retries": self.max_retries,
                "cooldown_time_sec": self.cooldown_time_sec,
                "gateway_health": "Healthy" if active_keys else ("Degraded" if cooling_keys else "Critical"),
                "keys_pool": key_dicts
            }

    def update_config(self, strategy=None, max_retries=None, cooldown_time_sec=None):
        """Dynamically updates gateway configuration."""
        with self._lock:
            if strategy and isinstance(strategy, str):
                self.strategy = strategy.strip()
            if max_retries is not None:
                self.max_retries = int(max_retries)
            if cooldown_time_sec is not None:
                self.cooldown_time_sec = int(cooldown_time_sec)
            logger.info(f"AI Gateway Config Updated: Strategy='{self.strategy}', Max Retries={self.max_retries}, Cooldown={self.cooldown_time_sec}s.")
            return self.get_status()

    def reset_metrics(self):
        """Resets all request counts, errors, and key health states back to baseline."""
        with self._lock:
            for k in self.keys:
                k.request_count = 0
                k.success_count = 0
                k.error_count = 0
                k.consecutive_failures = 0
                k.status = KeyStatus.HEALTHY
                k.cooldown_until = None
                k.total_response_time_ms = 0.0
                k.avg_response_time_ms = 0.0
            logger.info("AI Gateway metrics and key health pools reset to default baseline.")
            return self.get_status()


# Singleton Gateway Instance for global application usage
ai_gateway = AIGateway()
