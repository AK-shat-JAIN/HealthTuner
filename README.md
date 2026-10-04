# HealthTuner 🌿

**HealthTuner** is a clean, modern, production-ready Health Companion Web Application built with **FastAPI**, **SQLite**, **SQLAlchemy**, **Jinja2**, and **Tailwind CSS**, integrated with **Backboard.io** for intelligent LLM health summaries.

---

## 🚀 Features

- 🔐 **Authentication & Onboarding**:
  - Secure bcrypt password hashing.
  - Auto-login upon registration and seamless session handling.
- 📅 **Interactive Monthly Calendar Dashboard**:
  - Date access control: Active past/present days, visually locked future dates.
  - Workload badges (`Easy`, `Medium`, `Maximum`).
- ⚡ **Dynamic Workload Logging Modal**:
  - **Easy:** 1 open quick-log textarea.
  - **Medium:** 3 targeted inputs (Activity, Nutrition/Hydration, Energy).
  - **Maximum:** 5 structured inputs (Training, Macros, Sleep/Recovery, Stress, Key Wins).
- 🧠 **AI Health Intelligence & Timeline (Backboard.io)**:
  - Custom date range or 1-click Full Month AI analysis.
  - 2-Part structured output: Behavioral Performance Summary + Actionable Recommendations & Deload/Goal advice.
  - Historical AI timeline with instant deletion/review options.
- 🌓 **Full Light/Dark Mode**:
  - Smooth theme switcher persisted via `localStorage` with zero theme flash.

---

## 🛠️ Project Structure

```
HealthTuner/
├── main.py              # Server routing, auth endpoints, calendar & AI APIs
├── database.py          # SQLAlchemy engine & session configuration
├── models.py            # User, DailyLog, and AISummary ORM models
├── auth.py              # Password hashing & verification with bcrypt
├── ai_service.py        # Backboard.io LLM client & structured prompt pipeline
├── requirements.txt     # Python package dependencies
├── .env.example         # Environment template
├── .env                 # Local configuration & Backboard API Key
├── templates/
│   ├── base.html        # Main layout with Tailwind CDN, Lucide icons & Dark Mode
│   ├── login.html       # Clean login screen
│   ├── register.html    # Registration screen
│   ├── dashboard.html   # Monthly calendar grid & dynamic modal logger
│   └── timeline.html    # AI Intelligence generator & historical timeline
└── static/
    ├── css/style.css    # Custom styles and glassmorphic touches
    └── js/theme.js      # Global dark/light mode toggle
```

---

## ⚡ Quickstart Guide

### 1. Install Dependencies
Ensure you have Python 3.9+ installed:
```bash
pip install -r requirements.txt
```

### 2. Configure Backboard.io API Key
Edit the `.env` file and set your `BACKBOARD_API_KEY`:
```env
BACKBOARD_API_KEY=your_backboard_io_api_key_here
BACKBOARD_API_URL=https://api.backboard.io/v1/chat/completions
BACKBOARD_MODEL=meta-llama/llama-3-8b-instruct
```
*(Note: If no API key is provided, HealthTuner automatically operates with its built-in heuristics intelligence engine without crashing.)*

### 3. Start the Server
Run using Uvicorn:
```bash
python main.py
```
or:
```bash
uvicorn main:app --reload --port 8000
```

Open your browser at: **[http://localhost:8000](http://localhost:8000)**
