# 📖 Garuda AI: SOC Analyst & User Operational Manual

> **End-to-End User Guide for Security Operations & Analyst Teams**  
> *Target Audience: Tier-1 / Tier-2 / Tier-3 SOC Analysts, Incident Responders, Security Managers*  
> *Cross-Reference: [ADMIN_GUIDE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/ADMIN_GUIDE.md) | [USER_MANUAL.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/USER_MANUAL.md)*

---

## 📌 1. Welcome to Garuda AI

Garuda AI provides a real-time, unified dashboard for detecting and responding to insider threats. As a Security Operations Center (SOC) analyst, Garuda AI helps you cut through alert fatigue by converting thousands of raw log events into an intuitive **Behavioral Trust Score (0 to 100)**.

```
+-----------------------------------------------------------------------------------+
|                            GARUDA AI DASHBOARD NAVIGATION                         |
+-----------------------------------------------------------------------------------+
|  [ 1. Employee Risk Grid ]   --> Monitor live user scores (0-100)                 |
|  [ 2. Behavioral Timeline ]  --> Chronological collapsed log events               |
|  [ 3. Identity Cadence ]     --> Typing & Mouse organic confidence meters         |
|  [ 4. Virtual AI Sandbox ]   --> Interactive high-risk command execution          |
|  [ 5. Gemini AI Chatbot ]    --> Natural language threat hunting queries          |
|  [ 6. JIT PAM Portal ]       --> Emergency privilege elevation requests           |
+-----------------------------------------------------------------------------------+
```

---

## 2. Navigating the SOC Analyst Dashboard

---

### 2.1 Interpreting the Employee Risk Grid

The main dashboard screen displays user cards with color-coded Trust Score indicators:

* 🟢 **Green (80 – 100)**: **Healthy**. User exhibits normal, baseline enterprise behavior.
* 🟡 **Yellow (60 – 79)**: **Low Risk**. Minor policy deviations (e.g., occasional after-hours logon).
* 🟠 **Orange (40 – 59)**: **Medium Risk**. Multiple anomalies detected; command sandbox active.
* 🔴 **Red (0 – 39)**: **CRITICAL RISK**. Potential active insider breach.
* 🔒 **LOCKED**: Workstation automatically isolated by Zero Trust engine.

---

### 2.2 Investigating the Chronological Behavioral Timeline

Click on any employee card (e.g., `EMP032`) to open their interactive timeline:

1. **Collapsing Routine Events**: Hundreds of routine web requests or file views are automatically grouped into single expandable rows (e.g., `15x Routine Web Access`).
2. **Expanding Anomalies**: High-risk events (e.g., `USB Insertion`, `Obfuscated PowerShell Execution`) are automatically highlighted with score deduction tags (`-30.0 pts`).

---

### 2.3 Executing Interactive Sandbox Verifications

To test or verify suspicious employee commands without endangering production systems:

1. Open the **Sandbox Interceptor Tab** (`SandboxDashboard.jsx`).
2. Select a preset command template or type a custom command string.
3. Click **Execute in Sandbox**.
4. Review the instant verdict:
   * **SAFE**: Action allowed on host.
   * **SUSPICIOUS**: Action flagged; requires manager sign-off.
   * **MALICIOUS**: Execution blocked; workstation locked; score penalized by $-30.0$.

---

### 2.4 Utilizing the Gemini AI Incident Assistant

When investigating a high-risk employee:

1. Click the **Generate AI Investigation Report** button.
2. Google Gemini analyzes the employee's entire log trail and renders:
   * **Executive Summary**: 2-sentence breakdown of the incident.
   * **Incident Narrative**: Chronological story explaining attacker intent.
   * **SOAR Playbook**: Step-by-step mitigation actions (e.g., *Freeze Active Directory credentials*, *Isolate network switch port*).

---

### 2.5 Requesting Just-In-Time (JIT) Privileged Access

If you require temporary administrative access to execute a security hotfix:

1. Navigate to **JIT Access Management** (`JitPamDashboard.jsx`).
2. Select desired role (e.g., `Database Admin`).
3. Select duration: **15 Minutes** or **60 Minutes**.
4. Enter business justification reason.
5. Click **Request JIT Token**. Upon approval, your token becomes active with a live countdown timer.

---

## 3. Step-by-Step Incident Mitigation Checklist

When an employee workstation lock triggers:

- [ ] **Step 1**: Review the Gemini AI Incident Narrative in the dashboard.
- [ ] **Step 2**: Check Human-Machine Identity Telemetry for bot script markers.
- [ ] **Step 3**: Verify if the employee submitted a valid JIT request.
- [ ] **Step 4**: Contact employee via out-of-band channel (phone/video) to verify identity.
- [ ] **Step 5**: If verified, obtain the 16-character Unlock Key (`GARUDA-UNLOCK-XXXX-XXXX`) from the Admin Portal and enter it to restore workstation access.
