from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime
import hashlib
import json

import os
import json

# Debug: Check if Google credentials are loaded
print("🔍 Checking Google Calendar setup...")
if os.path.exists('credentials.json'):
    print("✅ credentials.json exists locally")
else:
    print("❌ credentials.json NOT found locally")
    
if os.environ.get('GOOGLE_CREDENTIALS'):
    print("✅ GOOGLE_CREDENTIALS environment variable found")
    # Write it to file
    creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    with open('credentials.json', 'w') as f:
        f.write(creds_json)
    print("✅ Written credentials from environment to file")
else:
    print("❌ GOOGLE_CREDENTIALS environment variable NOT found")


app = FastAPI(title="My Music Studio Automation")

# Create static directory
os.makedirs("static", exist_ok=True)

# Simple CSS file
css_content = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
.container { max-width: 1200px; margin: 0 auto; }
.card { background: white; border-radius: 24px; padding: 30px; margin-bottom: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
.btn { display: inline-block; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: 600; }
.btn-primary { background: #667eea; color: white; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.nav-card { background: white; padding: 30px; border-radius: 20px; text-align: center; text-decoration: none; color: #333; transition: transform 0.2s; display: block; }
.nav-card:hover { transform: translateY(-5px); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
"""

with open("static/style.css", "w") as f:
    f.write(css_content)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Password file
PASSWORD_FILE = "admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

# Data files
LEDGER_FILE = "studio_ledger.csv"
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

# Beautiful DASHBOARD
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Dashboard</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            h1 { font-size: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            .welcome { text-align: center; }
            .nav-emoji { font-size: 48px; display: block; margin-bottom: 15px; }
            .nav-title { font-size: 20px; font-weight: 600; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card welcome">
                <h1>🎵 Studio Console</h1>
                <p>Your complete music studio management system</p>
            </div>
            <div class="grid">
                <a href="/students" class="nav-card"><span class="nav-emoji">👥</span><div class="nav-title">Students</div><small>Manage profiles</small></a>
                <a href="/rates" class="nav-card"><span class="nav-emoji">💰</span><div class="nav-title">Rates</div><small>Pricing tiers</small></a>
                <a href="/schedule" class="nav-card"><span class="nav-emoji">📅</span><div class="nav-title">Schedule</div><small>Book lessons</small></a>
                <a href="/change-password" class="nav-card"><span class="nav-emoji">🔐</span><div class="nav-title">Security</div><small>Change password</small></a>
                <a href="/logout" class="nav-card"><span class="nav-emoji">🚪</span><div class="nav-title">Logout</div><small>End session</small></a>
            </div>
        </div>
    </body>
    </html>
    """)

# BEAUTIFUL STUDENTS PAGE - Green Table Theme
@app.get("/students", response_class=HTMLResponse)
def students_page():
    profiles = get_all_profiles()
    tiers = get_pricing_tiers()
    
    rows = ""
    for name, data in profiles.items():
        rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px;"><strong>{name}</strong></td>
            <td style="padding: 12px;">${data['rate']:.2f}/hr</td>
            <td style="padding: 12px;">{data['credits']} credits</td>
            <td style="padding: 12px;">{data['description']}</td>
            <td style="padding: 12px;">{data['target_minutes']} min</td>
        </tr>
        """
    
    tier_options = ""
    for tier, tdata in tiers.items():
        tier_options += f'<option value="{tier}">{tier} ({tdata["minutes"]} min @ ${tdata["rate"]:.2f}/hr)</option>'
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Students | Studio Console</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #059669 0%, #10b981 100%); min-height: 100vh; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .header {{ background: white; border-radius: 24px; padding: 30px; text-align: center; margin-bottom: 30px; }}
            h1 {{ font-size: 36px; color: #059669; }}
            table {{ width: 100%; background: white; border-radius: 16px; overflow: hidden; }}
            th {{ background: #059669; color: white; padding: 15px; text-align: left; }}
            td {{ padding: 12px; }}
            tr:hover {{ background: #f0fdf4; }}
            .form-card {{ background: white; border-radius: 20px; padding: 25px; margin-top: 30px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; font-weight: 600; }}
            input, select {{ width: 100%; padding: 10px; border: 2px solid #e5e7eb; border-radius: 8px; }}
            button {{ background: #059669; color: white; padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; width: 100%; }}
            .btn-back {{ display: inline-block; background: #6b7280; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>👥 Student Directory</h1>
                <p>Track attendance, credits, and progress</p>
            </div>
            <div style="background: white; border-radius: 16px; overflow: hidden;">
                <table>
                    <thead><tr><th>Name</th><th>Rate</th><th>Credits</th><th>Focus</th><th>Duration</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="5" style="text-align:center">No students yet</td></tr>'}</tbody>
                </table>
            </div>
            <div class="form-card">
                <h2>➕ Add New Student</h2>
                <form action="/add-profile" method="post">
                    <div class="form-group"><label>Name</label><input type="text" name="name" required></div>
                    <div class="form-group"><label>Pricing Tier</label><select name="rate_tier_name">{tier_options}</select></div>
                    <div class="form-group"><label>Focus/Instrument</label><input type="text" name="description" placeholder="e.g., Piano, Voice" required></div>
                    <button type="submit">Create Profile</button>
                </form>
            </div>
            <div style="text-align:center"><a href="/dashboard" class="btn-back">← Back</a></div>
        </div>
    </body>
    </html>
    """)

# Login routes
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = ""):
    error_html = f'<div style="background:#fee;color:#c33;padding:10px;border-radius:8px;margin-bottom:20px">{error}</div>' if error else ''
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Studio Login</title><style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);height:100vh;display:flex;justify-content:center;align-items:center}}
        .login-container{{background:white;padding:40px;border-radius:20px;width:100%;max-width:400px}}
        h1{{text-align:center;margin-bottom:20px}}
        .form-group{{margin-bottom:20px}}
        label{{display:block;margin-bottom:8px;font-weight:600}}
        input{{width:100%;padding:12px;border:2px solid #e5e7eb;border-radius:8px}}
        button{{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:8px;cursor:pointer}}
    </style></head>
    <body><div class="login-container"><h1>🎵 Studio Login</h1>{error_html}<form action="/login" method="post"><div class="form-group"><label>Username</label><input type="text" name="username" required></div><div class="form-group"><label>Password</label><input type="password" name="password" required></div><button type="submit">Login</button></form></div></body></html>
    """)

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    if username == "admin":
        input_hash = hashlib.sha256(password.encode()).hexdigest()
        with open(PASSWORD_FILE, 'r') as f:
            data = json.load(f)
            if input_hash == data.get("password_hash", ""):
                response = RedirectResponse(url="/", status_code=303)
                response.set_cookie(key="studio_session", value="authenticated", httponly=True, max_age=86400)
                return response
    return RedirectResponse(url="/login?error=Invalid credentials", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("studio_session")
    return response

@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)

@app.middleware("http")
async def check_auth(request: Request, call_next):
    if request.url.path in ["/login", "/logout", "/static", "/"]:
        return await call_next(request)
    session = request.cookies.get("studio_session")
    if session == "authenticated":
        return await call_next(request)
    return RedirectResponse(url="/login", status_code=303)

# Add other necessary routes (add-profile, save-pricing-tier, etc.)
@app.post("/add-profile")
def add_profile(name: str = Form(...), rate_tier_name: str = Form(...), description: str = Form(...)):
    tiers = get_pricing_tiers()
    selected = tiers.get(rate_tier_name, {"rate": DEFAULT_RATE, "minutes": 60})
    profiles = get_all_profiles()
    profiles[name] = {"tier_name": rate_tier_name, "rate": selected["rate"], "target_minutes": selected["minutes"], "credits": 0, "description": description}
    with open(PROFILES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "TierName", "Rate", "TargetMinutes", "Credits", "Description"])
        for n, d in profiles.items():
            writer.writerow([n, d['tier_name'], d['rate'], d['target_minutes'], d['credits'], d['description']])
    return RedirectResponse(url="/students", status_code=303)

@app.post("/save-pricing-tier")
def save_tier(tier_name: str = Form(...), hourly_rate: float = Form(...), target_minutes: int = Form(60)):
    tiers = get_pricing_tiers()
    tiers[tier_name] = {"rate": hourly_rate, "minutes": target_minutes}
    with open(PRICING_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["TierName", "HourlyRate", "TargetMinutes"])
        for n, d in tiers.items():
            writer.writerow([n, d['rate'], d['minutes']])
    return RedirectResponse(url="/rates", status_code=303)

@app.get("/rates", response_class=HTMLResponse)
def rates_page():
    tiers = get_pricing_tiers()
    cards = ""
    for name, data in tiers.items():
        cards += f"""
        <div style="background:white;border-radius:16px;padding:25px;text-align:center">
            <h3>{name}</h3>
            <p style="font-size:36px;color:#e94560;margin:15px 0">${data['rate']:.2f}<small>/hr</small></p>
            <p>{data['minutes']} minute lessons</p>
        </div>
        """
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Rates | Studio Console</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#1a1a2e;padding:20px}}
        .container{{max-width:1200px;margin:0 auto}}
        .header{{text-align:center;color:white;margin-bottom:40px}}
        h1{{font-size:48px}}
        .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:25px;margin-bottom:40px}}
        .form-card{{background:white;border-radius:20px;padding:30px}}
        input,select{{width:100%;padding:10px;margin:10px 0;border:2px solid #e5e7eb;border-radius:8px}}
        button{{background:#e94560;color:white;padding:12px;border:none;border-radius:8px;cursor:pointer;width:100%}}
        .btn-back{{display:inline-block;background:#6b7280;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;margin-top:20px}}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>💰 Pricing Plans</h1><p>Choose a pricing structure</p></div>
            <div class="grid">{cards if cards else '<div style="background:white;padding:40px;text-align:center;border-radius:16px">No plans yet</div>'}</div>
            <div class="form-card"><h2>➕ Add New Plan</h2>
            <form action="/save-pricing-tier" method="post">
                <input type="text" name="tier_name" placeholder="Plan Name" required>
                <input type="number" step="0.01" name="hourly_rate" placeholder="Hourly Rate $" required>
                <input type="number" name="target_minutes" placeholder="Minutes" value="60">
                <button type="submit">Create Plan</button>
            </form></div>
            <div style="text-align:center"><a href="/dashboard" class="btn-back">← Back</a></div>
        </div>
    </body>
    </html>
    """)

@app.get("/change-password", response_class=HTMLResponse)
def change_form():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Change Password</title>
    <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
        .card{background:white;border-radius:20px;padding:40px;max-width:400px;width:100%}
        h1{text-align:center;margin-bottom:20px}
        input{width:100%;padding:12px;margin:10px 0;border:2px solid #e5e7eb;border-radius:8px}
        button{width:100%;padding:12px;background:#667eea;color:white;border:none;border-radius:8px;cursor:pointer}
        a{color:#667eea;text-decoration:none}
    </style>
    </head>
    <body>
        <div class="card"><h1>🔐 Change Password</h1>
        <form action="/change-password" method="post">
            <input type="password" name="old_password" placeholder="Current Password" required>
            <input type="password" name="new_password" placeholder="New Password" required>
            <input type="password" name="confirm_password" placeholder="Confirm Password" required>
            <button type="submit">Update Password</button>
        </form>
        <p style="text-align:center;margin-top:20px"><a href="/dashboard">← Back</a></p>
        </div>
    </body>
    </html>
    """)

@app.post("/change-password")
def change_post(old_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    if new_password != confirm_password:
        return RedirectResponse(url="/change-password?error=Passwords don't match", status_code=303)
    with open(PASSWORD_FILE, 'r') as f:
        data = json.load(f)
        old_hash = hashlib.sha256(old_password.encode()).hexdigest()
        if old_hash != data.get("password_hash", ""):
            return RedirectResponse(url="/change-password?error=Wrong password", status_code=303)
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": new_hash}, f)
    return HTMLResponse("<div style='text-align:center;padding:50px'><h2>✅ Password Changed!</h2><a href='/logout'>Log in with new password</a></div>")

@app.get("/schedule", response_class=HTMLResponse)
def schedule_form():
    students = get_all_profiles()
    options = ""
    for name in students.keys():
        options += f'<option value="{name}">{name}</option>'
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head><title>Schedule | Studio Console</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box}}
        body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#3b82f6 0%,#1e40af 100%);min-height:100vh;padding:20px}}
        .container{{max-width:600px;margin:0 auto}}
        .card{{background:white;border-radius:20px;padding:40px}}
        h1{{margin-bottom:20px}}
        input,select{{width:100%;padding:12px;margin:10px 0;border:2px solid #e5e7eb;border-radius:8px}}
        button{{width:100%;padding:12px;background:#3b82f6;color:white;border:none;border-radius:8px;cursor:pointer}}
        .btn-back{{display:inline-block;background:#6b7280;color:white;padding:10px 20px;border-radius:8px;text-decoration:none;margin-top:20px;text-align:center}}
    </style>
    </head>
    <body>
        <div class="container"><div class="card"><h1>📅 Schedule Lesson</h1>
        <form action="/create-lesson" method="post">
            <select name="student_name" required><option value="">Select Student</option>{options}</select>
            <input type="date" name="date" required>
            <input type="time" name="time" required>
            <select name="duration"><option value="30">30 min</option><option value="60" selected>60 min</option><option value="90">90 min</option></select>
            <button type="submit">Create Lesson</button>
        </form>
        <div style="text-align:center;margin-top:20px"><a href="/dashboard" class="btn-back">← Back</a></div>
        </div></div>
    </body>
    </html>
    """)

@app.post("/create-lesson")
def create_lesson(student_name: str = Form(...), date: str = Form(...), time: str = Form(...), duration: int = Form(60)):
    return HTMLResponse(f"<div style='text-align:center;padding:50px'><h2>✅ Lesson Created!</h2><p>{student_name} on {date} at {time}</p><a href='/schedule'>Schedule Another</a> | <a href='/dashboard'>Dashboard</a></div>")

print("✅ App ready with beautiful designs!")


@app.get("/auth/google")
def auth_google():
    """Force Google Calendar authorization"""
    from google_auth_oauthlib.flow import Flow
    import os
    
    # Set up the flow
    flow = Flow.from_client_secrets_file(
        'credentials.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        redirect_uri='https://studio-app-7y7z.onrender.com/callback'
    )
    
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    return RedirectResponse(url=auth_url)


@app.get("/callback")
def callback(code: str = None, state: str = None):
    """Handle Google OAuth callback"""
    from google_auth_oauthlib.flow import Flow
    from fastapi.responses import HTMLResponse
    import os
    import json
    import traceback
    
    try:
        print("Callback received, fetching token...")
        
        # Use the same scopes as the auth request
        flow = Flow.from_client_secrets_file(
            'credentials.json',
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri='https://studio-app-7y7z.onrender.com/callback'
        )
        
        # Fetch the token - this may return additional scopes but that's OK
        flow.fetch_token(code=code)
        
        # Save credentials
        creds = flow.credentials
        token_data = {
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'token_uri': creds.token_uri,
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'scopes': creds.scopes
        }
        
        with open('token.json', 'w') as f:
            json.dump(token_data, f)
        
        return HTMLResponse("""
        <html>
        <head>
            <title>Success!</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 50px; }
                .success { color: green; }
                .btn { display: inline-block; padding: 10px 20px; margin: 10px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h2 class="success">✅ Google Calendar Connected!</h2>
            <p>Your calendar has been successfully linked to Studio Console.</p>
            <p>You can now see your events on the dashboard.</p>
            <a href="/dashboard" class="btn">Go to Dashboard</a>
            <script>setTimeout(function(){ window.location.href = "/dashboard"; }, 3000);</script>
        </body>
        </html>
        """)
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        return HTMLResponse(f"""
        <html>
        <head><title>Error</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h2>❌ Error: {error_msg}</h2>
            <p><a href="/auth/google">Try again</a></p>
            <p><a href="/dashboard">Go to Dashboard</a></p>
        </body>
        </html>
        """)
