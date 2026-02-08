import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from twilio.rest import Client

# ── Configuration ────────────────────────────────────────────────────────────

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_PHONE_NUMBER")
TEST_NUMBER = os.getenv("TEST_PHONE_NUMBER")

# When True, ALL SMS messages go to TEST_PHONE_NUMBER instead of real staff.
SAFETY_MODE = True

# When True, sends only ONE SMS with a summary of the worst finding, saving Twilio credits.
TEST_CHEAP_MODE = True

twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

BASE_DIR = Path(__file__).parent

# ── Helpers ──────────────────────────────────────────────────────────────────

def to_e164(number: str) -> str:
    """Convert an Australian mobile number (04xx) to E.164 format (+614xx)."""
    number = number.strip().replace(" ", "").replace("-", "")
    if number.startswith("0"):
        return "+61" + number[1:]
    if number.startswith("+"):
        return number
    return "+61" + number


def build_phonebook(staff_csv: Path) -> dict:
    """Load staff_list.csv into a {Full Name: Mobile Number} dictionary."""
    df = pd.read_csv(staff_csv)
    return dict(zip(df["Full Name"].str.strip(), df["Mobile Number"].astype(str).str.strip()))


def send_sms(to_number: str, body: str) -> str:
    """Send an SMS via Twilio. Returns the message SID."""
    message = twilio_client.messages.create(
        body=body,
        from_=TWILIO_FROM,
        to=to_number,
    )
    return message.sid


def log_sms(staff: str, number: str, body: str, sid: str, log_path: Path):
    """Append a timestamped entry to sms_history.log."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] SID={sid} | To={staff} ({number}) | Body={body}\n"
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(entry)

# ── Main Logic ───────────────────────────────────────────────────────────────

def main():
    report_path = BASE_DIR / "vigilant_audit_report.csv"
    staff_path = BASE_DIR / "staff_list.csv"
    log_path = BASE_DIR / "sms_history.log"

    report = pd.read_csv(report_path)
    phonebook = build_phonebook(staff_path)

    sent_count = 0
    skipped_count = 0
    error_count = 0

    if SAFETY_MODE:
        print(f"⚠️  SAFETY MODE ON — all SMS routed to TEST_PHONE_NUMBER ({TEST_NUMBER})")
    if TEST_CHEAP_MODE:
        print(f"💰 CHEAP MODE ON — sending 1 summary SMS only\n")
    else:
        print()

    # ── Collect flagged rows ─────────────────────────────────────────────────

    flagged = []

    for idx, row in report.iterrows():
        staff = str(row.get("Staff Member", "")).strip()
        score = str(row.get("audit_score", "")).strip().upper()
        risk = str(row.get("risk_level", "")).strip().upper()
        sms_body = str(row.get("coaching_sms", "")).strip()

        if score not in ("FAIL", "CRITICAL") and risk != "HIGH":
            skipped_count += 1
            continue

        if not sms_body or sms_body.lower() in ("nan", "no action required."):
            skipped_count += 1
            continue

        real_number = phonebook.get(staff)
        if not real_number:
            print(f"[SKIP] No phone number found for '{staff}'")
            skipped_count += 1
            continue

        flagged.append({"staff": staff, "score": score, "risk": risk,
                        "sms_body": sms_body, "real_number": real_number})

    # ── Send SMS ─────────────────────────────────────────────────────────────

    if TEST_CHEAP_MODE and flagged:
        # Build a single summary SMS from all flagged rows
        score_counts = {}
        for f in flagged:
            score_counts[f["score"]] = score_counts.get(f["score"], 0) + 1

        summary_lines = [f"AEGIS Audit Summary: {len(flagged)} notes flagged."]
        for verdict, count in sorted(score_counts.items()):
            summary_lines.append(f"- {verdict}: {count}")

        # Pick the worst row as a sample
        worst = next((f for f in flagged if f["score"] == "CRITICAL"),
                     next((f for f in flagged if f["score"] == "FAIL"), flagged[0]))
        summary_lines.append(f"Worst: {worst['staff']} ({worst['score']}/{worst['risk']})")
        summary_lines.append(f"Sample: {worst['sms_body'][:100]}")

        body = "\n".join(summary_lines)
        destination = to_e164(TEST_NUMBER)

        try:
            sid = send_sms(destination, body)
            sent_count = 1
            print(f"[SMS SENT] Summary to TEST_NUMBER ({destination}):")
            print(f"  {body}\n")
            log_sms("CHEAP_MODE_SUMMARY", destination, body, sid, log_path)
        except Exception as e:
            error_count = 1
            print(f"[ERROR] Failed to send summary: {e}")

        skipped_count += len(flagged) - 1

    elif not TEST_CHEAP_MODE:
        for f in flagged:
            destination = to_e164(TEST_NUMBER) if SAFETY_MODE else to_e164(f["real_number"])
            mode_label = "Test Mode" if SAFETY_MODE else "LIVE"

            try:
                sid = send_sms(destination, f["sms_body"])
                sent_count += 1
                print(f'[SMS SENT] To {f["staff"]} ({mode_label}): "{f["sms_body"][:70]}..."')
                log_sms(f["staff"], destination, f["sms_body"], sid, log_path)
            except Exception as e:
                error_count += 1
                print(f'[ERROR] Failed to send to {f["staff"]}: {e}')

    # ── Summary ──────────────────────────────────────────────────────────────

    print(f"\n{'='*50}")
    print(f"Sent {sent_count} SMS alert(s).")
    print(f"Flagged {len(flagged)} notes total.")
    print(f"Skipped {skipped_count} compliant/empty notes.")
    if error_count:
        print(f"Errors: {error_count} (check logs).")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
