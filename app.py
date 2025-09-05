# app.py
import os, math, time, random
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
from database import init_db, connect, ensure_user, get_balance, add_points, create_point_request, approve_point_request, leaderboard

# الإعداد
init_db()
conn = connect()

app = Flask(__name__)
CORS(app)  # اسمح للواجهة (GitHub Pages) تتواصل مع الـ API

# ثوابت لعبة Crash
TICK_SEC = 0.1            # تحديث كل 0.1 ثانية
GROWTH_PER_SEC = 1.06     # معدل نمو أسي تقريبي
MIN_CRASH = 1.3           # أقل نقطة ممكن ينهار عندها
MAX_CRASH = 10.0          # أعلى نقطة كراش (تقديرية)
HOUSE_EDGE = 0.01         # هامش صغير

def current_multiplier(started_at):
    elapsed = max(0.0, time.time() - started_at)             # ثواني
    # نمو أسي: m = 1.0 * (GROWTH_PER_SEC)^(elapsed)
    m = math.pow(GROWTH_PER_SEC, elapsed)
    return round(m, 2)

def random_crash_point():
    # توزيع عشوائي بسيط مع انحياز للكراش المبكر + Edge
    base = random.uniform(MIN_CRASH, MAX_CRASH)
    return round(max(MIN_CRASH, base * (1 - HOUSE_EDGE)), 2)

def get_round(round_id:int):
    cur = conn.execute("SELECT id, user_id, bet, started_at, crash_point, cashed_out, crashed, finished FROM rounds WHERE id=?", (round_id,))
    r = cur.fetchone()
    if not r: return None
    keys = ["id","user_id","bet","started_at","crash_point","cashed_out","crashed","finished"]
    d = dict(zip(keys, r))
    return d

def finish_round_as_crashed(rnd):
    if rnd["finished"]: return
    with conn:
        conn.execute("UPDATE rounds SET crashed=1, finished=1 WHERE id=?", (rnd["id"],))

@app.post("/api/register")
def api_register():
    data = request.get_json(force=True)
    user_id = int(data.get("user_id"))
    username = data.get("username","")
    ensure_user(conn, user_id, username)
    return jsonify({"ok": True})

@app.get("/api/balance")
def api_balance():
    user_id = int(request.args.get("user_id"))
    bal = get_balance(conn, user_id)
    return jsonify({"balance": bal})

@app.post("/api/request_points")
def api_request_points():
    data = request.get_json(force=True)
    user_id = int(data["user_id"])
    amount = int(data["amount"])
    create_point_request(conn, user_id, amount)
    return jsonify({"ok": True, "message": "تم إرسال طلبك للإدمن"})

# (اختياري) مصادقة بسيطة بالإدمن عبر مفتاح سرّي من .env
ADMIN_KEY = os.environ.get("ADMIN_KEY", "changeme")

@app.post("/api/admin/approve")
def api_admin_approve():
    key = request.headers.get("X-ADMIN-KEY","")
    if key != ADMIN_KEY:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(force
