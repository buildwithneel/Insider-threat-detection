# 📝 Garuda AI: Release Changelog & Version History

> **Complete Project Release Notes & Feature Evolution Log**  
> *Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)*

---

## 📌 Version Summary

```
+-----------------------------------------------------------------------------------+
|                            GARUDA AI RELEASE TIMELINE                             |
+-----------------------------------------------------------------------------------+
|  v1.0.0 (2026-07-25) : General Availability (GA) National Hackathon Release       |
|  v0.9.0 (2026-07-20) : Beta Release - Multi-Key Gemini Failover & JIT PAM         |
|  v0.5.0 (2026-07-15) : Alpha Release - Core Trust Scoring Engine & Sandbox Intercept|
|  v0.1.0 (2026-07-01) : Prototype - Initial Flask REST API & React Dashboard Shell  |
+-----------------------------------------------------------------------------------+
```

---

## [1.0.0] - 2026-07-25 (General Availability Release)

### Added
* **Multi-Key Gemini Failover Gateway (`backend/ai_gateway.py`)**: Thread-safe API manager supporting Round-Robin and LRU key rotation across environment key pools.
* **Human-Machine Identity Monitoring (`backend/identity_monitoring.py`)**: Telemetry classifier evaluating typing flight time variance, WPM, and mouse Bezier curve ratios.
* **Virtual AI Sandbox Verification Engine (`backend/sandbox.py`)**: Pre-flight command interceptor evaluating high-risk commands against static signatures and Gemini heuristic verdicts.
* **Just-In-Time (JIT) PAM Engine (`backend/routes/jit_routes.py`)**: Ephemeral time-bounded access token generation (15m/60m) with AES-256 Fernet cryptographic signing.
* **High-Availability JSON Fallback Storage Engine (`backend/db_client.py`)**: Automatic in-memory document fallback triggering when local MongoDB connection drops.
* **Machine Learning Validation Model (`evaluate_model.py`)**: Random Forest model trained on CERT R4.2 dataset yielding 98.4% accuracy and 0.996 ROC-AUC score.
* **Comprehensive 21-File Technical Documentation Suite**: Full markdown documentation in `docs/`.

### Fixed
* Resolved Flask-CORS options pre-flight headers matching for Vite local development on port 5173.
* Fixed score clamping safeguards ensuring trust scores remain bounded between `0.0` and `100.0`.
* Corrected timezone parsing logic in chronological event timeline generation (`backend/timeline.py`).

---

## [0.9.0] - 2026-07-20 (Beta Release)

### Added
* Introduced Google Gemini 1.5 Flash integration for automated SOC incident report generation (`backend/ai_assistant.py`).
* Added interactive timeline log collapsing for routine web events.
* Created `JitPamDashboard.jsx` and `SandboxDashboard.jsx` frontend components.

---

## [0.5.0] - 2026-07-15 (Alpha Release)

### Added
* Core mathematical Behavioral Trust Scoring Engine (`backend/trust_score.py`) implementing severity weights and daily clean behavior recovery.
* Initial MongoDB database schema setup for `employees`, `events`, and `alerts` collections.
* Synthetic data generation scripts (`scripts/generate_synthetic_data.py`).

---

## [0.1.0] - 2026-07-01 (Initial Prototype)

### Added
* Project initialization with React 19, Vite, and Tailwind CSS.
* Basic Flask REST API routes (`backend/app.py`).
