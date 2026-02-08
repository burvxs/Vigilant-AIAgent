import pandas as pd
import random
from datetime import datetime, timedelta

# 1. Setup Dummy Data
staff_names = ["Sarah Jenkins", "Mike Ross", "David Kim", "Emily Blunt", "Gary Oldman"]
clients = ["Liam H. (Participant)", "Noah B. (Participant)", "Olivia C. (Participant)"]
shift_types = ["SIL - Day", "SIL - Sleepover", "Community Access", "Personal Care"]

# 2. The "Vigilant AI" Scenarios (The Good, The Bad, & The Ugly)
notes_scenarios = [
    # TYPE A: The "Gold Standard" (Perfect Compliance)
    {
        "note": "Arrived at 0900. Supported Liam with morning routine as per care plan. Liam chose to wear his blue shirt. We worked on his goal of 'Money Handling' by going to Coles, where he used the self-checkout independently. Liam appeared happy and engaged. No incidents.",
        "goals_linked": "Money Handling, Independence",
        "incident": "No"
    },
    
    # TYPE B: The "Lazy Support Worker" (Audit Risk: Vague)
    {
        "note": "Had a good day. We went to the park and ate lunch. Liam was happy.",
        "goals_linked": "", # MISSING GOAL LINK
        "incident": "No"
    },
    
    # TYPE C: The "Hidden Incident" (Legal Risk: Fall)
    {
        "note": "Quiet shift. Noah was watching TV most of the day. He tripped over the rug in the hallway around 2pm but got back up and said he was fine, just a small red mark on his knee. Ate dinner well.",
        "goals_linked": "Daily Living",
        "incident": "No" # FALSE: This should be YES.
    },
    
    # TYPE D: The "Restrictive Practice" (Human Rights Violation)
    {
        "note": "Olivia was yelling at 4pm because she wanted a Coke. I told her she wasn't allowed to have one until she calmed down. I locked the pantry door so she couldn't get it. She eventually went to her room.",
        "goals_linked": "Emotional Regulation",
        "incident": "Yes" # Technically yes, but often missed.
    },
    
    # TYPE E: The "Medical Risk" (Duty of Care)
    {
        "note": "Administered evening meds. Noah refused his blood pressure tablet, said it tastes bad. I tried twice but he wouldn't take it. Settled for bed at 20:00.",
        "goals_linked": "Health & Wellbeing",
        "incident": "No" # FALSE: Med refusal is reportable in many orgs.
    },
    
    # TYPE F: The "Drift" (Opinion based, not factual)
    {
        "note": "Liam was being really lazy today. Didn't want to do anything. I think he is just trying to get out of doing his chores.",
        "goals_linked": "Daily Living",
        "incident": "No"
    }
]

# 3. Generate 20 Rows of "Messy" ShiftCare Data
data = []
start_date = datetime.now() - timedelta(days=7)

for i in range(20):
    scenario = random.choice(notes_scenarios)
    
    row = {
        "Shift ID": f"SC-{1000+i}",
        "Date": (start_date + timedelta(days=i % 3)).strftime("%Y-%m-%d"),
        "Client": random.choice(clients),
        "Staff Member": random.choice(staff_names),
        "Shift Type": random.choice(shift_types),
        "Start Time": "09:00",
        "End Time": "17:00",
        "Progress Note": scenario["note"], # The mess
        "Goals Referenced": scenario["goals_linked"],
        "Incident Flag (Manual)": scenario["incident"]
    }
    data.append(row)

# 4. Save to CSV
df = pd.DataFrame(data)
df.to_csv("shiftcare_messy_export.csv", index=False)

print("✅ 'shiftcare_messy_export.csv' generated.")
print("Use this file to test your 'Vigilant AI' auditing logic.")