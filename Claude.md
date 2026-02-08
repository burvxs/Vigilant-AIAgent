Vigilant AI - Project Context & Guidelines

## How to Interact With Me 
Assume I know nothing and consult me before writing code. You are my tech lead while I'm building this project. Identify gaps in my thinking and processes to build a higher performance applicaiton following "Project Identity" 

## Project Identity
Name: Vigilant AI (Vector-3 Integrity Protocol) Role: Enterprise NDIS Compliance & Revenue Protection System. Goal: Automate the auditing of NDIS Progress Notes to prevent regulatory failure and funding clawbacks. Target User: Australian NDIS Providers (SIL/Community Access). Core Mechanism: "Bi-Directional Semantic Auditing" — We don't just read notes; we coach staff via SMS to fix them in real-time.

## Tech Stack & Environment
Language: Python 3.12+

## Core Libraries:

pandas (Data manipulation & cleaning)

playwright (Headless browser for ShiftCare automation)

openai / anthropic (LLM for Semantic Auditing)

twilio (SMS notifications & webhooks)

flask (Handling SMS replies)

pydantic (Data validation)

Infrastructure: Local Dev -> AWS Lambda / Docker (Future).

Region: Australia (Ensure timezones are Australia/Sydney or AEDT).

## Architecture Overview
Phase 1: Ingestion (The "Shadow" Reader)
Source: ShiftCare (SaaS Platform).

Method:

Primary: Email Parser (SendGrid/Postmark receives scheduled CSV reports).

Secondary: playwright script logs in as Admin to scrape Events Report.

Data: CSV format. Columns include Staff Name, Client, Date, Note Body, Shift ID.

Phase 2: The Vector-3 Audit Engine (The Brain)
Input: Raw Text Note.

Reference Data:

staff_list.csv (Maps Name -> Mobile Number).

client_goals.json (Maps Client -> NDIS Goals).

Logic: LLM evaluates note against NDIS Practice Standards:

Goal Link: Does it reference a specific goal?

Safety: Are there "Hidden Incidents" (falls, refusals, behaviors)?

Quality: Is it person-centered or generic ("Had a good day")?

Output: AuditScore (Pass/Fail), RiskLevel (Low/Med/High), SuggestedFix.

Phase 3: The "Feedback Loop" (The Fix)
Channel: SMS (Twilio).

Trigger: If AuditScore = Fail OR RiskLevel > Low.

Flow:

Agent texts Worker: "Note for [Client] is vague. Reply '1' to add: '[AI Suggestion]' or reply with your own text."

Worker replies.

Flask Webhook captures reply.

System appends correction to the official record (Database/CSV).

4. Coding Standards (High Agency)
General Rules
No "Happy Path" Only: Always assume the CSV is messy, the browser will timeout, and the API will fail. Write robust try/except blocks with logging.

Privacy First: NEVER print PII (Client Names) to console logs. Use IDs or masked names (e.g., Clie**).

Async First: Use asyncio for Playwright and API calls to ensure speed.

Type Hinting: Use Python type hints (def process(data: pd.DataFrame) -> dict:) for clarity.

Project Structure
Plaintext

/vigilant-ai
├── /src
│   ├── ingestion.py    # Playwright/Email parsing logic
│   ├── audit.py        # LLM Prompting & Logic
│   ├── notify.py       # Twilio SMS Handler
│   ├── webhooks.py     # Flask Server for Replies
│   └── utils.py        # Phone number formatting, timezones
├── /data
│   ├── raw/            # Incoming CSVs
│   ├── processed/      # Cleaned/Audited Data
│   └── reference/      # staff_list.csv, goals.json
├── /tests              # Pytest files
├── .env                # API Keys (Twilio, OpenAI, ShiftCare)
├── requirements.txt
└── main.py             # Orchestrator

## Key Terminology (Domain Knowledge)
SIL: Supported Independent Living (24/7 Care).

Incident Report: Mandatory form for falls, abuse, injury.

Restrictive Practice: Locking doors, withholding items (Illegal without auth).

ShiftCare: The CRM we are integrating with.

Documentation Drift: The time gap between the shift and the note (Our enemy).

## Current Objective
Build the MVP "Audit Loop".

Load shiftcare_messy_export.csv.

Load staff_list.csv.

Run audit.py to flag "At Risk" notes.

Simulate sending an SMS via notify.py.