
"""
🕵️ Ritesh OSINT Toolkit - All-in-One (FULLY FIXED)
Run: python Ritesh.py
"""

from flask import (Flask, request, render_template_string, jsonify,
                   redirect, url_for, session, send_from_directory, flash)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import os
import json
import sqlite3
import secrets
from datetime import datetime
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

# ============================================================
# CONFIG
# ============================================================
API_BASE = "https://api.sarkariallupdates.com/api"
API_KEY = "30day"
TIMEOUT = 30
DB_PATH = "osint.db"
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# UPI Payment Config
UPI_ID = "riteshgiri7930@okhdfcbank"
UPI_NAME = "Ritesh Giri"
QR_IMAGE = "qr.png"
ADMIN_USERNAME = "@SADAURA4U"
ADMIN_PASSWORD = "ritesh111"

# Credit Packages
PACKAGES = [
    {"id": "p1",  "amount": 50,   "credits": 50,   "label": "₹50 - 50 Credits"},
    {"id": "p2",  "amount": 100,  "credits": 120,  "label": "₹100 - 120 Credits (Bonus)"},
    {"id": "p3",  "amount": 250,  "credits": 320,  "label": "₹250 - 320 Credits (Bonus)"},
    {"id": "p4",  "amount": 500,  "credits": 700,  "label": "₹500 - 700 Credits (Best Value)"},
    {"id": "p5",  "amount": 1000, "credits": 1500, "label": "₹1000 - 1500 Credits (Mega)"},
]

DEFAULT_COST = 1

# ============================================================
# ENDPOINTS - All 10 APIs from sarkariallupdates.com
# ============================================================
ENDPOINTS = {
    "num_info": {
        "path": "", "param": "num", "api_name": "num_info",
        "label": "📞 Number Info", "placeholder": "9162516577",
        "category": "📱 Phone", "cost": 2,
        "desc": "Get details from mobile number"
    },
    "vehicle_full": {
        "path": "", "param": "xr", "api_name": "vehicle_full",
        "label": "🚗 Vehicle Full Info", "placeholder": "KL41V3504",
        "category": "🚗 Vehicle", "cost": 2,
        "desc": "Full vehicle registration details"
    },
    "vehicle_to_number": {
        "path": "", "param": "xr", "api_name": "vehicle_to_number",
        "label": "🔗 Vehicle → Number", "placeholder": "KL41V3504",
        "category": "🚗 Vehicle", "cost": 2,
        "desc": "Get owner number from vehicle"
    },
    "pan2dob_name": {
        "path": "", "param": "pan2dob_name", "api_name": "pan2dob_name",
        "label": "🆔 PAN 2 Name & DOB", "placeholder": "cnkpk7230d",
        "category": "🆔 Identity", "cost": 3,
        "desc": "PAN card to name and DOB"
    },
    "aadhaar2pan": {
        "path": "", "param": "aadhaar2pan", "api_name": "aadhaar2pan",
        "label": "🔗 Aadhaar → PAN", "placeholder": "123456789012",
        "category": "🆔 Identity", "cost": 3,
        "desc": "Get PAN from Aadhaar number"
    },
    "imei": {
        "path": "", "param": "imei", "api_name": "imei",
        "label": "📲 IMEI Info", "placeholder": "356938035643809",
        "category": "📱 Phone", "cost": 2,
        "desc": "IMEI number information"
    },
    "pincode": {
        "path": "", "param": "pincode", "api_name": "pincode",
        "label": "📍 Pincode Info", "placeholder": "110001",
        "category": "📍 Location", "cost": 1,
        "desc": "Get area details from pincode"
    },
    "ifse": {
        "path": "", "param": "ifse", "api_name": "ifse",
        "label": "🏦 IFSC Info", "placeholder": "SBIN0001234",
        "category": "🏦 Banking", "cost": 1,
        "desc": "Bank branch details from IFSC"
    },
    "tg": {
        "path": "", "param": "q", "api_name": "tg",
        "label": "✈️ TG → Number", "placeholder": "@username",
        "category": "📱 Phone", "cost": 2,
        "desc": "Telegram username to number"
    },
    "addhaar2num": {
        "path": "", "param": "q", "api_name": "addhaar2num",
        "label": "🔗 Aadhaar → Number", "placeholder": "123456789012",
        "category": "🆔 Identity", "cost": 3,
        "desc": "Get mobile number from Aadhaar"
    },
}

GROUPED = {}
for k, v in ENDPOINTS.items():
    GROUPED.setdefault(v["category"], []).append((k, v))


# ============================================================
# DATABASE
# ============================================================
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        credits INTEGER DEFAULT 0,
        is_admin INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        tool TEXT NOT NULL,
        query TEXT NOT NULL,
        cost INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount INTEGER NOT NULL,
        credits INTEGER NOT NULL,
        utr TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS broadcasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS broadcast_reads (
        user_id INTEGER NOT NULL,
        broadcast_id INTEGER NOT NULL,
        read_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, broadcast_id)
    )""")

    c.execute("SELECT * FROM users WHERE username = ?", (ADMIN_USERNAME,))
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, credits, is_admin) VALUES (?, ?, ?, 1)",
            (ADMIN_USERNAME, generate_password_hash(ADMIN_PASSWORD), 999999)
        )

    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
# AUTH DECORATORS
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        conn = get_db()
        u = conn.execute("SELECT is_admin FROM users WHERE id=?", (session['user_id'],)).fetchone()
        conn.close()
        if not u or not u['is_admin']:
            return "Access Denied: Admin only", 403
        return f(*args, **kwargs)
    return wrapper


def current_user():
    if 'user_id' not in session:
        return None
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    return dict(u) if u else None


def get_unread_broadcasts(user_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT b.id, b.message, b.created_at
        FROM broadcasts b
        WHERE b.id NOT IN (
            SELECT broadcast_id FROM broadcast_reads WHERE user_id = ?
        )
        ORDER BY b.id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ============================================================
# BASE STYLE - Colorful Buttons
# ============================================================
BASE_STYLE = """
<style>
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
body { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; color: #fff; }
a { color: #4facfe; text-decoration: none; }
a:hover { text-decoration: underline; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
h1 { background: linear-gradient(90deg, #00f2fe, #4facfe); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.subtitle { color: #aaa; font-size: 0.9rem; }
.navbar {
    background: rgba(0,0,0,0.4); border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 14px 20px; display: flex; justify-content: space-between; align-items: center;
    flex-wrap: wrap; gap: 10px; backdrop-filter: blur(10px);
}
.navbar .brand { font-size: 1.1rem; font-weight: bold; color: #4facfe; }
.navbar .links { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.navbar .links a, .navbar .links span {
    font-size: 0.9rem; color: #ccc; padding: 6px 12px; border-radius: 6px;
    transition: all 0.2s;
}
.navbar .links a:hover { background: rgba(79,172,254,0.15); color: #fff; text-decoration: none; }
.credit-badge {
    background: linear-gradient(90deg, #ffd700, #ffb300);
    color: #000 !important; font-weight: bold;
    padding: 6px 14px !important; border-radius: 20px;
    display: inline-block; animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(255,215,0,0.5); }
    50% { box-shadow: 0 0 0 8px rgba(255,215,0,0); }
}
.btn {
    padding: 10px 20px; border-radius: 8px; border: none;
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #000; font-weight: bold; cursor: pointer; font-size: 0.95rem;
    transition: transform 0.2s; display: inline-block; text-decoration: none;
}
.btn:hover { transform: scale(1.03); text-decoration: none; }
.btn-danger { background: linear-gradient(90deg, #ff6b6b, #ff4444); color: #fff; }
.btn-ghost { background: rgba(255,255,255,0.1); color: #fff; }
.input {
    width: 100%; padding: 12px 14px; border-radius: 8px;
    background: rgba(0,0,0,0.3); color: #fff; border: 1px solid rgba(255,255,255,0.15);
    font-size: 1rem; outline: none;
}
.input:focus { border-color: #4facfe; }
.card {
    background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 20px; margin-bottom: 15px;
}
.error { background: rgba(255,50,50,0.15); border-left: 4px solid #ff4444; padding: 12px; border-radius: 8px; margin: 10px 0; }
.success { background: rgba(50,255,100,0.15); border-left: 4px solid #22c55e; padding: 12px; border-radius: 8px; margin: 10px 0; }
.warn { background: rgba(255,200,0,0.15); border-left: 4px solid #ffc800; padding: 12px; border-radius: 8px; margin: 10px 0; }
table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
table th, table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.08); }
table th { color: #4facfe; font-weight: 600; background: rgba(0,0,0,0.2); }
table tr:hover { background: rgba(255,255,255,0.03); }
.notif-bell {
    position: relative; padding: 6px 12px !important;
    background: rgba(255,200,0,0.2) !important; border-radius: 20px;
}
.notif-bell .dot {
    position: absolute; top: 2px; right: 4px; width: 8px; height: 8px;
    background: #ff4444; border-radius: 50%; animation: blink 1s infinite;
}
@keyframes blink { 50% { opacity: 0.3; } }
.broadcast-card {
    background: linear-gradient(135deg, rgba(255,200,0,0.15), rgba(255,100,0,0.1));
    border-left: 4px solid #ffc800; padding: 14px; border-radius: 10px; margin-bottom: 10px;
}

/* Colorful Tool Cards */
.tool-card {
    background: rgba(255,255,255,0.05);
    border: 2px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 16px; cursor: pointer;
    transition: all 0.25s ease;
    position: relative; overflow: hidden;
}
.tool-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 4px;
    background: var(--accent, #4facfe);
}
.tool-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    border-color: var(--accent, #4facfe);
}
.tool-card .tool-name {
    font-size: 1rem; font-weight: 700; color: #fff;
    margin-bottom: 6px; display: flex; align-items: center; gap: 6px;
}
.tool-card .tool-desc {
    font-size: 0.78rem; color: #aaa; margin-bottom: 8px; line-height: 1.4;
}
.tool-card .tool-meta {
    display: flex; justify-content: space-between; align-items: center;
    font-size: 0.75rem;
}
.tool-card .tool-cost {
    background: rgba(255,215,0,0.2); color: #ffd700;
    padding: 3px 10px; border-radius: 12px; font-weight: bold;
}
.tool-card .tool-cat {
    color: #888; font-size: 0.7rem;
}
.tool-card.selected {
    border-color: #00f2fe;
    background: rgba(79,172,254,0.15);
    box-shadow: 0 0 20px rgba(79,172,254,0.3);
}

/* Category colors */
.cat-phone { --accent: #22c55e; }
.cat-vehicle { --accent: #f59e0b; }
.cat-identity { --accent: #ef4444; }
.cat-location { --accent: #8b5cf6; }
.cat-banking { --accent: #06b6d4; }

.tab-btn {
    padding: 8px 18px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05); color: #ccc; cursor: pointer;
    font-size: 0.85rem; transition: all 0.2s;
}
.tab-btn:hover { background: rgba(79,172,254,0.2); color: #fff; }
.tab-btn.active {
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #000; font-weight: bold; border-color: transparent;
}
</style>
"""


def render_page(title, content, extra_head=""):
    user = current_user()
    unread_count = 0
    if user:
        unread_count = len(get_unread_broadcasts(user['id']))

    if user:
        credit_html = f'<span class="credit-badge">💰 {user["credits"]} Credits</span>'
        if unread_count > 0:
            notif_html = f'<a href="/inbox" class="notif-bell">🔔 Inbox<span class="dot"></span> ({unread_count})</a>'
        else:
            notif_html = '<a href="/inbox">🔔 Inbox</a>'

        nav_user = f'''
            {credit_html}
            <a href="/buy">🛒 Buy</a>
            <a href="/history">📜 History</a>
            {notif_html}
            {"<a href='/admin'>⚙️ Admin</a>" if user["is_admin"] else ""}
            <a href="/logout">🚪 Logout ({user["username"]})</a>
        '''
    else:
        nav_user = '<a href="/login">🔐 Login</a><a href="/signup">📝 Signup</a>'

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — OSINT Toolkit</title>
{BASE_STYLE}
{extra_head}
</head>
<body>
<div class="navbar">
    <a href="/" class="brand">🕵️ Ritesh OSINT Toolkit</a>
    <div class="links">{nav_user}</div>
</div>
<div class="container">{content}</div>
</body>
</html>
"""


# ============================================================
# AUTH ROUTES
# ============================================================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '').strip()
        if not u or not p or len(p) < 4:
            return render_page("Signup", '<div class="error">❌ Username required + password min 4 chars</div><a href="/signup">Back</a>')
        conn = get_db()
        try:
            conn.execute("INSERT INTO users (username, password, credits) VALUES (?, ?, ?)",
                         (u, generate_password_hash(p), 5))
            conn.commit()
            return render_page("Signup", '<div class="success">✅ Account created! 5 free credits added. <a href="/login">Login</a></div>')
        except sqlite3.IntegrityError:
            return render_page("Signup", '<div class="error">❌ Username already exists</div><a href="/signup">Try again</a>')
        finally:
            conn.close()

    content = """
    <div class="card" style="max-width:420px;margin:40px auto;">
        <h1 style="font-size:1.5rem;margin-bottom:15px;">📝 Sign Up</h1>
        <form method="POST">
            <input class="input" name="username" placeholder="Username" required style="margin-bottom:10px;">
            <input class="input" name="password" type="password" placeholder="Password (min 4)" required style="margin-bottom:15px;">
            <button class="btn" style="width:100%;">Create Account (Free 5 Credits)</button>
        </form>
        <p style="text-align:center;margin-top:15px;color:#aaa;">
            Already have account? <a href="/login">Login</a>
        </p>
    </div>
    """
    return render_page("Signup", content)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username', '').strip()
        p = request.form.get('password', '').strip()
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password'], p):
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        return render_page("Login", '<div class="error">❌ Invalid credentials</div><a href="/login">Try again</a>')

    content = """
    <div class="card" style="max-width:420px;margin:40px auto;">
        <h1 style="font-size:1.5rem;margin-bottom:15px;">🔐 Login</h1>
        <form method="POST">
            <input class="input" name="username" placeholder="Username" required style="margin-bottom:10px;">
            <input class="input" name="password" type="password" placeholder="Password" required style="margin-bottom:15px;">
            <button class="btn" style="width:100%;">Login</button>
        </form>
        <p style="text-align:center;margin-top:15px;color:#aaa;">
            New user? <a href="/signup">Sign up</a>
        </p>
    </div>
    """
    return render_page("Login", content)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ============================================================
# CREDIT API
# ============================================================
@app.route('/api/credits')
@login_required
def api_credits():
    conn = get_db()
    u = conn.execute("SELECT credits FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    return jsonify({"credits": u['credits'] if u else 0})


# ============================================================
# MAIN DASHBOARD - All Colorful Tool Buttons
# ============================================================
@app.route('/')
@login_required
def index():
    user = current_user()
    unread = get_unread_broadcasts(user['id'])

    broadcast_html = ""
    if unread:
        broadcast_html = '<div style="margin-bottom:20px;">'
        for b in unread[:3]:
            broadcast_html += f'''
            <div class="broadcast-card">
                <div style="font-weight:bold;color:#ffc800;margin-bottom:5px;">📢 Admin Message</div>
                <div style="color:#eee;line-height:1.5;">{b["message"]}</div>
                <div style="font-size:.75rem;color:#888;margin-top:6px;">{b["created_at"]}</div>
            </div>
            '''
        if len(unread) > 3:
            broadcast_html += f'<p style="text-align:center;color:#aaa;"><a href="/inbox">+{len(unread)-3} more →</a></p>'
        broadcast_html += '</div>'

    content = f"""
    {broadcast_html}
    <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;">
        <div>
            <h1 style="font-size:1.6rem;">🕵️ Welcome, {user['username']}!</h1>
            <p class="subtitle" style="margin-top:5px;">{len(ENDPOINTS)} tools available</p>
        </div>
        <div style="text-align:right;">
            <div style="color:#aaa;font-size:.8rem;">Your Balance</div>
            <div id="dashCredits" style="font-size:2rem;font-weight:bold;background:linear-gradient(90deg,#ffd700,#ffb300);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">💰 {user['credits']}</div>
            <a href="/buy" class="btn" style="margin-top:8px;padding:6px 14px;font-size:.85rem;">+ Buy Credits</a>
        </div>
    </div>

    <div class="tabs" style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:20px;">
        <button class="tab-btn active" data-cat="ALL" onclick="filterCat('ALL', this)">🌐 All</button>
        {"".join(f'<button class="tab-btn" data-cat="{cat}" onclick="filterCat(`{cat}`, this)">{cat}</button>' for cat in GROUPED.keys())}
    </div>

    <div class="tool-grid" id="toolGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:25px;">
    """

    # Map category to CSS class
    cat_class_map = {
        "📱 Phone": "cat-phone",
        "🚗 Vehicle": "cat-vehicle",
        "🆔 Identity": "cat-identity",
        "📍 Location": "cat-location",
        "🏦 Banking": "cat-banking",
    }

    for cat, items in GROUPED.items():
        css_cat = cat_class_map.get(cat, "")
        for key, cfg in items:
            safe_label = cfg['label'].replace(chr(39), '')
            safe_desc = cfg['desc'].replace(chr(39), '')
            content += f"""
            <div class="tool-card {css_cat}" data-cat="{cat}" data-key="{key}"
                 onclick="selectTool('{key}', '{safe_label}', '{cfg['placeholder']}', this)">
                <div class="tool-name">{cfg['label']}</div>
                <div class="tool-desc">{cfg['desc']}</div>
                <div class="tool-meta">
                    <span class="tool-cost">💰 {cfg['cost']} cr</span>
                    <span class="tool-cat">{cat}</span>
                </div>
            </div>
            """

    content += """
    </div>

    <div style="display:flex;gap:10px;background:rgba(255,255,255,0.05);padding:15px;border-radius:12px;border:1px solid rgba(255,255,255,0.1);margin-bottom:20px;flex-wrap:wrap;">
        <input type="text" id="queryInput" class="input" style="flex:1;min-width:200px;"
               placeholder="Select a tool first..." disabled>
        <button class="btn" id="searchBtn" onclick="runSearch()" disabled>🔍 Search</button>
    </div>

    <div id="output"></div>

    <script>
    let selectedTool = null;
    function filterCat(cat, btn) {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.tool-card').forEach(c => {
            c.style.display = (cat === 'ALL' || c.dataset.cat === cat) ? '' : 'none';
        });
    }
    function selectTool(key, label, placeholder, el) {
        selectedTool = key;
        document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('selected'));
        el.classList.add('selected');
        const input = document.getElementById('queryInput');
        input.disabled = false; input.placeholder = placeholder || 'Enter value...'; input.value = ''; input.focus();
        document.getElementById('searchBtn').disabled = false;
        document.getElementById('output').innerHTML = '';
    }
    document.getElementById('queryInput').addEventListener('keypress', e => { if (e.key === 'Enter') runSearch(); });

    async function refreshCredits() {
        try {
            const r = await fetch('/api/credits');
            const d = await r.json();
            const el = document.getElementById('dashCredits');
            if (el) el.textContent = '💰 ' + d.credits;
            document.querySelectorAll('.credit-badge').forEach(b => {
                b.textContent = '💰 ' + d.credits + ' Credits';
            });
        } catch (e) {}
    }

    async functionrunSearch() {
        if (!selectedTool) { alert('Please select a tool first'); return; }
        const q = document.getElementById('queryInput').value.trim();
        const out = document.getElementById('output');
        const btn = document.getElementById('searchBtn');
        if (!q) { out.innerHTML = '<div class="error">❌ Please enter a value</div>'; return; }
        btn.disabled = true;
        out.innerHTML = '<div style="text-align:center;padding:30px;color:#4facfe;">⏳ Fetching data...</div>';
        try {
            const res = await fetch(`/api/lookup?tool=${encodeURIComponent(selectedTool)}&q=${encodeURIComponent(q)}`);
            const data = await res.json();
            if (!data.success) {
                out.innerHTML = `<div class="error">❌ ${data.message}</div>`;
                return;
            }
            out.innerHTML = `
                <div style="background:rgba(0,0,0,0.3);padding:10px 14px;border-radius:8px;font-family:monospace;font-size:.78rem;color:#7dd3fc;margin-bottom:15px;word-break:break-all;border-left:3px solid #4facfe;">🔗 ${data.url}</div>
                <div class="card"><pre style="white-space:pre-wrap;word-break:break-word;font-size:.82rem;line-height:1.6;color:#b8f0ff;">${escapeHtml(data.pretty)}</pre></div>
                <p style="text-align:center;color:#aaa;font-size:.85rem;margin-top:10px;">💰 Charged: ${data.cost} credits • Remaining: ${data.remaining}</p>
            `;
            refreshCredits();
        } catch (err) {
            out.innerHTML = `<div class="error">❌ Error: ${err.message}</div>`;
        } finally { btn.disabled = false; }
    }
    function escapeHtml(s) {
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }
    </script>
    """
    return render_page("Dashboard", content)


# ============================================================
# API LOOKUP - Clean response (no promotion/admin/bot names)
# ============================================================
@app.route('/api/lookup')
@login_required
def lookup():
    tool = request.args.get('tool', '').strip()
    q = request.args.get('q', '').strip()

    if tool not in ENDPOINTS:
        return jsonify({"success": False, "message": "Invalid tool"}), 400
    if not q:
        return jsonify({"success": False, "message": "Empty query"}), 400

    cfg = ENDPOINTS[tool]
    cost = cfg.get('cost', DEFAULT_COST)
    user_id = session['user_id']

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()

    if not user:
        conn.close()
        return jsonify({"success": False, "message": "User not found"}), 401

    if user['credits'] < cost:
        conn.close()
        return jsonify({"success": False, "message": f"Insufficient credits. Need {cost}, have {user['credits']}. Please buy more."})

    # Build API URL
    url = f"{API_BASE}?={cfg['api_name']}&key={API_KEY}&{cfg['param']}={q}"

    try:
        r = requests.get(url, timeout=TIMEOUT)
        ctype = r.headers.get('content-type', '')

        if 'application/json' in ctype:
            try:
                data = r.json()
            except Exception:
                data = r.text
        else:
            data = r.text

        # Remove all promotional / admin / bot / channel info
        if isinstance(data, dict):
            keys_to_remove = [
                'credit_limit', 'credit', 'credits', 'bot_username', 'channel_link',
                'channel', 'username', 'bot', 'join', 'owner', 'rate_limit',
                'developer', 'dev', 'powered_by', 'powered', 'author',
                'telegram', 'tg', 'channel_username', 'bot_name', 'api_owner',
                'api_developer', 'api_channel', 'support', 'contact',
                'website', 'link', 'links', 'promo', 'promotion', 'ad',
                'advertisement', 'sponsor', 'sponsored', 'source', 'provider',
                'api_provider', 'api_name', 'api_version', 'version',
                'admin', 'admin_username', 'admin_name', 'admin_contact',
                'bot_link', 'channel_name', 'group', 'group_link',
                'subscribe', 'follow', 'like', 'share',
            ]
            for k in keys_to_remove:
                data.pop(k, None)

            # Recursively clean nested dicts
            if 'data' in data and isinstance(data['data'], dict):
                for k in keys_to_remove:
                    data['data'].pop(k, None)
            if 'result' in data and isinstance(data['result'], dict):
                for k in keys_to_remove:
                    data['result'].pop(k, None)

        pretty = json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)

        # Text-based cleanup for any remaining promotional content
        unwanted_patterns = [
            '@SADAURA4U', 'SADAURA4U', 'sadaura4u',
            '@shiva_158', 'shiva_158',
            '@Osintinfooobot', 'Osintinfooobot', 'osintinfoooo',
            't.me/', 'https://t.me/', 'telegram.me/', 'http://t.me/',
            'Telegram', 'telegram', 'TG Bot', 'tg bot',
            'Join @', 'join @', 'Join our', 'join our',
            'Owner:', 'owner:', 'Channel:', 'channel:', 'Bot:', 'bot:',
            'Follow @', 'follow @', 'Subscribe', 'subscribe',
            'powered by', 'Powered by', 'Powered By',
            'credit_limit', 'credit limit', 'rate_limit', 'rate limit',
            'API Owner', 'API Developer', 'API Channel',
            'Join Channel', 'join channel', 'Join Group', 'join group',
            'For support', 'for support', 'Contact:', 'contact:',
            'Visit:', 'visit:', 'Website:', 'website:',
            'Developed by', 'developed by', 'Made by', 'made by',
            'Admin:', 'admin:', 'Admin Name', 'admin name',
            '@admin', 'Admin Username', 'admin username',
        ]
        for pattern in unwanted_patterns:
            pretty = pretty.replace(pattern, '')

        # Remove empty lines
        pretty = '\n'.join(line for line in pretty.splitlines() if line.strip())

        # Deduct credits
        new_credits = user['credits'] - cost
        conn.execute("UPDATE users SET credits=? WHERE id=?", (new_credits, user_id))
        conn.execute("INSERT INTO history (user_id, tool, query, cost) VALUES (?, ?, ?, ?)",
                     (user_id, tool, q, cost))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "status": r.status_code,
            "pretty": pretty,
            "url": f"{API_BASE}?={cfg['api_name']}&key=***&{cfg['param']}={q}",
            "cost": cost,
            "remaining": new_credits,
        })

    except requests.exceptions.Timeout:
        conn.close()
        return jsonify({"success": False, "message": "API timeout. Credit not deducted. Try again."}), 504
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": f"Error: {str(e)}. Credit not deducted."}), 500


# ============================================================
# BUY CREDITS
# ============================================================
@app.route('/buy')
@login_required
def buy():
    user = current_user()
    content = f"""
    <h1 style="text-align:center;font-size:1.6rem;margin:20px 0;">🛒 Buy Credits</h1>
    <p class="subtitle" style="text-align:center;margin-bottom:25px;">
        Current Balance: <b style="color:#ffd700;">💰 {user['credits']} credits</b>
    </p>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:15px;margin-bottom:30px;">
    """

    for p in PACKAGES:
        content += f"""
        <div class="card" style="text-align:center;">
            <div style="font-size:1.3rem;font-weight:bold;color:#4facfe;margin-bottom:8px;">{p['label']}</div>
            <div style="font-size:0.85rem;color:#aaa;margin-bottom:15px;">₹{p['amount']} = {p['credits']} credits</div>
            <button class="btn" style="width:100%;" onclick="buyPack('{p['id']}')">Buy Now</button>
        </div>
        """

    content += f"""
    </div>

    <div class="card">
        <h2 style="font-size:1.2rem;margin-bottom:15px;color:#00f2fe;">💳 UPI Payment</h2>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start;">
            <div style="text-align:center;">
                <img src="/static/{QR_IMAGE}" alt="UPI QR" 
                     style="max-width:260px;width:100%;border-radius:12px;background:#fff;padding:8px;"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
                <div style="display:none;padding:20px;color:#ff8888;">
                    ⚠️ QR image not found. Please upload <code>static/{QR_IMAGE}</code>
                </div>
                <p style="margin-top:10px;color:#aaa;font-size:0.85rem;">Scan & Pay</p>
            </div>
            <div>
                <div class="info-row" style="display:grid;grid-template-columns:120px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                    <span style="color:#888;">UPI ID:</span>
                    <span style="color:#eee;word-break:break-all;"><b>{UPI_ID}</b></span>
                </div>
                <div class="info-row" style="display:grid;grid-template-columns:120px 1fr;gap:8px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.08);">
                    <span style="color:#888;">Name:</span>
                    <span style="color:#eee;">{UPI_NAME}</span>
                </div>
                <p style="margin-top:15px;color:#aaa;font-size:0.85rem;line-height:1.6;">
                    📌 After payment, enter <b>UTR / Transaction ID</b> below.<br>
                    ⏱ Admin will verify and add credits.
                </p>
                <div style="margin-top:15px;display:flex;gap:10px;flex-wrap:wrap;">
                    <a href="upi://pay?pa={UPI_ID}&pn={UPI_NAME}&cu=INR" class="btn">📲 Open UPI App</a>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2 style="font-size:1.2rem;margin-bottom:15px;color:#00f2fe;">📝 Submit Payment Proof</h2>
        <form method="POST"action="/submit-payment">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px;">
                <select name="package" class="input" required>
                    <option value="">-- Select Package --</option>
    """

    for p in PACKAGES:
        content += f'<option value="{p["id"]}">{p["label"]} - ₹{p["amount"]}</option>'

    content += """
                </select>
                <input class="input" name="utr" placeholder="UTR / Transaction ID" required>
            </div>
            <button class="btn" style="width:100%;">📤 Submit for Verification</button>
        </form>
    </div>

    <script>
    function buyPack(id) {
        document.querySelector('select[name="package"]').value = id;
        document.querySelector('input[name="utr"]').focus();
        window.scrollTo({ top: document.querySelector('input[name="utr"]').offsetTop - 100, behavior: 'smooth' });
    }
    </script>
    """
    return render_page("Buy Credits", content)


@app.route('/submit-payment', methods=['POST'])
@login_required
def submit_payment():
    pkg_id = request.form.get('package', '').strip()
    utr = request.form.get('utr', '').strip()
    user_id = session['user_id']

    pkg = next((p for p in PACKAGES if p['id'] == pkg_id), None)
    if not pkg or not utr:
        return redirect(url_for('buy'))

    conn = get_db()
    conn.execute("INSERT INTO payments (user_id, amount, credits, utr) VALUES (?, ?, ?, ?)",
                 (user_id, pkg['amount'], pkg['credits'], utr))
    conn.commit()
    conn.close()

    content = f"""
    <div class="card" style="max-width:520px;margin:40px auto;text-align:center;">
        <div style="font-size:3rem;margin-bottom:10px;">✅</div>
        <h2 style="color:#22c55e;margin-bottom:15px;">Payment Submitted!</h2>
        <p style="color:#ccc;line-height:1.7;margin-bottom:20px;">
            UTR: <b>{utr}</b><br>
            Package: <b>₹{pkg['amount']} = {pkg['credits']} credits</b><br><br>
            Credits will be added after admin verification.
        </p>
        <a href="/buy" class="btn">← Back to Buy</a>
    </div>
    """
    return render_page("Payment Submitted", content)


# ============================================================
# HISTORY
# ============================================================
@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM history WHERE user_id=? ORDER BY id DESC LIMIT 100", (user_id,)
    ).fetchall()
    conn.close()

    rows_html = ""
    for r in rows:
        rows_html += f"""
        <tr>
            <td>{r['id']}</td>
            <td>{r['tool']}</td>
            <td style="font-family:monospace;">{r['query']}</td>
            <td>-{r['cost']}</td>
            <td>{r['created_at']}</td>
        </tr>
        """

    content = f"""
    <h1 style="text-align:center;font-size:1.6rem;margin:20px 0;">📜 Search History</h1>
    <div class="card">
        <table>
            <tr><th>#</th><th>Tool</th><th>Query</th><th>Cost</th><th>Time</th></tr>
            {rows_html or '<tr><td colspan="5" style="text-align:center;color:#888;">No history yet</td></tr>'}
        </table>
    </div>
    """
    return render_page("History", content)


# ============================================================
# INBOX
# ============================================================
@app.route('/inbox')
@login_required
def inbox():
    user_id = session['user_id']
    messages = get_unread_broadcasts(user_id)

    conn = get_db()
    for m in messages:
        try:
            conn.execute("INSERT OR IGNORE INTO broadcast_reads (user_id, broadcast_id) VALUES (?, ?)",
                         (user_id, m['id']))
        except Exception:
            pass
    conn.commit()

    all_msgs = conn.execute("SELECT * FROM broadcasts ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()

    msgs_html = ""
    for m in all_msgs:
        msgs_html += f"""
        <div class="broadcast-card" style="margin-bottom:12px;">
            <div style="font-weight:bold;color:#ffc800;margin-bottom:5px;">📢 Admin Message</div>
            <div style="color:#eee;line-height:1.6;white-space:pre-wrap;">{m['message']}</div>
            <div style="font-size:.75rem;color:#888;margin-top:8px;">{m['created_at']}</div>
        </div>
        """

    content = f"""
    <h1 style="text-align:center;font-size:1.6rem;margin:20px 0;">🔔 Inbox</h1>
    <div class="card">
        {msgs_html or '<p style="text-align:center;color:#888;">No messages yet.</p>'}
    </div>
    """
    return render_page("Inbox", content)


# ============================================================
# ADMIN PANEL
# ============================================================
@app.route('/admin')
@admin_required
def admin():
    conn = get_db()
    users = conn.execute("SELECT id, username, credits, is_admin, created_at FROM users ORDER BY id DESC").fetchall()
    payments = conn.execute("""SELECT p.*, u.username FROM payments p 
                               JOIN users u ON u.id = p.user_id 
                               ORDER BY p.id DESC LIMIT 50""").fetchall()
    broadcasts = conn.execute("SELECT * FROM broadcasts ORDER BY id DESC LIMIT 20").fetchall()
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()['c'],
        "total_searches": conn.execute("SELECT COUNT(*) c FROM history").fetchone()['c'],
        "pending_payments": conn.execute("SELECT COUNT(*) c FROM payments WHERE status='pending'").fetchone()['c'],
        "revenue": conn.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved'").fetchone()['s'],
        "total_broadcasts": conn.execute("SELECT COUNT(*) c FROM broadcasts").fetchone()['c'],
    }
    conn.close()

    users_html = ""
    for u in users:
        badge = "👑 Admin" if u['is_admin'] else "👤"
        users_html += f"""
        <tr>
            <td>{u['id']}</td>
            <td>{badge} {u['username']}</td>
            <td>💰 {u['credits']}</td>
            <td>{u['created_at']}</td>
            <td>
                <form method="POST" action="/admin/add-credits" style="display:inline-flex;gap:5px;">
                    <input type="hidden" name="user_id" value="{u['id']}">
                    <input class="input" name="amount" type="number" placeholder="+/-" style="width:80px;padding:6px;">
                    <button class="btn" style="padding:6px 12px;font-size:.8rem;">Add</button>
                </form>
            </td>
        </tr>
        """

    payments_html = ""
    for p in payments:
        status_color = {"pending": "#ffc800", "approved": "#22c55e", "rejected": "#ff4444"}.get(p['status'], "#888")
        actions = ""
        if p['status'] == 'pending':
            actions = f"""
            <form method="POST" action="/admin/payment-action" style="display:inline;">
                <input type="hidden" name="payment_id" value="{p['id']}">
                <button class="btn" name="action" value="approve" style="padding:5px 10px;font-size:.75rem;">✅ Approve</button>
                <button class="btn btn-danger" name="action" value="reject" style="padding:5px 10px;font-size:.75rem;">❌ Reject</button>
            </form>
            """
        payments_html += f"""
        <tr>
            <td>{p['id']}</td>
            <td>{p['username']}</td>
            <td>₹{p['amount']}</td>
            <td>💰 {p['credits']}</td>
            <td style="font-family:monospace;font-size:.8rem;">{p['utr']}</td>
            <td style="color:{status_color};">{p['status'].upper()}</td>
            <td>{p['created_at']}</td>
            <td>{actions}</td>
        </tr>
        """

    broadcast_history = ""
    for b in broadcasts:
        preview = b['message'][:120].replace('\n', ' ')
        broadcast_history += f"""
        <tr>
            <td>{b['id']}</td>
            <td style="max-width:500px;">{preview}{'…' if len(b['message'])>120 else ''}</td>
            <td>{b['created_at']}</td>
            <td>
                <form method="POST" action="/admin/delete-broadcast" style="display:inline;">
                    <input type="hidden" name="bid" value="{b['id']}">
                    <button class="btn btn-danger" style="padding:4px 10px;font-size:.7rem;">🗑 Delete</button>
                </form>
            </td>
        </tr>
        """

    content = f"""
    <h1 style="text-align:center;font-size:1.6rem;margin:20px 0;">⚙️ Admin Panel</h1>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px;margin-bottom:20px;">
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Users</div><div style="font-size:1.8rem;color:#4facfe;font-weight:bold;">{stats['total_users']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Searches</div><div style="font-size:1.8rem;color:#4facfe;font-weight:bold;">{stats['total_searches']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Pending Pay</div><div style="font-size:1.8rem;color:#ffc800;font-weight:bold;">{stats['pending_payments']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Revenue (₹)</div><div style="font-size:1.8rem;color:#22c55e;font-weight:bold;">{stats['revenue']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Broadcasts</div><div style="font-size:1.8rem;color:#c084fc;font-weight:bold;">{stats['total_broadcasts']}</div></div>
    </div>

    <div class="card" style="border:2px solid #ffc800;">
        <h2 style="font-size:1.15rem;margin-bottom:12px;color:#ffc800;">📢 Broadcast Message (Send to All)</h2>
        <form method="POST" action="/admin/broadcast">
            <textarea class="input" name="message" rows="4" placeholder="Type your message here... All users will see it in inbox." required
                      style="resize:vertical;font-family:inherit;margin-bottom:10px;"></textarea>
            <button class="btn" style="width:100%;">📤 Send to All Users</button>
        </form>
        <p style="color:#888;font-size:.8rem;margin-top:10px;">Note: This message will go to all users' Inbox and also appear on their dashboard.</p>
    </div>

    <div class="card">
        <h2 style="font-size:1.15rem;margin-bottom:12px;color:#00f2fe;">📜 Recent Broadcasts</h2>
        <div style="overflow-x:auto;">
            <table>
                <tr><th>ID</th><th>Message</th><th>Time</th><th>Action</th></tr>
                {broadcast_history or '<tr><td colspan="4" style="text-align:center;color:#888;">No broadcasts yet</td></tr>'}
            </table>
        </div>
    </div>

    <div class="card">
        <h2 style="font-size:1.15rem;margin-bottom:12px;color:#00f2fe;">💳 Payment Requests</h2>
        <div style="overflow-x:auto;">
            <table>
                <tr><th>ID</th><th>User</th><th>Amount</th><th>Credits</th><th>UTR</th><th>Status</th><th>Time</th><th>Action</th></tr>
                {payments_html or '<tr><td colspan="8" style="text-align:center;color:#888;">No payments yet</td></tr>'}
            </table>
        </div>
    </div>

    <div class="card">
        <h2 style="font-size:1.15rem;margin-bottom:12px;color:#00f2fe;">👥 All Users</h2>
        <div style="overflow-x:auto;">
            <table>
                <tr><th>ID</th><th>Username</th><th>Credits</th><th>Joined</th><th>Adjust Credits</th></tr>
                {users_html}
            </table>
        </div>
    </div>

    <div class="card">
        <h2 style="font-size:1.15rem;margin-bottom:12px;color:#00f2fe;">⚙️ Settings</h2>
        <p style="color:#aaa;font-size:.9rem;line-height:1.7;">
            • API Base: <code>{API_BASE}</code><br>
            • Total APIs: <b>{len(ENDPOINTS)}</b><br>
            • QR Image: <code>static/{QR_IMAGE}</code>
        </p>
    </div>
    """
    return render_page("Admin Panel", content)


@app.route('/admin/add-credits', methods=['POST'])
@admin_required
def admin_add_credits():
    try:
        uid = int(request.form.get('user_id', 0))
        amt = int(request.form.get('amount', 0))
        if uid and amt:
            conn = get_db()
            conn.execute("UPDATE users SET credits = MAX(0, credits + ?) WHERE id = ?", (amt, uid))
            conn.commit()
            conn.close()
    except Exception:
        pass
    return redirect(url_for('admin'))


@app.route('/admin/payment-action', methods=['POST'])
@admin_required
def admin_payment_action():
    pid = request.form.get('payment_id')
    action = request.form.get('action')
    conn = get_db()
    p = conn.execute("SELECT * FROM payments WHERE id=?", (pid,)).fetchone()
    if not p or p['status'] != 'pending':
        conn.close()
        return redirect(url_for('admin'))

    if action == 'approve':
        conn.execute("UPDATE payments SET status='approved' WHERE id=?", (pid,))
        conn.execute("UPDATE users SET credits = credits + ? WHERE id=?", (p['credits'], p['user_id']))
    elif action == 'reject':
        conn.execute("UPDATE payments SET status='rejected' WHERE id=?", (pid,))

    conn.commit()
    conn.close()
    return redirect(url_for('admin'))


@app.route('/admin/broadcast', methods=['POST'])
@admin_required
def admin_broadcast():
    message = request.form.get('message', '').strip()
    if message:
        conn = get_db()
        conn.execute("INSERT INTO broadcasts (message) VALUES (?)", (message,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin'))


@app.route('/admin/delete-broadcast', methods=['POST'])
@admin_required
def admin_delete_broadcast():
    bid = request.form.get('bid')
    conn = get_db()
    conn.execute("DELETE FROM broadcasts WHERE id=?", (bid,))
    conn.execute("DELETE FROM broadcast_reads WHERE broadcast_id=?", (bid,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))


# ============================================================
# STATIC
# ============================================================
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(str(STATIC_DIR), filename)


# ============================================================
# STARTUP
# ============================================================
init_db()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🕵️  Ritesh OSINT Toolkit")
    print("="*60)
    print(f"🌐 URL        : http://127.0.0.1:8080")
    print(f"📦 Tools      : {len(ENDPOINTS)} APIs")
    print(f"👑 Admin      : {ADMIN_USERNAME}")
    print(f"💰 UPI        : {UPI_ID}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
    
