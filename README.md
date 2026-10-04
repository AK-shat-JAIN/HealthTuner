# HealthTuner 🌿

**HealthTuner** is an intelligent, full-stack Health & Workout Companion Web Application built with **FastAPI**, **Neon Cloud PostgreSQL**, **SQLAlchemy**, **Jinja2**, and **Tailwind CSS**, integrated with **Backboard.io** for structured AI health intelligence and recommendations.

---

## 🚀 Key Features

- 🔐 **Authentication & Session Management**:
  - Secure bcrypt password hashing.
  - Auto-login upon registration with cookie-based session management.
- 📅 **Interactive Responsive Calendar Dashboard**:
  - Month-at-a-glance layout with full mobile responsiveness and touch horizontal scrolling.
  - Date access control: Active past/present days, visually locked future dates.
  - Workload badges (`Easy`, `Medium`, `Maximum`).
- ⚡ **Dynamic Multi-Tier Workload Logger**:
  - **Easy:** 1 open quick-log textarea for rapid check-ins.
  - **Medium:** 3 targeted inputs (Activity, Nutrition/Hydration, Energy/Notes).
  - **Maximum:** 5 structured inputs (Training Breakdown, Macros/Diet, Sleep/Recovery, Stress & Wellness, Key Accomplishments).
- 🧠 **AI Health Intelligence & Timeline (Backboard.io)**:
  - Custom date range or 1-click **Full Current Month** AI analysis.
  - Structured 2-part health assessments:
    1. *Behavioral Summary* (workload intensity, volume, recovery markers).
    2. *Actionable Recommendations & Goal Suggestions* (recovery timing, deload advice, targets).
  - Formatted markdown output with lists, bold headers, and subheadings.
  - Historical AI timeline with one-click record deletion and inspection.
- ☁️ **Cloud Database Architecture (Neon Postgres)**:
  - Backed by serverless Neon PostgreSQL with auto-scaling compute and connection pooling (`DATABASE_URL`).
  - Automatic fallback compatibility for local SQLite during isolated offline testing.
- 🌓 **Zero-Flicker Light/Dark Mode**:
  - Smooth theme switcher persisted via `localStorage` and system theme detection.

---

## 🛠️ Tech Stack & Architecture

- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **Database**: [Neon Cloud PostgreSQL](https://neon.tech/) & SQLAlchemy ORM
- **Database Driver**: `psycopg2-binary`
- **AI Inference Engine**: [Backboard.io](https://backboard.io/) (with built-in heuristics fallback)
- **Frontend / UI**: Jinja2 Templates, Tailwind CSS (Dark Mode enabled), Lucide Icons, Marked.js
- **Server**: Uvicorn ASGI

---

## 📂 Project Structure

```
HealthTuner/
├── main.py              # FastAPI server, authentication routes, calendar & AI APIs
├── database.py          # SQLAlchemy engine, Neon Postgres pooling & session handling
├── models.py            # User, DailyLog, and AISummary ORM models
├── auth.py              # Password hashing & verification with bcrypt
├── ai_service.py        # Backboard.io LLM client & structured prompt pipeline
├── neon.ts              # Neon configuration & branching definition
├── requirements.txt     # Python package dependencies
├── .env.example         # Environment template with Postgres & Backboard configs
├── .env                 # Local configuration & environment variables
├── .gitignore           # Git ignore rules for secrets and temporary files
├── templates/
│   ├── base.html        # Main layout with Tailwind, Marked.js & theme switcher
│   ├── login.html       # Clean login screen
│   ├── register.html    # Registration screen
│   ├── dashboard.html   # Monthly calendar grid & dynamic modal logger
│   └── timeline.html    # AI Intelligence generator & historical timeline
└── static/
    ├── css/style.css    # Custom animations, markdown styling & responsive utilities
    └── js/theme.js      # Global dark/light mode toggle
```

---

## ⚡ Quickstart Guide

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/AK-shat-JAIN/HealthTuner.git
cd HealthTuner
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Set your configuration values in `.env`:
```env
# Backboard.io Configuration
BACKBOARD_API_KEY=your_backboard_io_api_key_here
BACKBOARD_API_URL=https://api.backboard.io/v1/chat/completions
BACKBOARD_MODEL=meta-llama/llama-3-8b-instruct

# Neon Cloud PostgreSQL Connection String
DATABASE_URL=postgresql://user:password@ep-sample-pooler.aws.neon.tech/mydb?sslmode=require
SECRET_KEY=your_secure_random_session_key
```
*(Note: If `BACKBOARD_API_KEY` is not provided, HealthTuner automatically operates using its built-in heuristics intelligence engine without crashing.)*

### 3. Start the Web Application
Run using Uvicorn:
```bash
python main.py
```
Or with auto-reload:
```bash
uvicorn main:app --reload --port 8000
```

Open your browser at **[http://localhost:8000](http://localhost:8000)**.
