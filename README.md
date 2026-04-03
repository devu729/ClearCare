# 🏥 ClearCare — Healthcare Decision Intelligence

> ClearCare reads insurance policy documents, traces denial codes to the exact policy rule that triggered them, and explains the decision — to clinicians in clinical language, and to patients in plain English.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-clearcarever0.netlify.app-0ea5e9)](https://clearcarever0.netlify.app)
[![Backend](https://img.shields.io/badge/Backend-Render-46E3B7)](https://clearcare-44nc.onrender.com/health)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)

---

## 🌐 Live Demo

**Frontend:** https://clearcarever0.netlify.app

**Backend health check:** https://clearcare-44nc.onrender.com/health

| Role | Org Code |
|---|---|
| Clinician | `DEMO2024` |
| Patient | — (no code needed) |

> Note: Deployed on free tiers for this demo. First request after inactivity may take 30 seconds to wake up.

---

## What It Does

**The problem:** 250 million insurance claims are denied every year in the US. Patients get a letter with a code like `CO-4` and no explanation. Doctors don't have time to interpret it. The appeal deadline is ticking.

**The solution:** Upload the insurance policy PDF once. Enter any denial code. ClearCare finds the exact policy rule, generates a clinician-facing explanation with clinical citations, a patient-facing explanation in plain English, and drafts a formal appeal letter — all in one request.

### Core Features

- **Policy Parser** — Upload insurance PDFs. Rules extracted, PHI-stripped, chunked, embedded with Gemini, stored in ChromaDB
- **Denial Tracer** — Enter any denial code. Vector similarity search finds matching rules. Gemini generates dual explanations
- **Hallucination Guard** — Every AI claim verified against source document before display. Confidence score shown
- **Dual Audience** — One API call generates clinician explanation (clinical language, rule citations) and patient explanation (plain English, next steps) simultaneously
- **Appeal Drafter** — Formal appeal letter generated, placeholders filled, sent via email, deadline tracked in calendar
- **Role Separation** — Clinicians see all tabs including source rules and clinical actions. Patients see only plain English
- **HIPAA-Aligned Security** — PHI stripping, JWT on every endpoint, row-level security, audit log, 15-minute session timeout
- **Observability** — Langfuse traces every AI call with inputs, outputs, latency, confidence score

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│         React 18 + Vite  (Netlify)                  │
│   Login │ Clinician Dashboard │ Patient Dashboard    │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS + JWT
┌──────────────────▼──────────────────────────────────┐
│                    BACKEND                           │
│              FastAPI (Render.com)                    │
│  CORS │ JWT Validation │ PHI Stripping │ Audit Log   │
├─────────────┬───────────────┬───────────────────────┤
│  Policy     │   Decision    │   Communication        │
│  Parser     │   Tracer      │   Agent                │
│  Agent      │   Agent       │                        │
│             │               │                        │
│  PDF→Chunks │  ChromaDB     │  Resend Email          │
│  PHI Strip  │  Search       │  ICS Calendar          │
│  Gemini     │  Gemini LLM   │                        │
│  Embeddings │  Dual Output  │                        │
│  ChromaDB   │  Hallucination│                        │
│  Store      │  Guard        │                        │
└──────┬──────┴───────┬───────┴───────────────────────┘
       │              │
┌──────▼──────┐ ┌─────▼──────────────────────────────┐
│  ChromaDB   │ │           Supabase                  │
│  Vector DB  │ │  Auth │ Audit Logs │ RLS            │
│  (local)    │ └────────────────────────────────────┘
└─────────────┘
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Frontend | React 18 + Vite | UI and routing |
| Backend | FastAPI Python 3.11 | API and agent orchestration |
| Auth + DB | Supabase | Authentication, audit logs, RLS |
| Vector DB | ChromaDB | Store and search policy embeddings |
| LLM | Gemini 2.5 Flash | Dual explanation generation |
| Embeddings | Gemini Embedding API | Convert text to vectors |
| Email | Resend API | Send appeal letters |
| Calendar | ICS file generation | Appeal deadline reminders |
| Observability | Langfuse | AI call tracing and monitoring |
| Frontend Deploy | Netlify | Static hosting |
| Backend Deploy | Render.com | Python API hosting |

---

## Project Structure

```
clearcare/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, keep-alive
│   ├── config.py                  # Settings from env vars (Pydantic)
│   ├── observability.py           # Langfuse tracing setup
│   ├── requirements.txt
│   ├── agents/
│   │   ├── policy_parser.py       # PDF → ChromaDB pipeline
│   │   ├── decision_tracer.py     # RAG + Gemini + hallucination guard
│   │   └── mcp_agent.py           # Resend email + ICS calendar
│   ├── auth/
│   │   ├── __init__.py
│   │   └── token_vault.py         # Auth0 Token Vault integration
│   ├── security/
│   │   ├── phi_stripper.py        # Remove PHI before LLM calls
│   │   ├── auth_guard.py          # JWT validation on every endpoint
│   │   └── audit_logger.py        # HIPAA action logging
│   ├── routers/
│   │   ├── policy_router.py       # /api/policy/upload, /api/policy/documents
│   │   ├── trace_router.py        # /api/trace/denial
│   │   ├── mcp_router.py          # /api/mcp/email, /api/mcp/calendar
│   │   ├── audit_router.py        # /api/audit/logs
│   │   └── eval_router.py         # /api/evals/run
│   └── evals/
│       └── eval_runner.py         # Automated eval suite
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx               # App entry point
        ├── App.jsx                # Router + AuthProvider
        ├── index.css              # Global styles
        ├── lib/
        │   ├── supabaseClient.js  # Supabase singleton
        │   ├── AuthContext.jsx    # Auth state + 15min timeout
        │   └── agentClient.js     # All backend API calls
        ├── components/
        │   ├── ProtectedRoute.jsx # Auth guard for routes
        │   ├── PolicyParser.jsx   # PDF upload + indexing UI
        │   ├── DenialTracer.jsx   # Denial code input + results
        │   ├── AppealDrafter.jsx  # Letter generation + send
        │   └── AuditLog.jsx       # HIPAA audit trail
        └── pages/
            ├── Login.jsx          # Login + signup + role selection
            ├── ClinicianDashboard.jsx
            └── PatientDashboard.jsx
```

---

## Local Setup — Step by Step

### Prerequisites

- Python 3.11
- Node.js 18+
- Git

### Step 1 — Clone the repo

```bash
git clone https://github.com/devu729/ClearCare.git
cd ClearCare
```

### Step 2 — Get your API keys

You need 4 services. All have free tiers.

#### Gemini API Key (required)
1. Go to https://aistudio.google.com
2. Click **Get API Key** → Create API key
3. Copy the key — starts with `AIza...`

#### Supabase (required)
1. Go to https://supabase.com → New project
2. Wait for it to spin up (~2 minutes)
3. Go to **Project Settings → API**
4. Copy **Project URL** and **service_role key**
5. Run this SQL in the Supabase SQL editor:

```sql
-- Audit logs table
CREATE TABLE audit_logs (
  id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     text,
  action      text NOT NULL,
  resource    text,
  ip_address  text,
  user_agent  text,
  created_at  timestamptz DEFAULT now()
);

-- Row Level Security
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own logs"
  ON audit_logs FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role can insert"
  ON audit_logs FOR INSERT
  WITH CHECK (true);
```

6. Go to **Authentication → Providers → Email**
7. Turn off **Confirm email** (so signups work immediately in dev)

#### Resend API Key (required for email)
1. Go to https://resend.com → Sign up free
2. **API Keys → Create API Key**
3. Copy the key — starts with `re_...`

#### Langfuse (optional but recommended)
1. Go to https://cloud.langfuse.com → Sign up free
2. Create a project → **Settings → API Keys → Create**
3. Copy the public key (`pk-lf-...`) and secret key (`sk-lf-...`)
4. App works without these — observability just won't show

### Step 3 — Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

Edit `backend/.env` and fill in your keys:

```env
GEMINI_API_KEY=AIza...your_key_here

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...your_service_role_key

RESEND_API_KEY=re_...your_key_here

CHROMA_PERSIST_PATH=./chroma_db
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# Optional — app works without these
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

Start the backend:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO: ClearCare started ✓ keep-alive pinger active
INFO: Uvicorn running on http://0.0.0.0:8000
```

Test it:
```
http://localhost:8000/health
→ {"status":"ok","version":"1.0.0"}

http://localhost:8000/docs
→ Swagger UI with all endpoints
```

### Step 4 — Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...your_anon_key_here
VITE_BACKEND_URL=http://localhost:8000
VITE_CLINICIAN_ORG_CODES=DEMO2024
```

> The anon key is different from the service role key. Get it from Supabase → Project Settings → API → `anon public` key.

Start the frontend:

```bash
npm run dev
```

Open http://localhost:3000

### Step 5 — Test the full flow

1. Go to http://localhost:3000
2. Click Sign Up → select **Clinician** → enter org code `DEMO2024`
3. Click **Policy Parser** → upload `demo_insurance_policy.pdf`
4. Wait for "Policy indexed successfully"
5. Click **Denial Tracer** → paste:
```
CO-4 - The service is inconsistent with the payer's payment policy.
MRI scan of the lumbar spine was denied.
```
6. Click Trace Denial → see dual explanation appear
7. Click **Appeal Drafter** → generate letter → fill details → send email

---

## Deployment

### Deploy Backend to Render

1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Python Version:** 3.11 (add `.python-version` file with content `3.11`)

4. Add environment variables (same as local `.env` but with production values):

```
GEMINI_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_KEY
RESEND_API_KEY
CHROMA_PERSIST_PATH=/tmp/chroma_db
ALLOWED_ORIGINS=https://your-netlify-app.netlify.app
ENVIRONMENT=production
RENDER_EXTERNAL_URL=https://your-service.onrender.com
LANGFUSE_PUBLIC_KEY      (optional)
LANGFUSE_SECRET_KEY      (optional)
LANGFUSE_HOST=https://cloud.langfuse.com
```

> Use `/tmp/chroma_db` for `CHROMA_PERSIST_PATH` on Render — it's the only writable directory.

5. Click **Create Web Service** → wait for deployment

6. Test: `https://your-service.onrender.com/health`

### Deploy Frontend to Netlify

1. Go to https://netlify.com → Add new site → Import from Git
2. Settings:
   - **Base directory:** `frontend`
   - **Build command:** `npm run build`
   - **Publish directory:** `frontend/dist`

3. Add environment variables:

```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...your_anon_key
VITE_BACKEND_URL=https://your-service.onrender.com
VITE_CLINICIAN_ORG_CODES=DEMO2024
```

4. Click **Deploy** → wait 2 minutes

5. Update `ALLOWED_ORIGINS` in Render to match your Netlify URL

---

## API Reference

All endpoints except `/health` require `Authorization: Bearer <supabase_jwt>` header.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check |
| POST | `/api/policy/upload` | Clinician | Upload and index PDF |
| GET | `/api/policy/documents` | Clinician | List indexed policies |
| POST | `/api/trace/denial` | Any | Trace denial code |
| POST | `/api/mcp/email` | Any | Send appeal email |
| POST | `/api/mcp/calendar` | Any | Create calendar reminder |
| GET | `/api/audit/logs` | Any | Get own audit logs |
| POST | `/api/evals/run` | Clinician | Run eval suite |

### Trace Denial Request

```json
POST /api/trace/denial
{
  "query": "CO-4 - The service is inconsistent with the payer's payment policy",
  "document_id": "optional_specific_doc_id",
  "generate_appeal": true,
  "patient_name": "John Smith",
  "recipient_type": "insurance"
}
```

### Trace Denial Response

```json
{
  "status": "success",
  "clinician_explanation": "The MRI scan was denied with CO-4...",
  "patient_explanation": "Your MRI was denied because...",
  "clinician_actions": ["Review prior auth records", "..."],
  "patient_actions": ["Contact your doctor", "..."],
  "source_rule": "Section 2.1.3 — Advanced Diagnostic Imaging",
  "page_num": "2",
  "appeal_deadline": "180 days from denial notice",
  "confidence": 0.82,
  "verified": true,
  "source_chunks": [...],
  "appeal_letter": "April 3, 2026\n\nInsurance Company..."
}
```

---

## Security Architecture

| Layer | Implementation |
|---|---|
| PHI Protection | Regex stripping of SSN, phone, email, DOB, names before any LLM call |
| Authentication | Supabase JWT validated on every request via `auth_guard.py` |
| Authorization | Role-based — clinicians require org code; upload endpoints require clinician role |
| Data Isolation | Supabase Row Level Security — users only see their own data |
| Session Security | 15-minute inactivity timeout, `sessionStorage` for tokens |
| Audit Trail | Every action logged to Supabase with timestamp, no PHI in logs |
| Transport | HTTPS enforced, HSTS headers, X-Frame-Options, X-Content-Type-Options |

---

## Known Limitations

- **Scanned PDFs not supported** — PyMuPDF extracts text only. OCR not implemented
- **ChromaDB resets on redeploy** — local storage means indexed policies are lost when Render redeploys. Production fix: Pinecone
- **PHI stripping is regex-based** — catches structured patterns well, misses contextual identifiers. Production fix: Microsoft Presidio
- **Single-tenant ChromaDB** — all users share one ChromaDB instance. Production fix: per-organization namespacing
- **Gemini JSON mode not used** — structured output would guarantee valid JSON. Currently uses regex parsing with fallback

---

## Hackathon — Auth0 Token Vault Integration

ClearCare integrates Auth0 Token Vault to send appeal letters from the user's own Gmail account. An appeal from `john.smith@gmail.com` carries more legal weight than a generic service address.

**How it works:**
1. User connects their Google account via Auth0 Universal Login
2. Auth0 stores the Google OAuth token in Token Vault
3. When sending an appeal letter, ClearCare exchanges the user's Auth0 access token for their Google token via the Token Vault grant
4. The appeal letter is sent via Gmail API using the user's real identity
5. ClearCare never stores Google credentials — Auth0 manages the entire token lifecycle

**Setup for Token Vault:**
```env
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://clearcare-api.com
AUTH0_CLIENT_ID=your_client_id
AUTH0_CLIENT_SECRET=your_client_secret
AUTH0_CUSTOM_API_CLIENT_ID=your_custom_api_client_id
AUTH0_CUSTOM_API_CLIENT_SECRET=your_custom_api_client_secret
```

See `backend/auth/token_vault.py` for implementation details.

---

## Production Roadmap

- [ ] Replace ChromaDB with Pinecone for persistent vector storage
- [ ] Replace regex PHI stripping with Microsoft Presidio
- [ ] Use Gemini structured output mode for guaranteed JSON
- [ ] Add per-user rate limiting with usage tracking table
- [ ] Add iterative RAG — if confidence is low, refine query and retry
- [ ] Business Associate Agreements with Supabase, Render, Google for real PHI

---

## Built By

**Devu Anil** — 3rd Year CS Student, India

---

## Disclaimer

ClearCare is a student project built for educational and hackathon purposes. It is not a substitute for professional medical, legal, or insurance advice. All AI-generated content should be verified by a licensed professional before acting on it. This project is not HIPAA-certified for production use with real patient data.