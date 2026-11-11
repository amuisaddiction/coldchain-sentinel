# ColdChain Sentinel — Official Production Free-Tier Deployment Guide (Zero Credit Card Required)

This guide provides the exact, validated deployment instructions for **ColdChain Sentinel** across **Render** (FastAPI Backend Free Web Service), **Supabase** (Managed PostgreSQL Database + Persistent Evidence Storage Free Tier), and **Vercel** (Next.js 15 Frontend Free Hobby Tier).

**Total Cost: $0.00 / month. No payment or credit card is required for any of these services.**

---

## Architecture Overview

```
┌─────────────────────────────────┐           HTTPS API           ┌─────────────────────────────────┐
│     Vercel (Hobby Free Tier)    │ ────────────────────────────> │     Render (Free Web Service)   │
│  - Next.js 15 App Router        │    NEXT_PUBLIC_API_BASE_URL   │  - FastAPI / Python 3.13        │
│  - Static + Edge Runtime        │                               │  - Uvicorn (Port 8000/10000)    │
│  - URL: coldchain-sentinel...   │                               │  - Zero ephemeral disk reliance │
└─────────────────────────────────┘                               └─────────────────────────────────┘
                                                                                  │
                                                      PostgreSQL 15/16 Connection │ REST Storage API
                                                      (Direct or Session Pooler)  │ (Private Object Bucket)
                                                                                  ▼
                                                                  ┌─────────────────────────────────┐
                                                                  │       Supabase (Free Tier)      │
                                                                  │  - Database: 500 MB PostgreSQL  │
                                                                  │  - Storage: 1 GB "evidence"     │
                                                                  │  - SHA-256 Verified Artifacts   │
                                                                  └─────────────────────────────────┘
```

---

## Prerequisites (Accounts & Services)

All services used in this setup have a generous free tier requiring **no credit card**:

1. **GitHub Account:** Access to repository `https://github.com/amuisaddiction/coldchain-sentinel`
2. **Supabase Account:** [https://supabase.com](https://supabase.com) (Free Tier: 500 MB DB, 1 GB Storage, No Card Required)
3. **Render Account:** [https://render.com](https://render.com) (Free Web Service, No Card Required)
4. **Vercel Account:** [https://vercel.com](https://vercel.com) (Hobby Free Tier, No Card Required)
5. **PayPal Developer Account (Optional):** [https://developer.paypal.com](https://developer.paypal.com) (Sandbox simulation enabled by default)

---

## SECTION 1: Database & Persistent Storage Setup (Supabase Free)

Supabase provides the managed PostgreSQL database and S3-compatible private object storage for audit evidence files.

### 1. Create a Supabase Project
1. Log in to [Supabase Dashboard](https://supabase.com/dashboard).
2. Click **New Project**.
3. Choose your organization.
4. Fill in:
   - **Name:** `coldchain-sentinel`
   - **Database Password:** Enter a strong password (save this securely).
   - **Region:** Choose a region close to your Render deployment (e.g., `Frankfurt (eu-central-1)` or `East US (North Virginia)`).
   - **Pricing Plan:** Select **Free ($0/month)**.
5. Click **Create new project** and wait 1–2 minutes for provisioning to finish.

### 2. Copy the PostgreSQL Connection String
1. In the Supabase project dashboard, click the **Settings** icon (gear icon at bottom-left) $\rightarrow$ **Database**.
2. Scroll to the **Connection parameters** / **Connection string** section.
3. Select the **URI** tab.
4. Copy the connection string. It will look like:
   - Direct: `postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres`
   - Or Pooler (Session mode): `postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres`
5. Replace `[YOUR-PASSWORD]` with your actual database password.
   *(Note: ColdChain Sentinel automatically translates `postgresql://` and `postgres://` to `postgresql+psycopg2://` at runtime. Both direct and pooler connection strings are supported).*

### 3. Create the Private Evidence Storage Bucket
1. In the Supabase left navigation bar, click **Storage** (folder icon).
2. Click **New Bucket**.
3. Configure the bucket:
   - **Name:** `evidence`
   - **Public bucket:** Keep toggle **OFF** (Private bucket for audit security).
4. Click **Create Bucket**.

### 4. Copy the Supabase API Credentials
1. In the Supabase left navigation bar, go to **Settings** $\rightarrow$ **API**.
2. Under **Project URL**, copy the URL (e.g., `https://[PROJECT-REF].supabase.co`). This is `SUPABASE_URL`.
3. Under **Project API keys**:
   - For backend server operations, copy the `service_role` secret key (or the `anon` `public` key). The `service_role` key grants the backend full access to read and write uploaded evidence files into the private `evidence` bucket. This is `SUPABASE_KEY`.

---

## SECTION 2: Backend API Deployment (Render Free Web Service)

Deploy the FastAPI backend on Render using the Free Web Service tier.

### Method A: One-Click Blueprint (Recommended)
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **Blueprints** on the top navigation bar, then click **New Blueprint Instance**.
3. Connect your GitHub repository: `amuisaddiction/coldchain-sentinel`.
4. Render detects `render.yaml` which defines the free-tier service:
   - **Service Name:** `coldchain-api`
   - **Plan:** `free`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Pre-Deploy Command:** `alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
5. Under Environment Variables to configure before deploying:
   - `DATABASE_URL`: Paste your Supabase PostgreSQL URI (with password filled in).
   - `SUPABASE_URL`: Paste your Supabase Project URL (`https://[PROJECT-REF].supabase.co`).
   - `SUPABASE_KEY`: Paste your Supabase `service_role` (or `anon`) key.
   - `SUPABASE_STORAGE_BUCKET`: `evidence`
   - `STORAGE_BACKEND`: `supabase`
   - `CORS_ORIGINS`: `https://coldchain-sentinel.vercel.app,http://localhost:3000`
6. Click **Apply**. Render will run migrations (`alembic upgrade head`) against Supabase and launch the service.

---

### Method B: Manual Dashboard Configuration
If creating the service manually:
1. In Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Connect `amuisaddiction/coldchain-sentinel`.
3. Fill in the service details:
   - **Name:** `coldchain-api`
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Region:** Match your Supabase region if possible.
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Pre-Deploy Command:** `alembic upgrade head`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 2`
   - **Instance Type:** `Free` ($0/mo)
   - **Health Check Path:** `/api/health`
4. Expand **Advanced** $\rightarrow$ **Add Environment Variable**:

| Variable Name | Exact / Recommended Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Production environment guard |
| `APP_DEBUG` | `false` | Disables interactive debug tools |
| `APP_SECRET_KEY` | *(Click "Generate" or provide 64-char hex)* | JWT signing and cryptographic key |
| `DATABASE_URL` | `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres` | Supabase Managed PostgreSQL URI |
| `STORAGE_BACKEND` | `supabase` | Uses persistent Supabase Storage |
| `SUPABASE_URL` | `https://[PROJECT-REF].supabase.co` | Supabase Project API URL |
| `SUPABASE_KEY` | `[YOUR-SUPABASE-SERVICE-ROLE-KEY]` | Supabase API authentication token |
| `SUPABASE_STORAGE_BUCKET` | `evidence` | Target private storage bucket |
| `CORS_ORIGINS` | `https://coldchain-sentinel.vercel.app,http://localhost:3000` | Allowed frontend origins (no trailing slashes) |
| `PAYPAL_MODE` | `SANDBOX` | Sandbox payment simulation mode |
| `PAYPAL_BASE_URL` | `https://api-m.sandbox.paypal.com` | Official PayPal Sandbox gateway |
| `PAYPAL_CLIENT_ID` | *(Optional sandbox client id)* | Sandbox client ID |
| `PAYPAL_CLIENT_SECRET` | *(Optional sandbox secret)* | Sandbox client secret |

5. Click **Create Web Service**.
6. Note your Render URL (e.g., `https://coldchain-api.onrender.com`).

> [!NOTE]
> Render Free web services spin down after 15 minutes of inactivity. When a new request arrives, it takes approximately 30–50 seconds to wake up (cold start). Once awake, responses are instantaneous.

---

## SECTION 3: Frontend Deployment (Vercel Free Hobby Tier)

Deploy the Next.js 15 frontend on Vercel at zero cost.

1. Log in to [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** $\rightarrow$ **Project**.
3. Select your repository: `amuisaddiction/coldchain-sentinel`.
4. In the project configuration:
   - **Project Name:** `coldchain-sentinel`
   - **Framework Preset:** `Next.js` (automatically detected)
   - **Root Directory:** Click **Edit**, select `frontend`, and click **Continue**.
5. Under **Environment Variables**, add:

| Name | Exact Value |
| :--- | :--- |
| `NEXT_PUBLIC_API_BASE_URL` | `https://<your-render-backend-name>.onrender.com/api` |

*(Note: `frontend/src/lib/api.ts` accepts either `NEXT_PUBLIC_API_BASE_URL` or `NEXT_PUBLIC_API_URL`).*

6. Click **Deploy**.
7. Once deployment finishes, Vercel gives you your production URL (e.g., `https://coldchain-sentinel.vercel.app`).

---

## SECTION 4: Post-Deployment Origin Sync (CORS)

1. Return to the Render Dashboard $\rightarrow$ `coldchain-api` $\rightarrow$ **Environment**.
2. Ensure `CORS_ORIGINS` contains your exact Vercel assigned domain:
   ```env
   CORS_ORIGINS=https://coldchain-sentinel.vercel.app
   ```
   *(Ensure no trailing slashes are present).*
3. Save changes. Render will automatically apply the environment change.

---

## SECTION 5: Live Verification Checklist

Run these commands from any terminal or verify directly in the browser:

### 1. Backend Health Check
```bash
curl -fsS https://<your-render-backend-name>.onrender.com/api/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "python_runtime": "3.13.x",
  "database_connected": true,
  "database_url_dialect": "postgresql+psycopg2",
  "storage_backend": "supabase",
  "paypal_mode": "SANDBOX"
}
```

### 2. Swagger OpenAPI Documentation
Open in browser: `https://<your-render-backend-name>.onrender.com/api/v1/openapi.json`  
Verify all 34 REST API endpoints are registered and valid.

### 3. Frontend Operations Console
Open in browser: `https://<your-vercel-domain>/`
- Verify the header displays **COLDCHAIN SENTINEL** and the system status shows `OPERATIONAL`.
- Click **Sentinel Challenge** tab.
- Click **Reset Environment**. Verify all 4 demo scenarios load:
  - Scenario 1: Clean Shipment (`VERIFIED & CAPTURED`)
  - Scenario 2: Thermal Excursion (`FAILED & CAPTURE_BLOCKED`)
  - Scenario 3: Evidence Tamper Anomaly (`TAMPER_DETECTED & BLOCKED`)
  - Scenario 4: Chain of Custody Gap (`CUSTODY_GAP & REVIEW_REQUIRED`)
- Test Scenario 1: Click **Approve & Settle via PayPal Sandbox** $\rightarrow$ verifies successful simulated capture.
- Test Scenario 2: Observe that payment capture is strictly blocked with compliance warning.

---

## SECTION 6: Free-Tier Costs & Quotas Summary

| Component | Provider & Tier | Cost | Quota / Limits | Credit Card Required? |
| :--- | :--- | :--- | :--- | :--- |
| **Backend API** | Render Free Web Service | **$0.00** / mo | 0.1 CPU, 512 MB RAM, spins down after 15m idle | **NO** |
| **PostgreSQL Database** | Supabase Free Tier | **$0.00** / mo | 500 MB database, unlimited reads/writes | **NO** |
| **Evidence Storage** | Supabase Storage Free Tier | **$0.00** / mo | 1 GB storage, 2 GB egress / mo | **NO** |
| **Frontend Console** | Vercel Hobby Free Tier | **$0.00** / mo | 100 GB bandwidth, unlimited deployments | **NO** |
| **Total Deployment** | | **$0.00** | Full production-ready stack | **ZERO CREDIT CARDS** |
