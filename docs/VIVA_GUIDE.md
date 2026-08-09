# 🎓 Garuda AI: Academic Viva Voce, Technical Interview & Cheat Sheet Manual

> **500 Rapid-Fire Viva Questions, Core Definitions, Mnemonics & Revision Cheat Sheets**  
> *Target Audience: Second-Year & Final-Year Engineering Students, Technical Interviewees*  
> *Cross-Reference: [JURY_QA.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/JURY_QA.md) | [FORMULAS.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/FORMULAS.md) | [PROJECT_DEFENSE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/PROJECT_DEFENSE.md)*

---

## 📌 1. Master Glossary & Definitions

* **Zero Trust Architecture (ZTA)**: A security framework based on the principle of "Never Trust, Always Verify", requiring continuous authentication and authorization for every request regardless of network location.
* **Behavioral Trust Score**: A dynamic metric (0–100) representing an employee's trustworthiness based on real-time activity evaluation, daily recovery rates, and severity deductions.
* **Just-In-Time (JIT) PAM**: Privileged Access Management protocol that grants temporary, time-bounded (15m/60m) elevated permissions only when needed.
* **Virtual AI Sandbox**: An isolated virtual execution environment used to test high-risk commands and scripts before allowing host system execution.
* **SIEM**: Security Information and Event Management system that aggregates and analyzes security log data from across an enterprise network.
* **SOAR**: Security Orchestration, Automation, and Response framework that automates incident triage and playbooks.
* **Keystroke Dynamics**: Behavioral biometric verification measuring typing speed (WPM), key hold duration, and flight time variance between key presses.
* **Bezier Mouse Curve**: Smooth, natural curved mouse movement paths characteristic of human interaction, as opposed to straight linear bot movements.
* **Multi-Key Failover Gateway**: A proxy layer that balances generative AI API calls across multiple API keys to maintain high availability despite rate limits (HTTP 429).
* **CERT R4.2 Dataset**: A benchmark cybersecurity dataset containing synthetic insider threat activity logs used for machine learning model training.

---

## 🧠 2. Mnemonics & Memory Tricks for Viva Defense

### Mnemonic 1: `T-R-U-S-T` (Core System Pillars)
* **T**elemetry Processing (Typing cadence & mouse Bezier curves)
* **R**eal-time Behavioral Scoring (Dynamic 0–100 algorithm)
* **U**nqualified Access Revocation (Autonomous workstation lock below 30.0)
* **S**andbox Pre-Flight Verification (Isolated virtual execution)
* **T**ime-Bounded JIT Tokens (Ephemeral 15m/60m privileges)

### Mnemonic 2: `Z-E-R-O` (Zero Trust Guarantees)
* **Z**ero Static Trust (Verify every request)
* **E**ncrypted In Transit & Rest (AES-256 Fernet + TLS 1.3)
* **R**ole-Based Authorization (RBAC permission decorators)
* **O**ut-of-Band Incident Containment (Gemini AI SOAR Playbooks)

---

## ⚡ 3. 500 Rapid-Fire Viva Questions & Answers (Categorized Summary)

---

### Section A: Web Development & Frontend (Q1 – Q100)

* **Q1: What is the Virtual DOM in React?**  
  *Ans*: An in-memory lightweight representation of the real DOM. React diffs the Virtual DOM against the actual DOM to apply minimal, high-speed UI updates.
* **Q2: Why use Vite over Webpack?**  
  *Ans*: Vite uses native ES modules (ESM) and esbuild written in Go, starting dev servers up to 100x faster than Webpack.
* **Q3: What is SPA routing?**  
  *Ans*: Single Page Application routing renders component views dynamically without triggering full page browser reloads.
* **Q4: How does Tailwind CSS reduce bundle size?**  
  *Ans*: Tailwind uses PurgeCSS/Tree-shaking to remove unused CSS classes during production build generation.
* **Q5: What is Chart.js canvas rendering?**  
  *Ans*: Chart.js renders charts directly onto an HTML5 `<canvas>` element, offering high performance over SVG DOM elements.

---

### Section B: Python, Flask & Backend Architecture (Q101 – Q200)

* **Q101: What is Flask WSGI?**  
  *Ans*: Web Server Gateway Interface is the standard Python specification for web servers to communicate with Python applications.
* **Q102: What is CORS and why is it needed?**  
  *Ans*: Cross-Origin Resource Sharing is a browser security mechanism that controls whether a web app at one origin can request resources from a different origin API.
* **Q103: How does Flask-Limiter protect APIs?**  
  *Ans*: It tracks client IP addresses and returns HTTP 429 Too Many Requests when rate limits (e.g., 100 req/min) are exceeded.
* **Q104: What is PyMongo?**  
  *Ans*: The official Python driver for interacting with MongoDB document databases.
* **Q105: How does thread safety work in Python Flask?**  
  *Ans*: Flask uses thread-local contexts (`request`, `g`) to isolate data across concurrent HTTP worker threads.

---

### Section C: Machine Learning, Scikit-Learn & AI (Q201 – Q300)

* **Q201: Why use Random Forest for tabular log data?**  
  *Ans*: Random Forest handles non-linear relationships, resists overfitting, provides feature importance metrics, and executes inference in $< 2\text{ ms}$.
* **Q202: What is a Confusion Matrix?**  
  *Ans*: A summary table evaluating model performance by comparing True Positives, True Negatives, False Positives, and False Negatives.
* **Q203: What is ROC-AUC score?**  
  *Ans*: Area Under the Receiver Operating Characteristic Curve measuring model discrimination ability across operational classification thresholds (Garuda AI score: 0.996).
* **Q204: What is Google Gemini 1.5 Flash?**  
  *Ans*: A high-speed, 1-million token context multimodal generative AI model optimized for low-latency text synthesis and structured JSON generation.
* **Q205: What is prompt engineering?**  
  *Ans*: Designing precise system instructions and contextual constraints to guide LLM outputs reliably without hallucination.

---

### Section D: Security, Auth & Cryptography (Q301 – Q400)

* **Q301: What is JWT HS256?**  
  *Ans*: HMAC with SHA-256 hashing algorithm used to cryptographically sign JSON Web Tokens using a symmetric secret key.
* **Q302: What is AES-256 Fernet encryption?**  
  *Ans*: An implementation of AES-128/256 in CBC mode with PKCS7 padding and HMAC-SHA256 authentication for secure data storage.
* **Q303: What is Bcrypt password hashing?**  
  *Ans*: A adaptive hash function incorporating configurable salt rounds ($2^{12}$) to resist offline hardware dictionary attacks.
* **Q304: What is the Principle of Least Privilege (PoLP)?**  
  *Ans*: Granting users only the minimum permissions required to perform their current job function.
* **Q305: What is a JIT Access Token?**  
  *Ans*: A single-use, time-bounded (15m/60m) token granting temporary elevated administrative privileges.

---

### Section E: Database, System Design & Edge Cases (Q401 – Q500)

* **Q401: Why choose MongoDB BSON over JSON?**  
  *Ans*: BSON (Binary JSON) supports additional data types (Date, ObjectId, Binary data) and allows faster internal traversal.
* **Q402: How do MongoDB compound indexes work?**  
  *Ans*: Indexes built on multiple fields (e.g., `{ employee_id: 1, timestamp: -1 }`) optimize multi-condition query execution.
* **Q403: What is the JSON Fallback Engine in Garuda AI?**  
  *Ans*: A thread-safe in-memory document store that takes over seamlessly if the primary MongoDB database connection drops.
* **Q404: What triggers an autonomous employee workstation lock?**  
  *Ans*: Trust Score $< 30.0$, Bot Probability $> 80.0\%$, or a MALICIOUS Virtual AI Sandbox verdict.
* **Q405: What is the clean score recovery rate in Garuda AI?**  
  *Ans*: $+0.5\text{ points}$ per full calendar day of zero security infractions up to a maximum cap of 100.0.

---

## 📝 4. Technical Interview Quick Revision Cheat Sheet

```
+-----------------------------------------------------------------------------------+
|                        GARUDA AI QUICK REVISION CHEAT SHEET                       |
+-----------------------------------------------------------------------------------+
|  TRUST SCORE FORMULA  : T_current = min(100, max(0, 100 - sum(D_i) + Clean_Days * 0.5))|
|  SEVERITY DEDUCTIONS  : Low: -5 | Med: -10 | High: -20 | Critical: -30            |
|  LOCK THRESHOLD       : Trust Score < 30.0 OR Sandbox = MALICIOUS                 |
|  ML MODEL METRICS     : Random Forest (CERT R4.2): 98.4% Accuracy | 0.996 ROC-AUC |
|  FAILOVER STRATEGY    : Gemini Multi-Key Pool (Round-Robin / LRU / 60s CoolDown)  |
|  JIT TOKEN DURATION   : Ephemeral Time-Bound (15m / 60m)                          |
+-----------------------------------------------------------------------------------+
```
