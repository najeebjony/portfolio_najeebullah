import sys
import os
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.main import app, settings
import sqlite3

def run_tests():
    client = TestClient(app)
    print("--- Starting Automated Portfolio Tests ---")

    # 1. Test GET /
    print("\n1. Testing GET /")
    res = client.get("/")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "Najeeb Ullah" in res.text, "Index should contain Najeeb Ullah"
    print("PASS: Root endpoint serves index.html")

    # 2. Test GET /favicon.svg
    print("\n2. Testing GET /favicon.svg")
    res = client.get("/favicon.svg")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert "svg" in res.headers["content-type"], "Favicon should be svg"
    print("PASS: Favicon served correctly")

    # 3. Test Static CSS & JS
    print("\n3. Testing Static Assets")
    res_css = client.get("/css/styles.css")
    assert res_css.status_code == 200, f"Expected 200 for styles.css, got {res_css.status_code}"
    res_js = client.get("/js/app.js")
    assert res_js.status_code == 200, f"Expected 200 for app.js, got {res_js.status_code}"
    print("PASS: Static CSS and JS accessible")

    # 4. Test GET /api/health
    print("\n4. Testing GET /api/health")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res.json() == {"status": "ok"}, f"Unexpected health response: {res.json()}"
    print("PASS: Health check returns status: ok")

    # 5. Test GET /api/profile
    print("\n5. Testing GET /api/profile")
    res = client.get("/api/profile")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["name"] == "Najeeb Ullah", "Name mismatch"
    assert data["location"] == "Karachi, Pakistan", "Location mismatch"
    assert data["github"] is None, "GitHub must be null"
    assert "images" in data, "Images info must be included"
    print("PASS: Profile data matches specification")

    # 6. Test GET /api/projects
    print("\n6. Testing GET /api/projects")
    res = client.get("/api/projects")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    projects = res.json()
    assert len(projects) == 3, f"Expected exactly 3 projects, got {len(projects)}"
    slugs = [p["slug"] for p in projects]
    assert "cardioguard-heart-disease" in slugs
    assert "diabetes-risk-prediction" in slugs
    assert "breast-cancer-survival-prognosis" in slugs
    print(f"PASS: 3 verified projects returned ({', '.join(slugs)})")

    # Verify Project 1 Metrics (CardioGuard)
    p1 = next(p for p in projects if p["slug"] == "cardioguard-heart-disease")
    assert p1["metrics"]["accuracy"] == "91.80%"
    assert p1["metrics"]["recall"] == "96.43%"
    assert p1["champion_model"] == "Random Forest"
    assert p1["cross_validation"] == "5-fold CV accuracy 80.55% (± 2.66%)"
    assert p1["live_url"] == "https://heart-diseases-prediction84.streamlit.app/"

    # Verify Project 2 Metrics (Diabetes)
    p2 = next(p for p in projects if p["slug"] == "diabetes-risk-prediction")
    assert p2["metrics"]["accuracy"] == "79%"
    assert p2["metrics"]["f1"] == "0.486"
    assert p2["live_url"] is None

    # Verify Project 3 Metrics (Breast Cancer)
    p3 = next(p for p in projects if p["slug"] == "breast-cancer-survival-prognosis")
    assert p3["metrics"]["accuracy"] == "77.89%"
    assert p3["champion_model"] == "XGBoost"
    assert p3["live_url"] == "https://breast-cancerproject.streamlit.app"
    print("PASS: All project metrics match Section 4 exactly")

    # 7. Test GET /api/projects/{slug}
    print("\n7. Testing GET /api/projects/{slug}")
    res = client.get("/api/projects/cardioguard-heart-disease")
    assert res.status_code == 200
    assert res.json()["slug"] == "cardioguard-heart-disease"

    res_404 = client.get("/api/projects/non-existent-project")
    assert res_404.status_code == 404
    print("PASS: Single project retrieval and 404 handling verified")

    # 8. Test POST /api/contact validation
    print("\n8. Testing POST /api/contact validation")
    
    # 8a: Missing required fields
    res = client.post("/api/contact", json={})
    assert res.status_code == 422, f"Expected 422 for empty body, got {res.status_code}"

    # 8b: Invalid email
    res = client.post("/api/contact", json={
        "name": "Test User",
        "email": "not-an-email",
        "subject": "Inquiry",
        "message": "This is a valid length test message."
    })
    assert res.status_code == 422, f"Expected 422 for invalid email, got {res.status_code}"

    # 8c: Short message (< 10 chars)
    res = client.post("/api/contact", json={
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Inquiry",
        "message": "Too short"
    })
    assert res.status_code == 422, f"Expected 422 for short message, got {res.status_code}"

    # 8d: Honeypot check (filled 'website' field should return 200 without saving)
    res = client.post("/api/contact", json={
        "name": "Spam Bot",
        "email": "spambot@example.com",
        "subject": "Buy crypto",
        "message": "Spam message that should be ignored by honeypot.",
        "website": "http://spam.example.com"
    }, headers={"X-Forwarded-For": "192.168.1.50"})
    assert res.status_code == 200, f"Expected 200 for honeypot, got {res.status_code}"
    assert res.json()["status"] == "ok"

    # Verify honeypot did NOT save to database
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM messages WHERE name = 'Spam Bot'")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 0, "Spam bot submission was saved to database!"
    print("PASS: Honeypot silently dropped spam message")

    # 8e: Valid message submission
    res = client.post("/api/contact", json={
        "name": "Dr. Sarah Khan",
        "email": "sarah.khan@example.com",
        "subject": "Collaboration Inquiry",
        "message": "Hello Najeeb, I am interested in collaborating on machine learning healthcare applications."
    }, headers={"X-Forwarded-For": "10.0.0.1"})
    assert res.status_code == 200, f"Expected 200 for valid contact, got {res.status_code}"
    assert res.json()["status"] == "ok"

    # Verify saved in SQLite
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, subject, ip_hash FROM messages WHERE email = 'sarah.khan@example.com'")
    row = cursor.fetchone()
    conn.close()
    assert row is not None, "Message not found in database!"
    assert row[0] == "Dr. Sarah Khan"
    assert row[1] == "sarah.khan@example.com"
    assert len(row[3]) == 64, "IP should be hashed with SHA-256 (64 hex characters)"
    print("PASS: Valid contact stored with SHA-256 hashed IP")

    # 8f: Rate limiting check (max 5 per hour per IP)
    test_ip = "192.168.100.99"
    for i in range(4):
        r = client.post("/api/contact", json={
            "name": f"Rate Tester {i}",
            "email": f"tester{i}@example.com",
            "subject": f"Test {i}",
            "message": "Valid test message for rate limit check."
        }, headers={"X-Forwarded-For": test_ip})
        assert r.status_code == 200

    # 5th submission from this IP (total 5)
    r5 = client.post("/api/contact", json={
        "name": "Rate Tester 5",
        "email": "tester5@example.com",
        "subject": "Test 5",
        "message": "Valid test message for rate limit check."
    }, headers={"X-Forwarded-For": test_ip})
    assert r5.status_code == 200

    # 6th submission should be 429 Too Many Requests
    r6 = client.post("/api/contact", json={
        "name": "Rate Tester 6",
        "email": "tester6@example.com",
        "subject": "Test 6",
        "message": "This should be blocked by rate limit."
    }, headers={"X-Forwarded-For": test_ip})
    assert r6.status_code == 429, f"Expected 429 Too Many Requests, got {r6.status_code}"
    print("PASS: In-memory rate limiting blocks after 5 requests per IP per hour")

    # 9. Test GET /api/admin/messages
    print("\n9. Testing GET /api/admin/messages")
    # Without ADMIN_TOKEN configured in settings
    settings.ADMIN_TOKEN = None
    res = client.get("/api/admin/messages")
    assert res.status_code == 403, f"Expected 403 when ADMIN_TOKEN is not set, got {res.status_code}"

    # With ADMIN_TOKEN configured, but wrong header
    settings.ADMIN_TOKEN = "supersecrettoken123"
    res = client.get("/api/admin/messages", headers={"X-Admin-Token": "wrongtoken"})
    assert res.status_code == 401, f"Expected 401 with wrong token, got {res.status_code}"

    # With correct header
    res = client.get("/api/admin/messages", headers={"X-Admin-Token": "supersecrettoken123"})
    assert res.status_code == 200, f"Expected 200 with valid token, got {res.status_code}"
    messages = res.json()
    assert isinstance(messages, list)
    assert len(messages) > 0
    print("PASS: Admin messages endpoint security verified")

    print("\nALL AUTOMATED TESTS PASSED SUCCESSFULLY! ZERO ERRORS.")

if __name__ == "__main__":
    run_tests()
