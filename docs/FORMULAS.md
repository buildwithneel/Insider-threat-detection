# 📐 Garuda AI: Mathematical Foundations, Equations & Scoring Formulas

> **Complete Mathematical Specification & Worked Numerical Examples**  
> *Cross-Reference: [SCORING_ENGINE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SCORING_ENGINE.md) | [DECISION_MATRIX.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/DECISION_MATRIX.md)*

---

## 📌 1. Executive Mathematical Overview

Garuda AI quantifies human risk, machine identity confidence, and system threat levels using rigorous, deterministic mathematical equations. Every score is bounded and normalized to standard numerical ranges (typically $0.0 \text{ to } 100.0$).

---

## 2. Core Mathematical Formulas

---

### 2.1 Dynamic Behavioral Trust Score Formula

The core equation governing employee Trust Score calculation over chronological security events:

$$T_{current} = \min \left( 100.0, \, \max \left( 0.0, \, T_{initial} - \sum_{i=1}^{N} D_i + \min\left(5.0, \, \Delta_{days} \times R_{clean}\right) \right) \right)$$

#### Variables
* $T_{current}$: Current rolling Trust Score ($0.0 \le T_{current} \le 100.0$).
* $T_{initial}$: Initial baseline score ($100.0$).
* $N$: Total number of security events evaluated.
* $D_i$: Point deduction associated with event $i$.
* $\Delta_{days}$: Number of consecutive clean days without security infractions.
* $R_{clean}$: Daily recovery rate coefficient ($0.5 \text{ points/day}$).

#### Severity Weight Matrix ($D_i$)
* **Low Severity**: $5.0 \text{ points}$ (e.g., After-hours logon).
* **Medium Severity**: $10.0 \text{ points}$ (e.g., USB connection, restricted file access).
* **High Severity**: $20.0 \text{ points}$ (e.g., Unauthorized privilege escalation, mass transfer $> 1\text{ GB}$).
* **Critical Severity**: $30.0 \text{ points}$ (e.g., Identity automation detected, malicious sandbox verdict).

#### Worked Numerical Example
1. Employee starts at $T_{initial} = 100.0$.
2. Day 1: Connects unknown USB (Medium, $-10.0$) and opens confidential file (Medium, $-10.0$).  
   $$T_1 = 100.0 - 10.0 - 10.0 = 80.0$$
3. Days 2–5: 3 clean days elapse ($\Delta_{days} = 3, R_{clean} = 0.5$).  
   $$\text{Recovery} = 3 \times 0.5 = +1.5 \text{ points}$$  
   $$T_2 = 80.0 + 1.5 = 81.5$$

#### Advantages & Limitations
* **Advantage**: Provides predictable, smooth risk degradation with realistic recovery incentive.
* **Limitation**: Linear deduction step functions can be sensitive to event ordering.

---

### 2.2 System Risk Score Formula

Calculates the inverse relationship between Trust Score and overall system risk:

$$R_{system} = 100.0 - T_{current}$$

#### Worked Example
If an employee's Trust Score $T_{current} = 12.5$:
$$R_{system} = 100.0 - 12.5 = 87.5 \quad (\text{Critical System Risk})$$

---

### 2.3 Human Confidence Percentage Formula

Quantifies the likelihood that user interactions originate from a organic human based on telemetry flight time variance ($\sigma_{flight}$) and mouse Bezier curvature ratio ($C_{bezier}$):

$$H_{conf} = 100.0 \times \left( w_1 \cdot \frac{\sigma_{flight}}{\sigma_{max}} + w_2 \cdot C_{bezier} + w_3 \cdot (1.0 - R_{linear}) \right)$$

#### Variables
* $w_1 = 0.4, w_2 = 0.35, w_3 = 0.25$ (Weight coefficients summing to $1.0$).
* $\sigma_{flight}$: Typing flight time standard deviation.
* $C_{bezier}$: Mouse trajectory Bezier curvature ratio ($0.0 \le C_{bezier} \le 1.0$).
* $R_{linear}$: Straight-line point-to-point mouse ratio ($1.0$ = pure script bot).

#### Worked Example
For a normal human user ($\sigma_{flight} = 42.1\text{ms}, C_{bezier} = 0.94, R_{linear} = 0.08$):
$$H_{conf} = 100.0 \times (0.4(0.95) + 0.35(0.94) + 0.25(0.92)) = 93.9\%$$

---

### 2.4 Machine / Bot Confidence Formula

The direct complement of Human Confidence:

$$M_{conf} = 100.0 - H_{conf}$$

#### Worked Example
For an automated Python script where $H_{conf} = 14.0\%$:
$$M_{conf} = 100.0 - 14.0 = 86.0\% \quad (\text{Automation Confirmed})$$

---

### 2.5 Overall Identity Score Formula

Combines behavioral consistency and human confidence into a single unified identity verification metric:

$$I_{score} = 0.60 \times H_{conf} + 0.40 \times B_{consistency}$$

#### Worked Example
Given $H_{conf} = 96.0\%$ and $B_{consistency} = 94.0\%$:
$$I_{score} = (0.60 \times 96.0) + (0.40 \times 94.0) = 57.6 + 37.6 = 95.2$$

---

### 2.6 Virtual Sandbox Risk Score Formula

Evaluates intercepted command strings based on threat indicators:

$$S_{risk} = \min \left( 100, \, \sum_{k=1}^{M} W_k \right)$$

Where $W_k$ represents indicator severity weights:
* Base64 Obfuscation Flag: $+35$
* Execution Policy Bypass: $+30$
* Unsanctioned USB Target Path: $+30$
* System Directory Modifications: $+25$

#### Worked Example
Command: `powershell.exe -ExecutionPolicy Bypass -EncodedCommand ...`
$$S_{risk} = 35 + 30 = 65 \quad (\text{Verdict: SUSPICIOUS / HIGH RISK})$$

---

### 2.7 Threat Probability Formula ($P_{threat}$)

Calculated using a Logistic Sigmoid Function applied to accumulated threat deductions:

$$P_{threat} = \frac{1}{1 + e^{-k(R_{system} - R_{threshold})}}$$

Where $k = 0.1$ (logistic growth steepness) and $R_{threshold} = 50.0$.

---

### 2.8 Just-In-Time (JIT) Access Time Expiration Formula

Time remaining until token invalidation:

$$t_{rem} = \max\left(0, \, t_{expire} - t_{current}\right)$$

Where $t_{expire} = t_{issue} + (M_{duration} \times 60)$.

---

## 3. Summary Formula Quick Reference Table

| Formula Name | Output Range | Key Input Variables | Target Threshold |
|---|---|---|---|
| **Trust Score** ($T_{current}$) | $0.0 \text{ to } 100.0$ | Severity deductions, Clean days | $< 30.0$ triggers Lock |
| **System Risk** ($R_{system}$) | $0.0 \text{ to } 100.0$ | $100 - T_{current}$ | $> 70.0$ triggers Alert |
| **Human Confidence** ($H_{conf}$) | $0.0\% \text{ to } 100.0\%$ | Typing variance, Bezier mouse curve | $< 30.0\%$ indicates Bot |
| **Sandbox Risk** ($S_{risk}$) | $0 \text{ to } 100$ | Command threat indicators | $\ge 70$ is Malicious |
