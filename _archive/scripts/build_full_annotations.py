"""
Step 2B: Full Golden Evaluation Set Assisted Annotation Engine
Generates:
  - eval/golden_review_assisted.xlsx (5 sheets, stylized, dashboard, conditional formatting)
  - eval/assistant_annotation_summary.md (comprehensive audit and breakdown)
"""

import csv
import json
import re
import os
import sys
from pathlib import Path
from collections import Counter, defaultdict
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Reconfigure stdout for UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CSV_PATH = Path("eval/golden_eval_set.csv")
BACKUP_PATH = Path("eval/golden_eval_set_pre_review_backup.csv")
THREADS_PATH = Path("data/processed/AmazonHelp_threads.jsonl")
EXCEL_PATH = Path("eval/golden_review_assisted.xlsx")
SUMMARY_PATH = Path("eval/assistant_annotation_summary.md")

LOCKED_INTENTS = [
    "Delivery Tracking & Status",
    "Delivery Problem & Logistics",
    "Returns, Replacements & Refunds",
    "Payment, Billing & Gift Cards",
    "Prime & Subscription Services",
    "Order & Checkout",
    "Account Access & Security",
    "Digital Services & Devices",
    "Seller & Product Quality",
    "General / Feedback / Other",
]

ALLOWED_LANGUAGES = ["en", "es", "ja", "de", "pt", "fr", "it", "other"]

ALLOWED_STATES = [
    "new_issue",
    "active_troubleshooting",
    "dm_handoff",
    "follow_up",
    "resolved_or_acknowledgment",
    "unclear",
]

# Ensure backup exists
if not BACKUP_PATH.exists():
    import shutil
    shutil.copyfile(CSV_PATH, BACKUP_PATH)
    print(f"Created pre-review backup at {BACKUP_PATH}")

# Read CSV rows
with open(CSV_PATH, "r", encoding="utf-8") as f:
    raw_rows = list(csv.DictReader(f))

# Index threads
target_convs = {r["conversation_id"] for r in raw_rows}
threads = {}
with open(THREADS_PATH, "r", encoding="utf-8") as f:
    for line in f:
        t = json.loads(line)
        cid = str(t.get("conversation_id"))
        if cid in target_convs:
            threads[cid] = t

print(f"Loaded {len(raw_rows)} rows and {len(threads)} conversation threads.")
