from flask import Flask, request, render_template_string, jsonify
import requests
import os

app = Flask(__name__)

API_URL = "https://api.osintxc.com/num"
API_KEY = "DADDY"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Ritesh Number Lookup</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial, sans-serif; }
        body {
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            padding: 20px;
            color: #fff;
        }
        .container { max-width: 1100px; margin: 0 auto; }
        h1 {
            text-align: center;
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00f2fe, #4facfe);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .subtitle { text-align: center; color: #aaa; margin-bottom: 25px; font-size: 0.9rem; }
        .search-box {
            display: flex;
            gap: 10px;
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 14px;
            border: none;
            border-radius: 8px;
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 1rem;
            outline: none;
            border: 1px solid rgba(255,255,255,0.1);
        }
        input[type="text"]:focus { border-color: #4facfe; }
        button {
            padding: 14px 30px;
            border: none;
            border-radius: 8px;
            background: linear-gradient(90deg, #00f2fe, #4facfe);
            color: #000;
            font-weight: bold;
            cursor: pointer;
            font-size: 1rem;
            transition: transform 0.2s;
        }
        button:hover { transform: scale(1.05); }
        button:disabled { opacity: 0.5; cursor: wait; }
        .stats {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            padding: 15px 20px;
            border-radius: 10px;
            border-left: 4px solid #4facfe;
            flex: 1;
            min-width: 150px;
        }
        .stat-card .label { font-size: 0.8rem; color: #aaa; }
        .stat-card .value { font-size: 1.5rem; font-weight: bold; color: #4facfe; margin-top: 5px; }
        .result-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: transform 0.2s;
        }
        .result-card:hover { transform: translateY(-3px); border-color: #4facfe; }
        .result-card .name {
            font-size: 1.2rem;
            font-weight: bold;
            color: #00f2fe;
            margin-bottom: 10px;
        }
        .info-row {
            display: grid;
            grid-template-columns: 130px 1fr;
            gap: 8px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 0.9rem;
        }
        .info-row .key { color: #888; }
        .info-row .val { color: #eee; word-break: break-word; }
        .error {
            background: rgba(255, 50, 50, 0.15);
            border-left: 4px solid #ff4444;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .loading { text-align: center; padding: 40px; color: #4facfe; }
        .spinner {
            border: 4px solid rgba(255,255,255,0.1);
            border-top: 4px solid #4facfe;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer { text-align: center; margin-top: 30px; color: #555; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📱 Ritesh Number Lookup</h1>
        <p class="subtitle">Enter any 10-digit mobile number to get info</p>

        <div class="search-box">
            <input type="text" id="numberInput" placeholder="Enter 10-digit number (e.g. 9876543210)" maxlength="10">
            <button id="searchBtn" onclick="searchNumber()">🔍 Search</button>
        </div>

        <div id="output"></div>

        <div class="footer"> Ritesh Goswami</div>
    </div>

    <script>
        async function searchNumber() {
            const number = document.getElementById('numberInput').value.trim();
            const output = document.getElementById('output');
            const btn = document.getElementById('searchBtn');

            if (!/^[0-9]{10}$/.test(number)) {
                output.innerHTML = '<div class="error">❌ Please enter a valid 10-digit number</div>';
                return;
            }

            btn.disabled = true;
            output.innerHTML = '<div class="loading"><div class="spinner"></div>Fetching data...</div>';

            try {
                const res = await fetch(`/api/lookup?number=${number}`);
                const data = await res.json();

                if (!data.success) {
                    output.innerHTML = `<div class="error">❌ ${data.message || 'No data found'}</div>`;
                    return;
                }

                let html = `
                    <div class="stats">
                        <div class="stat-card"><div class="label">Total Records</div><div class="value">${data.count}</div></div>
                        <div class="stat-card"><div class="label">Status</div><div class="value">✅ Found</div></div>
                    </div>
                `;

                data.result.forEach((item, i) => {
                    html += `
                        <div class="result-card">
                            <div class="name">#${i + 1} — ${item.name || 'N/A'}</div>
                            <div class="info-row"><span class="key">Mobile</span><span class="val">${item.mobile || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Father Name</span><span class="val">${item.father_name || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Aadhaar</span><span class="val">${item.aadhaar || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Address</span><span class="val">${item.address || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Alt Mobile</span><span class="val">${item.alt_mobile || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Circle</span><span class="val">${item.circle || 'N/A'}</span></div>
                            <div class="info-row"><span class="key">Email</span><span class="val">${item.email || 'N/A'}</span></div>
                        </div>
                    `;
                });

                output.innerHTML = html;
            } catch (err) {
                output.innerHTML = `<div class="error">❌ Error: ${err.message}</div>`;
            } finally {
                btn.disabled = false;
            }
        }

        document.getElementById('numberInput').addEventListener('keypress', e => {
            if (e.key === 'Enter') searchNumber();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/lookup')
def lookup():
    number = request.args.get('number', '').strip()

    if not number.isdigit() or len(number) != 10:
        return jsonify({"success": False, "message": "Invalid 10-digit number"}), 400

    try:
        r = requests.get(
            API_URL,
            params={"number": number, "key": API_KEY},
            timeout=20
        )
        data = r.json()

        if not data.get('success') or not data.get('found'):
            return jsonify({
                "success": False,
                "message": "No records found for this number"
            })

        return jsonify({
            "success": True,
            "count": data.get('count', 0),
            "result": data.get('result', [])
        })

    except requests.exceptions.Timeout:
        return jsonify({"success": False, "message": "API timeout. Try again."}), 504
    except Exception as e:
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500


if __name__ == '__main__':
    print("🚀 Server starting...")
    print("📍 Open in browser: http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
