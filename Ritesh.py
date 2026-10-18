"""
🕵️ Ritesh OSINT Toolkit - All-in-One (FIXED + Broadcast + Credit Display + New APIs)
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
import re
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
# ENDPOINTS  (Sarkari All Updates API)
# FIXED: "api_name" = exact tool name in URL (?=api_name)
#        "param"    = query parameter name
# ============================================================
ENDPOINTS = {
    # -------- Phone / Number --------
    "num_info": {
        "api_name": "num_info",
        "param": "num",
        "label": "📞 Number Info",
        "placeholder": "9162516577",
        "category": "📱 Phone",
        "cost": 2,
    },
    "tg": {
        "api_name": "tg",
        "param": "q",
        "label": "📨 Telegram to Number",
        "placeholder": "@Perfectamit65",
        "category": "📱 Phone",
        "cost": 2,
    },

    # -------- Vehicle --------
    "vehicle_full": {
        "api_name": "vehicle_full",
        "param": "xr",
        "label": "🚗 Vehicle Full Info",
        "placeholder": "KL41V3504",
        "category": "🚗 Vehicle",
        "cost": 3,
    },
    "vehicle_to_number": {
        "api_name": "vehicle_to_number",
        "param": "xr",
        "label": "🔢 Vehicle to Number",
        "placeholder": "KL41V3504",
        "category": "🚗 Vehicle",
        "cost": 2,
    },

    # -------- Identity / KYC --------
    "pan2dob_name": {
        "api_name": "pan2dob_name",
        "param": "pan2dob_name",
        "label": "🆔 PAN → Name + DOB",
        "placeholder": "cnkpk7230d",
        "category": "🆔 Identity",
        "cost": 3,
    },
    "aadhaar2pan": {
        "api_name": "aadhaar2pan",
        "param": "aadhaar2pan",
        "label": "🪪 Aadhaar → PAN",
        "placeholder": "123456789012",
        "category": "🆔 Identity",
        "cost": 3,
    },
    "addhaar2num": {
        "api_name": "addhaar2num",
        "param": "q",
        "label": "📱 Aadhaar → Number",
        "placeholder": "123456789012",
        "category": "🆔 Identity",
        "cost": 3,
    },

    # -------- Other --------
    "imei": {
        "api_name": "imei",
        "param": "imei",
        "label": "📲 IMEI Info",
        "placeholder": "356938035643809",
        "category": "📲 Device",
        "cost": 2,
    },
    "pincode": {
        "api_name": "pincode",
        "param": "pincode",
        "label": "📍 Pincode Info",
        "placeholder": "110001",
        "category": "📍 Address",
        "cost": 1,
    },
    "ifse": {
        "api_name": "ifse",
        "param": "ifse",
        "label": "🏦 IFSC Info",
        "placeholder": "SBIN0001234",
        "category": "🏦 Banking",
        "cost": 1,
    },
}

# Group by category for UI
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
# BASE STYLE
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
.tab-btn {
    padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.05); color: #ccc; cursor: pointer; font-size: 0.85rem;
    transition: all 0.2s;
}
.tab-btn:hover { background: rgba(79,172,254,0.15); color: #fff; }
.tab-btn.active {
    background: linear-gradient(90deg, #00f2fe, #4facfe); color: #000; font-weight: bold;
    border-color: transparent;
}
.tool-card:hover { border-color: #4facfe !important; transform: translateY(-2px); }
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
<title>{title} — Ritesh OSINT</title>
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
            return render_page("Signup", '<div class="success">✅ Account bana! 5 free credits mile. <a href="/login">Login karo</a></div>')
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
# CREDIT API (live refresh)
# ============================================================
@app.route('/api/credits')
@login_required
def api_credits():
    conn = get_db()
    u = conn.execute("SELECT credits FROM users WHERE id=?", (session['user_id'],)).fetchone()
    conn.close()
    return jsonify({"credits": u['credits'] if u else 0})


# ============================================================
# MAIN DASHBOARD
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

    for cat, items in GROUPED.items():
        for key, cfg in items:
            safe_label = cfg['label'].replace("'", "")
            content += f"""
            <div class="tool-card" data-cat="{cat}" data-key="{key}"
                 onclick="selectTool('{key}', '{safe_label}', '{cfg['placeholder']}', this)"
                 style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:14px;cursor:pointer;transition:all .2s;">
                <div style="font-size:.95rem;font-weight:600;color:#eee;">{cfg['label']}</div>
                <div style="font-size:.75rem;color:#888;margin-top:4px;">Cost: {cfg['cost']} credits</div>
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
        document.querySelectorAll('.tool-card').forEach(c => {
            c.style.borderColor = 'rgba(255,255,255,0.08)';
            c.style.background = 'rgba(255,255,255,0.05)';
        });
        el.style.borderColor = '#00f2fe';
        el.style.background = 'rgba(79,172,254,0.15)';
        const input = document.getElementById('queryInput');
        input.disabled = false; input.placeholder = placeholder || 'Value daalo...'; input.value = ''; input.focus();
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

    async function runSearch() {
        if (!selectedTool) { alert('Pehle tool select karo'); return; }
        const q = document.getElementById('queryInput').value.trim();
        const out = document.getElementById('output');
        const btn = document.getElementById('searchBtn');
        if (!q) { out.innerHTML = '<div class="error">❌ Value daalo</div>'; return; }
        btn.disabled = true;
        out.innerHTML = '<div style="text-align:center;padding:30px;color:#4facfe;">⏳ Fetching...</div>';
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
# API LOOKUP  (FIXED URL + strong promotional filtering)
# ============================================================
@app.route('/api/lookup')
@login_required
def lookup():
    tool = request.args.get('tool', '').strip()
    q = request.args.get('q', '').strip()

    if tool not in ENDPOINTS:
        return jsonify({"success": False, "message": f"Invalid tool: {tool}"}), 400
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

    # ============================================================
    # FIXED URL CONSTRUCTION
    # Format: https://api.sarkariallupdates.com/api?=<api_name>&key=30day&<param>=<value>
    # Example: https://api.sarkariallupdates.com/api?=num_info&key=30day&num=9162516577
    # ============================================================
    api_name = cfg['api_name']
    param = cfg['param']
    url = f"{API_BASE}?={api_name}&key={API_KEY}&{param}={q}"

    print(f"[LOOKUP] Tool={tool} | URL={url}")

    try:
        r = requests.get(url, timeout=TIMEOUT)
        status_code = r.status_code
        ctype = r.headers.get('content-type', '')

        if 'application/json' in ctype:
            try:
                data = r.json()
            except Exception:
                data = r.text
        else:
            data = r.text

        # ---------- Strong promotional stripping ----------
        if isinstance(data, dict):
            unwanted_keys = {
                'credit_limit', 'credit', 'bot_username', 'channel_link',
                'channel', 'username', 'bot', 'join', 'owner', 'rate_limit',
                'developer', 'dev', 'powered_by', 'powered', 'author',
                'telegram', 'tg', 'channel_username', 'bot_name',
                'promo', 'advertisement', 'sponsor', 'watermark', 'footer',
                'header', 'join_us', 'our_channel', 'subscribe', 'follow',
                'credit_used', 'credits_used', 'quota', 'remaining', 'limit',
                'api_name', 'api', 'endpoint'
            }
            def clean_obj(obj):
                if isinstance(obj, dict):
                    return {k: clean_obj(v) for k, v in obj.items() if k.lower() not in unwanted_keys}
                elif isinstance(obj, list):
                    return [clean_obj(i) for i in obj]
                return obj
            data = clean_obj(data)

        pretty = json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)

        # Remove promotional patterns
        promo_patterns = [
            '@SADAURA4U', 'SADAURA4U', 'sadaura4u',
            '@shiva_158', 'shiva_158',
            '@Osintinfooobot', 'Osintinfooobot',
            't.me/', 'https://t.me/', 'telegram.me/',
            't.me/osintinfoooo', 'osintinfoooo',
            'Join @', 'join @', 'Join our', 'join our',
            'Owner:', 'owner:', 'Channel:', 'channel:', 'Bot:', 'bot:',
            'Follow @', 'follow @', 'Subscribe', 'subscribe',
            'powered by', 'Powered by', 'Powered By',
            'credit_limit', 'credit limit', 'rate_limit', 'rate limit',
            'sarkariallupdates', 'sarkari all updates', 'api.sarkariallupdates.com',
            'osintinfo', 'osint info',
        ]
        for pattern in promo_patterns:
            pretty = pretty.replace(pattern, '')

        # Regex cleanup for @usernames and telegram links
        pretty = re.sub(r'@[A-Za-z0-9_]{4,}', '', pretty)
        pretty = re.sub(r'https?://t\.me/\S+', '', pretty)
        pretty = re.sub(r'\b(?:channel|group|bot)\s*[:\-]\s*\S+', '', pretty, flags=re.I)
        pretty = re.sub(r'\bjoin\s+\S+', '', pretty, flags=re.I)

        # Remove empty lines
        pretty = '\n'.join(line for line in pretty.splitlines() if line.strip())

        if not pretty.strip():
            pretty = "⚠️ No data returned (or all fields were promotional and stripped)."

        # ---------- Detect API error response ----------
        is_error = False
        error_msg = ""
        if status_code >= 400:
            is_error = True
            error_msg = f"API returned HTTP {status_code}"
        elif isinstance(data, dict):
            # Common error keys
            for k in ('error', 'message', 'msg', 'status', 'success'):
                if k in data and str(data[k]).lower() in ('false', 'error', 'failed', 'fail'):
                    is_error = True
                    error_msg = str(data.get('message', data.get('msg', 'API error')))
                    break

        # If API error — do NOT deduct credits
        if is_error and ('error' in pretty.lower() or 'fail' in pretty.lower() or status_code >= 400):
            conn.close()
            return jsonify({
                "success": False,
                "message": f"{error_msg} — API Response: {pretty[:300]}",
                "raw": pretty
            })

        # ---------- Success: deduct credits ----------
        new_credits = user['credits'] - cost
        conn.execute("UPDATE users SET credits=? WHERE id=?", (new_credits, user_id))
        conn.execute("INSERT INTO history (user_id, tool, query, cost) VALUES (?, ?, ?, ?)",
                     (user_id, tool, q, cost))
        conn.commit()
        conn.close()

        # Mask the key in the displayed URL
        safe_url = f"{API_BASE}?={api_name}&key=***&{param}={q}"

        return jsonify({
            "success": True,
            "status": status_code,
            "pretty": pretty,
            "url": safe_url,
            "cost": cost,
            "remaining": new_credits,
        })

    except requests.exceptions.Timeout:
        conn.close()
        return jsonify({"success": False, "message": "⏱ API timeout. Credit NOT deducted. Try again."}), 504
    except requests.exceptions.ConnectionError as e:
        conn.close()
        return jsonify({"success": False, "message": f"🌐 Connection error: {str(e)}. Credit NOT deducted."}), 503
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": f"❌ Error: {str(e)}. Credit NOT deducted."}), 500
```

---

📁 PART 2 — Copy this after Part 1

```python
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
                    📌 Payment ke baad <b>UTR / Transaction ID</b> neeche form me daale.<br>
                    ⏱ Admin verify karke credits add karega.
                </p>
                <div style="margin-top:15px;display:flex;gap:10px;flex-wrap:wrap;">
                    <a href="upi://pay?pa={UPI_ID}&pn={UPI_NAME}&cu=INR" class="btn">📲 Open UPI App</a>
                </div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2 style="font-size:1.2rem;margin-bottom:15px;color:#00f2fe;">📝 Submit Payment Proof</h2>
        <form method="POST" action="/submit-payment">
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
            Admin verification ke baad credits add ho jayenge.
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
# INBOX (broadcasts for users)
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
            <textarea class="input" name="message" rows="4" placeholder="Yahan message likho... Sabhi users ko inbox me dikhega." required
                      style="resize:vertical;font-family:inherit;margin-bottom:10px;"></textarea>
            <button class="btn" style="width:100%;">📤 Send to All Users</button>
        </form>
        <p style="color:#888;font-size:.8rem;margin-top:10px;">Note: Ye message sabhi users ke Inbox me chala jayega aur unke dashboard par bhi dikhega.</p>
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


# ============================================================
# ADMIN BROADCAST
# ============================================================
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
