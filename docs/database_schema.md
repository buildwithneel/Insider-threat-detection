# 🗄️ Garuda AI: Database Schema & High-Availability Data Architecture

> **Comprehensive Database Specification & Data Dictionary**  
> *Cross-Reference: [ARCHITECTURE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/ARCHITECTURE.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 1. Database Architectural Overview

Garuda AI relies on a **NoSQL Document Database Architecture** powered by MongoDB (with a thread-safe JSON file fallback engine managed by `backend/db_client.py`).

Cybersecurity logs, behavioral telemetry streams, and identity cadence records are unstructured and dynamic. Document databases allow Garuda AI to store complex, nested security details (e.g., file paths, network packet metadata, mouse Bezier curve coordinates) without requiring rigid `ALTER TABLE` operations or complex multitable SQL `JOIN` bottlenecks.

```
+-----------------------------------------------------------------------------------+
|                            GARUDA AI MONGODB DATA STORE                           |
+-----------------------------------------------------------------------------------+
|  COLLECTIONS:                                                                     |
|  ├── employees          : Core user profile, trust scores, lock status            |
|  ├── events             : Chronological security log streams (Logon, File, USB)   |
|  ├── alerts             : Triggered SOC incidents & security violations          |
|  ├── timeline           : Aggregated & collapsed threat timeline records          |
|  ├── audit_logs         : System administration & JIT access audit trails         |
|  ├── users              : Authentication & RBAC credentials                       |
|  ├── jit_tokens         : Time-bounded JIT access tokens                          |
|  ├── sandbox_history    : Virtual sandbox execution results & verdicts            |
|  └── identity_telemetry : Human vs Bot physical cadence metrics                   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Collection Data Dictionaries

---

### 2.1 Collection: `employees`

Stores corporate employee profiles, current rolling Trust Scores, risk status, and security lock credentials.

* **Primary Key**: `employee_id` (Indexed, Unique)
* **Sample BSON Document**:
```json
{
  "_id": "662a8b9f10c3d9a4f2100001",
  "employee_id": "EMP032",
  "name": "Alex Mercer",
  "role": "Lead DevOps Engineer",
  "department": "Infrastructure",
  "trust_score": 12.5,
  "status": "Critical",
  "is_locked": true,
  "locked_reason": "Automated script exfiltration and high-risk sandbox malicious verdict",
  "locked_at": "2026-07-25T02:18:00Z",
  "unlock_key": "GARUDA-UNLOCK-98A4-71CF",
  "reasons": [
    "identity_automation_detected (-30.0)",
    "massive_data_transfer (-20.0)",
    "sandbox_malicious (-30.0)"
  ],
  "updated_at": "2026-07-25T02:18:00Z"
}
```

---

### 2.2 Collection: `events`

Contains raw security log events ingested from operating systems, file servers, network proxies, and USB drivers.

* **Primary Key**: `_id` (ObjectId)
* **Indexes**: `employee_id` (1), `timestamp` (-1), `type` (1)
* **Sample BSON Document**:
```json
{
  "_id": "662a8b9f10c3d9a4f2100002",
  "employee_id": "EMP032",
  "timestamp": "2026-07-25T02:16:30Z",
  "type": "file",
  "severity": "High",
  "details": {
    "action": "bulk_download",
    "filename": "customer_financial_records_2026.csv",
    "file_sensitivity": "Restricted",
    "file_size_mb": 1450.0,
    "destination": "E:\\ExfilDrive\\"
  }
}
```

---

### 2.3 Collection: `identity_telemetry`

Stores physical human-machine telemetry variables capturing typing dynamics and mouse behavior.

* **Primary Key**: `telemetry_id` (String / ObjectId)
* **Foreign Key**: `employee_id` $\rightarrow$ `employees.employee_id`
* **Sample BSON Document**:
```json
{
  "_id": "662a8b9f10c3d9a4f2100003",
  "employee_id": "EMP032",
  "timestamp": "2026-07-25T02:15:00Z",
  "profile_id": "python_script",
  "human_confidence": 14.0,
  "machine_confidence": 86.0,
  "bot_probability": 92.0,
  "behaviour_consistency": 22.0,
  "overall_identity_score": 18.0,
  "telemetry": {
    "typing_wpm": 420,
    "flight_time_stdev": 0.2,
    "mouse_path_type": "None (Disembodied)",
    "micro_jitters": 0,
    "straight_line_ratio": 1.0,
    "headless_browser": true
  },
  "status": "Automation Detected"
}
```

---

### 2.4 Collection: `sandbox_history`

Tracks actions intercepted and executed inside the Virtual AI Sandbox environment.

* **Sample BSON Document**:
```json
{
  "_id": "662a8b9f10c3d9a4f2100004",
  "sandbox_id": "SB-884920",
  "employee_id": "EMP032",
  "command": "powershell.exe -ExecutionPolicy Bypass -EncodedCommand SQBFA...",
  "category": "PowerShell execution",
  "verdict": "MALICIOUS",
  "risk_score": 95,
  "threat_indicators": [
    "Obfuscated Base64 payload",
    "Execution Policy Bypass Flag",
    "Direct memory invocation"
  ],
  "evaluated_at": "2026-07-25T02:17:00Z"
}
```

---

### 2.5 Collection: `jit_tokens`

Stores Just-In-Time privileged access tokens generated for temporary elevation.

* **Sample BSON Document**:
```json
{
  "_id": "662a8b9f10c3d9a4f2100005",
  "token_id": "JIT-TOK-99410A",
  "employee_id": "EMP015",
  "requested_role": "Database Admin",
  "duration_minutes": 15,
  "reason": "Emergency production schema patch",
  "approved_by": "admin@garuda.ai",
  "status": "ACTIVE",
  "created_at": "2026-07-25T02:00:00Z",
  "expires_at": "2026-07-25T02:15:00Z"
}
```

---

## 3. Database Indexes & Query Optimizations

Garuda AI enforces compounding compound indexes to guarantee sub-5ms query response times:

```javascript
// Index 1: Fast Employee Event Timeline Fetching
db.events.createIndex({ "employee_id": 1, "timestamp": -1 });

// Index 2: Rapid High-Severity Alert Queries
db.alerts.createIndex({ "severity": 1, "status": 1 });

// Index 3: JIT Token Expiration Verification
db.jit_tokens.createIndex({ "token_id": 1, "expires_at": 1 });

// Index 4: User Search & Authentication
db.users.createIndex({ "email": 1 }, { unique: true });
```

---

## 4. Aggregation Pipelines

### SOC Threat Score Trend Aggregation Pipeline
This pipeline groups trust score point deductions over a 30-day window per employee:

```javascript
db.events.aggregate([
  { $match: { employee_id: "EMP032" } },
  { $sort: { timestamp: 1 } },
  {
    $group: {
      _id: { $dateToString: { format: "%Y-%m-%d", date: "$timestamp" } },
      event_count: { $sum: 1 },
      high_severity_count: {
        $sum: { $cond: [ { $eq: [ "$severity", "High" ] }, 1, 0 ] }
      }
    }
  },
  { $sort: { "_id": 1 } }
]);
```

---

## 5. Architectural Comparison: MongoDB vs Relational SQL

| Metric | MongoDB (Garuda AI Choice) | Relational SQL (PostgreSQL/MySQL) |
|---|---|---|
| **Schema Paradigm** | Dynamic Document Schemas | Strict Fixed Tables |
| **Ingestion Throughput** | $50,000+\text{ write ops/sec}$ | $8,000-15,000\text{ write ops/sec}$ |
| **Nested Data Storage** | Native JSON array storage | Requires normalization or stringified JSON |
| **Schema Migration Impact**| Zero downtime schema updates | Requires lock-heavy `ALTER TABLE` |
| **Garuda AI Rationale** | Essential for fast ingestion of unpredictable security telemetry. | Rejected due to rigid schema constraints. |
