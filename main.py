from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime, timedelta
import hashlib
import json
from urllib.parse import quote as _url_encode, unquote as _url_decode
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
INVOICES_FILE = "/data/invoices.csv"
INVOICE_HEADERS = ["ID", "Student", "Month", "Year", "LessonsCount", "TotalAmount", "PaymentsApplied", "BalanceDue", "Status", "CreatedDate", "PaidDate"]
LEDGER_FIELDS = ['Date', 'Student', 'Status', 'AmountCharged', 'Notes']
SETTINGS_FILE = "/data/calendar_settings.json"
DEFAULT_RATE = 50.00

# Status bucket constants — used everywhere status is evaluated
ATTENDED_STATUSES    = frozenset(['Confirmed', 'Attended', 'Completed', 'Completed (Half Rate)'])
MISSED_STATUSES      = frozenset(['Missed', 'No-Show', 'No Show'])
ZERO_CHARGE_STATUSES = frozenset(['Cancelled', 'Rescheduled', 'Completed (Make-up)'])
HALF_CHARGE_STATUSES = frozenset(['Completed (Half Rate)'])

# Rate limiter dictionary to prevent rapid repeated clicks
rate_limit = {}

# Password file (kept for backward compat — admin hash is also seeded into users.csv)
PASSWORD_FILE = "/data/admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

# Users CSV
USERS_FILE    = "/data/users.csv"
USER_HEADERS  = ["id", "name", "email", "password_hash", "is_beta_tester", "is_admin", "created_at"]

def _seed_users_file():
    """Create users.csv with the admin account if it doesn't exist or is empty."""
    needs_seed = not os.path.exists(USERS_FILE)
    if not needs_seed:
        with open(USERS_FILE, 'r') as _f:
            needs_seed = sum(1 for _ in _f) <= 1   # header-only or empty
    if not needs_seed:
        return
    admin_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    if os.path.exists(PASSWORD_FILE):
        try:
            with open(PASSWORD_FILE, 'r') as _f:
                admin_hash = json.load(_f).get("password_hash", admin_hash)
        except Exception:
            pass
    with open(USERS_FILE, 'w', newline='') as _f:
        _w = csv.DictWriter(_f, fieldnames=USER_HEADERS)
        _w.writeheader()
        _w.writerow({"id": "1", "name": "Admin", "email": "admin",
                     "password_hash": admin_hash, "is_beta_tester": "false",
                     "is_admin": "true", "created_at": datetime.now().strftime('%Y-%m-%d')})

_seed_users_file()

if not os.path.exists(LEDGER_FILE):
    with open(LEDGER_FILE, 'w', newline='') as f:
        csv.writer(f).writerow(LEDGER_FIELDS)


def _ledger_reader(f):
    """Return a DictReader for the ledger that works whether or not the file has a header row."""
    first = f.readline()
    f.seek(0)
    if first.strip() == ','.join(LEDGER_FIELDS):
        return csv.DictReader(f)          # file has headers — normal read
    return csv.DictReader(f, fieldnames=LEDGER_FIELDS)   # legacy no-header file


def _safe_float(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


# ─── User management helpers ──────────────────────────────────────────────────

def get_all_users():
    rows = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
    return rows


def save_all_users(users):
    with open(USERS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=USER_HEADERS)
        writer.writeheader()
        for u in users:
            writer.writerow({k: u.get(k, '') for k in USER_HEADERS})


def get_user_by_email(email: str):
    email = email.strip().lower()
    return next((u for u in get_all_users() if u.get('email', '').lower() == email), None)


def create_user(name: str, email: str, password: str, is_beta: bool = True) -> dict:
    users  = get_all_users()
    new_id = max((int(u.get('id', 0)) for u in users), default=0) + 1
    user   = {
        "id": str(new_id),
        "name": name.strip(),
        "email": email.strip().lower(),
        "password_hash": hashlib.sha256(password.encode()).hexdigest(),
        "is_beta_tester": "true" if is_beta else "false",
        "is_admin": "false",
        "created_at": datetime.now().strftime('%Y-%m-%d'),
    }
    users.append(user)
    save_all_users(users)
    return user


def get_session_user(request: Request):
    """Return the user dict for the current session, or None."""
    identifier = _url_decode(request.cookies.get("session", ""))
    if not identifier:
        return None
    return get_user_by_email(identifier)


def is_admin_user(request: Request) -> bool:
    user = get_session_user(request)
    return bool(user and user.get('is_admin') == 'true')


def page(title: str, content: str, active: str = "dashboard", extra_head: str = "") -> str:
    links = [
        ("dashboard", "/dashboard", "🏠", "Dashboard"),
        ("students",  "/students",  "👥", "Students"),
        ("rates",     "/rates",     "💰", "Rates"),
        ("payments",  "/payments",  "💳", "Payments"),
        ("invoices",  "/invoices",  "🧾", "Invoices"),
        ("schedule",  "/schedule",  "📅", "Schedule"),
        ("revenue",   "/revenue",   "📊", "Revenue"),
        ("analytics", "/analytics", "📈", "Analytics"),
        ("settings",  "/settings",  "⚙️",  "Settings"),
        ("admin",     "/admin",     "🔐", "Admin"),
        ("users",     "/admin/users", "👤", "Users"),
        ("notes",     "/admin/lesson-notes", "📝", "Lesson Notes"),
        ("cancels",   "/admin/blocked-dates", "🚫", "Cancellations"),
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


def student_page(title: str, content: str, student_name: str, active: str = "dashboard") -> str:
    """Layout for the student-facing portal (green theme, limited nav)."""
    links = [
        ("dashboard", "/student/dashboard", "🏠", "My Dashboard"),
        ("lessons",   "/student/lessons",   "📅",  "My Lessons"),
        ("payments",  "/student/payments",  "💳",  "My Payments"),
    ]
    nav_html = ""
    for k, href, icon, label in links:
        cls = "nav-link active" if k == active else "nav-link"
        nav_html += f'<a href="{href}" class="{cls}"><span class="nav-icon">{icon}</span>{label}</a>\n'
    initials = "".join(p[0].upper() for p in student_name.split()[:2]) or "S"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Student Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="layout">
<aside class="sidebar" id="sidebar" style="background:#064e3b;">
  <div class="sidebar-brand">
    <div class="brand-icon" style="background:linear-gradient(135deg,#10b981,#059669);font-size:14px;font-weight:800;">{initials}</div>
    <div><div class="brand-name">{student_name}</div><div class="brand-sub">Student Portal</div></div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-group">
      <div class="nav-group-label">My Studio</div>
      {nav_html}
    </div>
  </nav>
  <div class="sidebar-footer">
    <a href="/student/logout" class="nav-link"><span class="nav-icon">🚪</span>Logout</a>
  </div>
</aside>
<div class="main">
  <header class="topbar">
    <div style="display:flex;align-items:center;gap:10px;">
      <button class="menu-btn" onclick="openSidebar()">☰</button>
      <span class="topbar-title">{title}</span>
    </div>
    <div class="topbar-right">
      <span style="font-size:12px;color:var(--muted);padding:4px 10px;background:var(--bg);border-radius:20px;">🎵 Student Portal</span>
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


def beta_page(title: str, content: str, user_name: str, active: str = "dashboard") -> str:
    """Simplified layout for beta testers — no admin nav items."""
    links = [
        ("dashboard", "/dashboard", "🏠", "Dashboard"),
    ]
    nav_html = ""
    for k, href, icon, label in links:
        cls = "nav-link active" if k == active else "nav-link"
        nav_html += f'<a href="{href}" class="{cls}"><span class="nav-icon">{icon}</span>{label}</a>\n'
    initials = "".join(p[0].upper() for p in user_name.split()[:2]) or "B"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Studio Beta</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
<style>
:root{{--primary:#0891b2;--primary-dark:#0e7490;--secondary:#06b6d4;}}
.sidebar{{background:#0c4a6e;}}
.nav-link.active{{background:linear-gradient(135deg,#0891b2,#06b6d4);box-shadow:0 2px 8px rgba(8,145,178,.4);}}
</style>
</head>
<body>
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="layout">
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <div class="brand-icon" style="background:linear-gradient(135deg,#0891b2,#06b6d4);font-size:14px;font-weight:800;">{initials}</div>
    <div>
      <div class="brand-name">{user_name}</div>
      <div class="brand-sub" style="color:#f59e0b;font-weight:700;">BETA TESTER</div>
    </div>
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
      <span style="font-size:11px;font-weight:700;padding:3px 10px;background:#fef3c7;color:#92400e;border-radius:20px;border:1px solid #fde68a;">🧪 BETA</span>
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


def get_all_invoices():
    invoices = []
    if os.path.exists(INVOICES_FILE):
        with open(INVOICES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                invoices.append(dict(row))
    return invoices


def save_all_invoices(invoices):
    with open(INVOICES_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=INVOICE_HEADERS)
        writer.writeheader()
        for inv in invoices:
            writer.writerow({k: inv.get(k, '') for k in INVOICE_HEADERS})


def generate_invoices_for_month(year: int, month: int) -> int:
    profiles = get_all_profiles()
    invoices = get_all_invoices()
    existing_keys = {(inv['Student'], inv['Year'], inv['Month']) for inv in invoices}

    ledger_by_student = {}
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            reader = _ledger_reader(f)
            for row in reader:
                try:
                    date = datetime.strptime(row.get('Date', ''), '%Y-%m-%d')
                except ValueError:
                    continue
                if date.year != year or date.month != month:
                    continue
                student = row.get('Student', '').strip()
                status = row.get('Status', '')
                amount = float(row.get('AmountCharged', 0) or 0)
                if student not in ledger_by_student:
                    ledger_by_student[student] = {'lessons': 0, 'amount_charged': 0.0}
                if status in ATTENDED_STATUSES:
                    ledger_by_student[student]['lessons'] += 1
                    ledger_by_student[student]['amount_charged'] += amount

    next_id = max((int(inv.get('ID', 0)) for inv in invoices), default=0) + 1
    new_invoices = []
    month_str = str(month)
    year_str = str(year)

    for student, data in ledger_by_student.items():
        if data['lessons'] == 0:
            continue
        if (student, year_str, month_str) in existing_keys:
            continue
        rate = profiles.get(student, {}).get('rate', DEFAULT_RATE)
        total_amount = round(data['lessons'] * rate, 2)
        payments_applied = round(data['amount_charged'], 2)
        balance_due = round(max(total_amount - payments_applied, 0), 2)
        new_invoices.append({
            'ID': str(next_id),
            'Student': student,
            'Month': month_str,
            'Year': year_str,
            'LessonsCount': str(data['lessons']),
            'TotalAmount': f"{total_amount:.2f}",
            'PaymentsApplied': f"{payments_applied:.2f}",
            'BalanceDue': f"{balance_due:.2f}",
            'Status': 'Paid' if balance_due <= 0 else 'Unpaid',
            'CreatedDate': datetime.now().strftime('%Y-%m-%d'),
            'PaidDate': '',
        })
        next_id += 1

    invoices.extend(new_invoices)
    save_all_invoices(invoices)
    return len(new_invoices)


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
def dashboard(request: Request, notice: str = ""):
    user = get_session_user(request)
    admin = user and user.get('is_admin') == 'true'

    # ── Beta tester view ──────────────────────────────────────────────────────
    if not admin:
        user_name = user.get('name', 'Beta Tester') if user else 'Beta Tester'
        profiles  = get_all_profiles()
        total_prepaid = sum(d.get('prepaid', 0) for d in profiles.values())
        total_revenue = calculate_total_revenue()
        beta_content = f"""
<div class="alert alert-warning" style="margin-bottom:18px;">
  🧪 <strong>Beta Tester Mode</strong> — You have read-only access to the studio dashboard.
  Management features are reserved for the admin account.
</div>
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#ede9fe;">👥</div>
    <div class="stat-val">{len(profiles)}</div><div class="stat-lbl">Students</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">📊</div>
    <div class="stat-val">${total_revenue:.0f}</div><div class="stat-lbl">Total Revenue</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">💳</div>
    <div class="stat-val">${total_prepaid:.0f}</div><div class="stat-lbl">Prepaid Balance</div></div>
</div>
<div class="two-col">
  <div class="card">
    <h3 class="card-title" style="margin-bottom:14px;">🎵 What You Can Try</h3>
    <div style="display:flex;flex-direction:column;gap:10px;font-size:13px;">
      <a href="/parent/login" class="btn btn-outline" style="justify-content:flex-start;">
        👨‍👩‍👧 Parent Portal — manage lessons &amp; billing
      </a>
      <a href="/student/login" class="btn btn-outline" style="justify-content:flex-start;">
        🎓 Student Portal — view lessons &amp; balance
      </a>
    </div>
  </div>
  <div class="card">
    <h3 class="card-title" style="margin-bottom:14px;">👤 Your Account</h3>
    <div style="font-size:13px;line-height:2;">
      <div><span style="color:var(--muted);">Name:</span> <strong>{user_name}</strong></div>
      <div><span style="color:var(--muted);">Email:</span> {user.get('email','') if user else ''}</div>
      <div><span style="color:var(--muted);">Role:</span> <span class="badge badge-warning">Beta Tester</span></div>
      <div><span style="color:var(--muted);">Joined:</span> {user.get('created_at','') if user else ''}</div>
    </div>
  </div>
</div>"""
        return HTMLResponse(beta_page(f"Welcome, {user_name}!", beta_content, user_name))

    # ── Admin view (full dashboard) ───────────────────────────────────────────
    notice_html = ""
    if notice == "admin_only":
        notice_html = '<div class="alert alert-warning" style="margin-bottom:16px;">⚠️ That page is restricted to admin users.</div>'

    existing_students = get_all_profiles()
    settings = load_calendar_settings()
    show_all = True
    mode = request.cookies.get("dashboard_mode", "simple")

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
                    if mode == "detailed":
                        today_events_html += f"""<div class="event-item">
  <div class="event-name">🎵 {matched_student}</div>
  <div class="event-meta">{display_time} &middot; {duration_minutes} min</div>
  <form action="/log-attendance" method="post" style="margin-top:10px;">
    <input type="hidden" name="student_name" value="{matched_student}">
    <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
      <select name="status" style="flex:2;min-width:210px;padding:7px 10px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;color:var(--dark);background:#fff;outline:none;">
        <option value="Completed">✅ Completed (Full Rate)</option>
        <option value="Completed (Half Rate)">⚡ Completed (Half Rate)</option>
        <option value="Completed (Make-up)">🔄 Make-up (No Charge)</option>
        <option value="No Show">❌ No Show (Full Charge)</option>
        <option value="Cancelled">🚫 Cancelled (No Charge)</option>
        <option value="Rescheduled">📅 Rescheduled (No Charge)</option>
      </select>
      <input type="text" name="notes" placeholder="Add a note…" style="flex:1;min-width:130px;padding:7px 10px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;color:var(--dark);background:#fff;outline:none;font-family:inherit;">
      <button type="submit" class="btn btn-sm" style="flex-shrink:0;">Log</button>
    </div>
  </form>
</div>"""
                    else:
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

    now_month = datetime.now().month
    now_year  = datetime.now().year
    student_rows_html = ""
    for name, data in profiles.items():
        prepaid  = data.get('prepaid', 0)
        rate     = data.get('rate', DEFAULT_RATE) or DEFAULT_RATE
        attended = missed = cancelled = lessons_this_month = 0
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, 'r') as f:
                for row in _ledger_reader(f):
                    if row.get('Student', '') != name:
                        continue
                    s = row.get('Status', '')
                    if s in ATTENDED_STATUSES:
                        attended += 1
                        try:
                            d = datetime.strptime(row.get('Date', ''), '%Y-%m-%d')
                            if d.year == now_year and d.month == now_month:
                                lessons_this_month += 1
                        except ValueError:
                            pass
                    elif s in MISSED_STATUSES:
                        missed += 1
                    elif s in ZERO_CHARGE_STATUSES:
                        cancelled += 1
        lessons_remaining = int(prepaid / rate) if rate > 0 else 0
        initials = ''.join(p[0].upper() for p in name.split()[:2])
        student_rows_html += f"""<div class="student-row">
  <div class="student-avatar">{initials}</div>
  <div class="student-info">
    <div class="student-name">{name}</div>
    <div class="student-meta">${rate:.0f}/hr &middot; {data.get('target_minutes', 60)} min &middot; {data.get('description', '') or 'No description'}</div>
    <div class="student-meta" style="margin-top:3px;">
      <span style="color:var(--primary);">📚 {lessons_this_month} this month</span>
      &middot;
      <span style="color:var(--success);">💳 {lessons_remaining} remaining</span>
    </div>
  </div>
  <div style="display:flex;gap:4px;flex-wrap:wrap;align-items:center;">
    <span class="stat-badge badge-success">✅ {attended}</span>
    <span class="stat-badge badge-danger">❌ {missed}</span>
    <span class="stat-badge badge-info">💰 ${prepaid:.0f}</span>
  </div>
</div>"""

    if not student_rows_html:
        student_rows_html = '<p style="color:var(--muted);font-size:13px;">No students yet. <a href="/students" style="color:var(--primary);">Add your first student →</a></p>'

    mode_label   = "⚙️ Simple" if mode == "detailed" else "⚙️ Detailed"
    mode_tip     = "Switch to Simple Mode" if mode == "detailed" else "Switch to Detailed Mode"
    mode_badge   = f'<span style="font-size:10px;padding:2px 7px;border-radius:10px;background:{"#e0e7ff" if mode=="detailed" else "#f1f5f9"};color:{"#3730a3" if mode=="detailed" else "var(--muted)"};">{"DETAILED" if mode=="detailed" else "SIMPLE"}</span>'

    content = f"""{notice_html}
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
      <div style="display:flex;align-items:center;gap:8px;">
        <h3 class="card-title">📅 Today's Lessons</h3>
        {mode_badge}
      </div>
      <div style="display:flex;gap:6px;">
        <form action="/toggle-dashboard-mode" method="post" style="display:inline;">
          <button type="submit" class="btn btn-ghost btn-sm" title="{mode_tip}">{mode_label}</button>
        </form>
        <a href="/schedule" class="btn btn-outline btn-sm">+ Schedule</a>
      </div>
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


@app.post("/toggle-dashboard-mode")
def toggle_dashboard_mode(request: Request):
    current  = request.cookies.get("dashboard_mode", "simple")
    new_mode = "detailed" if current == "simple" else "simple"
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="dashboard_mode", value=new_mode, httponly=True, max_age=86400 * 90)
    return response

# Login
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = "", success: str = ""):
    err  = f'<div class="alert alert-danger">{error}</div>'   if error   else ''
    succ = f'<div class="alert alert-success">{success}</div>' if success else ''
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
    {err}{succ}
    <form action="/login" method="post">
      <div class="form-group">
        <label class="form-label">Email / Username</label>
        <input type="text" name="email" placeholder="admin or your email" required autocomplete="username">
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="••••••••" required autocomplete="current-password">
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;margin-top:4px;">Sign In</button>
    </form>
    <div style="margin-top:14px;text-align:center;">
      <a href="/signup" style="font-size:12px;color:var(--primary);">Join the beta — create account →</a>
    </div>
    <div style="margin-top:16px;padding-top:14px;border-top:1px solid var(--border);text-align:center;display:flex;gap:16px;justify-content:center;">
      <a href="/student/login" style="font-size:12px;color:var(--muted);">Student portal →</a>
      <a href="/parent/login" style="font-size:12px;color:#7c3aed;">Parent portal →</a>
    </div>
  </div>
</div>
</body>
</html>""")


@app.post("/login")
def login_post(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    user = get_user_by_email(email)
    if user and user.get('password_hash') == pw_hash:
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(
            key="session",
            value=_url_encode(user['email'], safe=""),
            httponly=True,
            max_age=86400 * 30,
        )
        return response
    return RedirectResponse(url="/login?error=Invalid+email+or+password", status_code=303)


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response

@app.get("/signup", response_class=HTMLResponse)
def signup_page(error: str = ""):
    err = f'<div class="alert alert-danger">{error}</div>' if error else ''
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Join Beta — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card" style="max-width:420px;">
    <div class="login-logo" style="background:linear-gradient(135deg,#0891b2,#06b6d4);">🧪</div>
    <h1 style="text-align:center;margin-bottom:4px;">Join the Beta</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:8px;">Create a free beta tester account</p>
    <div style="text-align:center;margin-bottom:20px;">
      <span style="font-size:11px;font-weight:700;padding:3px 10px;background:#fef3c7;color:#92400e;border-radius:20px;border:1px solid #fde68a;">🧪 BETA — Free Access</span>
    </div>
    {err}
    <form action="/signup" method="post">
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" name="name" placeholder="Your name" required>
      </div>
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" name="email" placeholder="you@email.com" required autocomplete="email">
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="At least 8 characters" required minlength="8" autocomplete="new-password">
      </div>
      <div class="form-group">
        <label class="form-label">Confirm Password</label>
        <input type="password" name="confirm_password" placeholder="Repeat password" required autocomplete="new-password">
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;background:linear-gradient(135deg,#0891b2,#06b6d4);">
        Create Beta Account
      </button>
    </form>
    <div style="margin-top:16px;text-align:center;border-top:1px solid var(--border);padding-top:14px;">
      <a href="/login" style="font-size:12px;color:var(--muted);">Already have an account? Sign in →</a>
    </div>
  </div>
</div>
</body>
</html>""")


@app.post("/signup")
def signup_post(name: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    email = email.strip().lower()

    if password != confirm_password:
        return RedirectResponse(url="/signup?error=Passwords+do+not+match", status_code=303)
    if len(password) < 8:
        return RedirectResponse(url="/signup?error=Password+must+be+at+least+8+characters", status_code=303)
    if get_user_by_email(email):
        return RedirectResponse(url="/signup?error=Email+already+registered", status_code=303)

    user = create_user(name=name, email=email, password=password, is_beta=True)
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=_url_encode(user['email'], safe=""),
        httponly=True,
        max_age=86400 * 30,
    )
    return response


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)

# Routes only admins may visit; beta testers get redirected to /dashboard
_ADMIN_ONLY_PATHS = frozenset([
    '/students', '/rates', '/payments', '/invoices', '/schedule',
    '/revenue', '/analytics', '/settings',
])
_ADMIN_ONLY_PREFIXES = (
    '/admin', '/add-profile', '/edit-student', '/update-student',
    '/delete-student', '/save-pricing-tier', '/record-payment',
    '/generate-invoices', '/mark-invoice-paid', '/create-lesson',
    '/log-attendance', '/quick-create-student', '/api/',
    '/calendar-auth', '/calendar-callback', '/calendar-events',
    '/debug-calendar',
)

# Auth middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Always public: static assets, root redirect
    if path in ["/", "/static"] or path.startswith("/static/"):
        return await call_next(request)

    # Student portal: own login/logout are always public; other /student/* need student cookie
    if path in ["/student/login", "/student/logout"]:
        return await call_next(request)
    if path.startswith("/student/"):
        if request.cookies.get("student_session"):
            return await call_next(request)
        return RedirectResponse(url="/student/login", status_code=303)

    # Parent portal: login/register/logout always public; other /parent/* need parent cookie
    if path in ["/parent/login", "/parent/logout", "/parent/register"]:
        return await call_next(request)
    if path.startswith("/parent/"):
        if request.cookies.get("parent_session"):
            return await call_next(request)
        return RedirectResponse(url="/parent/login", status_code=303)

    # Public admin-side paths (login, signup, test)
    if path in ["/login", "/logout", "/signup", "/test"]:
        return await call_next(request)

    # Validate session cookie → must be a real user in users.csv
    identifier = _url_decode(request.cookies.get("session", ""))
    if not identifier:
        return RedirectResponse(url="/login", status_code=303)

    user = get_user_by_email(identifier)
    if not user:
        resp = RedirectResponse(url="/login", status_code=303)
        resp.delete_cookie("session")
        return resp

    # Admin-only route guard: redirect beta testers politely
    admin = user.get('is_admin') == 'true'
    if not admin:
        if path in _ADMIN_ONLY_PATHS or any(path.startswith(p) for p in _ADMIN_ONLY_PREFIXES):
            return RedirectResponse(url="/dashboard?notice=admin_only", status_code=303)

    return await call_next(request)

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
def log_attendance(request: Request, student_name: str = Form(...), status: str = Form(...), notes: str = Form("")):
    """Log attendance and deduct lesson fee from prepaid balance."""
    today = datetime.now().strftime("%Y-%m-%d")
    profiles = get_all_profiles()
    student = profiles.get(student_name, {})
    rate    = student.get('rate', DEFAULT_RATE)
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
            for row in _ledger_reader(f):
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

    # Determine charge multiplier by status
    if status in ZERO_CHARGE_STATUSES:
        charge_mult = 0.0
    elif status in HALF_CHARGE_STATUSES:
        charge_mult = 0.5
    else:
        charge_mult = 1.0  # full rate for attended and missed/no-show

    target_charge = round(rate * charge_mult, 2)

    if charge_mult == 0.0:
        # No charge — no balance check needed
        amount_charged = 0.00
        new_prepaid    = prepaid
        ledger_note    = notes or f"{status} — no charge"
        insufficient   = False
    else:
        if prepaid >= target_charge:
            amount_charged = target_charge
            new_prepaid    = round(prepaid - target_charge, 2)
            ledger_note    = notes or f"Deducted from prepaid: ${prepaid:.2f} → ${new_prepaid:.2f}"
            insufficient   = False
        else:
            amount_charged = 0.00
            new_prepaid    = prepaid
            ledger_note    = notes or f"Balance insufficient (${prepaid:.2f}) — payment required"
            insufficient   = True

    # Write ledger entry
    with open(LEDGER_FILE, 'a', newline='') as f:
        csv.writer(f).writerow([today, student_name, status, f"{amount_charged:.2f}", ledger_note])

    # Update prepaid balance
    if student_name in profiles:
        profiles[student_name]['prepaid'] = new_prepaid
        save_all_profiles(profiles)

    # Insufficient balance warning
    if insufficient:
        return HTMLResponse(f"""<!DOCTYPE html>
        <html><head><title>Insufficient Balance</title><link rel="stylesheet" href="/static/style.css"></head>
        <body><div class="container" style="max-width:520px;margin-top:40px;">
            <div class="card" style="text-align:center;">
                <h1>⚠️ Insufficient Balance</h1>
                <p><strong>{student_name}</strong> has been marked as <strong>{status}</strong> in the ledger.</p>
                <div style="background:#fef3c7;border:2px solid #f59e0b;border-radius:16px;padding:20px;margin:20px 0;">
                    <p style="margin:0;font-size:16px;color:#92400e;">
                        <strong>Current prepaid balance: ${prepaid:.2f}</strong><br>
                        Charge required: ${target_charge:.2f}<br><br>
                        Insufficient prepaid balance.<br>Please collect payment first.
                    </p>
                </div>
                <p style="color:#666;font-size:14px;">Lesson logged as <em>{status}</em> — no amount deducted.</p>
                <a href="/dashboard" class="btn">Back to Dashboard</a>
                <a href="/payments" class="btn" style="background:#22c55e;">Record Payment</a>
            </div></div></body></html>""")

    # Zero-charge statuses — silent redirect
    if charge_mult == 0.0:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Success page
    STATUS_EMOJI = {
        'Confirmed': '✅', 'Completed': '✅', 'Completed (Half Rate)': '⚡',
        'Missed': '❌', 'No Show': '❌', 'No-Show': '❌',
    }
    emoji = STATUS_EMOJI.get(status, '📋')
    half_note = ' <span style="font-size:13px;opacity:.8;">(half rate)</span>' if status in HALF_CHARGE_STATUSES else ''
    return HTMLResponse(f"""<!DOCTYPE html>
    <html><head><title>Lesson Logged</title><link rel="stylesheet" href="/static/style.css">
    <meta http-equiv="refresh" content="3;url=/dashboard"></head>
    <body><div class="container" style="max-width:520px;margin-top:40px;">
        <div class="card" style="text-align:center;">
            <h1>{emoji} Lesson Logged</h1>
            <p><strong>{student_name}</strong> marked as <strong>{status}</strong>.</p>
            <div style="background:#d1fae5;border:2px solid #22c55e;border-radius:16px;padding:20px;margin:20px 0;">
                <p style="margin:0;font-size:16px;color:#065f46;">
                    <strong>💰 ${amount_charged:.2f} deducted{half_note}</strong><br>
                    New balance: <strong>${new_prepaid:.2f}</strong>
                </p>
            </div>
            {f'<p style="color:var(--muted);font-size:12px;margin-bottom:12px;">Note: {ledger_note}</p>' if notes else ''}
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
            for row in _ledger_reader(f):
                total_revenue += _safe_float(row.get("AmountCharged", 0))
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
            for row in _ledger_reader(f):
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
        if s in ATTENDED_STATUSES:
            att['confirmed'] += 1
        elif s in MISSED_STATUSES:
            att['missed'] += 1
        elif s in ZERO_CHARGE_STATUSES:
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
            if s in ATTENDED_STATUSES:
                mthly_att[key]['confirmed'] += 1
            elif s in MISSED_STATUSES:
                mthly_att[key]['missed'] += 1
            elif s in ZERO_CHARGE_STATUSES:
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
        if s in ATTENDED_STATUSES:
            stu_att[stu]['c'] += 1
        elif s in MISSED_STATUSES:
            stu_att[stu]['m'] += 1
        elif s in ZERO_CHARGE_STATUSES:
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
        if row['_date'] and row.get('Status', '') in ATTENDED_STATUSES:
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
            for row in _ledger_reader(f):
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
<div class="two-col">
  <div class="card">
    <h2>🔐 Data & Backup</h2>
    <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">Backup and restore your studio data.</p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <a href="/api/backup" class="btn">📥 JSON Backup</a>
      <a href="/api/backup/csv" class="btn btn-outline">📦 CSV Backup (ZIP)</a>
    </div>
  </div>
  <div class="card">
    <h2>👤 User Management</h2>
    <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">View beta testers, promote users, or remove accounts.</p>
    <a href="/admin/users" class="btn">👤 Manage Users</a>
  </div>
</div>
<div class="two-col">
  <div class="card">
    <h2>📝 Lesson Notes</h2>
    <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">Add notes and assignments after each lesson. Parents can view these in their portal.</p>
    <a href="/admin/lesson-notes" class="btn">📝 Manage Notes</a>
  </div>
  <div class="card">
    <h2>🚫 Cancellation Requests</h2>
    <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">Review and respond to date-blocking requests submitted by parents.</p>
    <a href="/admin/blocked-dates" class="btn btn-warning">🚫 View Requests</a>
  </div>
</div>
<div class="card" style="max-width:480px;">
  <h2>👨‍👩‍👧 Parent Accounts</h2>
  <p style="color:var(--muted);margin-bottom:18px;font-size:13px;">Parents can register and manage their child's lessons at the parent portal.</p>
  <a href="/parent/login" class="btn btn-outline" target="_blank">👁️ View Parent Portal</a>
</div>"""
    return HTMLResponse(page("Admin", content, "admin"))


@app.get("/admin/users", response_class=HTMLResponse)
def admin_users_page(request: Request, msg: str = ""):
    users = get_all_users()
    msg_html = f'<div class="alert alert-success">{msg}</div>' if msg else ''

    rows = ""
    for u in sorted(users, key=lambda x: x.get('created_at', ''), reverse=True):
        uid     = u.get('id', '')
        is_admin = u.get('is_admin') == 'true'
        is_beta  = u.get('is_beta_tester') == 'true'
        role_badge = ('<span class="badge badge-info">Admin</span>' if is_admin
                      else '<span class="badge badge-warning">Beta Tester</span>')
        promote_btn = "" if is_admin else (
            f'<form action="/admin/users/{uid}/promote" method="post" style="display:inline;">'
            f'<button type="submit" class="btn btn-sm" onclick="return confirm(\'Promote {u.get("name","")} to admin?\')">⬆️ Promote</button>'
            f'</form>'
        )
        delete_btn = "" if uid == "1" else (  # protect seed admin (id=1)
            f'<form action="/admin/users/{uid}/delete" method="post" style="display:inline;">'
            f'<button type="submit" class="btn btn-danger btn-sm" onclick="return confirm(\'Delete {u.get("name","")}?\')">🗑️</button>'
            f'</form>'
        )
        rows += f"""<tr>
  <td><strong>{u.get('name','')}</strong></td>
  <td style="font-size:12px;">{u.get('email','')}</td>
  <td>{role_badge}</td>
  <td style="font-size:12px;color:var(--muted);">{u.get('created_at','')}</td>
  <td style="display:flex;gap:4px;flex-wrap:wrap;">{promote_btn}{delete_btn}</td>
</tr>"""

    if not rows:
        rows = '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px;">No users yet.</td></tr>'

    beta_count  = sum(1 for u in users if u.get('is_beta_tester') == 'true')
    admin_count = sum(1 for u in users if u.get('is_admin') == 'true')

    content = f"""{msg_html}
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">👥</div>
    <div class="stat-val">{len(users)}</div><div class="stat-lbl">Total Users</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fef3c7;">🧪</div>
    <div class="stat-val">{beta_count}</div><div class="stat-lbl">Beta Testers</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">🔐</div>
    <div class="stat-val">{admin_count}</div><div class="stat-lbl">Admins</div></div>
</div>
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">👤 All Users</h2>
    <a href="/signup" class="btn btn-outline btn-sm" target="_blank">🔗 Share Signup</a>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Joined</th><th>Actions</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""
    return HTMLResponse(page("User Management", content, "users"))


@app.post("/admin/users/{user_id}/promote")
def admin_promote_user(user_id: str):
    users = get_all_users()
    for u in users:
        if u.get('id') == user_id:
            u['is_admin']       = 'true'
            u['is_beta_tester'] = 'false'
            break
    save_all_users(users)
    return RedirectResponse(url="/admin/users?msg=User+promoted+to+admin", status_code=303)


@app.post("/admin/users/{user_id}/delete")
def admin_delete_user(user_id: str):
    if user_id == "1":  # never delete the seed admin
        return RedirectResponse(url="/admin/users?msg=Cannot+delete+the+primary+admin+account", status_code=303)
    users = [u for u in get_all_users() if u.get('id') != user_id]
    save_all_users(users)
    return RedirectResponse(url="/admin/users?msg=User+deleted", status_code=303)


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


MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
MONTH_SHORT  = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


@app.get("/invoices", response_class=HTMLResponse)
def invoices_page():
    invoices = get_all_invoices()
    invoices_sorted = sorted(
        invoices,
        key=lambda x: (x.get('Year', ''), x.get('Month', '').zfill(2), x.get('Student', '')),
        reverse=True,
    )

    unpaid = [i for i in invoices if i.get('Status') == 'Unpaid']
    paid   = [i for i in invoices if i.get('Status') == 'Paid']
    total_outstanding = sum(float(i.get('BalanceDue', 0)) for i in unpaid)

    rows = ""
    for inv in invoices_sorted:
        m = int(inv.get('Month', 1))
        month_label = f"{MONTH_SHORT[m]} {inv.get('Year', '')}"
        status  = inv.get('Status', 'Unpaid')
        badge   = 'badge-success' if status == 'Paid' else 'badge-warning'
        balance = float(inv.get('BalanceDue', 0))
        bal_color = 'color:var(--success);' if balance <= 0 else 'color:var(--danger);'
        inv_id  = inv.get('ID', '')
        rows += f"""<tr>
  <td><a href="/invoices/{inv_id}" style="color:var(--primary);font-weight:600;">#INV-{inv_id.zfill(4)}</a></td>
  <td><strong>{inv.get('Student', '')}</strong></td>
  <td>{month_label}</td>
  <td>{inv.get('LessonsCount', 0)}</td>
  <td>${float(inv.get('TotalAmount', 0)):.2f}</td>
  <td>${float(inv.get('PaymentsApplied', 0)):.2f}</td>
  <td style="font-weight:700;{bal_color}">${balance:.2f}</td>
  <td><span class="badge {badge}">{status}</span></td>
  <td><a href="/invoices/{inv_id}" class="btn btn-outline btn-sm">View</a></td>
</tr>"""

    if not rows:
        rows = '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--muted);">No invoices yet — use the form below to generate.</td></tr>'

    now = datetime.now()
    prev_month = now.month - 1 if now.month > 1 else 12
    prev_year  = now.year if now.month > 1 else now.year - 1
    month_options = "".join(
        f'<option value="{i}"{" selected" if i == prev_month else ""}>{MONTH_NAMES[i]}</option>'
        for i in range(1, 13)
    )

    content = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">🧾</div>
    <div class="stat-val">{len(invoices)}</div><div class="stat-lbl">Total Invoices</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fee2e2;">⏳</div>
    <div class="stat-val">{len(unpaid)}</div><div class="stat-lbl">Unpaid</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">✅</div>
    <div class="stat-val">{len(paid)}</div><div class="stat-lbl">Paid</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fef3c7;">💰</div>
    <div class="stat-val">${total_outstanding:.2f}</div><div class="stat-lbl">Outstanding</div></div>
</div>

<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">🧾 Invoices</h2>
    <a href="/invoices" class="btn btn-outline btn-sm">🔄 Refresh</a>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Invoice</th><th>Student</th><th>Period</th><th>Lessons</th><th>Total</th><th>Applied</th><th>Balance Due</th><th>Status</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>

<div class="card" style="max-width:480px;">
  <h2>⚡ Generate Invoices</h2>
  <p style="color:var(--muted);font-size:13px;margin-bottom:16px;">Creates one invoice per student for all confirmed lessons in the selected month. Skips months already invoiced.</p>
  <form action="/generate-invoices" method="post">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;">
        <label class="form-label">Month</label>
        <select name="month">{month_options}</select>
      </div>
      <div class="form-group" style="margin:0;">
        <label class="form-label">Year</label>
        <input type="number" name="year" value="{prev_year}" min="2020" max="2035" required>
      </div>
    </div>
    <button type="submit" class="btn" style="margin-top:14px;">⚡ Generate Invoices</button>
  </form>
</div>"""
    return HTMLResponse(page("Invoices", content, "invoices"))


@app.post("/generate-invoices")
def generate_invoices_post(month: int = Form(...), year: int = Form(...)):
    count = generate_invoices_for_month(year, month)
    period = f"{MONTH_NAMES[month]} {year}"
    if count > 0:
        msg = f"Generated {count} invoice(s) for {period}."
        icon = "✅"
        heading = "Invoices Generated"
    else:
        msg = f"No new invoices for {period}. Either no confirmed lessons exist or invoices were already generated."
        icon = "ℹ️"
        heading = "Nothing to Generate"
    content = f"""<div class="card" style="max-width:480px;text-align:center;">
  <div style="font-size:48px;margin-bottom:12px;">{icon}</div>
  <h2>{heading}</h2>
  <p style="color:var(--muted);margin:12px 0;">{msg}</p>
  <a href="/invoices" class="btn" style="margin-top:8px;">← View All Invoices</a>
</div>"""
    return HTMLResponse(page("Generate Invoices", content, "invoices"))


@app.get("/invoices/{invoice_id}", response_class=HTMLResponse)
def invoice_detail(invoice_id: str):
    invoices = get_all_invoices()
    inv = next((i for i in invoices if i.get('ID') == invoice_id), None)
    if not inv:
        return RedirectResponse(url="/invoices", status_code=303)

    m           = int(inv.get('Month', 1))
    month_label = f"{MONTH_NAMES[m]} {inv.get('Year', '')}"
    student     = inv.get('Student', '')
    lessons     = int(inv.get('LessonsCount', 0))
    total       = float(inv.get('TotalAmount', 0))
    applied     = float(inv.get('PaymentsApplied', 0))
    balance     = float(inv.get('BalanceDue', 0))
    status      = inv.get('Status', 'Unpaid')
    rate        = total / lessons if lessons > 0 else 0

    status_badge = (
        '<span class="badge badge-success" style="font-size:14px;padding:5px 14px;">✅ Paid</span>'
        if status == 'Paid' else
        '<span class="badge badge-warning" style="font-size:14px;padding:5px 14px;">⏳ Unpaid</span>'
    )
    paid_row = (
        f'<tr><td style="color:var(--muted);padding:6px 12px;">Paid On</td>'
        f'<td style="padding:6px 12px;"><strong>{inv.get("PaidDate","")}</strong></td></tr>'
        if status == 'Paid' and inv.get('PaidDate') else ''
    )
    mark_paid_btn = (
        '' if status == 'Paid' else
        f'<form action="/mark-invoice-paid/{invoice_id}" method="post" style="display:inline;">'
        f'<button type="submit" class="btn btn-success">✅ Mark as Paid</button></form>'
    )
    bal_color = 'color:var(--success);' if balance <= 0 else 'color:var(--danger);'

    content = f"""
<div class="card" style="max-width:600px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;flex-wrap:wrap;gap:12px;">
    <div>
      <h2 style="margin:0;">Invoice #INV-{invoice_id.zfill(4)}</h2>
      <div style="color:var(--muted);font-size:13px;margin-top:4px;">Created {inv.get('CreatedDate','')}</div>
    </div>
    {status_badge}
  </div>

  <div style="background:var(--bg);border-radius:10px;padding:16px;margin-bottom:20px;">
    <table style="border:none;">
      <tbody>
        <tr><td style="color:var(--muted);width:130px;padding:5px 12px;border:none;">Student</td>
            <td style="padding:5px 12px;border:none;"><strong>{student}</strong></td></tr>
        <tr><td style="color:var(--muted);padding:5px 12px;border:none;">Period</td>
            <td style="padding:5px 12px;border:none;"><strong>{month_label}</strong></td></tr>
        {paid_row}
      </tbody>
    </table>
  </div>

  <div style="border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:20px;">
    <table>
      <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
      <tbody>
        <tr>
          <td>{lessons} lesson{"s" if lessons != 1 else ""} × ${rate:.2f}/lesson</td>
          <td style="text-align:right;font-weight:600;">${total:.2f}</td>
        </tr>
        <tr>
          <td style="color:var(--success);">Payments Applied</td>
          <td style="text-align:right;color:var(--success);font-weight:600;">−${applied:.2f}</td>
        </tr>
        <tr style="border-top:2px solid var(--border);">
          <td style="font-weight:700;font-size:15px;padding:12px 13px;">Balance Due</td>
          <td style="text-align:right;font-weight:800;font-size:18px;padding:12px 13px;{bal_color}">${balance:.2f}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    {mark_paid_btn}
    <a href="/invoices" class="btn btn-outline">← All Invoices</a>
  </div>
</div>"""
    return HTMLResponse(page(f"Invoice #INV-{invoice_id.zfill(4)}", content, "invoices"))


@app.post("/mark-invoice-paid/{invoice_id}")
def mark_invoice_paid(invoice_id: str):
    invoices = get_all_invoices()
    for inv in invoices:
        if inv.get('ID') == invoice_id:
            inv['Status']   = 'Paid'
            inv['PaidDate'] = datetime.now().strftime('%Y-%m-%d')
            inv['BalanceDue'] = '0.00'
            break
    save_all_invoices(invoices)
    return RedirectResponse(url=f"/invoices/{invoice_id}", status_code=303)


# ─── Student Portal ───────────────────────────────────────────────────────────

def _get_student_name(request: Request) -> str:
    """Decode the student name from the session cookie."""
    return _url_decode(request.cookies.get("student_session", ""))


@app.get("/student/login", response_class=HTMLResponse)
def student_login_page(error: str = ""):
    profiles = get_all_profiles()
    err = f'<div class="alert alert-danger">{error}</div>' if error else ''
    if profiles:
        options = "".join(
            f'<option value="{n}">{n}</option>'
            for n in sorted(profiles.keys())
        )
        form_html = f"""
    <form action="/student/login" method="post">
      <div class="form-group">
        <label class="form-label">Your Name</label>
        <select name="student_name" required>
          <option value="">Select your name…</option>
          {options}
        </select>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;margin-top:4px;background:linear-gradient(135deg,#10b981,#059669);">
        Enter Portal
      </button>
    </form>"""
    else:
        form_html = '<div class="alert alert-warning">No students are registered yet. Please contact your instructor.</div>'

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Student Portal — Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo" style="background:linear-gradient(135deg,#10b981,#059669);">🎵</div>
    <h1 style="text-align:center;margin-bottom:4px;">Student Portal</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">
      View your lessons, balance, and history
    </p>
    {err}
    {form_html}
    <div style="margin-top:24px;padding-top:18px;border-top:1px solid var(--border);text-align:center;">
      <a href="/login" style="font-size:12px;color:var(--muted);">Staff login →</a>
    </div>
  </div>
</div>
</body>
</html>""")


@app.post("/student/login")
def student_login_post(student_name: str = Form(...)):
    profiles = get_all_profiles()
    if student_name not in profiles:
        return RedirectResponse(url="/student/login?error=Name+not+found.+Please+select+your+name.", status_code=303)
    response = RedirectResponse(url="/student/dashboard", status_code=303)
    response.set_cookie(
        key="student_session",
        value=_url_encode(student_name, safe=""),
        httponly=True,
        max_age=86400,
    )
    return response


@app.get("/student/logout")
def student_logout():
    response = RedirectResponse(url="/student/login", status_code=303)
    response.delete_cookie("student_session")
    return response


@app.get("/student/dashboard", response_class=HTMLResponse)
def student_dashboard(request: Request):
    student_name = _get_student_name(request)
    profiles = get_all_profiles()
    student = profiles.get(student_name, {})
    prepaid  = student.get("prepaid", 0)
    rate     = student.get("rate", DEFAULT_RATE) or DEFAULT_RATE
    lessons_remaining = int(prepaid / rate)

    # All lessons for this student from the ledger
    all_lessons = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            for row in _ledger_reader(f):
                if row.get("Student", "") == student_name:
                    all_lessons.append(row)
    all_lessons.sort(key=lambda x: x.get("Date", ""), reverse=True)

    confirmed_total = sum(1 for l in all_lessons if l.get("Status") in ATTENDED_STATUSES)
    missed_total    = sum(1 for l in all_lessons if l.get("Status") in MISSED_STATUSES)

    # This-month count
    now = datetime.now()
    this_month = sum(
        1 for l in all_lessons
        if l.get("Status") in ATTENDED_STATUSES
        and l.get("Date", "")[:7] == now.strftime("%Y-%m")
    )

    # Upcoming lessons from Google Calendar
    upcoming_html = next_lesson_html = ""
    try:
        import pytz
        service = get_calendar_service()
        if service:
            tz = pytz.timezone("America/New_York")
            now_tz  = datetime.now(tz)
            end_utc = (now_tz + timedelta(days=60)).astimezone(pytz.UTC).isoformat()
            events  = service.events().list(
                calendarId="primary",
                timeMin=now_tz.astimezone(pytz.UTC).isoformat(),
                timeMax=end_utc,
                singleEvents=True, orderBy="startTime",
            ).execute().get("items", [])
            aliases    = student.get("aliases", [])
            my_events  = [e for e in events if matches_student(e.get("summary", ""), student_name, aliases)]
            if my_events:
                first_st = my_events[0].get("start", {}).get("dateTime", "")
                if first_st:
                    try:
                        st_dt  = datetime.fromisoformat(first_st.replace("Z", "+00:00")).astimezone(tz)
                        days   = (st_dt.date() - now_tz.date()).days
                        when   = "Today" if days == 0 else ("Tomorrow" if days == 1 else f"In {days} days")
                        next_lesson_html = (
                            f'<div class="alert alert-info" style="margin-bottom:18px;">'
                            f'📅 Next lesson: <strong>{st_dt.strftime("%A, %B %-d")} at {format_standard_time(first_st)}</strong>'
                            f' &mdash; {when}</div>'
                        )
                    except Exception:
                        pass
            for e in my_events[:4]:
                st = e.get("start", {}).get("dateTime", "All day")
                try:
                    dt_local = datetime.fromisoformat(st.replace("Z", "+00:00")).astimezone(tz)
                    date_str = dt_local.strftime("%a, %b %-d")
                except Exception:
                    date_str = st[:10]
                upcoming_html += (
                    f'<div class="event-item">'
                    f'<div class="event-name">🎵 Lesson</div>'
                    f'<div class="event-meta">{date_str} &middot; {format_standard_time(st)}</div>'
                    f'</div>'
                )
    except Exception:
        pass
    if not upcoming_html:
        upcoming_html = '<p style="color:var(--muted);font-size:13px;">No upcoming lessons found in calendar.</p>'

    # Recent history rows
    history_rows = ""
    for l in all_lessons[:6]:
        s = l.get("Status", "")
        badge = "badge-success" if s in ATTENDED_STATUSES else ("badge-danger" if s in MISSED_STATUSES else "badge-muted")
        history_rows += (
            f'<tr><td>{l.get("Date","")}</td>'
            f'<td><span class="badge {badge}">{s}</span></td>'
            f'<td>${_safe_float(l.get("AmountCharged", 0)):.2f}</td></tr>'
        )
    if not history_rows:
        history_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:16px;">No lessons recorded yet.</td></tr>'

    bal_color = "var(--success)" if prepaid > 0 else "var(--danger)"
    content = f"""
{next_lesson_html}
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon" style="background:#d1fae5;">💰</div>
    <div class="stat-val" style="color:{bal_color};">${prepaid:.2f}</div>
    <div class="stat-lbl">Prepaid Balance</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#e0e7ff;">📚</div>
    <div class="stat-val">{lessons_remaining}</div>
    <div class="stat-lbl">Lessons Remaining</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#d1fae5;">✅</div>
    <div class="stat-val">{confirmed_total}</div>
    <div class="stat-lbl">Lessons Completed</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#fef3c7;">🗓️</div>
    <div class="stat-val">{this_month}</div>
    <div class="stat-lbl">This Month</div>
  </div>
</div>

<div class="two-col">
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">📅 Upcoming Lessons</h3>
      <a href="/student/lessons" class="btn btn-outline btn-sm">See All</a>
    </div>
    {upcoming_html}
  </div>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">📋 Recent History</h3>
      <a href="/student/lessons" class="btn btn-outline btn-sm">Full History</a>
    </div>
    <table>
      <thead><tr><th>Date</th><th>Status</th><th>Amount</th></tr></thead>
      <tbody>{history_rows}</tbody>
    </table>
  </div>
</div>
"""
    return HTMLResponse(student_page(f"Welcome, {student_name}!", content, student_name, "dashboard"))


@app.get("/student/lessons", response_class=HTMLResponse)
def student_lessons(request: Request):
    student_name = _get_student_name(request)
    profiles = get_all_profiles()
    student  = profiles.get(student_name, {})
    aliases  = student.get("aliases", [])

    # All past lessons from ledger
    all_lessons = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            for row in _ledger_reader(f):
                if row.get("Student", "") == student_name:
                    all_lessons.append(row)
    all_lessons.sort(key=lambda x: x.get("Date", ""), reverse=True)

    # Upcoming from calendar (next 90 days)
    upcoming_html = ""
    try:
        import pytz
        service = get_calendar_service()
        if service:
            tz     = pytz.timezone("America/New_York")
            now_tz = datetime.now(tz)
            events = service.events().list(
                calendarId="primary",
                timeMin=now_tz.astimezone(pytz.UTC).isoformat(),
                timeMax=(now_tz + timedelta(days=90)).astimezone(pytz.UTC).isoformat(),
                singleEvents=True, orderBy="startTime",
            ).execute().get("items", [])
            for e in events:
                if not matches_student(e.get("summary", ""), student_name, aliases):
                    continue
                st = e.get("start", {}).get("dateTime", "All day")
                et = e.get("end",   {}).get("dateTime", "")
                duration = 60
                if st and "T" in st and et and "T" in et:
                    try:
                        duration = int((
                            datetime.fromisoformat(et.replace("Z", "+00:00")) -
                            datetime.fromisoformat(st.replace("Z", "+00:00"))
                        ).total_seconds() / 60)
                    except Exception:
                        pass
                try:
                    dt_local = datetime.fromisoformat(st.replace("Z", "+00:00")).astimezone(tz)
                    date_str = dt_local.strftime("%A, %B %-d, %Y")
                except Exception:
                    date_str = st[:10]
                upcoming_html += (
                    f'<div class="event-item">'
                    f'<div class="event-name">🎵 {date_str}</div>'
                    f'<div class="event-meta">{format_standard_time(st)} &middot; {duration} min</div>'
                    f'</div>'
                )
    except Exception:
        pass
    if not upcoming_html:
        upcoming_html = '<p style="color:var(--muted);font-size:13px;">No upcoming lessons found in calendar.</p>'

    # History table
    history_rows = ""
    for l in all_lessons:
        s = l.get("Status", "")
        if s in ATTENDED_STATUSES:
            badge, emoji = "badge-success", "✅"
        elif s in MISSED_STATUSES:
            badge, emoji = "badge-danger", "❌"
        elif s in ZERO_CHARGE_STATUSES:
            badge, emoji = "badge-muted", "🔄"
        else:
            badge, emoji = "badge-warning", "⚠️"
        note = (l.get("Notes", "") or "")[:55]
        history_rows += (
            f'<tr><td>{l.get("Date","")}</td>'
            f'<td><span class="badge {badge}">{emoji} {s}</span></td>'
            f'<td>${_safe_float(l.get("AmountCharged", 0)):.2f}</td>'
            f'<td style="color:var(--muted);font-size:11px;">{note}</td></tr>'
        )
    if not history_rows:
        history_rows = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:20px;">No lesson history yet.</td></tr>'

    content = f"""
<div class="card">
  <div class="card-header"><h2 style="margin:0;">📅 Upcoming Lessons</h2></div>
  {upcoming_html}
</div>
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">📋 Lesson History</h2>
    <span style="color:var(--muted);font-size:12px;">{len(all_lessons)} total</span>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Date</th><th>Status</th><th>Amount</th><th>Notes</th></tr></thead>
      <tbody>{history_rows}</tbody>
    </table>
  </div>
</div>
"""
    return HTMLResponse(student_page("My Lessons", content, student_name, "lessons"))


@app.get("/student/payments", response_class=HTMLResponse)
def student_payments(request: Request):
    student_name = _get_student_name(request)
    profiles = get_all_profiles()
    student  = profiles.get(student_name, {})
    prepaid  = student.get("prepaid", 0)
    rate     = student.get("rate", DEFAULT_RATE) or DEFAULT_RATE
    target_minutes    = student.get("target_minutes", 60)
    lessons_remaining = int(prepaid / rate)

    # Charged lesson activity (proxy for account activity)
    activity = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, "r") as f:
            for row in _ledger_reader(f):
                if row.get("Student", "") == student_name and _safe_float(row.get("AmountCharged", 0)) > 0:
                    activity.append(row)
    activity.sort(key=lambda x: x.get("Date", ""), reverse=True)
    total_charged = sum(_safe_float(r.get("AmountCharged", 0)) for r in activity)

    activity_rows = ""
    for r in activity:
        s = r.get("Status", "")
        badge = "badge-success" if s in ("Confirmed", "Attended") else "badge-danger"
        note  = (r.get("Notes", "") or "")[:55]
        activity_rows += (
            f'<tr><td>{r.get("Date","")}</td>'
            f'<td><span class="badge {badge}">{s}</span></td>'
            f'<td style="font-weight:600;color:var(--danger);">−${_safe_float(r.get("AmountCharged",0)):.2f}</td>'
            f'<td style="color:var(--muted);font-size:11px;">{note}</td></tr>'
        )
    if not activity_rows:
        activity_rows = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:20px;">No charges yet.</td></tr>'

    bal_bg    = "#d1fae5" if prepaid > 0 else "#fee2e2"
    bal_color = "#065f46" if prepaid > 0 else "#991b1b"

    content = f"""
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon" style="background:{bal_bg};">💰</div>
    <div class="stat-val" style="color:{bal_color};">${prepaid:.2f}</div>
    <div class="stat-lbl">Current Balance</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#e0e7ff;">📚</div>
    <div class="stat-val">{lessons_remaining}</div>
    <div class="stat-lbl">Lessons Remaining</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#fef3c7;">💲</div>
    <div class="stat-val">${rate:.0f}</div>
    <div class="stat-lbl">Per Lesson ({target_minutes} min)</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#fee2e2;">📊</div>
    <div class="stat-val">${total_charged:.0f}</div>
    <div class="stat-lbl">Total Charged</div>
  </div>
</div>

<div class="card">
  <h2>💳 Account Balance</h2>
  <div style="background:{bal_bg};border-radius:12px;padding:24px;text-align:center;margin-bottom:14px;">
    <div style="font-size:44px;font-weight:800;color:{bal_color};">${prepaid:.2f}</div>
    <div style="color:{bal_color};font-size:14px;margin-top:8px;">
      {lessons_remaining} lesson{"s" if lessons_remaining != 1 else ""} remaining at ${rate:.0f}/lesson
    </div>
  </div>
  <p style="color:var(--muted);font-size:12px;">To add funds to your account, please contact your instructor.</p>
</div>

<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">📋 Lesson Charges</h2>
    <span style="color:var(--muted);font-size:12px;">{len(activity)} lessons charged</span>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Date</th><th>Status</th><th>Charged</th><th>Notes</th></tr></thead>
      <tbody>{activity_rows}</tbody>
    </table>
  </div>
</div>
"""
    return HTMLResponse(student_page("My Payments", content, student_name, "payments"))


@app.get("/static/style.css")
def serve_css():
    """Serve the CSS file"""
    return Response(content=css_content, media_type="text/css")


# ─── Parent Portal ────────────────────────────────────────────────────────────

PARENTS_FILE = "/data/parents.csv"
PARENT_HEADERS = ["id", "name", "email", "password_hash", "student_names", "created_at"]

BLOCKED_DATES_FILE = "/data/blocked_dates.csv"
BLOCKED_DATES_HEADERS = ["id", "student_name", "date", "reason", "status", "parent_email", "created_at"]

LESSON_NOTES_FILE = "/data/lesson_notes.csv"
LESSON_NOTES_HEADERS = ["id", "student_name", "lesson_date", "notes", "assignment", "created_by", "created_at"]

for _fp, _hdr in [
    (PARENTS_FILE, PARENT_HEADERS),
    (BLOCKED_DATES_FILE, BLOCKED_DATES_HEADERS),
    (LESSON_NOTES_FILE, LESSON_NOTES_HEADERS),
]:
    if not os.path.exists(_fp):
        with open(_fp, 'w', newline='') as _f:
            csv.writer(_f).writerow(_hdr)


def get_all_parents():
    rows = []
    if os.path.exists(PARENTS_FILE):
        with open(PARENTS_FILE, 'r') as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
    return rows


def save_all_parents(parents):
    with open(PARENTS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=PARENT_HEADERS)
        writer.writeheader()
        for p in parents:
            writer.writerow({k: p.get(k, '') for k in PARENT_HEADERS})


def get_blocked_dates():
    rows = []
    if os.path.exists(BLOCKED_DATES_FILE):
        with open(BLOCKED_DATES_FILE, 'r') as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
    return rows


def save_blocked_dates(rows):
    with open(BLOCKED_DATES_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=BLOCKED_DATES_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in BLOCKED_DATES_HEADERS})


def get_lesson_notes():
    rows = []
    if os.path.exists(LESSON_NOTES_FILE):
        with open(LESSON_NOTES_FILE, 'r') as f:
            for row in csv.DictReader(f):
                rows.append(dict(row))
    return rows


def save_lesson_notes(rows):
    with open(LESSON_NOTES_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=LESSON_NOTES_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, '') for k in LESSON_NOTES_HEADERS})


def _get_parent_email(request: Request) -> str:
    return request.cookies.get("parent_session", "")


def _get_parent(request: Request):
    email = _get_parent_email(request)
    if not email:
        return None
    parents = get_all_parents()
    return next((p for p in parents if p.get('email', '').lower() == email.lower()), None)


def _parent_students(parent: dict) -> list:
    raw = parent.get('student_names', '')
    return [s.strip() for s in raw.split(';') if s.strip()]


def parent_page(title: str, content: str, parent_name: str, active: str = "dashboard") -> str:
    links = [
        ("dashboard", "/parent/dashboard", "🏠", "Dashboard"),
        ("schedule",  "/parent/schedule",  "📅", "Schedule"),
        ("notes",     "/parent/notes",     "📝", "Lesson Notes"),
        ("invoices",  "/parent/invoices",  "🧾", "Invoices"),
        ("payments",  "/parent/payments",  "💳", "Payments"),
        ("profile",   "/parent/profile",   "👤", "My Profile"),
    ]
    nav_html = ""
    for k, href, icon, label in links:
        cls = "nav-link active" if k == active else "nav-link"
        nav_html += f'<a href="{href}" class="{cls}"><span class="nav-icon">{icon}</span>{label}</a>\n'
    initials = "".join(p[0].upper() for p in parent_name.split()[:2]) or "P"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Parent Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
<style>
:root{{--primary:#7c3aed;--primary-dark:#6d28d9;--secondary:#a855f7;}}
.sidebar{{background:#3b0764;}}
.nav-link.active{{background:linear-gradient(135deg,#7c3aed,#a855f7);box-shadow:0 2px 8px rgba(124,58,237,.4);}}
</style>
</head>
<body>
<div class="sidebar-overlay" id="overlay" onclick="closeSidebar()"></div>
<div class="layout">
<aside class="sidebar" id="sidebar">
  <div class="sidebar-brand">
    <div class="brand-icon" style="background:linear-gradient(135deg,#7c3aed,#a855f7);font-size:14px;font-weight:800;">{initials}</div>
    <div><div class="brand-name">{parent_name}</div><div class="brand-sub">Parent Portal</div></div>
  </div>
  <nav class="sidebar-nav">
    <div class="nav-group">
      <div class="nav-group-label">My Studio</div>
      {nav_html}
    </div>
  </nav>
  <div class="sidebar-footer">
    <a href="/parent/logout" class="nav-link"><span class="nav-icon">🚪</span>Logout</a>
  </div>
</aside>
<div class="main">
  <header class="topbar">
    <div style="display:flex;align-items:center;gap:10px;">
      <button class="menu-btn" onclick="openSidebar()">☰</button>
      <span class="topbar-title">{title}</span>
    </div>
    <div class="topbar-right">
      <span style="font-size:12px;color:var(--muted);padding:4px 10px;background:var(--bg);border-radius:20px;">🎵 Parent Portal</span>
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


@app.get("/parent/login", response_class=HTMLResponse)
def parent_login_page(error: str = "", success: str = ""):
    err  = f'<div class="alert alert-danger">{error}</div>'   if error   else ''
    succ = f'<div class="alert alert-success">{success}</div>' if success else ''
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Parent Portal — Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo" style="background:linear-gradient(135deg,#7c3aed,#a855f7);">👨‍👩‍👧</div>
    <h1 style="text-align:center;margin-bottom:4px;">Parent Portal</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Manage your child's lessons, billing &amp; schedule</p>
    {err}{succ}
    <form action="/parent/login" method="post">
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" name="email" placeholder="parent@email.com" required>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;background:linear-gradient(135deg,#7c3aed,#a855f7);">Sign In</button>
    </form>
    <div style="margin-top:14px;text-align:center;">
      <a href="/parent/register" style="font-size:12px;color:#7c3aed;">No account? Register here →</a>
    </div>
    <div style="margin-top:16px;padding-top:14px;border-top:1px solid var(--border);display:flex;gap:16px;justify-content:center;">
      <a href="/login" style="font-size:12px;color:var(--muted);">Staff login →</a>
      <a href="/student/login" style="font-size:12px;color:var(--muted);">Student portal →</a>
    </div>
  </div>
</div>
</body>
</html>""")


@app.post("/parent/login")
def parent_login_post(email: str = Form(...), password: str = Form(...)):
    email = email.strip().lower()
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    parents = get_all_parents()
    parent = next((p for p in parents if p.get('email', '').lower() == email and p.get('password_hash') == pw_hash), None)
    if not parent:
        return RedirectResponse(url="/parent/login?error=Invalid+email+or+password", status_code=303)
    response = RedirectResponse(url="/parent/dashboard", status_code=303)
    response.set_cookie(key="parent_session", value=email, httponly=True, max_age=86400 * 30)
    return response


@app.get("/parent/register", response_class=HTMLResponse)
def parent_register_page(error: str = ""):
    profiles = get_all_profiles()
    err = f'<div class="alert alert-danger">{error}</div>' if error else ''
    checkboxes = ""
    for sname in sorted(profiles.keys()):
        checkboxes += (
            f'<label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;'
            f'cursor:pointer;border:1px solid var(--border);margin-bottom:6px;font-size:13px;">'
            f'<input type="checkbox" name="students" value="{sname}" style="width:auto;margin:0;"> {sname}</label>'
        )
    if not checkboxes:
        checkboxes = '<p style="color:var(--muted);font-size:13px;">No students registered yet. Please contact your instructor first.</p>'
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Register — Parent Portal</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card" style="max-width:460px;">
    <div class="login-logo" style="background:linear-gradient(135deg,#7c3aed,#a855f7);">👨‍👩‍👧</div>
    <h1 style="text-align:center;margin-bottom:4px;">Create Account</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Parent / Guardian Registration</p>
    {err}
    <form action="/parent/register" method="post">
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" name="name" placeholder="Your full name" required>
      </div>
      <div class="form-group">
        <label class="form-label">Email Address</label>
        <input type="email" name="email" placeholder="parent@email.com" required>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="At least 8 characters" required minlength="8">
      </div>
      <div class="form-group">
        <label class="form-label">Confirm Password</label>
        <input type="password" name="confirm_password" placeholder="Repeat password" required>
      </div>
      <div class="form-group">
        <label class="form-label">My Child(ren) — select all that apply</label>
        {checkboxes}
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;background:linear-gradient(135deg,#7c3aed,#a855f7);">Create Account</button>
    </form>
    <div style="margin-top:16px;text-align:center;border-top:1px solid var(--border);padding-top:14px;">
      <a href="/parent/login" style="font-size:12px;color:#7c3aed;">Already have an account? Sign in →</a>
    </div>
  </div>
</div>
</body>
</html>""")


@app.post("/parent/register")
async def parent_register_post(request: Request, name: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    form = await request.form()
    students_selected = form.getlist("students")
    email = email.strip().lower()

    if password != confirm_password:
        return RedirectResponse(url="/parent/register?error=Passwords+do+not+match", status_code=303)
    if len(password) < 8:
        return RedirectResponse(url="/parent/register?error=Password+must+be+at+least+8+characters", status_code=303)

    parents = get_all_parents()
    if any(p.get('email', '').lower() == email for p in parents):
        return RedirectResponse(url="/parent/register?error=Email+already+registered", status_code=303)

    if not students_selected:
        return RedirectResponse(url="/parent/register?error=Please+select+at+least+one+student", status_code=303)

    profiles = get_all_profiles()
    valid_students = [s for s in students_selected if s in profiles]
    if not valid_students:
        return RedirectResponse(url="/parent/register?error=Selected+students+not+found", status_code=303)

    new_id = max((int(p.get('id', 0)) for p in parents), default=0) + 1
    parents.append({
        'id': str(new_id),
        'name': name.strip(),
        'email': email,
        'password_hash': hashlib.sha256(password.encode()).hexdigest(),
        'student_names': ';'.join(valid_students),
        'created_at': datetime.now().strftime('%Y-%m-%d'),
    })
    save_all_parents(parents)
    return RedirectResponse(url="/parent/login?success=Account+created.+Please+sign+in.", status_code=303)


@app.get("/parent/logout")
def parent_logout():
    response = RedirectResponse(url="/parent/login", status_code=303)
    response.delete_cookie("parent_session")
    return response


@app.get("/parent/dashboard", response_class=HTMLResponse)
def parent_dashboard(request: Request):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)
    profiles = get_all_profiles()
    now = datetime.now()
    total_balance = sum(profiles.get(s, {}).get('prepaid', 0) for s in my_students)

    children_html = ""
    for sname in my_students:
        student = profiles.get(sname, {})
        prepaid  = student.get('prepaid', 0)
        rate     = student.get('rate', DEFAULT_RATE) or DEFAULT_RATE
        lessons_remaining = int(prepaid / rate)

        this_month_count = 0
        if os.path.exists(LEDGER_FILE):
            with open(LEDGER_FILE, 'r') as f:
                for row in _ledger_reader(f):
                    if row.get('Student') == sname and row.get('Status') in ('Confirmed', 'Attended'):
                        try:
                            d = datetime.strptime(row.get('Date', ''), '%Y-%m-%d')
                            if d.year == now.year and d.month == now.month:
                                this_month_count += 1
                        except ValueError:
                            pass

        pending_blocks = [b for b in get_blocked_dates() if b.get('student_name') == sname and b.get('status') == 'pending']
        initials  = ''.join(p[0].upper() for p in sname.split()[:2])
        bal_color = 'var(--success)' if prepaid > 0 else 'var(--danger)'
        pending_badge = f'<span class="badge badge-warning" style="margin-left:8px;">{len(pending_blocks)} pending</span>' if pending_blocks else ''

        children_html += f"""
<div class="card" style="margin-bottom:14px;">
  <div style="display:flex;align-items:center;gap:14px;margin-bottom:14px;">
    <div class="student-avatar" style="width:46px;height:46px;font-size:16px;">{initials}</div>
    <div>
      <div style="font-size:16px;font-weight:700;">{sname}{pending_badge}</div>
      <div style="font-size:12px;color:var(--muted);">{student.get('description','') or 'Student'} &middot; ${rate:.0f}/lesson</div>
    </div>
  </div>
  <div class="stats-row" style="margin-bottom:14px;">
    <div class="stat-card" style="padding:12px;"><div class="stat-val" style="font-size:20px;color:{bal_color};">${prepaid:.2f}</div><div class="stat-lbl">Balance</div></div>
    <div class="stat-card" style="padding:12px;"><div class="stat-val" style="font-size:20px;">{lessons_remaining}</div><div class="stat-lbl">Remaining</div></div>
    <div class="stat-card" style="padding:12px;"><div class="stat-val" style="font-size:20px;">{this_month_count}</div><div class="stat-lbl">This Month</div></div>
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    <a href="/parent/schedule" class="btn btn-outline btn-sm">📅 Schedule</a>
    <a href="/parent/notes" class="btn btn-outline btn-sm">📝 Notes</a>
    <a href="/parent/invoices" class="btn btn-outline btn-sm">🧾 Invoices</a>
  </div>
</div>"""

    if not children_html:
        children_html = '<div class="alert alert-warning">No students linked to your account. Please contact your instructor.</div>'

    all_notes = get_lesson_notes()
    my_notes  = sorted([n for n in all_notes if n.get('student_name') in my_students],
                        key=lambda x: x.get('lesson_date', ''), reverse=True)

    recent_notes_html = ""
    for note in my_notes[:3]:
        recent_notes_html += f"""<div class="event-item">
  <div class="event-name">📝 {note.get('student_name','')} — {note.get('lesson_date','')}</div>
  <div class="event-meta" style="margin-top:4px;">{note.get('notes','')[:100]}</div>
  {f'<div class="event-meta" style="margin-top:2px;color:var(--primary);">Assignment: {note.get("assignment","")}</div>' if note.get('assignment') else ''}
</div>"""
    if not recent_notes_html:
        recent_notes_html = '<p style="color:var(--muted);font-size:13px;">No lesson notes yet.</p>'

    content = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#ede9fe;">👶</div>
    <div class="stat-val">{len(my_students)}</div><div class="stat-lbl">Children</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">💰</div>
    <div class="stat-val">${total_balance:.2f}</div><div class="stat-lbl">Total Balance</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">📝</div>
    <div class="stat-val">{len(my_notes)}</div><div class="stat-lbl">Lesson Notes</div></div>
</div>
<div class="two-col">
  <div>
    <h2 style="margin-bottom:14px;">My Children</h2>
    {children_html}
  </div>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">📝 Recent Notes</h3>
      <a href="/parent/notes" class="btn btn-outline btn-sm">All Notes</a>
    </div>
    {recent_notes_html}
  </div>
</div>"""
    return HTMLResponse(parent_page(f"Welcome, {parent_name}!", content, parent_name, "dashboard"))


@app.get("/parent/schedule", response_class=HTMLResponse)
def parent_schedule(request: Request, msg: str = ""):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)
    profiles    = get_all_profiles()
    msg_html    = f'<div class="alert alert-success">{msg}</div>' if msg else ''

    all_blocked = get_blocked_dates()
    my_blocked  = sorted([b for b in all_blocked if b.get('student_name') in my_students],
                          key=lambda x: x.get('date', ''), reverse=True)

    student_options = "".join(f'<option value="{s}">{s}</option>' for s in my_students)

    blocked_rows = ""
    for b in my_blocked:
        status = b.get('status', 'pending')
        badge_cls = 'badge-warning' if status == 'pending' else ('badge-success' if status == 'approved' else 'badge-danger')
        blocked_rows += f"""<tr>
  <td><strong>{b.get('student_name','')}</strong></td>
  <td>{b.get('date','')}</td>
  <td style="font-size:12px;color:var(--muted);">{b.get('reason','')[:60]}</td>
  <td><span class="badge {badge_cls}">{status}</span></td>
</tr>"""
    if not blocked_rows:
        blocked_rows = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:20px;">No requests submitted yet.</td></tr>'

    upcoming_rows = ""
    try:
        import pytz
        service = get_calendar_service()
        if service:
            tz     = pytz.timezone('America/New_York')
            now_tz = datetime.now(tz)
            events = service.events().list(
                calendarId='primary',
                timeMin=now_tz.astimezone(pytz.UTC).isoformat(),
                timeMax=(now_tz + timedelta(days=90)).astimezone(pytz.UTC).isoformat(),
                singleEvents=True, orderBy='startTime',
            ).execute().get('items', [])
            for e in events:
                for sname in my_students:
                    student_data = profiles.get(sname, {})
                    if matches_student(e.get('summary', ''), sname, student_data.get('aliases', [])):
                        st = e.get('start', {}).get('dateTime', '')
                        try:
                            dt_local = datetime.fromisoformat(st.replace('Z', '+00:00')).astimezone(tz)
                            date_val = dt_local.strftime('%Y-%m-%d')
                            display  = dt_local.strftime('%a, %b %-d')
                        except Exception:
                            date_val = st[:10]
                            display  = date_val
                        upcoming_rows += f"""<tr>
  <td>{sname}</td>
  <td>{display} — {format_standard_time(st)}</td>
  <td>
    <form action="/parent/block-date" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{sname}">
      <input type="hidden" name="date" value="{date_val}">
      <input type="hidden" name="reason" value="Parent requested cancellation">
      <button type="submit" class="btn btn-warning btn-sm" onclick="return confirm('Request cancellation for this lesson?')">🚫 Request Cancel</button>
    </form>
  </td>
</tr>"""
    except Exception:
        pass

    if not upcoming_rows:
        upcoming_rows = '<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:20px;">No upcoming lessons found in calendar.</td></tr>'

    content = f"""{msg_html}
<div class="two-col">
  <div>
    <div class="card">
      <h2>📅 Upcoming Lessons</h2>
      <p style="font-size:12px;color:var(--muted);margin-bottom:12px;">Click "Request Cancel" to notify your instructor of a conflict.</p>
      <div style="overflow-x:auto;">
        <table>
          <thead><tr><th>Student</th><th>Lesson</th><th>Action</th></tr></thead>
          <tbody>{upcoming_rows}</tbody>
        </table>
      </div>
    </div>
    <div class="card">
      <h2>🚫 Block a Date</h2>
      <p style="color:var(--muted);font-size:12px;margin-bottom:14px;">Submit a cancellation request or mark a date unavailable.</p>
      <form action="/parent/block-date" method="post">
        <div class="form-group"><label class="form-label">Student</label>
          <select name="student_name" required>
            <option value="">Select student…</option>
            {student_options}
          </select>
        </div>
        <div class="form-group"><label class="form-label">Date</label>
          <input type="date" name="date" required>
        </div>
        <div class="form-group"><label class="form-label">Reason (optional)</label>
          <input type="text" name="reason" placeholder="e.g. Family vacation, sick day">
        </div>
        <button type="submit" class="btn btn-warning">🚫 Submit Request</button>
      </form>
    </div>
  </div>
  <div class="card">
    <div class="card-header">
      <h3 class="card-title">📋 Cancellation Requests</h3>
    </div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Student</th><th>Date</th><th>Reason</th><th>Status</th></tr></thead>
        <tbody>{blocked_rows}</tbody>
      </table>
    </div>
  </div>
</div>"""
    return HTMLResponse(parent_page("Schedule & Cancellations", content, parent_name, "schedule"))


@app.post("/parent/block-date")
def parent_block_date(request: Request, student_name: str = Form(...), date: str = Form(...), reason: str = Form("")):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)
    if student_name not in _parent_students(parent):
        return RedirectResponse(url="/parent/schedule", status_code=303)

    rows   = get_blocked_dates()
    new_id = max((int(r.get('id', 0)) for r in rows), default=0) + 1
    rows.append({
        'id': str(new_id),
        'student_name': student_name,
        'date': date,
        'reason': reason or 'Parent requested cancellation',
        'status': 'pending',
        'parent_email': parent.get('email', ''),
        'created_at': datetime.now().strftime('%Y-%m-%d'),
    })
    save_blocked_dates(rows)
    return RedirectResponse(url="/parent/schedule?msg=Cancellation+request+submitted.+Your+instructor+will+review+it.", status_code=303)


@app.get("/parent/notes", response_class=HTMLResponse)
def parent_notes(request: Request):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)

    all_notes = get_lesson_notes()
    my_notes  = sorted([n for n in all_notes if n.get('student_name') in my_students],
                        key=lambda x: x.get('lesson_date', ''), reverse=True)

    notes_html = ""
    for note in my_notes:
        notes_html += f"""
<div class="card" style="margin-bottom:14px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;flex-wrap:wrap;gap:8px;">
    <div>
      <strong style="font-size:14px;">{note.get('student_name','')}</strong>
      <span style="color:var(--muted);font-size:12px;margin-left:10px;">📅 {note.get('lesson_date','')}</span>
    </div>
    <span style="font-size:11px;color:var(--muted);">By {note.get('created_by','Instructor')}</span>
  </div>
  <div style="background:var(--bg);border-radius:9px;padding:14px;font-size:13px;line-height:1.7;">
    {note.get('notes','').replace(chr(10), '<br>')}
  </div>
  {f'<div style="margin-top:10px;padding:10px 14px;background:#e0e7ff;border-radius:8px;font-size:12px;"><strong>📌 Assignment:</strong> {note.get("assignment","")}</div>' if note.get('assignment') else ''}
</div>"""

    if not notes_html:
        notes_html = '<div class="card"><p style="color:var(--muted);text-align:center;padding:30px;">No lesson notes yet. Notes will appear here after each lesson.</p></div>'

    content = f"""
<div style="margin-bottom:18px;">
  <h2>📝 Lesson Notes</h2>
  <p style="color:var(--muted);font-size:13px;margin-top:4px;">{len(my_notes)} note(s) for {', '.join(my_students) or 'your students'}</p>
</div>
{notes_html}"""
    return HTMLResponse(parent_page("Lesson Notes", content, parent_name, "notes"))


@app.get("/parent/invoices", response_class=HTMLResponse)
def parent_invoices(request: Request):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)

    all_invoices = get_all_invoices()
    my_invoices  = sorted(
        [inv for inv in all_invoices if inv.get('Student') in my_students],
        key=lambda x: (x.get('Year', ''), x.get('Month', '').zfill(2)), reverse=True
    )

    unpaid = [i for i in my_invoices if i.get('Status') == 'Unpaid']
    paid   = [i for i in my_invoices if i.get('Status') == 'Paid']
    total_outstanding = sum(float(i.get('BalanceDue', 0)) for i in unpaid)

    rows = ""
    for inv in my_invoices:
        m = int(inv.get('Month', 1))
        month_label = f"{MONTH_NAMES[m]} {inv.get('Year','')}"
        status  = inv.get('Status', 'Unpaid')
        badge   = 'badge-success' if status == 'Paid' else 'badge-warning'
        balance = float(inv.get('BalanceDue', 0))
        bal_style = 'color:var(--success);' if balance <= 0 else 'color:var(--danger);font-weight:700;'
        rows += f"""<tr>
  <td><strong>#INV-{inv.get('ID','').zfill(4)}</strong></td>
  <td>{inv.get('Student','')}</td>
  <td>{month_label}</td>
  <td>{inv.get('LessonsCount',0)}</td>
  <td>${float(inv.get('TotalAmount',0)):.2f}</td>
  <td style="{bal_style}">${balance:.2f}</td>
  <td><span class="badge {badge}">{status}</span></td>
</tr>"""

    if not rows:
        rows = '<tr><td colspan="7" style="text-align:center;color:var(--muted);padding:24px;">No invoices yet.</td></tr>'

    outstanding_card = ""
    if total_outstanding > 0:
        outstanding_card = f"""
<div class="card" style="border:2px solid var(--danger);margin-top:0;">
  <h3 style="color:var(--danger);margin-bottom:10px;">💳 Outstanding Balance: ${total_outstanding:.2f}</h3>
  <p style="color:var(--muted);font-size:13px;margin-bottom:14px;">Contact your instructor to make a payment or use the payment request form.</p>
  <a href="/parent/payments" class="btn btn-success">💳 Make Payment Request</a>
</div>"""

    content = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">🧾</div>
    <div class="stat-val">{len(my_invoices)}</div><div class="stat-lbl">Total Invoices</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fee2e2;">⏳</div>
    <div class="stat-val">{len(unpaid)}</div><div class="stat-lbl">Unpaid</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">✅</div>
    <div class="stat-val">{len(paid)}</div><div class="stat-lbl">Paid</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fef3c7;">💰</div>
    <div class="stat-val">${total_outstanding:.2f}</div><div class="stat-lbl">Outstanding</div></div>
</div>
{outstanding_card}
<div class="card">
  <div class="card-header"><h2 style="margin:0;">🧾 Your Invoices</h2></div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Invoice</th><th>Student</th><th>Period</th><th>Lessons</th><th>Total</th><th>Balance Due</th><th>Status</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""
    return HTMLResponse(parent_page("Invoices", content, parent_name, "invoices"))


@app.get("/parent/payments", response_class=HTMLResponse)
def parent_payments(request: Request, msg: str = ""):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)
    profiles    = get_all_profiles()
    msg_html    = f'<div class="alert alert-success">{msg}</div>' if msg else ''

    balance_cards = ""
    student_options = ""
    for sname in my_students:
        student = profiles.get(sname, {})
        prepaid  = student.get('prepaid', 0)
        rate     = student.get('rate', DEFAULT_RATE) or DEFAULT_RATE
        lessons_remaining = int(prepaid / rate)
        bal_bg    = '#d1fae5' if prepaid > 0 else '#fee2e2'
        bal_color = '#065f46' if prepaid > 0 else '#991b1b'
        balance_cards += f"""
<div class="stat-card">
  <div class="stat-icon" style="background:{bal_bg};">💰</div>
  <div class="stat-val" style="color:{bal_color};">${prepaid:.2f}</div>
  <div class="stat-lbl">{sname} — {lessons_remaining} lesson{'s' if lessons_remaining != 1 else ''} left</div>
</div>"""
        student_options += f'<option value="{sname}">{sname} (Balance: ${prepaid:.2f})</option>'

    content = f"""{msg_html}
<div class="stats-row" style="margin-bottom:22px;">{balance_cards}</div>
<div class="two-col">
  <div class="card">
    <h2>💳 Submit Payment Notification</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:16px;">Let your instructor know you've sent a payment. They will confirm and update your balance.</p>
    <form action="/parent/payments/request" method="post">
      <div class="form-group"><label class="form-label">Student</label>
        <select name="student_name" required>
          <option value="">Select student…</option>
          {student_options}
        </select>
      </div>
      <div class="form-group"><label class="form-label">Amount ($)</label>
        <input type="number" step="0.01" name="amount" placeholder="0.00" required>
      </div>
      <div class="form-group"><label class="form-label">Payment Method</label>
        <select name="method">
          <option>Venmo</option><option>Zelle</option><option>Cash</option><option>Check</option><option>Other</option>
        </select>
      </div>
      <div class="form-group"><label class="form-label">Notes (optional)</label>
        <input type="text" name="notes" placeholder="e.g. Monthly prepay for June">
      </div>
      <button type="submit" class="btn btn-success">💳 Submit Notification</button>
    </form>
  </div>
  <div class="card">
    <h2>ℹ️ How Payments Work</h2>
    <div style="font-size:13px;line-height:2;color:var(--dark);">
      <div>1. Submit a payment notification here</div>
      <div>2. Send the payment via your chosen method</div>
      <div>3. Your instructor confirms receipt</div>
      <div>4. Your prepaid balance is updated</div>
    </div>
    <div class="alert alert-info" style="margin-top:16px;font-size:12px;">
      Questions about billing? Contact your instructor directly.
    </div>
  </div>
</div>"""
    return HTMLResponse(parent_page("Payments", content, parent_name, "payments"))


@app.post("/parent/payments/request")
def parent_payment_request(request: Request, student_name: str = Form(...), amount: float = Form(...), method: str = Form(...), notes: str = Form("")):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)
    if student_name not in _parent_students(parent):
        return RedirectResponse(url="/parent/payments", status_code=303)
    msg = f"Payment+notification+sent+for+{_url_encode(student_name,safe='')}+%E2%80%94+%24{amount:.2f}+via+{method}.+Your+instructor+will+confirm+receipt."
    return RedirectResponse(url=f"/parent/payments?msg={msg}", status_code=303)


@app.get("/parent/profile", response_class=HTMLResponse)
def parent_profile_page(request: Request, msg: str = ""):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    parent_name = parent.get('name', 'Parent')
    my_students = _parent_students(parent)
    msg_html    = f'<div class="alert alert-success">{msg}</div>' if msg else ''
    profiles    = get_all_profiles()

    checkboxes = ""
    for sname in sorted(profiles.keys()):
        checked = 'checked' if sname in my_students else ''
        checkboxes += (
            f'<label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;'
            f'cursor:pointer;border:1px solid var(--border);margin-bottom:6px;font-size:13px;">'
            f'<input type="checkbox" name="students" value="{sname}" {checked} style="width:auto;margin:0;"> {sname}</label>'
        )

    content = f"""{msg_html}
<div class="two-col">
  <div class="card">
    <h2>👤 Update Profile</h2>
    <form action="/parent/profile" method="post">
      <div class="form-group"><label class="form-label">Full Name</label>
        <input type="text" name="name" value="{parent.get('name','')}" required>
      </div>
      <div class="form-group"><label class="form-label">Email Address</label>
        <input type="email" value="{parent.get('email','')}" disabled style="background:#f9fafb;color:var(--muted);">
        <div style="font-size:11px;color:var(--muted);margin-top:3px;">Email cannot be changed. Contact your instructor.</div>
      </div>
      <div class="form-group"><label class="form-label">My Children</label>
        {checkboxes}
      </div>
      <button type="submit" class="btn">Save Changes</button>
    </form>
  </div>
  <div class="card">
    <h2>🔑 Change Password</h2>
    <form action="/parent/change-password" method="post">
      <div class="form-group"><label class="form-label">Current Password</label>
        <input type="password" name="current_password" placeholder="Current password" required>
      </div>
      <div class="form-group"><label class="form-label">New Password</label>
        <input type="password" name="new_password" placeholder="At least 8 characters" required minlength="8">
      </div>
      <div class="form-group"><label class="form-label">Confirm New Password</label>
        <input type="password" name="confirm_password" placeholder="Repeat new password" required>
      </div>
      <button type="submit" class="btn">Update Password</button>
    </form>
  </div>
</div>"""
    return HTMLResponse(parent_page("My Profile", content, parent_name, "profile"))


@app.post("/parent/profile")
async def parent_profile_post(request: Request, name: str = Form(...)):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    form = await request.form()
    students_selected = form.getlist("students")
    profiles = get_all_profiles()
    valid_students = [s for s in students_selected if s in profiles]

    parents = get_all_parents()
    email   = parent.get('email', '')
    for p in parents:
        if p.get('email', '').lower() == email.lower():
            p['name'] = name.strip()
            if valid_students:
                p['student_names'] = ';'.join(valid_students)
            break
    save_all_parents(parents)
    return RedirectResponse(url="/parent/profile?msg=Profile+updated+successfully", status_code=303)


@app.post("/parent/change-password")
def parent_change_password(request: Request, current_password: str = Form(...), new_password: str = Form(...), confirm_password: str = Form(...)):
    parent = _get_parent(request)
    if not parent:
        return RedirectResponse(url="/parent/login", status_code=303)

    if new_password != confirm_password:
        return RedirectResponse(url="/parent/profile?msg=New+passwords+do+not+match", status_code=303)
    if hashlib.sha256(current_password.encode()).hexdigest() != parent.get('password_hash', ''):
        return RedirectResponse(url="/parent/profile?msg=Current+password+is+incorrect", status_code=303)

    parents = get_all_parents()
    email   = parent.get('email', '')
    for p in parents:
        if p.get('email', '').lower() == email.lower():
            p['password_hash'] = hashlib.sha256(new_password.encode()).hexdigest()
            break
    save_all_parents(parents)
    return RedirectResponse(url="/parent/profile?msg=Password+updated+successfully", status_code=303)


# ─── Admin: Lesson Notes ──────────────────────────────────────────────────────

@app.get("/admin/lesson-notes", response_class=HTMLResponse)
def admin_lesson_notes():
    profiles = get_all_profiles()
    student_options = "".join(f'<option value="{n}">{n}</option>' for n in sorted(profiles.keys()))

    notes = sorted(get_lesson_notes(), key=lambda x: x.get('lesson_date', ''), reverse=True)
    rows  = ""
    for note in notes:
        rows += f"""<tr>
  <td><strong>{note.get('student_name','')}</strong></td>
  <td>{note.get('lesson_date','')}</td>
  <td style="font-size:12px;">{note.get('notes','')[:80]}{'…' if len(note.get('notes',''))>80 else ''}</td>
  <td style="font-size:12px;color:var(--primary);">{note.get('assignment','') or '—'}</td>
  <td>
    <form action="/admin/lesson-notes/delete/{note.get('id','')}" method="post" style="display:inline;">
      <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Delete this note?')">🗑️</button>
    </form>
  </td>
</tr>"""
    if not rows:
        rows = '<tr><td colspan="5" style="text-align:center;color:var(--muted);padding:20px;">No lesson notes yet.</td></tr>'

    today = datetime.now().strftime('%Y-%m-%d')
    content = f"""
<div class="two-col">
  <div class="card">
    <h2>📝 Add Lesson Note</h2>
    <form action="/admin/lesson-notes/add" method="post">
      <div class="form-group"><label class="form-label">Student</label>
        <select name="student_name" required>
          <option value="">Select student…</option>
          {student_options}
        </select>
      </div>
      <div class="form-group"><label class="form-label">Lesson Date</label>
        <input type="date" name="lesson_date" value="{today}" required>
      </div>
      <div class="form-group"><label class="form-label">Notes</label>
        <textarea name="notes" rows="5" style="width:100%;padding:9px 11px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;font-family:inherit;resize:vertical;" placeholder="Lesson summary, what was covered, progress made…" required></textarea>
      </div>
      <div class="form-group"><label class="form-label">Assignment (optional)</label>
        <input type="text" name="assignment" placeholder="e.g. Practice scales, review measures 1–8">
      </div>
      <button type="submit" class="btn">💾 Save Note</button>
    </form>
  </div>
  <div class="card">
    <div class="card-header"><h2 style="margin:0;">📋 All Notes</h2></div>
    <div style="overflow-x:auto;">
      <table>
        <thead><tr><th>Student</th><th>Date</th><th>Notes</th><th>Assignment</th><th></th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>
</div>"""
    return HTMLResponse(page("Lesson Notes", content, "notes"))


@app.post("/admin/lesson-notes/add")
def admin_add_lesson_note(student_name: str = Form(...), lesson_date: str = Form(...), notes: str = Form(...), assignment: str = Form("")):
    all_notes = get_lesson_notes()
    new_id = max((int(n.get('id', 0)) for n in all_notes), default=0) + 1
    all_notes.append({
        'id': str(new_id),
        'student_name': student_name,
        'lesson_date': lesson_date,
        'notes': notes,
        'assignment': assignment,
        'created_by': 'Instructor',
        'created_at': datetime.now().strftime('%Y-%m-%d'),
    })
    save_lesson_notes(all_notes)
    return RedirectResponse(url="/admin/lesson-notes", status_code=303)


@app.post("/admin/lesson-notes/delete/{note_id}")
def admin_delete_lesson_note(note_id: str):
    notes = [n for n in get_lesson_notes() if n.get('id') != note_id]
    save_lesson_notes(notes)
    return RedirectResponse(url="/admin/lesson-notes", status_code=303)


# ─── Admin: Cancellation Requests ────────────────────────────────────────────

@app.get("/admin/blocked-dates", response_class=HTMLResponse)
def admin_blocked_dates():
    rows_data = sorted(get_blocked_dates(), key=lambda x: x.get('date', ''), reverse=True)
    pending_count = sum(1 for b in rows_data if b.get('status') == 'pending')

    rows = ""
    for b in rows_data:
        status = b.get('status', 'pending')
        badge_cls = 'badge-warning' if status == 'pending' else ('badge-success' if status == 'approved' else 'badge-danger')
        action_btns = ""
        if status == 'pending':
            action_btns = f"""
<form action="/admin/blocked-dates/{b.get('id','')}/approve" method="post" style="display:inline;">
  <button type="submit" class="btn btn-success btn-sm">✅ Approve</button>
</form>
<form action="/admin/blocked-dates/{b.get('id','')}/deny" method="post" style="display:inline;">
  <button type="submit" class="btn btn-danger btn-sm">❌ Deny</button>
</form>"""
        rows += f"""<tr>
  <td><strong>{b.get('student_name','')}</strong></td>
  <td>{b.get('date','')}</td>
  <td style="font-size:12px;color:var(--muted);">{b.get('reason','')}</td>
  <td style="font-size:11px;color:var(--muted);">{b.get('parent_email','')}</td>
  <td><span class="badge {badge_cls}">{status}</span></td>
  <td>{action_btns}</td>
</tr>"""
    if not rows:
        rows = '<tr><td colspan="6" style="text-align:center;color:var(--muted);padding:20px;">No cancellation requests yet.</td></tr>'

    pending_alert = f'<div class="alert alert-warning">⚠️ {pending_count} pending request(s) need your review.</div>' if pending_count > 0 else ''
    content = f"""{pending_alert}
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">🚫 Parent Cancellation Requests</h2>
    <a href="/admin/blocked-dates" class="btn btn-outline btn-sm">🔄 Refresh</a>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Student</th><th>Date</th><th>Reason</th><th>Parent</th><th>Status</th><th>Actions</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>"""
    return HTMLResponse(page("Cancellation Requests", content, "cancels"))


@app.post("/admin/blocked-dates/{date_id}/approve")
def admin_approve_blocked_date(date_id: str):
    rows = get_blocked_dates()
    for r in rows:
        if r.get('id') == date_id:
            r['status'] = 'approved'
            break
    save_blocked_dates(rows)
    return RedirectResponse(url="/admin/blocked-dates", status_code=303)


@app.post("/admin/blocked-dates/{date_id}/deny")
def admin_deny_blocked_date(date_id: str):
    rows = get_blocked_dates()
    for r in rows:
        if r.get('id') == date_id:
            r['status'] = 'denied'
            break
    save_blocked_dates(rows)
    return RedirectResponse(url="/admin/blocked-dates", status_code=303)


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
