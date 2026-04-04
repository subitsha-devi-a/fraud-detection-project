from flask import Flask, render_template, request, jsonify, redirect
import time
import csv
import os

app = Flask(__name__)

user_data = {}
DATA_FILE = "data.csv"

# Create CSV if not exists
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ip", "click_time", "click_count", "is_fraud", "reason"])


# LOGIN
@app.route('/')
def home():
    return redirect('/login')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return redirect('/dashboard')
    return render_template('login.html')


# DASHBOARD
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


# USER PAGE
@app.route('/user')
def user():
    return render_template("user.html")


# CLICK LOGIC
@app.route('/click', methods=['POST'])
def click():

    current_time = time.time()

    # ✅ FIXED REAL IP
    raw_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip = raw_ip.split(',')[0].strip()

    print("USER IP:", ip)

    # 🎯 FRAUD LOGIC (FINAL)
    if ip not in user_data:
        user_data[ip] = 1
        is_fraud = 0
        reason = "Genuine user (first click)"
    else:
        user_data[ip] += 1
        is_fraud = 1
        reason = "Repeated click from same IP"

    # Save to CSV
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([ip, current_time, user_data[ip], is_fraud, reason])

    return jsonify({
        "fraud": is_fraud,
        "reason": reason,
        "ip": ip
    })


# RUN
if __name__ == "__main__":
    app.run(debug=True)
