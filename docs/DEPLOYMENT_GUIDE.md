# ☁️ Garuda AI: Cloud Deployment & Production Orchestration Guide

> **Enterprise Production Deployment Configurations & Manifests**  
> *Platforms Covered: Docker, Render, Vercel, Railway, AWS, Azure, Google Cloud, Kubernetes*  
> *Cross-Reference: [INSTALLATION_GUIDE.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/INSTALLATION_GUIDE.md) | [SECURITY.md](file:///c:/Users/PRathmesh/Desktop/FINSpark/docs/SECURITY.md)*

---

## 📌 1. Production Architecture Overview

In production, Garuda AI adopts a microservice separation pattern:

* **Frontend**: Static SPA hosted on Edge CDN networks (Vercel, AWS CloudFront, Cloudflare Pages).
* **Backend REST API**: Python Gunicorn WSGI container hosted on container runners (Render, Railway, AWS ECS, GCP Cloud Run).
* **Database**: Managed MongoDB Atlas cluster or multi-node MongoDB replica set.

---

## 2. Docker & Containerization Blueprint

---

### 2.1 Backend Dockerfile (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependencies and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy backend application code
COPY . .

EXPOSE 5000

ENV PORT=5000
ENV DEV_MODE=false

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "app:app"]
```

---

### 2.2 Docker Compose Suite (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "5000:5000"
    environment:
      - MONGODB_URI=mongodb://mongodb:27017/garudaai
      - DEV_MODE=false
      - GEMINI_API_KEY_1=${GEMINI_API_KEY_1}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - mongodb
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: always

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    restart: always

volumes:
  mongo_data:
```

---

## 3. Platform Cloud Deployment Recipes

---

### 🚀 3.1 Deploying Backend on Render

1. Create a new **Web Service** on [Render.com](https://render.com).
2. Connect your GitHub repository branch.
3. Set Environment to `Python 3`.
4. Set Build Command: `cd backend && pip install -r requirements.txt`.
5. Set Start Command: `cd backend && gunicorn app:app`.
6. Add Environment Variables (`MONGODB_URI`, `GEMINI_API_KEY_1`, `JWT_SECRET_KEY`).

---

### 🌐 3.2 Deploying Frontend on Vercel

1. Import repository to [Vercel](https://vercel.com).
2. Root Directory: Select `frontend`.
3. Framework Preset: `Vite`.
4. Add Build Command: `npm run build`.
5. Output Directory: `dist`.
6. Configure `frontend/vercel.json` for SPA URL Rewrites:

```json
{
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 4. Kubernetes (k8s) Production Deployment Manifests

For enterprise-scale, high-availability deployments:

### `k8s/backend-deployment.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: garudaai-backend
  labels:
    app: garudaai-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: garudaai-backend
  template:
    metadata:
      labels:
        app: garudaai-backend
    spec:
      containers:
      - name: backend
        image: garudaai/backend:v1.0.0
        ports:
        - containerPort: 5000
        envFrom:
        - secretRef:
            name: garudaai-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: garudaai-backend-service
spec:
  type: ClusterIP
  ports:
  - port: 5000
    targetPort: 5000
  selector:
    app: garudaai-backend
```
