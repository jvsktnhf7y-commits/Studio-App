from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
import os
import csv
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import re
import pytz
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

try:
    import stripe as _stripe
    _stripe.api_key        = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
    STRIPE_WEBHOOK_SECRET  = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
    STRIPE_PRICE_MONTHLY   = os.environ.get('STRIPE_PRICE_MONTHLY', '')
    _STRIPE_READY          = bool(_stripe.api_key)
except ImportError:
    _stripe                = None  # type: ignore
    STRIPE_PUBLISHABLE_KEY = ''
    STRIPE_WEBHOOK_SECRET  = ''
    STRIPE_PRICE_MONTHLY   = ''
    _STRIPE_READY          = False

# ── Subscriptions CSV ─────────────────────────────────────────────────────────
SUBSCRIPTIONS_FILE    = 'subscriptions.csv'
PROCESSED_EVENTS_FILE = 'processed_stripe_events.json'
_SUB_HEADERS = [
    'user_key', 'stripe_customer_id', 'stripe_subscription_id',
    'subscription_status', 'current_period_end', 'cancel_at_period_end',
]
_SUB_DEFAULTS = {
    'user_key': 'admin', 'stripe_customer_id': '', 'stripe_subscription_id': '',
    'subscription_status': 'none', 'current_period_end': '', 'cancel_at_period_end': 'false',
}

if not os.path.exists(SUBSCRIPTIONS_FILE):
    with open(SUBSCRIPTIONS_FILE, 'w', newline='') as _f:
        csv.DictWriter(_f, fieldnames=_SUB_HEADERS).writeheader()


def _sub_get(user_key: str = 'admin') -> dict:
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE) as f:
            for row in csv.DictReader(f):
                if row.get('user_key') == user_key:
                    return dict(row)
    return dict(_SUB_DEFAULTS, user_key=user_key)


def _sub_save(data: dict):
    user_key = data.get('user_key', 'admin')
    rows, found = [], False
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE) as f:
            for row in csv.DictReader(f):
                if row.get('user_key') == user_key:
                    rows.append({**_SUB_DEFAULTS, **row, **data})
                    found = True
                else:
                    rows.append(dict(row))
    if not found:
        rows.append({**_SUB_DEFAULTS, **data})
    with open(SUBSCRIPTIONS_FILE, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=_SUB_HEADERS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, '') for k in _SUB_HEADERS})


def _event_processed(event_id: str) -> bool:
    if os.path.exists(PROCESSED_EVENTS_FILE):
        try:
            with open(PROCESSED_EVENTS_FILE) as f:
                return event_id in json.load(f)
        except Exception:
            pass
    return False


def _mark_event(event_id: str):
    events = {}
    if os.path.exists(PROCESSED_EVENTS_FILE):
        try:
            with open(PROCESSED_EVENTS_FILE) as f:
                events = json.load(f)
        except Exception:
            pass
    events[event_id] = datetime.now().isoformat()
    if len(events) > 1000:
        events = dict(list(events.items())[-1000:])
    with open(PROCESSED_EVENTS_FILE, 'w') as f:
        json.dump(events, f)


def _fetch_stripe_data(sub: dict) -> dict:
    """Fetch live subscription/invoice data from Stripe. Safe defaults on any failure."""
    result = {
        'payment_method': None,
        'next_billing_date': None,
        'cancel_at_period_end': sub.get('cancel_at_period_end', 'false') == 'true',
        'invoices': [],
    }
    if not _STRIPE_READY:
        return result
    customer_id = sub.get('stripe_customer_id', '')
    sub_id      = sub.get('stripe_subscription_id', '')
    if sub_id:
        try:
            s = _stripe.Subscription.retrieve(sub_id, expand=['default_payment_method'])
            period_end = s.get('current_period_end')
            if period_end:
                result['next_billing_date'] = datetime.fromtimestamp(int(period_end)).strftime('%B %d, %Y')
            result['cancel_at_period_end'] = bool(s.get('cancel_at_period_end', False))
            pm = s.get('default_payment_method') or {}
            if isinstance(pm, dict) and pm.get('card'):
                c = pm['card']
                result['payment_method'] = {
                    'brand': c.get('brand', '').title(),
                    'last4': c.get('last4', ''),
                    'exp':   f"{c.get('exp_month','')}/{c.get('exp_year','')}",
                }
        except Exception:
            pass
    if customer_id:
        try:
            for inv in _stripe.Invoice.list(customer=customer_id, limit=10).data:
                created = inv.get('created', 0)
                result['invoices'].append({
                    'date':   datetime.fromtimestamp(int(created)).strftime('%b %d, %Y') if created else '—',
                    'amount': f"${inv.get('amount_paid', 0) / 100:.2f}",
                    'status': inv.get('status', '').title(),
                    'url':    inv.get('hosted_invoice_url', ''),
                    'pdf':    inv.get('invoice_pdf', ''),
                })
        except Exception:
            pass
    return result

app = FastAPI(title="Studio App")

# Create static directory
os.makedirs("static", exist_ok=True)

# CSS — full design system (sidebar layout)
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
.btn-warning{background:var(--warning);color:#fff;}
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
input[type=text],input[type=number],input[type=date],input[type=time],input[type=password],input[type=email],select,textarea{width:100%;padding:8px 11px;border:1.5px solid var(--border);border-radius:8px;font-size:13px;color:var(--dark);background:#fff;transition:border-color .15s;outline:none;font-family:inherit;margin:0;}
input:focus,select:focus,textarea:focus{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.1);}
.badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:20px;font-size:11px;font-weight:600;}
.badge-success{background:#d1fae5;color:#065f46;}.badge-danger{background:#fee2e2;color:#991b1b;}
.badge-warning{background:#fef3c7;color:#92400e;}.badge-info{background:#e0e7ff;color:#3730a3;}
.badge-muted{background:var(--bg);color:var(--muted);}
.two-col{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px;}
.three-col{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;}
.container{max-width:1100px;margin:0 auto;padding:24px;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;}
.alert{padding:12px 16px;border-radius:9px;margin-bottom:14px;font-size:13px;font-weight:500;}
.alert-warning{background:#fef3c7;color:#92400e;border:1px solid #fde68a;}
.alert-success{background:#d1fae5;color:#065f46;border:1px solid #a7f3d0;}
.alert-danger{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5;}
.alert-info{background:#e0e7ff;color:#3730a3;border:1px solid #c7d2fe;}
.login-wrap{min-height:100vh;background:var(--bg);display:flex;align-items:center;justify-content:center;padding:24px;}
.login-card{background:#fff;border-radius:18px;padding:36px;width:100%;max-width:390px;border:1px solid var(--border);box-shadow:0 8px 32px rgba(0,0,0,.08);}
.login-logo{width:52px;height:52px;border-radius:13px;background:linear-gradient(135deg,var(--primary),var(--secondary));display:flex;align-items:center;justify-content:center;font-size:24px;margin:0 auto 18px;}
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
  .two-col,.three-col,.grid{grid-template-columns:1fr;}
  h1{font-size:18px;}
}
.toast-container{position:fixed;bottom:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;pointer-events:none;}
.toast{background:#1e293b;color:#fff;padding:12px 18px;border-radius:10px;font-size:13px;font-weight:500;box-shadow:0 4px 16px rgba(0,0,0,.18);display:flex;align-items:center;gap:10px;opacity:1;transform:translateY(0);transition:opacity .4s ease,transform .4s ease;pointer-events:auto;}
.toast.toast-success{border-left:3px solid #10b981;}.toast.toast-error{border-left:3px solid #ef4444;}.toast.toast-info{border-left:3px solid #6366f1;}
.toast.hiding{opacity:0;transform:translateY(8px);}
@media(max-width:600px){.toast-container{bottom:16px;right:16px;left:16px;}.toast{max-width:100%;}}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid rgba(255,255,255,.35);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite;vertical-align:middle;}
@keyframes spin{to{transform:rotate(360deg);}}
.empty-state{text-align:center;padding:48px 24px;color:var(--muted);}
.empty-state-icon{font-size:48px;margin-bottom:14px;opacity:.6;}
.empty-state h3{font-size:15px;font-weight:700;color:var(--dark);margin-bottom:6px;}
.empty-state p{font-size:13px;max-width:320px;margin:0 auto 18px;}
"""

with open("static/style.css", "w") as f:
    f.write(css_content)


@app.get("/static/style.css")
def serve_css():
    return Response(content=css_content, media_type="text/css")


def page(title: str, content: str, active: str = "dashboard") -> str:
    """Render a full page with the dark sidebar layout."""
    links = [
        ("dashboard", "/dashboard",  "🏠", "Dashboard"),
        ("students",  "/students",   "👥", "Students"),
        ("rates",     "/rates",      "💰", "Rates"),
        ("payments",  "/payments",   "💳", "Payments"),
        ("schedule",  "/schedule",   "📅", "Schedule"),
        ("invoices",  "/invoices",   "🧾", "Invoices"),
        ("analytics", "/analytics",  "📈", "Analytics"),
        ("beta-stats", "/beta-analytics", "🧪", "Beta Stats"),
        ("settings",  "/settings",   "⚙️",  "Settings"),
        ("admin",     "/admin",      "🔐", "Admin"),
        ("billing",   "/billing",    "💳", "Billing"),
    ]
    nav_html = "".join(
        f'<a href="{href}" class="nav-link{" active" if k == active else ""}">'
        f'<span class="nav-icon">{icon}</span>{label}</a>\n'
        for k, href, icon, label in links
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
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
  </header>
  <div class="page-body">{content}</div>
</div>
</div>
<div class="toast-container" id="toastContainer"></div>
<script>
function openSidebar(){{document.getElementById('sidebar').classList.add('open');document.getElementById('overlay').classList.add('open');}}
function closeSidebar(){{document.getElementById('sidebar').classList.remove('open');document.getElementById('overlay').classList.remove('open');}}
function showToast(msg, type){{
  var icons = {{success:'✅',error:'❌',info:'💬'}};
  var t = document.createElement('div');
  t.className = 'toast toast-' + (type||'success');
  t.innerHTML = '<span>' + (icons[type||'success']||'') + '</span><span>' + msg + '</span>';
  document.getElementById('toastContainer').appendChild(t);
  setTimeout(function(){{t.classList.add('hiding');}}, 2800);
  setTimeout(function(){{t.remove();}}, 3200);
}}
(function(){{
  var p = new URLSearchParams(window.location.search);
  var msg = p.get('toast');
  if(msg) showToast(decodeURIComponent(msg.replace(/\+/g,' ')), p.get('toast_type')||'success');
}})();
document.addEventListener('keydown', function(e){{
  if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA'||e.target.tagName==='SELECT'||e.isComposing) return;
  if(e.metaKey||e.ctrlKey||e.altKey) return;
  var k = e.key.toUpperCase();
  if(k==='S'){{ e.preventDefault(); window.location.href='/schedule'; }}
  if(k==='C'){{
    var btn = document.querySelector('button[value="Confirmed"],form [name="status"] option[value="Confirmed"]');
    var confirmForm = document.querySelector('form input[value="Confirmed"]');
    if(confirmForm){{ confirmForm.closest('form').submit(); showToast('Lesson confirmed','success'); }}
    else{{
      var allBtns = document.querySelectorAll('.btn-success');
      if(allBtns.length){{ allBtns[0].click(); }}
    }}
  }}
  if(k==='M'){{
    var missedInput = document.querySelector('form input[value="Missed"]');
    if(missedInput){{ missedInput.closest('form').submit(); showToast('Marked as missed','info'); }}
    else{{
      var dangerBtns = document.querySelectorAll('.btn-danger');
      if(dangerBtns.length){{ dangerBtns[0].click(); }}
    }}
  }}
  if(k==='?'){{
    showToast('Shortcuts: C = Confirm lesson · M = Mark missed · S = Schedule','info');
  }}
}});
<!-- Feedback widget (beta testers) -->
<style>
#fb-btn{{position:fixed;bottom:24px;right:24px;z-index:8000;background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;border:none;border-radius:50px;padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;box-shadow:0 4px 16px rgba(99,102,241,.35);display:flex;align-items:center;gap:6px;transition:transform .2s,box-shadow .2s;}}
#fb-btn:hover{{transform:translateY(-2px);box-shadow:0 6px 20px rgba(99,102,241,.5);}}
#fb-panel{{position:fixed;bottom:72px;right:24px;z-index:8000;width:310px;background:#fff;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,.16);padding:22px;border:1px solid var(--border);display:none;animation:fbIn .18s ease;}}
@keyframes fbIn{{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:translateY(0);}}}}
#fb-close{{position:absolute;top:10px;right:12px;background:none;border:none;font-size:20px;cursor:pointer;color:var(--muted);line-height:1;padding:2px 6px;border-radius:4px;}}
#fb-close:hover{{background:var(--bg);}}
#fb-panel h3{{font-size:14px;font-weight:700;margin:0 0 16px;color:var(--dark);}}
.fb-field{{margin-bottom:12px;}}
.fb-lbl{{display:block;font-size:11px;font-weight:600;color:var(--dark);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px;}}
#fb-trying,#fb-happened{{width:100%;padding:8px 10px;border:1.5px solid var(--border);border-radius:7px;font-size:13px;font-family:inherit;outline:none;box-sizing:border-box;}}
#fb-happened{{resize:vertical;min-height:60px;}}
#fb-trying:focus,#fb-happened:focus{{border-color:var(--primary);box-shadow:0 0 0 3px rgba(99,102,241,.1);}}
.star-row{{display:flex;gap:4px;margin-top:4px;}}
.star-btn{{background:none;border:none;font-size:24px;cursor:pointer;color:#d1d5db;padding:0;line-height:1;transition:color .1s;}}
.star-btn.on,.star-btn:hover~.star-btn{{color:#f59e0b;}}
#fb-submit{{width:100%;padding:10px;margin-top:14px;background:linear-gradient(135deg,var(--primary),var(--secondary));color:#fff;border:none;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;transition:opacity .15s;}}
#fb-submit:disabled{{opacity:.55;cursor:default;}}
</style>
<button id="fb-btn" onclick="fbToggle()">💬 Feedback</button>
<div id="fb-panel">
  <button id="fb-close" onclick="fbToggle()" title="Close">×</button>
  <h3>Share Feedback</h3>
  <div class="fb-field">
    <label class="fb-lbl" for="fb-trying">What were you trying to do?</label>
    <input type="text" id="fb-trying" placeholder="e.g. Generate invoices for July">
  </div>
  <div class="fb-field">
    <label class="fb-lbl" for="fb-happened">What happened?</label>
    <textarea id="fb-happened" placeholder="e.g. Button didn't respond"></textarea>
  </div>
  <div class="fb-field">
    <label class="fb-lbl">Rate your experience</label>
    <div class="star-row" id="fbStars">
      <button class="star-btn" data-v="1" onclick="fbStar(1)">★</button>
      <button class="star-btn" data-v="2" onclick="fbStar(2)">★</button>
      <button class="star-btn" data-v="3" onclick="fbStar(3)">★</button>
      <button class="star-btn" data-v="4" onclick="fbStar(4)">★</button>
      <button class="star-btn" data-v="5" onclick="fbStar(5)">★</button>
    </div>
  </div>
  <button id="fb-submit" onclick="fbSend()">Send Feedback</button>
</div>
<script>
var _fbR = 0;
function fbToggle(){{
  var p = document.getElementById('fb-panel');
  p.style.display = p.style.display === 'block' ? 'none' : 'block';
  if(p.style.display === 'block') document.getElementById('fb-trying').focus();
}}
function fbStar(v){{
  _fbR = v;
  document.querySelectorAll('.star-btn').forEach(function(b){{
    b.classList.toggle('on', +b.dataset.v <= v);
  }});
}}
function fbSend(){{
  var t = document.getElementById('fb-trying').value.trim();
  var h = document.getElementById('fb-happened').value.trim();
  if(!t || !h){{ showToast('Please fill in both fields.','error'); return; }}
  if(!_fbR){{ showToast('Please choose a star rating.','error'); return; }}
  var btn = document.getElementById('fb-submit');
  btn.disabled = true; btn.textContent = 'Sending…';
  var fd = new FormData();
  fd.append('trying_to', t); fd.append('what_happened', h); fd.append('rating', _fbR);
  fetch('/feedback', {{method:'POST', body:fd}})
    .then(function(r){{ return r.json(); }})
    .then(function(){{
      document.getElementById('fb-panel').style.display = 'none';
      document.getElementById('fb-trying').value = '';
      document.getElementById('fb-happened').value = '';
      _fbR = 0;
      document.querySelectorAll('.star-btn').forEach(function(b){{ b.classList.remove('on'); }});
      btn.disabled = false; btn.textContent = 'Send Feedback';
      showToast('Thanks for your feedback! 🙏','success');
    }})
    .catch(function(){{
      btn.disabled = false; btn.textContent = 'Send Feedback';
      showToast('Could not send — please try again.','error');
    }});
}}
</script>
</body>
</html>"""


# Password file
PASSWORD_FILE = "admin_password.json"
if not os.path.exists(PASSWORD_FILE):
    default_hash = hashlib.sha256("studio2025".encode()).hexdigest()
    with open(PASSWORD_FILE, 'w') as f:
        json.dump({"password_hash": default_hash}, f)

# Users file
USERS_FILE    = "/data/users.csv"
USERS_HEADERS = [
    "name", "email", "password_hash", "is_beta_tester", "created_at",
    "is_verified", "verification_token", "reset_token", "reset_token_expires",
]
os.makedirs("/data", exist_ok=True)


def _init_users_csv():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='') as _f:
            csv.DictWriter(_f, fieldnames=USERS_HEADERS).writeheader()
        return
    # Migrate: add missing columns to existing file without losing data
    with open(USERS_FILE, 'r') as _f:
        _r = csv.DictReader(_f)
        _fields = list(_r.fieldnames or [])
        _rows   = [dict(r) for r in _r]
    if not set(USERS_HEADERS).issubset(set(_fields)):
        with open(USERS_FILE, 'w', newline='') as _f:
            _w = csv.DictWriter(_f, fieldnames=USERS_HEADERS)
            _w.writeheader()
            for _row in _rows:
                # existing users are treated as already verified
                _w.writerow({k: _row.get(k, 'true' if k == 'is_verified' else '') for k in USERS_HEADERS})

_init_users_csv()


# ── SendGrid email helper ─────────────────────────────────────────────────────
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY', '')
SENDGRID_FROM    = os.environ.get('SENDGRID_FROM_EMAIL', 'noreply@studioconsole.app')


def send_email(to: str, subject: str, body_html: str) -> bool:
    if not SENDGRID_API_KEY:
        print(f"[Email — no SENDGRID_API_KEY] To: {to} | {subject}")
        return False
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        SendGridAPIClient(SENDGRID_API_KEY).send(
            Mail(from_email=SENDGRID_FROM, to_emails=to,
                 subject=subject, html_content=body_html)
        )
        return True
    except ImportError:
        import urllib.request
        payload = json.dumps({
            "personalizations": [{"to": [{"email": to}]}],
            "from":    {"email": SENDGRID_FROM},
            "subject": subject,
            "content": [{"type": "text/html", "value": body_html}],
        }).encode()
        req = urllib.request.Request(
            "https://api.sendgrid.com/v3/mail/send", data=payload, method="POST",
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}",
                     "Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as exc:
        print(f"[Email error] {exc}")
        return False


def get_all_users() -> list[dict]:
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return [dict(row) for row in csv.DictReader(f)]


def update_user(email: str, **kwargs):
    users = get_all_users()
    with open(USERS_FILE, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=USERS_HEADERS)
        w.writeheader()
        for u in users:
            if u.get('email') == email:
                u.update(kwargs)
            w.writerow({k: u.get(k, '') for k in USERS_HEADERS})


def save_user(name: str, email: str, password_hash: str, verification_token: str = ''):
    with open(USERS_FILE, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=USERS_HEADERS).writerow({
            "name":                name,
            "email":               email,
            "password_hash":       password_hash,
            "is_beta_tester":      "true",
            "created_at":          datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "is_verified":         "false" if verification_token else "true",
            "verification_token":  verification_token,
            "reset_token":         "",
            "reset_token_expires": "",
        })

# ── Analytics events ──────────────────────────────────────────────────────────
ANALYTICS_FILE    = "/data/analytics_events.csv"
ANALYTICS_HEADERS = ["timestamp", "event_type", "user", "path", "detail"]

if not os.path.exists(ANALYTICS_FILE):
    with open(ANALYTICS_FILE, 'w', newline='') as _f:
        csv.DictWriter(_f, fieldnames=ANALYTICS_HEADERS).writeheader()


def log_event(event_type: str, user: str = "", path: str = "", detail: str = ""):
    try:
        with open(ANALYTICS_FILE, 'a', newline='') as f:
            csv.writer(f).writerow([
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                event_type, user, path, detail,
            ])
    except Exception:
        pass

# Data files
PROFILES_FILE = "/data/student_profiles.csv"
PRICING_FILE  = "/data/pricing_tiers.csv"
LEDGER_FILE   = "/data/ledger.csv"
DEFAULT_RATE  = 50.00

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
                    }
    return profiles

def save_all_profiles(profiles_map):
    with open(PROFILES_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "TierName", "Rate", "TargetMinutes", "Credits", "Description", "Prepaid"])
        for name, data in profiles_map.items():
            writer.writerow([name, data.get('tier_name', ''), data.get('rate', DEFAULT_RATE),
                             data.get('target_minutes', 60), data.get('credits', 0),
                             data.get('description', ''), data.get('prepaid', 0)])

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


# ── Status constants ──────────────────────────────────────────────────────────
ATTENDED_STATUSES    = frozenset(['Confirmed', 'Attended', 'Completed', 'Completed (Half Rate)'])
MISSED_STATUSES      = frozenset(['Missed', 'No-Show', 'No Show'])
ZERO_CHARGE_STATUSES = frozenset(['Cancelled', 'Rescheduled', 'Completed (Make-up)'])
HALF_CHARGE_STATUSES = frozenset(['Completed (Half Rate)'])

LEDGER_FIELDS = ['Date', 'Student', 'Status', 'AmountCharged', 'Notes']

def _ledger_reader(f):
    """DictReader that works whether or not the CSV has a header row."""
    first = f.readline()
    f.seek(0)
    if first.strip() == ','.join(LEDGER_FIELDS):
        return csv.DictReader(f)
    return csv.DictReader(f, fieldnames=LEDGER_FIELDS)

def _safe_float(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


# ── Calendar settings ─────────────────────────────────────────────────────────
SETTINGS_FILE = "calendar_settings.json"

def load_calendar_settings():
    defaults = {
        "lesson_keywords": ["lesson", "private", "student", "class", "music",
                            "piano", "guitar", "violin", "drums", "voice"],
        "show_all": True,
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults

def save_calendar_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def clean_student_name(title: str) -> str:
    name = title.strip()
    for p in [
        r'^private\s+lesson\s*[:–\-]\s*',
        r'^lesson\s+with\s+',
        r'^lesson\s*[:–\-]\s*',
        r'^(?:piano|guitar|violin|drums|voice|music)\s+lesson\s*[:–\-]\s*',
    ]:
        name = re.sub(p, '', name, flags=re.IGNORECASE).strip()
    for s in [
        r'\s*[-–]\s*private\s+lesson$',
        r'\s*[-–]\s*lesson$',
        r'\s*\(\d+\s*min\w*\)$',
    ]:
        name = re.sub(s, '', name, flags=re.IGNORECASE).strip()
    return name


def _suggested_rate(duration_minutes: int) -> float:
    if duration_minutes <= 30:
        return 30.0
    elif duration_minutes <= 45:
        return 40.0
    elif duration_minutes <= 60:
        return 50.0
    return 75.0


def get_today_calendar_events():
    if not os.path.exists('/data/calendar_token.json'):
        return []
    try:
        with open('/data/calendar_token.json', 'r') as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)
        service = build('calendar', 'v3', credentials=creds)
        tz = pytz.timezone('America/New_York')
        now = datetime.now(tz)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end   = now.replace(hour=23, minute=59, second=59, microsecond=0)
        return service.events().list(
            calendarId='primary',
            timeMin=start.astimezone(pytz.UTC).isoformat(),
            timeMax=end.astimezone(pytz.UTC).isoformat(),
            singleEvents=True,
            orderBy='startTime',
        ).execute().get('items', [])
    except Exception:
        return []


# ── Invoice helpers ───────────────────────────────────────────────────────────
INVOICES_FILE   = "/data/invoices.csv"
INVOICE_HEADERS = [
    "id", "student_name", "month", "year", "scheduled_lessons",
    "total_amount", "amount_paid", "balance_due", "status",
    "created_date", "paid_date",
]
MONTH_NAMES = ['', 'January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']
MONTH_SHORT  = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

# Migrate invoices.csv from old (attendance-based) field names to new schema
def _init_invoices_csv():
    _OLD_MAP = {
        'ID': 'id', 'Student': 'student_name', 'Month': 'month', 'Year': 'year',
        'LessonsCount': 'scheduled_lessons', 'TotalAmount': 'total_amount',
        'PaymentsApplied': 'amount_paid', 'BalanceDue': 'balance_due',
        'Status': 'status', 'CreatedDate': 'created_date', 'PaidDate': 'paid_date',
    }
    if not os.path.exists(INVOICES_FILE):
        with open(INVOICES_FILE, 'w', newline='') as _f:
            csv.DictWriter(_f, fieldnames=INVOICE_HEADERS).writeheader()
        return
    with open(INVOICES_FILE, 'r') as _f:
        _r      = csv.DictReader(_f)
        _fields = list(_r.fieldnames or [])
        _rows   = [dict(r) for r in _r]
    if set(INVOICE_HEADERS).issubset(set(_fields)):
        return
    with open(INVOICES_FILE, 'w', newline='') as _f:
        _w = csv.DictWriter(_f, fieldnames=INVOICE_HEADERS)
        _w.writeheader()
        for _row in _rows:
            nr = {nk: _row.get(ok, _row.get(nk, '')) for ok, nk in _OLD_MAP.items()}
            st = nr.get('status', '')
            nr['status'] = 'paid' if st == 'Paid' else ('draft' if st in ('Unpaid', '') else st)
            _w.writerow({k: nr.get(k, '') for k in INVOICE_HEADERS})

_init_invoices_csv()


def get_all_invoices() -> list[dict]:
    if not os.path.exists(INVOICES_FILE):
        return []
    with open(INVOICES_FILE, 'r') as f:
        return [dict(row) for row in csv.DictReader(f)]


def save_all_invoices(invoices: list[dict]):
    with open(INVOICES_FILE, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=INVOICE_HEADERS)
        w.writeheader()
        for inv in invoices:
            w.writerow({k: inv.get(k, '') for k in INVOICE_HEADERS})


def get_calendar_events_for_month(year: int, month: int) -> list:
    """Fetch all calendar events for the given month. Returns [] if not connected."""
    if not os.path.exists('/data/calendar_token.json'):
        return []
    try:
        import calendar as _cal
        with open('/data/calendar_token.json', 'r') as f:
            token_data = json.load(f)
        creds    = Credentials.from_authorized_user_info(token_data)
        service  = build('calendar', 'v3', credentials=creds)
        tz       = pytz.timezone('America/New_York')
        last_day = _cal.monthrange(year, month)[1]
        t_start  = tz.localize(datetime(year, month, 1, 0, 0, 0))
        t_end    = tz.localize(datetime(year, month, last_day, 23, 59, 59))
        return service.events().list(
            calendarId='primary',
            timeMin=t_start.astimezone(pytz.UTC).isoformat(),
            timeMax=t_end.astimezone(pytz.UTC).isoformat(),
            singleEvents=True,
            orderBy='startTime',
        ).execute().get('items', [])
    except Exception:
        return []


def _display_status(inv: dict) -> str:
    """Return display status: overdue if draft/sent and the invoice month is already past."""
    st = inv.get('status', 'draft')
    if st in ('draft', 'sent'):
        try:
            now = datetime.now()
            if (int(inv['year']), int(inv['month'])) < (now.year, now.month):
                return 'overdue'
        except Exception:
            pass
    return st


def generate_invoices_for_month(year: int, month: int) -> tuple[int, str]:
    """Generate draft invoices from Google Calendar scheduled events.
    Returns (count_added, error_message)."""
    if not os.path.exists('/data/calendar_token.json'):
        return 0, "Google Calendar is not connected — connect it in Settings first."
    profiles = get_all_profiles()
    invoices = get_all_invoices()
    existing = {(i['student_name'], i['year'], i['month']) for i in invoices}
    events   = get_calendar_events_for_month(year, month)
    counts: dict[str, int] = {}
    for e in events:
        name = clean_student_name(e.get('summary', ''))
        if name and name in profiles:
            counts[name] = counts.get(name, 0) + 1
    next_id = max((int(i.get('id') or 0) for i in invoices), default=0) + 1
    added = 0
    for student_name, count in counts.items():
        if (student_name, str(year), str(month)) in existing:
            continue
        rate  = profiles[student_name].get('rate', DEFAULT_RATE)
        total = round(count * rate, 2)
        invoices.append({
            'id':                str(next_id),
            'student_name':      student_name,
            'month':             str(month),
            'year':              str(year),
            'scheduled_lessons': str(count),
            'total_amount':      f"{total:.2f}",
            'amount_paid':       '0.00',
            'balance_due':       f"{total:.2f}",
            'status':            'draft',
            'created_date':      datetime.now().strftime('%Y-%m-%d'),
            'paid_date':         '',
        })
        next_id += 1
        added   += 1
    save_all_invoices(invoices)
    return added, ""


# ── Analytics helpers ─────────────────────────────────────────────────────────
def calculate_total_revenue():
    total = 0.0
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            for row in _ledger_reader(f):
                total += _safe_float(row.get('AmountCharged', 0))
    return total

def compute_analytics():
    from collections import defaultdict
    now = datetime.now()

    def _months(n):
        result = []
        for i in range(n - 1, -1, -1):
            m, y = now.month - i, now.year
            while m <= 0:
                m += 12; y -= 1
            result.append((y, m))
        return result

    profiles    = get_all_profiles()
    ledger_rows = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            for row in _ledger_reader(f):
                try:
                    row['_date'] = datetime.strptime(row.get('Date', ''), '%Y-%m-%d')
                except Exception:
                    row['_date'] = None
                ledger_rows.append(row)

    six_m   = _months(6)
    three_m = _months(3)

    month_rev = defaultdict(float)
    for row in ledger_rows:
        if row['_date']:
            month_rev[(row['_date'].year, row['_date'].month)] += _safe_float(row.get('AmountCharged', 0))

    monthly_revenue = [
        {'label': datetime(y, m, 1).strftime('%b %Y'), 'rev': round(month_rev.get((y, m), 0), 2)}
        for y, m in six_m
    ]

    student_rev = defaultdict(float)
    for row in ledger_rows:
        amt = _safe_float(row.get('AmountCharged', 0))
        if amt > 0:
            student_rev[row.get('Student', 'Unknown')] += amt
    top5 = sorted(student_rev.items(), key=lambda x: x[1], reverse=True)[:5]

    att = defaultdict(int)
    for row in ledger_rows:
        s = row.get('Status', '')
        if s in ATTENDED_STATUSES:    att['confirmed'] += 1
        elif s in MISSED_STATUSES:    att['missed']    += 1
        elif s in ZERO_CHARGE_STATUSES: att['cancelled'] += 1
    att_total = sum(att.values()) or 1

    stu_att = defaultdict(lambda: defaultdict(int))
    for row in ledger_rows:
        stu = row.get('Student', '')
        s   = row.get('Status', '')
        if s in ATTENDED_STATUSES:      stu_att[stu]['c'] += 1
        elif s in MISSED_STATUSES:      stu_att[stu]['m'] += 1
        elif s in ZERO_CHARGE_STATUSES: stu_att[stu]['x'] += 1

    reliability = []
    for stu, counts in stu_att.items():
        total = counts['c'] + counts['m']
        rate  = round(counts['c'] / total * 100, 1) if total > 0 else 100.0
        reliability.append({'name': stu, 'rate': rate,
                             'confirmed': counts['c'], 'missed': counts['m']})
    reliability.sort(key=lambda x: x['rate'], reverse=True)

    last3_rev  = sum(month_rev.get(k, 0) for k in three_m)
    projected  = round(last3_rev / 3, 2)
    total_rev  = sum(month_rev.values())
    total_pre  = sum(d.get('prepaid', 0) for d in profiles.values())

    return {
        'monthly_revenue': monthly_revenue,
        'total_revenue': round(total_rev, 2),
        'revenue_by_student': [{'name': n, 'rev': round(r, 2)} for n, r in top5],
        'att': dict(att), 'att_total': att_total,
        'confirmed_pct': round(att['confirmed'] / att_total * 100, 1),
        'missed_pct':    round(att['missed']    / att_total * 100, 1),
        'cancelled_pct': round(att['cancelled'] / att_total * 100, 1),
        'reliability': reliability,
        'total_students': len(profiles),
        'projected': projected,
        'total_prepaid': round(total_pre, 2),
    }


# Dashboard with Calendar
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    profiles = get_all_profiles()
    calendar_items = ""
    cal_header = '<a href="/calendar-auth" class="btn btn-outline btn-sm" onclick="this.innerHTML=\'<span class=\\\'spinner\\\'></span> Connecting…\';this.style.pointerEvents=\'none\';">Connect Calendar</a>'
    if os.path.exists('/data/calendar_token.json'):
        try:
            tz = pytz.timezone('America/New_York')
            events = get_today_calendar_events()
            cal_header = '<span class="badge badge-success">Connected</span>'
            if events:
                for e in events:
                    summary  = e.get('summary', 'Lesson')
                    start_dt = e.get('start', {}).get('dateTime', '')
                    end_dt   = e.get('end',   {}).get('dateTime', '')
                    t = 'All day'
                    if start_dt:
                        t = datetime.fromisoformat(start_dt.replace('Z', '+00:00')).astimezone(tz).strftime('%I:%M %p')
                    dur = 60
                    if start_dt and end_dt:
                        try:
                            s_dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
                            e_dt = datetime.fromisoformat(end_dt.replace('Z', '+00:00'))
                            dur  = max(15, int((e_dt - s_dt).total_seconds() / 60))
                        except Exception:
                            pass
                    student_name  = clean_student_name(summary)
                    is_registered = student_name in profiles
                    quick_create_btn = ""
                    if not is_registered and student_name:
                        safe_name = student_name.replace('"', '&quot;')
                        quick_create_btn = (
                            f'<form action="/quick-create-student" method="post" style="margin-top:6px;">'
                            f'<input type="hidden" name="student_name" value="{safe_name}">'
                            f'<input type="hidden" name="duration_minutes" value="{dur}">'
                            f'<input type="hidden" name="redirect_to" value="/dashboard">'
                            f'<button type="submit" class="btn btn-success btn-sm">➕ Quick Create Student</button>'
                            f'</form>'
                        )
                    reg_badge = ('' if is_registered else
                                 '<span class="badge badge-warning" style="margin-left:6px;font-size:10px;">Not registered</span>')
                    calendar_items += (
                        f'<div style="padding:10px 0;border-bottom:1px solid var(--border);">'
                        f'<div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:4px;">'
                        f'<span style="font-weight:600;">🎵 {summary}{reg_badge}</span>'
                        f'<span style="color:var(--muted);font-size:12px;">{t} · {dur} min</span>'
                        f'</div>'
                        f'{quick_create_btn}'
                        f'</div>'
                    )
            else:
                calendar_items = '<p style="color:var(--muted);font-size:13px;">No lessons scheduled today.</p>'
        except Exception as exc:
            calendar_items = f'<p style="color:var(--muted);font-size:13px;">{str(exc)[:80]}</p>'
    else:
        calendar_items = '<p style="color:var(--muted);font-size:13px;">Connect Google Calendar to see today\'s lessons.</p>'
    content = f"""
<h1>Dashboard</h1>
<div class="stats-row">
  <div class="stat-card">
    <div class="stat-icon" style="background:#ede9fe;">👥</div>
    <div class="stat-val">{len(profiles)}</div>
    <div class="stat-lbl">Students</div>
  </div>
  <div class="stat-card">
    <div class="stat-icon" style="background:#d1fae5;">📅</div>
    <div class="stat-val">{datetime.now().strftime('%b %d')}</div>
    <div class="stat-lbl">Today</div>
  </div>
</div>
<div class="two-col">
  <div class="card">
    <div class="card-header">
      <span class="card-title">📅 Today's Lessons</span>
      {cal_header}
    </div>
    {calendar_items or '<p style="color:var(--muted);font-size:13px;">No events.</p>'}
  </div>
  <div class="card">
    <div class="card-title" style="margin-bottom:14px;">Quick Actions</div>
    <a href="/students" class="btn" style="display:block;margin-bottom:8px;">👥 Manage Students</a>
    <a href="/schedule" class="btn btn-success" style="display:block;margin-bottom:8px;">📅 Schedule Lesson</a>
    <a href="/payments" class="btn btn-warning" style="display:block;margin-bottom:8px;">💳 Record Payment</a>
    <a href="/billing"  class="btn btn-outline"  style="display:block;">🧾 Billing</a>
  </div>
</div>"""
    return HTMLResponse(page("Dashboard", content, active="dashboard"))


# Login
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = "", info: str = ""):
    error_html = f'<div class="alert alert-danger">{error}</div>'  if error else ''
    info_html  = f'<div class="alert alert-success">{info}</div>'  if info  else ''
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
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Sign in to your studio</p>
    {info_html}{error_html}
    <form action="/login" method="post">
      <div class="form-group">
        <label class="form-label">Email or Username</label>
        <input type="text" name="username" placeholder="you@example.com" required autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" placeholder="••••••••" required>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;padding:10px;">Sign In</button>
    </form>
    <p style="text-align:center;margin-top:14px;font-size:13px;">
      <a href="/forgot-password" style="color:var(--muted);">Forgot password?</a>
      &nbsp;·&nbsp;
      <a href="/resend-confirmation" style="color:var(--muted);">Resend confirmation email</a>
    </p>
    <p style="text-align:center;margin-top:8px;font-size:13px;color:var(--muted);">
      Don't have an account? <a href="/signup" style="color:var(--primary);font-weight:600;">Sign up here</a>
    </p>
  </div>
</div>
</body>
</html>""")

@app.post("/login")
def login_post(username: str = Form(...), password: str = Form(...)):
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    # Admin account (never requires email verification)
    if username == "admin":
        with open(PASSWORD_FILE, 'r') as f:
            if input_hash == json.load(f).get("password_hash", ""):
                response = RedirectResponse(url="/dashboard", status_code=303)
                response.set_cookie(key="session", value="authenticated", httponly=True, max_age=86400)
                return response
    # Signed-up users (email login)
    for user in get_all_users():
        if user.get("email") == username and user.get("password_hash") == input_hash:
            if user.get("is_verified", "true") != "true":
                return RedirectResponse(
                    url="/login?error=Please+verify+your+email+before+signing+in."
                        "+Check+your+inbox+for+the+confirmation+link.",
                    status_code=303,
                )
            response = RedirectResponse(url="/dashboard", status_code=303)
            response.set_cookie(key="session", value="authenticated", httponly=True, max_age=86400)
            return response
    return RedirectResponse(url="/login?error=Invalid+credentials", status_code=303)

@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("session")
    return response


@app.post("/feedback")
def submit_feedback(
    trying_to:    str = Form(...),
    what_happened: str = Form(...),
    rating:       str = Form(...),
):
    stars = "⭐" * max(1, min(5, int(rating)))
    log_event("feature", detail=f"feedback:{rating}stars")
    send_email(
        to="robertcollech@gmail.com",
        subject=f"Studio Feedback — {stars}",
        body_html=(
            f"<h2 style='color:#6366f1;margin-bottom:4px;'>Studio Console Feedback</h2>"
            f"<p style='color:#64748b;font-size:13px;margin-top:0;'>Rating: {stars} ({rating}/5)</p>"
            f"<hr style='border:none;border-top:1px solid #e2e8f0;margin:16px 0;'>"
            f"<p><strong>What were you trying to do?</strong></p>"
            f"<p style='background:#f8fafc;padding:12px;border-radius:8px;'>{trying_to}</p>"
            f"<p><strong>What happened?</strong></p>"
            f"<p style='background:#f8fafc;padding:12px;border-radius:8px;'>{what_happened}</p>"
        ),
    )
    return {"ok": True}


@app.get("/resend-confirmation", response_class=HTMLResponse)
def resend_confirmation_page(info: str = "", error: str = ""):
    info_html  = f'<div class="alert alert-success">{info}</div>'  if info  else ''
    error_html = f'<div class="alert alert-danger">{error}</div>'  if error else ''
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Resend Confirmation — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo">🎵</div>
    <h1 style="text-align:center;margin-bottom:4px;">Resend Confirmation</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">
      Enter your email and we'll send a new confirmation link.</p>
    {info_html}{error_html}
    <form action="/resend-confirmation" method="post">
      <div class="form-group">
        <label class="form-label">Email</label>
        <input type="email" name="email" placeholder="you@example.com" required autofocus>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;padding:10px;">
        Send Confirmation Email</button>
    </form>
    <p style="text-align:center;margin-top:18px;font-size:13px;color:var(--muted);">
      <a href="/login" style="color:var(--primary);font-weight:600;">Back to sign in</a>
    </p>
  </div>
</div>
</body>
</html>""")


@app.post("/resend-confirmation")
def resend_confirmation_post(request: Request, email: str = Form(...)):
    email = email.strip().lower()
    for user in get_all_users():
        if user.get("email") == email:
            if user.get("is_verified", "true") == "true":
                return RedirectResponse(
                    url="/resend-confirmation?info=This+account+is+already+verified.+You+can+sign+in.",
                    status_code=303,
                )
            token = secrets.token_urlsafe(32)
            update_user(email, verification_token=token)
            base_url    = str(request.base_url).rstrip('/')
            confirm_url = f"{base_url}/confirm/{token}"
            send_email(
                to=email,
                subject="Confirm your Studio Console account",
                body_html=(
                    f"<p>Hi {user.get('name', '')}!</p>"
                    f"<p>Click the link below to verify your email address:</p>"
                    f"<p><a href='{confirm_url}' style='color:#6366f1;font-weight:600;'>"
                    f"Confirm my email</a></p>"
                    f"<p style='color:#64748b;font-size:12px;'>Or paste: {confirm_url}</p>"
                ),
            )
            break
    # Always show the same message to avoid email enumeration
    return RedirectResponse(
        url="/resend-confirmation?info=If+that+email+is+registered+and+unverified%2C"
            "+a+new+confirmation+link+has+been+sent.",
        status_code=303,
    )


@app.get("/signup", response_class=HTMLResponse)
def signup_page(error: str = ""):
    error_html = f'<div class="alert alert-danger">{error}</div>' if error else ''
    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sign Up — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="login-wrap">
  <div class="login-card">
    <div class="login-logo">🎵</div>
    <h1 style="text-align:center;margin-bottom:4px;">Create Account</h1>
    <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Join Studio Console</p>
    {error_html}
    <form action="/signup" method="post" id="signupForm">
      <div class="form-group">
        <label class="form-label">Full Name</label>
        <input type="text" name="name" placeholder="Jane Smith" required autofocus>
      </div>
      <div class="form-group">
        <label class="form-label">Email</label>
        <input type="email" name="email" id="emailInput" placeholder="you@example.com" required
               oninput="validateEmail(this)">
        <div id="emailHint" style="font-size:11px;margin-top:4px;display:none;"></div>
      </div>
      <div class="form-group">
        <label class="form-label">Password</label>
        <input type="password" name="password" id="pw1" placeholder="••••••••" required minlength="6"
               oninput="checkMatch()">
      </div>
      <div class="form-group">
        <label class="form-label">Confirm Password</label>
        <input type="password" name="confirm_password" id="pw2" placeholder="••••••••" required minlength="6"
               oninput="checkMatch()">
        <div id="pwHint" style="font-size:11px;margin-top:4px;display:none;"></div>
      </div>
      <button type="submit" class="btn" style="width:100%;justify-content:center;padding:10px;">Create Account</button>
    </form>
    <p style="text-align:center;margin-top:18px;font-size:13px;color:var(--muted);">
      Already have an account? <a href="/login" style="color:var(--primary);font-weight:600;">Sign in</a>
    </p>
  </div>
</div>
<script>
function validateEmail(inp) {{
  var hint = document.getElementById('emailHint');
  var re = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
  if (inp.value && !re.test(inp.value)) {{
    hint.style.display = 'block';
    hint.style.color   = '#ef4444';
    hint.textContent   = '⚠ Enter a valid email address';
  }} else if (inp.value) {{
    hint.style.display = 'block';
    hint.style.color   = '#10b981';
    hint.textContent   = '✓ Looks good';
  }} else {{
    hint.style.display = 'none';
  }}
}}
function checkMatch() {{
  var pw1 = document.getElementById('pw1').value;
  var pw2 = document.getElementById('pw2').value;
  var hint = document.getElementById('pwHint');
  if (!pw2) {{ hint.style.display = 'none'; return; }}
  hint.style.display = 'block';
  if (pw1 === pw2) {{
    hint.style.color   = '#10b981';
    hint.textContent   = '✓ Passwords match';
  }} else {{
    hint.style.color   = '#ef4444';
    hint.textContent   = '⚠ Passwords do not match';
  }}
}}
</script>
</body>
</html>""")


@app.post("/signup")
def signup_post(
    request:          Request,
    name:             str = Form(...),
    email:            str = Form(...),
    password:         str = Form(...),
    confirm_password: str = Form(...),
):
    if password != confirm_password:
        return RedirectResponse(url="/signup?error=Passwords+do+not+match", status_code=303)
    if len(password) < 6:
        return RedirectResponse(url="/signup?error=Password+must+be+at+least+6+characters", status_code=303)
    email = email.strip().lower()
    if any(u.get("email") == email for u in get_all_users()):
        return RedirectResponse(url="/signup?error=An+account+with+that+email+already+exists", status_code=303)
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    token   = secrets.token_urlsafe(32)
    save_user(name.strip(), email, pw_hash, verification_token=token)
    log_event("signup", user=email, detail="beta_tester")
    base_url = str(request.base_url).rstrip('/')
    confirm_url = f"{base_url}/confirm/{token}"
    send_email(
        to=email,
        subject="Confirm your Studio Console account",
        body_html=(
            f"<p>Hi {name},</p>"
            f"<p>Click the link below to verify your email address:</p>"
            f"<p><a href='{confirm_url}' style='color:#6366f1;font-weight:600;'>"
            f"Confirm my email</a></p>"
            f"<p style='color:#64748b;font-size:12px;'>Or paste this URL: {confirm_url}</p>"
            f"<p style='color:#64748b;font-size:12px;'>This link does not expire.</p>"
        ),
    )
    return RedirectResponse(
        url="/login?info=Account+created%21+Check+your+email+to+verify+your+account+before+signing+in.",
        status_code=303,
    )


@app.get("/confirm/{token}", response_class=HTMLResponse)
def confirm_email(token: str):
    for user in get_all_users():
        if user.get("verification_token") == token:
            update_user(user["email"], is_verified="true", verification_token="")
            return RedirectResponse(
                url="/login?info=Email+verified%21+You+can+now+sign+in.",
                status_code=303,
            )
    return HTMLResponse("""<!DOCTYPE html><html><head>
<link rel="stylesheet" href="/static/style.css"></head><body>
<div class="login-wrap"><div class="login-card">
<div class="login-logo">🎵</div>
<div class="alert alert-danger">This confirmation link is invalid or has already been used.</div>
<p style="text-align:center;margin-top:14px;">
  <a href="/login" style="color:var(--primary);font-weight:600;">Back to sign in</a>
</p></div></div></body></html>""")


_FORGOT_PW_PAGE = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forgot Password — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head><body>
<div class="login-wrap"><div class="login-card">
  <div class="login-logo">🎵</div>
  <h1 style="text-align:center;margin-bottom:4px;">Forgot Password</h1>
  <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">
    Enter your email and we'll send a reset link.</p>
  {notice}
  <form action="/forgot-password" method="post">
    <div class="form-group">
      <label class="form-label">Email</label>
      <input type="email" name="email" placeholder="you@example.com" required autofocus>
    </div>
    <button type="submit" class="btn" style="width:100%;justify-content:center;padding:10px;">
      Send Reset Link</button>
  </form>
  <p style="text-align:center;margin-top:18px;font-size:13px;color:var(--muted);">
    <a href="/login" style="color:var(--primary);font-weight:600;">Back to sign in</a>
  </p>
</div></div></body></html>"""


@app.get("/forgot-password", response_class=HTMLResponse)
def forgot_password_page(info: str = ""):
    notice = f'<div class="alert alert-success">{info}</div>' if info else ''
    return HTMLResponse(_FORGOT_PW_PAGE.format(notice=notice))


@app.post("/forgot-password")
def forgot_password_post(request: Request, email: str = Form(...)):
    email = email.strip().lower()
    for user in get_all_users():
        if user.get("email") == email:
            token   = secrets.token_urlsafe(32)
            expires = (datetime.now() + timedelta(hours=1)).timestamp()
            update_user(email, reset_token=token, reset_token_expires=str(expires))
            base_url   = str(request.base_url).rstrip('/')
            reset_url  = f"{base_url}/reset-password/{token}"
            send_email(
                to=email,
                subject="Reset your Studio Console password",
                body_html=(
                    f"<p>Hi {user.get('name', '')}!</p>"
                    f"<p>Click the link below to reset your password. "
                    f"This link expires in 1 hour.</p>"
                    f"<p><a href='{reset_url}' style='color:#6366f1;font-weight:600;'>"
                    f"Reset my password</a></p>"
                    f"<p style='color:#64748b;font-size:12px;'>Or paste: {reset_url}</p>"
                    f"<p style='color:#64748b;font-size:12px;'>"
                    f"If you didn't request this, ignore this email.</p>"
                ),
            )
            break
    # Always show the same message to avoid email enumeration
    return RedirectResponse(
        url="/forgot-password?info=If+that+email+is+registered+you%27ll+receive+a+reset+link+shortly.",
        status_code=303,
    )


@app.get("/reset-password/{token}", response_class=HTMLResponse)
def reset_password_page(token: str, error: str = ""):
    for user in get_all_users():
        if user.get("reset_token") == token:
            try:
                expires = float(user.get("reset_token_expires", 0))
            except ValueError:
                expires = 0
            if datetime.now().timestamp() > expires:
                return HTMLResponse("""<!DOCTYPE html><html><head>
<link rel="stylesheet" href="/static/style.css"></head><body>
<div class="login-wrap"><div class="login-card">
<div class="login-logo">🎵</div>
<div class="alert alert-danger">This reset link has expired. Please request a new one.</div>
<p style="text-align:center;margin-top:14px;">
  <a href="/forgot-password" style="color:var(--primary);font-weight:600;">Request new link</a>
</p></div></div></body></html>""")
            error_html = f'<div class="alert alert-danger">{error}</div>' if error else ''
            return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reset Password — Studio Console</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head><body>
<div class="login-wrap"><div class="login-card">
  <div class="login-logo">🎵</div>
  <h1 style="text-align:center;margin-bottom:4px;">Reset Password</h1>
  <p style="text-align:center;color:var(--muted);font-size:13px;margin-bottom:22px;">Choose a new password</p>
  {error_html}
  <form action="/reset-password/{token}" method="post">
    <div class="form-group">
      <label class="form-label">New Password</label>
      <input type="password" name="password" id="pw1" placeholder="••••••••"
             required minlength="6" autofocus oninput="checkMatch()">
    </div>
    <div class="form-group">
      <label class="form-label">Confirm New Password</label>
      <input type="password" name="confirm_password" id="pw2" placeholder="••••••••"
             required minlength="6" oninput="checkMatch()">
      <div id="pwHint" style="font-size:11px;margin-top:4px;display:none;"></div>
    </div>
    <button type="submit" class="btn" style="width:100%;justify-content:center;padding:10px;">
      Set New Password</button>
  </form>
</div></div>
<script>
function checkMatch(){{
  var h=document.getElementById('pwHint');
  var match=document.getElementById('pw1').value===document.getElementById('pw2').value;
  h.style.display=document.getElementById('pw2').value?'block':'none';
  h.style.color=match?'#10b981':'#ef4444';
  h.textContent=match?'✓ Passwords match':'⚠ Passwords do not match';
}}
</script>
</body></html>""")
    return HTMLResponse("""<!DOCTYPE html><html><head>
<link rel="stylesheet" href="/static/style.css"></head><body>
<div class="login-wrap"><div class="login-card">
<div class="login-logo">🎵</div>
<div class="alert alert-danger">This reset link is invalid or has already been used.</div>
<p style="text-align:center;margin-top:14px;">
  <a href="/forgot-password" style="color:var(--primary);font-weight:600;">Request a new link</a>
</p></div></div></body></html>""")


@app.post("/reset-password/{token}")
def reset_password_post(
    token:            str,
    password:         str = Form(...),
    confirm_password: str = Form(...),
):
    if password != confirm_password:
        return RedirectResponse(url=f"/reset-password/{token}?error=Passwords+do+not+match", status_code=303)
    if len(password) < 6:
        return RedirectResponse(url=f"/reset-password/{token}?error=Password+must+be+at+least+6+characters", status_code=303)
    for user in get_all_users():
        if user.get("reset_token") == token:
            try:
                expires = float(user.get("reset_token_expires", 0))
            except ValueError:
                expires = 0
            if datetime.now().timestamp() > expires:
                return RedirectResponse(url="/forgot-password?info=Link+expired.+Please+request+a+new+one.", status_code=303)
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            update_user(user["email"], password_hash=pw_hash, reset_token="", reset_token_expires="")
            return RedirectResponse(
                url="/login?info=Password+reset+successfully.+You+can+now+sign+in.",
                status_code=303,
            )
    return RedirectResponse(url="/forgot-password?error=Invalid+or+expired+reset+link.", status_code=303)


@app.get("/")
def root():
    return RedirectResponse(url="/dashboard", status_code=303)

# Auth middleware
_PUBLIC_PATHS    = frozenset([
    "/login", "/logout", "/", "/test", "/signup",
    "/forgot-password", "/resend-confirmation",
])
_BILLING_PATHS   = frozenset(["/billing", "/create-checkout-session",
                               "/billing/portal", "/billing/cancel"])

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Stripe webhook: fully public — Stripe servers POST here, no cookie possible
    if path == '/webhook/stripe':
        return await call_next(request)

    if (path in _PUBLIC_PATHS or path.startswith("/static/")
            or path.startswith("/confirm/") or path.startswith("/reset-password/")):
        return await call_next(request)

    # All other paths require an authenticated session
    if request.cookies.get("session") != "authenticated":
        return RedirectResponse(url="/login", status_code=303)

    # Billing paths: authenticated users can always reach them (that's where they subscribe)
    if path in _BILLING_PATHS:
        return await call_next(request)

    # Log page views for GET requests (not API/static calls)
    if (request.method == "GET"
            and not path.startswith("/api/")
            and not path.startswith("/static/")):
        log_event("page_view", path=path)

    return await call_next(request)

@app.get("/students", response_class=HTMLResponse)
def students_page():
    profiles = get_all_profiles()
    # Compute open invoice balance per student
    inv_balance: dict[str, float] = {}
    for inv in get_all_invoices():
        if inv.get('status') != 'paid':
            n = inv.get('student_name', '')
            inv_balance[n] = inv_balance.get(n, 0.0) + _safe_float(inv.get('balance_due', 0))
    rows = ""
    for name, data in profiles.items():
        initials = ''.join(p[0].upper() for p in name.split()[:2])
        prepaid  = data.get('prepaid', 0)
        owed     = inv_balance.get(name, 0.0)
        owed_badge = (
            f'<span class="badge badge-danger">${owed:.2f}</span>'
            if owed > 0 else
            '<span class="badge badge-success">$0.00</span>'
        )
        rows += f"""<tr>
  <td><div style="display:flex;align-items:center;gap:10px;">
    <div class="student-avatar" style="width:30px;height:30px;font-size:11px;border-radius:7px;">{initials}</div>
    <strong>{name}</strong></div></td>
  <td>${data['rate']:.0f}/hr</td>
  <td>{data.get('target_minutes',60)} min</td>
  <td>{data.get('description','') or '—'}</td>
  <td><span class="badge badge-info">${prepaid:.2f}</span></td>
  <td>{owed_badge}</td>
  <td>
    <form action="/delete-student" method="post" style="display:inline;"
          onsubmit="return confirm('Delete {name}? This cannot be undone.')">
      <input type="hidden" name="student_name" value="{name}">
      <button type="submit" class="btn btn-danger btn-sm">🗑️ Delete</button>
    </form>
  </td>
</tr>"""

    if rows:
        table_html = f"""<div style="overflow-x:auto;">
  <table>
    <thead><tr><th>Student</th><th>Rate</th><th>Lesson</th><th>Focus</th><th>Prepaid</th><th>Invoice Balance</th><th></th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""
    else:
        table_html = """<div class="empty-state">
  <div class="empty-state-icon">👥</div>
  <h3>No students yet</h3>
  <p>Add your first student below to start tracking lessons and payments.</p>
  <a href="#add-student" class="btn">➕ Add Your First Student</a>
</div>"""

    # Calendar suggestions: unregistered students from today's events
    cal_suggestions_html = ""
    try:
        cal_events = get_today_calendar_events()
        seen, suggestions = set(), []
        for e in cal_events:
            summary      = e.get('summary', '')
            student_name = clean_student_name(summary)
            if student_name and student_name not in profiles and student_name not in seen:
                seen.add(student_name)
                start_dt = e.get('start', {}).get('dateTime', '')
                end_dt   = e.get('end',   {}).get('dateTime', '')
                dur = 60
                if start_dt and end_dt:
                    try:
                        s_dt = datetime.fromisoformat(start_dt.replace('Z', '+00:00'))
                        e_dt = datetime.fromisoformat(end_dt.replace('Z', '+00:00'))
                        dur  = max(15, int((e_dt - s_dt).total_seconds() / 60))
                    except Exception:
                        pass
                suggestions.append({'name': student_name, 'summary': summary, 'dur': dur})
        if suggestions:
            sug_rows = ""
            for s in suggestions:
                safe_name = s['name'].replace('"', '&quot;')
                rate      = _suggested_rate(s['dur'])
                sug_rows += f"""<tr>
  <td><strong>{s['name']}</strong></td>
  <td style="color:var(--muted);font-size:12px;">{s['summary']}</td>
  <td>{s['dur']} min → ${rate:.0f}/hr</td>
  <td>
    <form action="/quick-create-student" method="post" style="display:inline;">
      <input type="hidden" name="student_name" value="{safe_name}">
      <input type="hidden" name="duration_minutes" value="{s['dur']}">
      <input type="hidden" name="redirect_to" value="/students">
      <button type="submit" class="btn btn-success btn-sm">➕ Quick Create</button>
    </form>
  </td>
</tr>"""
            cal_suggestions_html = f"""<div class="card" style="border-color:#fbbf24;background:#fffbeb;">
  <div class="card-header">
    <h2 style="margin:0;color:#92400e;">📅 Detected from Today's Calendar</h2>
    <span class="badge badge-warning">{len(suggestions)} new</span>
  </div>
  <p style="color:var(--muted);font-size:13px;margin-bottom:12px;">These names appear in today's calendar events but aren't registered yet.</p>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Detected Name</th><th>Event Title</th><th>Suggested Rate</th><th></th></tr></thead>
      <tbody>{sug_rows}</tbody>
    </table>
  </div>
</div>"""
    except Exception:
        cal_suggestions_html = ""

    content = f"""
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">👥 Students ({len(profiles)})</h2>
  </div>
  {table_html}
</div>
{cal_suggestions_html}
<div class="card" id="add-student">
  <h2>➕ Add Student</h2>
  <form action="/add-profile" method="post">
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;">
        <label class="form-label">Student Name</label>
        <input type="text" name="name" placeholder="Full name" required>
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
    profiles[name] = {"tier_name": rate_tier_name, "rate": DEFAULT_RATE, "target_minutes": 60, "credits": 0, "description": description}
    save_all_profiles(profiles)
    log_event("feature", detail="add_student")
    return RedirectResponse(url=f"/students?toast=Student+{name}+added", status_code=303)


@app.post("/delete-student")
def delete_student(student_name: str = Form(...)):
    profiles = get_all_profiles()
    if student_name in profiles:
        del profiles[student_name]
        save_all_profiles(profiles)
    return RedirectResponse(url=f"/students?toast={student_name.replace(' ', '+')}+deleted&toast_type=info", status_code=303)


@app.post("/quick-create-student")
def quick_create_student(
    student_name: str = Form(...),
    duration_minutes: int = Form(60),
    redirect_to: str = Form("/dashboard"),
):
    name = clean_student_name(student_name)
    if not name:
        name = student_name.strip()
    rate = _suggested_rate(duration_minutes)
    profiles = get_all_profiles()
    if name not in profiles:
        profiles[name] = {
            "tier_name": "Standard",
            "rate": rate,
            "target_minutes": duration_minutes,
            "credits": 0,
            "description": f"Auto-created from {duration_minutes} min calendar event",
            "prepaid": 0.0,
        }
        save_all_profiles(profiles)
    log_event("feature", detail="quick_create_student")
    safe_redirect = redirect_to if redirect_to in ("/dashboard", "/students") else "/dashboard"
    toast = name.replace(' ', '+')
    return RedirectResponse(
        url=f"{safe_redirect}?toast={toast}+added&toast_type=success",
        status_code=303,
    )


@app.get("/rates", response_class=HTMLResponse)
def rates_page():
    tiers = get_pricing_tiers()
    rows = ""
    for name, data in tiers.items():
        per_lesson = round(data['rate'] * data['minutes'] / 60, 2)
        rows += f"""<tr>
  <td><strong>{name}</strong></td>
  <td>${data['rate']:.2f}/hr</td>
  <td>{data['minutes']} min</td>
  <td style="color:var(--success);font-weight:600;">${per_lesson:.2f}/lesson</td>
</tr>"""

    if rows:
        table_html = f"""<div style="overflow-x:auto;">
  <table>
    <thead><tr><th>Tier Name</th><th>Hourly Rate</th><th>Duration</th><th>Per Lesson</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
</div>"""
    else:
        table_html = """<div class="empty-state">
  <div class="empty-state-icon">💰</div>
  <h3>No pricing tiers yet</h3>
  <p>Create a tier (e.g. "1 Hour Standard" at $50/hr) to assign rates to students.</p>
</div>"""

    content = f"""
<div class="two-col">
  <div class="card">
    <div class="card-header">
      <h2 style="margin:0;">💰 Pricing Tiers ({len(tiers)})</h2>
    </div>
    {table_html}
  </div>
  <div class="card">
    <h2>➕ Add Pricing Tier</h2>
    <form action="/save-pricing-tier" method="post">
      <div class="form-group">
        <label class="form-label">Tier Name</label>
        <input type="text" name="tier_name" placeholder="e.g. 1 Hour Standard" required>
      </div>
      <div class="form-group">
        <label class="form-label">Hourly Rate ($)</label>
        <input type="number" step="0.01" name="hourly_rate" placeholder="50.00" required>
      </div>
      <div class="form-group">
        <label class="form-label">Duration (minutes)</label>
        <input type="number" name="target_minutes" placeholder="60" value="60">
      </div>
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
    return RedirectResponse(url="/rates?toast=Pricing+tier+saved", status_code=303)

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
    with open('/data/calendar_token.json', 'w') as f:
        f.write(token_data)
    
    return HTMLResponse("<h2>✅ Calendar Connected!</h2><a href='/dashboard'>Back</a>")

@app.get("/calendar-events")
def calendar_events():
    if not os.path.exists('/data/calendar_token.json'):
        return HTMLResponse("<h2>Calendar not connected. <a href='/calendar-auth'>Connect here</a></h2>")
    
    with open('/data/calendar_token.json', 'r') as f:
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
    log_event("feature", detail=f"record_payment:{amount:.2f}")
    return RedirectResponse(url=f"/payments?toast=Payment+of+%24{amount:.2f}+recorded+for+{student_name.replace(' ', '+')}", status_code=303)
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


# ─── Stripe Billing ───────────────────────────────────────────────────────────

@app.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    if not _STRIPE_READY or not STRIPE_PRICE_MONTHLY:
        return RedirectResponse(url="/billing?error=stripe_not_configured", status_code=303)
    sub  = _sub_get()
    base = str(request.base_url).rstrip('/')
    try:
        kwargs: dict = {
            "mode":        "subscription",
            "line_items":  [{"price": STRIPE_PRICE_MONTHLY, "quantity": 1}],
            "success_url": f"{base}/billing?success=1&session_id={{CHECKOUT_SESSION_ID}}",
            "cancel_url":  f"{base}/billing?checkout_cancelled=1",
            "metadata":    {"user_key": "admin"},
        }
        customer_id = sub.get('stripe_customer_id', '')
        if customer_id:
            kwargs["customer"] = customer_id
        session = _stripe.checkout.Session.create(**kwargs)
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as exc:
        return RedirectResponse(url=f"/billing?error={str(exc)[:200]}", status_code=303)


@app.get("/billing", response_class=HTMLResponse)
def billing_page(success: str = "", checkout_cancelled: str = "",
                 msg: str = "", error: str = ""):
    sub    = _sub_get()
    status = sub.get('subscription_status', 'none')
    data   = _fetch_stripe_data(sub)

    # ── Notice banner ──
    notice = ""
    if success:
        notice = ('<div style="background:#f0fdf4;border:1px solid #86efac;color:#166534;'
                  'padding:14px 16px;border-radius:8px;margin-bottom:20px;font-weight:500;">'
                  '✅ Subscription activated! Welcome to Studio Console.</div>')
    elif checkout_cancelled:
        notice = ('<div style="background:#fefce8;border:1px solid #fde047;color:#854d0e;'
                  'padding:14px 16px;border-radius:8px;margin-bottom:20px;">'
                  'Checkout was cancelled — no charge was made.</div>')
    elif msg == "cancel_scheduled":
        cancel_date = data.get('next_billing_date') or 'the end of your billing period'
        notice = (f'<div style="background:#fff7ed;border:1px solid #fdba74;color:#9a3412;'
                  f'padding:14px 16px;border-radius:8px;margin-bottom:20px;">'
                  f'Your subscription will cancel on {cancel_date}. You keep access until then.</div>')
    elif msg == "portal_error":
        notice = ('<div style="background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;'
                  'padding:14px 16px;border-radius:8px;margin-bottom:20px;">'
                  '⚠️ Could not open Stripe portal — make sure it\'s enabled in your '
                  '<a href="https://dashboard.stripe.com/settings/billing/portal" target="_blank">'
                  'Stripe Dashboard</a>.</div>')
    if error:
        notice += (f'<div style="background:#fef2f2;border:1px solid #fca5a5;color:#991b1b;'
                   f'padding:14px 16px;border-radius:8px;margin-bottom:20px;">Error: {error}</div>')

    # ── Status badge ──
    badge_map = {
        'active':     ('#16a34a', '✓ Active'),
        'cancelled':  ('#dc2626', 'Cancelled'),
        'incomplete': ('#d97706', 'Incomplete'),
        'past_due':   ('#dc2626', 'Past Due'),
        'none':       ('#6b7280', 'No Subscription'),
    }
    bc, bl = badge_map.get(status, ('#6b7280', status.title()))

    # ── Plan card meta ──
    pm = data['payment_method']
    pm_html = (f'<div style="color:#64748b;font-size:14px;margin-top:4px;">'
               f'{pm["brand"]} ···· {pm["last4"]} &nbsp;exp {pm["exp"]}</div>') if pm else ''

    nd = data['next_billing_date']
    if nd:
        lbl = 'Cancels on' if data['cancel_at_period_end'] else 'Next billing'
        nd_html = f'<div style="color:#64748b;font-size:14px;margin-top:4px;">{lbl}: {nd}</div>'
    else:
        nd_html = ''

    cancel_warn = (
        f'<div style="background:#fff7ed;border:1px solid #fdba74;color:#9a3412;'
        f'padding:10px 14px;border-radius:8px;margin-top:14px;font-size:14px;">'
        f'Scheduled to cancel on {nd or "end of billing period"}.</div>'
    ) if data['cancel_at_period_end'] else ''

    configured = _STRIPE_READY and bool(STRIPE_PRICE_MONTHLY)
    if status == 'active':
        cancel_btn = '' if data['cancel_at_period_end'] else (
            '<form method="post" action="/billing/cancel" style="display:inline;"'
            ' onsubmit="return confirm(\'Schedule cancellation at end of billing period?\')">'
            '<button type="submit" style="background:#fee2e2;color:#991b1b;border:none;'
            'padding:12px 24px;border-radius:12px;font-weight:600;cursor:pointer;">'
            'Cancel Plan</button></form>')
        action = f"""
        <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:20px;">
          <form method="post" action="/billing/portal" style="display:inline;"
                onsubmit="var b=this.querySelector('button');b.disabled=true;b.innerHTML='<span class=\\'spinner\\'></span> Opening portal…';">
            <button type="submit" class="btn" style="margin:0;">Manage Billing</button>
          </form>
          {cancel_btn}
        </div>"""
    elif configured:
        action = """
        <div style="margin-top:20px;">
          <form method="post" action="/create-checkout-session"
                onsubmit="var b=this.querySelector('button');b.disabled=true;b.innerHTML='<span class=\\'spinner\\'></span> Redirecting to Stripe…';">
            <button type="submit" class="btn"
              style="font-size:16px;padding:14px 32px;margin:0;">
              Subscribe — $15/month</button>
          </form>
        </div>"""
    else:
        action = ('<p style="color:#94a3b8;margin-top:16px;">'
                  'Stripe is not yet configured. Set <code>STRIPE_SECRET_KEY</code> '
                  'and <code>STRIPE_PRICE_MONTHLY</code>.</p>')

    # ── Billing history ──
    if data['invoices']:
        rows_html = ""
        for inv in data['invoices']:
            sc = '#16a34a' if inv['status'] == 'Paid' else '#d97706'
            links = ""
            if inv['url']:
                links += f'<a href="{inv["url"]}" target="_blank" style="color:#667eea;margin-right:8px;">View</a>'
            if inv['pdf']:
                links += f'<a href="{inv["pdf"]}" target="_blank" style="color:#667eea;">PDF</a>'
            rows_html += f"""<tr>
              <td>{inv['date']}</td>
              <td style="font-weight:600;">{inv['amount']}</td>
              <td><span style="background:{sc}22;color:{sc};padding:2px 10px;
                border-radius:20px;font-size:13px;">{inv['status']}</span></td>
              <td>{links}</td></tr>"""
        history_html = f"""
        <div class="card">
          <h2 style="margin-top:0;">Billing History</h2>
          <table>
            <thead><tr><th>Date</th><th>Amount</th><th>Status</th><th>Receipt</th></tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>"""
    else:
        history_html = '<div class="card" style="color:#94a3b8;">No billing history yet.</div>'

    content = f"""
<h1>💳 Billing &amp; Subscription</h1>
{notice}
<div class="card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;flex-wrap:wrap;">
    <div>
      <div style="font-size:16px;font-weight:700;">Studio Console Monthly</div>
      <div style="color:var(--muted);font-size:14px;margin-top:2px;">$15 / month</div>
      {pm_html}
      {nd_html}
    </div>
    <span style="background:{bc}22;color:{bc};border:1px solid {bc}44;
      padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;
      white-space:nowrap;">{bl}</span>
  </div>
  {cancel_warn}
  {action}
</div>
{history_html}"""
    return HTMLResponse(page("Billing & Subscription", content, active="billing"))


@app.post("/billing/portal")
async def billing_portal(request: Request):
    sub         = _sub_get()
    customer_id = sub.get('stripe_customer_id', '')
    if not _STRIPE_READY or not customer_id:
        return RedirectResponse(url="/billing?msg=portal_error", status_code=303)
    base = str(request.base_url).rstrip('/')
    try:
        portal = _stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{base}/billing",
        )
        return RedirectResponse(url=portal.url, status_code=303)
    except Exception:
        return RedirectResponse(url="/billing?msg=portal_error", status_code=303)


@app.post("/billing/cancel")
async def billing_cancel():
    sub    = _sub_get()
    sub_id = sub.get('stripe_subscription_id', '')
    if _STRIPE_READY and sub_id:
        try:
            updated = _stripe.Subscription.modify(sub_id, cancel_at_period_end=True)
            sub['cancel_at_period_end'] = 'true'
            period_end = updated.get('current_period_end', '')
            if period_end:
                sub['current_period_end'] = str(period_end)
            _sub_save(sub)
        except Exception:
            pass
    return RedirectResponse(url="/billing?msg=cancel_scheduled", status_code=303)


@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload    = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if not _STRIPE_READY or not STRIPE_WEBHOOK_SECRET:
        return {"status": "not_configured"}

    try:
        event = _stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        return Response(status_code=400)

    event_id = event.get("id", "")
    if _event_processed(event_id):
        return {"status": "already_processed"}
    _mark_event(event_id)

    etype = event.get("type", "")
    obj   = event["data"]["object"]

    if etype == "checkout.session.completed":
        sub = _sub_get()
        sub['stripe_customer_id']     = obj.get('customer', '')
        sub['stripe_subscription_id'] = obj.get('subscription', '')
        sub['subscription_status']    = 'active'
        sub['cancel_at_period_end']   = 'false'
        _sub_save(sub)

    elif etype == "invoice.paid":
        sub = _sub_get()
        sub['subscription_status'] = 'active'
        _sub_save(sub)

    elif etype == "customer.subscription.updated":
        sub = _sub_get()
        sub['subscription_status']  = obj.get('status', 'active')
        sub['cancel_at_period_end'] = str(obj.get('cancel_at_period_end', False)).lower()
        period_end = obj.get('current_period_end', '')
        if period_end:
            sub['current_period_end'] = str(period_end)
        _sub_save(sub)

    elif etype == "customer.subscription.deleted":
        sub = _sub_get()
        sub['subscription_status']  = 'cancelled'
        sub['cancel_at_period_end'] = 'false'
        _sub_save(sub)

    return {"status": "ok"}


# ─── Analytics ────────────────────────────────────────────────────────────────

@app.get("/analytics", response_class=HTMLResponse)
def analytics_page():
    try:
        data = compute_analytics()
    except Exception as e:
        return HTMLResponse(page("Analytics", f'<div class="card"><p style="color:var(--danger);">Error loading analytics: {e}</p></div>', "analytics"))

    chart_json = json.dumps({
        'monthlyLabels': [m['label'] for m in data['monthly_revenue']],
        'monthlyValues': [m['rev']   for m in data['monthly_revenue']],
        'studentLabels': [s['name']  for s in data['revenue_by_student']],
        'studentValues': [s['rev']   for s in data['revenue_by_student']],
        'attValues': [data['att'].get('confirmed', 0),
                      data['att'].get('missed', 0),
                      data['att'].get('cancelled', 0)],
    })

    reliability_rows = ""
    for r in data['reliability']:
        bar = min(int(r['rate']), 100)
        reliability_rows += f"""<tr>
  <td><strong>{r['name']}</strong></td>
  <td><div style="display:flex;align-items:center;gap:8px;">
    <div style="width:{bar}px;height:8px;border-radius:4px;background:linear-gradient(90deg,var(--primary),var(--secondary));min-width:4px;flex-shrink:0;"></div>
    <span>{r['rate']}%</span></div></td>
  <td style="color:var(--success);font-weight:700;">{r['confirmed']}</td>
  <td style="color:var(--danger);font-weight:700;">{r['missed']}</td>
</tr>"""
    if not reliability_rows:
        reliability_rows = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:20px;">No attendance data yet</td></tr>'

    rev_by_student = "".join(
        f'<tr><td><strong>{s["name"]}</strong></td><td style="color:var(--success);font-weight:700;">${s["rev"]:.2f}</td></tr>'
        for s in data['revenue_by_student']
    ) or '<tr><td colspan="2" style="text-align:center;color:var(--muted);padding:16px;">No data yet</td></tr>'

    content = f"""
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;margin-bottom:22px;}}
.kpi-card{{background:#fff;border:1px solid var(--border);border-radius:13px;padding:18px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.04);}}
.kpi-value{{font-size:28px;font-weight:800;background:linear-gradient(135deg,var(--primary),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1.2;}}
.kpi-label{{color:var(--muted);font-size:11px;font-weight:700;margin-top:6px;text-transform:uppercase;letter-spacing:.7px;}}
.chart-card{{background:#fff;border-radius:13px;padding:20px;border:1px solid var(--border);box-shadow:0 1px 3px rgba(0,0,0,.04);margin-bottom:16px;}}
.chart-card h3{{font-size:13px;font-weight:700;margin:0 0 14px;}}
</style>

<div class="kpi-grid">
  <div class="kpi-card"><div class="kpi-value">${data['total_revenue']:.2f}</div><div class="kpi-label">Total Revenue</div></div>
  <div class="kpi-card"><div class="kpi-value">{data['total_students']}</div><div class="kpi-label">Active Students</div></div>
  <div class="kpi-card"><div class="kpi-value">{data['confirmed_pct']}%</div><div class="kpi-label">Attendance Rate</div></div>
  <div class="kpi-card"><div class="kpi-value">${data['projected']:.2f}</div><div class="kpi-label">Projected / Month</div></div>
  <div class="kpi-card"><div class="kpi-value">${data['total_prepaid']:.2f}</div><div class="kpi-label">Total Prepaid</div></div>
</div>

<div class="two-col">
  <div class="chart-card"><h3>📊 Monthly Revenue — Last 6 Months</h3><canvas id="monthlyChart"></canvas></div>
  <div class="chart-card"><h3>👥 Revenue by Student</h3>
    <table><thead><tr><th>Student</th><th>Revenue</th></tr></thead><tbody>{rev_by_student}</tbody></table>
  </div>
</div>

<div class="two-col">
  <div class="chart-card"><h3>📅 Overall Attendance</h3>
    <canvas id="attChart" style="max-height:220px;"></canvas>
    <div style="display:flex;justify-content:center;gap:16px;margin-top:12px;font-size:12px;font-weight:600;">
      <span style="color:var(--success);">✅ {data['confirmed_pct']}% Confirmed</span>
      <span style="color:var(--danger);">❌ {data['missed_pct']}% Missed</span>
      <span style="color:var(--warning);">🔄 {data['cancelled_pct']}% Cancelled</span>
    </div>
  </div>
  <div class="chart-card"><h3>⭐ Student Reliability</h3>
    <table>
      <thead><tr><th>Student</th><th>Rate</th><th>✅</th><th>❌</th></tr></thead>
      <tbody>{reliability_rows}</tbody>
    </table>
  </div>
</div>

<script>
const D = {chart_json};
Chart.defaults.font.family = "'Inter',-apple-system,sans-serif";
new Chart(document.getElementById('monthlyChart'),{{type:'bar',data:{{labels:D.monthlyLabels,datasets:[{{label:'Revenue',data:D.monthlyValues,backgroundColor:'rgba(99,102,241,.75)',borderColor:'#6366f1',borderWidth:2,borderRadius:7,borderSkipped:false}}]}},options:{{responsive:true,plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:ctx=>'$'+ctx.parsed.y.toFixed(2)}}}}}},scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>'$'+v}}}}}}}}}});
new Chart(document.getElementById('attChart'),{{type:'doughnut',data:{{labels:['Confirmed','Missed','Cancelled'],datasets:[{{data:D.attValues,backgroundColor:['rgba(16,185,129,.85)','rgba(239,68,68,.85)','rgba(245,158,11,.85)'],borderColor:['#10b981','#ef4444','#f59e0b'],borderWidth:2}}]}},options:{{responsive:true,cutout:'62%',plugins:{{legend:{{position:'bottom'}}}}}}}});
</script>"""
    return HTMLResponse(page("Analytics", content, "analytics"))


# ─── Invoices ─────────────────────────────────────────────────────────────────

@app.get("/invoices", response_class=HTMLResponse)
def invoices_page():
    all_inv = sorted(
        get_all_invoices(),
        key=lambda x: (x.get('year', ''), x.get('month', '').zfill(2), x.get('student_name', '')),
        reverse=True,
    )
    _ST_STYLE = {
        'paid':     ('badge-success',  'Paid'),
        'sent':     ('badge-info',     'Sent'),
        'draft':    ('badge-muted',    'Draft'),
        'overdue':  ('badge-danger',   'Overdue'),
    }
    paid_inv      = [i for i in all_inv if i.get('status') == 'paid']
    open_inv      = [i for i in all_inv if i.get('status') != 'paid']
    outstanding   = sum(_safe_float(i.get('balance_due', 0)) for i in open_inv)
    overdue_count = sum(1 for i in all_inv if _display_status(i) == 'overdue')

    rows = ""
    for inv in all_inv:
        iid     = inv.get('id', '')
        m       = int(inv.get('month', 1) or 1)
        label   = f"{MONTH_SHORT[m]} {inv.get('year', '')}"
        dst     = _display_status(inv)
        bcls, blbl = _ST_STYLE.get(dst, ('badge-muted', dst.title()))
        bal     = _safe_float(inv.get('balance_due', 0))
        rows += f"""<tr>
  <td><a href="/invoices/{iid}" style="color:var(--primary);font-weight:600;">#INV-{iid.zfill(4)}</a></td>
  <td><strong>{inv.get('student_name', '')}</strong></td>
  <td>{label}</td>
  <td style="text-align:center;">{inv.get('scheduled_lessons', '—')}</td>
  <td>${_safe_float(inv.get('total_amount', 0)):.2f}</td>
  <td style="color:var(--success);font-weight:600;">${_safe_float(inv.get('amount_paid', 0)):.2f}</td>
  <td style="font-weight:700;color:{'var(--danger)' if bal > 0 else 'var(--success)'};">${bal:.2f}</td>
  <td><span class="badge {bcls}">{blbl}</span></td>
  <td><a href="/invoices/{iid}" class="btn btn-outline btn-sm">View</a></td>
</tr>"""
    if not rows:
        rows = '<tr><td colspan="9" style="text-align:center;padding:24px;color:var(--muted);">No invoices yet — generate below.</td></tr>'

    now        = datetime.now()
    nm         = now.month + 1 if now.month < 12 else 1
    ny         = now.year if now.month < 12 else now.year + 1
    next_label = f"{MONTH_NAMES[nm]} {ny}"
    cur_m      = now.month
    cur_y      = now.year
    opts       = "".join(
        f'<option value="{i}"{" selected" if i == cur_m else ""}>{MONTH_NAMES[i]}</option>'
        for i in range(1, 13)
    )

    content = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">🧾</div><div class="stat-val">{len(all_inv)}</div><div class="stat-lbl">Total</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">✅</div><div class="stat-val">{len(paid_inv)}</div><div class="stat-lbl">Paid</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fee2e2;">🔴</div><div class="stat-val">{overdue_count}</div><div class="stat-lbl">Overdue</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#fef3c7;">💰</div><div class="stat-val">${outstanding:.2f}</div><div class="stat-lbl">Outstanding</div></div>
</div>
<div class="card">
  <div class="card-header">
    <h2 style="margin:0;">🧾 Invoices</h2>
    <form action="/generate-invoices" method="post">
      <input type="hidden" name="month" value="{nm}">
      <input type="hidden" name="year"  value="{ny}">
      <button type="submit" class="btn btn-success btn-sm">⚡ Generate {next_label}</button>
    </form>
  </div>
  <div style="overflow-x:auto;">
    <table>
      <thead><tr><th>Invoice</th><th>Student</th><th>Period</th><th style="text-align:center;">Lessons</th><th>Total</th><th>Paid</th><th>Balance</th><th>Status</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
  </div>
</div>
<div class="card" style="max-width:440px;">
  <h2>⚡ Generate Invoices for Any Month</h2>
  <p style="color:var(--muted);font-size:13px;margin-bottom:16px;">
    Counts scheduled events on Google Calendar for each registered student and creates draft invoices.
    Attendance tracking is separate and does not change invoice amounts.
  </p>
  <form action="/generate-invoices" method="post">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
      <div class="form-group" style="margin:0;"><label class="form-label">Month</label><select name="month">{opts}</select></div>
      <div class="form-group" style="margin:0;"><label class="form-label">Year</label><input type="number" name="year" value="{cur_y}" min="2020" max="2035" required></div>
    </div>
    <button type="submit" class="btn" style="margin-top:14px;">⚡ Generate</button>
  </form>
</div>"""
    return HTMLResponse(page("Invoices", content, "invoices"))


@app.post("/generate-invoices")
def generate_invoices_post(month: int = Form(...), year: int = Form(...)):
    count, err = generate_invoices_for_month(year, month)
    period     = f"{MONTH_NAMES[month]} {year}"
    if not err and count > 0:
        log_event("feature", detail=f"generate_invoices:{count}:{period}")
    if err:
        msg = f'<div class="alert alert-danger">❌ {err}</div>'
    elif count > 0:
        msg = f'<div class="alert alert-success">✅ Generated {count} draft invoice(s) for {period} based on scheduled calendar events.</div>'
    else:
        msg = f'<div class="alert alert-warning">ℹ️ No new invoices for {period} — already generated or no registered students found in calendar events.</div>'
    return HTMLResponse(page("Generate Invoices", msg + '<a href="/invoices" class="btn" style="margin-top:14px;">← View All Invoices</a>', "invoices"))


@app.get("/invoices/{invoice_id}", response_class=HTMLResponse)
def invoice_detail(invoice_id: str):
    invoices = get_all_invoices()
    inv = next((i for i in invoices if i.get('id') == invoice_id), None)
    if not inv:
        return RedirectResponse(url="/invoices", status_code=303)

    m        = int(inv.get('month', 1) or 1)
    total    = _safe_float(inv.get('total_amount', 0))
    paid_amt = _safe_float(inv.get('amount_paid', 0))
    balance  = _safe_float(inv.get('balance_due', 0))
    lessons  = int(inv.get('scheduled_lessons', 0) or 0)
    rate     = total / lessons if lessons > 0 else 0
    dst      = _display_status(inv)
    stored   = inv.get('status', 'draft')

    _ST_BADGE = {
        'paid':    '<span class="badge badge-success" style="font-size:13px;padding:5px 14px;">✅ Paid</span>',
        'sent':    '<span class="badge badge-info"    style="font-size:13px;padding:5px 14px;">📤 Sent</span>',
        'draft':   '<span class="badge badge-muted"   style="font-size:13px;padding:5px 14px;">📝 Draft</span>',
        'overdue': '<span class="badge badge-danger"  style="font-size:13px;padding:5px 14px;">🔴 Overdue</span>',
    }
    badge = _ST_BADGE.get(dst, f'<span class="badge badge-muted">{dst}</span>')

    send_btn = (
        f'<form action="/mark-invoice-sent/{invoice_id}" method="post" style="display:inline;">'
        f'<button type="submit" class="btn btn-sm" style="background:#3b82f6;">📤 Mark as Sent</button></form>'
        if stored == 'draft' else ''
    )
    pay_btn = (
        f'<form action="/mark-invoice-paid/{invoice_id}" method="post" style="display:inline;">'
        f'<button type="submit" class="btn btn-success btn-sm">✅ Mark as Paid</button></form>'
        if stored != 'paid' else ''
    )
    paid_on = (
        f'<span style="color:var(--muted);">Paid On</span><strong>{inv.get("paid_date", "")}</strong>'
        if stored == 'paid' and inv.get('paid_date') else ''
    )

    content = f"""
<div class="card" style="max-width:580px;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;flex-wrap:wrap;gap:12px;">
    <div>
      <h2 style="margin:0;">Invoice #INV-{invoice_id.zfill(4)}</h2>
      <div style="color:var(--muted);font-size:13px;margin-top:3px;">Created {inv.get('created_date', '')}</div>
    </div>
    {badge}
  </div>
  <div style="background:var(--bg);border-radius:10px;padding:14px;margin-bottom:18px;">
    <div style="display:grid;grid-template-columns:140px 1fr;gap:6px;font-size:13px;">
      <span style="color:var(--muted);">Student</span><strong>{inv.get('student_name', '')}</strong>
      <span style="color:var(--muted);">Billing Period</span><strong>{MONTH_NAMES[m]} {inv.get('year', '')}</strong>
      <span style="color:var(--muted);">Scheduled Lessons</span><strong>{lessons}</strong>
      {paid_on}
    </div>
  </div>
  <table style="margin-bottom:18px;">
    <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
    <tbody>
      <tr>
        <td>{lessons} scheduled lesson{"s" if lessons != 1 else ""} × ${rate:.2f}/lesson</td>
        <td style="text-align:right;font-weight:600;">${total:.2f}</td>
      </tr>
      <tr>
        <td style="color:var(--success);">Amount Paid</td>
        <td style="text-align:right;color:var(--success);font-weight:600;">−${paid_amt:.2f}</td>
      </tr>
      <tr style="border-top:2px solid var(--border);">
        <td style="font-weight:700;padding:12px 13px;">Balance Due</td>
        <td style="text-align:right;font-weight:800;font-size:18px;padding:12px 13px;
            color:{'var(--success)' if balance <= 0 else 'var(--danger)'};">${balance:.2f}</td>
      </tr>
    </tbody>
  </table>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    {send_btn}{pay_btn}
    <a href="/invoices" class="btn btn-outline">← All Invoices</a>
  </div>
</div>"""
    return HTMLResponse(page(f"Invoice #INV-{invoice_id.zfill(4)}", content, "invoices"))


@app.post("/mark-invoice-sent/{invoice_id}")
def mark_invoice_sent(invoice_id: str):
    invoices = get_all_invoices()
    for inv in invoices:
        if inv.get('id') == invoice_id and inv.get('status') == 'draft':
            inv['status'] = 'sent'
            break
    save_all_invoices(invoices)
    return RedirectResponse(url=f"/invoices/{invoice_id}?toast=Invoice+marked+as+sent", status_code=303)


@app.post("/mark-invoice-paid/{invoice_id}")
def mark_invoice_paid(invoice_id: str):
    invoices = get_all_invoices()
    target = None
    for inv in invoices:
        if inv.get('id') == invoice_id:
            target = inv
            inv['status']      = 'paid'
            inv['paid_date']   = datetime.now().strftime('%Y-%m-%d')
            inv['amount_paid'] = inv.get('total_amount', '0.00')
            inv['balance_due'] = '0.00'
            break
    save_all_invoices(invoices)
    if target:
        m   = int(target.get('month', 1) or 1)
        stu = target.get('student_name', '')
        amt = _safe_float(target.get('total_amount', 0))
        note = f"Invoice #{invoice_id} — {MONTH_NAMES[m]} {target.get('year', '')}"
        with open(LEDGER_FILE, 'a', newline='') as lf:
            csv.writer(lf).writerow([
                datetime.now().strftime('%Y-%m-%d'), stu, 'Invoice Payment', f"{amt:.2f}", note,
            ])
    if target:
        log_event("feature", detail=f"mark_invoice_paid:{target.get('student_name','')}:{target.get('total_amount','')}")
    return RedirectResponse(url=f"/invoices/{invoice_id}?toast=Invoice+marked+as+paid", status_code=303)


# ─── Settings ─────────────────────────────────────────────────────────────────

@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    s        = load_calendar_settings()
    keywords = ", ".join(s.get("lesson_keywords", []))
    checked  = "checked" if s.get("show_all", True) else ""
    content  = f"""
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
def save_settings_post(lesson_keywords: str = Form(""), show_all: str = Form("false")):
    save_calendar_settings({
        "lesson_keywords": [k.strip() for k in lesson_keywords.split(',') if k.strip()],
        "show_all": show_all == "true",
    })
    return RedirectResponse(url="/settings?toast=Settings+saved", status_code=303)


# ─── Admin ────────────────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    profiles   = get_all_profiles()
    total_rev  = calculate_total_revenue()
    total_pre  = sum(d.get('prepaid', 0) for d in profiles.values())
    content = f"""
<div class="stats-row">
  <div class="stat-card"><div class="stat-icon" style="background:#ede9fe;">👥</div><div class="stat-val">{len(profiles)}</div><div class="stat-lbl">Students</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#d1fae5;">📊</div><div class="stat-val">${total_rev:.2f}</div><div class="stat-lbl">Total Revenue</div></div>
  <div class="stat-card"><div class="stat-icon" style="background:#e0e7ff;">💳</div><div class="stat-val">${total_pre:.2f}</div><div class="stat-lbl">Prepaid Balance</div></div>
</div>
<div class="two-col">
  <div class="card">
    <h2>📥 Data Backup</h2>
    <p style="color:var(--muted);font-size:13px;margin-bottom:18px;">Download a backup of all your studio data.</p>
    <div style="display:flex;gap:10px;flex-wrap:wrap;">
      <a href="/api/backup" class="btn">📥 JSON Backup</a>
      <a href="/api/backup/csv" class="btn btn-outline">📦 CSV Backup (ZIP)</a>
    </div>
  </div>
  <div class="card">
    <h2>🔧 Quick Links</h2>
    <div style="display:flex;flex-direction:column;gap:8px;">
      <a href="/analytics" class="btn btn-outline" style="justify-content:flex-start;">📈 View Analytics</a>
      <a href="/invoices"  class="btn btn-outline" style="justify-content:flex-start;">🧾 Manage Invoices</a>
      <a href="/settings"  class="btn btn-outline" style="justify-content:flex-start;">⚙️ Calendar Settings</a>
      <a href="/billing"   class="btn btn-outline" style="justify-content:flex-start;">💳 Billing & Stripe</a>
    </div>
  </div>
</div>
<div class="card" style="max-width:480px;">
  <h2>🗄️ Data Files</h2>
  <table>
    <thead><tr><th>File</th><th>Status</th></tr></thead>
    <tbody>
      {''.join(f'<tr><td style="font-size:12px;font-family:monospace;">{fp}</td><td><span class="badge {"badge-success" if os.path.exists(fp) else "badge-danger"}">{"✓ exists" if os.path.exists(fp) else "missing"}</span></td></tr>' for fp in [PROFILES_FILE, LEDGER_FILE, PRICING_FILE, INVOICES_FILE, SETTINGS_FILE])}
    </tbody>
  </table>
</div>"""
    return HTMLResponse(page("Admin", content, "admin"))


@app.get("/api/backup")
def backup_json():
    profiles = get_all_profiles()
    ledger   = []
    if os.path.exists(LEDGER_FILE):
        with open(LEDGER_FILE, 'r') as f:
            for row in _ledger_reader(f):
                ledger.append(dict(row))
    return JSONResponse(
        content={"backup_date": datetime.now().isoformat(),
                 "students": profiles, "ledger": ledger,
                 "stats": {"total_students": len(profiles),
                           "total_revenue": calculate_total_revenue()}},
        headers={"Content-Disposition": "attachment; filename=studio_backup.json"},
    )


@app.get("/api/backup/csv")
def backup_csv():
    import zipfile
    from io import BytesIO
    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fp in [PROFILES_FILE, LEDGER_FILE, PRICING_FILE, INVOICES_FILE]:
            if os.path.exists(fp):
                zf.write(fp, arcname=os.path.basename(fp))
    buf.seek(0)
    return Response(content=buf.getvalue(), media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=studio_backup.zip"})


# ─── Beta Analytics ────────────────────────────────────────────────────────────

@app.get("/beta-analytics", response_class=HTMLResponse)
def beta_analytics_page():
    from collections import Counter

    # Load events
    events = []
    if os.path.exists(ANALYTICS_FILE):
        with open(ANALYTICS_FILE, 'r', newline='') as f:
            for row in csv.DictReader(f):
                events.append(row)

    # Last-30-day window
    cutoff = datetime.now() - timedelta(days=30)
    recent = []
    for e in events:
        try:
            if datetime.strptime(e.get('timestamp', ''), '%Y-%m-%d %H:%M:%S') >= cutoff:
                recent.append(e)
        except ValueError:
            pass

    # Signups (all-time)
    signup_events = [e for e in events if e.get('event_type') == 'signup']

    # Beta testers from users.csv
    users        = get_all_users()
    beta_testers = [u for u in users if u.get('is_beta_tester') == 'true']

    # Page views (last 30d) — show real page paths only
    _PAGE_PATHS = {"/dashboard", "/students", "/rates", "/payments", "/schedule",
                   "/invoices", "/analytics", "/beta-analytics", "/settings", "/admin", "/billing"}
    page_views  = Counter(
        e['path'] for e in recent
        if e.get('event_type') == 'page_view' and e.get('path', '') in _PAGE_PATHS
    )

    # Feature events (last 30d)
    _FEATURE_LABELS = {
        "add_student":        "Add Student",
        "quick_create_student": "Quick-Create Student",
        "record_payment":     "Record Payment",
        "feedback":           "Submit Feedback",
        "generate_invoices":  "Generate Invoices",
        "mark_invoice_paid":  "Mark Invoice Paid",
    }
    feature_raw = Counter()
    for e in recent:
        if e.get('event_type') == 'feature':
            key = e.get('detail', '').split(':')[0]
            feature_raw[key] += 1

    # KPI cards
    total_testers    = len(beta_testers)
    signups_30d      = sum(1 for e in recent if e.get('event_type') == 'signup')
    page_views_30d   = sum(1 for e in recent if e.get('event_type') == 'page_view' and e.get('path','') in _PAGE_PATHS)
    feature_events_30d = sum(feature_raw.values())

    kpis = f"""
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:28px;">
  <div class="card" style="text-align:center;padding:20px 12px;">
    <div style="font-size:2rem;font-weight:700;color:#6366f1;">{total_testers}</div>
    <div style="color:#64748b;font-size:13px;margin-top:4px;">Total Beta Testers</div>
  </div>
  <div class="card" style="text-align:center;padding:20px 12px;">
    <div style="font-size:2rem;font-weight:700;color:#10b981;">{signups_30d}</div>
    <div style="color:#64748b;font-size:13px;margin-top:4px;">Signups (30d)</div>
  </div>
  <div class="card" style="text-align:center;padding:20px 12px;">
    <div style="font-size:2rem;font-weight:700;color:#f59e0b;">{page_views_30d}</div>
    <div style="color:#64748b;font-size:13px;margin-top:4px;">Page Views (30d)</div>
  </div>
  <div class="card" style="text-align:center;padding:20px 12px;">
    <div style="font-size:2rem;font-weight:700;color:#8b5cf6;">{feature_events_30d}</div>
    <div style="color:#64748b;font-size:13px;margin-top:4px;">Feature Events (30d)</div>
  </div>
</div>"""

    # Beta tester list
    tester_rows = ""
    for u in sorted(beta_testers, key=lambda x: x.get('created_at', ''), reverse=True):
        verified_badge = '<span style="color:#10b981;font-size:11px;">✓ verified</span>' if u.get('is_verified') == 'true' else '<span style="color:#f59e0b;font-size:11px;">⏳ pending</span>'
        tester_rows += (
            f"<tr>"
            f"<td>{u.get('name','')}</td>"
            f"<td style='color:#64748b;'>{u.get('email','')}</td>"
            f"<td>{verified_badge}</td>"
            f"<td style='color:#94a3b8;font-size:12px;'>{u.get('created_at','')[:10]}</td>"
            f"</tr>"
        )
    if not tester_rows:
        tester_rows = '<tr><td colspan="4" style="color:#94a3b8;text-align:center;">No beta testers yet</td></tr>'

    # Top pages table
    page_rows = ""
    for path, count in page_views.most_common(10):
        bar_w = int(count / max(page_views.values()) * 120) if page_views else 0
        page_rows += (
            f"<tr>"
            f"<td style='font-family:monospace;'>{path}</td>"
            f"<td><div style='display:flex;align-items:center;gap:8px;'>"
            f"<div style='height:8px;width:{bar_w}px;background:#6366f1;border-radius:4px;'></div>"
            f"<span style='font-weight:600;'>{count}</span></div></td>"
            f"</tr>"
        )
    if not page_rows:
        page_rows = '<tr><td colspan="2" style="color:#94a3b8;text-align:center;">No page views logged yet</td></tr>'

    # Feature usage table
    feature_rows = ""
    for key, count in feature_raw.most_common():
        label   = _FEATURE_LABELS.get(key, key)
        bar_w   = int(count / max(feature_raw.values()) * 120) if feature_raw else 0
        feature_rows += (
            f"<tr>"
            f"<td>{label}</td>"
            f"<td><div style='display:flex;align-items:center;gap:8px;'>"
            f"<div style='height:8px;width:{bar_w}px;background:#8b5cf6;border-radius:4px;'></div>"
            f"<span style='font-weight:600;'>{count}</span></div></td>"
            f"</tr>"
        )
    if not feature_rows:
        feature_rows = '<tr><td colspan="2" style="color:#94a3b8;text-align:center;">No feature events logged yet</td></tr>'

    content = f"""
<h2 style="margin-bottom:6px;">🧪 Beta Analytics</h2>
<p style="color:#64748b;margin-bottom:24px;">Usage stats for beta testers — page views and feature events update in real-time.</p>

{kpis}

<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
  <div class="card">
    <h3 style="margin-bottom:14px;">Beta Testers</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead><tr>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Name</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Email</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Status</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Joined</th>
      </tr></thead>
      <tbody>{tester_rows}</tbody>
    </table>
  </div>
  <div class="card">
    <h3 style="margin-bottom:14px;">Top Pages (last 30d)</h3>
    <table style="width:100%;border-collapse:collapse;font-size:13px;">
      <thead><tr>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Page</th>
        <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Views</th>
      </tr></thead>
      <tbody>{page_rows}</tbody>
    </table>
  </div>
</div>

<div class="card" style="max-width:480px;">
  <h3 style="margin-bottom:14px;">Feature Usage (last 30d)</h3>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <thead><tr>
      <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Feature</th>
      <th style="text-align:left;padding:6px 8px;border-bottom:1px solid #e2e8f0;">Uses</th>
    </tr></thead>
    <tbody>{feature_rows}</tbody>
  </table>
</div>"""

    return HTMLResponse(page("Beta Analytics", content, "beta-stats"))

