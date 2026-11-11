# ColdChain Sentinel — Official Production Deployment Guide

This guide provides the exact, validated deployment instructions for **ColdChain Sentinel** across **Render** (FastAPI Backend + Managed PostgreSQL 16 + Persistent Evidence Disk) and **Vercel** (Next.js 15 Frontend).

---

## Architecture Overview

```
┌─────────────────────────────────┐           HTTPS API           ┌─────────────────────────────────┐
│        Vercel (Frontend)        │ ────────────────────────────> │       Render (Backend API)      │
│  - Next.js 15 App Router        │    NEXT_PUBLIC_API_BASE_URL   │  - FastAPI / Python 3.13        │
│  - URL: coldchain-sentinel...   │                               │  - Uvicorn (Port 8000/10000)    │
└─────────────────────────────────┘                               └─────────────────────────────────┘
                                                                                  │
                                                                   PostgreSQL 16  │ /var/data/storage
                                                                   Connection     ▼ (Persistent Disk)
                                                                  ┌─────────────────────────────────┐
                                                                  │     Render Managed Database     │
                                                                  │  - Database: coldchain_db       │
                                                                  │  - User: coldchain_user         │
                                                                  └─────────────────────────────────┘
```

---

## Prerequisites (Accounts & Services)

1. **GitHub Account:** Access to `https://github.com/amuisaddiction/coldchain-sentinel`
2. **Render Account:** [https://render.com](https://render.com) (Free or Starter)
3. **Vercel Account:** [https://vercel.com](https://vercel.com) (Hobby Free tier)
4. **PayPal Developer Account (Optional):** [https://developer.paypal.com](https://developer.paypal.com) (Sandbox credentials)

---

## SECTION 1: Backend & Database Deployment (Render)

There are two methods to deploy the backend on Render. **Method A (Blueprint)** is recommended as it automates database creation, disk mounting, and environment wiring in one click.

### Method A: One-Click Blueprint (Recommended)

1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **Blueprints** on the top navigation bar, then click **New Blueprint Instance**.
3. Connect your GitHub repository: `amuisaddiction/coldchain-sentinel`.
4. Render will detect `render.yaml` and display the resources to create:
   - **Service:** `coldchain-api` (Web Service, Python, rootDir: `backend`)
   - **Database:** `coldchain-db` (PostgreSQL 16)
   - **Disk:** `coldchain-evidence-disk` (`/var/data/storage`, 1 GB)
5. Review the plan settings and click **Apply**.
6. Render will automatically:
   - Provision PostgreSQL 16.
   - Run `alembic upgrade head` during the pre-deploy phase.
   - Start the FastAPI service with Uvicorn.
7. Once deployed, note your service URL (e.g., `https://coldchain-api.onrender.com`).

---

### Method B: Manual Dashboard Configuration

If provisioning services individually without Blueprint:

#### 1. Create Managed PostgreSQL 16
1. In Render Dashboard, click **New +** $\rightarrow$ **PostgreSQL**.
2. **Name:** `coldchain-db`
3. **Database:** `coldchain_db`
4. **User:** `coldchain_user`
5. **Region:** Choose your preferred region (e.g., `Frankfurt` or `Oregon`).
6. **PostgreSQL Version:** `16`
7. Click **Create Database**.
8. Copy the **Internal Database URL** (for services inside Render).

#### 2. Create Web Service
1. Click **New +** $\rightarrow$ **Web Service**.
2. Connect `amuisaddiction/coldchain-sentinel`.
3. Fill in the exact fields:
   - **Name:** `coldchain-api`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Pre-Deploy Command:** `alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Health Check Path:** `/api/health`
4. Under **Disks**, click **Add Disk**:
   - **Name:** `coldchain-evidence-disk`
   - **Mount Path:** `/var/data/storage`
   - **Size:** `1 GB`
5. Under **Environment Variables**, add:

| Key | Exact Value |
| :--- | :--- |
| `APP_ENV` | `production` |
| `APP_DEBUG` | `false` |
| `APP_SECRET_KEY` | *(Click "Generate" or provide 64-char hex string)* |
| `DATABASE_URL` | *(Paste Internal Database URL from Step 1)* |
| `STORAGE_BACKEND` | `local` |
| `STORAGE_LOCAL_PATH` | `/var/data/storage` |
| `CORS_ORIGINS` | `https://coldchain-sentinel.vercel.app,http://localhost:3000` |
| `PAYPAL_MODE` | `SANDBOX` |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` |
| `PAYPAL_CLIENT_ID` | *(Optional sandbox client id)* |
| `PAYPAL_CLIENT_SECRET` | *(Optional sandbox secret)* |

6. Click **Create Web Service**.

---

## SECTION 2: Frontend Deployment (Vercel)

1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select your repository: `amuisaddiction/coldchain-sentinel`.
4. In the configuration screen:
   - **Project Name:** `coldchain-sentinel`
   - **Framework Preset:** `Next.js` (automatically detected)
   - **Root Directory:** Click **Edit**, select `frontend`, and click **Continue**.
5. Under **Environment Variables**, expand the panel and add:

| Name | Exact Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://<your-render-backend-name>.onrender.com/api` |

*(Note: `frontend/src/lib/api.ts` supports both `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_API_URL`)*.

6. Click **Deploy**.
7. Once deployment completes, Vercel provides your live domain (e.g., `https://coldchain-sentinel.vercel.app`).

---

## SECTION 3: Post-Deployment Origin Sync (CORS)

1. Return to the Render Dashboard $\rightarrow$ `coldchain-api` $\rightarrow$ **Environment**.
2. Update `CORS_ORIGINS` with your exact Vercel assigned domain:
   ```env
   CORS_ORIGINS=https://coldchain-sentinel.vercel.app
   ```
   *(Ensure no trailing slashes are present).*
3. Save changes. Render will automatically redeploy the service with updated CORS policies.

---

## SECTION 4: Live Verification Checklist

Run these commands from any terminal or verify directly in the browser:

### 1. Backend Health Check
```bash
curl -fsS https://<your-backend-url>/api/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "python_runtime": "3.13.x",
  "database_connected": true,
  "database_url_dialect": "postgresql",
  "storage_backend": "local",
  "paypal_mode": "SANDBOX"
}
```

### 2. Swagger OpenAPI Documentation
Open in your browser: `https://<your-backend-url>/docs`  
Verify all 34 REST API endpoints are active.

### 3. Frontend Operations Console
Open in your browser: `https://<your-vercel-domain>/`  
- Verify the header displays **COLDCHAIN SENTINEL** and the system status shows `OPERATIONAL`.
- Click **Sentinel Challenge** tab.
- Click **Reset Environment**. Verify all 4 demo scenarios load:
  - Scenario 1: Clean Shipment (`VERIFIED & CAPTURED`)
  - Scenario 2: Thermal Excursion (`FAILED & CAPTURE_BLOCKED`)
  - Scenario 3: Evidence Tamper Anomaly (`TAMPER_DETECTED & BLOCKED`)
  - Scenario 4: Chain of Custody Gap (`CUSTODY_GAP & REVIEW_REQUIRED`)
- Test Scenario 1: Click **Approve & Settle via PayPal Sandbox** $\rightarrow$ verifies successful simulated capture.
- Test Scenario 2: Observe that payment capture is strictly blocked with compliance warning.
