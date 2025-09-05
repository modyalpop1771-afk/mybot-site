from flask import Flask, request, jsonify, render_template_string
import sqlite3, uuid

app = Flask(__name__)
DB = "users.db"

# ======================
# 📌 إنشاء قاعدة البيانات
# ======================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS vouchers (
        code TEXT PRIMARY KEY,
        amount INTEGER,
        used INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        amount INTEGER,
        status TEXT DEFAULT 'pending'
    )""")
    conn.commit()
    conn.close()

init_db()

# ======================
# 📌 HTML كامل (للاعب + الأدمن)
# ======================
INDEX_HTML = """
<!DOCTYPE html>
<html lang="ar">
<head>
  <meta charset="UTF-8">
  <title>OoNoo Bet</title>
  <style>
    body { font-family: Arial; background:#111; color:#fff; text-align:center; }
    .box { margin:20px; padding:20px; background:#222; border-radius:10px; }
    button { padding:10px 20px; margin:5px; cursor:pointer; }
    input { padding:5px; }
  </style>
</head>
<body>
  <h1>OoNoo Bet 🎮</h1>
  <div id="loginBox" class="box">
    <input id="username" placeholder="ادخل اسم المستخدم">
    <button onclick="login()">دخول</button>
  </div>

  <div id="gameBox" class="box" style="display:none;">
    <h2>رصيدك: <span id="balance">0</span> 🪙</h2>
    <div id="crashGame">
      <p>💥 لعبة Crash</p>
      <p id="multiplier">x1.00</p>
      <button id="startCrash">ابدأ</button>
      <button id="cashOut" disabled>سحب</button>
    </div>

    <div id="voucherBox" style="margin-top:20px;">
      <input id="voucherCode" placeholder="كود الشحن">
      <button onclick="redeemVoucher()">شحن</button>
      <div id="voucherMsg"></div>
    </div>

    <div id="requestBox" style="margin-top:20px;">
      <input id="requestAmount" type="number" placeholder="عدد النقاط">
      <button onclick="requestPoints()">💰 طلب نقاط</button>
      <div id="requestMsg"></div>
    </div>

    <button onclick="logout()">🚪 تسجيل خروج</button>
  </div>

  <div id="adminBox" class="box" style="display:none;">
    <h2>لوحة تحكم الأدمن 👑</h2>
    <div id="requestsList">جاري التحميل...</div>
    <button onclick="logout()">🚪 تسجيل خروج</button>
  </div>

<script>
let username = "";
let multiplier = 1.0, crashInterval;

function login(){
  username = document.getElementById("username").value.trim();
  if(!username) return alert("⚠️ اكتب اسم المستخدم");

  document.getElementById("loginBox").style.display = "none";
  if(username === "admin"){
    document.getElementById("adminBox").style.display = "block";
    loadRequests();
  } else {
    document.getElementById("gameBox").style.display = "block";
    getBalance();
  }
}

function logout(){
  username = "";
  document.getElementById("loginBox").style.display = "block";
  document.getElementById("gameBox").style.display = "none";
  document.getElementById("adminBox").style.display = "none";
  document.getElementById("username").value = "";
}

async function getBalance(){
  let res = await fetch("/balance/"+username);
  let data = await res.json();
  document.getElementById("balance").innerText = data.balance;
}

document.getElementById("startCrash").onclick = ()=>{
  multiplier = 1.0;
  document.getElementById("multiplier").innerText = "x1.00";
  document.getElementById("cashOut").disabled = false;

  crashInterval = setInterval(()=>{
    multiplier += 0.1;
    document.getElementById("multiplier").innerText = "x"+multiplier.toFixed(2);

    if(Math.random() < 0.05){
      clearInterval(crashInterval);
      document.getElementById("multiplier").innerText += " 💥 CRASH!";
      document.getElementById("cashOut").disabled = true;
    }
  }, 500);
};

document.getElementById("cashOut").onclick = async ()=>{
  clearInterval(crashInterval);
  document.getElementById("cashOut").disabled = true;

  let reward = Math.floor(multiplier*10);
  let res = await fetch("/add_points", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({username:username, amount:reward})
  });
  let data = await res.json();
  if(data.status==="success") getBalance();
};

// 📌 شحن بالكود
async function redeemVoucher(){
  let code = document.getElementById("voucherCode").value.trim();
  if(!code) return;
  let res = await fetch("/redeem", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({username:username, code:code})
  });
  let data = await res.json();
  document.getElementById("voucherMsg").innerText = data.message;
  getBalance();
}

// 📌 طلب نقاط
async function requestPoints(){
  let amount = document.getElementById("requestAmount").value;
  if(!amount) return;
  let res = await fetch("/request_points", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({username:username, amount:amount})
  });
  let data = await res.json();
  if(data.status==="success"){
    document.getElementById("requestMsg").innerText = "✅ تم إرسال طلبك";
  }
}

// 📌 لوحة تحكم الأدمن
async function loadRequests(){
  let res = await fetch("/admin/requests");
  let data = await res.json();
  let html = "";
  data.forEach(r=>{
    html += `<div>
      ${r.username} طلب ${r.amount} نقطة - [${r.status}]
      <button onclick="handleRequest(${r.id},'accept')">✅</button>
      <button onclick="handleRequest(${r.id},'reject')">❌</button>
    </div>`;
  });
  document.getElementById("requestsList").innerHTML = html;
}

async function handleRequest(id, action){
  let res = await fetch("/admin/handle", {
    method:"POST", headers:{"Content-Type":"application/json"},
    body: JSON.stringify({id:id, action:action})
  });
  let data = await res.json();
  if(data.status==="success") loadRequests();
}
</script>
</body>
</html>
"""

# ======================
# 📌 API Endpoints
# ======================

@app.route("/")
def home():
    return render_template_string(INDEX_HTML)

@app.route("/balance/<username>")
def balance(username):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username,balance) VALUES (?,0)", (username,))
    conn.commit()
    c.execute("SELECT balance FROM users WHERE username=?", (username,))
    bal = c.fetchone()[0]
    conn.close()
    return jsonify({"balance": bal})

@app.route("/add_points", methods=["POST"])
def add_points():
    data = request.json
    username, amount = data["username"], int(data["amount"])
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username,balance) VALUES (?,0)", (username,))
    c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, username))
    conn.commit()
    conn.close()
    return jsonify({"status":"success"})

@app.route("/redeem", methods=["POST"])
def redeem():
    data = request.json
    username, code = data["username"], data["code"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT amount, used FROM vouchers WHERE code=?", (code,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"status":"error","message":"❌ الكود غير صحيح"})
    amount, used = row
    if used:
        conn.close()
        return jsonify({"status":"error","message":"⚠️ الكود مستخدم بالفعل"})

    c.execute("UPDATE vouchers SET used=1 WHERE code=?", (code,))
    c.execute("INSERT OR IGNORE INTO users (username,balance) VALUES (?,0)", (username,))
    c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, username))
    conn.commit()
    conn.close()
    return jsonify({"status":"success","message":"✅ تم إضافة النقاط"})

@app.route("/request_points", methods=["POST"])
def request_points():
    data = request.json
    username, amount = data["username"], int(data["amount"])
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO requests (username,amount,status) VALUES (?,?, 'pending')", (username, amount))
    conn.commit()
    conn.close()
    return jsonify({"status":"success"})

@app.route("/admin/requests")
def admin_requests():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, username, amount, status FROM requests ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id":r[0], "username":r[1], "amount":r[2], "status":r[3]} for r in rows])

@app.route("/admin/handle", methods=["POST"])
def handle_request():
    data = request.json
    req_id, action = data["id"], data["action"]
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT username, amount FROM requests WHERE id=?", (req_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"status":"error","message":"الطلب غير موجود"})
    username, amount = row

    if action=="accept":
        c.execute("INSERT OR IGNORE INTO users (username,balance) VALUES (?,0)", (username,))
        c.execute("UPDATE users SET balance=balance+? WHERE username=?", (amount, username))
        c.execute("UPDATE requests SET status='accepted' WHERE id=?", (req_id,))
    elif action=="reject":
        c.execute("UPDATE requests SET status='rejected' WHERE id=?", (req_id,))

    conn.commit()
    conn.close()
    return jsonify({"status":"success"})

if __name__ == "__main__":
    app.run(debug=True)
