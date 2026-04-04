from flask import Flask, render_template, request, redirect, session
import pandas as pd
import time

app = Flask(__name__)
app.secret_key = "secret"

# Track click count per IP
user_click_count = {}

@app.route('/')
def home():
    return redirect('/login')

# ✅ LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == "admin" and request.form['password'] == "admin":
            session['user'] = "admin"
            return redirect('/dashboard')
        else:
            return "Invalid Login"
    return render_template('login.html')


# ✅ USER PAGE (NO FAKE IP NOW)
@app.route('/user')
def user():
    user_ip = request.remote_addr
    return render_template('user.html', user_ip=user_ip)


# 🔥 CLICK LOGIC (REAL IP BASED)
@app.route('/click', methods=['POST'])
def click():
    watch_time = float(request.form.get("watch_time"))
    ip = request.remote_addr

    result = 0
    reason = "Genuine Click"

    print("\n--- NEW CLICK ---")
    print("User IP:", ip)
    print("Watch Time:", watch_time)

    # 🔴 Rule 1: Too fast
    if watch_time < 2:
        result = 1
        reason = "Clicked too fast"

    # 🔴 Track click count per IP
    if ip not in user_click_count:
        user_click_count[ip] = 1
    else:
        user_click_count[ip] += 1

    # 🔴 Rule 2: Only 1 genuine click per IP
    if user_click_count[ip] > 1:
        result = 1
        reason = "Multiple clicks from same IP"

    print("Result:", "Fraud" if result else "Genuine")

    # 🔥 SAVE DATA
    df = pd.read_csv("data.csv")

    new_row = {
        "ip": ip,
        "click_time": watch_time,
        "device": "desktop",
        "click_count": user_click_count[ip],
        "is_fraud": result,
        "reason": reason
    }

    df = pd.concat([df, pd.DataFrame([new_row])])
    df.to_csv("data.csv", index=False)

    return {"status": "Fraud" if result else "Genuine", "reason": reason}


# 🔒 DASHBOARD (ADMIN ONLY)
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    df = pd.read_csv("data.csv")

    total = len(df)
    fraud = len(df[df['is_fraud'] == 1])
    genuine = len(df[df['is_fraud'] == 0])

    return render_template(
        'dashboard.html',
        total=total,
        fraud=fraud,
        genuine=genuine
    )


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)
