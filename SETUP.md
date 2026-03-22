# ClearCare — Complete Setup Guide
## $0 cost · No credit card · ~30 minutes

---

## STEP 1 — Install Python 3.11 (Required for Windows)

Your current Python 3.13 has a conflict with PyMuPDF on Windows.
Use Miniconda (which you already have) to create a 3.11 environment:

```powershell
# Create environment with Python 3.11
conda create -n clearcare python=3.11 -y

# Activate it
conda activate clearcare

# Verify
python --version   # Should say Python 3.11.x
```

---

## STEP 2 — Supabase Setup

Your project URL is already: https://kvxfldvpuguvndtcrxzh.supabase.co

### Get your keys
- Supabase Dashboard → **Project Settings** → **API**
- Copy `anon public` key → frontend `.env`
- Copy `service_role` key → backend `.env`

### Run the SQL
1. Supabase Dashboard → **SQL Editor** → New query
2. Open `docs/supabase_setup.sql` → paste all contents → click **Run**

### Configure Auth
- **Authentication** → **URL Configuration**
- Site URL: `http://localhost:3000`
- Add redirect: `http://localhost:3000/**`

---

## STEP 3 — Get Gemini API Key (Free, No Card)

1. Go to **https://aistudio.google.com**
2. Sign in with Google
3. Click **Get API key** → **Create API key**
4. Copy it — takes 2 minutes

---

## STEP 4 — Backend

```powershell
# Make sure clearcare conda env is active
conda activate clearcare

# Go to backend folder
cd clearcare\backend

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
```

Open `backend\.env` and fill in:
```
GEMINI_API_KEY=your_gemini_key_here
SUPABASE_URL=https://kvxfldvpuguvndtcrxzh.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key_here
CHROMA_PERSIST_PATH=./chroma_db
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

### Start the backend
```powershell
uvicorn main:app --reload --port 8000
```

### Verify
Open: http://localhost:8000/health
Should return: `{"status":"ok","version":"1.0.0",...}`

---

## STEP 5 — Frontend

Open a new terminal window:

```powershell
cd clearcare\frontend

# Install dependencies
npm install

# Create your .env file
copy .env.example .env
```

Open `frontend\.env` and fill in:
```
VITE_SUPABASE_URL=https://kvxfldvpuguvndtcrxzh.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_BACKEND_URL=http://localhost:8000
VITE_CLINICIAN_ORG_CODES=DEMO2024
```

### Start the frontend
```powershell
npm run dev
```

Open: **http://localhost:3000** → ClearCare login page appears ✅

---

## STEP 6 — Test Everything

### Clinician account
1. Sign Up → select **Clinician** → org code: `DEMO2024`
2. Confirm email → Sign In → Clinician Dashboard
3. Click **Policy Parser** → upload any insurance PDF
4. Click **Denial Tracer** → type `CO-4` → click Trace
5. See explanation with confidence score ✅

### Patient account
1. Sign Up → select **Patient** (no org code needed)
2. Confirm email → Sign In → Patient Portal
3. Click **Explain My Denial** → paste any denial text
4. Click **Write My Appeal** → get ready-to-send letter ✅

---

## STEP 7 — Deploy Free

### Frontend → Netlify
```powershell
npm run build
```
- Go to https://netlify.com → sign up free
- Drag `frontend\dist\` folder → site is live
- Add env variables in Netlify site settings

### Backend → Render.com
- Push backend folder to GitHub
- Go to https://render.com → New Web Service
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add all env variables
- Set `ENVIRONMENT=production`

---

## Total Cost: $0

| Service            | Cost |
|--------------------|------|
| Supabase (free)    | $0   |
| Netlify (free)     | $0   |
| Render.com (free)  | $0   |
| Gemini API (free)  | $0   |
| sentence-transformers (local) | $0 |
| ChromaDB (local)   | $0   |
| **Total**          | **$0** |

---

## File Structure

```
clearcare/
├── SETUP.md
├── docs/
│   └── supabase_setup.sql
├── frontend/
│   ├── src/
│   │   ├── lib/
│   │   │   ├── supabaseClient.js
│   │   │   ├── AuthContext.jsx
│   │   │   └── agentClient.js
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx
│   │   │   ├── PolicyParser.jsx
│   │   │   ├── DenialTracer.jsx
│   │   │   ├── AppealDrafter.jsx
│   │   │   └── AuditLog.jsx
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── ClinicianDashboard.jsx
│   │   │   └── PatientDashboard.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
└── backend/
    ├── agents/
    │   ├── policy_parser.py    ← sentence-transformers (local)
    │   ├── decision_tracer.py  ← Gemini (free)
    │   └── mcp_agent.py        ← Gmail + Calendar MCP
    ├── security/
    │   ├── phi_stripper.py
    │   ├── auth_guard.py
    │   └── audit_logger.py
    ├── routers/
    │   ├── policy_router.py
    │   ├── trace_router.py
    │   ├── mcp_router.py
    │   ├── audit_router.py
    │   └── eval_router.py
    ├── evals/
    │   └── eval_runner.py
    ├── config.py
    ├── main.py
    ├── requirements.txt
    └── .env.example
```
