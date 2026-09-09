# FedSanitize — Production Cloud Deployment Guide

This guide provides step-by-step instructions for deploying the complete **FedSanitize Threat-Defense Platform** using 100% free-tier cloud PaaS services:

| Component | Technology | Recommended Host | Free Tier Link |
| :--- | :--- | :--- | :--- |
| **Backend API** | FastAPI + PyTorch + Uvicorn | **Render** / **Railway** | [render.com](https://render.com) |
| **Frontend UI** | React 19 + Vite + Tailwind | **Vercel** / **Netlify** | [vercel.com](https://vercel.com) |
| **SOC & Analytics** | Streamlit + Plotly | **Streamlit Community Cloud** | [streamlit.io/cloud](https://streamlit.io/cloud) |

```
                                  ┌────────────────────────┐
                                  │      Vercel / Netlify   │
                                  │   (React 19 Frontend)  │
                                  └───────────┬────────────┘
                                              │ REST / Bearer JWT
                                              ▼
┌────────────────────────┐        ┌────────────────────────┐
│ Streamlit Cloud        │        │     Render / Railway   │
│ (Forensics & Replay)   │        │   (FastAPI Gateway)    │
└────────────────────────┘        └────────────────────────┘
```

---

## 1. Deploy the Backend (Render Free Tier)

The backend provides the REST API gateway, Zero-Trust authentication, and federated simulation engine.

### Step 1: Push Repository to GitHub
Ensure all recent changes are pushed to your GitHub repository:
```bash
git push origin main
```

### Step 2: Create Web Service on Render
1. Go to [dashboard.render.com](https://dashboard.render.com) and click **New +** → **Web Service**.
2. Connect your GitHub account and select your **`FedSanitize`** repository.
3. Configure the service settings:
   - **Name**: `fedsanitize-backend` (or your choice)
   - **Region**: Closest to you (e.g., `Oregon (US West)` or `Frankfurt (EU)`)
   - **Branch**: `main`
   - **Root Directory**: *(Leave blank)*
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn backend_api.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Instance Type**: `Free`

### Step 3: Configure Environment Variables
Under the **Environment Variables** section on Render, add:
| Key | Value | Description |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.11.9` | Ensures clean C-extension builds |
| `CORS_ORIGINS` | `*` | Or specify your Vercel URL once deployed |

4. Click **Create Web Service**. Render will build and deploy the container.
5. Once deployed, copy your backend URL (e.g., `https://fedsanitize-backend.onrender.com`).
6. Test in your browser: `https://fedsanitize-backend.onrender.com/health` should return:
   ```json
   {"status":"online","service":"FedSanitize Threat-Defense API","version":"1.0.0"}
   ```

*(Alternative: You can also deploy directly using `render.yaml` Blueprint or via Docker using the included `Dockerfile`)*.

---

## 2. Deploy the Frontend (Vercel Free Tier)

The frontend is a modern React 19 single-page application styled with cyber neon Tailwind themes.

### Step 1: Import Project on Vercel
1. Go to [vercel.com/new](https://vercel.com/new) and log in with GitHub.
2. Select your **`FedSanitize`** repository and click **Import**.

### Step 2: Configure Project Settings
- **Framework Preset**: `Vite`
- **Root Directory**: Click *Edit* and select **`frontend`** (or leave as root; both `vercel.json` configurations are pre-configured).
- **Build Command**: `npm run build` *(auto-detected)*
- **Output Directory**: `dist` *(auto-detected)*

### Step 3: Add Environment Variables
Expand **Environment Variables** and add:
| Key | Value |
| :--- | :--- |
| `VITE_API_URL` | `https://fedsanitize-backend.onrender.com` *(your Render URL from Step 1)* |

> **Note**: Do not include a trailing slash in `VITE_API_URL`.

### Step 4: Deploy
Click **Deploy**. In under 1 minute, your app will be live with a global CDN URL (e.g., `https://fedsanitize.vercel.app`).

---

## 3. Deploy Streamlit SOC Dashboard (Streamlit Cloud)

The Streamlit dashboard houses deep forensic heatmaps, cosine distribution charts, and the standalone SOC monitoring suite.

### Step 1: Open Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
2. Click **New app**.

### Step 2: Deploy App
Fill in the deployment details:
- **Repository**: `gamerboyadarsh-dot/FedSanitize`
- **Branch**: `main`
- **Main file path**: `app.py` *(or `dashboard/security_soc.py` for standalone SOC)*
- **App URL**: Choose a custom subdomain (e.g., `fedsanitize-soc.streamlit.app`)

### Step 3: Deploy
Click **Deploy!**. Streamlit Cloud will read `requirements.txt` and `.streamlit/config.toml` automatically and launch the dashboard with the dark theme.

---

## 4. Environment Variables Reference

### Backend (`backend_api`)
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `PORT` | `8000` | Port assigned by hosting provider (Render/Railway sets this automatically) |
| `CORS_ORIGINS` | Auto-regex | Comma-separated list of allowed web origins |
| `JWT_SECRET` | System-generated | Secret key for signing Zero-Trust tokens |
| `DEVICE` | `cpu` | Hardware acceleration device (`cpu` or `cuda`) |

### Frontend (`frontend`)
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `VITE_API_URL` | `http://127.0.0.1:8000` | Target URL of the live FastAPI backend |

---

## 5. Verification & Testing Checklist

Once all three services are live:
1. **Backend Health Check**: Open `https://<YOUR-RENDER-URL>/` and `https://<YOUR-RENDER-URL>/health` in your browser.
2. **Interactive API Docs**: Open `https://<YOUR-RENDER-URL>/docs` (Swagger UI).
3. **Frontend UI**: Open `https://<YOUR-VERCEL-URL>/`. The boot sequence should initialize smoothly, and telemetry records should load.
4. **Zero-Trust Auth**: Click the **Zero-Trust Status** badge in the header. Log in with the pre-seeded credentials:
   - **Role**: Admin
   - **Username**: `admin`
   - **Password**: `admin123`
5. **Streamlit Console**: Open `https://<YOUR-STREAMLIT-URL>/` to explore forensic graphs and replay rounds.

---

## Troubleshooting Common Issues

### Render Cold Starts (Free Tier)
Render's free tier spins down after 15 minutes of inactivity. The first request after idle can take ~30-50 seconds to spin up. The frontend startup sequence gracefully handles initial latency and retries connection.

### Cross-Origin Request Blocked (CORS)
If the browser console displays a CORS error:
1. Go to your Render backend dashboard → **Environment**.
2. Set `CORS_ORIGINS` to `*` or include your exact Vercel frontend URL (e.g. `https://fedsanitize.vercel.app`).
3. Click **Save Changes** to redeploy.
