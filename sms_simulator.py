"""
SMS Simulator — Local testing ground for Vigilant AI.
Fully standalone. No Twilio, no ngrok, no webhooks.py needed.

Usage:
    1. Run notify.py (with SIMULATOR_MODE = True) to populate sms_outbox.json
    2. Start simulator:  python3 sms_simulator.py
    3. Open browser:     http://localhost:5002
"""

import json
from datetime import datetime
from pathlib import Path

from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
OUTBOX_FILE = BASE_DIR / "sms_outbox.json"
PENDING_FILE = BASE_DIR / "pending_fixes.json"
FIX_LOG = BASE_DIR / "fix_history.log"

# ── Data Helpers ─────────────────────────────────────────────────────────────

def load_outbox() -> list:
    if not OUTBOX_FILE.exists():
        return []
    with open(OUTBOX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_outbox(outbox: list):
    with open(OUTBOX_FILE, "w", encoding="utf-8") as f:
        json.dump(outbox, f, indent=2, ensure_ascii=False)


def load_pending() -> dict:
    if not PENDING_FILE.exists():
        return {}
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_pending(pending: dict):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(pending, f, indent=2, ensure_ascii=False)


def log_fix(staff: str, number: str, shift_id: str, body: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] From={staff} ({number}) | Shift={shift_id} | Fix={body}\n"
    with open(FIX_LOG, "a", encoding="utf-8") as f:
        f.write(entry)


# ── HTML Templates ───────────────────────────────────────────────────────────

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Vigilant AI — SMS Simulator</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            min-height: 100vh;
        }
        .header {
            background: #16213e;
            padding: 20px;
            border-bottom: 2px solid #0f3460;
            text-align: center;
        }
        .header h1 { color: #e94560; font-size: 24px; }
        .header .sub { color: #888; font-size: 13px; margin-top: 4px; }
        .stats {
            margin-top: 10px;
            display: flex;
            justify-content: center;
            gap: 8px;
        }
        .stats span {
            background: #0f3460;
            padding: 4px 14px;
            border-radius: 12px;
            font-size: 13px;
        }
        .stats .critical { background: #e94560; color: white; }
        .container { max-width: 800px; margin: 20px auto; padding: 0 16px; }
        .conversation {
            background: #16213e;
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid #0f3460;
        }
        .conv-header {
            background: #0f3460;
            padding: 12px 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .conv-header .name { font-weight: 600; font-size: 16px; }
        .conv-header .phone { color: #888; font-size: 13px; }
        .badge {
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            color: white;
        }
        .badge-awaiting { background: #e94560; }
        .badge-received { background: #4ecca3; }
        .pending-info {
            background: #1a1a2e;
            margin: 12px 16px 0;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            border-left: 3px solid #e94560;
        }
        .pending-info strong { color: #e94560; }
        .messages { padding: 16px; }
        .msg {
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 16px;
            margin-bottom: 8px;
            font-size: 14px;
            line-height: 1.5;
        }
        .msg-out {
            background: #0f3460;
            margin-left: auto;
            border-bottom-right-radius: 4px;
        }
        .msg-in {
            background: #2d4059;
            margin-right: auto;
            border-bottom-left-radius: 4px;
        }
        .msg-meta {
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }
        .msg-label {
            font-size: 11px;
            font-weight: 600;
            margin-bottom: 4px;
        }
        .msg-label-out { color: #e94560; }
        .msg-label-in { color: #4ecca3; }
        .reply-form {
            display: flex;
            padding: 12px 16px;
            gap: 8px;
            border-top: 1px solid #0f3460;
            background: #1a1a2e;
        }
        .reply-form input[type="text"] {
            flex: 1;
            padding: 10px 14px;
            border-radius: 20px;
            border: 1px solid #0f3460;
            background: #16213e;
            color: #e0e0e0;
            font-size: 14px;
            outline: none;
        }
        .reply-form input[type="text"]:focus { border-color: #e94560; }
        .reply-form button {
            background: #4ecca3;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
            font-size: 14px;
        }
        .reply-form button:hover { background: #3dbb92; }
        .empty {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        .empty h2 { margin-bottom: 12px; color: #888; }
        .empty code {
            display: block;
            margin-top: 12px;
            color: #e94560;
            font-size: 14px;
        }
        .flash {
            max-width: 800px;
            margin: 12px auto;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
        }
        .flash-success { background: #1a3a2a; border: 1px solid #4ecca3; color: #4ecca3; }
        .flash-error { background: #3a1a1a; border: 1px solid #e94560; color: #e94560; }
        .refresh-bar {
            text-align: center;
            padding: 12px;
            font-size: 12px;
            color: #555;
        }
        .refresh-bar a { color: #e94560; text-decoration: none; }
        .clear-link {
            display: inline-block;
            margin-top: 8px;
            color: #e94560;
            font-size: 12px;
            text-decoration: none;
        }
        .clear-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="header">
        <h1>VIGILANT AI &mdash; SMS Simulator</h1>
        <div class="sub">Local testing ground &mdash; no Twilio, no cost</div>
        <div class="stats">
            <span>{{ total_outbound }} sent</span>
            <span>{{ total_inbound }} replies</span>
            <span class="critical">{{ total_pending }} pending</span>
        </div>
        <a class="clear-link" href="/clear-outbox"
           onclick="return confirm('Clear all messages from sms_outbox.json?')">
           Clear outbox
        </a>
    </div>

    {% if flash_msg %}
    <div class="flash {{ flash_class }}" style="max-width:800px; margin:12px auto; padding:0 16px;">
        {{ flash_msg }}
    </div>
    {% endif %}

    <div class="container">
        {% if not conversations %}
        <div class="empty">
            <h2>No messages yet</h2>
            <p>Run notify.py with SIMULATOR_MODE = True to populate the outbox.</p>
            <code>python3 notify.py</code>
        </div>
        {% endif %}

        {% for phone, conv in conversations.items() %}
        <div class="conversation">
            <div class="conv-header">
                <div>
                    <div class="name">{{ conv.staff_name }}</div>
                    <div class="phone">{{ conv.phone }}</div>
                </div>
                {% if conv.status == "AWAITING_REPLY" %}
                <span class="badge badge-awaiting">AWAITING REPLY</span>
                {% elif conv.status == "FIX_RECEIVED" %}
                <span class="badge badge-received">FIX RECEIVED</span>
                {% endif %}
            </div>

            {% if conv.pending_info %}
            <div class="pending-info">
                <strong>Shift:</strong> {{ conv.pending_info.get('shift_id', 'N/A') }} &middot;
                <strong>Client:</strong> {{ conv.pending_info.get('client', 'N/A') }} &middot;
                <strong>Score:</strong> {{ conv.pending_info.get('audit_score', 'N/A') }} &middot;
                <strong>Risk:</strong> {{ conv.pending_info.get('risk_level', 'N/A') }}
            </div>
            {% endif %}

            <div class="messages">
                {% for msg in conv.messages %}
                {% if msg.direction == "inbound" %}
                <div class="msg msg-in">
                    <div class="msg-label msg-label-in">{{ conv.staff_name }} replied</div>
                    {{ msg.body }}
                    <div class="msg-meta">{{ msg.timestamp }}</div>
                </div>
                {% else %}
                <div class="msg msg-out">
                    <div class="msg-label msg-label-out">AEGIS Core</div>
                    {{ msg.body }}
                    <div class="msg-meta">SID: {{ msg.sid }} &middot; {{ msg.timestamp }}</div>
                </div>
                {% endif %}
                {% endfor %}
            </div>

            {% if conv.status != "FIX_RECEIVED" %}
            <form class="reply-form" action="/simulate-reply" method="POST">
                <input type="hidden" name="phone" value="{{ phone }}">
                <input type="text" name="body"
                       placeholder="Reply as {{ conv.staff_name }}..."
                       required autocomplete="off">
                <button type="submit">Send</button>
            </form>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <div class="refresh-bar">
        Auto-refreshes every 5s &middot; <a href="/">Refresh now</a>
    </div>
    <script>setTimeout(function() { window.location.reload(); }, 5000);</script>
</body>
</html>
"""

# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_page()


@app.route("/simulate-reply", methods=["POST"])
def simulate_reply():
    phone = request.form.get("phone", "").strip()
    body = request.form.get("body", "").strip()

    if not phone or not body:
        return render_page(flash_msg="Phone and reply body are required.",
                           flash_class="flash-error")

    pending = load_pending()
    record = pending.get(phone)

    if not record:
        return render_page(
            flash_msg=f"No pending audit found for {phone}.",
            flash_class="flash-error")

    staff_name = record.get("staff_name", "Unknown")
    shift_id = record.get("shift_id", "N/A")
    client = record.get("client", "N/A")

    # 1. Append inbound reply to the outbox so it shows in the conversation
    outbox = load_outbox()
    outbox.append({
        "sid": f"REPLY-{int(datetime.now().timestamp() * 1000)}",
        "from": phone,
        "to": OUTBOX_FILE.name,
        "body": body,
        "staff_name": staff_name,
        "direction": "inbound",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_outbox(outbox)

    # 2. Update pending_fixes.json status
    record["status"] = "FIX_RECEIVED"
    record["fix_received"] = body
    record["fix_timestamp"] = int(datetime.now().timestamp())
    save_pending(pending)

    # 3. Log to fix_history.log
    log_fix(staff_name, phone, shift_id, body)

    print(f'[FIX RECEIVED] From {staff_name} ({phone}): "{body}"')
    print(f"  Shift: {shift_id} | Client: {client}")

    return render_page(
        flash_msg=f"Reply received from {staff_name} for {client} (Shift {shift_id}). Record updated.",
        flash_class="flash-success")


@app.route("/clear-outbox")
def clear_outbox():
    save_outbox([])
    return render_page(flash_msg="Outbox cleared.", flash_class="flash-success")


@app.route("/api/messages")
def api_messages():
    return jsonify({"outbox": load_outbox(), "pending": load_pending()})


# ── Page Renderer ────────────────────────────────────────────────────────────

def render_page(flash_msg="", flash_class=""):
    outbox = load_outbox()
    pending = load_pending()

    # Group messages by phone number
    conversations = {}
    for msg in outbox:
        # For outbound messages, group by "to". For inbound replies, group by "from".
        phone = msg["to"] if msg.get("direction") == "outbound" else msg["from"]

        if phone not in conversations:
            pending_info = pending.get(phone, {})
            conversations[phone] = {
                "staff_name": msg.get("staff_name",
                                      pending_info.get("staff_name", "Unknown")),
                "phone": phone,
                "messages": [],
                "pending_info": pending_info,
                "status": pending_info.get("status", ""),
            }
        conversations[phone]["messages"].append(msg)

    total_outbound = sum(1 for m in outbox if m.get("direction") == "outbound")
    total_inbound = sum(1 for m in outbox if m.get("direction") == "inbound")
    total_pending = sum(1 for p in pending.values() if p.get("status") == "AWAITING_REPLY")

    return render_template_string(
        MAIN_TEMPLATE,
        conversations=conversations,
        total_outbound=total_outbound,
        total_inbound=total_inbound,
        total_pending=total_pending,
        flash_msg=flash_msg,
        flash_class=flash_class,
    )


# ── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    outbox = load_outbox()
    pending = load_pending()

    print("=" * 50)
    print("  VIGILANT AI — SMS Simulator")
    print("=" * 50)
    print(f"  Outbox:  {len(outbox)} message(s)")
    print(f"  Pending: {len(pending)} fix(es)")
    print()
    print("  Open in browser: http://localhost:5002")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5002, debug=False)
