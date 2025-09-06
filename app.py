# app.py
from flask import Flask, render_template_string, request, redirect, session, url_for
import random
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# إعداد قاعدة البيانات
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            balance INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# HTML Template أساسي
template = '''
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>OoNoo Bet</title>
<style>
body { font-family: Arial; background:#111; color:#fff; text-align:center; }
input { padding:5px; margin:5px; }
button { padding:5px 10px; margin:5px; }
.container { max-width:500px; margin:auto; padding:20px; background:#222; border-radius:10px; margin-top:50px;}
.balance { font-weight:bold; margin:10px 0; }
.result { margin:10px 0; color:#0f0; font-weight:bold;}
</style>
</head>
<body>
<div class="container">
<h1>OoNoo Bet</h1>

{% if not session.get('username') %}
<h3>تسجيل / دخول</h3>
<form method="post" action="/login">
<input type="text" name="username" placeholder="اسم المستخدم" required><br>
<input type="password" name="password" placeholder="كلمة المرور" required><br>
<button type="submit">دخول</button>
</form>
<form method="post" action="/register">
<input type="text" name="username" placeholder="اسم المستخدم" required><br>
<input type="password" name="password" placeholder="كلمة المرور" required><br>
<button type="submit">تسجيل</button>
</form>
{% else %}
<p>مرحبا {{ session['username'] }} | <a href="/logout" style="color:#f00;">تسجيل خروج</a></p>
<p class="balance">رصيدك الحالي: {{ balance }} نقطة</p>

<h3>الرهان</h3>
<form method="post" action="/bet">
اختر رقم بين 1 و 10: <input type="number" name="number" min="1" max="10" required><br>
المبلغ: <input type="number" name="amount" min="1" max="{{ balance }}" required><br>
<button type="submit">راهن</button>
</form>

{% if result %}
<p class="result">{{ result }}</p>
{% endif %}
{% endif %}
</div>
</body>
</html>
'''

# دوال قاعدة البيانات
def get_user(username):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

def update_balance(username, new_balance):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("UPDATE users SET balance=? WHERE username=?", (new_balance, username))
    conn.commit()
    conn.close()

# الصفحات
@app.route('/', methods=['GET'])
def index():
    if session.get('username'):
        user = get_user(session['username'])
        return render_template_string(template, session=session, balance=user[3], result=None)
    return render_template_string(template, session=session)

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    if get_user(username):
        return "اسم المستخدم موجود بالفعل. <a href='/'>عودة</a>"
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username, password, balance) VALUES (?, ?, ?)", (username, password, 1000))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = get_user(username)
    if user and user[2] == password:
        session['username'] = username
        return redirect(url_for('index'))
    return "بيانات غير صحيحة. <a href='/'>عودة</a>"

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/bet', methods=['POST'])
def bet():
    if not session.get('username'):
        return redirect(url_for('index'))
    number = int(request.form['number'])
    amount = int(request.form['amount'])
    user = get_user(session['username'])
    balance = user[3]
    if amount > balance:
        return "الرصيد غير كافي. <a href='/'>عودة</a>"
    winning_number = random.randint(1, 10)
    if number == winning_number:
        balance += amount * 2
        result = f"مبروك! الرقم الصحيح {winning_number}. ربحت {amount*2} نقطة."
    else:
        balance -= amount
        result = f"للأسف! الرقم الصحيح {winning_number}. خسرت {amount} نقطة."
    update_balance(session['username'], balance)
    return render_template_string(template, session=session, balance=balance, result=result)

if __name__ == '__main__':
    app.run(debug=True)
