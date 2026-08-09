# GarudaAI Deployment Guide

This document outlines the step-by-step instructions to deploy GarudaAI to production using Vercel (frontend React client) and Render (backend Flask server).

---

## ⏸ Needs User Secrets to Go Live
To deploy the application live, you must gather and configure the following secret variables in the respective hosting consoles. Do not check these secrets into Git.

| Variable Name | Target Host | Description |
|---|---|---|
| `MONGODB_URI` | Render (Backend) | Connection string for MongoDB Atlas (e.g. `mongodb+srv://...`) |
| `GEMINI_API_KEY` | Render (Backend) | Google Gemini AI access token from Google AI Studio |
| `FIREBASE_PROJECT_ID` | Render (Backend) | Firebase project configuration ID |
| `FIREBASE_PRIVATE_KEY` | Render (Backend) | Firebase Admin private certificate key (JSON text string) |
| `FIREBASE_CLIENT_EMAIL`| Render (Backend) | Firebase admin account email |
| `VITE_API_BASE_URL` | Vercel (Frontend)| Public URL of the running backend API server |

---

## 1. Backend Deployment (Render)

We host the Flask API server on **Render** as a Web Service.

### Setup Instructions
1. Create a new **Web Service** on Render and link your Git repository.
2. Configure the following build settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `python backend/app.py`
3. Expand the **Environment Variables** panel and add:
   - `MONGODB_URI` = *(Your MongoDB Atlas URI)*
   - `GEMINI_API_KEY` = *(Your Google Gemini API Key)*
   - `DEV_MODE` = `false` (Enables strict Firebase Admin auth validations)
   - `FIREBASE_PROJECT_ID` = *(Your ID)*
   - `FIREBASE_PRIVATE_KEY` = *(Your Private Key)*
   - `FIREBASE_CLIENT_EMAIL` = *(Your Client Email)*
4. Click **Deploy Web Service**. Render will install dependencies and start the Flask service. Copy the public URL (e.g. `https://garudaai-backend.onrender.com`).

---

## 2. Frontend Deployment (Vercel)

We host the React static application on **Vercel**.

### Setup Instructions
1. Import your Git repository into Vercel.
2. Select the repository and configure the project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
3. Expand the **Environment Variables** section and add:
   - `VITE_API_BASE_URL` = *(The URL of your Render backend, e.g. `https://garudaai-backend.onrender.com`)*
4. Click **Deploy**. Vercel will build the frontend assets, set up SPA rewrites based on `frontend/vercel.json`, and serve the app at a public domain.
