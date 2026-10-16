"""
🕵️ Ritesh OSINT Toolkit - All-in-One (Updated with New API)
Features: User Auth + Credits + Admin Panel + UPI/QR Payment
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
API_BASE = "https://api.osintxc.com"
API_KEY = "DADDY"
TIMEOUT = 25
DB_PATH = "osint.db"
STATIC_DIR = Path("static")
STATIC_DIR.mkdir(exist_ok=True)

# UPI Payment Config
UPI_ID = "riteshgiri7930@okhdfcbank"              # <-- Apna UPI ID yahan daalo
UPI_NAME = "Ritesh Giri"        # <-- Apna naam
QR_IMAGE = "qr.png"                # static/qr.png me rakho
ADMIN_USERNAME = "@SADAURA4U"           # <-- Admin username
ADMIN_PASSWORD = "ritesh111"        # <-- Admin password (change karo!)

# Credit Packages (₹ -> credits)
PACKAGES = [
    {"id": "p1",  "amount": 50,   "credits": 50,   "label": "₹50 - 50 Credits"},
    {"id": "p2",  "amount": 100,  "credits": 120,  "label": "₹100 - 120 Credits (Bonus)"},
    {"id": "p3",  "amount": 250,  "credits": 320,  "label": "₹250 - 320 Credits (Bonus)"},
    {"id": "p4",  "amount": 500,  "credits": 700,  "label": "₹500 - 700 Credits (Best Value)"},
    {"id": "p5",  "amount": 1000, "credits": 1500, "label": "₹1000 - 1500 Credits (Mega)"},
]

# Default credit cost per API call
DEFAULT_COST = 1

# ============================================================
# ENDPOINTS - New API endpoints
# ============================================================
ENDPOINTS = {
    "num":  {"path": "num",  "param": "number", "label": "📞 Number Lookup",  "placeholder": "9876543210", "category": "📱 Phone", "cost": 2},
    # Add more endpoints here as needed, following the same pattern:
    # "endpoint_name": {"path": "endpoint_path", "param": "param_name", "label": "Display Label", "placeholder": "example", "category": "Category", "cost": 1},
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

    # Create admin if not exists
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
.navbar .links { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
.navbar .links a, .navbar .links span {
    font-size: 0.9rem; color: #ccc; padding: 6px 12px; border-radius: 6px;
    transition: all 0.2s;
}
.navbar .links a:hover { background: rgba(79,172,254,0.15); color: #fff; text-decoration: none; }
.credit-badge {
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #000; font-weight: bold; padding: 6px 12px; border-radius: 20px;
    font-size: 0.85rem;
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
</style>
"""


def render_page(title, content, extra_head=""):
    user = current_user()
    nav_user = ""
    if user:
        nav_user = f'''
            <span class="credit-badge">💰 {user["credits"]} Credits</span>
            <a href="/buy">🛒 Buy</a>
            <a href="/history">📜 History</a>
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
                         (u, generate_password_hash(p), 5))  # 5 free credits
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
# MAIN DASHBOARD
# ============================================================
@app.route('/')
@login_required
def index():
    user = current_user()
    content = f"""
    <h1 style="text-align:center;font-size:1.8rem;margin-top:20px;">🕵️ OSINT Toolkit</h1>
    <p class="subtitle" style="text-align:center;margin-bottom:25px;">
        Welcome, <b>{user['username']}</b>! • {len(ENDPOINTS)} tools available • Har tool ka alag credit cost hai
    </p>

    <div class="tabs" style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:20px;">
        <button class="tab-btn active" data-cat="ALL" onclick="filterCat('ALL', this)">🌐 All</button>
        {"".join(f'<button class="tab-btn" data-cat="{cat}" onclick="filterCat(`{cat}`, this)">{cat}</button>' for cat in GROUPED.keys())}
    </div>

    <div class="tool-grid" id="toolGrid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin-bottom:25px;">
    """

    for cat, items in GROUPED.items():
        for key, cfg in items:
            cost = cfg.get('cost', DEFAULT_COST)
            content += f"""
            <div class="tool-card" data-cat="{cat}" data-key="{key}"
                 onclick="selectTool('{key}', '{cfg['label'].replace(chr(39), '')}', '{cfg['placeholder']}', this)"
                 style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);border-radius:10px;padding:12px;cursor:pointer;transition:all .2s;">
                <div style="font-size:.9rem;font-weight:600;color:#eee;">{cfg['label']}</div>
                <div style="font-size:.7rem;color:#4facfe;margin-top:6px;">💰 Cost: {cost} credits</div>
                <div style="font-size:.7rem;color:#666;margin-top:2px;">/api/{cfg['path']}</div>
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
        document.querySelectorAll('.tool-card').forEach(c => c.style.borderColor = 'rgba(255,255,255,0.08)');
        el.style.borderColor = '#00f2fe';
        el.style.background = 'rgba(79,172,254,0.15)';
        const input = document.getElementById('queryInput');
        input.disabled = false; input.placeholder = placeholder || 'Value daalo...'; input.value = ''; input.focus();
        document.getElementById('searchBtn').disabled = false;
        document.getElementById('output').innerHTML = '';
    }
    document.getElementById('queryInput').addEventListener('keypress', e => { if (e.key === 'Enter') runSearch(); });

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
            // Update credit badge
            const badge = document.querySelector('.credit-badge');
            if (badge && data.remaining_credits !== undefined) badge.textContent = `💰 ${data.remaining_credits} Credits`;
            out.innerHTML = `
                <div style="background:rgba(0,0,0,0.3);padding:10px 14px;border-radius:8px;font-family:monospace;font-size:.78rem;color:#7dd3fc;margin-bottom:15px;word-break:break-all;border-left:3px solid #4facfe;">🔗 ${data.url}</div>
                <div style="background:rgba(255,200,0,0.1);border-left:4px solid #ffc800;padding:10px;border-radius:8px;margin-bottom:12px;font-size:.85rem;">💸 ${data.cost} credits deducted • Remaining: <b>${data.remaining_credits}</b></div>
                <div class="card"><pre style="white-space:pre-wrap;word-break:break-word;font-size:.82rem;line-height:1.6;color:#b8f0ff;">${escapeHtml(data.pretty)}</pre></div>
            `;
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
# API LOOKUP (with credit deduction)
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
        return jsonify({"success": False, "message": f"Insufficient credits. Need {cost}, you have {user['credits']}. Please buy more."})

    # Build URL - New API format: https://api.osintxc.com/num?number=9876543210&key=DADDY
    url = f"{API_BASE}/{cfg['path']}?{cfg['param']}={q}&key={API_KEY}"
    if "extra" in cfg:
        for k, v in cfg["extra"].items():
            url += f"&{k}={v}"

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

        pretty = json.dumps(data, indent=2, ensure_ascii=False) if isinstance(data, (dict, list)) else str(data)

        # Deduct credit + log history (only if request reached API)
        pretty = pretty.replace('by @SADAURA4U', '')
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
            "cost": cost,
            "remaining_credits": new_credits
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
        Current Balance: <b>{user['credits']} credits</b>
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
                    ⏱ Admin verify karke credits add karega (usually 5-30 min).
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
        flash("Invalid data", "error")
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
            Admin verification ke baad credits add ho jayenge.<br>
            Usually 5-30 minutes lagte hain.
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
            <td>💰 {r['cost']}</td>
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
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) c FROM users").fetchone()['c'],
        "total_searches": conn.execute("SELECT COUNT(*) c FROM history").fetchone()['c'],
        "pending_payments": conn.execute("SELECT COUNT(*) c FROM payments WHERE status='pending'").fetchone()['c'],
        "revenue": conn.execute("SELECT COALESCE(SUM(amount),0) s FROM payments WHERE status='approved'").fetchone()['s'],
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

    content = f"""
    <h1 style="text-align:center;font-size:1.6rem;margin:20px 0;">⚙️ Admin Panel</h1>

    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;margin-bottom:20px;">
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Total Users</div><div style="font-size:1.8rem;color:#4facfe;font-weight:bold;">{stats['total_users']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Total Searches</div><div style="font-size:1.8rem;color:#4facfe;font-weight:bold;">{stats['total_searches']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Pending Payments</div><div style="font-size:1.8rem;color:#ffc800;font-weight:bold;">{stats['pending_payments']}</div></div>
        <div class="card"><div style="color:#aaa;font-size:.8rem;">Revenue (₹)</div><div style="font-size:1.8rem;color:#22c55e;font-weight:bold;">{stats['revenue']}</div></div>
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
            • API Key: <code>{API_KEY}</code><br>
            • UPI ID: <b>{UPI_ID}</b><br>
            • Total APIs: <b>{len(ENDPOINTS)}</b><br>
            • QR Image: <code>static/{QR_IMAGE}</code>
        </p>
    </div>
    """
    return render_page("Admin Panel", content)


@app.route('/admin/add-credits', methods=['POST'])
@admin_required
def admin_add_credits():
    uid = request.form.get('user_id')
    amt = int(request.form.get('amount', 0))
    conn = get_db()
    conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amt, uid))
    conn.commit()
    conn.close()
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
    print(f"👑 Admin      : {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"💰 UPI        : {UPI_ID}")
    print(f"📷 QR Image   : static/{QR_IMAGE}")
    print(f"🔑 API Base   : {API_BASE}")
    print(f"🔑 API Key    : {API_KEY}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
