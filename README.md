# 🏥 ClearCare — Healthcare Decision Intelligence

> When an insurance claim is denied, nobody can explain why. ClearCare reads the policy, finds the exact rule, and explains it — to the clinician in clinical language, and to the patient in plain English. Then it drafts the appeal letter and sends it from the patient's own Gmail using **Auth0 Token Vault**.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-clearcarever0.netlify.app-0ea5e9?style=for-the-badge)](https://clearcarever0.netlify.app)
[![Backend](https://img.shields.io/badge/Backend-Online-46E3B7?style=for-the-badge)](https://clearcare-44nc.onrender.com/health)
[![Auth0](https://img.shields.io/badge/Auth0-Token%20Vault-EB5424?style=for-the-badge)](https://auth0.com)
[![Demo Video](https://img.shields.io/badge/Demo-YouTube-red?style=for-the-badge)](https://youtu.be/sdwFkKAcPKQ?si=5z_YKkglFayz-rpX)

---

## 📹 Demo Video

**[→ Watch 3-Minute Demo on YouTube](https://youtu.be/sdwFkKAcPKQ?si=5z_YKkglFayz-rpX)**

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

An AI-generated appeal letter sent from `onboarding@resend.dev` gets filtered, ignored, or deprioritized. **An appeal from `john.smith@gmail.com` is different — it has real identity, legal standing, and an auditable paper trail.**

Before Token Vault, building this would require building an OAuth 2.0 consent flow from scratch, storing and encrypting refresh tokens per user, handling token expiry and rotation, and taking on the security liability of storing user credentials.

**Token Vault replaced all of that with a single API call.**

```python
# backend/auth/token_vault.py
google_token = await exchange_token_for_google(user_access_token)
# → Auth0 handles OAuth, storage, refresh, revocation
# → ClearCare gets a usable token
# → Appeal letter sent from john.smith@gmail.com
```

In healthcare, the identity of the sender determines whether an appeal gets reviewed or ignored.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────┐
│              FRONTEND (Netlify)                  │
│         React 18 + Vite                         │
│  Login │ Clinician Dashboard │ Patient Portal    │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS + Supabase JWT
┌──────────────────▼──────────────────────────────┐
│              BACKEND (Render)                    │
│         FastAPI · Python 3.11                   │
│                                                  │
│  ┌─────────────────────────────────────────┐    │
│  │  PHI Strip │ JWT Guard │ Audit Logger   │    │
│  └────────────────────────┬────────────────┘    │
│                           │                     │
│  ┌──────────┐  ┌──────────▼──────┐  ┌────────┐ │
│  │ Policy   │  │ Decision Tracer │  │  MCP   │ │
│  │ Parser   │  │ ChromaDB Search │  │ Agent  │ │
│  │ PDF→Text │  │ Gemini LLM      │  │ Resend │ │
│  │ PHI Strip│  │ Dual Explain    │  │ Email  │ │
│  │ Embed    │  │ Hallucination   │  │ ICS Cal│ │
│  │ ChromaDB │  │ Guard + Retry   │  │        │ │
│  └──────────┘  └─────────────────┘  └────────┘ │
│                                                  │
│  ┌───────────────────────────────────────────┐  │
│  │         AUTH0 TOKEN VAULT LAYER           │  │
│  │  Exchange Auth0 token → Google token      │  │
│  │  Send appeal FROM user's real Gmail       │  │
│  │  Add deadline to user's Google Calendar   │  │
│  └───────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┘
    ┌──────────┴──────────────────┐
┌───▼────────┐         ┌─────────▼──────────┐
│  ChromaDB  │         │      Supabase       │
│ Vector     │         │ Auth · Audit Logs   │
│ Store      │         │ Row Level Security  │
└────────────┘         └────────────────────┘
```

---

## What Makes This Technically Strong

**RAG Pipeline built from scratch** — no LangChain. Direct FastAPI orchestration. Policy PDFs are chunked at 800 words with 100-word overlap, embedded via Gemini, stored in ChromaDB with cosine similarity search.

**Dual-audience generation** — one Gemini call with a carefully engineered system prompt produces two structurally different explanations simultaneously via a JSON schema that forces both outputs.

**Hallucination guard** — verifiable claims (section numbers, dollar amounts, day counts) are extracted post-generation and checked against source chunks. If less than 70% verify, the user sees a warning.

**Production failure handling** — tenacity retry with exponential backoff on every Gemini call. Three retries at 2s, 4s, 8s. If all fail, a structured fallback response is returned.

**PHI stripping** — before any text reaches an external API, regex patterns strip SSNs, phone numbers, email addresses, dates of birth, and medical record numbers.

**Observability** — Langfuse traces every agent call with input, output, confidence score, latency, and token count.

**Role-based separation at every layer** — org code on signup, JWT role claim, backend `require_clinician` FastAPI dependency, and frontend conditional rendering.

---

## Demo Assets

### Demo Insurance Policy PDF

Download: **[demo_insurance_policy.pdf](demo_insurance_policy.pdf)**

Synthetic Blue Shield PPO policy (8 pages) containing:
- Section 2.1.3 — Prior Authorization for Advanced Imaging
- Section 3.1 — Medical Necessity Definition
- Section 5.3 — Member Appeal Rights
- Denial code reference table: CO-4, CO-11, CO-97, and more

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

**Gemini (required)** → https://aistudio.google.com → Get API Key

**Supabase (required)** → https://supabase.com → New project → Settings → API

Run this SQL in Supabase:

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

CREATE POLICY "Users see own logs" ON audit_logs FOR SELECT USING (auth.uid()::text = user_id);
CREATE POLICY "Service role insert" ON audit_logs FOR INSERT WITH CHECK (true);
```

Turn off **Confirm email** under Authentication → Providers → Email.

**Resend (required for email)** → https://resend.com → API Keys → Create

**Langfuse (optional)** → https://cloud.langfuse.com → free account

**Auth0 Token Vault (optional — for send-from-Gmail)** → https://manage.auth0.com → Applications → Create → Regular Web Application → APIs → Create API → identifier: `https://clearcare-api.com` → enable Token Vault grant type

### Step 3 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```env
# Required
GEMINI_API_KEY=AIza...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJ...
RESEND_API_KEY=re_...
CHROMA_PERSIST_PATH=./chroma_db
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development

# Optional — Observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional — Auth0 Token Vault
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_AUDIENCE=https://clearcare-api.com
AUTH0_CLIENT_ID=...
AUTH0_CLIENT_SECRET=...
AUTH0_CUSTOM_API_CLIENT_ID=...
AUTH0_CUSTOM_API_CLIENT_SECRET=...
```

```bash
uvicorn main:app --reload --port 8000
```

Verify: http://localhost:8000/health → `{"status":"ok"}`

### Step 4 — Frontend

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
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
5. See dual explanation with confidence score and source citation
6. Sign out → sign up as **Patient** (no org code)
7. Explain My Denial → paste same code → see plain English only
8. Clinician → Appeal Drafter → send to `devuanil0831@gmail.com`

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

**Trace Denial — Response**
```json
{
  "clinician_explanation": "The MRI scan was denied with CO-4...",
  "patient_explanation": "Your MRI was denied because...",
  "source_rule": "Section 2.1.3 — Advanced Diagnostic Imaging",
  "appeal_deadline": "180 days from denial notice",
  "confidence": 0.82,
  "verified": true,
  "appeal_letter": "..."
}
```

---

## Security Architecture

| Layer | What We Did | Why |
|---|---|---|
| PHI Protection | Regex stripping before every LLM call | HIPAA — PHI must not reach third-party APIs |
| Authentication | Supabase JWT on every endpoint | No anonymous requests |
| Authorization | Role claims in JWT + `require_clinician` dependency | Patients cannot reach clinical endpoints |
| Data Isolation | Supabase Row Level Security | Users only see their own data |
| Session Security | 15-min inactivity timeout, `sessionStorage` | Healthcare workstations are shared |
| Audit Trail | Every action logged, no PHI in logs | HIPAA Security Rule compliance |
| Transport | HTTPS, HSTS, security headers | Standard production hardening |

---

## Known Limitations

| Limitation | Current State | Production Fix |
|---|---|---|
| Scanned PDFs | Not supported | Add OCR via Google Vision API |
| ChromaDB persistence | Resets on redeploy | Replace with Pinecone |
| PHI stripping | Regex only | Microsoft Presidio NLP |
| Email sender | Generic on free tier | Custom domain or Auth0 Token Vault |

---

## Project Structure

```
clearcare/
├── demo_insurance_policy.pdf
├── backend/
│   ├── main.py
│   ├── agents/
│   │   ├── policy_parser.py       # PDF → embed → ChromaDB
│   │   ├── decision_tracer.py     # RAG + Gemini + hallucination guard
│   │   └── mcp_agent.py           # Email + Calendar
│   ├── auth/
│   │   └── token_vault.py         # Auth0 Token Vault → Gmail + Calendar
│   ├── security/
│   │   ├── phi_stripper.py
│   │   ├── auth_guard.py
│   │   └── audit_logger.py
│   └── routers/
└── frontend/
    └── src/
        ├── components/
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

## Built By

**Devu Anil** — CS Student, India 🇮🇳

---

## Disclaimer

ClearCare is a student project built for educational and hackathon purposes. Not HIPAA-certified for production use with real patient data. Always verify AI-generated content with a licensed professional.
