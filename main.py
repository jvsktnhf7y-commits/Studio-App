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

# Simple CSS
css_content = """
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; margin: 0; }
.container { max-width: 1200px; margin: 0 auto; }
.card { background: white; border-radius: 24px; padding: 30px; margin-bottom: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
h1 { font-size: 48px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0 0 10px 0; }
.btn { display: inline-block; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: 600; background: #667eea; color: white; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
"""

with open("static/style.css", "w") as f:
    f.write(css_content)

# Password file
PASSWORD_FILE = "admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return HTMLResponse(f"""
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
    error_html = f'<div style="background:#fee;color:#c33;padding:10px;">{error}</div>' if error else ''
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
                    <input type="text" name="username" placeholder="Username" style="width:100%;padding:10px;margin:10px 0;" required>
                    <input type="password" name="password" placeholder="Password" style="width:100%;padding:10px;margin:10px 0;" required>
                    <button type="submit" style="width:100%;padding:10px;background:#667eea;color:white;border:none;border-radius:8px;">Login</button>
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
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head><title>Students</title><link rel="stylesheet" href="/static/style.css"></head>
    <body>
        <div class="container">
            <div class="card"><h1>👥 Students</h1><p>Student management coming soon!</p></div>
            <a href="/dashboard">Back</a>
        </div>
    </body>
    </html>
    """)

# Test endpoint


# Student data functions
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

@app.get("/students", response_class=HTMLResponse)
def students_page():
    profiles = get_all_profiles()
    
    rows = ""
    for name, data in profiles.items():
        rows += f"""
        <tr style="border-bottom: 1px solid #eee;">
            <td style="padding: 12px;"><strong>{name}</strong></td>
            <td style="padding: 12px;">${data['rate']}/hr</td>
            <td style="padding: 12px;">{data['credits']}</td>
            <td style="padding: 12px;">{data['description']}</td>
        </tr>
        """
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Students</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #667eea; color: white; padding: 12px; text-align: left; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>👥 Students</h1>
                <div style="overflow-x: auto;">
                    <table>
                        <thead>
                            <tr><th>Name</th><th>Rate</th><th>Credits</th><th>Focus</th></tr>
                        </thead>
                        <tbody>
                            {rows if rows else '<tr><td colspan="4" style="text-align:center">No students yet</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <h2>➕ Add Student</h2>
                <form action="/add-profile" method="post">
                    <input type="text" name="name" placeholder="Student Name" style="width:100%; padding:10px; margin:5px 0;" required>
                    <input type="text" name="rate_tier_name" placeholder="Pricing Tier" style="width:100%; padding:10px; margin:5px 0;" value="Standard">
                    <input type="text" name="description" placeholder="Focus/Instrument" style="width:100%; padding:10px; margin:5px 0;">
                    <button type="submit" class="btn" style="margin-top:10px;">Create Profile</button>
                </form>
            </div>
            <a href="/dashboard" class="btn">← Back</a>
        </div>
    </body>
    </html>
    """)

@app.post("/add-profile")
def add_profile(name: str = Form(...), rate_tier_name: str = Form(...), description: str = Form(...)):
    profiles = get_all_profiles()
    profiles[name] = {
        "tier_name": rate_tier_name,
        "rate": DEFAULT_RATE,
        "target_minutes": 60,
        "credits": 0,
        "description": description
    }
    save_all_profiles(profiles)
    return RedirectResponse(url="/students", status_code=303)


@app.get("/test")
def test():
    return {"status": "ok", "message": "App is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
