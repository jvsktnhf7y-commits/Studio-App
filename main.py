from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime, timedelta
import hashlib
import json
from googleapiclient.discovery import build

app = FastAPI(title="Studio App")

# Create static directory
os.makedirs("static", exist_ok=True)
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
SETTINGS_FILE = "/data/calendar_settings.json"
DEFAULT_RATE = 50.00

# Rate limiter dictionary to prevent rapid repeated clicks
rate_limit = {}

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
                        "prepaid": float(row.get("Prepaid", 0)),
                        "aliases": row.get("Aliases", "").split("|") if row.get("Aliases") else []
                    }
    return profiles

def save_all_profiles(profiles_map):
    with open(PROFILES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "TierName", "Rate", "TargetMinutes", "Credits", "Description", "Prepaid", "Aliases"])
        for name, data in profiles_map.items():
            aliases_str = "|".join(data.get('aliases', []))
            writer.writerow([name, data.get('tier_name', ''), data.get('rate', DEFAULT_RATE), data.get('target_minutes', 60), data.get('credits', 0), data.get('description', ''), data.get('prepaid', 0), aliases_str])

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


def load_calendar_settings():
    defaults = {
        "lesson_keywords": ["lesson", "private", "student", "class", "music", "piano", "guitar", "violin", "drums", "voice"],
        "show_all": True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                loaded = json.load(f)
            defaults.update(loaded)
        except Exception:
            pass
    return defaults


def save_calendar_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def format_standard_time(time_str):
    """Convert 24-hour time to 12-hour time with AM/PM"""
    try:
        if not time_str or time_str == 'All day':
            return 'All day'

        if 'T' in time_str:
            time_part = time_str.split('T')[1][:5]
        else:
            time_part = time_str[:5]

        hours, minutes = map(int, time_part.split(':'))
        ampm = 'AM' if hours < 12 else 'PM'
        display_hours = hours % 12
        if display_hours == 0:
            display_hours = 12

        return f"{display_hours}:{minutes:02d} {ampm}"
    except Exception:
        return time_str or 'All day'


def extract_student_name(title):
    """Extract clean student name from various calendar title formats"""
    import re

    if not title:
        return "Unknown"

    clean_title = title

    prefixes = [
        "Private Lesson: ", "Private Lesson - ", "Lesson: ", "Lesson - ",
        "Music Lesson: ", "Music Lesson - ", "Piano: ", "Guitar: ",
        "Drums: ", "Voice: ", "Violin: ", "with ", "& "
    ]

    clean_title = title
    for prefix in prefixes:
        if clean_title.startswith(prefix):
            clean_title = clean_title[len(prefix):]

    suffixes = ["'s Lesson", "'s Private Lesson", "'s Music Lesson", " Lesson", " - Canceled"]
    for suffix in suffixes:
        if clean_title.endswith(suffix):
            clean_title = clean_title[:-len(suffix)]

    if ':' in clean_title:
        clean_title = clean_title.split(':')[-1].strip()
    if '-' in clean_title and len(clean_title.split('-')) == 2:
        clean_title = clean_title.split('-')[-1].strip()

    clean_title = re.sub(r'\([^)]*\)', '', clean_title).strip()
    clean_title = ' '.join(clean_title.split())

    return clean_title if clean_title else title


def looks_like_student_name(name):
    """Filter out non-student calendar entries"""
    skip_words = [
        'rehearsal', 'sound check', 'dress rehearsal', 'warm up', 'break',
        'lunch', 'meeting', 'call', 'admin', 'setup', 'teardown',
        'travel', 'commute', 'office hours', 'prep', 'planning'
    ]

    name_lower = name.lower()
    for word in skip_words:
        if word in name_lower:
            return False

    generic = ['lesson', 'class', 'session', 'appointment', 'meeting']
    if name_lower in generic:
        return False

    if name.replace(' ', '').isdigit():
        return False

    return True


def matches_student(event_title, student_name, student_aliases):
    """Check if an event matches a student by name or alias"""
    event_lower = event_title.lower()

    if student_name.lower() in event_lower:
        return True

    for alias in student_aliases:
        if alias and alias.lower() in event_lower:
            return True

    name_parts = student_name.lower().split()
    for part in name_parts:
        if len(part) > 2 and part in event_lower:
            return True

    return False


# Dashboard
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    existing_students = get_all_profiles()
    settings = load_calendar_settings()
    show_all = True

    # Fetch calendar events
    calendar_html = ""
    try:
        from datetime import datetime
        import pytz

        service = get_calendar_service()
        if service:
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
                
                lesson_keywords = [item.strip().lower() for item in settings.get('lesson_keywords', []) if item.strip()]
                if not lesson_keywords:
                    lesson_keywords = ['lesson', 'private', 'student', 'class', 'music', 'piano', 'guitar', 'violin', 'drums', 'voice', '🎵', '🎹', '🎸', '🎻', '🥁']

                for e in events:
                    raw_summary = e.get('summary', 'Lesson')
                    clean_name = extract_student_name(raw_summary)
                    start_time = e.get('start', {}).get('dateTime', 'All day')
                    duration_minutes = 60
                    end_time = e.get('end', {}).get('dateTime', 'All day')
                    if start_time and 'T' in start_time and end_time and 'T' in end_time:
                        try:
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                        except Exception:
                            pass

                    if start_time and 'T' in start_time:
                        start_time = format_standard_time(start_time)
                    else:
                        start_time = format_standard_time(start_time)

                    matched_student = None
                    for student_name, student_data in existing_students.items():
                        if matches_student(raw_summary, student_name, student_data.get('aliases', [])) or matches_student(clean_name, student_name, student_data.get('aliases', [])):
                            matched_student = student_name
                            break

                    has_keyword = any(keyword in raw_summary.lower() for keyword in lesson_keywords)

                    if matched_student:
                        calendar_html += f'''
                        <li style="padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <span>🎵 <strong>{matched_student}</strong> at {start_time} ({duration_minutes} min)</span>
                                <div style="display: flex; gap: 8px; margin-top: 8px;">
                                    <form action="/log-attendance" method="post" style="display: inline;">
                                        <input type="hidden" name="student_name" value="{matched_student}">
                                        <input type="hidden" name="status" value="Confirmed">
                                        <button type="submit" style="background: #22c55e; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">✅ Confirm</button>
                                    </form>
                                    <form action="/log-attendance" method="post" style="display: inline;">
                                        <input type="hidden" name="student_name" value="{matched_student}">
                                        <input type="hidden" name="status" value="Missed">
                                        <button type="submit" style="background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">❌ Missed</button>
                                    </form>
                                    <form action="/log-attendance" method="post" style="display: inline;">
                                        <input type="hidden" name="student_name" value="{matched_student}">
                                        <input type="hidden" name="status" value="Cancelled">
                                        <button type="submit" style="background: #f59e0b; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">🔄 Cancelled</button>
                                    </form>
                                </div>
                            </div>
                        </li>'''
                    elif has_keyword and show_all:
                        calendar_html += f'''
                        <li style="padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.2);">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <span>🎵 <strong>{clean_name}</strong> at {start_time} ({duration_minutes} min)</span>
                                <div style="display: flex; gap: 8px; margin-top: 8px;">
                                    <form action="/quick-create-student" method="post" style="display: inline;">
                                        <input type="hidden" name="student_name" value="{clean_name}">
                                        <input type="hidden" name="duration_minutes" value="{duration_minutes}">
                                        <button type="submit" style="background: #22c55e; color: white; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer;">✨ Quick Create</button>
                                    </form>
                                    <a href="/students?prefill_name={clean_name}" style="background: #f59e0b; color: white; text-decoration: none; padding: 6px 12px; border-radius: 8px; display: inline-block;">✏️ Full Setup</a>
                                </div>
                            </div>
                            <div style="font-size: 12px; margin-top: 4px; opacity: 0.8;">⚠️ Not registered - click Quick Create to add</div>
                        </li>'''
                    else:
                        continue
                calendar_html += '</ul></div>'
            else:
                calendar_html = '<div class="card"><h2>📅 Today\'s Lessons</h2><p>No lessons scheduled for today.</p><a href="/schedule" class="btn">Schedule a Lesson</a></div>'
        else:
            calendar_html = '<div class="card"><h2>📅 Calendar</h2><p><a href="/calendar-auth">Connect Google Calendar</a> to see your lessons.</p></div>'
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
        <script>
            document.querySelectorAll('form[action="/log-attendance"]').forEach(form => {{
                form.addEventListener('submit', function() {{
                    const buttons = this.querySelectorAll('button');
                    buttons.forEach(btn => {{
                        btn.disabled = true;
                        btn.style.opacity = '0.5';
                        btn.innerText = btn.innerText + ' ✓';
                    }});
                }});
            }});
        </script>
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
def students_page(prefill_name: str = ""):
    profiles = get_all_profiles()
    rows = ""
    for name, data in profiles.items():
        rows += f"""
        <tr>
            <td><strong>{name}</strong></td>
            <td>${data['rate']}/hr</td>
            <td>{data['credits']}</td>
            <td>{data['description']}</td>
            <td>
                <a href="/edit-student/{name}" class="btn" style="background: #3b82f6; padding: 4px 12px; font-size: 12px;">✏️ Edit</a>
                <form action="/delete-student" method="post" style="display: inline;">
                    <input type="hidden" name="student_name" value="{name}">
                    <button type="submit" class="btn" style="background: #ef4444; padding: 4px 12px; font-size: 12px; margin-left: 5px;" onclick="return confirm('Delete {name}?')">🗑️ Delete</button>
                </form>
            </td>
        </tr>
        """

    suggestions_html = ""
    try:
        service = get_calendar_service()
        if service:
            from datetime import datetime
            import pytz

            tz = pytz.timezone('America/New_York')
            now = datetime.now(tz)
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = now.replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=30)

            start_utc = start.astimezone(pytz.UTC).isoformat()
            end_utc = end.astimezone(pytz.UTC).isoformat()

            events = service.events().list(
                calendarId='primary',
                timeMin=start_utc,
                timeMax=end_utc,
                singleEvents=True
            ).execute().get('items', [])

            existing_names = set(profiles.keys())
            suggested_students = {}

            for e in events:
                raw_name = e.get('summary', '').strip()
                name = extract_student_name(raw_name)
                if name and name not in existing_names and looks_like_student_name(name):
                    duration_minutes = 60
                    start_time = e.get('start', {}).get('dateTime', '')
                    end_time = e.get('end', {}).get('dateTime', '')
                    if start_time and 'T' in start_time and end_time and 'T' in end_time:
                        try:
                            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
                        except Exception:
                            pass

                    if name not in suggested_students:
                        suggested_students[name] = {
                            'duration_minutes': duration_minutes,
                            'start_time': format_standard_time(start_time) if start_time else 'TBD',
                        }

            if suggested_students:
                suggestions_html = '<div class="card" style="background: #fef3c7; border: 2px solid #f59e0b;"><h2>💡 Suggested Students from Calendar</h2><p>These names appear in your Google Calendar but don\'t have profiles yet:</p><ul style="list-style: none; padding: 0;">'
                for name, info in suggested_students.items():
                    duration = info['duration_minutes']
                    start_label = info['start_time']
                    if duration <= 30:
                        suggested_rate = 30.00
                    elif duration <= 45:
                        suggested_rate = 40.00
                    elif duration <= 60:
                        suggested_rate = 50.00
                    else:
                        suggested_rate = 75.00

                    suggestions_html += f'''
                    <li style="padding: 10px; margin: 8px 0; background: white; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <span><strong>{name}</strong> — {start_label} • {duration} min lessons (suggested rate: ${suggested_rate}/hr)</span>
                        <form action="/quick-create-student" method="post" style="display: inline;">
                            <input type="hidden" name="student_name" value="{name}">
                            <input type="hidden" name="duration_minutes" value="{duration}">
                            <button type="submit" style="background: #22c55e; color: white; border: none; padding: 8px 16px; border-radius: 8px; cursor: pointer;">✨ Quick Create</button>
                        </form>
                    </li>'''
                suggestions_html += '</ul></div>'
    except Exception as e:
        print(f"Calendar suggestion error: {e}")

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Students</title>
        <link rel="stylesheet" href="/static/style.css">
        <style>
            .suggestion-card {{
                background: #fef3c7;
                border: 2px solid #f59e0b;
                border-radius: 20px;
                padding: 20px;
                margin-bottom: 24px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            {suggestions_html}
            <div class="card">
                <h1>👥 Students</h1>
                <div style="overflow-x:auto;">
                    <table>
                        <thead><tr><th>Name</th><th>Rate</th><th>Credits</th><th>Focus</th><th>Actions</th></tr></thead>
                        <tbody>{rows if rows else '<tr><td colspan="4">No students yet</td></tr>'}</tbody>
                    </table>
                </div>
            </div>
            <div class="card">
                <h2>➕ Add Student</h2>
                <form action="/add-profile" method="post">
                    <input type="text" name="name" placeholder="Student Name" value="{prefill_name}" required>
                    <input type="text" name="rate_tier_name" placeholder="Pricing Tier" value="Standard">
                    <input type="text" name="description" placeholder="Focus/Instrument">
                    <button type="submit" class="btn">Create Profile</button>
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
    lesson_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    display_time = format_standard_time(lesson_time.isoformat())
    return HTMLResponse(f"""<!DOCTYPE html><html><head><title>Lesson Created</title><link rel="stylesheet" href="/static/style.css"></head><body><div class="container"><div class="card" style="text-align:center;"><h1>✅ Lesson Created!</h1><p><strong>{student_name}</strong> on {date} at {display_time} for {duration} minutes</p><a href="/schedule" class="btn">Schedule Another</a><a href="/dashboard" class="btn">Dashboard</a></div></div></body></html>""")

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
def log_attendance(request: Request, student_name: str = Form(...), status: str = Form(...)):
    """Log attendance (Confirmed, Missed, Cancelled) - prevents duplicate entries"""
    today = datetime.now().strftime("%Y-%m-%d")
    profiles = get_all_profiles()
    rate = profiles.get(student_name, {}).get('rate', DEFAULT_RATE)
    amount_charged = rate if status in ("Confirmed", "Missed") else 0.00

    # Rate limiting - prevent multiple clicks within 5 seconds
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}_{student_name}"
    now = datetime.now()
    if key in rate_limit and (now - rate_limit[key]).total_seconds() < 5:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head><title>Too Fast</title><link rel="stylesheet" href="/static/style.css"></head>
        <body>
            <div class="container" style="max-width: 480px; margin-top: 40px;">
                <div class="card" style="text-align:center;">
                    <h1>⏳ Too Fast!</h1>
                    <p>Please wait a moment before clicking again.</p>
                    <a href="/dashboard" class="btn">Back to Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """)
    rate_limit[key] = now

    # Check if this lesson was already logged today
    already_logged = False
    existing_status = None
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('Date') == today and row.get('Student') == student_name:
                    already_logged = True
                    existing_status = row.get('Status', '')
                    break

    if already_logged:
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html>
        <head><title>Already Logged</title><link rel="stylesheet" href="/static/style.css"></head>
        <body>
            <div class="container" style="max-width: 480px; margin-top: 40px;">
                <div class="card" style="text-align:center;">
                    <h1>⚠️ Already Logged</h1>
                    <p>{student_name} was already marked as <strong>{existing_status}</strong> for today.</p>
                    <p>Redirecting back to dashboard...</p>
                    <a href="/dashboard" class="btn">Click here if not redirected</a>
                </div>
            </div>
        </body>
        </html>
        """)

    with open(LEDGER_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([today, student_name, status, f"{amount_charged:.2f}", f"Attendance: {status}"])

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/test")
def test():
    return {"status": "ok"}

def calculate_total_revenue():
    total_revenue = 0
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                amount = float(row.get("AmountCharged", 0) or 0)
                total_revenue += amount
    return total_revenue

@app.get("/api/backup")
def backup_data():
    """Download all data as JSON backup"""
    profiles = get_all_profiles()

    ledger = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ledger.append(row)

    tiers = get_pricing_tiers()

    backup_data = {
        "backup_date": datetime.now().isoformat(),
        "students": profiles,
        "ledger": ledger,
        "pricing_tiers": tiers,
        "stats": {
            "total_students": len(profiles),
            "total_ledger_entries": len(ledger),
            "total_revenue": calculate_total_revenue()
        }
    }

    return JSONResponse(
        content=backup_data,
        headers={"Content-Disposition": "attachment; filename=studio_backup.json"}
    )


@app.get("/api/backup/csv")
def backup_csv():
    """Download all CSV files as a zip"""
    import zipfile
    from io import BytesIO

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in [PROFILES_FILE, LEDGER_FILE, PRICING_FILE]:
            if os.path.exists(file_path):
                zip_file.write(file_path, arcname=os.path.basename(file_path))

    zip_buffer.seek(0)
    return Response(
        content=zip_buffer.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=studio_backup.zip"}
    )


@app.get("/admin")
def admin_panel():
    """Admin-only backup page"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Panel</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card" style="text-align: center;">
                <h1>🔐 Admin Panel</h1>
                <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
                    <a href="/api/backup" class="btn">📥 Download JSON Backup</a>
                    <a href="/api/backup/csv" class="btn">📥 Download CSV Backup (ZIP)</a>
                </div>
                <p style="margin-top: 20px;"><a href="/dashboard">← Back to Dashboard</a></p>
            </div>
        </div>
    </body>
    </html>
    """)


@app.get("/edit-student/{student_name}")
def edit_student_page(student_name: str):
    """Edit student profile page"""
    profiles = get_all_profiles()
    student = profiles.get(student_name)

    if not student:
        return RedirectResponse(url="/students", status_code=303)

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Edit {student_name}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>✏️ Edit Student: {student_name}</h1>
                <form action="/update-student" method="post">
                    <input type="hidden" name="original_name" value="{student_name}">
                    <div class="form-group">
                        <label>Student Name</label>
                        <input type="text" name="name" value="{student_name}" required>
                    </div>
                    <div class="form-group">
                        <label>Hourly Rate ($)</label>
                        <input type="number" step="0.01" name="rate" value="{student.get('rate', 50)}" required>
                    </div>
                    <div class="form-group">
                        <label>Credits</label>
                        <input type="number" name="credits" value="{student.get('credits', 0)}">
                    </div>
                    <div class="form-group">
                        <label>Prepaid Balance ($)</label>
                        <input type="number" step="0.01" name="prepaid" value="{student.get('prepaid', 0)}">
                    </div>
                    <div class="form-group">
                        <label>Target Minutes (Lesson Length)</label>
                        <input type="number" name="target_minutes" value="{student.get('target_minutes', 60)}">
                    </div>
                    <div class="form-group">
                        <label>Description / Focus</label>
                        <input type="text" name="description" value="{student.get('description', '')}">
                    </div>
                    <div class="form-group">
                        <label>Alternative Names (comma separated)</label>
                        <input type="text" name="aliases" value="{', '.join(student.get('aliases', []))}" placeholder="Jane, Jenny, Becky's Lesson">
                        <small>These names will also match calendar events</small>
                    </div>
                    <button type="submit" class="btn">Save Changes</button>
                    <a href="/students" class="btn">Cancel</a>
                </form>
            </div>
        </div>
    </body>
    </html>
    """)


@app.post("/update-student")
def update_student(original_name: str = Form(...), name: str = Form(...), rate: float = Form(...), credits: int = Form(0), prepaid: float = Form(0), target_minutes: int = Form(60), description: str = Form(""), aliases: str = Form("")):
    """Update student profile"""
    profiles = get_all_profiles()

    if original_name != name and original_name in profiles:
        old_data = profiles.pop(original_name)
    else:
        old_data = profiles.get(original_name, {})

    alias_list = [item.strip() for item in aliases.split(',') if item.strip()]
    profiles[name] = {
        "tier_name": old_data.get('tier_name', 'Custom'),
        "rate": rate,
        "target_minutes": target_minutes,
        "credits": credits,
        "description": description,
        "prepaid": prepaid,
        "aliases": alias_list
    }

    save_all_profiles(profiles)
    return RedirectResponse(url="/students", status_code=303)


@app.post("/delete-student")
def delete_student(student_name: str = Form(...)):
    """Delete a student profile"""
    profiles = get_all_profiles()
    if student_name in profiles:
        del profiles[student_name]
        save_all_profiles(profiles)
    return RedirectResponse(url="/students", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    settings = load_calendar_settings()
    keywords = ", ".join(settings.get("lesson_keywords", []))
    show_all_checked = "checked" if settings.get("show_all", True) else ""
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Calendar Settings</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h1>⚙️ Calendar Settings</h1>
                <form action="/settings" method="post">
                    <label>Lesson Keywords (comma separated)</label>
                    <textarea name="lesson_keywords" rows="4" style="width:100%; padding:10px; border-radius:8px; border:2px solid #e5e7eb;">{keywords}</textarea>
                    <label style="display:flex; align-items:center; gap:10px; margin-top:12px;">
                        <input type="checkbox" name="show_all" value="true" {show_all_checked}>
                        Show all lesson-like events on the dashboard
                    </label>
                    <button type="submit" class="btn">Save Settings</button>
                    <a href="/dashboard" class="btn">Back</a>
                </form>
            </div>
        </div>
    </body>
    </html>
    """)


@app.post("/settings")
def save_settings(lesson_keywords: str = Form(""), show_all: str = Form("false")):
    settings = {
        "lesson_keywords": [item.strip() for item in lesson_keywords.split(',') if item.strip()],
        "show_all": show_all == "true"
    }
    save_calendar_settings(settings)
    return RedirectResponse(url="/settings", status_code=303)


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


@app.post("/quick-create-student")
def quick_create_student(student_name: str = Form(...), duration_minutes: int = Form(60)):
    """Quickly create a student profile from calendar event"""
    import re

    raw_name = student_name
    clean_name = raw_name

    prefixes = [
        "Private Lesson: ", "Private Lesson - ", "Lesson: ", "Lesson - ",
        "Music Lesson: ", "Music Lesson - ", "Piano: ", "Guitar: ",
        "Drums: ", "Voice: ", "Violin: ", "with ", "& "
    ]
    for prefix in prefixes:
        if clean_name.startswith(prefix):
            clean_name = clean_name[len(prefix):]
            break

    suffixes = ["'s Lesson", "'s Private Lesson", "'s Music Lesson", " Lesson", " - Canceled"]
    for suffix in suffixes:
        if clean_name.endswith(suffix):
            clean_name = clean_name[:-len(suffix)]
            break

    if ':' in clean_name:
        clean_name = clean_name.split(':')[-1].strip()
    if '-' in clean_name:
        clean_name = clean_name.split('-')[-1].strip()

    clean_name = re.sub(r'\([^)]*\)', '', clean_name).strip()
    clean_name = ' '.join(clean_name.split())

    if not clean_name:
        clean_name = raw_name

    profiles = get_all_profiles()

    if duration_minutes <= 30:
        suggested_rate = 30.00
    elif duration_minutes <= 45:
        suggested_rate = 40.00
    elif duration_minutes <= 60:
        suggested_rate = 50.00
    else:
        suggested_rate = 75.00

    profiles[clean_name] = {
        "tier_name": f"{duration_minutes} min lesson",
        "rate": suggested_rate,
        "target_minutes": duration_minutes,
        "credits": 0,
        "description": f"Auto-created from {duration_minutes} min calendar event",
        "prepaid": 0
    }
    save_all_profiles(profiles)

    return RedirectResponse(url="/dashboard", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Google Calendar endpoints

def get_calendar_service():
    """Get authenticated Google Calendar service with automatic token refresh"""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    import json
    import os

    token_path = '/data/calendar_token.json'

    if not os.path.exists(token_path):
        return None

    with open(token_path, 'r') as f:
        token_data = json.load(f)

    creds = Credentials.from_authorized_user_info(token_data)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    from googleapiclient.discovery import build
    return build('calendar', 'v3', credentials=creds)


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
        scopes=['https://www.googleapis.com/auth/calendar'],
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
        scopes=['https://www.googleapis.com/auth/calendar'],
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
    from datetime import datetime
    import pytz

    service = get_calendar_service()
    if not service:
        return HTMLResponse("<h2>Calendar not connected. <a href='/calendar-auth'>Connect here</a></h2>")
    
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
        display_time = format_standard_time(start_time)
        html += f"<li>{summary} at {display_time}</li>"
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
