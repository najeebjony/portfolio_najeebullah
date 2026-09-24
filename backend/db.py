import sqlite3
import hashlib
import time
from typing import List, Dict, Any, Optional
from collections import defaultdict

# In-memory rate limiter: ip_hash -> list of submission timestamps
_rate_limits: Dict[str, List[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 3600  # 1 hour
MAX_SUBMISSIONS_PER_HOUR = 5

def hash_ip(ip: str) -> str:
    """Hashes IP address using SHA-256 for privacy."""
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()

def check_rate_limit(ip_hash: str) -> bool:
    """Returns True if request is allowed, False if limit exceeded."""
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    # Filter timestamps to within the 1-hour window
    _rate_limits[ip_hash] = [t for t in _rate_limits[ip_hash] if t > cutoff]
    if len(_rate_limits[ip_hash]) >= MAX_SUBMISSIONS_PER_HOUR:
        return False
    _rate_limits[ip_hash].append(now)
    return True

def init_db(db_path: str = "messages.db"):
    """Initializes SQLite database and tables with WAL mode for concurrency."""
    conn = sqlite3.connect(db_path, timeout=20.0)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_hash TEXT NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()

def save_message(db_path: str, name: str, email: str, subject: str, message: str, ip_hash: str) -> int:
    """Saves a message to the database and returns the generated row id."""
    conn = sqlite3.connect(db_path, timeout=20.0)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (name, email, subject, message, ip_hash)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email, subject, message, ip_hash))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_all_messages(db_path: str) -> List[Dict[str, Any]]:
    """Retrieves all stored messages ordered by creation date descending."""
    conn = sqlite3.connect(db_path, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, subject, message, created_at, ip_hash FROM messages ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
