# 🛠️ Garuda AI: Technical Stack & Deep Technology Specification

> **Comprehensive Technology Justification & Engineering Matrix**  
> *Cross-Reference: [ARCHITECTURE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/ARCHITECTURE.md) | [AI_MODELS.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/AI_MODELS.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 Executive Technology Summary

Garuda AI is built on a modern, decoupled, asynchronous micro-services ready architecture. The stack is carefully selected to deliver high throughput, sub-second latency for security threat scoring, continuous Zero Trust identity verification, and multi-key generative AI failover.

```
+-----------------------------------------------------------------------------------+
|                                 GARUDA AI TECH STACK                              |
+-----------------------------------------------------------------------------------+
|  FRONTEND LAYER    : React 19 | Vite | Tailwind CSS v3 | Chart.js                 |
|  BACKEND LAYER     : Python 3.11 | Flask | Flask-CORS | Flask-Limiter             |
|  AI / GATEWAY LAYER: Google Gemini 1.5 Flash | Multi-Key LRU Pool | Scikit-Learn  |
|  DATABASE LAYER    : MongoDB 7.0 | PyMongo | JSON Fallback Storage Engine        |
|  SECURITY / AUTH   : Firebase Admin SDK | PyJWT | Cryptography (AES-256 Fernet)    |
+-----------------------------------------------------------------------------------+
```

---

## 1. Primary Technology Deep-Dives

---

### 1.1 React 19 (Frontend UI Framework)

#### • What it is
React 19 is an open-source, component-based JavaScript library developed by Meta for building dynamic, high-performance web user interfaces.

#### • Why it is used in Garuda AI
Garuda AI requires a highly responsive, real-time Security Operations Center (SOC) dashboard. React's Virtual DOM allows instant updating of employee trust scores, live threat timelines, and modal dialogs without full page reloads.

#### • Why Selected
React 19 introduces automatic rendering optimizations, concurrent mode rendering, and cleaner component state lifecycles, ensuring zero UI lag even when rendering hundreds of security logs.

#### • How Garuda AI Uses It
The entire single-page application (`frontend/src/App.jsx`) is built using React components, including `JitPamDashboard.jsx`, `SandboxDashboard.jsx`, `HumanIdentityDashboard.jsx`, `AuditLogsView.jsx`, and `RbacUserManagementModal.jsx`.

#### • Internal Working
React creates an in-memory Virtual DOM tree. When security events alter an employee's trust score state, React calculates the diff between the previous and new Virtual DOM states using its Reconciliation Algorithm (Fiber) and updates only the altered DOM elements.

#### • Key Metrics & Trade-offs
* **Advantages**: Declarative UI, massive ecosystem, component reusability, Virtual DOM speed.
* **Disadvantages**: Large bundle size if unoptimized, fast-moving ecosystem require frequent updates.
* **Alternatives Evaluated**: Angular 17 (Rejected: Excessive boilerplate and rigid OOP structure), Vue 3 (Rejected: Smaller enterprise SOC community support).
* **Security Benefits**: Automatic XSS protection via string escaping in JSX.
* **Performance & Scalability**: Render updates take $< 16\text{ ms}$ (60 FPS rendering).
* **Cost**: $100\%$ Open Source (Free MIT License).
* **Learning Curve**: Low to Moderate.
* **Real-world Adoption**: Meta, Netflix, Airbnb, Uber, Bloomberg.
* **Best Practices**: Keep components modular, use custom hooks for state isolation.
* **When NOT to use**: Static, document-heavy websites with zero interactive user state.

---

### 1.2 Vite (Frontend Build Tool & Dev Server)

#### • What it is
Vite (French for "fast") is a next-generation frontend tooling build tool that utilizes native browser ES modules (ESM) to deliver lightning-fast development server startup and instant HMR (Hot Module Replacement).

#### • Why it is used in Garuda AI
Traditional bundlers like Webpack re-bundle the entire application on every code save. Vite leverages esbuild (written in Go) to pre-bundle dependencies 10–100x faster than Webpack.

#### • How Garuda AI Uses It
Used as the build pipeline and development server for the entire `frontend/` directory.

#### • Key Comparison
* **Vite vs Webpack**: Startup time is $300\text{ ms}$ (Vite) vs $12,000\text{ ms}$ (Webpack).
* **Security Benefits**: Strict environment variable scoping (`VITE_` prefix) prevents secret leakage.

---

### 1.3 Python 3.11 & Flask (Backend Framework)

#### • What it is
Python 3.11 is a high-level interpreted programming language renowned for AI/ML data science libraries. Flask is a lightweight WSGI web application micro-framework.

#### • Why it is used in Garuda AI
Python serves as the native language for Machine Learning (Scikit-Learn) and AI SDKs (Google Generative AI). Flask provides a lightweight, flexible REST API routing layer without forcing unnecessary database ORM overhead.

#### • How Garuda AI Uses It
Hosts all REST endpoints in `backend/app.py`, managing trust score calculations, multi-key Gemini routing, identity cadence processing, and database operations.

#### • Internal Working
Flask routes HTTP requests via `Werkzeug` to specific controller view functions. Middleware handles CORS via `Flask-CORS` and rate-limiting via `Flask-Limiter`.

#### • Advantages & Disadvantages
* **Advantages**: Minimalist, fast setup, native access to Python AI/ML libraries, blueprint routing modularity.
* **Disadvantages**: Single-threaded WSGI default (mitigated using Gunicorn/Uvicorn workers in production).
* **Alternatives Evaluated**: Node.js/Express (Rejected: Lacks native ML ecosystem for Random Forest joblib model execution), Spring Boot (Rejected: Slow iteration speed for hackathon development).

---

### 1.4 Google Gemini 1.5 Flash API & Multi-Key Gateway

#### • What it is
Google Gemini 1.5 Flash is a state-of-the-art multimodal AI model optimized for high-speed, low-latency text analysis, narrative generation, and structured JSON output.

#### • How Garuda AI Uses It
Powers the **AI Incident Assistant**, generating automatic incident investigation playbooks, plain-English security summaries, and handling natural language database queries.

#### • Multi-Key Failover Engine (`backend/ai_gateway.py`)
Garuda AI implements a custom multi-key resilience gateway. If one API key hits a rate limit (HTTP 429) or quota restriction, the gateway automatically rotates to alternative keys (`GEMINI_API_KEY_1`, `GEMINI_API_KEY_2`, etc.) using Round-Robin or Least Recently Used (LRU) algorithms.

```
+-----------------------------------------------------------------------------------+
|                           GEMINI MULTI-KEY FAILOVER GATEWAY                       |
+-----------------------------------------------------------------------------------+
|  [ API Request ] ---> [ Key Pool Manager ]                                         |
|                             |---> Key 1 (Healthy)      --> [ Gemini API Success ] |
|                             |---> Key 2 (Cooling Down)                           |
|                             |---> Key 3 (Rate Limited)                           |
+-----------------------------------------------------------------------------------+
```

---

### 1.5 MongoDB & JSON High-Availability Fallback Storage Engine

#### • What it is
MongoDB is a NoSQL document-oriented database that stores data in flexible, JSON-like BSON documents.

#### • Why it is used in Garuda AI
Security log events (logon times, network IP, file access, USB serial numbers) have dynamic, heterogeneous schemas. Document databases eliminate rigid SQL schema migrations.

#### • High-Availability Fallback Engine (`backend/db_client.py`)
If MongoDB is offline or unavailable during a local deployment or hackathon demo, Garuda AI automatically falls back to an in-memory, thread-safe JSON document store (`backend/mock_db/`), ensuring $100\%$ platform uptime.

---

## 2. Exhaustive Framework & Library Comparison Matrices

---

### 📊 Matrix 1: Frontend Framework Comparison

| Metric | React 19 (Selected) | Angular 17 | Vue 3 |
|---|---|---|---|
| **Architecture** | Component / Virtual DOM | Full Framework / Real DOM | Component / Reactive Virtual DOM |
| **Data Binding** | One-Way Reactive | Two-Way | Two-Way / Reactive |
| **State Management** | React Hooks (`useState`) | RxJS / Services | Pinia / Vuex |
| **Bundle Size** | Light (~42 KB) | Heavy (~150 KB) | Very Light (~33 KB) |
| **Learning Curve** | Gentle / Moderate | Steep | Gentle |
| **Garuda AI Verdict** | **Selected**: Best ecosystem for custom security dashboards. | **Rejected**: Over-engineered for real-time log rendering. | **Rejected**: Fewer enterprise SOC plugins. |

---

### 📊 Matrix 2: Database Technology Comparison

| Metric | MongoDB (Selected) | PostgreSQL | MySQL |
|---|---|---|---|
| **Data Model** | Dynamic BSON Document | Relational SQL + JSONB | Relational SQL |
| **Schema Flexibility**| High (Dynamic fields) | Moderate | Low (Strict ALTER TABLE) |
| **Write Throughput** | Very High ($>50k\text{ ops/sec}$) | Moderate | Moderate |
| **Aggregation Engine**| Native Pipeline (`$group`, `$match`)| SQL JOINs | SQL JOINs |
| **Garuda AI Verdict** | **Selected**: Perfect for unstructured cybersecurity logs. | **Rejected**: Schema changes slow down development. | **Rejected**: Lacks native JSON document indexing. |

---

### 📊 Matrix 3: Backend Runtime & Framework Comparison

| Metric | Python Flask (Selected) | Node.js Express | Java Spring Boot |
|---|---|---|---|
| **Language** | Python 3.11 | JavaScript (Node.js) | Java 21 |
| **AI/ML Integration** | Native (`joblib`, `scikit-learn`) | Indirect (requires HTTP IPC) | Indirect |
| **API Overhead** | Ultra Low | Low | Medium / Heavy |
| **Development Speed** | Extremely Fast | Fast | Moderate |
| **Garuda AI Verdict** | **Selected**: Seamless integration between REST APIs and ML models. | **Rejected**: Poor native Python ML bindings. | **Rejected**: High RAM consumption ($>512\text{ MB}$). |

---

### 📊 Matrix 4: Generative AI Provider Comparison

| Metric | Google Gemini 1.5 Flash (Selected)| OpenAI GPT-4o-mini | Anthropic Claude 3 Haiku |
|---|---|---|---|
| **Context Window** | 1,000,000 Tokens | 128,000 Tokens | 200,000 Tokens |
| **Response Latency** | Ultra Low ($<800\text{ ms}$) | Low ($<1200\text{ ms}$) | Low ($<1000\text{ ms}$) |
| **Free Tier Quota** | Generous (15 RPM free) | Strict Paid Only | Paid Only |
| **Garuda AI Verdict** | **Selected**: Massive context window for large security log feeds. | **Rejected**: High API cost structure. | **Rejected**: Limited multi-key SDK tooling. |

---

### 📊 Matrix 5: CSS Framework Comparison

| Metric | Tailwind CSS v3 (Selected) | Bootstrap 5 |
|---|---|---|
| **Design Utility** | Atomic Utility Classes | Pre-built Components |
| **Customization** | Infinite (Theme Config) | Requires SASS Overrides |
| **Dark Mode Support** | Native Class (`dark:bg-slate-900`)| Requires Custom CSS |
| **Garuda AI Verdict** | **Selected**: Essential for custom SOC dark mode styling. | **Rejected**: Clunky, generic visual appearance. |

---

### 📊 Matrix 6: Charting Engine Comparison

| Metric | Chart.js + react-chartjs-2 (Selected) | Recharts |
|---|---|---|
| **Render Engine** | HTML5 Canvas | SVG Elements |
| **Performance** | High (Handles 10k+ data points) | Degrades with high SVG node count |
| **Garuda AI Verdict** | **Selected**: Fast canvas rendering for historical trust score trend lines. | **Rejected**: Performance bottleneck on large timelines. |

---

### 📊 Matrix 7: Machine Learning Library Comparison

| Metric | Scikit-Learn (Selected) | TensorFlow / Keras | PyTorch |
|---|---|---|---|
| **Primary Focus** | Classical ML (Random Forest, Isolation Forest) | Deep Neural Networks | Deep Learning Research |
| **Model Footprint** | Lightweight (`.joblib` ~170 KB) | Heavy ($>100\text{ MB}$) | Heavy ($>200\text{ MB}$) |
| **Inference Latency**| $< 2\text{ ms}$ | $15-50\text{ ms}$ | $20-60\text{ ms}$ |
| **Garuda AI Verdict** | **Selected**: Optimal for tabular CERT R4.2 behavioral logs. | **Rejected**: Overkill for structured tabular logs. | **Rejected**: Excessive compute requirements. |

---

## 3. Technology Life-Cycle & Enterprise Roadmap

* **Phase 1 (Current - Hackathon v1.0)**: Single-instance Flask API, PyMongo with JSON fallback, Gemini Multi-Key Gateway, React 19 Frontend.
* **Phase 2 (Enterprise v2.0)**: Containerized Kubernetes (k8s) pods, Redis Caching Cluster for real-time sub-millisecond trust score lookups, Apache Kafka log streaming pipeline.
