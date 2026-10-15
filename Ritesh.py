from flask import Flask, request, render_template_string, jsonify
import requests
import os
import json

app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================
API_BASE = "https://ftosint.world/api"
API_KEY = "cobra-limited-land"
TIMEOUT = 25

# ============================================================
# SAARE ENDPOINTS (28 APIs)
# ============================================================
ENDPOINTS = {
    # -------- Phone --------
    "number":     {"path": "number",     "param": "num",     "label": "📞 Number Lookup",           "placeholder": "9876543210",       "category": "📱 Phone"},
    "numleak":    {"path": "numleak",    "param": "num",     "label": "🔎 Number Leak (HiTeck+ICMR)", "placeholder": "9876543210",       "category": "📱 Phone"},

    # -------- Address --------
    "address":    {"path": "address",    "param": "address", "label": "📍 Address Lookup",           "placeholder": "Okhla Delhi",      "category": "📍 Address"},
    "pincode":    {"path": "pincode",    "param": "pin",     "label": "📍 Pincode",                 "placeholder": "110001",           "category": "📍 Address"},

    # -------- Vehicle --------
    "vehicle":    {"path": "vehicle",    "param": "vehicle", "label": "🚗 Vehicle to Owner",         "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "veh2num":    {"path": "veh2num",    "param": "vehicle", "label": "🚗 Vehicle to Mobile",        "placeholder": "KL41V3504",        "category": "🚗 Vehicle"},
    "fastag":     {"path": "fastag",     "param": "vehicle", "label": "🏷 FASTag Lookup",             "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "challan":    {"path": "challan",    "param": "vehicle", "label": "🧾 Challan Lookup",            "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "rcpdf":      {"path": "rcpdf",      "param": "vehicle", "label": "📄 RC PDF",                   "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "rcchip":     {"path": "rcchip",     "param": "vehicle", "label": "📄 RC PDF Chip",              "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "vinfo":      {"path": "vinfo",      "param": "reg",     "label": "📘 VInfo RC Details",         "placeholder": "MH16BZ7090",       "category": "🚗 Vehicle"},
    "puc":        {"path": "puc",        "param": "reg",     "label": "🌿 PUC Certificate PDF",      "placeholder": "MH16BZ7090",       "category": "🚗 Vehicle"},
    "hw":         {"path": "hw",         "param": "chasi",   "label": "⚙️ Chassis / Engine Lookup",  "placeholder": "MA3NYFB1SKD530868", "category": "🚗 Vehicle"},
    "hpt":        {"path": "hpt",        "param": "reg",     "label": "📝 HP / Financier Record",    "placeholder": "KA01AB1234",       "category": "🚗 Vehicle"},
    "vehindex":   {"path": "vehindex",   "param": "reg",     "label": "📋 Vehicle Index Lookup",     "placeholder": "MH16BZ7090",       "category": "🚗 Vehicle"},

    # -------- Banking --------
    "ifsc":       {"path": "ifsc",       "param": "ifsc",    "label": "🏦 IFSC Lookup",              "placeholder": "SBIN0001234",      "category": "🏦 Banking"},

    # -------- Tax / GST / PAN --------
    "pan":        {"path": "pan",        "param": "pan",     "label": "🪪 PAN to GST",               "placeholder": "ABCDE1234F",       "category": "🪪 Tax / PAN / GST"},
    "paninfo":    {"path": "paninfo",    "param": "pan",     "label": "🪪 PAN to Info",              "placeholder": "BNZPM2501F",       "category": "🪪 Tax / PAN / GST"},
    "pantogstin": {"path": "pantogstin", "param": "pan",     "label": "🪪 PAN to GSTIN",             "placeholder": "ANXPV7978A",       "category": "🪪 Tax / PAN / GST"},
    "gstin":      {"path": "gstin",      "param": "gstin",   "label": "🪪 GSTIN to Info",            "placeholder": "07AABCF8078M1Z3",  "category": "🪪 Tax / PAN / GST"},
    "gstin2pan":  {"path": "gstin2pan",  "param": "gstin",   "label": "🔄 GSTIN to PAN",             "placeholder": "07AABCF8078M1Z3",  "category": "🪪 Tax / PAN / GST"},
    "gstreturns": {"path": "gstreturns", "param": "gstin",   "label": "🧾 GST Returns",              "placeholder": "07AABCF8078M1Z3",  "category": "🪪 Tax / PAN / GST",
                   "extra": {"financial_year": "2023-24"}},
    "name2gstin": {"path": "name2gstin", "param": "name",    "label": "🔎 Name to GSTIN",            "placeholder": "FLIPKART",         "category": "🪪 Tax / PAN / GST"},
    "nametoinfo": {"path": "nametoinfo", "param": "name",    "label": "👤 Name to Info",             "placeholder": "RAHUL",            "category": "🪪 Tax / PAN / GST"},
    "namesearch": {"path": "namesearch", "param": "q",       "label": "👤 Name Search",              "placeholder": "Ramesh",           "category": "🪪 Tax / PAN / GST",
                   "extra": {"from": "Delhi"}},

    # -------- Identity --------
    "aadhar":     {"path": "aadhar",     "param": "num",     "label": "🆔 Aadhaar Lookup",           "placeholder": "393933081942",     "category": "🆔 Identity"},
    "voter":      {"path": "voter",      "param": "id",      "label": "🗳 Voter ID Lookup",          "placeholder": "ZNO1150077",       "category": "🆔 Identity"},
}

# Category-wise grouping
GROUPED = {}
for k, v in ENDPOINTS.items():
    GROUPED.setdefault(v["category"], []).append((k, v))


# ============================================================
# HTML TEMPLATE
# ============================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🕵️ Ritesh OSINT Toolkit — All-in-One</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
body {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh; padding: 20px; color: #fff;
}
.container { max-width: 1200px; margin: 0 auto; }
h1 {
    text-align: center; font-size: 2rem; margin-bottom: 8px;
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.subtitle { text-align: center; color: #aaa; margin-bottom: 25px; font-size: 0.9rem; }

/* Tabs */
.tabs {
    display: flex; flex-wrap: wrap; gap: 8px; justify-content: center;
    margin-bottom: 20px;
}
.tab-btn {
    padding: 8px 16px; border-radius: 20px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: #ccc; cursor: pointer; font-size: 0.85rem;
    transition: all 0.2s;
}
.tab-btn:hover { border-color: #4facfe; color: #fff; }
.tab-btn.active {
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #000; font-weight: bold; border: none;
}

/* Tool grid */
.tool-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 12px;
    margin-bottom: 25px;
}
.tool-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 12px;
    cursor: pointer; transition: all 0.2s;
}
.tool-card:hover { border-color: #4facfe; transform: translateY(-2px); }
.tool-card.active {
    border-color: #00f2fe;
    background: rgba(79, 172, 254, 0.15);
}
.tool-card .tname { font-size: 0.9rem; font-weight: 600; color: #eee; }
.tool-card .tpath { font-size: 0.7rem; color: #666; margin-top: 4px; }
.tool-card .tcat  { font-size: 0.7rem; color: #4facfe; margin-top: 4px; }

/* Search */
.search-box {
    display: flex; gap: 10px;
    background: rgba(255,255,255,0.05);
    padding: 15px; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 20px;
}
input[type="text"] {
    flex: 1; padding: 14px; border-radius: 8px;
    background: rgba(0,0,0,0.3); color: #fff;
    font-size: 1rem; outline: none;
    border: 1px solid rgba(255,255,255,0.1);
    min-width: 0;
}
input[type="text"]:focus { border-color: #4facfe; }
button.go-btn {
    padding: 14px 30px; border: none; border-radius: 8px;
    background: linear-gradient(90deg, #00f2fe, #4facfe);
    color: #000; font-weight: bold; cursor: pointer;
    font-size: 1rem; transition: transform 0.2s; white-space: nowrap;
}
button.go-btn:hover { transform: scale(1.05); }
button.go-btn:disabled { opacity: 0.5; cursor: wait; }

/* Result */
.result-card {
    background: rgba(255,255,255,0.05);
    border-radius: 12px; padding: 20px;
    margin-bottom: 15px;
    border: 1px solid rgba(255,255,255,0.1);
}
.result-card .name {
    font-size: 1.1rem; font-weight: bold;
    color: #00f2fe; margin-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
}
.info-row {
    display: grid; grid-template-columns: 160px 1fr;
    gap: 8px; padding: 6px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    font-size: 0.9rem;
}
.info-row:last-child { border-bottom: none; }
.info-row .key { color: #888; }
.info-row .val { color: #eee; word-break: break-word; }

/* JSON view */
.json-view {
    background: rgba(0,0,0,0.4);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px; padding: 18px;
    overflow: auto; max-height: 70vh;
    white-space: pre-wrap; word-break: break-word;
    font-family: 'Consolas', 'Fira Code', monospace;
    font-size: 0.82rem; line-height: 1.6;
    color: #b8f0ff;
}

.error {
    background: rgba(255, 50, 50, 0.15);
    border-left: 4px solid #ff4444;
    padding: 15px; border-radius: 8px; margin-bottom: 20px;
}
.loading { text-align: center; padding: 40px; color: #4facfe; }
.spinner {
    border: 4px solid rgba(255,255,255,0.1);
    border-top: 4px solid #4facfe;
    border-radius: 50%; width: 40px; height: 40px;
    animation: spin 1s linear infinite; margin: 0 auto 15px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.footer { text-align: center; margin-top: 30px; color: #555; font-size: 0.8rem; }

.url-preview {
    background: rgba(0,0,0,0.3);
    padding: 10px 14px; border-radius: 8px;
    font-family: monospace; font-size: 0.78rem;
    color: #7dd3fc; margin-bottom: 15px;
    word-break: break-all;
    border-left: 3px solid #4facfe;
}

@media (max-width: 600px) {
    h1 { font-size: 1.4rem; }
    .info-row { grid-template-columns: 1fr; }
    .info-row .key { font-size: 0.75rem; }
    .search-box { flex-direction: column; }
}
</style>
</head>
<body>
<div class="container">
    <h1>🕵️ Ritesh OSINT Toolkit</h1>
    <p class="subtitle">All-in-One — 28 APIs integrated • Powered by ftosint.world</p>

    <!-- Category Tabs -->
    <div class="tabs" id="categoryTabs">
        <button class="tab-btn active" data-cat="ALL" onclick="filterCat('ALL', this)">🌐 All Tools</button>
        {% for cat in grouped.keys() %}
            <button class="tab-btn" data-cat="{{ cat }}" onclick="filterCat('{{ cat }}', this)">{{ cat }}</button>
        {% endfor %}
    </div>

    <!-- Tool Grid -->
    <div class="tool-grid" id="toolGrid">
        {% for cat, items in grouped.items() %}
            {% for key, cfg in items %}
            <div class="tool-card" data-cat="{{ cat }}" data-key="{{ key }}"
                 onclick="selectTool('{{ key }}', '{{ cfg.label|e }}', '{{ cfg.placeholder|e }}', this)">
                <div class="tname">{{ cfg.label }}</div>
                <div class="tcat">{{ cfg.category }}</div>
                <div class="tpath">/api/{{ cfg.path }}</div>
            </div>
            {% endfor %}
        {% endfor %}
    </div>

    <!-- Search -->
    <div class="search-box">
        <input type="text" id="queryInput" placeholder="Select a tool first..." disabled>
        <button class="go-btn" id="searchBtn" onclick="runSearch()" disabled>🔍 Search</button>
    </div>

    <div id="output"></div>

    <div class="footer">Made by Ritesh Goswami • Educational use only</div>
</div>

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
    document.querySelectorAll('.tool-card').forEach(c => c.classList.remove('active'));
    el.classList.add('active');
    const input = document.getElementById('queryInput');
    input.disabled = false;
    input.placeholder = placeholder || 'Enter value...';
    input.value = '';
    input.focus();
    document.getElementById('searchBtn').disabled = false;
    document.getElementById('output').innerHTML = '';
}

document.getElementById('queryInput').addEventListener('keypress', e => {
    if (e.key === 'Enter') runSearch();
});

async function runSearch() {
    if (!selectedTool) { alert('Pehle tool select karo'); return; }
    const query = document.getElementById('queryInput').value.trim();
    const out = document.getElementById('output');
    const btn = document.getElementById('searchBtn');

    if (!query) { out.innerHTML = '<div class="error">❌ Value daalo</div>'; return; }

    btn.disabled = true;
    out.innerHTML = '<div class="loading"><div class="spinner"></div>Fetching data from API...</div>';

    try {
        const res = await fetch(`/api/lookup?tool=${encodeURIComponent(selectedTool)}&q=${encodeURIComponent(query)}`);
        const data = await res.json();

        if (!data.success) {
            out.innerHTML = `<div class="error">❌ ${data.message || 'No data found'}</div>`;
            return;
        }

        let html = `<div class="url-preview">🔗 ${data.url}</div>`;

        // Agar data object/array hai — auto render as JSON
        html += `<div class="result-card"><div class="name">📊 Result</div>`;
        html += `<div class="json-view">${escapeHtml(data.pretty)}</div></div>`;

        out.innerHTML = html;
    } catch (err) {
        out.innerHTML = `<div class="error">❌ Error: ${err.message}</div>`;
    } finally {
        btn.disabled = false;
    }
}

function escapeHtml(s) {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}
</script>
</body>
</html>
"""


# ============================================================
# ROUTES
# ============================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, grouped=GROUPED)


@app.route('/api/lookup')
def lookup():
    tool = request.args.get('tool', '').strip()
    q = request.args.get('q', '').strip()

    if tool not in ENDPOINTS:
        return jsonify({"success": False, "message": "Invalid tool"}), 400
    if not q:
        return jsonify({"success": False, "message": "Empty query"}), 400

    cfg = ENDPOINTS[tool]

    # URL build
    url = f"{API_BASE}/{cfg['path']}?key={API_KEY}&{cfg['param']}={q}"
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

        # Pretty print
        if isinstance(data, (dict, list)):
            pretty = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            pretty = str(data)

        return jsonify({
            "success": True,
            "url": url,
            "status": r.status_code,
            "pretty": pretty,
            "raw": data
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "API timeout. Try again."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "message": f"Network error: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🕵️  Ritesh OSINT Toolkit — All-in-One")
    print("="*60)
    print(f"🌐 Open in browser : http://127.0.0.1:8080")
    print(f"📦 Total tools     : {len(ENDPOINTS)} APIs")
    print(f"📂 Categories      : {len(GROUPED)}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
