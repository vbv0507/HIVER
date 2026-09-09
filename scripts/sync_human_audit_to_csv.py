"""
Step 4: Synchronize Human Audit Ratings from Canonical Workbook to CSV

Copies the reviewed human_* fields from:
  eval/judge_human_review_ready_for_manual_check.xlsx
to:
  eval/judge_human_audit.csv

Guarantees:
1. Exactly 50 rows preserved in canonical order.
2. Machine columns (message_id, original_text, agent_response, retrieved_evidence, llm_judge_*)
   remain completely unchanged.
3. Only human_correctness, human_helpfulness, human_groundedness, human_policy, human_escalation,
   and human_notes are updated.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Any, List
import openpyxl

# UTF-8 stdout configuration
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
CANONICAL_WORKBOOK = ROOT_DIR / "eval/judge_human_review_ready_for_manual_check.xlsx"
AUDIT_CSV_PATH = ROOT_DIR / "eval/judge_human_audit.csv"

# Columns in 'Judge-Human Audit'
COL_MESSAGE_ID = 1
COL_ORIGINAL_TEXT = 2
COL_AGENT_RESPONSE = 3
COL_RETRIEVED_EVIDENCE = 4
COL_AUDIT_FLAG = 5
COL_LLM_CORRECTNESS = 6
COL_LLM_HELPFULNESS = 8
COL_LLM_GROUNDEDNESS = 10
COL_LLM_POLICY = 12
COL_LLM_ESCALATION = 14
COL_REVIEW_STATUS = 17
COL_HUMAN_CORRECTNESS = 18
COL_HUMAN_HELPFULNESS = 19
COL_HUMAN_GROUNDEDNESS = 20
COL_HUMAN_POLICY = 21
COL_HUMAN_ESCALATION = 22
COL_HUMAN_REVIEW_ACTION = 23
COL_HUMAN_NOTES = 24


def sync_ratings(workbook_path: Path = CANONICAL_WORKBOOK, csv_path: Path = AUDIT_CSV_PATH) -> bool:
    print("=" * 75)
    print("SYNCHRONIZING HUMAN AUDIT RATINGS TO CSV")
    print(f"Source: {workbook_path.name}")
    print(f"Target: {csv_path.name}")
    print("=" * 75)

    if not workbook_path.exists():
        print(f"❌ Error: Canonical workbook not found: {workbook_path}")
        return False

    if not csv_path.exists():
        print(f"❌ Error: Target CSV not found: {csv_path}")
        return False

    # 1. Load canonical workbook
    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    if "Judge-Human Audit" not in wb.sheetnames:
        print(f"❌ Error: Sheet 'Judge-Human Audit' missing in {workbook_path.name}")
        return False
    ws = wb["Judge-Human Audit"]

    # Read rows from workbook
    sheet_data = {}
    sheet_order = []
    for r in range(6, 56):
        mid = str(ws.cell(row=r, column=COL_MESSAGE_ID).value).strip()
        sheet_order.append(mid)
        sheet_data[mid] = {
            "status": str(ws.cell(row=r, column=COL_REVIEW_STATUS).value or "").strip(),
            "action": str(ws.cell(row=r, column=COL_HUMAN_REVIEW_ACTION).value or "").strip(),
            "human_correctness": ws.cell(row=r, column=COL_HUMAN_CORRECTNESS).value,
            "human_helpfulness": ws.cell(row=r, column=COL_HUMAN_HELPFULNESS).value,
            "human_groundedness": ws.cell(row=r, column=COL_HUMAN_GROUNDEDNESS).value,
            "human_policy": ws.cell(row=r, column=COL_HUMAN_POLICY).value,
            "human_escalation": ws.cell(row=r, column=COL_HUMAN_ESCALATION).value,
            "human_notes": str(ws.cell(row=r, column=COL_HUMAN_NOTES).value or "").strip(),
        }

    if len(sheet_order) != 50:
        print(f"❌ Error: Expected 50 rows in workbook, found {len(sheet_order)}")
        return False

    # 2. Read target CSV
    with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        csv_rows = list(reader)

    if len(csv_rows) != 50:
        print(f"❌ Error: Expected 50 rows in CSV, found {len(csv_rows)}")
        return False

    csv_mids = [str(r["message_id"]).strip() for r in csv_rows]
    if csv_mids != sheet_order:
        print("❌ Error: Message IDs in CSV do not match canonical workbook order.")
        return False

    # 3. Synchronize human review fields without altering machine fields
    synced_count = 0
    for r in csv_rows:
        mid = str(r["message_id"]).strip()
        data = sheet_data[mid]

        # Only sync if reviewed
        if data["status"] == "Reviewed" and data["action"] in ["approved", "edited"]:
            r["human_correctness"] = str(int(data["human_correctness"]))
            r["human_helpfulness"] = str(int(data["human_helpfulness"]))
            r["human_groundedness"] = str(int(data["human_groundedness"]))
            r["human_policy"] = str(int(data["human_policy"]))
            r["human_escalation"] = str(int(data["human_escalation"]))
            r["human_notes"] = data["human_notes"]
            synced_count += 1
        else:
            r["human_correctness"] = ""
            r["human_helpfulness"] = ""
            r["human_groundedness"] = ""
            r["human_policy"] = ""
            r["human_escalation"] = ""
            r["human_notes"] = ""

    # 4. Write back to CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)

    print(f"✓ Synchronized {synced_count} / 50 human audit ratings to {csv_path.name}.")
    print("✓ Machine columns remained 100% untouched.")
    print("=" * 75)
    return True


if __name__ == "__main__":
    success = sync_ratings()
    sys.exit(0 if success else 1)
