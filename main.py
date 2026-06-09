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
os.makedirs("/data", exist_ok=True)
os.makedirs("/data", exist_ok=True)

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
LEDGER_FILE = "/data/studio_ledger.csv"
PROFILES_FILE = "/data/student_profiles.csv"
PRICING_FILE = "/data/pricing_tiers.csv"
DEFAULT_RATE = 50.00

# Password file
PASSWORD_FILE = "/data/admin_password.json"
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
    # Fetch calendar events
    calendar_html = ""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        import json
        from datetime import datetime
        import pytz
        import os
        
        token_path = "/data/calendar_token.json"
        if os.path.exists(token_path):
            with open(token_path, 'r') as f:
                token_data = json.load(f)
            creds = Credentials.from_authorized_user_info(token_data)
            service = build('calendar', 'v3', credentials=creds)
            
            tz = pytz.timezone('America/New_York')
            now = datetime.now(tz)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=0)
            
            start_utc = start.astimezone(pytz.UTC).isoformat()
            end_utc = end.astimezone(pytz.UTC).isoformat()
            
            events = service.events().list(
                calendarId='primary',
                timeMin=start_utc,
                timeMax=end_utc,
                singleEvents=True
            ).execute().get('items', [])
            
            if events:
                calendar_html = '<div class="card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"><h2>📅 Today\'s Lessons</h2><ul style="list-style: none; padding: 0;">'
                for e in events:
                    summary = e.get('summary', 'Lesson')
                    start_time = e.get('start', {}).get('dateTime', 'All day')
                    if start_time and 'T' in start_time:
                        start_time = start_time.split('T')[1][:5]
                    # Add action buttons for each lesson
                    calendar_html += f'''
                    <li style="padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <span>🎵 <strong>{summary}</strong> at {start_time}</span>
                            <div style="display: flex; gap: 8px; margin-top: 8px;">
                                <form action="/log-attendance" method="post" style="display: inline;">
                                    <input type="hidden" name="student_name" value="{summary}">
                                    <input type="hidden" name="status" value="Confirmed">
                                    <button type="submit" style="background: #22c55e; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">✅ Confirm</button>
                                </form>
                                <form action="/log-attendance" method="post" style="display: inline;">
                                    <input type="hidden" name="student_name" value="{summary}">
                                    <input type="hidden" name="status" value="Missed">
                                    <button type="submit" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">❌ Missed</button>
                                </form>
                                <form action="/log-attendance" method="post" style="display: inline;">
                                    <input type="hidden" name="student_name" value="{summary}">
                                    <input type="hidden" name="status" value="Cancelled">
                                    <button type="submit" style="background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">🔄 Cancelled</button>
                                </form>
                            </div>
                        </div>
                    </li>'''
                calendar_html += '</ul></div>'
            else:
                calendar_html = '<div class="card"><h2>📅 Today\'s Lessons</h2><p>No lessons scheduled for today.</p><a href="/schedule" class="btn">Schedule a Lesson</a></div>'
    except Exception as e:
        calendar_html = '<div class="card"><h2>📅 Calendar</h2><p><a href="/calendar-auth">Connect Google Calendar</a> to see your lessons.</p></div>'
    
    # Get student stats
    profiles = get_all_profiles()
    student_stats = ""
    for name, data in profiles.items():
        prepaid = data.get('prepaid', 0)
        # Calculate lessons paid for (assuming $50 per lesson, adjust as needed)
        lessons_paid = int(prepaid / 50) if prepaid > 0 else 0
        
        # Get attendance stats from ledger
        attended = 0
        missed = 0
        cancelled = 0
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Student', '') == name:
                        status = row.get('Status', '')
                        if status == 'Confirmed':
                            attended += 1
                        elif status == 'Missed':
                            missed += 1
                        elif status == 'Cancelled':
                            cancelled += 1
        
        student_stats += f"""
        <div class="student-card">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                <h3 style="margin: 0;">👤 {name}</h3>
                <div style="display: flex; gap: 8px;">
                    <span class="stat-badge" style="background: #d1fae5; color: #065f46;">✅ {attended}</span>
                    <span class="stat-badge" style="background: #fee2e2; color: #991b1b;">❌ {missed}</span>
                    <span class="stat-badge" style="background: #fef3c7; color: #92400e;">🔄 {cancelled}</span>
                </div>
            </div>
            <div style="margin-top: 12px;">
                <span class="stat-badge" style="background: #e0e7ff; color: #4338ca;">💰 ${prepaid:.2f} prepaid</span>
                <span class="stat-badge" style="background: #d1fae5; color: #065f46;">📚 {lessons_paid} lessons paid</span>
            </div>
        </div>
        """
    
    if not student_stats:
        student_stats = '<p style="text-align: center;">No students yet. <a href="/students">Add your first student</a></p>'
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Dashboard</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .nav-card {{
                background: white;
                border-radius: 16px;
                padding: 25px 15px;
                text-align: center;
                text-decoration: none;
                color: #333;
                transition: all 0.3s;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }}
            .nav-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .nav-emoji {{
                font-size: 48px;
                display: block;
                margin-bottom: 12px;
            }}
            .nav-title {{
                font-size: 18px;
                font-weight: 600;
            }}
            .student-card {{
                background: white;
                border-radius: 16px;
                padding: 18px;
                margin-bottom: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                transition: transform 0.2s;
            }}
            .student-card:hover {{
                transform: translateX(5px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }}
            .stat-badge {{
                display: inline-block;
                padding: 4px 10px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                margin: 2px;
            }}
            .stats-section {{
                background: white;
                border-radius: 20px;
                padding: 20px;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card" style="text-align: center;">
                <h1>🎵 Studio Console</h1>
                <p>Welcome to your music studio management system</p>
            </div>
            
            {calendar_html}
            
            <div class="stats-section">
                <h2>📊 Student Stats</h2>
                {student_stats}
            </div>
            
            <div class="dashboard-grid">
                <a href="/students" class="nav-card">
                    <span class="nav-emoji">👥</span>
                    <div class="nav-title">Students</div>
                    <small>Manage profiles</small>
                </a>
                <a href="/rates" class="nav-card">
                    <span class="nav-emoji">💰</span>
                    <div class="nav-title">Rates</div>
                    <small>Pricing tiers</small>
                </a>
                <a href="/payments" class="nav-card">
                    <span class="nav-emoji">💵</span>
                    <div class="nav-title">Payments</div>
                    <small>Record payments</small>
                </a>
                <a href="/schedule" class="nav-card">
                    <span class="nav-emoji">📅</span>
                    <div class="nav-title">Schedule</div>
                    <small>Book lessons</small>
                </a>
                <a href="/revenue" class="nav-card">
                    <span class="nav-emoji">📊</span>
                    <div class="nav-title">Revenue</div>
                    <small>View earnings</small>
                </a>
                <a href="/logout" class="nav-card">
                    <span class="nav-emoji">🚪</span>
                    <div class="nav-title">Logout</div>
                    <small>End session</small>
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

@app.post("/log-attendance")
def log_attendance(student_name: str = Form(...), status: str = Form(...)):
    """Log attendance (Confirmed, Missed, Cancelled)"""
    today = datetime.now().strftime("%Y-%m-%d")

    # Check if this lesson was already logged today to avoid duplicates
    already_logged = False
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Date') == today and row.get('Student') == student_name:
                    already_logged = True
                    break

    if not already_logged:
        with open(LEDGER_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([today, student_name, status, "0.00", f"Attendance: {status}"])

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/test")
def test():
    return {"status": "ok"}
@app.get("/revenue")
def revenue_page():
    """Display total revenue page"""
    total = calculate_total_revenue()
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Revenue Report</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card" style="text-align: center;">
                <h1>💰 Total Revenue</h1>
                <p style="font-size: 48px; color: #22c55e; font-weight: bold;">${total:.2f}</p>
                <p>From all recorded payments</p>
                <a href="/dashboard" class="btn">← Back to Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
# function to calculate total revenue from all payments
def calculate_total_revenue():
    total_revenue = 0
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                amount = float(row.get("Amount", 0))
                total_revenue += amount
    return total_revenue

# function to calculate total payments for a student
def calculate_student_payments(student_name: str):
    total_payments = 0
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("Student Name", "").strip() == student_name.strip():
                    amount = float(row.get("Amount", 0))
                    total_payments += amount
    return total_payments

# Add this to your main.py (before the last if __name__ line)

# Google Calendar endpoints
@app.get("/calendar-auth")
def calendar_auth():
    """Start Google Calendar authorization"""
    from google_auth_oauthlib.flow import Flow
    from fastapi.responses import RedirectResponse
    import json
    import os
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    if not creds_json:
        return HTMLResponse("<h2>❌ GOOGLE_CREDENTIALS not set</h2>")
    
    client_config = json.loads(creds_json)
    if 'web' not in client_config:
        client_config = {"web": client_config}
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar.readonly'],
        redirect_uri='https://studio-app-7y7z.onrender.com/calendar-callback'
    )
    
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    return RedirectResponse(auth_url)

@app.get("/calendar-callback")
def calendar_callback(code: str = None):
    """Handle Google OAuth callback"""
    from google_auth_oauthlib.flow import Flow
    from fastapi.responses import HTMLResponse
    import json
    import os
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    client_config = json.loads(creds_json)
    if 'web' not in client_config:
        client_config = {"web": client_config}
    
    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar.readonly'],
        redirect_uri='https://studio-app-7y7z.onrender.com/calendar-callback'
    )
    
    flow.fetch_token(code=code)
    
    # Save token
    token_data = flow.credentials.to_json()
    with open('/data/calendar_token.json', 'w') as f:
        f.write(token_data)
    
    return HTMLResponse("<h2>✅ Calendar Connected!</h2><a href='/dashboard'>Back</a>")

@app.get("/calendar-events")
def calendar_events():
    """Show today's calendar events"""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import json
    from datetime import datetime
    import pytz
    import os
    
    token_path = '/data/calendar_token.json'
    if not os.path.exists(token_path):
        return HTMLResponse("<h2>Calendar not connected. <a href='/calendar-auth'>Connect here</a></h2>")
    
    with open(token_path, 'r') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data)
    service = build('calendar', 'v3', credentials=creds)
    
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    start_utc = start.astimezone(pytz.UTC).isoformat()
    end_utc = end.astimezone(pytz.UTC).isoformat()
    
    events = service.events().list(
        calendarId='primary',
        timeMin=start_utc,
        timeMax=end_utc,
        singleEvents=True
    ).execute().get('items', [])
    
    if not events:
        return HTMLResponse("<h2>No events today</h2><a href='/dashboard'>Back</a>")
    
    html = "<h2>Today's Events</h2><ul>"
    for e in events:
        summary = e.get('summary', 'Untitled')
        start_time = e.get('start', {}).get('dateTime', 'All day')
        html += f"<li>{summary} at {start_time}</li>"
    html += "</ul><a href='/dashboard'>Back</a>"
    return HTMLResponse(html)

@app.get("/debug-calendar")
def debug_calendar():
    """Debug calendar connection"""
    import os
    from google.oauth2.credentials import Credentials
    import json

    result = {
        "token_exists": os.path.exists("/data/calendar_token.json"),
        "token_size": 0,
        "has_creds": bool(os.environ.get('GOOGLE_CREDENTIALS')),
        "events_found": 0
    }

    if result["token_exists"]:
        result["token_size"] = os.path.getsize("/data/calendar_token.json")

    # Try to fetch events
    try:
        with open("/data/calendar_token.json", 'r') as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)
        from googleapiclient.discovery import build
        service = build('calendar', 'v3', credentials=creds)
        
        from datetime import datetime
        import pytz
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0)
        end = now.replace(hour=23, minute=59, second=59)
        
        start_utc = start.astimezone(pytz.UTC).isoformat()
        end_utc = end.astimezone(pytz.UTC).isoformat()
        
        events = service.events().list(
            calendarId='primary',
            timeMin=start_utc,
            timeMax=end_utc,
            singleEvents=True
        ).execute()
        
        result["events_found"] = len(events.get('items', []))
        result["first_event"] = events.get('items', [])[0].get('summary') if events.get('items') else None
    except Exception as e:
        result["error"] = str(e)
    
    return result
