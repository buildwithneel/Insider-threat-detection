# GarudaAI Final Project Summary

GarudaAI is an advanced security intelligence platform that calculates behavior trust scores, visualizes interactive attack timelines, and leverages Gemini models for automated incident response.

---

## 🚀 3-Sentence Demo Pitch

GarudaAI empowers security operations centers (SOC) to detect and contain insider threats before data exfiltration occurs by transforming millions of raw, noisy logs into clean, human-readable behavioral trust scores and chronological timelines. When an alert triggers, our integration with Gemini models instantly delivers a comprehensive incident narrative and structured containment playbook, saving critical hours during a breach. With an interactive attack simulator and natural-language security search, GarudaAI elevates security analysts from passive query-builders to proactive threat-hunters.

---

## What Was Built

1. **React Client Dashboard**: Styled using vanilla CSS + Tailwind CSS v3 with Outfit typography. Renders real-time user profiles, circular trust indicators, Chart.js score history lines, collapsed event timelines, and a Gemini-powered SOC chat window.
2. **Behavior Trust Score Engine**: Configurable delta calculations and daily decay-recovery algorithms (+1.0 pt/day of clean behavior).
3. **Attack Timeline Parser**: Synthesizes and collapses routine logon/email/browsing logs while keeping critical alerts expanded.
4. **Flask REST API**: Exposes endpoints for data retrieval, simulator inputs, rate limits, and CORS.
5. **AI Assistant & Chat Bot**: Gemini prompting, database caching, and rule-based fallback schemas.
6. **Relational Ingest Pipeline & Connector**: Idempotent python import scripts with a transparent file-based JSON storage fallback for local execution.
7. **Automated Verification Suite**: End-to-end integration and unit tests passing green.

---

## Simulated vs. Real Components

- **Simulated (Synthetic)**:
  - Activity logs (`logon`, `file_access`, `device_usage`, `http_activity`, `email_activity`, `privilege_escalation`) are synthetically generated to model CERT dataset threat sequences.
  - Local database runs on file-based JSON caching to eliminate setup friction.
  - Gemini API runs in rule-based fallback mode unless an API key is provided.
  - Firebase token check is bypassed in local development (`DEV_MODE=true`).
- **Real (Platform Code)**:
  - React + Tailwind CSS client, compiled production assets.
  - Flask backend server, request routing, rate limiters, and CORS structures.
  - PyMongo integrations, indexing schemas, and database CRUD transactions.
  - Trust scoring mathematical formulations, chronological event grouping and sorting.

---

## Post-Hackathon v2 Roadmap

1. **Real-time Log Ingestion**: Connect the Flask API server to live corporate logging systems (SIEM/Splunk) or host agents on endpoints rather than importing static CSV logs.
2. **Deep-Learning Score Adjusters**: Replace simple deduction weights with dynamic anomaly-detection algorithms (e.g. Isolation Forests, Autoencoders) to establish custom employee baseline behaviors.
3. **SOAR Active Containment**: Wire up the "Mitigation Playbook" suggestions directly to Active Directory / Okta APIs, allowing analysts to lock accounts or revoke session tokens with a single click inside the GarudaAI dashboard.
