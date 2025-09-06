from flask import Flask, request, session, redirect
import random

app = Flask(__name__)
app.secret_key = "supersecretkey"

# قاعدة بيانات مؤقتة داخل الكود (بدل users.json)
users = {}

# الصفحة الرئيسية / تسجيل الدخول
@app.route("/", methods=["GET", "POST"])
def home():
    if "username" in session:
        return redirect("/dashboard")
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username]["password"] == password:
            session["username"] = username
            return redirect("/dashboard")
        return "<h3>اسم المستخدم أو كلمة المرور خطأ</h3><a href='/'>عودة</a>"
    return '''
    <h2>تسجيل الدخول</h2>
    <form method="post">
        اسم المستخدم: <input name="username"><br>
        كلمة المرور: <input name="password" type="password"><br>
        <button type="submit">دخول</button>
    </form>
    <p>ليس لديك حساب؟ <a href="/register">سجل الآن</a></p>
    '''

# تسجيل حساب جديد
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            return "<h3>اسم المستخدم موجود مسبقاً</h3><a href='/register'>عودة</a>"
        users[username] = {"password": password, "balance": 1000, "history": []}
        return "<h3>تم التسجيل بنجاح!</h3><a href='/'>تسجيل الدخول</a>"
    return '''
    <h2>تسجيل حساب جديد</h2>
    <form method="post">
        اسم المستخدم: <input name="username"><br>
        كلمة المرور: <input name="password" type="password"><br>
        <button type="submit">سجل</button>
    </form>
    <p>لديك حساب؟ <a href="/">تسجيل الدخول</a></p>
    '''

# لوحة التحكم
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/")
    user = users[session["username"]]
    history_html = "<ul>" + "".join(f"<li>{h}</li>" for h in user["history"]) + "</ul>"
    return f'''
    <h2>مرحبا {session["username"]}</h2>
    <p>رصيدك: {user["balance"]} نقطة</p>
    <a href="/bet">المراهنة</a><br>
    <a href="/logout">تسجيل الخروج</a>
    <h3>سجل المراهنات</h3>
    {history_html}
    '''

# صفحة المراهنة
@app.route("/bet", methods=["GET", "POST"])
def bet():
    if "username" not in session:
        return redirect("/")
    user = users[session["username"]]
    result = ""
    if request.method == "POST":
        amount = int(request.form["amount"])
        choice = int(request.form["choice"])
        if amount > user["balance"]:
            result = "الرصيد غير كافي"
        else:
            win_number = random.randint(1, 10)
            if choice == win_number:
                user["balance"] += amount
                result = f"مبروك! الرقم الصحيح {win_number}. ربحك: {amount}"
            else:
                user["balance"] -= amount
                result = f"خسرت! الرقم الصحيح {win_number}. خسارتك: {amount}"
            user["history"].append(result)
    return f'''
    <h2>المراهنة</h2>
    <p>رصيدك الحالي: {user["balance"]} نقطة</p>
    <form method="post">
        المبلغ: <input name="amount" type="number" min="1" max="{user["balance"]}" required><br>
        اختر رقم من 1 إلى 10: <input name="choice" type="number" min="1" max="10" required><br>
        <button type="submit">راهن</button>
    </form>
    <p>{result}</p>
    <a href="/dashboard">العودة للوحة التحكم</a>
    '''

# تسجيل الخروج
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
