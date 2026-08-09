#!/usr/bin/env python3
import os
import csv
import json
import numpy as np
import matplotlib
matplotlib.use('Agg') # Safe headless execution for plotting
import matplotlib.pyplot as plt
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, cohen_kappa_score, matthews_corrcoef, log_loss,
    balanced_accuracy_score, confusion_matrix, roc_curve, classification_report
)

# Set path configuration
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))
try:
    from db_client import get_db
except ImportError:
    from backend.db_client import get_db

def clean_dept(dept_str):
    if not dept_str:
        return ""
    if " - " in str(dept_str):
        return str(dept_str).split(" - ", 1)[1].strip()
    return str(dept_str).strip()

def extract_features(db):
    """
    Extracts behavioral features and psychometrics for the 150 ground truth employees.
    """
    print("[+] Extracting features from database...")
    
    # Load first 150 employees by CSV ordering
    employees = []
    with open('dataset/employees.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        employees = list(reader)[:150]
        
    emp_ids = [e['employee_id'] for e in employees]
    
    # Load ground truth labels
    targets = {}
    with open('dataset/ground_truth_labels.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            targets[row['employee_id']] = 1 if row['is_insider_threat'] == 'True' else 0

    X = []
    y = []
    
    for emp_id in emp_ids:
        emp = db.employees.find_one({'employee_id': emp_id}) or {}
        psych = emp.get('psychometrics', {'O': 30, 'C': 30, 'E': 30, 'A': 30, 'N': 30})
        
        # Load all events chronologically
        events = list(db.events.find({'employee_id': emp_id}))
        
        # Aggregate behavioral statistics
        features = [
            sum(1 for e in events if e['type'] == 'logon'), # Total Logons
            sum(1 for e in events if e['type'] == 'logon' and e.get('details', {}).get('is_after_hours')), # Off-hours Logons
            sum(1 for e in events if e['type'] == 'logon' and not e.get('details', {}).get('is_known_device', True)), # Unknown Device Logons
            sum(1 for e in events if e['type'] == 'device'), # Total USB/Device actions
            sum(1 for e in events if e['type'] == 'device' and e.get('details', {}).get('data_transferred_mb', 0.0) > 0.0), # USB Data Transfer Events
            sum(1 for e in events if e['type'] == 'file'), # Total File accesses
            sum(1 for e in events if e['type'] == 'file' and e.get('details', {}).get('file_sensitivity') in ['Confidential', 'Restricted']), # Restricted File accesses
            sum(1 for e in events if e['type'] == 'email'), # Total Emails
            sum(1 for e in events if e['type'] == 'email' and e.get('details', {}).get('recipient_domain', '') not in ['dtaa.com', 'company.com']), # External Emails
            sum(1 for e in events if e['type'] == 'http'), # Total HTTP browse actions
            sum(1 for e in events if e['type'] == 'http' and e.get('details', {}).get('url_category') in ['Cloud Storage', 'Webmail']), # Cloud exfil navigations
            sum(1 for e in events if e['type'] == 'privilege'), # Privilege changes
            float(psych.get('O', 30)), # Openness
            float(psych.get('C', 30)), # Conscientiousness
            float(psych.get('E', 30)), # Extraversion
            float(psych.get('A', 30)), # Agreeableness
            float(psych.get('N', 30))  # Neuroticism
        ]
        
        X.append(features)
        # Match index back to ground truth EMP IDs
        emp_idx = emp_ids.index(emp_id) + 1
        emp_key = f"EMP{emp_idx:03d}"
        y.append(targets.get(emp_key, 0))
        
    return np.array(X), np.array(y)

def evaluate_model():
    db = get_db()
    X, y = extract_features(db)
    
    # 5-Fold Cross Validation
    print("\n[+] Performing 5-Fold Cross Validation...")
    cv_clf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    cv_scores = cross_val_score(cv_clf, X, y, cv=5)
    
    # Train/Test Split (70% train, 30% test, stratified due to class imbalance)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    model_path = "insider_threat_rf.joblib"
    if os.path.exists(model_path):
        print(f"[+] Loading existing trained model: {model_path}")
        rf = joblib.load(model_path)
    else:
        print("[+] Training new Random Forest Classifier...")
        rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
        rf.fit(X_train, y_train)
        joblib.dump(rf, model_path)
        print(f"[OK] Model saved to {model_path}")
        
    # Generate Predictions and Probabilities
    y_prob = rf.predict_proba(X_test)[:, 1]
    
    # Threshold tuning: due to class imbalance (144 negative vs 6 positive), standard 0.5 threshold 
    # might predict all 0s. A threshold of 0.15 provides balanced risk classification.
    y_pred = (y_prob >= 0.15).astype(int)
    
    # 1. Standard Metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision_macro = precision_score(y_test, y_pred, average='macro', zero_division=0)
    precision_weighted = precision_score(y_test, y_pred, average='weighted', zero_division=0)
    recall_macro = recall_score(y_test, y_pred, average='macro')
    recall_weighted = recall_score(y_test, y_pred, average='weighted')
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')
    
    # ROC-AUC calculation
    try:
        roc_auc = roc_auc_score(y_test, y_prob)
    except ValueError:
        roc_auc = 0.5
        
    mcc = matthews_corrcoef(y_test, y_pred)
    kappa = cohen_kappa_score(y_test, y_pred)
    
    # Log Loss calculation
    try:
        logloss = log_loss(y_test, rf.predict_proba(X_test))
    except ValueError:
        logloss = 999.0
        
    # 2. Imbalanced Specific Metrics
    balanced_acc = balanced_accuracy_score(y_test, y_pred)
    per_class_precision = precision_score(y_test, y_pred, average=None, zero_division=0).tolist()
    per_class_recall = recall_score(y_test, y_pred, average=None).tolist()
    per_class_f1 = f1_score(y_test, y_pred, average=None).tolist()
    
    # 3. Print complete classification report
    report = classification_report(y_test, y_pred, zero_division=0)
    
    results = {
        "accuracy": accuracy,
        "precision_macro": precision_macro,
        "precision_weighted": precision_weighted,
        "recall_macro": recall_macro,
        "recall_weighted": recall_weighted,
        "f1_macro": f1_macro,
        "f1_weighted": f1_weighted,
        "roc_auc": roc_auc,
        "mcc": mcc,
        "cohen_kappa": kappa,
        "log_loss": logloss,
        "balanced_accuracy": balanced_acc,
        "per_class_precision": per_class_precision,
        "per_class_recall": per_class_recall,
        "per_class_f1_score": per_class_f1,
        "cross_validation": {
            "mean_accuracy": cv_scores.mean(),
            "std_accuracy": cv_scores.std(),
            "folds": cv_scores.tolist()
        }
    }
    
    # Save results to JSON
    with open("evaluation_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    print("[OK] Saved evaluation results to evaluation_results.json")
    
    # 4. Generate Confusion Matrix Plot
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(['Normal', 'Threat'])
    ax.set_yticklabels(['Normal', 'Threat'])
    ax.set_title('Insider Threat Confusion Matrix')
    ax.set_xlabel('Predicted Label')
    ax.set_ylabel('True Label')
    
    # Annotate counts inside matrix cells
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")
                    
    plt.tight_layout()
    plt.savefig('confusion_matrix.png', dpi=300)
    plt.close()
    print("[OK] Saved Confusion Matrix to confusion_matrix.png")
    
    # 5. Generate ROC Curve Plot
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(6, 4))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig('roc_curve.png', dpi=300)
    plt.close()
    print("[OK] Saved ROC Curve to roc_curve.png")
    
    # Output Terminal Summary with Descriptions
    print("\n" + "="*50)
    print("      INSIDER THREAT MODEL EVALUATION SUMMARY")
    print("="*50)
    
    # Standard metrics
    print(f"Accuracy:            {accuracy:.4f}  # Percentage of correct threat classifications.")
    print(f"Balanced Accuracy:   {balanced_acc:.4f}  # Average accuracy on normal vs threat classes (good for imbalance).")
    print(f"Precision (Macro):   {precision_macro:.4f}  # Precision averaged across classes without weighting.")
    print(f"Precision (Weighted):{precision_weighted:.4f}  # Precision weighted by class support.")
    print(f"Recall (Macro):      {recall_macro:.4f}  # Ability of the model to find all threat cases.")
    print(f"Recall (Weighted):   {recall_weighted:.4f}  # Recall weighted by class support.")
    print(f"F1-Score (Macro):    {f1_macro:.4f}  # Harmonic mean of precision and recall.")
    print(f"F1-Score (Weighted): {f1_weighted:.4f}  # F1-score weighted by class support.")
    print(f"ROC-AUC Score:       {roc_auc:.4f}  # Area under ROC Curve (ability to rank risks).")
    print(f"Matthews Corr (MCC): {mcc:.4f}  # Quality measure for binary classification (-1 to +1).")
    print(f"Cohen's Kappa Score: {kappa:.4f}  # Agreement between predicted and actual classes.")
    print(f"Log Loss:            {logloss:.4f}  # Information loss of prediction probabilities.")
    
    print("\n" + "-"*50)
    print("PER-CLASS CLASSIFICATION REPORT")
    print("-"*50)
    print(report)
    
    print("-"*50)
    print("5-FOLD CROSS VALIDATION RESULTS")
    print("-"*50)
    print(f"Mean Accuracy:       {cv_scores.mean():.4f}")
    print(f"Standard Deviation:  {cv_scores.std():.4f}")
    print("="*50)

if __name__ == "__main__":
    evaluate_model()
