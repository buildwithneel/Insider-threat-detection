# 📚 Garuda AI: Academic References, Industry Standards & Citations

> **Complete Bibliography, Academic References & Industry Standards Repository**  
> *Cross-Reference: [HACKATHON_BIBLE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/HACKATHON_BIBLE.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 1. Benchmark Cybersecurity Datasets

1. **CERT Synthetic Insider Threat Test Dataset (r4.2)**
   * *Publisher*: Software Engineering Institute, Carnegie Mellon University (CMU/SEI).
   * *URL*: `https://kilthub.cmu.edu/articles/dataset/Insider_Threat_Test_Dataset/12841247`
   * *Usage in Garuda AI*: Provides benchmark synthetic user activity feature vectors (logon, file, email, USB) used for training and evaluating our Scikit-Learn Random Forest Classifier (`insider_threat_rf.joblib`).

---

## 2. Industry Security Frameworks & Standards

2. **NIST Special Publication 800-207: Zero Trust Architecture**
   * *Publisher*: National Institute of Standards and Technology (NIST), U.S. Department of Commerce (2020).
   * *Usage in Garuda AI*: Formulates our Zero Trust core principles ("Never Trust, Always Verify", Microsegmentation, Continuous Verification).

3. **NIST Cybersecurity Framework (CSF) 2.0**
   * *Publisher*: National Institute of Standards and Technology (NIST) (2024).
   * *Usage in Garuda AI*: Governs our functional security taxonomy across GOVERN, IDENTIFY, PROTECT, DETECT, RESPOND, and RECOVER.

4. **MITRE ATT&CK® Framework for Enterprise**
   * *Publisher*: The MITRE Corporation.
   * *Usage in Garuda AI*: Maps threat indicators (PowerShell obfuscation `T1059.001`, USB data exfiltration `T1052.001`, Privilege Escalation `T1068`).

5. **OWASP Top 10:2021 Security Risks**
   * *Publisher*: Open Web Application Security Project (OWASP).
   * *Usage in Garuda AI*: Provides security requirements for access control enforcement (`A01`), cryptographic data protection (`A02`), injection mitigation (`A03`), and rate limiting (`A07`).

---

## 3. Official Documentation & Technical Specifications

6. **Google Gemini API & SDK Documentation**
   * *URL*: `https://ai.google.dev/docs`
   * *Usage*: Multi-key prompt engineering, JSON mode output formatting, and Gemini 1.5 Flash API specifications.

7. **MongoDB 7.0 Manual & Aggregation Pipeline Specification**
   * *URL*: `https://www.mongodb.com/docs/manual/`
   * *Usage*: Schema design, compound indexing rules, and aggregation pipeline constructs (`$match`, `$group`, `$sort`).

8. **React 19 Official Documentation**
   * *URL*: `https://react.dev/`
   * *Usage*: Concurrent rendering hooks, component state management, Virtual DOM optimization.

9. **Python 3.11 & Flask API Framework Reference**
   * *URL*: `https://flask.palletsprojects.com/`
   * *Usage*: REST API blueprint routing, CORS middleware configuration, Flask-Limiter integration.

---

## 4. Academic Research Papers & Books

10. **Cappelli, D. M., Moore, A. P., & Trzeciak, R. F. (2012)**. *The CERT Guide to Insider Threats: How to Prevent, Detect, and Respond to Information Technology Crimes (Risk Management)*. Addison-Wesley Professional.
11. **Breiman, L. (2001)**. *Random Forests*. Machine Learning, 45(1), 5-32.
12. **Ponemon Institute (2023)**. *Cost of Insider Threats Global Report*. Sponsored by Proofpoint.
