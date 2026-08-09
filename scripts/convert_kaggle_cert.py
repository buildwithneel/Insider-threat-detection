#!/usr/bin/env python3
import os
import sys
import argparse
import csv
from datetime import datetime

"""
GarudaAI Kaggle CERT Dataset Converter & Importer
Converts raw Kaggle CMU CERT Insider Threat Dataset (Release 4.2 / 5.2 / 6.2) into GarudaAI CSV format.
"""

def parse_args():
    parser = argparse.ArgumentParser(description="Convert Kaggle CERT Insider Threat dataset to GarudaAI format")
    parser.add_argument("--source", type=str, default="dataset/kaggle_raw", help="Directory containing raw Kaggle CERT CSV files")
    parser.add_argument("--output", type=str, default="dataset", help="Output directory for converted GarudaAI CSV files")
    parser.add_argument("--import-db", action="store_true", default=True, help="Automatically run import_data.py after conversion")
    parser.add_argument("--max-rows", type=int, default=0, help="Optional max row cap per file (0 for all rows)")
    return parser.parse_args()

def convert_logon(source_dir, output_dir, max_rows=0):
    src_file = os.path.join(source_dir, "logon.csv")
    if not os.path.exists(src_file):
        print(f"[-] {src_file} not found. Skipping logon conversion.")
        return 0

    out_file = os.path.join(output_dir, "logon_activity.csv")
    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["event_id", "timestamp", "employee_id", "device_id", "login_type", "is_after_hours", "location", "is_known_device"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if max_rows and count >= max_rows:
                break
            
            evt_id = row.get("id", f"EVT-LOG-{count:06d}")
            date_str = row.get("date", "")
            user_id = row.get("user", "")
            pc_id = row.get("pc", "")
            activity = row.get("activity", "Logon")

            is_after = False
            try:
                dt = datetime.strptime(date_str, "%m/%d/%Y %H:%M:%S")
                if dt.hour < 7 or dt.hour > 19 or dt.weekday() in [5, 6]:
                    is_after = True
            except Exception:
                pass

            writer.writerow({
                "event_id": evt_id,
                "timestamp": date_str,
                "employee_id": user_id,
                "device_id": pc_id,
                "login_type": "Interactive" if activity == "Logon" else "Logoff",
                "is_after_hours": "True" if is_after else "False",
                "location": "HQ Corporate Network",
                "is_known_device": "True"
            })
            count += 1

    print(f"[OK] Converted {count} logon records.")
    return count

def convert_file(source_dir, output_dir, max_rows=0):
    src_file = os.path.join(source_dir, "file.csv")
    if not os.path.exists(src_file):
        print(f"[-] {src_file} not found. Skipping file access conversion.")
        return 0

    out_file = os.path.join(output_dir, "file_access.csv")
    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["event_id", "timestamp", "employee_id", "file_name", "file_sensitivity", "action", "file_size_mb"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if max_rows and count >= max_rows:
                break
            
            evt_id = row.get("id", f"EVT-FILE-{count:06d}")
            date_str = row.get("date", "")
            user_id = row.get("user", "")
            filename = row.get("filename", "document.doc")
            
            sensitivity = "High" if any(w in filename.lower() for w in ["secret", "payroll", "db", "confidential", "bank"]) else "Medium"

            writer.writerow({
                "event_id": evt_id,
                "timestamp": date_str,
                "employee_id": user_id,
                "file_name": filename,
                "file_sensitivity": sensitivity,
                "action": "Copy" if "usb" in filename.lower() else "Open",
                "file_size_mb": 12.5
            })
            count += 1

    print(f"[OK] Converted {count} file access records.")
    return count

def convert_device(source_dir, output_dir, max_rows=0):
    src_file = os.path.join(source_dir, "device.csv")
    if not os.path.exists(src_file):
        print(f"[-] {src_file} not found. Skipping device conversion.")
        return 0

    out_file = os.path.join(output_dir, "device_usage.csv")
    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["event_id", "timestamp", "employee_id", "device_type", "action", "data_transferred_mb"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if max_rows and count >= max_rows:
                break

            evt_id = row.get("id", f"EVT-DEV-{count:06d}")
            date_str = row.get("date", "")
            user_id = row.get("user", "")
            act = row.get("activity", "Connect")

            writer.writerow({
                "event_id": evt_id,
                "timestamp": date_str,
                "employee_id": user_id,
                "device_type": "USB Drive",
                "action": "PlugIn" if act == "Connect" else "Unplug",
                "data_transferred_mb": 150.0 if act == "Connect" else 0.0
            })
            count += 1

    print(f"[OK] Converted {count} device records.")
    return count

def convert_email(source_dir, output_dir, max_rows=0):
    src_file = os.path.join(source_dir, "email.csv")
    if not os.path.exists(src_file):
        print(f"[-] {src_file} not found. Skipping email conversion.")
        return 0

    out_file = os.path.join(output_dir, "email_activity.csv")
    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["event_id", "timestamp", "employee_id", "recipient_domain", "has_attachment", "attachment_size_mb"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if max_rows and count >= max_rows:
                break

            evt_id = row.get("id", f"EVT-MAIL-{count:06d}")
            date_str = row.get("date", "")
            user_id = row.get("user", "")
            to_addr = row.get("to", "external.com")
            
            domain = to_addr.split("@")[-1] if "@" in to_addr else "gmail.com"

            writer.writerow({
                "event_id": evt_id,
                "timestamp": date_str,
                "employee_id": user_id,
                "recipient_domain": domain,
                "has_attachment": "True" if int(row.get("size", 0)) > 50000 else "False",
                "attachment_size_mb": round(int(row.get("size", 0)) / 1000000.0, 2)
            })
            count += 1

    print(f"[OK] Converted {count} email records.")
    return count

def convert_http(source_dir, output_dir, max_rows=0):
    src_file = os.path.join(source_dir, "http.csv")
    if not os.path.exists(src_file):
        print(f"[-] {src_file} not found. Skipping HTTP conversion.")
        return 0

    out_file = os.path.join(output_dir, "http_activity.csv")
    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["event_id", "timestamp", "employee_id", "url_category", "domain"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            if max_rows and count >= max_rows:
                break

            evt_id = row.get("id", f"EVT-HTTP-{count:06d}")
            date_str = row.get("date", "")
            user_id = row.get("user", "")
            url = row.get("url", "http://google.com")

            domain = url.split("//")[-1].split("/")[0] if "//" in url else "example.com"
            category = "Cloud Storage" if any(w in domain for w in ["dropbox", "mega", "drive"]) else "General Web"

            writer.writerow({
                "event_id": evt_id,
                "timestamp": date_str,
                "employee_id": user_id,
                "url_category": category,
                "domain": domain
            })
            count += 1

    print(f"[OK] Converted {count} HTTP records.")
    return count

def convert_employees(source_dir, output_dir):
    src_file = None
    for candidate in ["users.csv", "LDAP/2009-12.csv", "employees.csv", "psychometric.csv"]:
        path = os.path.join(source_dir, candidate)
        if os.path.exists(path):
            src_file = path
            break

    out_file = os.path.join(output_dir, "employees.csv")
    if not src_file:
        print(f"[-] No raw user catalog found in {source_dir}. Preserving existing {out_file}.")
        return 0

    print(f"[+] Converting {src_file} -> {out_file}...")

    count = 0
    with open(src_file, mode="r", encoding="utf-8") as f_in, open(out_file, mode="w", encoding="utf-8", newline="") as f_out:
        reader = csv.DictReader(f_in)
        fieldnames = ["employee_id", "full_name", "department", "role", "seniority_level", "is_privileged_user", "hire_date", "manager_id", "office_location"]
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            user_id = row.get("user_name") or row.get("user") or row.get("user_id") or f"EMP{count+1:03d}"
            name = row.get("employee_name") or row.get("name") or f"User {user_id}"
            dept = row.get("department") or "Engineering"
            role = row.get("role") or "Software Engineer"
            is_priv = "True" if any(w in role.lower() for w in ["admin", "it", "sysadmin", "lead", "director"]) else "False"

            writer.writerow({
                "employee_id": user_id,
                "full_name": name,
                "department": dept,
                "role": role,
                "seniority_level": "Senior" if is_priv == "True" else "Mid",
                "is_privileged_user": is_priv,
                "hire_date": "2022-01-15",
                "manager_id": row.get("manager"),
                "office_location": "New York HQ"
            })
            count += 1

    print(f"[OK] Converted {count} employee catalog records.")
    return count

def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)

    print("=" * 60)
    print("GarudaAI Kaggle CERT Release 4.2 Dataset Ingestion Tool")
    print("=" * 60)

    convert_employees(args.source, args.output)
    convert_logon(args.source, args.output, args.max_rows)
    convert_file(args.source, args.output, args.max_rows)
    convert_device(args.source, args.output, args.max_rows)
    convert_email(args.source, args.output, args.max_rows)
    convert_http(args.source, args.output, args.max_rows)

    if args.import_db:
        print("\n[+] Triggering GarudaAI automatic database reset & re-indexing...")
        import_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "import_data.py"))
        os.system(f"python \"{import_script}\" --reset")

    print("\n[OK] Kaggle CERT Release 4.2 Dataset Ingestion Completed Successfully!")

if __name__ == "__main__":
    main()
