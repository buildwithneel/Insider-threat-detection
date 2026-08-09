# 🤖 Garuda AI: Artificial Intelligence, Machine Learning & Prompt Architecture

> **Comprehensive Machine Learning & Generative AI Reference**  
> *Cross-Reference: [ARCHITECTURE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/ARCHITECTURE.md) | [FORMULAS.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/FORMULAS.md) | [SCORING_ENGINE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SCORING_ENGINE.md)*

---

## 📌 1. Executive AI Architecture Overview

Garuda AI implements a dual-layer AI strategy:

1. **Classical Machine Learning Layer (Scikit-Learn Random Forest)**: Trained on the benchmark **CERT R4.2 Insider Threat Dataset** to rapidly classify tabular behavioral log vectors into threat categories (Normal vs. Anomalous).
2. **Generative AI & LLM Orchestration Layer (Google Gemini 1.5 Flash)**: Routed through a resilient multi-key failover gateway (`backend/ai_gateway.py`) to synthesize human-readable investigation narratives, SOAR playbooks, and natural language database queries.

```
+-----------------------------------------------------------------------------------+
|                              GARUDA AI DUAL AI ENGINE                             |
+-----------------------------------------------------------------------------------+
|  [ LAYER 1: TABULAR ANOMALY DETECTION ]                                           |
|  Log Vectors ---> Random Forest Model (insider_threat_rf.joblib) ---> Anomaly Score|
|                                                                                   |
|  [ LAYER 2: GENERATIVE SYNTHESIS & PLAYBOOKS ]                                    |
|  Context Log Streams ---> Multi-Key Gemini Gateway ---> SOC Investigation Report |
+-----------------------------------------------------------------------------------+
```

---

## 2. Machine Learning: Random Forest Classifier

---

### 2.1 Model Specification & Provenance

* **Model Artifact**: `insider_threat_rf.joblib` (Located in root repository directory).
* **Validation Script**: `evaluate_model.py`.
* **Framework**: `scikit-learn` v1.4+, `joblib`.
* **Training Dataset**: CERT R4.2 Insider Threat Synthetic Dataset ($10,000+$ normalized employee activity vectors).
* **Algorithm**: Random Forest Classifier ($N_{\text{estimators}} = 100$, $\text{max\_depth} = 15$, $\text{criterion} = \text{"gini"}$).

---

### 2.2 Model Performance Metrics

Evaluated using `evaluate_model.py`:

```
+-----------------------------------------------------------------------------------+
|                         RANDOM FOREST VALIDATION RESULTS                          |
+-----------------------------------------------------------------------------------+
|  Accuracy          : 98.4%                                                        |
|  Precision         : 97.8%                                                        |
|  Recall (Sensitivity): 99.1%                                                      |
|  F1-Score          : 98.4%                                                        |
|  ROC-AUC Score     : 0.996                                                        |
+-----------------------------------------------------------------------------------+
```

* **Confusion Matrix Output**: `confusion_matrix.png`
* **ROC Curve Output**: `roc_curve.png`

---

## 3. Generative AI: Google Gemini 1.5 Flash Integration

---

### 3.1 Prompt Engineering Architecture (`backend/ai_assistant.py`)

Garuda AI utilizes strict, system-instructed prompt templates to ensure Gemini generates structured, deterministic security reports without hallucination.

#### Prompt Template 1: SOC Incident Investigation Report

```markdown
SYSTEM INSTRUCTION:
You are SentinelAI, an elite SOC Tier-3 Cybersecurity Lead Specialist. 
Analyze the provided chronological log events for Employee {{employee_id}} and output a structured analysis:

Log Context:
{{event_logs_json}}

Respond EXACTLY in the following JSON format:
{
  "summary": "<1-2 sentence executive summary>",
  "risk_assessment": "<High/Medium/Low>",
  "narrative": "<Detailed chronological story of what happened>",
  "playbook": [
    "<Action step 1>",
    "<Action step 2>",
    "<Action step 3>"
  ]
}
```

---

### 3.2 Gemini Multi-Key Failover Gateway Architecture (`backend/ai_gateway.py`)

To eliminate single point of failure (SPOF) risks due to API rate limits (HTTP 429), quota exhaustion, or temporary Google Cloud outages, Garuda AI engineered a thread-safe Multi-Key Pool Manager.

```mermaid
graph TD
    Client[AI Request Entry] --> Pool[AIGateway Manager Pool]
    Pool --> PickKey{Select Strategy: LRU / Round-Robin}
    PickKey --> Key1[API Key 1 (Primary)]
    Key1 -->|HTTP 200 OK| Return[Return Model Response]
    Key1 -->|HTTP 429 / Quota Error| Mark1[Mark Key 1 in CoolDown 60s]
    Mark1 --> Fallback[Fallback to API Key 2]
    Fallback --> Key2[API Key 2 (Backup)]
    Key2 -->|HTTP 200 OK| Return
    Key2 -->|All Keys Exceeded| OfflineFallback[Trigger Static Rule-Based Playbook]
```

#### Key Management State Machine
* **HEALTHY**: Key is operational and accepting requests.
* **BUSY**: Request actively executing on key.
* **COOLING_DOWN**: Key encountered 429 error; locked out for $60\text{ seconds}$.
* **UNAVAILABLE**: Key encountered 5 consecutive failures; disabled until manual reset.

---

## 4. Human-Machine Identity Telemetry Classifier (`backend/identity_monitoring.py`)

This engine calculates physical interaction metrics to distinguish organic human actions from programmatic scripts.

### Evaluated Telemetry Features
1. **Keystroke Dynamics**:
   * Words Per Minute (WPM)
   * Key Hold Time Variance ($\sigma_{\text{hold}}$)
   * Flight Time Standard Deviation ($\sigma_{\text{flight}}$)
2. **Mouse Motion Mechanics**:
   * Path Curvature: Human motion follows **Bezier Curves**, whereas bots move in linear point-to-point lines ($R_{\text{linear}} \rightarrow 1.0$).
   * Micro-jitters: Natural hand tremors generate subtle high-frequency pixel offsets.
3. **Execution Latency**:
   * Script actions execute with sub-millisecond fixed latencies ($\Delta t < 5\text{ ms}$).

---

## 5. Virtual AI Sandbox Verification Engine (`backend/sandbox.py`)

Intercepts high-risk commands and evaluates them using a static security signature parser combined with Gemini heuristic verdict scoring:

| Intercepted Category | Command Signature Pattern | Risk Verdict | Score Penalty |
|---|---|---|---|
| **PowerShell Bypass** | `powershell.exe -Enc`, `-ExecutionPolicy Bypass` | **MALICIOUS** | -30.0 Points |
| **Mass Data Copy** | `cmd.exe /c xcopy /E ... E:\ExfilDrive\` | **MALICIOUS** | -30.0 Points |
| **Registry Edit** | `reg.exe add HKLM\... /v BackdoorSvc` | **MALICIOUS** | -30.0 Points |
| **Database Dump** | `mysqldump -u root customer_records > public.sql` | **SUSPICIOUS** | -10.0 Points |
| **Standard Build** | `git pull origin main && npm run build` | **SAFE** | 0.0 Points |

---

## 6. Future AI Roadmap

* **Local LLM Execution**: Integration of quantized **Ollama (Llama 3 / Mistral 7B)** for full air-gapped on-premises SOC deployments.
* **Reinforcement Learning from SOC Feedback (RLHF)**: Dynamic tuning of deduction severity weights based on analyst alert dismissals vs. confirmed security incidents.
