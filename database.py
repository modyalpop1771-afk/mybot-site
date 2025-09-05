# database.py
import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import datetime

DB_PATH = Path("points.db")

def init_db():
    with closing(sqlite3.connect(DB_PATH)) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0,
            created_at TEXT
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            bet INTEGER,
            started_at REAL,      -- timestamp (seconds)
            crash_point REAL,     -- where it will crash (hidden from client)
            cashed_out REAL,      -- multiplier at cashout (NULL if not)
            crashed INTEGER,      -- 0/1
            finished INTEGER,     -- 0/1
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS point_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount INTEGER,
            status TEXT,          -- pending/approved/rejected
            created_at TEXT
        )""")

def connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def ensure_user(conn, user_id:int, username:str):
    with conn:
        cur = conn.execute("SELECT id FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (id, username, balance, created_at) VALUES (?, ?, ?, ?)",
                (user_id, username or "", 0, datetime.utcnow().isoformat())
            )

def get_balance(conn, user_id:int) -> int:
    cur = conn.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0

def add_points(conn, user_id:int, delta:int):
    with conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE id=?", (delta, user_id,))

def create_point_request(conn, user_id:int, amount:int):
    with conn:
        conn.execute(
            "INSERT INTO point_requests (user_id, amount, status, created_at) VALUES (?, ?, 'pending', ?)",
            (user_id, amount, datetime.utcnow().isoformat())
        )

def approve_point_request(conn, request_id:int):
    with conn:
        cur = conn.execute("SELECT user_id, amount FROM point_requests WHERE id=? AND status='pending'", (request_id,))
        row = cur.fetchone()
        if row:
            uid, amt = row
            conn.execute("UPDATE point_requests SET status='approved' WHERE id=?", (request_id,))
            add_points(conn, uid, amt)
            return True
    return False

def leaderboard(conn, limit:int=20):
    cur = conn.execute("SELECT username, balance FROM users ORDER BY balance DESC LIMIT ?", (limit,))
    return [{"username": r[0] or f"User", "balance": r[1]} for r in cur.fetchall()]
