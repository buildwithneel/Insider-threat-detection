# 📊 Garuda AI: System Decision Matrix & Response Protocols

> **Complete Operational Decision Tables, Threshold Matrices & Action Mapping**  
> *Cross-Reference: [SCORING_ENGINE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SCORING_ENGINE.md) | [FORMULAS.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/FORMULAS.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 1. Executive Matrix Summary

The Garuda AI Decision Engine translates raw numerical metrics (Trust Scores, Sandbox verdicts, Human Confidence percentages) into immediate, automated system actions.

---

## 2. Core Operational Decision Matrices

---

### 📊 Matrix 1: Trust Score vs System Action

| Trust Score Range | Status Tag | Access Level | Command Sandbox Policy | Automated System Action |
|---|---|---|---|---|
| **80.0 – 100.0** | **Healthy** | Full Standard Access | Bypassed (Direct Execution) | Allow all normal operations. |
| **60.0 – 79.9** | **Low Risk** | Standard Access | Bypassed for routine tasks | Log events to background timeline. |
| **40.0 – 59.9** | **Medium Risk**| Monitored Access | Intercept High-Risk Categories | Send background alert to SOC Tier-1. |
| **30.0 – 39.9** | **High Risk** | Restricted Access | Intercept ALL PowerShell & Scripts| Trigger Gemini AI Incident Report. |
| **0.0 – 29.9** | **CRITICAL** | **ACCESS REVOKED** | **ALL COMMANDS BLOCKED** | **LOCK WORKSTATION IMMEDIATELY**. |

---

### 📊 Matrix 2: Identity Telemetry vs Governance Decision

| Human Confidence ($H_{conf}$) | Bot Probability ($P_{bot}$) | Cadence Status | System Governance Action |
|---|---|---|---|
| **$\ge 90.0\%$** | $< 5.0\%$ | Verified Organic Human | Pass without restriction. |
| **$70.0\% - 89.9\%$** | $5.0\% - 19.9\%$ | Human with Minor Variance | Allow; record telemetry snapshot. |
| **$40.0\% - 69.9\%$** | $20.0\% - 49.9\%$ | Suspicious / Ambiguous | Trigger MFA Re-Authentication prompt. |
| **$< 40.0\%$** | **$\ge 80.0\%$** | **Automated Script / Bot** | **Deduct -30.0 Trust Score & Lock Workstation**. |

---

### 📊 Matrix 3: Sandbox Verification Verdict vs Execution Policy

| Sandbox Verdict | Risk Score ($S_{risk}$) | Threat Indicators | Host System Response |
|---|---|---|---|
| **SAFE** | $0 - 29$ | Standard developer commands | Allow execution on host operating system. |
| **SUSPICIOUS** | $30 - 69$ | Unencrypted dump, mass downloads | Require JIT Admin Token approval prior to execution. |
| **MALICIOUS** | **$70 - 100$** | Base64 bypass, USB mass copy, wipe | **BLOCK EXECUTION**, deduct -30.0 points, lock workstation. |

---

### 📊 Matrix 4: Threat Alert Priority Matrix

| Event Severity | Employee Trust Level | Resulting Alert Priority | Notification Routing |
|---|---|---|---|
| **Low** | Healthy ($80-100$) | **INFO** | Silent Timeline Logging |
| **Medium** | Healthy ($80-100$) | **LOW** | Background SOC Dashboard Entry |
| **Medium** | Medium Risk ($40-59$)| **MEDIUM** | Standard Analyst Alert Feed |
| **High** | High Risk ($30-39$) | **HIGH** | Instant Push Notification + Gemini Report |
| **Critical** | Critical ($0-29$) | **CRITICAL** | Emergency Pager + Automated Workstation Lock |

---

### 📊 Matrix 5: Incident Severity & Containment Matrix

| Severity Level | Trigger Condition | Automated Containment | Resolution SLA |
|---|---|---|---|
| **SEV-4 (Informational)**| Routine after-hours logon | None | N/A |
| **SEV-3 (Low)** | Single USB insertion | Log event to timeline | 24 Hours |
| **SEV-2 (Medium)** | Mass file download ($>100\text{MB}$) | Intercept subsequent commands into Sandbox | 4 Hours |
| **SEV-1 (Critical)** | Malicious Sandbox execution / Script Bot | **Lock Workstation, Revoke JIT Tokens, Generate Playbook** | **Immediate ($< 5\text{ mins}$)** |
