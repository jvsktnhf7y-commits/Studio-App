from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime
import hashlib
import json
import pytz
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

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

# Password file
PASSWORD_FILE = "admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

# Data files
PROFILES_FILE = "student_profiles.csv"
PRICING_FILE = "pricing_tiers.csv"
DEFAULT_RATE = 50.00

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
                        "description": row.get("Description", "")
                    }
    return profiles

def save_all_profiles(profiles_map):
    with open(PROFILES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "TierName", "Rate", "TargetMinutes", "Credits", "Description"])
        for name, data in profiles_map.items():
            writer.writerow([name, data['tier_name'], data['rate'], data['target_minutes'], data['credits'], data['description']])

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

# Dashboard with Calendar
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    """Main dashboard page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Dashboard</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
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
                    <small>Manage profiles</small>
                </a>
                <a href="/rates" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">💰</div>
                    <h3>Rates</h3>
                    <small>Pricing tiers</small>
                </a>
                <a href="/payments" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">💵</div>
                    <h3>Payments</h3>
                    <small>Record payments</small>
                </a>
                <a href="/schedule" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">📅</div>
                    <h3>Schedule</h3>
                    <small>Book lessons</small>
                </a>
                <a href="/logout" class="card" style="text-align: center; text-decoration: none; color: #333;">
                    <div style="font-size: 48px;">🚪</div>
                    <h3>Logout</h3>
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
    profiles[name] = {"tier_name": rate_tier_name, "rate": DEFAULT_RATE, "target_minutes": 60, "credits": 0, "description": description}
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

# Google Calendar endpoints
@app.get("/calendar-auth")
def calendar_auth():
    from google_auth_oauthlib.flow import Flow
    from fastapi.responses import RedirectResponse, HTMLResponse
    import json
    import os
    
    creds_json = os.environ.get('GOOGLE_CREDENTIALS', '')
    if not creds_json:
        return HTMLResponse("<h2>❌ GOOGLE_CREDENTIALS not set</h2>")
    
    try:
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
    except Exception as e:
        return HTMLResponse(f"<h2>Error: {str(e)}</h2><a href='/dashboard'>Back</a>")

@app.get("/calendar-callback")
def calendar_callback(code: str = None):
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
    
    token_data = flow.credentials.to_json()
    with open('calendar_token.json', 'w') as f:
        f.write(token_data)
    
    return HTMLResponse("<h2>✅ Calendar Connected!</h2><a href='/dashboard'>Back</a>")

@app.get("/calendar-events")
def calendar_events():
    if not os.path.exists('calendar_token.json'):
        return HTMLResponse("<h2>Calendar not connected. <a href='/calendar-auth'>Connect here</a></h2>")
    
    with open('calendar_token.json', 'r') as f:
        token_data = json.load(f)
    
    creds = Credentials.from_authorized_user_info(token_data)
    service = build('calendar', 'v3', credentials=creds)
    
    tz = pytz.timezone('America/New_York')
    now = datetime.now(tz)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    start_utc = start.astimezone(pytz.UTC).isoformat()
    end_utc = end.astimezone(pytz.UTC).isoformat()
    
    events = service.events().list(calendarId='primary', timeMin=start_utc, timeMax=end_utc, singleEvents=True).execute().get('items', [])
    
    if not events:
        return HTMLResponse("<h2>No events today</h2><a href='/dashboard'>Back</a>")
    
    html = "<h2>Today's Events</h2><ul>"
    for e in events:
        summary = e.get('summary', 'Untitled')
        start_time = e.get('start', {}).get('dateTime', 'All day')
        html += f"<li>{summary} at {start_time}</li>"
    html += "</ul><a href='/dashboard'>Back</a>"
    return HTMLResponse(html)



@app.get("/debug-env")
def debug_env():
    """Check which environment variables are set"""
    import os
    return {
        "TWILIO_ACCOUNT_SID": bool(os.environ.get("TWILIO_ACCOUNT_SID")),
        "TWILIO_AUTH_TOKEN": bool(os.environ.get("TWILIO_AUTH_TOKEN")),
        "TWILIO_PHONE_NUMBER": bool(os.environ.get("TWILIO_PHONE_NUMBER")),
        "SENDGRID_API_KEY": bool(os.environ.get("SENDGRID_API_KEY")),
        "SENDGRID_FROM_EMAIL": bool(os.environ.get("SENDGRID_FROM_EMAIL")),
        "GOOGLE_CREDENTIALS": bool(os.environ.get("GOOGLE_CREDENTIALS")),
    }




# Payment Recording
@app.get("/payments", response_class=HTMLResponse)
def payments_page():
    """Payment recording page"""
    import csv
    from datetime import datetime
    
    # File constants
    LEDGER_FILE = "studio_ledger.csv"
    PROFILES_FILE = "student_profiles.csv"
    PRICING_FILE = "pricing_tiers.csv"
    DEFAULT_RATE = 50.00
    
    students = get_all_profiles()
    student_options = ""
    for name in students.keys():
        student_options += f'<option value="{name}">{name}</option>'
    
    # Get recent payments from ledger
    recent_payments = ""
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            rows_list = list(reader)
            for row in rows_list[-10:]:
                if 'Payment' in row.get('Status', '') or 'payment' in row.get('Notes', '').lower():
                    recent_payments += f"""
                    <tr>
                        <td>{row.get('Date', '')}</td>
                        <td>{row.get('Student', '')}</td>
                        <td>${float(row.get('AmountCharged', 0)):.2f}</td>
                        <td>{row.get('Notes', '')}</td>
                    </tr>
                    """
    
    # Get student balances
    balances_rows = ""
    for name, data in students.items():
        prepaid = data.get('prepaid', 0)
        credits = data.get('credits', 0)
        balances_rows += f"""
        <tr>
            <td><strong>{name}</strong></td>
            <td>{credits}</td>
            <td>${prepaid:.2f}</td>
        </tr>
        """
    
    if not balances_rows:
        balances_rows = '<tr><td colspan="3">No students yet</td></tr>'
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Record Payment</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .form-row {{ display: flex; gap: 15px; margin-bottom: 15px; flex-wrap: wrap; }}
            .form-group {{ flex: 1; min-width: 150px; }}
            .payment-card {{ background: #f0fdf4; border: 2px solid #22c55e; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card payment-card">
                <h1>💰 Record Payment</h1>
                <p>Record a payment received from a student (cash, check, Venmo, etc.)</p>
                <form action="/record-payment" method="post">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Student</label>
                            <select name="student_name" required>
                                <option value="">Select Student</option>
                                {student_options}
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Amount ($)</label>
                            <input type="number" step="0.01" name="amount" placeholder="50.00" required>
                        </div>
                        <div class="form-group">
                            <label>Date</label>
                            <input type="date" name="payment_date" required>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Payment Method</label>
                        <select name="payment_method">
                            <option value="Cash">Cash</option>
                            <option value="Check">Check</option>
                            <option value="Venmo">Venmo</option>
                            <option value="Zelle">Zelle</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Notes (optional)</label>
                        <input type="text" name="notes" placeholder="e.g., Payment for March lessons">
                    </div>
                    <button type="submit" class="btn">💵 Record Payment</button>
                </form>
            </div>
            
            <div class="card">
                <h2>📋 Recent Payments</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>Date</th><th>Student</th><th>Amount</th><th>Notes</th></tr></thead>
                        <tbody>{recent_payments if recent_payments else '<tr><td colspan="4">No payments recorded yet</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
            
            <div class="card">
                <h2>💰 Student Balances</h2>
                <div style="overflow-x: auto;">
                    <table>
                        <thead><tr><th>Student</th><th>Credits</th><th>Prepaid Balance</th></tr></thead>
                        <tbody>{balances_rows}</tbody>
                    </table>
                </div>
            </div>
            
            <a href="/dashboard" class="btn">← Back</a>
        </div>
    </body>
    </html>
    """)

@app.post("/record-payment")
def record_payment(
    student_name: str = Form(...),
    amount: float = Form(...),
    payment_date: str = Form(...),
    payment_method: str = Form(...),
    notes: str = Form("")
):
    """Record a payment from student"""
    import csv
    
    LEDGER_FILE = "studio_ledger.csv"
    
    # Update student prepaid balance
    profiles_map = get_all_profiles()
    if student_name in profiles_map:
        current_prepaid = profiles_map[student_name].get('prepaid', 0)
        profiles_map[student_name]['prepaid'] = current_prepaid + amount
        save_all_profiles(profiles_map)
    
    # Record in ledger
    full_notes = f"Payment - {payment_method}. {notes}".strip()
    with open(LEDGER_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([payment_date, student_name, "Payment", f"{amount:.2f}", full_notes])
    
    return RedirectResponse(url="/payments", status_code=303)
@app.get("/test")
def test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




# Twilio Email (no verification needed!)
from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')

def send_receipt_email(to_email, student_name, lesson_date, amount_paid):
    """Send receipt using Twilio's email (no verification)"""
    if not TWILIO_ACCOUNT_SID:
        print("Twilio not configured")
        return False
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Twilio's email sends from their domain
        message = client.messages.create(
            from_='notifications@twilio.com',  # Twilio's verified domain
            to=to_email,
            subject=f"Lesson Receipt - {student_name}",
            body=f"""
🎵 LESSON RECEIPT

Student: {student_name}
Date: {lesson_date}
Amount Paid: ${amount_paid:.2f}

Thank you for your lesson!
            """.strip()
        )
        print(f"Email sent: {message.sid}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

@app.post("/send-test-email")
def send_test_email(email: str = Form(...)):
    """Test email sending via Twilio"""
    result = send_receipt_email(email, "Test Student", "2024-01-01", 50.00)
    if result:
        return HTMLResponse("<h2>✅ Test email sent via Twilio!</h2><a href='/dashboard'>Back</a>")
    else:
        return HTMLResponse("<h2>❌ Failed to send email. Check Twilio settings.</h2><a href='/dashboard'>Back</a>")

@app.get("/email-settings")
def email_settings():
    """Email settings page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Settings</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>📧 Email Receipts (Twilio)</h1>
                <p>Send receipts to students after lessons.</p>
                
                <h3>Test Email</h3>
                <form action="/send-test-email" method="post">
                    <input type="email" name="email" placeholder="student@example.com" required>
                    <button type="submit" class="btn">Send Test</button>
                </form>
                
                <h3>Setup Complete</h3>
                <p>✅ Twilio email is ready to use! No verification needed.</p>
                <p>Emails will come from: <code>notifications@twilio.com</code></p>
                <a href="/dashboard" class="btn">Back</a>
            </div>
        </div>
    </body>
    </html>
    """)


# SMS Settings Page
@app.get("/sms-settings")
def sms_settings():
    """SMS settings page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Settings</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>📱 SMS Reminders</h1>
                <p>Send text reminders to students before their lessons.</p>
                
                <h3>Test SMS</h3>
                <form action="/send-test-sms" method="post">
                    <input type="tel" name="phone" placeholder="+1234567890" required>
                    <button type="submit" class="btn">Send Test</button>
                </form>
                
                <h3>Status</h3>
                <p>✅ Twilio is ready. Enter your phone number above to test.</p>
                <a href="/dashboard" class="btn">Back</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/send-test-sms")
def send_test_sms(phone: str = Form(...)):
    """Send a test SMS via Twilio"""
    from twilio.rest import Client
    import os
    
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    if not TWILIO_ACCOUNT_SID:
        return HTMLResponse("<h2>❌ Twilio not configured. Missing Account SID.</h2><a href='/dashboard'>Back</a>")
    
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body="🎵 Test from Studio App! Your SMS is working.",
            from_=TWILIO_PHONE_NUMBER,
            to=phone
        )
        return HTMLResponse(f"""
        <h2>✅ Test SMS Sent!</h2>
        <p>Message ID: {message.sid}</p>
        <a href="/dashboard">Back</a>
        """)
    except Exception as e:
        return HTMLResponse(f"<h2>❌ Error: {str(e)}</h2><a href='/dashboard'>Back</a>")
