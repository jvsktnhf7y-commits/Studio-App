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

# CSS — full design system
css_content = """
:root{--primary:#6366f1;--primary-dark:#4f46e5;--secondary:#8b5cf6;--success:#10b981;--warning:#f59e0b;--danger:#ef4444;--dark:#1e293b;--muted:#64748b;--border:#e2e8f0;--bg:#f1f5f9;--sidebar:#0f172a;--sw:256px;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
body{font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--dark);min-height:100vh;font-size:14px;line-height:1.5;}
.layout{display:flex;min-height:100vh;}
.sidebar{width:var(--sw);background:var(--sidebar);position:fixed;top:0;left:0;bottom:0;display:flex;flex-direction:column;z-index:200;transition:transform .3s;overflow-y:auto;}
.sidebar-brand{padding:18px 14px;border-bottom:1px solid rgba(255,255,255,.06);display:flex;align-items:center;gap:12px;flex-shrink:0;}
.brand-icon{width:36px;height:36px;border-radius:9px;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0;}
.brand-name{color:#fff;font-size:14px;font-weight:700;}.brand-sub{color:rgba(255,255,255,.3);font-size:10px;margin-top:1px;}
.sidebar-nav{flex:1;padding:10px 10px;}.nav-group{margin-bottom:18px;}
.nav-group-label{color:rgba(255,255,255,.28);font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:1.1px;padding:0 8px;margin-bottom:5px;}
.nav-link{display:flex;align-items:center;gap:9px;padding:8px 10px;border-radius:7px;text-decoration:none;color:rgba(255,255,255,.5);font-size:13px;font-weight:500;transition:all .15s;margin-bottom:1px;}
.nav-link:hover{background:rgba(255,255,255,.07);color:rgba(255,255,255,.9);}
.nav-link.active{background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;box-shadow:0 2px 8px rgba(99,102,241,.4);}
.nav-icon{font-size:15px;width:17px;text-align:center;flex-shrink:0;}
.sidebar-footer{padding:10px;border-top:1px solid rgba(255,255,255,.06);flex-shrink:0;}
.main{margin-left:var(--sw);flex:1;display:flex;flex-direction:column;min-height:100vh;}
.topbar{background:#fff;border-bottom:1px solid var(--border);padding:0 26px;height:58px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;}
.topbar-title{font-size:16px;font-weight:700;color:var(--dark);}
.topbar-right{display:flex;align-items:center;gap:8px;}
.page-body{padding:26px;flex:1;}
.card{background:#fff;border-radius:14px;padding:22px;border:1px solid var(--border);box-shadow:0 1px 3px rgba(0,0,0,.04);margin-bottom:18px;}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;}
.card-title{font-size:14px;font-weight:700;color:var(--dark);}
.stats-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:22px;}
.stat-card{background:#fff;border:1px solid var(--border);border-radius:13px;padding:16px 18px;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.stat-icon{width:38px;height:38px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:17px;margin-bottom:10px;}
.stat-val{font-size:24px;font-weight:800;color:var(--dark);}
.stat-lbl{font-size:11px;color:var(--muted);font-weight:500;margin-top:2px;text-transform:uppercase;letter-spacing:.4px;}
h1{font-size:22px;font-weight:800;color:var(--dark);}
h2{font-size:16px;font-weight:700;color:var(--dark);margin-bottom:12px;}
h3{font-size:14px;font-weight:700;color:var(--dark);}
.btn{display:inline-flex;align-items:center;gap:5px;padding:8px 14px;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;cursor:pointer;border:none;outline:none;transition:all .15s;white-space:nowrap;background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;box-shadow:0 1px 4px rgba(99,102,241,.3);margin:2px;}
.btn:hover{transform:translateY(-1px);box-shadow:0 4px 12px rgba(99,102,241,.4);}
.btn:active{transform:none;}
.btn-success{background:var(--success);box-shadow:0 1px 4px rgba(16,185,129,.3);}
.btn-success:hover{box-shadow:0 4px 12px rgba(16,185,129,.4);}
.btn-danger{background:var(--danger);box-shadow:0 1px 4px rgba(239,68,68,.3);}
.btn-danger:hover{box-shadow:0 4px 12px rgba(239,68,68,.4);}
.btn-warning{background:var(--warning);color:#fff;box-shadow:0 1px 4px rgba(245,158,11,.3);}
.btn-outline{background:transparent;color:var(--primary);border:1.5px solid var(--border);box-shadow:none;}
.btn-outline:hover{border-color:var(--primary);background:#f5f3ff;transform:none;box-shadow:none;}
.btn-ghost{background:transparent;color:var(--muted);box-shadow:none;}
.btn-ghost:hover{background:var(--bg);color:var(--dark);transform:none;box-shadow:none;}
.btn-sm{padding:5px 11px;font-size:12px;border-radius:6px;margin:2px;}
table{width:100%;border-collapse:collapse;}
thead th{background:var(--bg);color:var(--muted);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:9px 13px;text-align:left;border-bottom:1px solid var(--border);}
tbody td{padding:11px 13px;border-bottom:1px solid var(--border);color:var(--dark);}
tbody tr:last-child td{border-bottom:none;}
tbody tr:hover td{background:#fafaff;}
.form-group{margin-bottom:14px;}
.form-label{display:block;font-size:12px;font-weight:600;color:var(--dark);margin-bottom:4px;}
input[type=text],input[type=number],input[type=date],input[type=time],input[type=password],input[type=email],select,textarea{width:100%;padding:8px 11px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;color:var(--dark);background:#fff;transition:border-color .15s,box-shadow .15s;outline:none;font-family:inherit;margin:0;}
input:focus,select:focus,textarea:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.1);}
input[type=checkbox]{width:auto;margin-right:6px;}
.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;}
.badge-success{background:#d1fae5;color:#065f46;}.badge-danger{background:#fee2e2;color:#991b1b;}
.badge-warning{background:#fef3c7;color:#92400e;}.badge-info{background:#e0e7ff;color:#3730a3;}
.badge-muted{background:var(--bg);color:var(--muted);}
.stat-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;margin:2px;}
.event-item{padding:12px 0;border-bottom:1px solid var(--border);}
.event-item:last-child{border-bottom:none;}
.event-name{font-size:14px;font-weight:600;color:var(--dark);}
.event-meta{font-size:11.5px;color:var(--muted);margin-top:2px;}
.event-actions{display:flex;gap:5px;margin-top:8px;flex-wrap:wrap;}
.student-row{display:flex;align-items:center;gap:11px;padding:11px 0;border-bottom:1px solid var(--border);}
.student-row:last-child{border-bottom:none;}
.student-avatar{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;color:#fff;font-size:13px;font-weight:700;flex-shrink:0;}
.student-info{flex:1;min-width:0;}
.student-name{font-size:13px;font-weight:600;color:var(--dark);}
.student-meta{font-size:11px;color:var(--muted);margin-top:1px;}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px;}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;}
.login-wrap{min-height:100vh;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:24px;}
.login-card{background:#fff;border-radius:18px;padding:36px;width:100%;max-width:390px;border:1px solid var(--border);box-shadow:0 8px 32px rgba(0,0,0,.08);}
.login-logo{width:52px;height:52px;border-radius:13px;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;font-size:24px;margin:0 auto 18px;}
.container{max-width:1100px;margin:0 auto;padding:24px;}
.alert{padding:12px 16px;border-radius:9px;margin-bottom:14px;font-size:13px;font-weight:500;}
.alert-warning{background:#fef3c7;color:#92400e;border:1px solid #fde68a;}
.alert-success{background:#d1fae5;color:#065f46;border:1px solid #a7f3d0;}
.alert-danger{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;}
.alert-info{background:#e0e7ff;color:#3730a3;border:1px solid #c7d2fe;}
.menu-btn{display:none;background:none;border:none;font-size:20px;cursor:pointer;color:var(--dark);padding:4px;}
.sidebar-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:150;}
@media(max-width:768px){
  .sidebar{transform:translateX(-100%);}
  .sidebar.open{transform:translateX(0);}
  .sidebar-overlay.open{display:block;}
  .main{margin-left:0;}
  .page-body{padding:14px;}
  .topbar{padding:0 14px;}
  .menu-btn{display:block;}
  .stats-row{grid-template-columns:1fr 1fr;gap:10px;}
  .two-col,.three-col{grid-template-columns:1fr;}
  h1{font-size:18px;}
}
@media(max-width:420px){.stats-row{grid-template-columns:1fr;}}
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

def page(title: str, content: str, active: str = "dashboard", extra_head: str = "") -> str:
    links = [
        ("dashboard", "/dashboard", "🏠", "Dashboard"),
        ("students",  "/students",  "👥", "Students"),
        ("rates",     "/rates",     "💰", "Rates"),
        ("payments",  "/payments",  "💳", "Payments"),
        ("schedule",  "/schedule",  "📅", "Schedule"),
        ("revenue",   "/revenue",   "📊", "Revenue"),
        ("analytics", "/analytics", "📈", "Analytics"),
        ("settings",  "/settings",  "⚙️",  "Settings"),
        ("admin",     "/admin",     "🔐", "Admin"),
    ]
    nav_html = ""
    for k, href, icon, label in links:
        cls = "nav-link active" if k == active else "nav-link"
        nav_html += f'<a href="{href}" class="{cls}"><span class="nav-icon">{icon}</span>{label}</a>\n'
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
{extra_head}
</head>
<body>
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="layout">
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <div class="brand-icon">🎵</div>
    <div><div class="brand-name">Studio Console</div><div class="brand-sub">Music Studio Manager</div></div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-group">
      <div class="nav-group-label">Navigation</div>
      {nav_html}
    </div>
  </nav>
  <div class="sidebar-footer">
    <a href="/logout" class="nav-link"><span class="nav-icon">🚪</span>Logout</a>
  </div>
</aside>
<div class="main">
  <header class="topbar">
    <div style="display:flex;align-items:center;gap:10px;">
      <button class="menu-btn" onclick="openSidebar()">☰</button>
      <span class="topbar-title">{title}</span>
    </div>
    <div class="topbar-right">
      <a href="/dashboard" class="btn btn-ghost btn-sm">🏠</a>
    </div>
  </header>
  <div class="page-body">
    {content}
  </div>
</div>
</div>
<script>
function openSidebar(){{document.getElementById('sidebar').classList.add('open');document.getElementById('overlay').classList.add('open');}}
function closeSidebar(){{document.getElementById('sidebar').classList.remove('open');document.getElementById('overlay').classList.remove('open');}}
</script>
</body>
</html>"""


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

    # Fetch calendar events — build event items HTML
    today_events_html = ""
    today_lesson_count = 0
    try:
        import pytz
        service = get_calendar_service()
        if service:
            tz = pytz.timezone('America/New_York')
            now_tz = datetime.now(tz)
            start = now_tz.replace(hour=0, minute=0, second=0, microsecond=0)
            end   = now_tz.replace(hour=23, minute=59, second=59, microsecond=0)
            start_utc = start.astimezone(pytz.UTC).isoformat()
            end_utc   = end.astimezone(pytz.UTC).isoformat()
            events = service.events().list(
                calendarId='primary', timeMin=start_utc, timeMax=end_utc,
                singleEvents=True
            ).execute().get('items', [])

            lesson_keywords = [k.strip().lower() for k in settings.get('lesson_keywords', []) if k.strip()] or \
                ['lesson','private','student','class','music','piano','guitar','violin','drums','voice']

            for e in events:
                raw_summary = e.get('summary', 'Lesson')
                clean_name  = extract_student_name(raw_summary)
                start_time  = e.get('start', {}).get('dateTime', 'All day')
                end_time    = e.get('end',   {}).get('dateTime', 'All day')
                duration_minutes = 60
                if start_time and 'T' in start_time and end_time and 'T' in end_time:
                    try:
                        s_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        e_dt = datetime.fromisoformat(end_time.replace('Z',   '+00:00'))
                        duration_minutes = int((e_dt - s_dt).total_seconds() / 60)
                    except Exception:
                        pass
                display_time = format_standard_time(start_time)

                matched_student = None
                for sn, sd in existing_students.items():
                    if matches_student(raw_summary, sn, sd.get('aliases', [])) or \
                       matches_student(clean_name,  sn, sd.get('aliases', [])):
                        matched_student = sn
                        break
                has_keyword = any(kw in raw_summary.lower() for kw in lesson_keywords)

                if matched_student:
                    today_lesson_count += 1
                    today_events_html += f"""<div class="event-item">
  <div class="event-name">🎵 {matched_student}</div>
  <div class="event-meta">{display_time} &middot; {duration_minutes} min</div>
  <div class="event-actions">
    <form action="/log-attendance" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{matched_student}">
      <input type="hidden" name="status" value="Confirmed">
      <button type="submit" class="btn btn-success btn-sm">✅ Confirm</button>
    </form>
    <form action="/log-attendance" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{matched_student}">
      <input type="hidden" name="status" value="Missed">
      <button type="submit" class="btn btn-danger btn-sm">❌ Missed</button>
    </form>
    <form action="/log-attendance" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{matched_student}">
      <input type="hidden" name="status" value="Cancelled">
      <button type="submit" class="btn btn-warning btn-sm">🔄 Cancelled</button>
    </form>
  </div>
</div>"""
                elif has_keyword and show_all:
                    today_lesson_count += 1
                    today_events_html += f"""<div class="event-item">
  <div class="event-name">🎵 {clean_name}</div>
  <div class="event-meta">{display_time} &middot; {duration_minutes} min &middot; <em style="color:#f59e0b;">Not registered</em></div>
  <div class="event-actions">
    <form action="/quick-create-student" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{clean_name}">
      <input type="hidden" name="duration_minutes" value="{duration_minutes}">
      <button type="submit" class="btn btn-success btn-sm">✨ Quick Add</button>
    </form>
    <a href="/students?prefill_name={clean_name}" class="btn btn-warning btn-sm">✏️ Full Setup</a>
  </div>
</div>"""
        if not today_events_html:
            today_events_html = '<p style="color:var(--muted);font-size:13px;">No lessons today. <a href="/schedule" style="color:var(--primary);">Schedule one →</a></p>'
        if not service:
            today_events_html = '<p style="color:var(--muted);font-size:13px;"><a href="/calendar-auth" style="color:var(--primary);">Connect Google Calendar</a> to see today\'s lessons.</p>'
    except Exception:
        today_events_html = '<p style="color:var(--muted);font-size:13px;"><a href="/calendar-auth" style="color:var(--primary);">Connect Google Calendar</a> to see today\'s lessons.</p>'

    # Student rows + aggregate stats
    profiles = get_all_profiles()
    total_prepaid = sum(d.get('prepaid', 0) for d in profiles.values())
    total_revenue = calculate_total_revenue()

    student_rows_html = ""
    for name, data in profiles.items():
        prepaid = data.get('prepaid', 0)
        attended = missed = cancelled = 0
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, 'r') as f:
                for row in csv.DictReader(f):
                    if row.get('Student', '') == name:
                        s = row.get('Status', '')
                        if s in ('Confirmed', 'Attended'): attended += 1
                        elif s in ('Missed', 'No-Show'):   missed   += 1
                        elif s == 'Cancelled':              cancelled += 1
        initials = ''.join(p[0].upper() for p in name.split()[:2])
        student_rows_html += f"""<div class="student-row">
  <div class="student-avatar">{initials}</div>
  <div class="student-info">
    <div class="student-name">{name}</div>
    <div class="student-meta">${data.get('rate', 50):.0f}/hr &middot; {data.get('target_minutes', 60)} min &middot; {data.get('description', '') or 'No description'}</div>
  </div>
  <div style="display:flex;gap:4px;flex-wrap:wrap;align-items:center;">
    <span class="stat-badge badge-success">✅ {attended}</span>
    <span class="stat-badge badge-danger">❌ {missed}</span>
    <span class="stat-badge badge-info">💰 ${prepaid:.0f}</span>
  </div>
</div>"""

    if not student_rows_html:
        student_rows_html = '<p style="color:var(--muted);font-size:13px;">No students yet. <a href="/students" style="color:var(--primary);">Add your first student →</a></p>'

    content = f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon" style="background:#ede9fe;">👥</div>
    <div class="stat-val">{len(profiles)}</div>
    <div class="stat-lbl">Active Students</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#d1fae5;">📅</div>
    <div class="stat-val">{today_lesson_count}</div>
    <div class="stat-lbl">Today's Lessons</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#fef3c7;">📊</div>
    <div class="stat-val">${total_revenue:.0f}</div>
    <div class="stat-lbl">Total Revenue</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#e0e7ff;">💳</div>
    <div class="stat-val">${total_prepaid:.0f}</div>
    <div class="stat-lbl">Prepaid Balance</div>
  </div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">📅 Today's Lessons</h3>
      <a href="/schedule" class="btn btn-outline btn-sm">+ Schedule</a>
    </div>
    {today_events_html}
  </div>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">👥 Students</h3>
      <a href="/students" class="btn btn-outline btn-sm">Manage</a>
    </div>
    {student_rows_html}
  </div>
</div>
"""
    return HTMLResponse(page("Dashboard", content, "dashboard"))

# Login
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = ""):
    err = f'<div class="alert alert-danger">{error}</div>' if error else ''
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Login — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo">🎵</div>
    <h1 style="text-align:center;margin-bottom:4px;">Studio Console</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Sign in to your account</p>
    {err}
    <form action="/login" method="post">
      <div class="form-group">
        <label class="form-label">Username</label>
        <input type="text" name="username" placeholder="admin" required>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;margin-top:4px;">Sign In</button>
    </form>
  </div>
</div>
</body>
</html>""")

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
        prepaid = data.get('prepaid', 0)
        rows += f"""<tr>
  <td><strong>{name}</strong></td>
  <td>${data['rate']:.0f}/hr</td>
  <td>{data.get('target_minutes', 60)} min</td>
  <td>{data.get('description', '') or '—'}</td>
  <td><span class="badge badge-info">${prepaid:.2f}</span></td>
  <td>
    <a href="/edit-student/{name}" class="btn btn-outline btn-sm">✏️ Edit</a>
    <form action="/delete-student" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{name}">
      <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Delete {name}?')">🗑️</button>
    </form>
  </td>
</tr>"""

    # Calendar suggestions
    suggestions_html = ""
    try:
        import pytz
        service = get_calendar_service()
        if service:
            tz  = pytz.timezone('America/New_York')
            now = datetime.now(tz)
            start_utc = now.replace(hour=0,  minute=0,  second=0,  microsecond=0).astimezone(pytz.UTC).isoformat()
            end_utc   = (now.replace(hour=23, minute=59, second=59, microsecond=0) + timedelta(days=30)).astimezone(pytz.UTC).isoformat()
            events = service.events().list(
                calendarId='primary', timeMin=start_utc, timeMax=end_utc, singleEvents=True
            ).execute().get('items', [])
            existing = set(profiles.keys())
            suggested = {}
            for e in events:
                raw = e.get('summary', '').strip()
                sname = extract_student_name(raw)
                if sname and sname not in existing and looks_like_student_name(sname):
                    st = e.get('start', {}).get('dateTime', '')
                    et = e.get('end',   {}).get('dateTime', '')
                    dur = 60
                    if st and 'T' in st and et and 'T' in et:
                        try:
                            dur = int((datetime.fromisoformat(et.replace('Z','+00:00')) - datetime.fromisoformat(st.replace('Z','+00:00'))).total_seconds() / 60)
                        except Exception:
                            pass
                    if sname not in suggested:
                        suggested[sname] = {'dur': dur, 'time': format_standard_time(st) if st else 'TBD'}
            if suggested:
                sug_rows = ""
                for sname, info in suggested.items():
                    rate = 30 if info['dur'] <= 30 else (40 if info['dur'] <= 45 else (50 if info['dur'] <= 60 else 75))
                    sug_rows += f"""<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;padding:10px;background:white;border-radius:9px;margin-bottom:8px;gap:8px;">
  <span><strong>{sname}</strong> — {info['time']} · {info['dur']} min · ${rate}/hr suggested</span>
  <form action="/quick-create-student" method="post" style="display:inline;">
    <input type="hidden" name="student_name" value="{sname}">
    <input type="hidden" name="duration_minutes" value="{info['dur']}">
    <button type="submit" class="btn btn-success btn-sm">✨ Quick Add</button>
  </form>
</div>"""
                suggestions_html = f'<div class="card alert-warning" style="border:1px solid #fde68a;background:#fef9ec;"><h3 style="margin-bottom:12px;">💡 Calendar Suggestions</h3>{sug_rows}</div>'
    except Exception as exc:
        print(f"Calendar suggestion error: {exc}")

    content = f"""{suggestions_html}
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">👥 Students</h2>
    <a href="/students" class="btn btn-outline btn-sm">Refresh</a>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Name</th><th>Rate</th><th>Lesson</th><th>Focus</th><th>Prepaid</th><th>Actions</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="6" style="text-align:center;padding:20px;color:var(--muted);">No students yet</td></tr>'}</tbody>
    </table>
  </div>
</div>
<div class="card">
  <h2>➕ Add Student</h2>
  <form action="/add-profile" method="post">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;">
        <label class="form-label">Student Name</label>
        <input type="text" name="name" placeholder="Full name" value="{prefill_name}" required>
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Pricing Tier</label>
        <input type="text" name="rate_tier_name" placeholder="e.g. Standard" value="Standard">
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Focus / Instrument</label>
        <input type="text" name="description" placeholder="e.g. Piano, Drums">
      </div>
    </div>
    <button type="submit" class="btn" style="margin-top:14px;">Create Profile</button>
  </form>
</div>"""
    return HTMLResponse(page("Students", content, "students"))

@app.post("/add-profile")
def add_profile(name: str = Form(...), rate_tier_name: str = Form(...), description: str = Form(...)):
    profiles = get_all_profiles()
    profiles[name] = {"tier_name": rate_tier_name, "rate": DEFAULT_RATE, "target_minutes": 60, "credits": 0, "description": description, "prepaid": 0}
    save_all_profiles(profiles)
    return RedirectResponse(url="/students", status_code=303)

@app.get("/rates", response_class=HTMLResponse)
def rates_page():
    tiers = get_pricing_tiers()
    rows = "".join(
        f'<tr><td><strong>{n}</strong></td><td>${d["rate"]:.2f}/hr</td><td>{d["minutes"]} min</td></tr>'
        for n, d in tiers.items()
    )
    content = f"""
<div class="two-col">
  <div class="card">
    <h2>💰 Pricing Tiers</h2>
    <table>
      <thead><tr><th>Tier Name</th><th>Hourly Rate</th><th>Duration</th></tr></thead>
      <tbody>{rows or '<tr><td colspan="3" style="text-align:center;padding:20px;color:var(--muted);">No tiers yet</td></tr>'}</tbody>
    </table>
  </div>
  <div class="card">
    <h2>➕ Add Pricing Tier</h2>
    <form action="/save-pricing-tier" method="post">
      <div class="form-group"><label class="form-label">Tier Name</label><input type="text" name="tier_name" placeholder="e.g. 1 Hour Standard" required></div>
      <div class="form-group"><label class="form-label">Hourly Rate ($)</label><input type="number" step="0.01" name="hourly_rate" placeholder="50.00" required></div>
      <div class="form-group"><label class="form-label">Duration (minutes)</label><input type="number" name="target_minutes" placeholder="60" value="60"></div>
      <button type="submit" class="btn">Create Tier</button>
    </form>
  </div>
</div>"""
    return HTMLResponse(page("Rates", content, "rates"))

@app.post("/save-pricing-tier")
def save_pricing_tier(tier_name: str = Form(...), hourly_rate: float = Form(...), target_minutes: int = Form(60)):
    tiers = get_pricing_tiers()
    tiers[tier_name] = {"rate": hourly_rate, "minutes": target_minutes}
    save_pricing_tiers(tiers)
    return RedirectResponse(url="/rates", status_code=303)

@app.get("/schedule", response_class=HTMLResponse)
def schedule_page():
    students = get_all_profiles()
    options = "".join(f'<option value="{n}">{n}</option>' for n in students.keys())
    content = f"""
<div class="card" style="max-width:520px;">
  <h2>📅 Schedule a Lesson</h2>
  <form action="/create-lesson" method="post">
    <div class="form-group"><label class="form-label">Student</label>
      <select name="student_name" required><option value="">Select student…</option>{options}</select>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;"><label class="form-label">Date</label><input type="date" name="date" required></div>
      <div class="form-group" style="margin:0;"><label class="form-label">Time</label><input type="time" name="time" required></div>
    </div>
    <div class="form-group" style="margin-top:12px;"><label class="form-label">Duration</label>
      <select name="duration">
        <option value="30">30 min</option>
        <option value="45">45 min</option>
        <option value="60" selected>60 min</option>
        <option value="90">90 min</option>
      </select>
    </div>
    <button type="submit" class="btn" style="margin-top:4px;">Book Lesson</button>
  </form>
</div>"""
    return HTMLResponse(page("Schedule", content, "schedule"))

@app.post("/create-lesson")
def create_lesson(student_name: str = Form(...), date: str = Form(...), time: str = Form(...), duration: int = Form(60)):
    lesson_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    display_time = format_standard_time(lesson_time.isoformat())
    content = f"""<div class="card" style="max-width:480px;text-align:center;">
  <div style="font-size:48px;margin-bottom:12px;">✅</div>
  <h2>Lesson Booked</h2>
  <p style="margin:12px 0;"><strong>{student_name}</strong><br>
  <span style="color:var(--muted);">{date} at {display_time} · {duration} min</span></p>
  <div style="display:flex;gap:8px;justify-content:center;margin-top:16px;">
    <a href="/schedule" class="btn btn-outline">+ Another</a>
    <a href="/dashboard" class="btn">Dashboard</a>
  </div>
</div>"""
    return HTMLResponse(page("Lesson Booked", content, "schedule"))

@app.get("/payments", response_class=HTMLResponse)
def payments_page():
    profiles = get_all_profiles()
    options = "".join(f'<option value="{n}">{n}</option>' for n in profiles.keys())
    # Build prepaid summary
    balance_rows = "".join(
        f'<tr><td><strong>{n}</strong></td>'
        f'<td><span class="badge badge-info">${d.get("prepaid",0):.2f}</span></td>'
        f'<td><a href="/edit-student/{n}" class="btn btn-outline btn-sm">Adjust</a></td></tr>'
        for n, d in profiles.items()
    )
    content = f"""
<div class="two-col">
  <div class="card">
    <h2>💳 Record Payment</h2>
    <form action="/record-payment" method="post">
      <div class="form-group"><label class="form-label">Student</label>
        <select name="student_name" required><option value="">Select student…</option>{options}</select>
      </div>
      <div class="form-group"><label class="form-label">Amount ($)</label>
        <input type="number" step="0.01" name="amount" placeholder="0.00" required>
      </div>
      <div class="form-group"><label class="form-label">Date</label>
        <input type="date" name="payment_date" required>
      </div>
      <div class="form-group"><label class="form-label">Method</label>
        <select name="payment_method">
          <option>Cash</option><option>Check</option><option>Venmo</option><option>Zelle</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">Notes (optional)</label>
        <input type="text" name="notes" placeholder="e.g. monthly prepay">
      </div>
      <button type="submit" class="btn">Record Payment</button>
    </form>
  </div>
  <div class="card">
    <h2>💰 Prepaid Balances</h2>
    <table>
      <thead><tr><th>Student</th><th>Balance</th><th></th></tr></thead>
      <tbody>{balance_rows or '<tr><td colspan="3" style="text-align:center;padding:20px;color:var(--muted);">No students</td></tr>'}</tbody>
    </table>
  </div>
</div>"""
    return HTMLResponse(page("Payments", content, "payments"))

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
    """Log attendance and deduct lesson fee from prepaid balance."""
    today = datetime.now().strftime("%Y-%m-%d")
    profiles = get_all_profiles()
    student = profiles.get(student_name, {})
    rate = student.get('rate', DEFAULT_RATE)
    prepaid = float(student.get('prepaid', 0.0))

    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    key = f"{client_ip}_{student_name}"
    now = datetime.now()
    if key in rate_limit and (now - rate_limit[key]).total_seconds() < 5:
        return HTMLResponse("""<!DOCTYPE html>
        <html><head><title>Too Fast</title><link rel="stylesheet" href="/static/style.css"></head>
        <body><div class="container" style="max-width:480px;margin-top:40px;">
            <div class="card" style="text-align:center;">
                <h1>⏳ Too Fast!</h1>
                <p>Please wait a moment before clicking again.</p>
                <a href="/dashboard" class="btn">Back to Dashboard</a>
            </div></div></body></html>""")
    rate_limit[key] = now

    # Duplicate check
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
        return HTMLResponse(f"""<!DOCTYPE html>
        <html><head><title>Already Logged</title><link rel="stylesheet" href="/static/style.css"></head>
        <body><div class="container" style="max-width:480px;margin-top:40px;">
            <div class="card" style="text-align:center;">
                <h1>⚠️ Already Logged</h1>
                <p>{student_name} was already marked as <strong>{existing_status}</strong> for today.</p>
                <meta http-equiv="refresh" content="3;url=/dashboard">
                <p style="color:#888;font-size:14px;">Redirecting in 3 seconds…</p>
                <a href="/dashboard" class="btn">Back to Dashboard</a>
            </div></div></body></html>""")

    # Determine charge and new balance
    if status == 'Cancelled':
        amount_charged = 0.00
        new_prepaid = prepaid
        ledger_status = 'Cancelled'
        ledger_note = 'Cancelled — no charge'
        insufficient = False
    else:
        # Confirmed and Missed both charge the full lesson rate
        if prepaid >= rate:
            amount_charged = rate
            new_prepaid = prepaid - rate
            ledger_status = status
            ledger_note = f"Deducted from prepaid: ${prepaid:.2f} → ${new_prepaid:.2f}"
            insufficient = False
        else:
            amount_charged = 0.00
            new_prepaid = prepaid
            ledger_status = 'Payment Due'
            ledger_note = f"Insufficient prepaid balance (${prepaid:.2f}) — payment required"
            insufficient = True

    # Write ledger entry
    with open(LEDGER_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([today, student_name, ledger_status, f"{amount_charged:.2f}", ledger_note])

    # Update prepaid balance in profiles
    if student_name in profiles:
        profiles[student_name]['prepaid'] = round(new_prepaid, 2)
        save_all_profiles(profiles)

    # Insufficient balance warning page
    if insufficient:
        return HTMLResponse(f"""<!DOCTYPE html>
        <html><head><title>Insufficient Balance</title><link rel="stylesheet" href="/static/style.css"></head>
        <body><div class="container" style="max-width:520px;margin-top:40px;">
            <div class="card" style="text-align:center;">
                <h1>⚠️ Insufficient Balance</h1>
                <p><strong>{student_name}</strong> has been marked as
                   <strong>{status}</strong> in the ledger.</p>
                <div style="background:#fef3c7;border:2px solid #f59e0b;border-radius:16px;padding:20px;margin:20px 0;">
                    <p style="margin:0;font-size:16px;color:#92400e;">
                        <strong>Current prepaid balance: ${prepaid:.2f}</strong><br>
                        Lesson rate: ${rate:.2f}<br><br>
                        Insufficient prepaid balance.<br>Please collect payment first.
                    </p>
                </div>
                <p style="color:#666;font-size:14px;">Lesson logged as <em>Payment Due</em> — no amount deducted.</p>
                <a href="/dashboard" class="btn">Back to Dashboard</a>
                <a href="/payments" class="btn" style="background:#22c55e;">Record Payment</a>
            </div></div></body></html>""")

    # Cancelled — silent redirect
    if status == 'Cancelled':
        return RedirectResponse(url="/dashboard", status_code=303)

    # Success confirmation with auto-redirect
    emoji = "✅" if status == "Confirmed" else "❌"
    return HTMLResponse(f"""<!DOCTYPE html>
    <html><head><title>Lesson Logged</title><link rel="stylesheet" href="/static/style.css">
    <meta http-equiv="refresh" content="3;url=/dashboard"></head>
    <body><div class="container" style="max-width:520px;margin-top:40px;">
        <div class="card" style="text-align:center;">
            <h1>{emoji} Lesson Logged</h1>
            <p><strong>{student_name}</strong> marked as <strong>{status}</strong>.</p>
            <div style="background:#d1fae5;border:2px solid #22c55e;border-radius:16px;padding:20px;margin:20px 0;">
                <p style="margin:0;font-size:16px;color:#065f46;">
                    <strong>💰 ${amount_charged:.2f} deducted from prepaid</strong><br>
                    New balance: <strong>${new_prepaid:.2f}</strong>
                </p>
            </div>
            <p style="color:#888;font-size:14px;">Redirecting in 3 seconds…</p>
            <a href="/dashboard" class="btn">Back to Dashboard</a>
        </div></div></body></html>""")

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


def compute_analytics():
    from collections import defaultdict

    now = datetime.now()

    def get_months(n):
        result = []
        for i in range(n - 1, -1, -1):
            m, y = now.month - i, now.year
            while m <= 0:
                m += 12
                y -= 1
            result.append((y, m))
        return result

    profiles = get_all_profiles()

    ledger_rows = []
    ledger_path = LEDGER_FILE if os.path.exists(LEDGER_FILE) else "studio_ledger.csv"
    if os.path.exists(ledger_path):
        with open(ledger_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['_date'] = datetime.strptime(row.get('Date', ''), '%Y-%m-%d')
                except Exception:
                    row['_date'] = None
                ledger_rows.append(row)

    six_months = get_months(6)
    three_months = get_months(3)

    # Revenue per month (net, including corrections)
    month_rev = defaultdict(float)
    for row in ledger_rows:
        if row['_date']:
            try:
                month_rev[(row['_date'].year, row['_date'].month)] += float(row.get('AmountCharged', 0) or 0)
            except Exception:
                pass

    monthly_revenue = [
        {'label': datetime(y, m, 1).strftime('%b %Y'), 'rev': round(month_rev.get((y, m), 0), 2)}
        for y, m in six_months
    ]

    total_revenue = sum(
        float(row.get('AmountCharged', 0) or 0)
        for row in ledger_rows
        if row.get('AmountCharged')
    )

    # Revenue by student (positive charges only)
    student_rev = defaultdict(float)
    for row in ledger_rows:
        try:
            amt = float(row.get('AmountCharged', 0) or 0)
            if amt > 0:
                student_rev[row.get('Student', 'Unknown')] += amt
        except Exception:
            pass
    top5 = sorted(student_rev.items(), key=lambda x: x[1], reverse=True)[:5]
    revenue_by_student = [{'name': n, 'rev': round(r, 2)} for n, r in top5]

    # Revenue by lesson length
    length_rev = defaultdict(float)
    for row in ledger_rows:
        try:
            amt = float(row.get('AmountCharged', 0) or 0)
            if amt > 0:
                mins = profiles.get(row.get('Student', ''), {}).get('target_minutes', 60)
                key = '30 min' if mins <= 30 else ('45 min' if mins <= 45 else ('60 min' if mins <= 60 else '90+ min'))
                length_rev[key] += amt
        except Exception:
            pass

    # Attendance
    att = defaultdict(int)
    for row in ledger_rows:
        s = row.get('Status', '')
        if s in ('Confirmed', 'Attended'):
            att['confirmed'] += 1
        elif s in ('Missed', 'No-Show'):
            att['missed'] += 1
        elif s == 'Cancelled':
            att['cancelled'] += 1
    att_total = sum(att.values()) or 1
    confirmed_pct = round(att['confirmed'] / att_total * 100, 1)
    missed_pct = round(att['missed'] / att_total * 100, 1)
    cancelled_pct = round(att['cancelled'] / att_total * 100, 1)

    # Monthly attendance (3 months)
    mthly_att = defaultdict(lambda: defaultdict(int))
    for row in ledger_rows:
        if row['_date']:
            key = (row['_date'].year, row['_date'].month)
            s = row.get('Status', '')
            if s in ('Confirmed', 'Attended'):
                mthly_att[key]['confirmed'] += 1
            elif s in ('Missed', 'No-Show'):
                mthly_att[key]['missed'] += 1
            elif s == 'Cancelled':
                mthly_att[key]['cancelled'] += 1

    monthly_att = [
        {'label': datetime(y, m, 1).strftime('%b %Y'),
         'confirmed': mthly_att[(y, m)]['confirmed'],
         'missed': mthly_att[(y, m)]['missed'],
         'cancelled': mthly_att[(y, m)]['cancelled']}
        for y, m in three_months
    ]

    # Student reliability
    stu_att = defaultdict(lambda: defaultdict(int))
    for row in ledger_rows:
        stu = row.get('Student', '')
        s = row.get('Status', '')
        if s in ('Confirmed', 'Attended'):
            stu_att[stu]['c'] += 1
        elif s in ('Missed', 'No-Show'):
            stu_att[stu]['m'] += 1
        elif s == 'Cancelled':
            stu_att[stu]['x'] += 1

    reliability = []
    for stu, counts in stu_att.items():
        total = counts['c'] + counts['m']
        rate = round(counts['c'] / total * 100, 1) if total > 0 else 100.0
        reliability.append({
            'name': stu, 'rate': rate,
            'confirmed': counts['c'], 'missed': counts['m'], 'cancelled': counts['x']
        })
    reliability.sort(key=lambda x: x['rate'], reverse=True)

    # Day of week distribution (confirmed lessons)
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    dow = defaultdict(int)
    for row in ledger_rows:
        if row['_date'] and row.get('Status', '') in ('Confirmed', 'Attended'):
            dow[row['_date'].weekday()] += 1
    dow_data = [{'day': day_names[i], 'count': dow[i]} for i in range(7)]

    # Avg lessons per student
    lessons_per_stu = defaultdict(int)
    for row in ledger_rows:
        if row.get('Status', '') in ('Confirmed', 'Attended'):
            lessons_per_stu[row.get('Student', '')] += 1
    avg_lessons = round(sum(lessons_per_stu.values()) / max(len(profiles), 1), 1)

    # Projections (average of last 3 months)
    last3_rev = sum(month_rev.get(k, 0) for k in three_months)
    projected = round(last3_rev / 3, 2)

    total_prepaid = round(sum(d.get('prepaid', 0) for d in profiles.values()), 2)
    total_credits = sum(d.get('credits', 0) for d in profiles.values())
    prepaid_students = sorted(
        [{'name': n, 'prepaid': round(d.get('prepaid', 0), 2), 'credits': d.get('credits', 0)}
         for n, d in profiles.items()],
        key=lambda x: x['prepaid'], reverse=True
    )

    return {
        'monthly_revenue': monthly_revenue,
        'total_revenue': round(total_revenue, 2),
        'revenue_by_student': revenue_by_student,
        'revenue_by_length': dict(length_rev),
        'att': dict(att),
        'att_total': att_total,
        'confirmed_pct': confirmed_pct,
        'missed_pct': missed_pct,
        'cancelled_pct': cancelled_pct,
        'monthly_att': monthly_att,
        'reliability': reliability,
        'dow': dow_data,
        'total_students': len(profiles),
        'avg_lessons': avg_lessons,
        'projected': projected,
        'total_prepaid': total_prepaid,
        'total_credits': total_credits,
        'prepaid_students': prepaid_students,
    }


@app.get("/analytics", response_class=HTMLResponse)
def analytics_page():
    try:
        data = compute_analytics()
    except Exception as e:
        return HTMLResponse(f"""<!DOCTYPE html><html>
        <head><title>Analytics Error</title><link rel="stylesheet" href="/static/style.css"></head>
        <body><div class="container"><div class="card">
        <h1>⚠️ Analytics Error</h1><p>Could not load analytics: {str(e)}</p>
        <a href="/dashboard" class="btn">← Back</a>
        </div></div></body></html>""")

    # Build reliability table rows
    reliability_rows = ""
    for r in data['reliability']:
        bar_w = min(int(r['rate']), 100)
        reliability_rows += f"""<tr>
            <td><strong>{r['name']}</strong></td>
            <td><div style="display:flex;align-items:center;gap:8px;">
                <div style="width:{bar_w}px;height:8px;border-radius:4px;background:linear-gradient(90deg,#667eea,#764ba2);flex-shrink:0;min-width:4px;"></div>
                <span>{r['rate']}%</span></div></td>
            <td style="color:#22c55e;font-weight:700;">{r['confirmed']}</td>
            <td style="color:#ef4444;font-weight:700;">{r['missed']}</td>
            <td style="color:#f59e0b;font-weight:700;">{r['cancelled']}</td>
        </tr>"""
    if not reliability_rows:
        reliability_rows = '<tr><td colspan="5" style="text-align:center;color:#888;padding:20px;">No attendance data yet</td></tr>'

    # Build prepaid table rows
    prepaid_rows = ""
    for s in data['prepaid_students']:
        prepaid_rows += f"""<tr>
            <td><strong>{s['name']}</strong></td>
            <td style="color:#065f46;font-weight:700;">${s['prepaid']:.2f}</td>
            <td style="color:#3730a3;font-weight:700;">{s['credits']}</td>
        </tr>"""
    if not prepaid_rows:
        prepaid_rows = '<tr><td colspan="3" style="text-align:center;color:#888;padding:20px;">No prepaid balances</td></tr>'

    # Build length revenue rows
    length_rows = ""
    for length, rev in sorted(data['revenue_by_length'].items()):
        length_rows += f'<tr><td><strong>{length}</strong></td><td style="color:#22c55e;font-weight:700;">${rev:.2f}</td></tr>'
    if not length_rows:
        length_rows = '<tr><td colspan="2" style="text-align:center;color:#888;padding:20px;">No data yet</td></tr>'

    # Pre-compute DOW colors in Python (avoids JS template literals in f-string)
    dow_max = max((d['count'] for d in data['dow']), default=1) or 1
    dow_colors_list = [
        f"rgba(102, 126, 234, {0.3 + (d['count'] / dow_max) * 0.7:.2f})"
        for d in data['dow']
    ]

    chart_json = json.dumps({
        'monthlyLabels': [m['label'] for m in data['monthly_revenue']],
        'monthlyValues': [m['rev'] for m in data['monthly_revenue']],
        'studentLabels': [s['name'] for s in data['revenue_by_student']],
        'studentValues': [s['rev'] for s in data['revenue_by_student']],
        'attValues': [data['att'].get('confirmed', 0), data['att'].get('missed', 0), data['att'].get('cancelled', 0)],
        'attMonthLabels': [m['label'] for m in data['monthly_att']],
        'attMonthConfirmed': [m['confirmed'] for m in data['monthly_att']],
        'attMonthMissed': [m['missed'] for m in data['monthly_att']],
        'attMonthCancelled': [m['cancelled'] for m in data['monthly_att']],
        'dowLabels': [d['day'] for d in data['dow']],
        'dowValues': [d['count'] for d in data['dow']],
        'dowColors': dow_colors_list,
    })

    total_revenue = data['total_revenue']
    total_students = data['total_students']
    avg_lessons = data['avg_lessons']
    projected = data['projected']
    confirmed_pct = data['confirmed_pct']
    missed_pct = data['missed_pct']
    cancelled_pct = data['cancelled_pct']
    total_prepaid = data['total_prepaid']
    total_credits = data['total_credits']

    rev_summary = ''.join(
        f'<tr><td><strong>{s["name"]}</strong></td><td style="color:var(--success);font-weight:700;">${s["rev"]:.2f}</td></tr>'
        for s in data['revenue_by_student']
    ) or '<tr><td colspan="2" style="text-align:center;padding:16px;color:var(--muted);">No data yet</td></tr>'

    content = f"""
<style>
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:22px;}}
.kpi-card{{background:#fff;border:1px solid var(--border);border-radius:13px;padding:18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04);}}
.kpi-value{{font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--primary),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2;}}
.kpi-label{{color:var(--muted);font-size:11px;font-weight:700;margin-top:6px;text-transform:uppercase;letter-spacing:.7px;}}
.an-title{{font-size:16px;font-weight:700;color:var(--dark);margin:22px 0 12px;display:flex;align-items:center;gap:8px;}}
.chart-card{{background:#fff;border-radius:13px;padding:20px;border:1px solid var(--border);box-shadow:0 1px 3px rgba(0,0,0,.04);margin-bottom:16px;}}
.chart-card h3{{font-size:13px;font-weight:700;color:var(--dark);margin:0 0 14px;}}
.proj-box{{border-radius:12px;padding:16px;text-align:center;margin-bottom:10px;}}
.proj-val{{font-size:26px;font-weight:800;line-height:1.1;}}
.proj-lbl{{font-size:12px;font-weight:600;margin-top:5px;}}
.att-leg{{display:flex;justify-content:center;gap:14px;margin-top:12px;flex-wrap:wrap;font-size:12px;font-weight:600;}}
</style>

<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-value">${total_revenue:.2f}</div><div class="kpi-label">Total Revenue</div></div>
  <div class="kpi-card"><div class="kpi-value">{total_students}</div><div class="kpi-label">Active Students</div></div>
  <div class="kpi-card"><div class="kpi-value">{avg_lessons}</div><div class="kpi-label">Avg Lessons / Student</div></div>
  <div class="kpi-card"><div class="kpi-value">{confirmed_pct}%</div><div class="kpi-label">Attendance Rate</div></div>
  <div class="kpi-card"><div class="kpi-value">${projected:.2f}</div><div class="kpi-label">Projected Next Month</div></div>
</div>

<div class="an-title">💰 Revenue Analytics</div>
<div class="two-col">
  <div class="chart-card"><h3>Monthly Revenue — Last 6 Months</h3><canvas id="monthlyRevenueChart"></canvas></div>
  <div class="chart-card"><h3>Top Students by Revenue</h3><canvas id="studentRevenueChart"></canvas></div>
</div>
<div class="two-col">
  <div class="chart-card"><h3>Revenue by Lesson Length</h3>
    <table><thead><tr><th>Type</th><th>Revenue</th></tr></thead><tbody>{length_rows}</tbody></table>
  </div>
  <div class="chart-card"><h3>Revenue by Student</h3>
    <table><thead><tr><th>Student</th><th>Revenue</th></tr></thead><tbody>{rev_summary}</tbody></table>
  </div>
</div>

<div class="an-title">📅 Attendance Analytics</div>
<div class="two-col">
  <div class="chart-card"><h3>Overall Attendance</h3>
    <canvas id="attendanceDoughnut" style="max-height:220px;"></canvas>
    <div class="att-leg">
      <span style="color:var(--success);">✅ {confirmed_pct}%</span>
      <span style="color:var(--danger);">❌ {missed_pct}%</span>
      <span style="color:var(--warning);">🔄 {cancelled_pct}%</span>
    </div>
  </div>
  <div class="chart-card"><h3>Monthly Trend (3 Months)</h3><canvas id="monthlyAttChart"></canvas></div>
</div>
<div class="chart-card">
  <h3>Student Reliability</h3>
  <table><thead><tr><th>Student</th><th>Rate</th><th>✅ Confirmed</th><th>❌ Missed</th><th>🔄 Cancelled</th></tr></thead>
  <tbody>{reliability_rows}</tbody></table>
</div>

<div class="an-title">🗓️ Day Distribution</div>
<div class="chart-card"><h3>Lessons by Day of Week</h3><canvas id="dowChart" style="max-height:160px;"></canvas></div>

<div class="an-title">💵 Financial Summary</div>
<div class="two-col">
  <div class="chart-card"><h3>Projections</h3>
    <div class="proj-box" style="background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;">
      <div class="proj-val">${projected:.2f}</div>
      <div class="proj-lbl">Projected Next Month</div>
      <div style="font-size:10px;opacity:.8;margin-top:3px;">3-month rolling average</div>
    </div>
    <div class="proj-box" style="background:#d1fae5;">
      <div class="proj-val" style="color:#065f46;">${total_prepaid:.2f}</div>
      <div class="proj-lbl" style="color:#065f46;">Total Prepaid Balance</div>
    </div>
    <div class="proj-box" style="background:#e0e7ff;">
      <div class="proj-val" style="color:#3730a3;">{total_credits}</div>
      <div class="proj-lbl" style="color:#3730a3;">Outstanding Credits</div>
    </div>
  </div>
  <div class="chart-card"><h3>Prepaid by Student</h3>
    <table><thead><tr><th>Student</th><th>Prepaid</th><th>Credits</th></tr></thead><tbody>{prepaid_rows}</tbody></table>
  </div>
</div>

<script>
const D = {chart_json};
Chart.defaults.font.family = "'Inter',-apple-system,sans-serif";
Chart.defaults.font.size = 12;
new Chart(document.getElementById('monthlyRevenueChart'),{{type:'bar',data:{{labels:D.monthlyLabels,datasets:[{{label:'Revenue',data:D.monthlyValues,backgroundColor:'rgba(99,102,241,.75)',borderColor:'#6366f1',borderWidth:2,borderRadius:7,borderSkipped:false}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>'$'+ctx.parsed.y.toFixed(2)}}}}}},scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>'$'+v}}}}}}}}}});
new Chart(document.getElementById('studentRevenueChart'),{{type:'bar',data:{{labels:D.studentLabels,datasets:[{{label:'Revenue',data:D.studentValues,backgroundColor:['rgba(99,102,241,.85)','rgba(139,92,246,.85)','rgba(16,185,129,.85)','rgba(59,130,246,.85)','rgba(245,158,11,.85)'],borderWidth:2,borderRadius:7,borderSkipped:false}}]}},options:{{indexAxis:'y',responsive:true,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>'$'+ctx.parsed.x.toFixed(2)}}}}}},scales:{{x:{{beginAtZero:true,ticks:{{callback:v=>'$'+v}}}}}}}}}});
new Chart(document.getElementById('attendanceDoughnut'),{{type:'doughnut',data:{{labels:['Confirmed','Missed','Cancelled'],datasets:[{{data:D.attValues,backgroundColor:['rgba(16,185,129,.85)','rgba(239,68,68,.85)','rgba(245,158,11,.85)'],borderColor:['#10b981','#ef4444','#f59e0b'],borderWidth:2}}]}},options:{{responsive:true,cutout:'62%',plugins:{{legend:{{position:'bottom'}}}}}}}});
new Chart(document.getElementById('monthlyAttChart'),{{type:'bar',data:{{labels:D.attMonthLabels,datasets:[{{label:'Confirmed',data:D.attMonthConfirmed,backgroundColor:'rgba(16,185,129,.8)',borderColor:'#10b981',borderWidth:2,borderRadius:5}},{{label:'Missed',data:D.attMonthMissed,backgroundColor:'rgba(239,68,68,.8)',borderColor:'#ef4444',borderWidth:2,borderRadius:5}},{{label:'Cancelled',data:D.attMonthCancelled,backgroundColor:'rgba(245,158,11,.8)',borderColor:'#f59e0b',borderWidth:2,borderRadius:5}}]}},options:{{responsive:true,plugins:{{legend:{{position:'bottom'}}}},scales:{{y:{{beginAtZero:true,ticks:{{precision:0}}}}}}}}}});
new Chart(document.getElementById('dowChart'),{{type:'bar',data:{{labels:D.dowLabels,datasets:[{{label:'Lessons',data:D.dowValues,backgroundColor:D.dowColors,borderColor:'#6366f1',borderWidth:2,borderRadius:7,borderSkipped:false}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}}}},scales:{{y:{{beginAtZero:true,ticks:{{precision:0}}}}}}}}}});
</script>"""
    return HTMLResponse(page("Analytics", content, "analytics",
                             extra_head='<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'))

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
    content = """
<div class="card" style="max-width:480px;">
  <h2>🔐 Admin Panel</h2>
  <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">Backup and restore your studio data.</p>
  <div style="display:flex;gap:10px;flex-wrap:wrap;">
    <a href="/api/backup" class="btn">📥 JSON Backup</a>
    <a href="/api/backup/csv" class="btn btn-outline">📦 CSV Backup (ZIP)</a>
  </div>
</div>"""
    return HTMLResponse(page("Admin", content, "admin"))


@app.get("/edit-student/{student_name}")
def edit_student_page(student_name: str):
    profiles = get_all_profiles()
    student = profiles.get(student_name)
    if not student:
        return RedirectResponse(url="/students", status_code=303)
    aliases_str = ', '.join(student.get('aliases', []))
    content = f"""
<div class="card" style="max-width:560px;">
  <h2>✏️ Edit Student: {student_name}</h2>
  <form action="/update-student" method="post">
    <input type="hidden" name="original_name" value="{student_name}">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;">
        <label class="form-label">Student Name</label>
        <input type="text" name="name" value="{student_name}" required>
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Hourly Rate ($)</label>
        <input type="number" step="0.01" name="rate" value="{student.get('rate', 50)}" required>
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Lesson Length (min)</label>
        <input type="number" name="target_minutes" value="{student.get('target_minutes', 60)}">
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Prepaid Balance ($)</label>
        <input type="number" step="0.01" name="prepaid" value="{student.get('prepaid', 0)}">
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Credits</label>
        <input type="number" name="credits" value="{student.get('credits', 0)}">
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Focus / Instrument</label>
        <input type="text" name="description" value="{student.get('description', '')}">
      </div>
    </div>
    <div class="form-group" style="margin-top:12px;">
      <label class="form-label">Alternative Names (comma separated)</label>
      <input type="text" name="aliases" value="{aliases_str}" placeholder="e.g. Jane, Jenny">
      <div style="font-size:11px;color:var(--muted);margin-top:3px;">These names will also match calendar events.</div>
    </div>
    <div style="display:flex;gap:8px;margin-top:6px;">
      <button type="submit" class="btn">Save Changes</button>
      <a href="/students" class="btn btn-ghost">Cancel</a>
    </div>
  </form>
</div>"""
    return HTMLResponse(page(f"Edit — {student_name}", content, "students"))


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
    checked = "checked" if settings.get("show_all", True) else ""
    content = f"""
<div class="card" style="max-width:560px;">
  <h2>⚙️ Calendar Settings</h2>
  <form action="/settings" method="post">
    <div class="form-group">
      <label class="form-label">Lesson Keywords (comma separated)</label>
      <textarea name="lesson_keywords" rows="3" style="width:100%;padding:9px 11px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;resize:vertical;">{keywords}</textarea>
      <div style="font-size:11px;color:var(--muted);margin-top:4px;">Events matching these words appear on the dashboard as lessons.</div>
    </div>
    <div class="form-group" style="display:flex;align-items:center;gap:8px;">
      <input type="checkbox" name="show_all" value="true" {checked} id="show_all" style="width:auto;">
      <label for="show_all" style="font-size:13px;font-weight:500;margin:0;cursor:pointer;">Show unregistered lesson-like events on dashboard</label>
    </div>
    <div style="display:flex;gap:8px;margin-top:6px;">
      <button type="submit" class="btn">Save Settings</button>
      <a href="/calendar-auth" class="btn btn-outline">🔗 Re-connect Calendar</a>
    </div>
  </form>
</div>"""
    return HTMLResponse(page("Settings", content, "settings"))


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
    total = calculate_total_revenue()
    profiles = get_all_profiles()
    total_prepaid = sum(d.get('prepaid', 0) for d in profiles.values())
    content = f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon" style="background:#d1fae5;">📊</div>
    <div class="stat-val">${total:.2f}</div>
    <div class="stat-lbl">Total Revenue</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#e0e7ff;">💳</div>
    <div class="stat-val">${total_prepaid:.2f}</div>
    <div class="stat-lbl">Prepaid on Account</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#fef3c7;">👥</div>
    <div class="stat-val">{len(profiles)}</div>
    <div class="stat-lbl">Active Students</div>
  </div>
</div>
<div class="card" style="text-align:center;padding:40px;">
  <div style="font-size:56px;font-weight:800;color:var(--success);">${total:.2f}</div>
  <div style="color:var(--muted);margin-top:8px;">Total revenue from all recorded lessons</div>
  <div style="margin-top:20px;display:flex;gap:10px;justify-content:center;">
    <a href="/analytics" class="btn">📈 Full Analytics</a>
    <a href="/payments" class="btn btn-outline">💳 Record Payment</a>
  </div>
</div>"""
    return HTMLResponse(page("Revenue", content, "revenue"))


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


@app.get("/static/style.css")
def serve_css():
    """Serve the CSS file"""
    return Response(content=css_content, media_type="text/css")


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
