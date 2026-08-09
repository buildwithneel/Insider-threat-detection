# 🎤 Garuda AI: Project Defense, Pitch Scripts & Hackathon Strategy

> **Master Hackathon Defense Guide: Pitch Scripts, Demo Walkthroughs, Judge Handling & Winning Tactics**  
> *Target Audience: Team Captains, Presenters, Technical Speakers at National Finale Competitions*  
> *Cross-Reference: [JURY_QA.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/JURY_QA.md) | [HACKATHON_BIBLE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/HACKATHON_BIBLE.md)*

---

## 📌 1. Elevator Pitch Variations

---

### ⏱️ 1.1 The 2-Minute Elevator Pitch (Rapid Finale Version)

"Respected Judges, insider threats cost financial institutions over **$15 million per incident**, with traditional SIEM tools generating thousands of unprioritized alerts while taking 85 days to identify a breach. 

Meet **Garuda AI**: an enterprise-grade AI-powered Zero Trust platform that quantifies insider risk into a single, dynamic **Behavioral Trust Score (0 to 100)**. 

Unlike legacy systems that log security events *after* damage occurs, Garuda AI introduces **Pre-Flight Virtual Sandbox Interception**, testing risky employee commands in isolated containers before execution. We combine physical human-machine telemetry (typing flight times, mouse Bezier curves) with a **Multi-Key Gemini AI Failover Gateway** that generates automated SOC investigation playbooks in under 3 seconds.

When a breach occurs, our Zero Trust engine autonomously locks the compromised workstation and revokes privileges using **Just-In-Time (JIT)** token control. Tested against the benchmark **CERT R4.2 dataset**, our Random Forest model achieves **98.4% accuracy**. Garuda AI transforms passive log monitoring into active, autonomous defense. Thank you!"

---

### ⏱️ 1.2 The 5-Minute Technical Pitch (Stage Presentation Version)

*(Slide 1: Problem Statement)*  
"Good morning, judges. In 2023, 68% of enterprise data breaches involved internal credentials. Legacy security tools fail because they suffer from **Perimeter Fallacy** and **Alert Fatigue**. They log events passively after data exfiltration has already happened.

*(Slide 2: Solution Architecture)*  
Garuda AI solves this with a 7-layer architecture. We continuously ingest user telemetry and convert raw events into a rolling **Behavioral Trust Score**. Every employee starts at 100 points. Low-severity events deduct minor points, while critical events—such as unauthorized privilege escalation or bulk file transfers—apply heavy penalties. If an employee exhibits clean behavior, their score recovers gradually at 0.5 points per day.

*(Slide 3: Technical USPs)*  
Our platform features three breakthrough innovations:
1. **Pre-Flight Virtual Sandbox**: Risky command lines (like obfuscated PowerShell scripts) are intercepted and evaluated in a virtual container *before* touching production hosts.
2. **Human-Machine Telemetry Classifier**: We analyze typing flight time variance and mouse Bezier curvature ratios to detect automated Python scripts and headless bots.
3. **Multi-Key Gemini Failover Gateway**: We engineered a thread-safe API proxy with Round-Robin and LRU rotation. If one API key encounters rate limits, the gateway rotates keys seamlessly in under 12 milliseconds.

*(Slide 4: Live Demo & Impact)*  
As you see on our screen, when `EMP032` attempts a mass USB transfer, Garuda AI detects the anomaly, drops the trust score to 12.5, triggers an autonomous workstation lock, and generates a full Gemini SOAR playbook. Garuda AI reduces SOC triage time from hours to seconds. Thank you!"

---

## 2. Live Demo Script & Step-by-Step Flow

---

### 🎬 Demo Execution Sequence (3 Minutes)

1. **Step 1: Baseline Dashboard Overview (0:00 – 0:45)**  
   *Presenter Action*: Show the main React dashboard (`frontend/src/App.jsx`). Point to the circular employee score indicators.  
   *Speaker Script*: "Notice our live SOC view. Most employees, like Sarah in Finance, are in the Green zone with a Trust Score of 88. However, DevOps Lead Alex Mercer (`EMP032`) is flagged in Red."

2. **Step 2: Interactive Sandbox Interception (0:45 – 1:30)**  
   *Presenter Action*: Switch to `SandboxDashboard.jsx`. Select the preset command `Obfuscated PowerShell Download` and click **Execute in Sandbox**.  
   *Speaker Script*: "Instead of executing this risky script directly on the host, Garuda AI routes it to our Virtual AI Sandbox. Within 400 milliseconds, the verdict returns **MALICIOUS**. Watch what happens next."

3. **Step 3: Autonomous Lock & Gemini Playbook (1:30 – 2:30)**  
   *Presenter Action*: Click back to the main dashboard. Show `EMP032` card transitioning to **LOCKED** with an auto-generated 16-character Unlock Key. Click **Generate AI Investigation Report**.  
   *Speaker Script*: "The Zero Trust engine autonomously locked Alex's workstation, revoked active JIT tokens, and invoked our Gemini AI Multi-Key Gateway. In under 3 seconds, Gemini generated an executive summary, chronological narrative, and a 3-step mitigation playbook."

4. **Step 4: JIT Privilege Elevation (2:30 – 3:00)**  
   *Presenter Action*: Show `JitPamDashboard.jsx`. Demonstrate requesting a 15-minute `Database Admin` token.  
   *Speaker Script*: "To prevent permanent privilege abuse, administrators issue time-bounded JIT access tokens. After 15 minutes, access automatically expires."

---

## 3. Judge Objections & Counter-Defense Strategies

| Judge Objection | Counter-Defense Script |
|---|---|
| *"What if Google Gemini goes down completely during a major attack?"* | "Great question, judge. Our multi-key gateway supports key pool rotation, but if Google Cloud suffers a global outage, Garuda AI automatically falls back to an offline rule-based playbook engine (`backend/ai_assistant.py`), ensuring uninterrupted SOC operations." |
| *"Is a 0.5 points/day recovery rate too slow for innocent employees?"* | "We deliberately chose a conservative recovery rate to prevent 'score gaming', where an attacker alternates between malicious bursts and artificial clean periods. Critical business needs can be overridden by SOC leads via JIT access tokens." |
| *"How do you protect mouse telemetry data from privacy regulations like GDPR?"* | "Garuda AI processes mouse motion metrics strictly as non-invertible statistical summaries (Bezier ratios, flight time standard deviations). Raw coordinate tracks are never stored or transmitted." |

---

## 4. Emergency Backup Plan (If Live Demo Fails)

If network connectivity drops during the hackathon finale:

1. **Activate Local JSON Fallback Mode**: The backend automatically detects offline MongoDB connections and switches to `db_client.py` in-memory fallback.
2. **Offline Local Playbooks**: Set `DEV_MODE=true` in `.env` to bypass external API calls and render pre-cached JSON playbooks.
3. **Pre-recorded Screen Backup**: Keep a 1080p MP4 screen recording of the live dashboard workflow ready on the desktop.

---

## 5. Winning Body Language & Presentation Tips

* **Maintain Eye Contact**: Divide eye contact equally across all jury members.
* **Anchor Technical Claims**: Back every feature claim with concrete numbers (e.g., *"98.4% model accuracy"*, *"sub-5ms calculation latency"*).
* **Seamless Role Handshake**: Transition cleanly between team members (e.g., *"I will now hand over to our Security Lead to demonstrate Virtual Sandboxing"*).
