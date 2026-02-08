# Vigilant AI — NDIS Compliance Agent

An automated compliance engine that audits support worker progress notes against NDIS Quality & Safeguards standards, flags risks, and coaches staff via SMS.

## Pipeline

```
dummy.py → shiftcare_messy_export.csv
                    │
                audit.py (LLM grades each note via AEGIS Core)
                    │
           vigilant_audit_report.csv
                    │
              notify.py (SMS coaching to staff via Twilio)
                    │
              Staff replies via SMS
                    │
             webhooks.py (receives reply, logs the fix)
```

## Components

| File | Purpose |
|---|---|
| `dummy.py` | Generates 20 rows of messy ShiftCare export data across 6 scenario types |
| `Audit.md` | System prompt for the AEGIS Core — defines persona, 3-pillar grading logic, and JSON output schema |
| `audit.py` | Reads the CSV, sends each note to Claude for compliance grading, saves results |
| `notify.py` | Reads the audit report and sends coaching SMS to flagged staff via Twilio |
| `webhooks.py` | Flask server that receives incoming SMS replies from staff via Twilio webhooks |
| `staff_list.csv` | Staff name to phone number mapping |
| `pending_fixes.json` | Tracks which staff have outstanding note corrections |

## The AEGIS Core — 3 Pillars of Grading

1. **Goal Alignment** — Does the note link activities to a specific participant goal?
2. **Risk Detection** — Scans for hidden incidents (falls, med refusal) and restrictive practices (locked doors, withheld items)
3. **Language Quality** — Scores 0–100 for person-centred, strengths-based, objective documentation

Each note receives a verdict: `PASS`, `FAIL`, or `CRITICAL`.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_anthropic_key
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=+1234567890
TEST_PHONE_NUMBER=+61412345678
```

### 3. Run the pipeline

```bash
# Generate dummy data
python3 dummy.py

# Audit all notes
python3 audit.py

# Send SMS notifications
python3 notify.py
```

### 4. Start the webhook server

```bash
# Start Flask server
python3 webhooks.py

# In another terminal, expose via ngrok
ngrok http 5001
```

Then set your Twilio phone number's incoming message webhook to:
```
https://<your-ngrok-id>.ngrok-free.app/sms-reply
```

## Safety Modes (notify.py)

| Flag | Effect |
|---|---|
| `SAFETY_MODE = True` | All SMS routed to `TEST_PHONE_NUMBER` instead of real staff |
| `TEST_CHEAP_MODE = True` | Sends 1 summary SMS instead of individual messages per flagged note |

## Tech Stack

- **LLM:** Claude (Anthropic API)
- **SMS:** Twilio
- **Webhook Server:** Flask
- **Data:** pandas
