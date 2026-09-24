import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.config import settings
from backend.schemas import ContactForm, ContactResponse, MessageRecord
from backend.db import init_db, save_message, get_all_messages, hash_ip, check_rate_limit

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BACKEND_DIR / "data"
IMAGES_DIR = FRONTEND_DIR / "assets" / "images"

# Ensure database is initialized
init_db(settings.DB_PATH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database
    init_db(settings.DB_PATH)
    yield

app = FastAPI(
    title="Najeeb Ullah Portfolio API",
    description="Official portfolio website backend for Najeeb Ullah",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

def load_json_file(file_path: Path):
    if not file_path.exists():
        raise HTTPException(status_code=500, detail=f"Data file {file_path.name} not found.")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_image_assets_info() -> Dict[str, Any]:
    """Inspects frontend/assets/images for existing photos."""
    has_profile_photo = False
    profile_photo_url = None
    gallery_images = []
    
    if IMAGES_DIR.exists():
        # Check profile photo
        for ext in [".jpg", ".jpeg", ".png", ".webp"]:
            candidate = IMAGES_DIR / f"profile{ext}"
            if candidate.exists():
                has_profile_photo = True
                profile_photo_url = f"/assets/images/{candidate.name}"
                break
                
        # Check gallery images (gallery-1.jpg, gallery-2.jpg, etc.)
        for file in sorted(IMAGES_DIR.iterdir()):
            if file.is_file() and file.stem.lower().startswith("gallery-") and file.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                gallery_images.append({
                    "filename": file.name,
                    "url": f"/assets/images/{file.name}",
                    "alt": f"Gallery Photo {file.stem.replace('gallery-', '')}"
                })
                
    return {
        "has_profile_photo": has_profile_photo,
        "profile_photo_url": profile_photo_url,
        "gallery_images": gallery_images
    }

# ----------------- API ROUTES ----------------- #

@app.get("/api/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/profile")
async def get_profile():
    profile_data = load_json_file(DATA_DIR / "profile.json")
    image_info = get_image_assets_info()
    profile_data["images"] = image_info
    return profile_data

@app.get("/api/projects")
async def get_projects():
    return load_json_file(DATA_DIR / "projects.json")

@app.get("/api/projects/{slug}")
async def get_project(slug: str):
    projects = load_json_file(DATA_DIR / "projects.json")
    for proj in projects:
        if proj.get("slug") == slug:
            return proj
    raise HTTPException(status_code=404, detail="Project not found")

@app.post("/api/contact", response_model=ContactResponse)
async def submit_contact(form: ContactForm, request: Request):
    # 1. Honeypot check: reject spam silently
    if form.website:
        return ContactResponse(status="ok", message="Your message has been sent successfully.")

    # 2. Extract and hash IP
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        client_ip = request.client.host
    else:
        client_ip = "127.0.0.1"
    
    ip_hashed = hash_ip(client_ip)

    # 3. Rate limiting (max 5 per hour per IP)
    if not check_rate_limit(ip_hashed):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before sending another message."
        )

    # 4. Save to SQLite database
    save_message(
        db_path=settings.DB_PATH,
        name=form.name.strip(),
        email=str(form.email).strip(),
        subject=form.subject.strip(),
        message=form.message.strip(),
        ip_hash=ip_hashed
    )

    # 5. Optional SMTP notification (non-blocking failure)
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASS:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.SMTP_TO
            msg["Subject"] = f"Portfolio Contact: {form.subject.strip()} from {form.name.strip()}"
            
            body = (
                f"New contact form submission from portfolio:\n\n"
                f"Name: {form.name.strip()}\n"
                f"Email: {form.email}\n"
                f"Subject: {form.subject.strip()}\n\n"
                f"Message:\n{form.message.strip()}\n"
            )
            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=5) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
        except Exception as e:
            # SMTP failure must never break the user request
            print(f"[Warning] Failed to send email alert: {e}")

    return ContactResponse(status="ok", message="Your message has been sent successfully.")

@app.get("/api/admin/messages")
async def get_admin_messages(x_admin_token: Optional[str] = Header(None, alias="X-Admin-Token")):
    if not settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin interface disabled: ADMIN_TOKEN not configured."
        )
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token."
        )
    return get_all_messages(settings.DB_PATH)

# ----------------- STATIC MOUNT & ROOT ----------------- #

# Mount static folders
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

@app.get("/favicon.svg")
async def get_favicon():
    favicon_path = FRONTEND_DIR / "assets" / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404, detail="Favicon not found")

@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="index.html not found")
