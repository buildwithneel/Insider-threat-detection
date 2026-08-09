import os
import sys
import traceback
from datetime import datetime
from pymongo import MongoClient

try:
    from backend.timeline import get_employee_timeline
except ImportError:
    from timeline import get_employee_timeline

try:
    from backend.gemini_client import gemini_service, validate_gemini_environment, get_gemini_api_key
except ImportError:
    from gemini_client import gemini_service, validate_gemini_environment, get_gemini_api_key

# Check environment validity
is_gemini_valid, _env_diag = validate_gemini_environment()
gemini_available = is_gemini_valid
if gemini_available:
    print("Gemini API configured successfully via google-genai SDK.")
else:
    print("Warning: GEMINI_API_KEY or network/validation check failed. Using rule-based fallback for AI Assistant.")


def clean_dept(dept_str):
    if not dept_str:
        return ""
    if " - " in str(dept_str):
        return str(dept_str).split(" - ", 1)[1].strip()
    return str(dept_str).strip()

def get_rule_based_fallback(employee, alert):
    """
    Constructs a detailed, structured, rule-based explanation of the incident
    in case the Gemini API is unavailable or unconfigured.
    """
    name = employee.get("full_name", "Unknown Employee")
    role = employee.get("role", "Staff")
    dept = clean_dept(employee.get("department", "General"))
    score = employee.get("current_score", 100)
    alert_type = alert.get("type", "Anomaly")
    desc = alert.get("description", "")
    
    narrative = f"Investigation details for {name} ({role} in {dept}) concerning Alert: **{alert_type}**.\n\n"
    
    if alert_type == "USB Theft":
        narrative += (
            "### Incident Narrative\n"
            f"Employee {name} executed a remote login outside of standard working hours from an unrecognized terminal. "
            "Shortly thereafter, the user accessed restricted files containing proprietary intellectual property or HR data, "
            "and transferred a massive payload (exceeding 4.0 GB) to a connected USB external storage device.\n\n"
            "### Suspicious Indicators\n"
            "- **After-Hours Auth**: Authenticated during off-hours window.\n"
            "- **Unknown Device Access**: Logged in from a device not registered to their profile.\n"
            "- **Massive Data Exfiltration**: Copied files to USB containing restricted classifications.\n\n"
            "### Business Impact\n"
            "- High risk of intellectual property leakage or trade secret compromise to external entities.\n"
            "- Potential GDPR/regulatory breach depending on file content.\n\n"
            "### Mitigation Playbook\n"
            "1. **Access Revocation**: Immediately freeze user credentials and disable active login sessions.\n"
            "2. **Physical Asset Control**: Recall assigned laptops/devices for physical forensic audit.\n"
            "3. **Incident Response**: Notify legal and HR teams of active data-transfer investigation."
        )
    elif alert_type == "Mass File Download":
        narrative += (
            "### Incident Narrative\n"
            f"Employee {name} performed a high volume of file read requests within a tight chronological window. "
            "The activity patterns indicate bulk harvesting of restricted spreadsheets and financial audit records.\n\n"
            "### Suspicious Indicators\n"
            "- **Bulk Read Spikes**: Excessive document queries (40+ instances in 60 minutes).\n"
            "- **Sensitive File Targeting**: Specifically targeted Restricted financial directories.\n\n"
            "### Business Impact\n"
            "- Exposure of corporate financials, roadmap strategies, or audit vulnerabilities.\n\n"
            "### Mitigation Playbook\n"
            "1. **Restructure Directory Access**: Suspend read permissions for the affected directory.\n"
            "2. **Manager Follow-Up**: Initiate administrative inquiry to verify business need for bulk downloads."
        )
    elif alert_type == "Impossible Travel":
        narrative += (
            "### Incident Narrative\n"
            f"Two authentications were recorded for {name} from locations separated by thousands of miles "
            "within an impossible travel duration (30 minutes between San Francisco and London). Following the second login, "
            "a large database backup file was downloaded and exfiltrated via email to an external competitor domain.\n\n"
            "### Suspicious Indicators\n"
            "- **Impossible Travel Anomaly**: Multi-location logs verify physical location mismatch.\n"
            "- **Compromised Credentials**: High probability of credential harvesting or session hijacking.\n"
            "- **Exfiltration**: Database dump transferred to an unverified external email domain.\n\n"
            "### Business Impact\n"
            "- High probability of compromised customer databases.\n\n"
            "### Mitigation Playbook\n"
            "1. **Session Termination**: Instantly invalidate all active session tokens.\n"
            "2. **Mandatory MFA Reset**: Enforce hardware multi-factor authentication reset.\n"
            "3. **Mail Gateway Block**: Block outbound mails to the target competitor domain."
        )
    elif alert_type == "Privilege Escalation":
        narrative += (
            "### Incident Narrative\n"
            f"The account for {name} experienced a privilege escalation from Standard User to Administrator. "
            "This change was approved by a automated service script without normal ticket routing, after which "
            "the user accessed sensitive mergers & acquisitions planning files.\n\n"
            "### Suspicious Indicators\n"
            "- **Unauthorized Level Shift**: Elevated from standard role without standard workflows.\n"
            "- **Targeted Directory Browsing**: Inspected acquisition strategies immediately post-escalation.\n\n"
            "### Business Impact\n"
            "- Infiltration of executive strategic blueprints and compliance vulnerabilities.\n\n"
            "### Mitigation Playbook\n"
            "1. **Demote Privileges**: Reset user permissions to baseline standard profile.\n"
            "2. **Audit Service Credentials**: Inspect logs of the system account that authorized the change."
        )
    else:
        narrative += (
            "### Incident Narrative\n"
            f"Behavior trust engine flagged anomalous sequence of logs for {name}. "
            f"The events show a score drop to {score}/100, indicating deviations from normal baseline operations.\n\n"
            "### Suspicious Indicators\n"
            f"- **Behavior Score Shift**: Sudden drop to {score}.\n"
            f"- **System Log Details**: {desc}\n\n"
            "### Business Impact\n"
            "- Potential unauthorized data access or staff burnout/risk profiles.\n\n"
            "### Mitigation Playbook\n"
            "1. **Monitor Profile**: Enable strict real-time auditing on this profile.\n"
            "2. **Verify Activity**: Contact employee's manager to confirm routine credentials usage."
        )
        
    return narrative

def generate_ai_explanation(db, alert_id):
    """
    Generates a security incident narrative and containment playbook.
    Checks cache first, calls Gemini API if active, or falls back to rule-based generation.
    """
    alert = db.alerts.find_one({"alert_id": alert_id})
    if not alert:
        return "Error: Alert not found in database."
        
    # 1. Cache hit check
    if alert.get("ai_explanation"):
        return alert["ai_explanation"]
        
    # 2. Get contextual data
    emp_id = alert["employee_id"]
    employee = db.employees.find_one({"employee_id": emp_id})
    if not employee:
        return "Error: Associated employee profile not found."
        
    # Get recent timeline events
    timeline = get_employee_timeline(db, emp_id)
    timeline_summary = "\n".join([
        f"[{t['timestamp']}] Type: {t['type']} | Severity: {t['severity']} | Description: {t['description']}"
        for t in timeline[-25:] # Fetch the latest 25 timeline items for prompt density
    ])

    if not gemini_available:
        # Fallback to rule-based explanation
        explanation = get_rule_based_fallback(employee, alert)
        db.alerts.update_one({"alert_id": alert_id}, {"$set": {"ai_explanation": explanation}})
        return explanation

    # 3. Call Gemini generative model
    try:
        prompt = f"""
You are GarudaAI, an elite AI Cyber Security Incident Response Investigator. 
Analyze the following security alert and employee profile behavior timeline to write an investigation report.

EMPLOYEE METADATA:
- Name: {employee.get('full_name')}
- Role: {employee.get('role')}
- Department: {clean_dept(employee.get('department'))}
- Seniority: {employee.get('seniority_level')}
- Privileged User: {employee.get('is_privileged_user')}
- Current Behavior Trust Score: {employee.get('current_score')}/100

SECURITY ALERT METADATA:
- Alert Type: {alert.get('type')}
- Severity: {alert.get('severity')}
- Initial Trigger Description: {alert.get('description')}

CHRONOLOGICAL EVENT LOGS:
{timeline_summary}

Please write a comprehensive incident report in markdown. Your report must contain the following four specific sections:
1. ### Incident Narrative
Provide a cohesive, professional narrative explaining exactly what happened in a chronological story. Explain how the threat pattern unfolded based on the event logs.
2. ### Suspicious Indicators
In bullet points, highlight the exact activities that are suspicious, including the off-hours times, file sensitivity levels, external domains, or data volumes involved.
3. ### Business Impact
Explain the business risk, data leakage concerns, regulatory impacts, or financial threats of this compromise.
4. ### Mitigation Playbook
Detail 3 to 4 immediate, actionable mitigation steps for the security operations center (SOC) (e.g. revoking auth, blocking domains, auditing devices).

Keep the explanation grounded strictly in the provided event logs. Do not fabricate file names, email domains, or locations not present in the logs.
"""
        explanation = gemini_service.generate_content(prompt)
        
        # Save to cache
        db.alerts.update_one({"alert_id": alert_id}, {"$set": {"ai_explanation": explanation}})
        return explanation
        
    except Exception as e:
        exc_type, exc_val, exc_tb = sys.exc_info()
        tb_str = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
        file_name = exc_tb.tb_frame.f_code.co_filename if exc_tb else "ai_assistant.py"
        line_no = exc_tb.tb_lineno if exc_tb else 0
        print(f"Warning: Gemini API call failed at {file_name}:{line_no}, falling back to rule-based: {e}\nFull Traceback:\n{tb_str}")
        
        explanation = get_rule_based_fallback(employee, alert)
        db.alerts.update_one({"alert_id": alert_id}, {"$set": {"ai_explanation": explanation}})
        return explanation


def generate_employee_investigation_report(db, employee_id):
    """
    Generates an 8-section evidence-based AI Investigation Report using actual CERT Release 4.2 dataset events.
    """
    emp = db.employees.find_one({"employee_id": employee_id})
    if not emp:
        return "Error: Employee profile not found in database."

    events = list(db.events.find({"employee_id": employee_id}).sort("timestamp", 1))
    timeline = get_employee_timeline(db, employee_id)
    
    # Categorize CERT activity logs
    logons = [e for e in events if e.get("type") == "logon"]
    devices = [e for e in events if e.get("type") == "device"]
    files = [e for e in events if e.get("type") == "file"]
    emails = [e for e in events if e.get("type") == "email"]
    https = [e for e in events if e.get("type") == "http"]

    # Compute Evidence Metrics
    off_hours_logons = [e for e in logons if e.get("details", {}).get("is_after_hours")]
    usb_connects = [e for e in devices if e.get("details", {}).get("action") in ["Connect", "PlugIn"]]
    confidential_files = [f for f in files if f.get("details", {}).get("file_sensitivity") in ["Confidential", "Restricted", "High"]]
    ext_emails = [m for m in emails if m.get("details", {}).get("recipient_domain") not in ["dtaa.com", "company.com", "partnercorp.com"]]
    cloud_https = [h for h in https if h.get("details", {}).get("url_category") in ["Cloud Storage", "Webmail"]]

    # Read Psychometrics
    psych = emp.get("psychometrics", {})
    o_val, c_val, e_val, a_val, n_val = psych.get("O", 30), psych.get("C", 30), psych.get("E", 30), psych.get("A", 30), psych.get("N", 30)

    score = emp.get("current_score", 100.0)
    score_reasons = emp.get("score_reasons", [])

    # Determine Verdict
    if score < 50.0 or len(usb_connects) > 5 or len(confidential_files) > 5:
        verdict = "CRITICAL INSIDER THREAT DETECTED"
        verdict_badge = "🚨 CRITICAL RISK"
    elif score < 80.0 or len(off_hours_logons) > 3 or len(ext_emails) > 3:
        verdict = "SUSPICIOUS BEHAVIORAL DEVIATION"
        verdict_badge = "⚠️ MEDIUM RISK"
    else:
        verdict = "CLEAN — NO ANOMALOUS ACTIVITY DETECTED"
        verdict_badge = "✅ LOW RISK (CLEAN)"

    # Format Evidence Section Lists
    logon_ev_str = "\n".join([f"- Logged in at `{l.get('timestamp')}` on device `{l.get('details',{}).get('device_id','PC')}` (After-hours: {l.get('details',{}).get('is_after_hours', False)})" for l in (off_hours_logons[:5] or logons[:3])]) or "- Standard logon activity."
    device_ev_str = "\n".join([f"- Plugged in USB Device on `{d.get('timestamp')}` at `{d.get('details',{}).get('device_id','PC')}`" for d in (usb_connects[:5] or devices[:3])]) or "- No unauthorized USB device connections."
    file_ev_str = "\n".join([f"- Accessed `{f.get('details',{}).get('file_name','doc')}` ({f.get('details',{}).get('file_sensitivity','Normal')}) on `{f.get('timestamp')}`" for f in (confidential_files[:5] or files[:3])]) or "- Standard routine file activity."
    email_ev_str = "\n".join([f"- Sent email to domain `{m.get('details',{}).get('recipient_domain','internal')}` with attachment: {m.get('details',{}).get('has_attachment', False)}" for m in (ext_emails[:5] or emails[:3])]) or "- Standard email communications."
    http_ev_str = "\n".join([f"- Visited domain `{h.get('details',{}).get('domain','internal')}` (Category: {h.get('details',{}).get('url_category','General')})" for h in (cloud_https[:5] or https[:3])]) or "- Standard internal network browsing."

    # Format Timeline Section
    timeline_str = "\n".join([f"1. **[{t['timestamp']}]** ({t['type'].upper()} via {t.get('source_dataset','CERT 4.2')}): {t['description']}" for t in timeline[-8:]]) or "1. Standard routine operational activity."

    reasons_str = "\n".join([f"- {r}" for r in score_reasons]) if score_reasons else "- Clean baseline (100% score rating)"

    report = f"""# Insider Threat AI Investigation Report

### 1. Executive Summary
- **Employee Name**: {emp.get('full_name')} ({emp.get('employee_id')})
- **Role / Title**: {emp.get('role')}
- **Organization / Unit**: {clean_dept(emp.get('functional_unit'))} &middot; {clean_dept(emp.get('department'))}
- **Supervisor**: {emp.get('supervisor')}
- **Behavior Trust Score**: **{score}/100** ({verdict_badge})
- **Dataset Evaluated**: Carnegie Mellon University CERT Insider Threat Dataset (Release 4.2)

### 2. Suspicious Activities
- **Off-Hours / Weekend Auth**: Identified **{len(off_hours_logons)}** logins outside standard operating hours.
- **Removable Media Events**: Recorded **{len(usb_connects)}** USB device connection / data transfer logs.
- **Sensitive File Interactions**: Detected **{len(confidential_files)}** confidential or restricted document operations.
- **External Email Activity**: Flagged **{len(ext_emails)}** communications routed to external recipient domains.
- **Web Anomalies**: Identified **{len(cloud_https)}** visits to cloud storage / external webmail portals.

### 3. Supporting Evidence
#### Logon Logs (`logon.csv`):
{logon_ev_str}

#### Removable Device Logs (`device.csv`):
{device_ev_str}

#### File Access Logs (`file.csv`):
{file_ev_str}

#### Email Activity Logs (`email.csv`):
{email_ev_str}

#### HTTP Web Logs (`http.csv`):
{http_ev_str}

### 4. Timeline of Events
{timeline_str}

### 5. Behavioral Analysis (Psychometrics & Trait Baseline)
- **Openness (O)**: `{o_val}/50` &middot; **Conscientiousness (C)**: `{c_val}/50` &middot; **Extraversion (E)**: `{e_val}/50`
- **Agreeableness (A)**: `{a_val}/50` &middot; **Neuroticism (N)**: `{n_val}/50`
- **Psychometric Risk Indicator**: {("Elevated Neuroticism / Low Conscientiousness trait combination detected, associated with heightened policy deviation likelihood." if n_val > 35 or c_val < 20 else "Psychometric profile is within normal behavioral variance bounds.")}

### 6. Risk Factors & Score Deductions
{reasons_str}

### 7. Recommended Action
1. **Security Operations Center (SOC)**: Immediately review session logs on assigned workstations.
2. **Access Governance**: Enforce time-boxed Just-in-Time (JIT) PAM controls for sensitive database resources.
3. **Managerial Audit**: Notify supervisor **{emp.get('supervisor')}** to verify operational necessity for off-hours access.

### 8. Final Verdict
**{verdict}**
"""
    return report
