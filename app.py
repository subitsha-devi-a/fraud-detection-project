from flask import Flask, render_template, request, jsonify, redirect
import time
import sqlite3
import os
import pickle

app = Flask(__name__)

# 🔥 LOAD ML MODEL
if os.path.exists("model.pkl"):
    model = pickle.load(open("model.pkl", "rb"))
else:
    model = None

# 🔥 INIT DATABASE
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            time REAL,
            time_diff REAL,
            click_count INTEGER,
            is_fraud INTEGER,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 🔥 STORE SESSION DATA
user_data = {}


# 🔐 LOGIN
@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect('/dashboard')
    return render_template('login.html')


# 📊 DASHBOARD
@app.route('/dashboard')
def dashboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    rows = c.execute("SELECT is_fraud, reason FROM clicks").fetchall()
    conn.close()

    total = len(rows)
    fraud = sum(1 for r in rows if r[0] == 1)
    genuine = total - fraud

    reason_count = {}
    for r in rows:
        if r[0] == 1:
            reason = r[1]
            reason_count[reason] = reason_count.get(reason, 0) + 1

    return render_template("dashboard.html",
                           total=total,
                           fraud=fraud,
                           genuine=genuine,
                           reasons=reason_count)


# 👤 USER PAGE
@app.route('/user')
def user():
    return render_template("user.html")


# 🔥 CLICK LOGIC (FINAL HYBRID)
@app.route('/click', methods=['POST'])
def click():

    current_time = time.time()

    # ✅ REAL IP
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip = raw_ip.split(',')[0].strip()

    print("USER IP:", ip)

    if ip not in user_data:
        user_data[ip] = {
            "last_click": 0,
            "count": 0
        }

    last_click = user_data[ip]["last_click"]
    time_diff = current_time - last_click if last_click != 0 else 999

    user_data[ip]["count"] += 1

    # 🎯 HYBRID LOGIC

    # Rule-based (PRIMARY)
    if last_click != 0 and time_diff < 3:
        is_fraud = 1
        reason = "Too fast click (bot)"

    elif user_data[ip]["count"] == 1:
        is_fraud = 0
        reason = "Genuine (first click)"

    else:
        is_fraud = 1
        reason = "Repeated click"

    # ML validation (SECONDARY)
    if model:
        features = [[round(time_diff, 2), user_data[ip]["count"]]]
        ml_pred = model.predict(features)[0]
        reason += " + ML checked"

    # UPDATE
    user_data[ip]["last_click"] = current_time

    # 💾 SAVE TO DATABASE
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''
        INSERT INTO clicks (ip, time, time_diff, click_count, is_fraud, reason)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ip, current_time, round(time_diff, 2), user_data[ip]["count"], is_fraud, reason))

    conn.commit()
    conn.close()

    return jsonify({
        "fraud": is_fraud,
        "reason": reason,
        "ip": ip
    })


if __name__ == "__main__":
    app.run(debug=True)
