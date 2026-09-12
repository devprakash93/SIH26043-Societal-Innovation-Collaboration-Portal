<div align="center">

# 🇮🇳 SamadhanX
### Smart India Hackathon 2026 — Problem Statement SIH 26043

**A Societal Innovation Collaboration Portal**
Connecting citizens, government, higher education institutions, and industry partners to transform real-world problems into academic innovations.

[![Live Frontend](https://img.shields.io/badge/Frontend-Live%20on%20Cloudflare-orange?style=for-the-badge&logo=cloudflare)](https://samadhanx-ar9.pages.dev)
[![Live Backend](https://img.shields.io/badge/Backend-Live%20on%20Render-46E3B7?style=for-the-badge&logo=render)](https://samadhanx-backend-arnavf.onrender.com/api/challenges/)
[![Django](https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql)](https://neon.tech)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Features by Role](#-features-by-role)
- [Tech Stack](#-tech-stack)
- [Local Setup](#-local-setup)
- [Environment Variables](#-environment-variables)
- [Production Deployment](#-production-deployment)
- [Demo Credentials](#-demo-credentials)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)

---

## 🌟 Overview

SamadhanX is a full-stack web platform that bridges the gap between grassroots civic problems and academic/industrial solutions. Citizens report real problems, the government validates and routes them to HEIs (Higher Education Institutions), academic teams form to solve them, and industry partners provide funding and mentorship.

```
Citizen Reports Problem
        ↓
Government Admin Reviews & Routes
        ↓
HEI SPOC Assigns to Faculty Team
        ↓
Faculty + Students Build Solution
        ↓
Industry Partner Funds & Mentors
        ↓
Problem Solved → Impact Recorded
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React + Vite)                │
│              Cloudflare Pages — Auto-deploy             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Citizen  │ │  Admin   │ │   HEI    │ │Industry  │  │
│  │ Portal   │ │Dashboard │ │  Portal  │ │ Partner  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
└─────────────────────────────────────────────────────────┘
                           │ HTTPS + JWT
┌─────────────────────────────────────────────────────────┐
│                BACKEND (Django 5 + DRF)                 │
│                Render — Auto-deploy                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Challenges│ │Industry  │ │Universities│ │Analytics │  │
│  │   API    │ │   API    │ │    API   │ │   API    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │      AI Engine (Gemini) + Duplicate Detection    │  │
│  │      (sentence-transformers / MiniLM-L6-v2)      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │ DATABASE_URL
┌─────────────────────────────────────────────────────────┐
│              DATABASE (PostgreSQL on Neon)              │
│                   Serverless Postgres                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎭 Features by Role

### 👤 Citizen
- Register and submit civic problems with photo evidence
- Track problem status through the pipeline (Submitted → Routed → In Progress → Completed)
- View AI-assigned category and priority
- Receive push notifications on status changes
- Mobile-first bottom navigation

### 🏛️ Government Admin
- Validate and route problems to HEIs
- Global search across all challenges and universities
- Manage master data (districts, categories, expertise areas)
- Export reports (Excel / PDF)
- AI Configuration panel (switch providers, set thresholds)
- Semantic duplicate detection with side-by-side review UI
- Problem Twin detection across similar challenges
- Audit logs and user management
- HEI approval workflow

### 🎓 HEI SPOC (Higher Education Institution)
- View routed challenges assigned to institution
- Form interdisciplinary project teams
- Assign faculty mentors
- Track milestone progress
- Receive partnership offers from industry

### 👨‍🏫 Faculty Mentor
- View assigned teams
- Track team milestones
- Provide guidance and reviews

### 🏭 Industry Partner
- Browse live HEI projects by sector, district, and technology
- Send partnership / funding offers to teams
- View and manage all active partnerships
- Assign industry mentors to teams
- Share project documents securely
- View impact summary dashboard

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, Vite 8, React Router v6 |
| **UI** | Custom CSS design system (no component library) |
| **State** | React Context API + `localStorage` for JWT |
| **Backend** | Django 5.2, Django REST Framework 3.15 |
| **Auth** | JWT via `djangorestframework-simplejwt` |
| **Database** | SQLite (dev) / PostgreSQL on Neon (prod) |
| **AI Categorization** | Google Gemini (`gemini-1.5-flash`) |
| **Duplicate Detection** | `sentence-transformers` (MiniLM-L6-v2, cosine similarity) |
| **Static Files** | WhiteNoise (production) |
| **Frontend Hosting** | Cloudflare Pages |
| **Backend Hosting** | Render (free tier) |
| **Database Hosting** | Neon (serverless PostgreSQL) |
| **Auto-Deploy** | GitHub → Render + Cloudflare (on every push to `main`) |

---

## 💻 Local Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/Arnav-Naive/SIH26043-Societal-Innovation-Collaboration-Portal.git
cd SIH26043-Societal-Innovation-Collaboration-Portal
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Create Backend Environment File

Create a file at `backend/.env` with the following contents:

```env
SECRET_KEY=dev-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DATABASE_URL=sqlite:///db.sqlite3
AI_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-flash
AI_TIMEOUT_SECONDS=10
```

> **Get a free Gemini API key at:** https://aistudio.google.com/apikey
> Without it, the app falls back to keyword-based categorization automatically.

### 4. Run Migrations and Seed Demo Data

```bash
python manage.py migrate
python manage.py seed_demo
```

This creates all demo users, sample challenges, universities, teams, and industry partnerships.

### 5. Start the Backend Server

```bash
python manage.py runserver
```

Backend runs at: `http://localhost:8000`

### 6. Frontend Setup

Open a **new terminal** (keep the backend running):

```bash
cd frontend

# Install dependencies
npm install
```

### 7. Create Frontend Environment File

Create a file at `frontend/.env.local` with:

```env
VITE_API_BASE_URL=http://localhost:8000/api
```

> This file is gitignored and safe to keep locally.

### 8. Start the Frontend

```bash
npm run dev
```

Frontend runs at: `http://localhost:5173`

### 9. Verify Everything Works

1. Open `http://localhost:5173`
2. Log in with any demo credential (see [Demo Credentials](#-demo-credentials))
3. You should land on the correct role dashboard

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

| Variable | Required | Description | Example |
|---|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key — must be unique in production | 50+ char random string |
| `DEBUG` | ✅ | `True` for dev, `False` for production | `False` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated list of allowed hostnames | `yourapp.onrender.com` |
| `CORS_ALLOWED_ORIGINS` | ✅ | Frontend URL(s) allowed to call the API | `https://yourapp.pages.dev` |
| `DATABASE_URL` | ✅ | Full database connection string | `postgresql://user:pass@host/db` |
| `AI_PROVIDER` | ✅ | AI categorization backend: `gemini` or `keyword` | `gemini` |
| `GEMINI_API_KEY` | ⚠️ | Required only when `AI_PROVIDER=gemini` | `AQ.xxxx...` |
| `GEMINI_MODEL` | ❌ | Gemini model to use | `gemini-1.5-flash` |
| `AI_TIMEOUT_SECONDS` | ❌ | API timeout in seconds | `10` |

### Frontend (`frontend/.env.local` or Cloudflare env var)

| Variable | Required | Description | Example |
|---|---|---|---|
| `VITE_API_BASE_URL` | ✅ | Full URL to the backend API | `https://samadhanx-backend-arnavf.onrender.com/api` |

---

## 🚀 Production Deployment

The app auto-deploys to production on every `git push` to `main`.

### Backend — Render

| Setting | Value |
|---|---|
| **Service type** | Web Service |
| **Repository** | This GitHub repo |
| **Root directory** | `backend` |
| **Runtime** | Python |
| **Build command** | `pip install --no-cache-dir -r requirements.txt && python manage.py migrate --no-input && python manage.py seed_demo && python manage.py collectstatic --no-input` |
| **Start command** | `gunicorn config.wsgi:application` |
| **Plan** | Free (0.1 CPU, 512 MB RAM) |

**Required environment variables on Render:**

```
SECRET_KEY=<generate at djecrety.ir>
DEBUG=False
ALLOWED_HOSTS=samadhanx-backend-arnavf.onrender.com
DATABASE_URL=<your Neon connection string>
CORS_ALLOWED_ORIGINS=https://samadhanx-ar9.pages.dev
AI_PROVIDER=gemini
GEMINI_API_KEY=<your key>
```

### Database — Neon

1. Create a project at [neon.tech](https://neon.tech) (free tier)
2. Copy the connection string from **Connection Details**
3. Paste it as `DATABASE_URL` in Render

### Frontend — Cloudflare Pages

| Setting | Value |
|---|---|
| **Repository** | This GitHub repo |
| **Root directory** | `frontend` |
| **Build command** | `npm run build` |
| **Output directory** | `dist` |

**Required environment variable on Cloudflare:**

```
VITE_API_BASE_URL=https://samadhanx-backend-arnavf.onrender.com/api
```

> SPA routing is handled automatically by `frontend/public/_redirects`.

---

## 🔑 Demo Credentials

All demo accounts use the password: **`Demo@1234`**

| Role | Username | Access |
|---|---|---|
| 🏛️ Government Admin | `admin` | Full platform management, AI config, reports |
| 👤 Citizen | `citizen1` | Submit and track civic problems |
| 🎓 HEI SPOC | `hei_spoc1` | Manage challenges routed to BIT Ranchi |
| 👨‍🏫 Faculty Mentor | `faculty1` | View and guide assigned teams |
| 🏭 Industry Partner | `industry1` | Browse projects, manage partnerships |

---

## 📡 API Reference

Base URL (production): `https://samadhanx-backend-arnavf.onrender.com/api`

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register/` | Register new user |
| `POST` | `/auth/login/` | Login — returns JWT access + refresh tokens |
| `POST` | `/auth/logout/` | Blacklist refresh token |
| `POST` | `/auth/token/refresh/` | Get new access token |
| `GET` | `/auth/me/` | Get current user profile |
| `GET` | `/auth/notifications/` | Get user notifications |

### Challenges
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/challenges/` | List challenges (role-filtered) |
| `POST` | `/challenges/` | Submit new challenge (citizen) |
| `GET` | `/challenges/{id}/` | Challenge detail |
| `PATCH` | `/challenges/{id}/` | Update challenge |
| `GET` | `/duplicate-flags/` | List pending duplicate flags (admin) |
| `POST` | `/duplicate-flags/{id}/review/` | Approve or reject duplicate flag |

### Industry
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/industry/projects/` | Browse HEI projects |
| `POST` | `/industry/projects/{id}/offer-support/` | Send partnership offer |
| `GET` | `/industry/my-partnerships/` | My partnerships |
| `GET` | `/industry/my-impact-summary/` | Impact dashboard data |
| `GET` | `/industry/teams/{id}/documents/` | List shared documents |
| `POST` | `/industry/teams/{id}/documents/` | Upload a document |

### Universities
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/universities/` | List universities |
| `GET` | `/universities/{id}/` | University detail |

---

## 📁 Project Structure

```
SIH26043-Societal-Innovation-Collaboration-Portal/
├── backend/                        # Django backend
│   ├── accounts/                   # User model, auth, JWT, notifications
│   ├── challenges/                 # Core challenge lifecycle + AI + duplicate detection
│   │   ├── duplicate_detection.py  # sentence-transformers cosine similarity
│   │   ├── categorizer.py          # Gemini AI / keyword categorization
│   │   └── management/commands/
│   │       └── seed_demo.py        # Demo data seeder (idempotent)
│   ├── industry/                   # Industry partner models, views, partnerships
│   ├── universities/               # HEI, teams, milestones
│   ├── projects/                   # Project tracking
│   ├── master_data/                # Districts, categories, AI config
│   ├── analytics/                  # Reports, exports, global search
│   ├── config/                     # Django settings, URLs, WSGI
│   │   ├── settings.py             # Env-var based configuration
│   │   └── views.py                # JSON 404/500 handlers
│   ├── requirements.txt
│   ├── runtime.txt                 # Pins Python 3.11.9 for Render
│   └── .env                        # Local secrets (gitignored)
│
├── frontend/                       # React + Vite frontend
│   ├── src/
│   │   ├── api/                    # Axios API clients per domain
│   │   │   ├── axiosClient.js      # JWT interceptor + auto-refresh
│   │   │   ├── challenges.js
│   │   │   ├── industry.js
│   │   │   └── auth.js
│   │   ├── components/common/      # Sidebar, TopHeader, MobileBottomNav
│   │   ├── context/AuthContext.jsx # Global auth state
│   │   ├── pages/
│   │   │   ├── admin/              # Gov Admin dashboard + tools
│   │   │   ├── citizen/            # Citizen portal
│   │   │   ├── hei/                # HEI SPOC portal
│   │   │   ├── faculty/            # Faculty mentor portal
│   │   │   ├── industry/           # Industry partner portal
│   │   │   └── auth/               # Login, Register, HEI Register
│   │   └── routes/
│   │       ├── AppRoutes.jsx       # All routes with lazy loading
│   │       └── ProtectedRoute.jsx  # RBAC + ?next= redirect
│   ├── public/
│   │   └── _redirects              # Cloudflare SPA routing fix
│   ├── .env.local                  # Local dev env (gitignored)
│   ├── vite.config.js              # Dev proxy to localhost:8000
│   └── index.css                   # Design system + responsive CSS
│
├── .gitignore
├── .python-version                 # Pins Python 3.11.9 for Cloudflare
└── README.md
```

---

## 🤝 Contributing

### Branching Strategy
- `main` — production branch (auto-deploys to Render + Cloudflare)
- Feature branches — create from `main`, submit PRs

### Workflow for New Features

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
# ... make your changes ...
git add .
git commit -m "feat: describe what you added"
git push origin feature/your-feature-name
# Open a Pull Request on GitHub → merge to main → auto-deploys
```

### Production Compatibility Checklist
Before opening a PR, confirm:
- [ ] `python manage.py check` passes with 0 issues
- [ ] `npm run build` completes with 0 errors
- [ ] New Django models have migrations (`python manage.py makemigrations`)
- [ ] New env vars are documented in this README
- [ ] No hardcoded localhost URLs or API keys
- [ ] New API endpoints are added to the API Reference table above
- [ ] `seed_demo.py` updated if new demo data is needed (use `get_or_create`)

### Local Dev Commands

```bash
# Backend
python manage.py runserver          # Start dev server
python manage.py makemigrations     # Create new migrations
python manage.py migrate            # Apply migrations
python manage.py seed_demo          # Re-seed demo data (safe to re-run)
python manage.py check              # Verify configuration

# Frontend
npm run dev                         # Start dev server (port 5173)
npm run build                       # Production build
npm run preview                     # Preview production build locally
```

---

<div align="center">
**Built for Smart India Hackathon 2026**
</div>