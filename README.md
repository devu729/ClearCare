# 🏥 ClearCare — Healthcare Decision Intelligence

> **Every insurance denial. Explained. In seconds. To everyone in the room.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)](https://fastapi.tiangolo.com)
[![Cost](https://img.shields.io/badge/Monthly%20Cost-%240-brightgreen)](https://github.com)

---

## 🌐 Live Demo

> **[→ View Live Demo](#)**  
> *(Replace `#` with your Netlify URL after deployment)*

**Demo credentials:**
| Role | Email | Password | Org Code |
|---|---|---|---|
| Clinician | demo-clinician@clearcare.app | demo1234 | DEMO2024 |
| Patient | demo-patient@clearcare.app | demo1234 | — |

---

## 📸 Architecture

![ClearCare System Architecture](clearcare_architecture.png)

---

## 🚨 The Problem

Every year in the United States:

- **250 million** insurance claims are denied
- **$262 billion** is lost to wrongful or unexplained denials
- **50% of patients** give up after the first denial — never appealing
- **67% of clinicians** don't feel confident understanding AI-generated outputs
- **79% of patients** never use AI health tools — they don't trust them

When a claim is denied, nobody can explain why — not the doctor, not the patient, not even the administrator. The policy document is 300 pages. The denial code is cryptic. The appeal deadline is ticking.

**ClearCare solves this in under 30 seconds.**

---

## ✅ What ClearCare Does

```
Patient gets $4,200 bill
    ↓
Doctor doesn't know why it was denied
    ↓
Insurance portal says "not medically necessary"
    ↓
Policy PDF is 340 pages
    ↓
Nobody can explain anything
    ↓
Patient gives up → $4,200 loss

─────────────── WITH CLEARCARE ───────────────

Upload policy PDF (once)
    ↓
Enter denial code → 30 seconds
    ↓
Clinician gets: exact rule, confidence score,
                source citation, recommended actions
    ↓
Patient gets: plain English explanation,
              rights summary, appeal steps
    ↓
Generate appeal letter → fill placeholders → send
    ↓
Download deadline to calendar → never miss it
```

---

## 🧠 System Architecture

### Three Core Problems Solved

| Problem | What ClearCare Does |
|---|---|
| **Policy Logic Lock** | AI extracts all decision rules from PDF into searchable vector index |
| **Shadow AI / Clinician Trust** | Every explanation shows confidence score + exact source + page number |
| **Patient Trust Gap** | Plain English explanations + appeal letter + deadline tracking |

### Agent Pipeline

```
┌─────────────────────────────────────────────────────────┐
│                     USER LAYER                          │
│           Clinician ←──────────→ Patient                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              FRONTEND (React + Vite)                    │
│  Login · ClinicianDashboard · PatientDashboard          │
│  PolicyParser · DenialTracer · AppealDrafter · AuditLog │
└────────────────────┬────────────────────────────────────┘
                     │ JWT Auth
┌────────────────────▼────────────────────────────────────┐
│              FASTAPI BACKEND                            │
│  CORS · Security Headers · JWT Validation              │
│  Global Error Handler · Audit Logging                  │
└──────┬──────────┬──────────┬──────────┬────────────────┘
       │          │          │          │
┌──────▼──┐ ┌────▼────┐ ┌───▼────┐ ┌──▼────────┐
│ Policy  │ │Decision │ │ Dual   │ │Hallucin-  │
│ Parser  │ │ Tracer  │ │Explain │ │ation Guard│
│         │ │         │ │er      │ │           │
│PDF→chunk│ │ChromaDB │ │Clinician│ │Verify     │
│PHI strip│ │ search  │ │+Patient │ │claims vs  │
│Embed→DB │ │Conf.score│ │views   │ │source 70% │
└──────┬──┘ └────┬────┘ └───┬────┘ └──▼────────┘
       │          │          │
┌──────▼──────────▼──────────▼────────────────────────────┐
│                  DATA LAYER                             │
│                                                         │
│  ChromaDB (local)  ←── sentence-transformers (local)   │
│  Supabase DB       ←── Row Level Security              │
│  Gemini 2.5 Flash  ←── Explanations + Eval grading     │
└─────────────────────────────────────────────────────────┘
```

### Security Architecture

```
Every request passes through:

1. JWT Validation      → Supabase token verified server-side
2. PHI Stripper        → SSN, DOB, phone, email, names removed
                         before any text reaches external LLM
3. Role Guard          → Clinician endpoints reject patient tokens
4. Audit Logger        → Every action logged (no PHI in logs)
5. Security Headers    → nosniff, DENY frames, HSTS, no-store
6. Row Level Security  → Database-level: users see only own data
7. Session Timeout     → 15-minute inactivity auto-signout
8. Env Var Protection  → Zero hardcoded secrets anywhere in code
```

---

## 🛠 Tech Stack

### Frontend
| Technology | Purpose | Cost |
|---|---|---|
| React 18 + Vite | UI framework | Free |
| Supabase Auth | Login, sessions, JWT | Free |
| React Router | Role-based routing | Free |
| Outfit + DM Mono | Typography | Free (Google Fonts) |

### Backend
| Technology | Purpose | Cost |
|---|---|---|
| FastAPI | REST API framework | Free |
| PyMuPDF | PDF text extraction | Free |
| sentence-transformers | Local embeddings (all-MiniLM-L6-v2) | Free |
| ChromaDB | Local vector database | Free |
| Google Gemini 2.5 Flash | LLM explanations | Free tier |
| Supabase | Database + Auth | Free |
| Resend | Email delivery | Free (3K/month) |

### Infrastructure
| Service | Purpose | Cost |
|---|---|---|
| Netlify | Frontend hosting | Free |
| Render.com | Backend hosting | Free |
| Supabase | Database hosting | Free |
| **Total** | **Everything** | **$0/month** |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (use conda: `conda create -n clearcare python=3.11`)
- Node.js 18+
- Git

### 1. Clone
```bash
git clone https://github.com/yourusername/clearcare.git
cd clearcare
```

### 2. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your keys (see Environment Variables below)

# Start backend
uvicorn main:app --reload --port 8000
```

Verify: http://localhost:8000/health → `{"status":"ok"}`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Supabase keys

# Start frontend
npm run dev
```

Open: http://localhost:3000

### 4. Database Setup
1. Create free Supabase project at https://supabase.com
2. Go to SQL Editor → paste contents of `docs/supabase_setup.sql` → Run
3. Go to Authentication → URL Configuration → set Site URL to `http://localhost:3000`

---

## 🔑 Environment Variables

### Backend (`backend/.env`)
```env
# Google Gemini (free — https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_key_here

# Supabase (Project Settings → API)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key

# ChromaDB (local folder — no account needed)
CHROMA_PERSIST_PATH=./chroma_db

# Resend email (free — https://resend.com)
RESEND_API_KEY=re_your_key_here

# CORS
ALLOWED_ORIGINS=http://localhost:3000

ENVIRONMENT=development
```

### Frontend (`frontend/.env`)
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key_here
VITE_BACKEND_URL=http://localhost:8000
VITE_CLINICIAN_ORG_CODES=DEMO2024
```

---

## 📁 Project Structure

```
clearcare/
├── README.md
├── clearcare_architecture.png
├── docs/
│   └── supabase_setup.sql
│
├── frontend/                        # React app → Netlify
│   ├── src/
│   │   ├── lib/
│   │   │   ├── supabaseClient.js    # Supabase connection
│   │   │   ├── AuthContext.jsx      # Session + 15-min timeout
│   │   │   └── agentClient.js       # All API calls
│   │   ├── components/
│   │   │   ├── ProtectedRoute.jsx   # Auth + role guard
│   │   │   ├── PolicyParser.jsx     # PDF upload UI
│   │   │   ├── DenialTracer.jsx     # Trace + dual explanation
│   │   │   ├── AppealDrafter.jsx    # Letter + fill placeholders
│   │   │   └── AuditLog.jsx         # HIPAA audit trail
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── ClinicianDashboard.jsx
│   │   │   └── PatientDashboard.jsx
│   │   └── App.jsx
│   └── package.json
│
└── backend/                         # FastAPI → Render.com
    ├── agents/
    │   ├── policy_parser.py         # PDF → ChromaDB pipeline
    │   ├── decision_tracer.py       # Gemini dual explanations
    │   └── mcp_agent.py             # Email + ICS calendar
    ├── security/
    │   ├── phi_stripper.py          # Remove PHI before LLM
    │   ├── auth_guard.py            # JWT validation
    │   └── audit_logger.py          # HIPAA logging
    ├── routers/
    │   ├── policy_router.py         # POST /api/policy/upload
    │   ├── trace_router.py          # POST /api/trace/denial
    │   ├── mcp_router.py            # POST /api/mcp/email+calendar
    │   ├── audit_router.py          # GET /api/audit/logs
    │   └── eval_router.py           # POST /api/evals/run
    ├── evals/
    │   └── eval_runner.py           # 5-case eval suite
    ├── config.py
    ├── main.py
    └── requirements.txt
```

---

## 🎯 Features

### For Clinicians
- 📄 **Policy Parser** — Upload any insurance PDF, rules extracted and indexed automatically
- 🔍 **Denial Tracer** — Enter denial code → exact policy rule match in seconds
- 📊 **Confidence Score** — Know how certain the AI is before acting
- ✅ **Source Citation** — Every claim linked to exact page and section
- ✍️ **Appeal Drafter** — Generate formal appeal letters with clinical arguments
- 🛡️ **Audit Log** — Full HIPAA-compliant action trail

### For Patients
- 🔍 **Explain My Denial** — Plain English explanation of why a claim was denied
- ✍️ **Write My Appeal** — Pre-drafted appeal letter with fill-in placeholders
- 📅 **Deadline Tracking** — Download `.ics` file → deadline in any calendar app
- 📧 **Email Appeal** — Send letter directly from the platform
- 🏛️ **Know Your Rights** — Automatic display of patient rights

### Security
- 🔐 PHI stripped before every LLM call
- 🔑 JWT validated on every endpoint
- 🗄️ Row Level Security — users see only their own data
- 📋 HIPAA-aligned audit trail
- ⏱️ 15-minute session timeout
- 🚫 Zero hardcoded secrets

---

## 📊 Evaluation

ClearCare includes a built-in evaluation suite that measures:

- **Retrieval Accuracy** — Does it find the right policy rule?
- **Explanation Quality** — Gemini grades Gemini (1–5 scale)
- **Hallucination Rate** — Claims verified against source (70% threshold)

```bash
# Run evaluation suite
curl -X POST http://localhost:8000/api/evals/run \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"document_id": "your_doc_id"}'
```

Target thresholds before production use:
- Pass rate ≥ 80%
- Average quality score ≥ 3.5/5
- `ready_for_production: true`

---

## 🌍 Impact

| Metric | Reality |
|---|---|
| US insurance denials/year | ~250 million |
| Value lost to wrongful denials | $262 billion |
| Patients who give up after first denial | ~50% |
| Time to understand a denial (before) | 3–5 hours |
| Time to understand a denial (ClearCare) | 30 seconds |
| Cost to deploy ClearCare | $0/month |

---

## 🗺️ Roadmap

- [ ] FHIR integration for direct EHR connectivity
- [ ] Multi-language patient explanations (Hindi, Spanish, Mandarin)
- [ ] Slack alerts for urgent high-severity denials
- [ ] Bulk denial processing for hospital billing departments
- [ ] Mobile app (React Native)
- [ ] HIPAA BAA with Supabase Pro for production PHI
- [ ] Automated prior authorization request generation

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## ⚠️ Disclaimer

ClearCare is an AI-assisted tool for educational and informational purposes. It is not a substitute for professional legal, medical, or healthcare advice. All AI-generated explanations should be verified by a licensed healthcare professional before acting on them. ClearCare is not HIPAA-certified for production use without proper Business Associate Agreements (BAAs) with all service providers.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👨‍💻 Built By

**Devu Anil**  
Healthcare AI Agent · Built with React, FastAPI, Gemini, ChromaDB  
University Student · India 🇮🇳

---

<div align="center">

**ClearCare** — Because every patient deserves to understand their healthcare.

⭐ Star this repo if you find it useful

</div>
