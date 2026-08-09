import os
import csv
import random
import uuid
from datetime import datetime, timedelta

# Configuration
NUM_EMPLOYEES = 150
DAYS_OF_ACTIVITY = 90
START_DATE = datetime(2026, 4, 13, 0, 0, 0)
DATASET_DIR = "dataset"

# Departments and Roles
DEPARTMENTS = {
    "Engineering": ["Software Engineer", "Senior Software Engineer", "DevOps Engineer", "QA Engineer", "Engineering Manager"],
    "HR": ["HR Specialist", "HR Manager", "Recruiter"],
    "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
    "Sales": ["Sales Representative", "Account Executive", "Sales Manager"],
    "Executive": ["CEO", "CTO", "CFO", "VP of Engineering"]
}

LOCATIONS = ["New York", "San Francisco", "London", "Tokyo", "Bengaluru"]
SENSITIVITY_LEVELS = ["Public", "Internal", "Confidential", "Restricted"]
URL_CATEGORIES = ["Search", "Technology", "Social Media", "News", "Business", "Entertainment", "Job Search", "Cloud Storage", "Webmail"]
DOMAINS = {
    "Search": ["google.com", "bing.com"],
    "Technology": ["github.com", "stackoverflow.com", "aws.amazon.com"],
    "Social Media": ["linkedin.com", "twitter.com"],
    "News": ["cnn.com", "bbc.com"],
    "Business": ["salesforce.com", "slack.com"],
    "Entertainment": ["youtube.com"],
    "Job Search": ["indeed.com", "glassdoor.com"],
    "Cloud Storage": ["dropbox.com", "google-drive.com"],
    "Webmail": ["gmail.com", "outlook.com"]
}

# Create dataset directory
os.makedirs(DATASET_DIR, exist_ok=True)

# Generate Employees
employees = []
managers = []

# Generate Executive Managers first
exec_id_counter = 1
for dept in DEPARTMENTS:
    manager_id = f"EMP{exec_id_counter:03d}"
    exec_id_counter += 1
    employees.append({
        "employee_id": manager_id,
        "full_name": f"Manager {dept} {random.randint(10, 99)}",
        "department": dept,
        "role": f"{dept} Director" if dept != "Executive" else DEPARTMENTS[dept][-1],
        "seniority_level": "Senior" if dept != "Executive" else "Executive",
        "is_privileged_user": "True" if dept in ["Engineering", "Finance", "Executive"] else "False",
        "hire_date": (START_DATE - timedelta(days=random.randint(300, 1500))).strftime("%Y-%m-%d"),
        "manager_id": "EMP001" if dept != "Executive" else "",
        "office_location": random.choice(LOCATIONS)
    })
    managers.append(manager_id)

# Generate other employees
for i in range(len(employees) + 1, NUM_EMPLOYEES + 1):
    emp_id = f"EMP{i:03d}"
    dept = random.choice(list(DEPARTMENTS.keys()))
    if dept == "Executive":
        dept = "Engineering"
    role = random.choice(DEPARTMENTS[dept])
    seniority = "Senior" if "Senior" in role or "Manager" in role else random.choice(["Junior", "Mid"])
    is_privileged = "True" if seniority in ["Senior", "Executive"] or dept == "Engineering" or "Manager" in role else "False"
    
    dept_manager = [e["employee_id"] for e in employees if e["department"] == dept and ("Director" in e["role"] or "Manager" in e["role"])]
    mgr_id = random.choice(dept_manager) if dept_manager else random.choice(managers)
    
    employees.append({
        "employee_id": emp_id,
        "full_name": f"Employee {i} {random.randint(100, 999)}",
        "department": dept,
        "role": role,
        "seniority_level": seniority,
        "is_privileged_user": is_privileged,
        "hire_date": (START_DATE - timedelta(days=random.randint(30, 800))).strftime("%Y-%m-%d"),
        "manager_id": mgr_id,
        "office_location": random.choice(LOCATIONS)
    })

# Define 6 Threat Scenarios
threats = {
    "EMP015": {
        "is_insider_threat": "True",
        "threat_pattern": "USB Theft",
        "notes": "Employee logged in after midnight, accessed highly confidential designs, and transferred large amounts of data to USB."
    },
    "EMP032": {
        "is_insider_threat": "True",
        "threat_pattern": "Mass File Download",
        "notes": "Employee downloaded a massive number of restricted files over a short period, far exceeding daily baseline."
    },
    "EMP055": {
        "is_insider_threat": "True",
        "threat_pattern": "Impossible Travel",
        "notes": "Employee logged in from London and San Francisco within 30 minutes. Exfiltrated database dump via email attachment to unknown recipient."
    },
    "EMP078": {
        "is_insider_threat": "True",
        "threat_pattern": "Privilege Escalation",
        "notes": "Employee escalated their account privileges without valid IT approval, then immediately accessed sensitive financial data."
    },
    "EMP102": {
        "is_insider_threat": "True",
        "threat_pattern": "USB Theft",
        "notes": "Employee uploaded large backup files to mega.io during off-hours, and transferred logs to a USB device."
    },
    "EMP145": {
        "is_insider_threat": "True",
        "threat_pattern": "Midnight Login",
        "notes": "Employee spending office hours on job search, downloaded core AI repo, and performed unauthorized midnight logins."
    }
}

ground_truth = []
for emp in employees:
    emp_id = emp["employee_id"]
    if emp_id in threats:
        ground_truth.append({
            "employee_id": emp_id,
            "is_insider_threat": "True",
            "threat_pattern": threats[emp_id]["threat_pattern"],
            "notes": threats[emp_id]["notes"]
        })
    else:
        ground_truth.append({
            "employee_id": emp_id,
            "is_insider_threat": "False",
            "threat_pattern": "None",
            "notes": "Normal behavior profile."
        })

logons = []
file_accesses = []
device_usages = []
http_activities = []
emails = []
priv_escalations = []

for day in range(DAYS_OF_ACTIVITY):
    current_date = START_DATE + timedelta(days=day)
    weekday = current_date.weekday()
    is_weekend = weekday >= 5
    
    # We will loop through employees and generate sparse logs
    for emp in employees:
        emp_id = emp["employee_id"]
        is_threat = emp_id in threats
        
        # Sparse activity check: normal users only log activity on ~25% of the 90 days to keep total rows low
        # But if it's a weekday, they have a 25% chance of generating events. On weekend, 1% chance.
        work_prob = 0.25 if not is_weekend else 0.01
        if not is_threat and random.random() > work_prob:
            continue
            
        # Threat users also have normal sparse days, but we want to ensure we don't drop their logs entirely
        # If it's a threat user, let's keep a slightly higher active probability (40%)
        if is_threat and random.random() > 0.40:
            continue

        login_hour = random.randint(8, 10) if not is_weekend else random.randint(10, 14)
        login_time = current_date.replace(hour=login_hour, minute=random.randint(0, 59), second=random.randint(0, 59))
        device = f"DEV-{emp_id[3:]}-101"
        location = emp["office_location"]
        
        # Logon event
        logons.append({
            "event_id": str(uuid.uuid4())[:18],
            "employee_id": emp_id,
            "timestamp": login_time.strftime("%Y-%m-%d %H:%M:%S"),
            "device_id": device,
            "login_type": "Interactive",
            "is_after_hours": "False",
            "location": location,
            "is_known_device": "True"
        })
        
        # File access (1-2 per active day)
        num_files = random.randint(1, 2)
        for f_idx in range(num_files):
            file_time = login_time + timedelta(minutes=random.randint(10, 480))
            sens = random.choices(SENSITIVITY_LEVELS, weights=[0.7, 0.2, 0.08, 0.02])[0]
            action = random.choice(["Read", "Write"])
            file_name = f"doc_{random.randint(100, 999)}.{random.choice(['docx', 'xlsx', 'pdf'])}"
            file_accesses.append({
                "event_id": str(uuid.uuid4())[:18],
                "employee_id": emp_id,
                "timestamp": file_time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_name": file_name,
                "file_sensitivity": sens,
                "action": action,
                "file_size_mb": round(random.uniform(0.1, 8.0), 2)
            })
            
        # Device Usage (very rare: 1% chance on active day)
        if random.random() < 0.01:
            dev_time = login_time + timedelta(minutes=random.randint(30, 400))
            device_usages.append({
                "event_id": str(uuid.uuid4())[:18],
                "employee_id": emp_id,
                "timestamp": dev_time.strftime("%Y-%m-%d %H:%M:%S"),
                "device_type": "USB Drive",
                "action": "Connect",
                "data_transferred_mb": round(random.uniform(1.0, 15.0), 2)
            })
            
        # HTTP browsing (2-4 per active day)
        num_http = random.randint(2, 4)
        for h_idx in range(num_http):
            http_time = login_time + timedelta(minutes=random.randint(5, 500))
            category = random.choices(
                list(DOMAINS.keys()), 
                weights=[0.3, 0.25, 0.15, 0.1, 0.1, 0.05, 0.02, 0.01, 0.02]
            )[0]
            domain = random.choice(DOMAINS[category])
            http_activities.append({
                "event_id": str(uuid.uuid4())[:18],
                "employee_id": emp_id,
                "timestamp": http_time.strftime("%Y-%m-%d %H:%M:%S"),
                "url_category": category,
                "domain": domain
            })
            
        # Email activity (0-1 per active day)
        if random.random() < 0.3:
            email_time = login_time + timedelta(minutes=random.randint(10, 450))
            rec_domain = random.choice(["company.com", "partnercorp.com"])
            has_att = "True" if random.random() < 0.1 else "False"
            att_size = round(random.uniform(0.5, 4.0), 2) if has_att == "True" else 0.0
            emails.append({
                "event_id": str(uuid.uuid4())[:18],
                "employee_id": emp_id,
                "timestamp": email_time.strftime("%Y-%m-%d %H:%M:%S"),
                "recipient_domain": rec_domain,
                "has_attachment": has_att,
                "attachment_size_mb": att_size
            })

# Inject Threat Scenario 1: USB Theft (EMP015)
# Happens on Day 45 (approx mid-period)
threat_day_1 = START_DATE + timedelta(days=45)
logons.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP015",
    "timestamp": threat_day_1.replace(hour=2, minute=14, second=10).strftime("%Y-%m-%d %H:%M:%S"),
    "device_id": "DEV-015-103",
    "login_type": "Remote",
    "is_after_hours": "True",
    "location": "New York",
    "is_known_device": "False"
})
for i in range(8):
    file_accesses.append({
        "event_id": str(uuid.uuid4())[:18],
        "employee_id": "EMP015",
        "timestamp": threat_day_1.replace(hour=2, minute=18 + i, second=random.randint(0, 50)).strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": f"confidential_patent_schematic_{i}.pdf",
        "file_sensitivity": "Restricted",
        "action": "Read",
        "file_size_mb": round(random.uniform(20.0, 80.0), 2)
    })
device_usages.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP015",
    "timestamp": threat_day_1.replace(hour=2, minute=32, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_type": "USB Drive",
    "action": "Connect",
    "data_transferred_mb": 4250.0
})
device_usages.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP015",
    "timestamp": threat_day_1.replace(hour=2, minute=48, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_type": "USB Drive",
    "action": "Disconnect",
    "data_transferred_mb": 0.0
})

# Inject Threat Scenario 2: Mass File Download (EMP032)
# Happens on Day 60
threat_day_2 = START_DATE + timedelta(days=60)
for i in range(40): # 40 restricted file reads in 1 hour
    file_accesses.append({
        "event_id": str(uuid.uuid4())[:18],
        "employee_id": "EMP032",
        "timestamp": threat_day_2.replace(hour=14, minute=random.randint(0, 59), second=random.randint(0, 59)).strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": f"financial_audit_q{random.randint(1,4)}_{i}.xlsx",
        "file_sensitivity": "Restricted",
        "action": "Read",
        "file_size_mb": round(random.uniform(5.0, 25.0), 2)
    })

# Inject Threat Scenario 3: Impossible Travel & Email Exfiltration (EMP055)
# Happens on Day 75
threat_day_3 = START_DATE + timedelta(days=75)
logons.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP055",
    "timestamp": threat_day_3.replace(hour=9, minute=0, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_id": "DEV-055-101",
    "login_type": "Interactive",
    "is_after_hours": "False",
    "location": "San Francisco",
    "is_known_device": "True"
})
logons.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP055",
    "timestamp": threat_day_3.replace(hour=9, minute=25, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_id": "DEV-055-999",
    "login_type": "Remote",
    "is_after_hours": "False",
    "location": "London",
    "is_known_device": "False"
})
file_accesses.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP055",
    "timestamp": threat_day_3.replace(hour=9, minute=30, second=12).strftime("%Y-%m-%d %H:%M:%S"),
    "file_name": "customer_database_dump_2026.sql",
    "file_sensitivity": "Restricted",
    "action": "Read",
    "file_size_mb": 950.0
})
emails.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP055",
    "timestamp": threat_day_3.replace(hour=9, minute=42, second=45).strftime("%Y-%m-%d %H:%M:%S"),
    "recipient_domain": "competitor-defense.com",
    "has_attachment": "True",
    "attachment_size_mb": 950.0
})

# Inject Threat Scenario 4: Privilege Escalation (EMP078)
# Happens on Day 30
threat_day_4 = START_DATE + timedelta(days=30)
priv_escalations.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP078",
    "timestamp": threat_day_4.replace(hour=11, minute=15, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "previous_access_level": "User",
    "new_access_level": "Administrator",
    "approved_by": "SYSTEM_AUTO",
    "justification_provided": "Urgent software update debugging"
})
file_accesses.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP078",
    "timestamp": threat_day_4.replace(hour=11, minute=18, second=22).strftime("%Y-%m-%d %H:%M:%S"),
    "file_name": "m_and_a_strategy_2026_confidential.pdf",
    "file_sensitivity": "Restricted",
    "action": "Read",
    "file_size_mb": 45.0
})

# Inject Threat Scenario 5: Cloud Data Exfiltration (EMP102)
# Happens on Day 50
threat_day_5 = START_DATE + timedelta(days=50)
logons.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP102",
    "timestamp": threat_day_5.replace(hour=23, minute=45, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_id": "DEV-102-101",
    "login_type": "Remote",
    "is_after_hours": "True",
    "location": "Tokyo",
    "is_known_device": "True"
})
for i in range(3):
    http_activities.append({
        "event_id": str(uuid.uuid4())[:18],
        "employee_id": "EMP102",
        "timestamp": threat_day_5.replace(hour=23, minute=50 + i, second=10).strftime("%Y-%m-%d %H:%M:%S"),
        "url_category": "Cloud Storage",
        "domain": "mega.io"
    })
device_usages.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP102",
    "timestamp": threat_day_5.replace(hour=23, minute=52, second=0).strftime("%Y-%m-%d %H:%M:%S"),
    "device_type": "USB Drive",
    "action": "Connect",
    "data_transferred_mb": 1500.0
})

# Inject Threat Scenario 6: Disgruntled Employee (EMP145)
# Day 80
threat_day_6 = START_DATE + timedelta(days=80)
for i in range(5):
    http_activities.append({
        "event_id": str(uuid.uuid4())[:18],
        "employee_id": "EMP145",
        "timestamp": threat_day_6.replace(hour=10, minute=i * 10).strftime("%Y-%m-%d %H:%M:%S"),
        "url_category": "Job Search",
        "domain": "indeed.com"
    })
file_accesses.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP145",
    "timestamp": threat_day_6.replace(hour=14, minute=30).strftime("%Y-%m-%d %H:%M:%S"),
    "file_name": "core_ai_trading_engine_source.zip",
    "file_sensitivity": "Restricted",
    "action": "Read",
    "file_size_mb": 350.0
})
emails.append({
    "event_id": str(uuid.uuid4())[:18],
    "employee_id": "EMP145",
    "timestamp": threat_day_6.replace(hour=14, minute=45).strftime("%Y-%m-%d %H:%M:%S"),
    "recipient_domain": "gmail.com",
    "has_attachment": "True",
    "attachment_size_mb": 350.0
})

# Write datasets to CSV files
def write_csv(filename, data, headers):
    filepath = os.path.join(DATASET_DIR, filename)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
    print(f"Generated {filepath} with {len(data)} rows.")

write_csv("employees.csv", employees, ["employee_id", "full_name", "department", "role", "seniority_level", "is_privileged_user", "hire_date", "manager_id", "office_location"])
write_csv("logon_activity.csv", logons, ["event_id", "employee_id", "timestamp", "device_id", "login_type", "is_after_hours", "location", "is_known_device"])
write_csv("file_access.csv", file_accesses, ["event_id", "employee_id", "timestamp", "file_name", "file_sensitivity", "action", "file_size_mb"])
write_csv("device_usage.csv", device_usages, ["event_id", "employee_id", "timestamp", "device_type", "action", "data_transferred_mb"])
write_csv("http_activity.csv", http_activities, ["event_id", "employee_id", "timestamp", "url_category", "domain"])
write_csv("email_activity.csv", emails, ["event_id", "employee_id", "timestamp", "recipient_domain", "has_attachment", "attachment_size_mb"])
write_csv("privilege_escalation.csv", priv_escalations, ["event_id", "employee_id", "timestamp", "previous_access_level", "new_access_level", "approved_by", "justification_provided"])
write_csv("ground_truth_labels.csv", ground_truth, ["employee_id", "is_insider_threat", "threat_pattern", "notes"])

print("All CSVs generated successfully.")
