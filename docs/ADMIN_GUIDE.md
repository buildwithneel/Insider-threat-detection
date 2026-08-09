# 👑 Garuda AI: System Administrator & Governance Guide

> **Enterprise Administration, Security Operations Management & Governance Reference**  
> *Target Audience: System Administrators, Chief Information Security Officers (CISOs), Enterprise IT Leads*  
> *Cross-Reference: [USER_MANUAL.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/USER_MANUAL.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 1. Administrative Responsibilities & Scope

As a Garuda AI System Administrator, you manage user identities, configure scoring weights, control Gemini API failover pools, audit JIT privilege elevations, and handle employee workstation unlocks.

---

## 2. Core Administrative Operations

---

### 2.1 Managing Gemini API Key Failover Pool (`backend/ai_gateway.py`)

Garuda AI maintains high availability for AI incident report generation by balancing requests across a multi-key pool.

#### Adding New API Keys to Pool
Open `.env` at the root directory and add sequential environment key variables:

```env
GEMINI_API_KEY_1=AIzaSy...Key1...
GEMINI_API_KEY_2=AIzaSy...Key2...
GEMINI_API_KEY_3=AIzaSy...Key3...
```

#### Configuring Key Load Balancing Strategy
In `backend/ai_gateway.py`, administrators can set the active routing policy:
* `ROUND_ROBIN` (Default): Sequential key distribution.
* `LEAST_RECENTLY_USED`: Prefers keys with longest idle times.
* `PRIORITY_BASED`: Uses Key 1 until quota depleted, then shifts to Key 2.

---

### 2.2 Unlocking Locked Employee Workstations

When an employee workstation triggers an autonomous security lock (`is_locked = true`), administrators can restore access:

1. Open the **User Governance & RBAC Portal** (`RbacUserManagementModal.jsx`).
2. Search for the locked employee ID (e.g., `EMP032`).
3. Click **View Unlock Credentials**.
4. Retrieve the auto-generated 16-character cryptographic unlock key (`GARUDA-UNLOCK-XXXX-XXXX`).
5. Confirm identity with the employee and submit the key to execute `/api/employees/unlock`.

---

### 2.3 Managing User Roles & RBAC Matrix (`backend/security/rbac_middleware.py`)

Administrators assign users to explicit system roles:

| Role Name | Access Scope | Description |
|---|---|---|
| `Employee` | Read-only personal status | Default user role. Cannot access SOC dashboard. |
| `SOC_Analyst_Tier1` | Read SOC Dashboard, Recalculate Scores | Triage alerts and review timelines. |
| `SOC_Lead` | Full SOC Dashboard + JIT Elevation | Full operational access including JIT approvals. |
| `Admin` | Full System Control | Unrestricted administrative access. |

---

### 2.4 Reviewing System Audit Logs (`AuditLogsView.jsx`)

Garuda AI captures immutable audit trails for every security-sensitive operation:
* JIT Access Requests and Approvals
* Workstation Lock and Unlock Events
* Manual Score Recalculation Triggers
* Admin Configuration Changes

To export audit logs for compliance:
```bash
# Export MongoDB Audit Collection to JSON:
mongoexport --db garudaai --collection audit_logs --out audit_logs_export.json
```

---

## 3. Database Backup & Disaster Recovery Procedures

### 3.1 MongoDB Automated Backup Script
Create a daily cron job running `scripts/backup_db.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/garudaai/$(date +%Y%m%m_%H%M%S)"
mkdir -p "$BACKUP_DIR"
mongodump --uri="mongodb://localhost:27017/garudaai" --out="$BACKUP_DIR"
echo "Garuda AI Backup completed cleanly at $BACKUP_DIR"
```

---

### 3.2 High-Availability JSON Fallback Mode Verification
To verify system resilience during database outages, temporarily stop the MongoDB service:

```bash
# Windows:
net stop MongoDB

# Linux:
sudo systemctl stop mongodb
```
*Garuda AI will instantly display `[DEBUG_LOG] PyMongo connection offline. Initializing Thread-Safe JSON Fallback Engine.` in backend logs without crashing client sessions.*
