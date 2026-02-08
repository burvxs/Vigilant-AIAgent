import os
import json
import pandas as pd
import anthropic
from dotenv import load_dotenv
from pathlib import Path

# ── Configuration ────────────────────────────────────────────────────────────

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-20250514"

# Load system prompt from Audit.md
audit_md_path = Path(__file__).parent / "Audit.md"
SYSTEM_PROMPT = audit_md_path.read_text(encoding="utf-8").strip()
if not SYSTEM_PROMPT:
    print("⚠️  Warning: Audit.md is empty. The LLM will have no grading instructions.")

# ── Audit Function ───────────────────────────────────────────────────────────

def audit_note(note_text: str, client_goals: str) -> dict:
    """Send a single progress note to the LLM for NDIS compliance grading."""

    user_message = f"Note: {note_text}\nGoals: {client_goals}"

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message},
                # Prefill with '{' to force the model into JSON-object output
                {"role": "assistant", "content": "{"},
            ],
        )

        # The response text is everything after our prefilled '{'
        raw = "{" + response.content[0].text
        result = json.loads(raw)
        return result

    except json.JSONDecodeError as e:
        print(f"    ⚠️  JSON parse error: {e}")
        return {"audit_score": "ERROR", "risk_level": "ERROR",
                "language_score": 0, "detected_incidents": [],
                "restrictive_practice_warning": False,
                "coaching_sms": "", "reasoning": f"JSON parse error: {e}"}
    except Exception as e:
        print(f"    ⚠️  API error: {e}")
        return {"audit_score": "ERROR", "risk_level": "ERROR",
                "language_score": 0, "detected_incidents": [],
                "restrictive_practice_warning": False,
                "coaching_sms": "", "reasoning": f"API error: {e}"}

# ── Batch Processing ─────────────────────────────────────────────────────────

def main():
    csv_path = Path(__file__).parent / "shiftcare_messy_export.csv"
    df = pd.read_csv(csv_path)

    total = len(df)
    results = []

    for idx, row in df.iterrows():
        row_num = idx + 1
        staff = row.get("Staff Member", "Unknown")
        note = str(row.get("Progress Note", ""))
        goals = str(row.get("Goals Referenced", ""))

        # Skip empty / trivial notes
        if not note.strip() or len(note.strip()) < 5 or note.strip().lower() == "nan":
            print(f"[Row {row_num}/{total}] Skipping empty note by {staff}")
            results.append({
                "audit_score": "SKIPPED", "risk_level": "N/A",
                "language_score": "", "detected_incidents": "",
                "restrictive_practice_warning": "",
                "coaching_sms": "", "reasoning": "Note empty or too short",
            })
            continue

        audit = audit_note(note, goals)

        verdict = audit.get("audit_score", "UNKNOWN")
        print(f"[Row {row_num}/{total}] Auditing note by {staff}... Result: {verdict}")

        incidents = audit.get("detected_incidents", [])
        results.append({
            "audit_score": audit.get("audit_score", ""),
            "risk_level": audit.get("risk_level", ""),
            "language_score": audit.get("language_score", ""),
            "detected_incidents": ", ".join(incidents) if isinstance(incidents, list) else str(incidents),
            "restrictive_practice_warning": audit.get("restrictive_practice_warning", ""),
            "coaching_sms": audit.get("coaching_sms", ""),
            "reasoning": audit.get("reasoning", ""),
        })

    # ── Build & Save Output ──────────────────────────────────────────────────

    results_df = pd.DataFrame(results)
    output_df = pd.concat([df, results_df], axis=1)

    output_path = Path(__file__).parent / "vigilant_audit_report.csv"
    output_df.to_csv(output_path, index=False)

    print(f"\n✅ Audit complete. Report saved to {output_path.name}")
    print(f"   Total rows:  {total}")
    print(f"   PASS:        {(results_df['audit_score'] == 'PASS').sum()}")
    print(f"   FAIL:        {(results_df['audit_score'] == 'FAIL').sum()}")
    print(f"   CRITICAL:    {(results_df['audit_score'] == 'CRITICAL').sum()}")
    print(f"   ERROR:       {(results_df['audit_score'] == 'ERROR').sum()}")
    print(f"   SKIPPED:     {(results_df['audit_score'] == 'SKIPPED').sum()}")


if __name__ == "__main__":
    main()
