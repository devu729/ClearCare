# 🏥 ClearCare — Healthcare Decision Intelligence

> When an insurance claim is denied, nobody can explain why. ClearCare reads the policy, finds the exact rule, and explains it — to the clinician in clinical language, and to the patient in plain English. Then it drafts the appeal letter and sends it from the patient's own Gmail using **Auth0 Token Vault**.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-clearcarever0.netlify.app-0ea5e9?style=for-the-badge)](https://clearcarever0.netlify.app)
[![Backend](https://img.shields.io/badge/Backend-Online-46E3B7?style=for-the-badge)](https://clearcare-44nc.onrender.com/health)
[![Auth0](https://img.shields.io/badge/Auth0-Token%20Vault-EB5424?style=for-the-badge)](https://auth0.com)

---

## 📹 Demo Video

**[→ Watch 3-Minute Demo on YouTube](#)**

> Replace `#` with your YouTube link before submitting

---

## 🌐 Live Demo

**App:** https://clearcarever0.netlify.app

| Role | Org Code | What You Can Do |
|---|---|---|
| Clinician | `DEMO2024` | Upload PDF, trace denials, see clinical view, generate appeals |
| Patient | none | Enter denial code, see plain English explanation, write appeal |

> **Note:** Deployed on Render free tier. First request after 15 minutes of inactivity takes ~30 seconds to wake up. This is a demo limitation, not a production architecture choice.

> **Email note:** Resend free tier only sends to verified addresses. Use `devuanil0831@gmail.com` when testing the Send Email feature in the demo.

---

## The Problem

In the United States alone, insurance companies deny **250 million claims per year**. Behind each denial is a specific policy rule — buried in a 300-page document that nobody reads. When a patient gets a denial letter, they receive a code like `CO-4` and no explanation.

- **Patients** don't know what the code means, what their rights are, or how to appeal
- **Clinicians** spend time they don't have decoding policy documents
- **Appeals** that come from generic email addresses get ignored or deprioritized
- **Deadlines** for appeals are typically 30–180 days — easy to miss

ClearCare addresses all four problems in one system.

---

## The Solution

```
Clinician uploads insurance policy PDF
              ↓
         [Once per policy]
              ↓
Patient gets denial code CO-4 from insurance company
              ↓
Enters code in ClearCare
              ↓
Vector search finds matching rule in policy
              ↓
Gemini generates two explanations simultaneously:
  → Clinician view: clinical language, rule citations, recommended actions
  → Patient view:   plain English, empathetic tone, numbered next steps
              ↓
Confidence score + hallucination guard verifies every claim
              ↓
Appeal letter drafted, placeholders filled
              ↓
Auth0 Token Vault → letter sent FROM patient's own Gmail
              ↓
Appeal deadline added to patient's Google Calendar
```

---

## Why Auth0 Token Vault Changes Everything

This is the part that makes ClearCare real rather than just a demo.

An AI-generated appeal letter sent from `onboarding@resend.dev` gets filtered, ignored, or deprioritized. Insurance companies receive thousands of automated emails. **An appeal from `john.smith@gmail.com` is different — it has real identity, legal standing, and an auditable paper trail.**

Before Token Vault, building this would require:
- Building an OAuth 2.0 consent flow from scratch
- Storing and encrypting refresh tokens per user
- Handling token expiry and rotation
- Managing Google API credentials at scale
- Taking on the security liability of storing user credentials

**Token Vault replaced all of that with a single API call.**

When a patient connects their Google account once through Auth0 Universal Login, Auth0 stores the token in Token Vault. When ClearCare needs to send an appeal, it exchanges the user's Auth0 access token for their Google token via the Token Vault grant. The letter goes out from the patient's real Gmail. ClearCare never stores a single Google credential.

```python
# backend/auth/token_vault.py
# This is all it takes to send from the user's real Gmail
google_token = await exchange_token_for_google(user_access_token)
# → Auth0 handles OAuth, storage, refresh, revocation
# → ClearCare gets a usable token
# → Appeal letter sent from john.smith@gmail.com
```

In healthcare, the identity of the sender is not a UX detail — it determines whether an appeal gets reviewed or ignored.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────┐
│              FRONTEND (Netlify)                  │
│         React 18 + Vite                         │
│                                                  │
│  Login │ Clinician Dashboard │ Patient Portal    │
│                                                  │
│  PolicyParser  DenialTracer  AppealDrafter       │
│  AuditLog      ProtectedRoute                    │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS + Supabase JWT
┌──────────────────▼──────────────────────────────┐
│              BACKEND (Render)                    │
│         FastAPI · Python 3.11                   │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │           SECURITY LAYER                │    │
│  │  PHI Strip │ JWT Guard │ Audit Logger   │    │
│  └────────────────────────┬────────────────┘    │
│                           │                     │
│  ┌──────────┐  ┌──────────▼──────┐  ┌────────┐ │
│  │ Policy   │  │ Decision Tracer │  │  MCP   │ │
│  │ Parser   │  │                 │  │ Agent  │ │
│  │ Agent    │  │ ChromaDB Search │  │        │ │
│  │          │  │ Gemini LLM      │  │ Resend │ │
│  │ PDF→Text │  │ Dual Explain    │  │ Email  │ │
│  │ PHI Strip│  │ Hallucination   │  │        │ │
│  │ Chunk    │  │ Guard           │  │ ICS    │ │
│  │ Embed    │  │ Confidence Score│  │ Cal    │ │
│  │ ChromaDB │  │ Retry + Fallback│  │        │ │
│  └──────────┘  └─────────────────┘  └────────┘ │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │         AUTH0 TOKEN VAULT LAYER           │  │
│  │  token_vault.py                           │  │
│  │  Exchange Auth0 token → Google token      │  │
│  │  Send appeal FROM user's real Gmail       │  │
│  │  Add deadline to user's Google Calendar   │  │
│  └───────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┴──────────────────┐
    │                             │
┌───▼────────┐         ┌─────────▼──────────┐
│  ChromaDB  │         │      Supabase       │
│            │         │                     │
│ Vector     │         │ Auth · Audit Logs   │
│ Store      │         │ Row Level Security  │
│ Policy     │         │ JWT Issuance        │
│ Rules      │         │                     │
└────────────┘         └────────────────────┘
```

---

## What Makes This Technically Strong

**RAG Pipeline built from scratch** — no LangChain, no frameworks. Direct FastAPI orchestration. Policy PDFs are chunked at 800 words with 100-word overlap, embedded via Gemini's API, stored in ChromaDB with cosine similarity search. Every design decision is deliberate and explainable.

**Dual-audience generation** — one Gemini call with a carefully engineered system prompt produces two structurally different explanations simultaneously. Clinical language for the doctor, plain English for the patient. This is not two API calls — it's one call with a JSON schema that forces both outputs.

**Hallucination guard** — after Gemini generates an explanation, we extract verifiable claims (section numbers, dollar amounts, day counts, specific phrases) using regex and check each one against the source chunks. If less than 70% of claims are verifiable, the response is flagged and the user sees a warning. The AI is not trusted blindly.

**Production failure handling** — tenacity retry with exponential backoff on every Gemini call. Three retries at 2s, 4s, 8s intervals. If all fail, a structured fallback response is returned. The server never returns a 500 to the user because Gemini had a bad moment.

**PHI stripping** — before any text reaches an external API, regex patterns strip SSNs, phone numbers, email addresses, dates of birth, medical record numbers, and common first names. The clean text goes to Gemini. The original never leaves our server.

**Observability** — Langfuse traces every agent call with input, output, confidence score, latency, and token count. In production, every AI decision is auditable.

**Role-based separation enforced at every layer** — org code on signup, JWT role claim, backend `require_clinician` FastAPI dependency, and frontend conditional rendering. A patient cannot reach a clinical endpoint even with a valid token.

---

## Demo Assets

### Demo Insurance Policy PDF

Download the demo policy used in the demo video:

**[→ demo_insurance_policy.pdf](demo_insurance_policy.pdf)**

This is a synthetic Blue Shield PPO policy document (8 pages) created for demo purposes. It contains realistic policy sections including:
- Section 2.1.3 — Prior Authorization for Advanced Imaging
- Section 3.1 — Medical Necessity Definition
- Section 5.3 — Member Appeal Rights
- Denial code reference table with CO-4, CO-11, CO-97, and more

### Demo Denial Codes to Try

```
CO-4 - The service is inconsistent with the payer's payment policy.
MRI scan of the lumbar spine was denied.
```

```
CO-97 - The benefit for this service is included in the payment
for another service. Physical therapy session denied.
```

```
Prior authorization was not obtained before the inpatient
hospital admission on January 15, 2026.
```

---

## Local Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Git

### Step 1 — Clone

```bash
git clone https://github.com/devu729/ClearCare.git
cd ClearCare
```

### Step 2 — Get API Keys

**Gemini (required)**
1. Go to https://aistudio.google.com → Get API Key
2. Copy key starting with `AIza...`

**Supabase (required)**
1. Go to https://supabase.com → New project
2. Project Settings → API → copy **Project URL** and **service_role key** and **anon key**
3. SQL Editor → run:

```sql
CREATE TABLE audit_logs (
  id          uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id     text,
  action      text NOT NULL,
  resource    text,
  ip_address  text,
  created_at  timestamptz DEFAULT now()
);

ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own logs"
  ON audit_logs FOR SELECT
  USING (auth.uid()::text = user_id);

CREATE POLICY "Service role insert"
  ON audit_logs FOR INSERT
  WITH CHECK (true);
```

4. Authentication → Providers → Email → **turn off Confirm email**

**Resend (required for email)**
1. Go to https://resend.com → free account
2. API Keys → Create API Key
3. Copy key starting with `re_...`
4. **Important:** Free tier only sends to your verified email address

**Langfuse (optional)**
1. Go to https://cloud.langfuse.com → free account
2. Settings → API Keys → Create
3. Copy `pk-lf-...` and `sk-lf-...`

**Auth0 Token Vault (optional — for send-from-Gmail feature)**
1. Go to https://manage.auth0.com → free account
2. Applications → Create Application → Regular Web Application
3. Applications → APIs → Create API → identifier: `https://clearcare-api.com`
4. From your API page → Add Application → creates Custom API Client → copy its ID and secret
5. Custom API Client → Settings → Advanced → Grant Types → enable **Token Vault**

### Step 3 — Backend

```bash
cd backend
python -m venv venv

# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```env
# ── Required ───────────────────────────────────────
GEMINI_API_KEY=AIza...

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...service_role_key...

RESEND_API_KEY=re_...

CHROMA_PERSIST_PATH=./chroma_db
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# ── Optional — Observability ────────────────────────
# App works without these. Add them to see AI traces.
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# ── Optional — Auth0 Token Vault ───────────────────
# Required only for send-from-user's-Gmail feature.
# Without these, email falls back to Resend (generic sender).
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://clearcare-api.com
AUTH0_CLIENT_ID=your_webapp_client_id
AUTH0_CLIENT_SECRET=your_webapp_client_secret
AUTH0_CUSTOM_API_CLIENT_ID=your_custom_api_client_id
AUTH0_CUSTOM_API_CLIENT_SECRET=your_custom_api_client_secret
```

```bash
uvicorn main:app --reload --port 8000
```

Verify: http://localhost:8000/health → `{"status":"ok"}`

Interactive API docs: http://localhost:8000/docs

### Step 4 — Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...anon_key...
VITE_BACKEND_URL=http://localhost:8000
VITE_CLINICIAN_ORG_CODES=DEMO2024
```

```bash
npm run dev
```

Open http://localhost:3000

### Step 5 — Test the Flow

1. Sign up as **Clinician** with org code `DEMO2024`
2. Policy Parser → upload `demo_insurance_policy.pdf`
3. Wait for "20 rules indexed"
4. Denial Tracer → paste `CO-4 - MRI scan denied`
5. See dual explanation appear with confidence score and source citation
6. Sign out → sign up as **Patient** (no org code)
7. Explain My Denial → paste same code → see plain English only
8. Clinician → Appeal Drafter → generate letter → fill details → send to `devuanil0831@gmail.com`

---

## Deployment

### Render (Backend)

1. New Web Service → connect GitHub repo
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add `.python-version` file to `backend/` containing `3.11`
6. Environment variables — same as local `.env` plus:

```
CHROMA_PERSIST_PATH=/tmp/chroma_db
ENVIRONMENT=production
RENDER_EXTERNAL_URL=https://your-service.onrender.com
ALLOWED_ORIGINS=https://your-app.netlify.app
```

> Do **not** add `PORT` as an environment variable — Render provides it automatically.

### Netlify (Frontend)

1. New site → import from Git
2. Base directory: `frontend`
3. Build command: `npm run build`
4. Publish directory: `frontend/dist`
5. Environment variables — same as local `frontend/.env` but with production values:

```
VITE_BACKEND_URL=https://your-service.onrender.com
```

---

## API Reference

All protected endpoints require `Authorization: Bearer <supabase_jwt>`.

| Method | Endpoint | Role | Description |
|---|---|---|---|
| GET | `/health` | Public | Server health check |
| POST | `/api/policy/upload` | Clinician | Upload and index PDF |
| GET | `/api/policy/documents` | Clinician | List indexed policies |
| POST | `/api/trace/denial` | Any | Trace denial + generate explanation |
| POST | `/api/mcp/email` | Any | Send appeal letter email |
| POST | `/api/mcp/calendar` | Any | Create calendar reminder |
| GET | `/api/audit/logs` | Any | User's own audit log |
| POST | `/api/evals/run` | Clinician | Run automated eval suite |

**Trace Denial — Request**
```json
{
  "query": "CO-4 - The service is inconsistent with the payer's payment policy",
  "document_id": null,
  "generate_appeal": true,
  "patient_name": "John Smith",
  "recipient_type": "insurance"
}
```

**Trace Denial — Response**
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
  "appeal_letter": "April 3, 2026\n\nInsurance Company Appeals..."
}
```

---

## Security Architecture

| Layer | What We Did | Why |
|---|---|---|
| PHI Protection | Regex stripping before every LLM call | HIPAA — PHI must not reach third-party APIs without BAA |
| Authentication | Supabase JWT validated on every endpoint | No anonymous requests |
| Authorization | Role claims in JWT, `require_clinician` FastAPI dependency | Patients cannot reach clinical endpoints |
| Data Isolation | Supabase Row Level Security | Users only see their own data even with valid JWT |
| Session Security | 15-min inactivity timeout, `sessionStorage` for tokens | Healthcare workstations are shared |
| Audit Trail | Every action logged, no PHI in logs | HIPAA Security Rule compliance |
| Transport | HTTPS, HSTS, X-Frame-Options, X-Content-Type-Options | Standard security headers on every response |

---

## Known Limitations

| Limitation | Current State | Production Fix |
|---|---|---|
| Scanned PDFs | Not supported — text extraction only | Add OCR via Google Vision API |
| ChromaDB persistence | Resets on Render redeploy | Replace with Pinecone |
| PHI stripping | Regex patterns — misses contextual identifiers | Microsoft Presidio NLP |
| JSON parsing | Regex cleanup before parse — not guaranteed | Gemini structured output mode |
| Email sender | Resend generic address on free tier | Custom domain or Auth0 Token Vault |
| Vector storage | Single shared instance | Per-organization namespacing |

---

## Project Structure

```
clearcare/
├── demo_insurance_policy.pdf      ← Use this to test the app
├── README.md
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Typed settings via Pydantic
│   ├── observability.py           # Langfuse @observe decorator setup
│   ├── requirements.txt
│   ├── .env.example
│   ├── .python-version            # 3.11 for Render
│   ├── agents/
│   │   ├── policy_parser.py       # PDF → PHI strip → embed → ChromaDB
│   │   ├── decision_tracer.py     # RAG + Gemini + hallucination guard
│   │   └── mcp_agent.py           # Email + Calendar (Token Vault + fallback)
│   ├── auth/
│   │   ├── __init__.py
│   │   └── token_vault.py         # Auth0 Token Vault → Gmail + Calendar
│   ├── security/
│   │   ├── phi_stripper.py        # PHI removal before LLM
│   │   ├── auth_guard.py          # JWT validation + role check
│   │   └── audit_logger.py        # HIPAA audit trail
│   ├── routers/
│   │   ├── policy_router.py
│   │   ├── trace_router.py
│   │   ├── mcp_router.py
│   │   ├── audit_router.py
│   │   └── eval_router.py
│   └── evals/
│       └── eval_runner.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── lib/
        │   ├── supabaseClient.js
        │   ├── AuthContext.jsx
        │   └── agentClient.js
        ├── components/
        │   ├── ProtectedRoute.jsx
        │   ├── PolicyParser.jsx
        │   ├── DenialTracer.jsx
        │   ├── AppealDrafter.jsx
        │   └── AuditLog.jsx
        └── pages/
            ├── Login.jsx
            ├── ClinicianDashboard.jsx
            └── PatientDashboard.jsx
```

---




---

## Built By

**Devu Anil** — CS Student, India 🇮🇳

---

## Disclaimer

ClearCare is a student project built for educational and hackathon purposes. It is not a substitute for professional medical, legal, or insurance advice. Not HIPAA-certified for production use with real patient data. Always verify AI-generated content with a licensed professional.