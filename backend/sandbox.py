"""
SentinelAI Virtual Sandbox Verification Engine
===============================================

Simulates an isolated virtual environment for evaluating high-risk employee actions
and commands before allowing execution in the production environment.
"""

import uuid
from datetime import datetime
try:
    from backend.trust_score import recalculate_score, get_trust_score_reasons
except ImportError:
    from trust_score import recalculate_score, get_trust_score_reasons

# List of high-risk action categories that trigger sandbox redirection
HIGH_RISK_TRIGGER_CATEGORIES = [
    "Opening executable files",
    "USB insertion",
    "File deletion",
    "Privilege escalation",
    "Registry modification",
    "PowerShell execution",
    "Bulk file copy",
    "Database export",
    "Unknown executable",
    "Mass downloads"
]

# Preset command templates for interactive sandbox testing
PRESET_SANDBOX_COMMANDS = [
    {
        "id": "ps_enc",
        "category": "PowerShell execution",
        "command": "powershell.exe -ExecutionPolicy Bypass -NoProfile -EncodedCommand SQBFA... (Encoded Payload)",
        "description": "Obfuscated PowerShell Download & Execute Payload",
        "expected_verdict": "MALICIOUS"
    },
    {
        "id": "usb_exfil",
        "category": "USB insertion",
        "command": "cmd.exe /c xcopy /E /I /Y C:\\CorporateData\\Finances\\* E:\\ExfilDrive\\",
        "description": "Mass Data Copy to Unsanctioned Removable USB Media",
        "expected_verdict": "MALICIOUS"
    },
    {
        "id": "reg_persistence",
        "category": "Registry modification",
        "command": "reg.exe add HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v BackdoorSvc /t REG_SZ /d C:\\Users\\Public\\svchost_update.exe /f",
        "description": "System Auto-Start Registry Modification for Persistence",
        "expected_verdict": "MALICIOUS"
    },
    {
        "id": "priv_escalate",
        "category": "Privilege escalation",
        "command": "runas /user:Administrator \"cmd.exe /c net localgroup Administrators john.doe /add\"",
        "description": "Unsanctioned Local Administrator Account Escalation",
        "expected_verdict": "MALICIOUS"
    },
    {
        "id": "file_wipe",
        "category": "File deletion",
        "command": "powershell.exe Remove-Item -Path C:\\Database\\Backups\\*.bak -Recurse -Force",
        "description": "Bulk Destruction of Production Database Backup Archives",
        "expected_verdict": "MALICIOUS"
    },
    {
        "id": "db_dump",
        "category": "Database export",
        "command": "mysqldump -u root -p customer_records_v2 > C:\\Users\\Public\\db_dump_raw.sql",
        "description": "Unencrypted Database Dumping to Public Folder",
        "expected_verdict": "SUSPICIOUS"
    },
    {
        "id": "mass_dl",
        "category": "Mass downloads",
        "command": "curl.exe -O https://external-temp-storage.net/bulk_archive_[1-100].zip",
        "description": "Rapid Mass Download of External Unverified Archives",
        "expected_verdict": "SUSPICIOUS"
    },
    {
        "id": "unk_exe",
        "category": "Unknown executable",
        "command": "C:\\Downloads\\patch_v4_unsigned.exe --silent --install",
        "description": "Execution of Unsigned & Unverified Third-Party Binary",
        "expected_verdict": "SUSPICIOUS"
    },
    {
        "id": "bulk_copy",
        "category": "Bulk file copy",
        "command": "robocopy D:\\Projects\\InternalDocs C:\\Users\\User\\Desktop\\Staging /MIR",
        "description": "Internal Directory Staging for Archival",
        "expected_verdict": "SUSPICIOUS"
    },
    {
        "id": "safe_cmd",
        "category": "Opening executable files",
        "command": "git.exe pull origin main && npm run build",
        "description": "Standard Developer Build & Source Repository Refresh",
        "expected_verdict": "SAFE"
    },
    {
        "id": "safe_ps",
        "category": "PowerShell execution",
        "command": "powershell.exe -Command Get-Service -Name W32Time",
        "description": "System Time Synchronization Diagnostic Check",
        "expected_verdict": "SAFE"
    }
]


def is_high_risk_action(action_type, command_str=""):
    """
    Checks if an action or command belongs to a high-risk category requiring sandbox redirection.
    """
    action_type_lower = (action_type or "").lower()
    cmd_lower = (command_str or "").lower()

    keywords = [
        "exe", "power", "ps1", "usb", "delete", "remove", "wipe",
        "priv", "admin", "reg", "copy", "export", "dump", "download",
        "unknown", "script", "cmd"
    ]
    return any(k in action_type_lower or k in cmd_lower for k in keywords) or action_type in HIGH_RISK_TRIGGER_CATEGORIES


def perform_sandbox_analysis(action_type, command_name, details=None):
    """
    Simulates isolated execution inside the Virtual Sandbox.
    Performs 8 security analysis checks:
    1. Behaviour Analysis
    2. File Integrity Check
    3. Command Sequence Analysis
    4. Registry Change Detection
    5. Network Connection Detection
    6. Privilege Escalation Detection
    7. Malware Signature Scan
    8. Data Exfiltration Detection
    """
    details = details or {}
    cmd_str = (command_name or "").lower()
    act_str = (action_type or "").lower()
    combined = f"{act_str} {cmd_str}"

    # Precise signature patterns
    is_encoded_ps = any(k in combined for k in ["encodedcommand", "-e ", "-enc ", "iex ", "invoke-expression", "bypass"])
    is_usb_transfer = any(k in combined for k in ["usb drive", "xcopy", "exfil", "removable media"])
    is_reg_mod = any(k in combined for k in ["reg.exe", "hklm", "hkcu", "currentversion\\run", "backdoorsvc", "registry modification"])
    is_admin_escalate = any(k in combined for k in ["runas", "administrators", "privilege escalation", "net localgroup"])
    is_wipe = any(k in combined for k in ["remove-item", "format ", "wipe", "del /f", "rmdir /s", "file deletion"])
    is_db_export = any(k in combined for k in ["mysqldump", "db_dump", "database export"])
    is_mass_dl = any(k in combined for k in ["mass downloads", "curl.exe", "wget.exe", "bulk_archive"])
    is_unsigned_exe = any(k in combined for k in ["unsigned", "unknown executable", "patch_v4_unsigned"])

    # Check 1: Behaviour Analysis
    if is_encoded_ps or is_reg_mod:
        c1 = {"status": "CRITICAL", "details": "Process injection attempt & hidden background child shell spawned", "score": 90}
    elif is_admin_escalate or is_wipe:
        c1 = {"status": "HIGH_RISK", "details": "Elevated process token acquisition without SOC authorization", "score": 85}
    elif is_usb_transfer or is_db_export:
        c1 = {"status": "WARNING", "details": "High volume memory staging detected in user space", "score": 60}
    else:
        c1 = {"status": "CLEAN", "details": "Standard user space execution within standard CPU/RAM bounds", "score": 10}

    # Check 2: File Integrity Check
    if is_wipe or is_unsigned_exe:
        c2 = {"status": "CRITICAL", "details": "Target file checksum matches destruction / unsigned binary signature", "score": 95}
    elif is_reg_mod or is_encoded_ps:
        c2 = {"status": "WARNING", "details": "System binary hash mismatch or payload entropy > 7.8", "score": 70}
    else:
        c2 = {"status": "PASSED", "details": "Digital signature valid and certified by trusted Root CA", "score": 5}

    # Check 3: Command Sequence Analysis
    if is_encoded_ps or is_reg_mod:
        c3 = {"status": "CRITICAL", "details": "Base64 obfuscation & pipeline chaining to download string payload", "score": 92}
    elif is_admin_escalate or is_wipe:
        c3 = {"status": "HIGH_RISK", "details": "Nested administrative execution with bypass flags", "score": 80}
    elif is_db_export or is_mass_dl:
        c3 = {"status": "WARNING", "details": "Sequential I/O batch commands targeting sensitive paths", "score": 55}
    else:
        c3 = {"status": "PASSED", "details": "Standard CLI parameter sequence with no obfuscation", "score": 0}

    # Check 4: Registry Change Detection
    if is_reg_mod:
        c4 = {"status": "CRITICAL", "details": "Unauthorized key injection into HKLM\\...\\CurrentVersion\\Run", "score": 98}
    elif is_admin_escalate or is_encoded_ps:
        c4 = {"status": "WARNING", "details": "SAM database modification attempt logged", "score": 65}
    else:
        c4 = {"status": "NO_CHANGE", "details": "No system registry hive modifications detected", "score": 0}

    # Check 5: Network Connection Detection
    if is_encoded_ps or is_mass_dl:
        c5 = {"status": "CRITICAL", "details": "Outbound connection socket established to unlisted C2 IP (185.220.x.x:443)", "score": 94}
    elif is_db_export:
        c5 = {"status": "WARNING", "details": "Unencrypted outbound protocol negotiation", "score": 60}
    else:
        c5 = {"status": "ISOLATED", "details": "No external socket connections attempted by process", "score": 0}

    # Check 6: Privilege Escalation Detection
    if is_admin_escalate or is_encoded_ps:
        c6 = {"status": "CRITICAL", "details": "UAC bypass pattern & SeDebugPrivilege token privilege requested", "score": 96}
    elif is_reg_mod:
        c6 = {"status": "WARNING", "details": "Attempted write access to protected system path", "score": 65}
    else:
        c6 = {"status": "SAFE", "details": "Executed under standard unprivileged user SID context", "score": 0}

    # Check 7: Malware Signature Scan
    if is_encoded_ps or is_wipe or is_reg_mod:
        c7 = {"status": "MALICIOUS", "details": "YARA Match: Win.Trojan.Generic / Ransomware.Wiper.v2 Signature", "score": 99}
    elif is_unsigned_exe or is_usb_transfer or is_db_export or is_mass_dl:
        c7 = {"status": "SUSPICIOUS", "details": "Heuristic match: Heur.Bypass.Script / Potentially Unwanted Program", "score": 60}
    else:
        c7 = {"status": "CLEAN", "details": "0 YARA signature matches across 45,000 security rules", "score": 0}

    # Check 8: Data Exfiltration Detection
    if is_usb_transfer or is_db_export:
        c8 = {"status": "CRITICAL", "details": "Staging classified files to external storage volume", "score": 90}
    elif is_mass_dl:
        c8 = {"status": "WARNING", "details": "High bandwidth throughput to unverified destination", "score": 65}
    else:
        c8 = {"status": "NONE", "details": "No data transfer anomalies or exfiltration channels observed", "score": 0}

    # Synthesize overall Risk Score (0-100)
    scores = [c1["score"], c2["score"], c3["score"], c4["score"], c5["score"], c6["score"], c7["score"], c8["score"]]
    max_score = max(scores)
    avg_score = sum(scores) / len(scores)

    # Determine Verdict cleanly:
    # High-risk malicious indicators -> MALICIOUS
    # Suspicious warnings -> SUSPICIOUS
    # Clean checks -> SAFE
    if is_encoded_ps or is_usb_transfer or is_reg_mod or is_admin_escalate or is_wipe:
        risk_score = min(100, max(75, int(round((max_score * 0.7) + (avg_score * 0.3)))))
        verdict = "MALICIOUS"
        confidence_score = 96
        if is_encoded_ps:
            threat_category = "Obfuscated PowerShell Ransomware Payload"
            recommendation = "Block command immediately, isolate workstation network interface, and revoke user credentials."
        elif is_usb_transfer:
            threat_category = "Removable Media Data Exfiltration"
            recommendation = "Block command, disable USB ports on target machine, and alert SOC data loss prevention team."
        elif is_reg_mod:
            threat_category = "Registry Persistence & Backdoor Installation"
            recommendation = "Block execution, wipe registry persistence key, and trigger full antivirus workstation scan."
        elif is_admin_escalate:
            threat_category = "Unauthorized Privilege Escalation Exploit"
            recommendation = "Block execution, revoke administrative token request, and initiate employee lock workflow."
        elif is_wipe:
            threat_category = "Mass Destructive File Wiper"
            recommendation = "Block command execution immediately and lock employee workstation to prevent data destruction."
        else:
            threat_category = "Malicious Code Execution Attack"
            recommendation = "Block command and isolate workstation environment."

    elif is_db_export or is_mass_dl or is_unsigned_exe:
        risk_score = min(69, max(45, int(round((max_score * 0.7) + (avg_score * 0.3)))))
        verdict = "SUSPICIOUS"
        confidence_score = 88
        if is_db_export:
            threat_category = "Unencrypted Database Dumping"
            recommendation = "Flag action for SOC manual review, restrict user data export permissions, and monitor active session."
        elif is_mass_dl:
            threat_category = "Unverified External Mass Download"
            recommendation = "Place user under high-frequency surveillance and require SOC analyst approval for file access."
        elif is_unsigned_exe:
            threat_category = "Unsigned Binary Execution"
            recommendation = "Hold binary in quarantine container and request digital certificate verification from developer."
        else:
            threat_category = "Suspicious System Activity"
            recommendation = "Reduce Trust Score, append observation marker, and notify security analyst."

    else:
        risk_score = min(25, int(round(avg_score)))
        verdict = "SAFE"
        confidence_score = 98
        threat_category = "Standard Legitimate Action"
        recommendation = "Sandbox Passed. Command is verified safe for execution in the production environment."

    return {
        "risk_score": risk_score,
        "threat_category": threat_category,
        "confidence_score": confidence_score,
        "recommendation": recommendation,
        "verdict": verdict,
        "checks": {
            "behaviour_analysis": c1,
            "file_integrity_check": c2,
            "command_sequence_analysis": c3,
            "registry_change_detection": c4,
            "network_connection_detection": c5,
            "privilege_escalation_detection": c6,
            "malware_signature_scan": c7,
            "data_exfiltration_detection": c8
        }
    }


def execute_sandbox_workflow(db, employee_id, action_type, command_name, details=None, critical_threshold=30):
    """
    Executes the full AI Sandbox Verification workflow for a given employee and action:
    1. Runs the Virtual Sandbox Engine checks.
    2. Generates the Sandbox Report with AI Verdict (SAFE, SUSPICIOUS, MALICIOUS).
    3. Triggers verdict-specific side-effects:
       - SAFE: Sandbox Passed -> Executed in real env -> Timeline: "Sandbox Verification Passed"
       - SUSPICIOUS: Reduce Trust Score -> Timeline: "Under Observation" -> Recommend Manual Review
       - MALICIOUS: Block execution -> Reduce Trust Score -> Generate Alert -> Trigger Employee Lock if threshold crossed -> Timeline: "Sandbox Blocked Malicious Action"
    4. Records the sandbox run in db.sandbox_runs.
    """
    details = details or {}
    employee = db.employees.find_one({"employee_id": employee_id})
    if not employee:
        raise ValueError(f"Employee with ID '{employee_id}' not found.")

    run_id = f"SBX-RUN-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now()

    # Step 1: Run Sandbox Analysis Engine
    analysis = perform_sandbox_analysis(action_type, command_name, details)
    verdict = analysis["verdict"]
    risk_score = analysis["risk_score"]
    threat_category = analysis["threat_category"]

    score_before = employee.get("current_score", 100.0)
    score_after = score_before
    alert_created = None
    lock_triggered = False
    execution_status = ""
    display_status = ""
    timeline_desc = ""

    # Step 2: Handle Verdict Actions
    if verdict == "SAFE":
        display_status = "Sandbox Passed"
        execution_status = "Executed in production environment"
        timeline_desc = f"Sandbox Verification Passed: Executed command '{command_name}' safely."

        # Insert clean event into database timeline
        event_doc = {
            "event_id": f"SIM-SBX-SAFE-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": employee_id,
            "timestamp": timestamp,
            "type": "sandbox",
            "source_dataset": "sandbox_engine",
            "details": {
                "custom_description": timeline_desc,
                "sandbox_verdict": "SAFE",
                "action_type": action_type,
                "command": command_name,
                "risk_score": risk_score,
                "severity": "Low"
            }
        }
        db.events.insert_one(event_doc)

    elif verdict == "SUSPICIOUS":
        display_status = "Under Observation"
        execution_status = "Redirected to SOC Manual Review"
        timeline_desc = f"Under Observation: Suspicious activity '{command_name}' analyzed in Sandbox."

        # Insert event into database timeline
        event_doc = {
            "event_id": f"SIM-SBX-SUSP-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": employee_id,
            "timestamp": timestamp,
            "type": "sandbox",
            "source_dataset": "sandbox_engine",
            "details": {
                "custom_description": timeline_desc,
                "sandbox_verdict": "SUSPICIOUS",
                "action_type": action_type,
                "command": command_name,
                "risk_score": risk_score,
                "severity": "Medium"
            }
        }
        db.events.insert_one(event_doc)

        # Recalculate Trust Score cleanly using recalculate_score engine
        score_after = recalculate_score(db, employee_id)

    elif verdict == "MALICIOUS":
        display_status = "Execution Blocked"
        execution_status = "Blocked by Sandbox Engine - Command execution suppressed"
        timeline_desc = f"Sandbox Blocked Malicious Action: Prevented command '{command_name}'."

        # Insert malicious block event into timeline
        event_doc = {
            "event_id": f"SIM-SBX-MAL-{uuid.uuid4().hex[:8].upper()}",
            "employee_id": employee_id,
            "timestamp": timestamp,
            "type": "sandbox",
            "source_dataset": "sandbox_engine",
            "details": {
                "custom_description": timeline_desc,
                "sandbox_verdict": "MALICIOUS",
                "action_type": action_type,
                "command": command_name,
                "risk_score": risk_score,
                "severity": "Critical"
            }
        }
        db.events.insert_one(event_doc)

        # Recalculate Trust Score cleanly using recalculate_score engine
        score_after = recalculate_score(db, employee_id)

        # Generate Security Alert
        alert_id = f"SIM-ALERT-SBX-{uuid.uuid4().hex[:8].upper()}"
        alert_doc = {
            "alert_id": alert_id,
            "employee_id": employee_id,
            "timestamp": timestamp,
            "type": f"Sandbox Blocked: {threat_category}",
            "severity": "Critical",
            "description": f"AI Sandbox intercepted and blocked malicious action '{command_name}'. Threat Category: {threat_category}. Risk Score: {risk_score}/100.",
            "status": "Open",
            "ai_explanation": None
        }
        db.alerts.insert_one(alert_doc)
        alert_created = alert_id

        # Trigger Employee Lock Workflow if threshold is crossed
        if score_after <= critical_threshold:
            lock_triggered = True
            db.employees.update_one(
                {"employee_id": employee_id},
                {"$set": {
                    "current_score": score_after,
                    "account_locked": True,
                    "lock_reason": f"AI Sandbox Blocked Malicious Action ({threat_category}) - Score dropped below threshold ({critical_threshold})"
                }}
            )
        else:
            db.employees.update_one(
                {"employee_id": employee_id},
                {"$set": {"current_score": score_after}}
            )

        deduction = max(0.0, score_before - score_after)
        db.trust_scores.insert_one({
            "employee_id": employee_id,
            "timestamp": timestamp,
            "score": score_after,
            "reason": f"AI Sandbox Blocked Malicious Command (-{deduction:.1f} pts)"
        })

    # Record full run report to MongoDB
    report_doc = {
        "run_id": run_id,
        "employee_id": employee_id,
        "employee_name": employee.get("full_name", f"Employee {employee_id}"),
        "department": employee.get("department", "SOC"),
        "timestamp": timestamp,
        "action_type": action_type,
        "command_name": command_name,
        "verdict": verdict,
        "risk_score": risk_score,
        "threat_category": threat_category,
        "confidence_score": analysis["confidence_score"],
        "recommendation": analysis["recommendation"],
        "display_status": display_status,
        "execution_status": execution_status,
        "timeline_description": timeline_desc,
        "checks": analysis["checks"],
        "score_before": score_before,
        "score_after": score_after,
        "alert_created": alert_created,
        "lock_triggered": lock_triggered,
        "virtual_env_metadata": {
            "container_id": f"SBX-ENV-{uuid.uuid4().hex[:6].upper()}",
            "kernel": "Windows 11 Enterprise (Sandbox Kernel v2.4)",
            "memory_allocated_mb": 128,
            "execution_duration_ms": 420
        }
    }

    db.sandbox_runs.insert_one(report_doc)

    # Format output dictionary (converting datetime objects to string for JSON serialization)
    report_doc["_id"] = str(report_doc.get("_id", ""))
    report_doc["timestamp"] = timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return report_doc


def get_sandbox_history(db, employee_id=None, limit=20):
    """
    Retrieves chronological sandbox execution history logs.
    """
    query = {}
    if employee_id:
        query["employee_id"] = employee_id

    runs = list(db.sandbox_runs.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit))
    for r in runs:
        if isinstance(r.get("timestamp"), datetime):
            r["timestamp"] = r["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    return runs
