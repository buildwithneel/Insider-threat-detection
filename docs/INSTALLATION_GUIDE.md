# 📥 Garuda AI: Comprehensive Installation & Setup Manual

> **Step-by-Step Local & Enterprise Setup Guide**  
> *Target Systems: Windows 10/11, Ubuntu Linux 22.04+, macOS Sequoia/Sonoma*  
> *Cross-Reference: [TECH_STACK.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/TECH_STACK.md) | [DEPLOYMENT_GUIDE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/DEPLOYMENT_GUIDE.md)*

---

## 📌 1. System Prerequisites

Ensure your host machine meets the following minimum requirements before proceeding:

* **Operating System**: Windows 10/11 (64-bit), Ubuntu 20.04+, or macOS 12+
* **Python Runtime**: Python `3.11.x` (Recommended) or `3.10+`
* **Node.js Runtime**: Node.js `v18.0.0+` or `v20.0.0+` (LTS) & npm `v9+`
* **Database**: MongoDB Community Server `v7.0+` *(Optional: Platform includes an automatic JSON Fallback Engine if MongoDB is not installed)*
* **Hardware Requirements**:
  * CPU: Dual-Core 2.0 GHz+
  * RAM: 4 GB minimum (8 GB recommended)
  * Disk: 2 GB available space

---

## 2. Step-by-Step Installation Workflow

---

### Step 1: Clone Repository
Open your terminal or command prompt and clone the repository:

```bash
git clone https://github.com/prathameshpandir-dev/GarudaAI-Insider-Threat-Platform.git
cd GarudaAI-Insider-Threat-Platform
```

---

### Step 2: Configure Environment Variables
Create a `.env` file at the root of the project by copying `.env.example`:

```bash
# On Windows PowerShell:
copy .env.example .env

# On Linux / macOS:
cp .env.example .env
```

Open `.env` in any text editor and populate the key configurations:

```env
# Database Settings
MONGODB_URI=mongodb://localhost:27017/garudaai
DEV_MODE=true

# Google Gemini Multi-Key Pool (Provide at least one active API Key)
GEMINI_API_KEY_1=AIzaSy...YourKey1...
GEMINI_API_KEY_2=AIzaSy...YourKey2...

# JWT Cryptographic Secret Key
JWT_SECRET_KEY=super-secret-garuda-key-2026-production
```

---

### Step 3: Backend Environment Setup (Python)

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   # On Windows:
   python -m venv venv
   venv\Scripts\activate

   # On Linux / macOS:
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

### Step 4: Data Ingestion & Seeding Pipeline (Optional)

Run the synthetic data generator to populate the database fallback with CERT R4.2 aligned security logs:

```bash
# Run from repository root directory:
python scripts/generate_synthetic_data.py
python scripts/import_data.py
```

---

### Step 5: Start Flask REST API Server

```bash
# Ensure virtual environment is active in backend directory:
python app.py
```
*(The Flask backend will launch at `http://localhost:5000`)*

---

### Step 6: Frontend Client Setup (React + Vite)

Open a **new terminal window**:

1. Navigate to the `frontend/` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start Vite development server:
   ```bash
   npm run dev
   ```
*(The React dashboard will launch at `http://localhost:5173`)*

---

## 3. Windows One-Click Quick Launch Shortcut

For rapid testing on Windows systems, double-click `start_platform.bat` at the repository root, or execute:

```cmd
start_platform.bat
```
*(This script automatically launches both Flask backend and Vite frontend in separate console windows).*

---

## 4. Troubleshooting Common Installation Issues

| Error Symptom | Root Cause | Resolution Strategy |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Python virtual environment not activated. | Run `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux) before starting `app.py`. |
| `ERR_CONNECTION_REFUSED` on port 5000 | Flask backend server crashed or is not running. | Check terminal for Flask errors; verify port 5000 is free using `netstat -ano \| findstr 5000`. |
| `MongoDB connection refused` | Local MongoDB service is offline. | **No action required**: Garuda AI automatically switches to thread-safe JSON Fallback Mode (`db_client.py`). |
| `HTTP 429 Rate Limit` from Gemini | Single API key hit rate limits. | Add additional Gemini keys in `.env` (`GEMINI_API_KEY_2`, etc.) to trigger multi-key failover rotation. |
