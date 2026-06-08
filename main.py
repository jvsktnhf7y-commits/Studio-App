from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime
import hashlib
import json

app = FastAPI(title="Studio App")

# Create static directory
os.makedirs("static", exist_ok=True)

# CSS
css_content = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; margin: 0; }
.container { max-width: 1200px; margin: 0 auto; }
.card { background: white; border-radius: 24px; padding: 30px; margin-bottom: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
h1 { font-size: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 10px 0; }
.btn { display: inline-block; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: 600; background: #667eea; color: white; margin: 5px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
table { width: 100%; border-collapse: collapse; }
th { background: #667eea; color: white; padding: 12px; text-align: left; }
td { padding: 12px; border-bottom: 1px solid #eee; }
input, select { width: 100%; padding: 10px; margin: 5px 0; border: 2px solid #e5e7eb; border-radius: 8px; }
"""

with open("static/style.css", "w") as f:
    f.write(css_content)

# File paths
LEDGER_FILE = "studio_ledger.csv"
PROFILES_FILE = "student_profiles.csv"
PRICING_FILE = "pricing_tiers.csv"
DEFAULT_RATE = 50.00

# Password file
PASSWORD_FILE = "admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

def get_all_profiles():
    profiles = {}
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("Name", "").strip()
                if name:
                    profiles[name] = {
                        "tier_name": row.get("TierName", ""),
                        "rate": float(row.get("Rate", DEFAULT_RATE)),
                        "target_minutes": int(row.get("TargetMinutes", 60)),
                        "credits": int(row.get("Credits", 0)),
                        "description": row.get("Description", ""),
                        "prepaid": float(row.get("Prepaid", 0))
                    }
    return profiles

def save_all_profiles(profiles_map):
    with open(PROFILES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "TierName", "Rate", "TargetMinutes", "Credits", "Description", "Prepaid"])
        for name, data in profiles_map.items():
            writer.writerow([name, data.get('tier_name', ''), data.get('rate', DEFAULT_RATE), data.get('target_minutes', 60), data.get('credits', 0), data.get('description', ''), data.get('prepaid', 0)])

def get_pricing_tiers():
    tiers = {}
    if os.path.exists(PRICING_FILE):
        with open(PRICING_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tier = row.get("TierName", "").strip()
                if tier:
                    tiers[tier] = {
                        "rate": float(row.get("HourlyRate", DEFAULT_RATE)),
                        "minutes": int(row.get("TargetMinutes", 60))
                    }
    return tiers

def save_pricing_tiers(tiers_map):
    with open(PRICING_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["TierName", "HourlyRate", "TargetMinutes"])
        for name, data in tiers_map.items():
            writer.writerow([name, data['rate'], data['minutes']])

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Studio Dashboard</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container">
            <div class="card" style="text-align: center;">
                <h1>🎵 Studio Console</h1>
                <p>Welcome to your music studio management system</p>
            </div>
            <div class="grid">
                <a href="/students" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">👥</div>
                    <h3>Students</h3>
                </a>
                <a href="/rates" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">💰</div>
                    <h3>Rates</h3>
                </a>
                <a href="/payments" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">💵</div>
                    <h3>Payments</h3>
                </a>
                <a href="/schedule" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">📅</div>
                    <h3>Schedule</h3>
                </a>
                <a href="/logout" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">🚪</div>
                    <h3>Logout</h3>
                </a>
            </div>
        </div>
    </body>
    </html>
    """)

# Login
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = ""):
    error_html = f'<div style="background:#fee;color:#c33;padding:10px;border-radius:8px;">{error}</div>' if error else ''
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Login</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container" style="max-width:400px;">
            <div class="card">
                <h1>🎵 Studio Login</h1>
                {error_html}
                <form action="/login" method="post">
                    <input type="text" name="username" placeholder="Username" required>
                    <input type="password" name="password" placeholder="Password" required>
                    <button type="submit" class="btn" style="width:100%;">Login</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == "admin":
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        with open(PASSWORD_FILE, 'r') as f:
            data = json.load(f)
            if input_hash == data.get("password_hash", ""):
                response = RedirectResponse(url="/dashboard", status_code=303)
                response.set_cookie(key="session", value="authenticated", httponly=True, max_age=86400)
                return response
    return RedirectResponse(url="/login?error=Invalid credentials", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)

# Auth middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ["/login", "/logout", "/static", "/"]:
        return await call_next(request)
    session = request.cookies.get("session")
    if session == "authenticated":
        return await call_next(request)
    return RedirectResponse(url="/login", status_code=303)

# Students page
@app.get("/students", response_class=HTMLResponse)
def students_page():
    profiles = get_all_profiles()
    rows = ""
    for name, data in profiles.items():
        rows += f"<tr><td><strong>{name}</strong></td><td>${data['rate']}/hr</td><td>{data['credits']}</td><td>{data['description']}</td></tr>"
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Students</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container"><div class="card"><h1>👥 Students</h1>{'<table><thead><tr><th>Name</th><th>Rate</th><th>Credits</th><th>Focus</th></tr></thead><tbody>' + rows if rows else '<p>No students yet</p>' + '</tbody></table>'}</div>
        <div class="card"><h2>➕ Add Student</h2><form action="/add-profile" method="post"><input type="text" name="name" placeholder="Student Name" required><input type="text" name="rate_tier_name" placeholder="Pricing Tier" value="Standard"><input type="text" name="description" placeholder="Focus/Instrument"><button type="submit" class="btn">Create Profile</button></form></div>
        <a href="/dashboard" class="btn">← Back</a></div>
    </body>
    </html>
    """)

@app.post("/add-profile")
def add_profile(name: str = Form(...), rate_tier_name: str = Form(...), description: str = Form(...)):
    profiles = get_all_profiles()
    profiles[name] = {"tier_name": rate_tier_name, "rate": DEFAULT_RATE, "target_minutes": 60, "credits": 0, "description": description, "prepaid": 0}
    save_all_profiles(profiles)
    return RedirectResponse(url="/students", status_code=303)

@app.get("/rates", response_class=HTMLResponse)
def rates_page():
    tiers = get_pricing_tiers()
    rows = ""
    for name, data in tiers.items():
        rows += f"<tr><td><strong>{name}</strong></td><td>${data['rate']}/hr</td><td>{data['minutes']} min</td></tr>"
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Rates</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container"><div class="card"><h1>💰 Pricing Tiers</h1>{'<table><thead><tr><th>Tier</th><th>Rate</th><th>Duration</th></tr></thead><tbody>' + rows if rows else '<p>No tiers yet</p>' + '</tbody></table>'}</div>
        <div class="card"><h2>➕ Add Pricing Tier</h2><form action="/save-pricing-tier" method="post"><input type="text" name="tier_name" placeholder="Tier Name" required><input type="number" step="0.01" name="hourly_rate" placeholder="Hourly Rate" required><input type="number" name="target_minutes" placeholder="Minutes" value="60"><button type="submit" class="btn">Create Tier</button></form></div>
        <a href="/dashboard" class="btn">← Back</a></div>
    </body>
    </html>
    """)

@app.post("/save-pricing-tier")
def save_pricing_tier(tier_name: str = Form(...), hourly_rate: float = Form(...), target_minutes: int = Form(60)):
    tiers = get_pricing_tiers()
    tiers[tier_name] = {"rate": hourly_rate, "minutes": target_minutes}
    save_pricing_tiers(tiers)
    return RedirectResponse(url="/rates", status_code=303)

@app.get("/schedule", response_class=HTMLResponse)
def schedule_page():
    students = get_all_profiles()
    options = ""
    for name in students.keys():
        options += f'<option value="{name}">{name}</option>'
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Schedule</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container"><div class="card"><h1>📅 Schedule Lesson</h1><form action="/create-lesson" method="post"><select name="student_name" required><option value="">Select Student</option>{options}</select><input type="date" name="date" required><input type="time" name="time" required><select name="duration"><option value="30">30 min</option><option value="60" selected>60 min</option><option value="90">90 min</option></select><button type="submit" class="btn">Create Lesson</button></form></div>
        <a href="/dashboard" class="btn">← Back</a></div>
    </body>
    </html>
    """)

@app.post("/create-lesson")
def create_lesson(student_name: str = Form(...), date: str = Form(...), time: str = Form(...), duration: int = Form(60)):
    return HTMLResponse(f"""<!DOCTYPE html><html><head><title>Lesson Created</title><link rel="stylesheet" href="/static/style.css"></head><body><div class="container"><div class="card" style="text-align:center;"><h1>✅ Lesson Created!</h1><p><strong>{student_name}</strong> on {date} at {time} for {duration} minutes</p><a href="/schedule" class="btn">Schedule Another</a><a href="/dashboard" class="btn">Dashboard</a></div></div></body></html>""")

@app.get("/payments", response_class=HTMLResponse)
def payments_page():
    profiles = get_all_profiles()
    student_options = ""
    for name in profiles.keys():
        student_options += f'<option value="{name}">{name}</option>'
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Record Payment</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container">
            <div class="card">
                <h1>💰 Record Payment</h1>
                <form action="/record-payment" method="post">
                    <select name="student_name" required><option value="">Select Student</option>{student_options}</select>
                    <input type="number" step="0.01" name="amount" placeholder="Amount ($)" required>
                    <input type="date" name="payment_date" required>
                    <select name="payment_method"><option value="Cash">Cash</option><option value="Check">Check</option><option value="Venmo">Venmo</option><option value="Zelle">Zelle</option></select>
                    <input type="text" name="notes" placeholder="Notes (optional)">
                    <button type="submit" class="btn">Record Payment</button>
                </form>
            </div>
            <a href="/dashboard" class="btn">← Back</a>
        </div>
    </body>
    </html>
    """)

@app.post("/record-payment")
def record_payment(student_name: str = Form(...), amount: float = Form(...), payment_date: str = Form(...), payment_method: str = Form(...), notes: str = Form("")):
    profiles = get_all_profiles()
    if student_name in profiles:
        current_prepaid = profiles[student_name].get('prepaid', 0)
        profiles[student_name]['prepaid'] = current_prepaid + amount
        save_all_profiles(profiles)
    return RedirectResponse(url="/payments", status_code=303)

@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
