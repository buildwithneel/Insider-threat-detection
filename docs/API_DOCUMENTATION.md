# 🔌 Garuda AI: REST API Reference & Specification Manual

> **Complete Developer API Reference & Endpoint Specification**  
> *Base URL*: `http://localhost:5000/api`  
> *Cross-Reference: [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md) | [DATABASE_SCHEMA.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/DATABASE_SCHEMA.md)*

---

## 📌 1. Authentication & Common Headers

All protected endpoints require HTTP Bearer JWT Authentication or custom X-Headers:

```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
Content-Type: application/json
X-JIT-Token: <JIT_ACCESS_TOKEN>  (Required for privileged JIT routes)
```

---

## 2. Authentication & User RBAC APIs

---

### 2.1 Login User (`POST /api/auth/login`)

#### Purpose
Authenticates SOC analysts, admins, or employees and returns a signed JWT access token.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "email": "admin@garuda.ai",
  "password": "SuperSecretPassword2026!"
}
```

#### Response (`200 OK`)
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "admin@garuda.ai",
    "role": "Admin",
    "name": "Security Administrator"
  }
}
```

---

## 3. Employee & Trust Score APIs

---

### 3.1 List All Employees (`GET /api/employees`)

#### Purpose
Retrieves all employee profiles with their rolling Trust Scores, risk status, and lock state.

#### Response (`200 OK`)
```json
[
  {
    "employee_id": "EMP032",
    "name": "Alex Mercer",
    "role": "Lead DevOps Engineer",
    "department": "Infrastructure",
    "trust_score": 12.5,
    "status": "Critical",
    "is_locked": true,
    "locked_reason": "High Risk Sandbox Execution",
    "unlock_key": "GARUDA-UNLOCK-98A4-71CF"
  },
  {
    "employee_id": "EMP015",
    "name": "Sarah Jenkins",
    "role": "Financial Analyst",
    "department": "Finance",
    "trust_score": 88.0,
    "status": "Healthy",
    "is_locked": false
  }
]
```

---

### 3.2 Recalculate Trust Score (`POST /api/employees/<employee_id>/recalculate`)

#### Purpose
Triggers an immediate algorithmic recalculation of an employee's Trust Score.

#### Response (`200 OK`)
```json
{
  "employee_id": "EMP032",
  "previous_score": 42.5,
  "new_score": 12.5,
  "deductions_applied": [
    "identity_automation_detected (-30.0)",
    "massive_data_transfer (-20.0)"
  ],
  "status": "Critical"
}
```

---

## 4. Virtual AI Sandbox Verification APIs

---

### 4.1 Evaluate Command Action (`POST /api/sandbox/evaluate`)

#### Purpose
Evaluates a high-risk command string inside the virtual sandbox prior to host execution.

#### Request Body
```json
{
  "employee_id": "EMP032",
  "command": "powershell.exe -ExecutionPolicy Bypass -EncodedCommand SQBFA...",
  "category": "PowerShell execution"
}
```

#### Response (`200 OK`)
```json
{
  "sandbox_id": "SB-99382",
  "verdict": "MALICIOUS",
  "risk_score": 95,
  "description": "Obfuscated Base64 PowerShell execution bypassing host execution policy",
  "score_deduction": 30.0,
  "action_taken": "Execution Blocked. Employee Workstation Locked."
}
```

---

## 5. Human-Machine Identity Monitoring APIs

---

### 5.1 Analyze User Telemetry (`POST /api/identity/analyze`)

#### Purpose
Analyzes physical mouse coordinates, typing flight times, and API cadences to classify human vs. bot interaction.

#### Request Body
```json
{
  "employee_id": "EMP032",
  "profile_id": "python_script"
}
```

#### Response (`200 OK`)
```json
{
  "employee_id": "EMP032",
  "human_confidence": 14.0,
  "machine_confidence": 86.0,
  "bot_probability": 92.0,
  "behaviour_consistency": 22.0,
  "overall_identity_score": 18.0,
  "status": "Automation Detected",
  "decision": "High Risk - Workstation Lock Initiated"
}
```

---

## 6. Just-In-Time (JIT) PAM Access APIs

---

### 6.1 Issue JIT Access Token (`POST /api/jit/tokens/issue`)

#### Purpose
Requests temporary elevation of administrative privileges for 15 or 60 minutes.

#### Request Body
```json
{
  "employee_id": "EMP015",
  "requested_role": "Database Admin",
  "duration_minutes": 15,
  "reason": "Emergency production hotfix"
}
```

#### Response (`200 OK`)
```json
{
  "success": true,
  "token_id": "JIT-TOK-99410A",
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "expires_at": "2026-07-25T02:15:00Z",
  "duration_minutes": 15
}
```

---

### 6.2 Verify JIT Access Token (`POST /api/jit/tokens/verify`)

#### Purpose
Validates the cryptographic authenticity and time expiration of a JIT access token.

#### Request Body
```json
{
  "token_id": "JIT-TOK-99410A"
}
```

#### Response (`200 OK`)
```json
{
  "valid": true,
  "employee_id": "EMP015",
  "requested_role": "Database Admin",
  "time_remaining_seconds": 842
}
```

---

## 7. AI Incident Assistant & Gateway APIs

---

### 7.1 Generate AI Incident Investigation Report (`POST /api/ai/investigate`)

#### Purpose
Requests Google Gemini AI to analyze an employee's recent events and generate a plain-English SOC investigation report and SOAR containment playbook.

#### Request Body
```json
{
  "employee_id": "EMP032"
}
```

#### Response (`200 OK`)
```json
{
  "employee_id": "EMP032",
  "summary": "Employee EMP032 exhibited suspicious behavior including after-hours logon, script execution, and mass file transfers.",
  "narrative": "At 02:14 AM, logon originated from an untrusted IP. Shortly after, powershell scripts transferred 1.4 GB to USB.",
  "playbook": [
    "1. Freeze Active Directory credentials for EMP032 immediately.",
    "2. Revoke active JIT access tokens.",
    "3. Isolate host endpoint on network switch port 12."
  ]
}
```

---

## 8. Summary API HTTP Status Code Reference

| Status Code | Meaning | Cause in Garuda AI |
|---|---|---|
| `200 OK` | Success | Request processed cleanly |
| `400 Bad Request` | Invalid Inputs | Missing payload fields or invalid JSON format |
| `401 Unauthorized` | Auth Failure | Invalid/Expired JWT token or bad unlock key |
| `403 Forbidden` | Access Denied | Insufficient RBAC permission or expired JIT token |
| `429 Too Many Requests` | Rate Limited | Exceeded 100 requests/minute Flask-Limiter cap |
| `500 Internal Error` | Server Exception | Internal logic crash (handled via clean JSON error) |
