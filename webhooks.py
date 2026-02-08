import json
from datetime import datetime
from pathlib import Path

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

# ── Configuration ────────────────────────────────────────────────────────────

app = Flask(__name__)
BASE_DIR = Path(__file__).parent
PENDING_FILE = BASE_DIR / "pending_fixes.json"


def load_pending() -> dict:
    """Load the pending fixes lookup from JSON."""
    if not PENDING_FILE.exists():
        return {}
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def log_fix(staff: str, number: str, shift_id: str, body: str):
    """Append received fix to a log file."""
    log_path = BASE_DIR / "fix_history.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] From={staff} ({number}) | Shift={shift_id} | Fix={body}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

# ── Webhook Endpoint ─────────────────────────────────────────────────────────

@app.route("/sms-reply", methods=["POST"])
def sms_reply():
    """Handle incoming SMS replies from staff via Twilio."""

    sender = request.form.get("From", "").strip()
    body = request.form.get("Body", "").strip()

    print(f"\n{'─'*50}")
    print(f"[INCOMING SMS] From: {sender}")
    print(f"[BODY] {body}")

    pending = load_pending()
    record = pending.get(sender)

    resp = MessagingResponse()

    if record:
        staff_name = record.get("staff_name", "Unknown")
        shift_id = record.get("shift_id", "N/A")
        client = record.get("client", "N/A")
        goal = record.get("goal", "N/A")

        print(f'[FIX RECEIVED] From {staff_name}: "{body}"')
        print(f"  Shift: {shift_id} | Client: {client} | Goal: {goal}")
        print(f"{'─'*50}\n")

        log_fix(staff_name, sender, shift_id, body)

        resp.message(
            f"Thanks {staff_name.split()[0]}! Your updated note for {client} "
            f"(Shift {shift_id}) has been received. Record updated."
        )

    else:
        print(f"[NO MATCH] Number {sender} not found in pending_fixes.json")
        print(f"{'─'*50}\n")

        resp.message("Vigilant AI: No pending audits found for your number.")

    return str(resp), 200, {"Content-Type": "application/xml"}

# ── Startup ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("  VIGILANT AI — SMS Webhook Server")
    print("=" * 50)
    print()

    pending = load_pending()
    print(f"Loaded {len(pending)} pending fixes from pending_fixes.json")
    for number, info in pending.items():
        print(f"  {info['staff_name']:20s} ({number}) -> Shift {info['shift_id']}")

    print()
    print("─" * 50)
    print("  HOW TO EXPOSE WITH NGROK:")
    print("─" * 50)
    print("  1. Install ngrok:    brew install ngrok")
    print("  2. Run ngrok:        ngrok http 5001")
    print("  3. Copy the https:// URL ngrok gives you.")
    print("  4. In Twilio Console -> Phone Numbers -> Active Numbers:")
    print(f"     Set 'A Message Comes In' webhook to:")
    print(f"     https://<your-ngrok-id>.ngrok-free.app/sms-reply")
    print("  5. Send an SMS to your Twilio number to test.")
    print("─" * 50)
    print()

    app.run(host="0.0.0.0", port=5001, debug=False)
