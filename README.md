# Najeeb Ullah — Official Portfolio Website

Official, production-ready personal portfolio website for **Najeeb Ullah** — Machine Learning Engineer & Residential Building Manager based in Karachi, Pakistan.

---

## 1. Tech Stack

- **Backend:** Python 3.11+, **FastAPI** + Uvicorn, Pydantic v2, SQLite (`sqlite3` built-in), Pillow.
- **Frontend:** Plain **HTML5 + Modern CSS + Vanilla JavaScript** (zero build step, zero npm dependencies), served directly by FastAPI.
- **Database:** Local SQLite (`messages.db`) storing contact inquiries with SHA-256 hashed IP addresses and rate limiting.

---

## 2. Directory Structure

```
portfolio_najeebullah/
├── .venv/                 # Python virtual environment
├── backend/
│   ├── main.py            # FastAPI app, API routes, static mounts
│   ├── config.py          # Environment settings (Pydantic Settings)
│   ├── schemas.py         # Pydantic validation models
│   ├── db.py              # SQLite storage & in-memory rate limiting
│   ├── optimize_images.py # Non-destructive Pillow image optimizer
│   └── data/
│       ├── profile.json   # Single source of truth: personal profile
│       └── projects.json  # Single source of truth: 3 ML projects
├── frontend/
│   ├── index.html         # Semantic, accessible HTML5 single-page
│   ├── css/
│   │   └── styles.css     # CSS custom properties, light/dark themes
│   ├── js/
│   │   └── app.js         # Vanilla JS: dynamic fetch, accordion, lightbox, form
│   └── assets/
│       ├── favicon.svg    # NU monogram vector icon
│       └── images/        # Place profile.jpg and gallery-*.jpg here
├── requirements.txt       # Pinned backend dependencies
├── .env.example           # Example environment variables
├── .gitignore             # Git ignore configuration
└── README.md              # Documentation, setup, and deployment guide
```

---

## 3. Local Setup & Running

### Step 1: Clone or Navigate to the Workspace
```bash
cd /d/portfolio_najeebullah
```

### Step 2: Initialize Virtual Environment & Install Dependencies
```bash
# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows Command Prompt:
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install pinned dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
*(Optional)* Adjust port, CORS origins, or set `ADMIN_TOKEN` and SMTP credentials.

### Step 4: Run the Application
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Open your browser at: **[http://localhost:8000](http://localhost:8000)**

---

## 4. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves the single-page frontend (`frontend/index.html`) |
| `GET` | `/api/health` | Healthcheck returning `{"status": "ok"}` |
| `GET` | `/api/profile` | Personal profile data & image availability status |
| `GET` | `/api/projects` | All verified machine learning projects |
| `GET` | `/api/projects/{slug}` | Detailed data for a single project |
| `POST`| `/api/contact` | Submits contact message (rate-limited, validated, honeypot protected) |
| `GET` | `/api/admin/messages`| Protected admin endpoint (requires `X-Admin-Token` header) |

---

## 5. Adding & Optimizing Photos

1. Place your headshot in `frontend/assets/images/profile.jpg`.
2. *(Optional)* Place additional gallery photos in `frontend/assets/images/` named:
   - `gallery-1.jpg`
   - `gallery-2.jpg`
   - `gallery-3.jpg` (any number)
3. Run the non-destructive image optimizer:
   ```bash
   python backend/optimize_images.py
   ```
   *Note: If no profile picture is placed, the website cleanly falls back to a circular monogram avatar "NU". If no gallery photos exist, the Gallery section remains completely hidden.*

---

## 6. Updating Projects

All project information is centralized in **`backend/data/projects.json`**.
To edit or update project information:
1. Open `backend/data/projects.json`.
2. Modify or add entries adhering to the JSON schema.
3. Refresh the website — updates render dynamically without rebuilding or restarting.

---

## 7. Deployment Guide (Render)

Deploy this application seamlessly to [Render](https://render.com) using their Web Service:

1. **Push your code to GitHub / GitLab**.
2. **Log into Render Dashboard** and click **New +** -> **Web Service**.
3. **Connect your repository**.
4. Configure the Web Service:
   - **Name:** `najeebullah-portfolio` (or preferred name)
   - **Environment:** `Python 3`
   - **Region:** Frankfurt (EU Central) or Oregon (US West)
   - **Branch:** `main`
   - **Build Command:**
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command:**
     ```bash
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
5. **Environment Variables**:
   Under the "Environment" tab on Render, add:
   - `PYTHON_VERSION`: `3.11.9` (or `3.12.2`)
   - `ADMIN_TOKEN`: `your-secure-secret-token` (optional, for viewing messages)
   - `ALLOWED_ORIGINS`: `*`
6. Click **Deploy Web Service**. Render will provision, install requirements, and deploy the application live.
