"""
SMS Simulator CLI — Local testing ground for Vigilant AI.
Fully standalone. No Twilio, no ngrok, no webhooks.py, no Flask.

Usage:
    1. Run notify.py (with SIMULATOR_MODE = True) to populate sms_outbox.json
    2. Run:  python3 sms_simulator.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTBOX_FILE = BASE_DIR / "sms_outbox.json"
PENDING_FILE = BASE_DIR / "pending_fixes.json"
FIX_LOG = BASE_DIR / "fix_history.log"

# ── Colours ───────────────────────────────────────────────────────────────────

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

# ── Data Helpers ──────────────────────────────────────────────────────────────

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


# ── Build Conversations ──────────────────────────────────────────────────────

def build_conversations(outbox: list, pending: dict) -> dict:
    """Group outbox messages by phone number into conversations."""
    conversations = {}
    for msg in outbox:
        phone = msg["to"] if msg.get("direction") == "outbound" else msg["from"]
        if phone not in conversations:
            pending_info = pending.get(phone, {})
            conversations[phone] = {
                "staff_name": msg.get("staff_name", pending_info.get("staff_name", "Unknown")),
                "phone": phone,
                "messages": [],
                "pending_info": pending_info,
                "status": pending_info.get("status", ""),
            }
        conversations[phone]["messages"].append(msg)
    return conversations


# ── Display ───────────────────────────────────────────────────────────────────

def print_header(outbox: list, pending: dict):
    total_out = sum(1 for m in outbox if m.get("direction") == "outbound")
    total_in = sum(1 for m in outbox if m.get("direction") == "inbound")
    total_pending = sum(1 for p in pending.values() if p.get("status") == "AWAITING_REPLY")

    print(f"\n{BOLD}{'=' * 60}")
    print(f"  VIGILANT AI — SMS Simulator (CLI)")
    print(f"{'=' * 60}{RESET}")
    print(f"  {CYAN}{total_out} sent{RESET}  |  {GREEN}{total_in} replies{RESET}  |  {RED}{total_pending} awaiting{RESET}")
    print(f"{DIM}{'─' * 60}{RESET}\n")


def print_conversation(idx: int, phone: str, conv: dict):
    status = conv["status"]
    if status == "AWAITING_REPLY":
        badge = f"{RED}AWAITING REPLY{RESET}"
    elif status == "FIX_RECEIVED":
        badge = f"{GREEN}FIX RECEIVED{RESET}"
    else:
        badge = f"{DIM}—{RESET}"

    print(f"  {BOLD}[{idx}]{RESET}  {BOLD}{conv['staff_name']}{RESET}  {DIM}{phone}{RESET}  {badge}")

    info = conv.get("pending_info", {})
    if info:
        shift = info.get("shift_id", "N/A")
        client = info.get("client", "N/A")
        score = info.get("audit_score", "N/A")
        risk = info.get("risk_level", "N/A")
        print(f"       {DIM}Shift: {shift} | Client: {client} | Score: {score} | Risk: {risk}{RESET}")

    for msg in conv["messages"]:
        direction = msg.get("direction", "outbound")
        body = msg["body"]
        ts = msg.get("timestamp", "")
        if direction == "outbound":
            label = f"{RED}AEGIS Core{RESET}"
        else:
            label = f"{GREEN}{conv['staff_name']}{RESET}"
        # Indent message body, wrap long lines
        print(f"       {label} {DIM}({ts}){RESET}")
        for line in body.split("\n"):
            print(f"         {line}")

    print()


def show_all(conversations: dict):
    if not conversations:
        print(f"  {DIM}No messages yet. Run: python3 notify.py{RESET}\n")
        return

    for idx, (phone, conv) in enumerate(conversations.items(), 1):
        print_conversation(idx, phone, conv)


# ── Reply Handler ─────────────────────────────────────────────────────────────

def handle_reply(conversations: dict):
    """Let user pick a conversation and send a reply as that staff member."""
    # Filter to only conversations awaiting reply
    awaiting = {phone: conv for phone, conv in conversations.items()
                if conv["status"] == "AWAITING_REPLY"}

    if not awaiting:
        print(f"  {YELLOW}No conversations awaiting a reply.{RESET}\n")
        return

    print(f"  {BOLD}Select a staff member to reply as:{RESET}\n")
    items = list(awaiting.items())
    for i, (phone, conv) in enumerate(items, 1):
        info = conv.get("pending_info", {})
        shift = info.get("shift_id", "N/A")
        print(f"    {BOLD}[{i}]{RESET}  {conv['staff_name']}  {DIM}({phone} — {shift}){RESET}")

    print(f"    {BOLD}[0]{RESET}  Cancel\n")

    try:
        choice = input(f"  {CYAN}>{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not choice or choice == "0":
        return

    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(items):
            print(f"  {RED}Invalid selection.{RESET}\n")
            return
    except ValueError:
        print(f"  {RED}Invalid selection.{RESET}\n")
        return

    phone, conv = items[idx]
    staff_name = conv["staff_name"]

    print(f"\n  {BOLD}Replying as {staff_name}{RESET}")
    print(f"  {DIM}Type your corrected note (or 'cancel'):{RESET}\n")

    try:
        reply = input(f"  {GREEN}>{RESET} ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if not reply or reply.lower() == "cancel":
        print(f"  {DIM}Cancelled.{RESET}\n")
        return

    pending = load_pending()
    record = pending.get(phone)
    if not record:
        print(f"  {RED}No pending audit found for {phone}.{RESET}\n")
        return

    shift_id = record.get("shift_id", "N/A")

    # 1. Append inbound reply to outbox
    outbox = load_outbox()
    outbox.append({
        "sid": f"REPLY-{int(datetime.now().timestamp() * 1000)}",
        "from": phone,
        "to": OUTBOX_FILE.name,
        "body": reply,
        "staff_name": staff_name,
        "direction": "inbound",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    save_outbox(outbox)

    # 2. Update pending_fixes.json
    record["status"] = "FIX_RECEIVED"
    record["fix_received"] = reply
    record["fix_timestamp"] = int(datetime.now().timestamp())
    save_pending(pending)

    # 3. Log to fix_history.log
    log_fix(staff_name, phone, shift_id, reply)

    print(f"\n  {GREEN}Fix received from {staff_name} — state updated.{RESET}\n")


# ── Clear Outbox ──────────────────────────────────────────────────────────────

def clear_outbox():
    try:
        confirm = input(f"  {YELLOW}Clear all messages from sms_outbox.json? (y/n):{RESET} ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    if confirm == "y":
        save_outbox([])
        print(f"  {GREEN}Outbox cleared.{RESET}\n")
    else:
        print(f"  {DIM}Cancelled.{RESET}\n")


# ── Main Menu ─────────────────────────────────────────────────────────────────

def main():
    print(f"\n{BOLD}  VIGILANT AI — SMS Simulator (CLI){RESET}")
    print(f"  {DIM}Type a command at any time. Ctrl+C to exit.{RESET}\n")

    while True:
        outbox = load_outbox()
        pending = load_pending()
        conversations = build_conversations(outbox, pending)

        print_header(outbox, pending)
        show_all(conversations)

        print(f"  {BOLD}Commands:{RESET}")
        print(f"    {BOLD}[r]{RESET}  Reply as a staff member")
        print(f"    {BOLD}[c]{RESET}  Clear outbox")
        print(f"    {BOLD}[q]{RESET}  Quit")
        print()

        try:
            cmd = input(f"  {CYAN}>{RESET} ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {DIM}Bye.{RESET}\n")
            break

        if cmd == "r":
            handle_reply(conversations)
        elif cmd == "c":
            clear_outbox()
        elif cmd == "q":
            print(f"\n  {DIM}Bye.{RESET}\n")
            break
        else:
            print(f"  {DIM}Unknown command. Use [r], [c], or [q].{RESET}\n")


if __name__ == "__main__":
    main()
