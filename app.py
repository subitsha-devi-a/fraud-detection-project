from flask import Flask, render_template, request, jsonify, redirect, url_for
import time
import csv
import os

app = Flask(__name__)

# Store user behavior
user_data = {}

DATA_FILE = "data.csv"

# Create CSV if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ip", "click_time", "time_diff", "click_count", "is_fraud", "reason"])


# 🔐 LOGIN PAGE
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
    total = 0
    fraud = 0
    genuine = 0

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                total += 1
                if row["is_fraud"] == "1":
                    fraud += 1
                else:
                    genuine += 1

    return render_template("dashboard.html",
                           total=total,
                           fraud=fraud,
                           genuine=genuine)


# 👤 USER PAGE
@app.route('/user')
def user():
    return render_template("user.html")


# 🔥 CLICK LOGIC (MAIN PART)
@app.route('/click', methods=['POST'])
def click():

    current_time = time.time()

    # ✅ FIX: REAL USER IP (IMPORTANT FOR RENDER)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Debug (optional)
    print("USER IP:", ip)

    if ip not in user_data:
        user_data[ip] = {
            "last_click": 0,
            "count": 0
        }

    last_time = user_data[ip]["last_click"]
    time_diff = current_time - last_time

    # 🎯 FRAUD LOGIC
    if time_diff < 3:
        is_fraud = 1
        reason = "Too fast clicking (bot behavior)"
    elif user_data[ip]["count"] >= 1:
        is_fraud = 1
        reason = "Repeated click from same IP"
    else:
        is_fraud = 0
        reason = "Genuine user"

    # Update data
    user_data[ip]["last_click"] = current_time
    user_data[ip]["count"] += 1

    # Save to CSV
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ip, current_time, round(time_diff, 2),
                         user_data[ip]["count"], is_fraud, reason])

    return jsonify({
        "fraud": is_fraud,
        "reason": reason,
        "ip": ip
    })


# RUN
if __name__ == "__main__":
    app.run(debug=True)
