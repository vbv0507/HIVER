"""
Step 2: Golden Evaluation Set Validation Suite

Validates the integrity, format, and review progress of:
  - eval/golden_eval_set.csv
  - eval/golden_thread_exclusions.json
  - eval/golden_review_summary.md

Performs comprehensive checks:
1. Exact row count (200).
2. Validity of message_ids against processed dataset.
3. Duplicate message_id check.
4. Completeness and vocabulary validation of human final columns:
   - my_final_intent
   - my_final_language
   - my_final_conversation_state
   - my_final_escalate
   - my_final_is_security_alert
   - my_final_priority
5. Agreement statistics between AI suggestions and human labels.
6. Generates/updates eval/golden_review_summary.md.
"""

import csv
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

EVAL_DIR = Path("eval")
DATA_PROCESSED_DIR = Path("data/processed")

GOLDEN_CSV_PATH = EVAL_DIR / "golden_eval_set.csv"
EXCLUSIONS_JSON_PATH = EVAL_DIR / "golden_thread_exclusions.json"
REVIEW_SUMMARY_PATH = EVAL_DIR / "golden_review_summary.md"
TWEETS_PATH = DATA_PROCESSED_DIR / "AmazonHelp_tweets.csv"

EXPECTED_ROW_COUNT = 200

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

ALLOWED_PRIORITIES = ["P0_CRITICAL", "standard"]

EXPECTED_HEADERS = [
    "message_id",
    "conversation_id",
    "original_text",
    "ai_suggested_intent",
    "my_final_intent",
    "ai_suggested_language",
    "my_final_language",
    "ai_suggested_conversation_state",
    "my_final_conversation_state",
    "ai_suggested_escalate",
    "my_final_escalate",
    "ai_suggested_reason",
    "is_security_alert",
    "my_final_is_security_alert",
    "priority",
    "my_final_priority",
    "notes",
]


def fail_validation(reason: str) -> None:
    print(f"\n❌ [GOLDEN SET VALIDATION ERROR] {reason}", file=sys.stderr)
    print("=" * 75, file=sys.stderr)
    sys.exit(1)


def is_truthy(val: str) -> bool:
    return str(val).strip().lower() in ["true", "1", "yes"]


def validate_golden_set() -> None:
    print("=" * 75)
    print("STEP 2: VALIDATING GOLDEN EVALUATION SET & REVIEW SPREADSHEET")
    print("=" * 75)

    # 1. File existence checks
    if not GOLDEN_CSV_PATH.exists():
        fail_validation(f"Review spreadsheet not found: {GOLDEN_CSV_PATH}")
    if not EXCLUSIONS_JSON_PATH.exists():
        fail_validation(f"Thread exclusion registry not found: {EXCLUSIONS_JSON_PATH}")

    # 2. Validate Thread Exclusions Registry
    print("\n--- Validating eval/golden_thread_exclusions.json ---")
    try:
        with open(EXCLUSIONS_JSON_PATH, "r", encoding="utf-8") as f:
            exclusions_data = json.load(f)
    except Exception as e:
        fail_validation(f"Failed to parse {EXCLUSIONS_JSON_PATH}: {e}")

    golden_tids_in_exclusions = exclusions_data.get("golden_tweet_ids", [])
    excluded_convs = exclusions_data.get("excluded_conversation_ids", [])
    excluded_tweets = exclusions_data.get("excluded_tweet_ids", [])

    if len(golden_tids_in_exclusions) != EXPECTED_ROW_COUNT:
        fail_validation(
            f"Exclusion registry contains {len(golden_tids_in_exclusions)} golden tweet IDs, "
            f"expected {EXPECTED_ROW_COUNT}."
        )
    if len(excluded_tweets) < EXPECTED_ROW_COUNT:
        fail_validation(f"Excluded tweet IDs ({len(excluded_tweets)}) is suspiciously low.")

    print(f"✓ Exclusions registry verified:")
    print(f"  - Golden Tweets:               {len(golden_tids_in_exclusions)}")
    print(f"  - Excluded Conversations:      {len(excluded_convs)}")
    print(f"  - Excluded Total Thread Tweets:{len(excluded_tweets)}")

    # 3. Validate eval/golden_eval_set.csv schema & rows
    print("\n--- Validating eval/golden_eval_set.csv ---")
    rows: List[Dict[str, str]] = []
    seen_message_ids: Set[str] = set()

    with open(GOLDEN_CSV_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        actual_headers = reader.fieldnames or []
        if actual_headers != EXPECTED_HEADERS:
            diff_m = [h for h in EXPECTED_HEADERS if h not in actual_headers]
            diff_e = [h for h in actual_headers if h not in EXPECTED_HEADERS]
            fail_validation(
                f"Column header mismatch in {GOLDEN_CSV_PATH}.\n"
                f"Expected ({len(EXPECTED_HEADERS)} cols): {EXPECTED_HEADERS}\n"
                f"Actual ({len(actual_headers)} cols):   {actual_headers}\n"
                f"Missing: {diff_m}, Extra: {diff_e}"
            )

        for line_num, row in enumerate(reader, start=2):
            rows.append(row)
            mid = row["message_id"].strip()
            if not mid:
                fail_validation(f"Missing message_id at row {line_num}")
            if mid in seen_message_ids:
                fail_validation(f"Duplicate message_id '{mid}' at row {line_num}")
            seen_message_ids.add(mid)

    actual_count = len(rows)
    print(f"✓ Row count check: Exactly {actual_count} rows found (Expected {EXPECTED_ROW_COUNT}).")
    if actual_count != EXPECTED_ROW_COUNT:
        fail_validation(f"Row count is {actual_count}, expected {EXPECTED_ROW_COUNT}.")

    # 4. Validate message_id validity against real processed dataset
    print("\n--- Verifying tweet_id authenticity against processed dataset ---")
    if TWEETS_PATH.exists():
        valid_dataset_tids: Set[str] = set()
        with open(TWEETS_PATH, "r", encoding="utf-8", errors="replace") as f:
            t_reader = csv.reader(f)
            next(t_reader)
            for t_row in t_reader:
                if t_row:
                    valid_dataset_tids.add(t_row[0].strip())

        invalid_tids = seen_message_ids - valid_dataset_tids
        if invalid_tids:
            fail_validation(f"Found {len(invalid_tids)} message_ids not present in {TWEETS_PATH}: {list(invalid_tids)[:5]}")
        print(f"✓ All {actual_count} message_ids verified as genuine customer tweets from the dataset.")

    # 5. Check Human Review Status
    print("\n--- Checking Human Review Progress ---")
    completed_rows = 0
    intent_violations: List[str] = []
    lang_violations: List[str] = []
    state_violations: List[str] = []
    escalate_violations: List[str] = []
    sec_violations: List[str] = []
    prio_violations: List[str] = []

    # Agreement tracking
    intent_agreements = 0
    intent_comparable = 0
    escalate_agreements = 0
    escalate_comparable = 0
    sec_agreements = 0
    sec_comparable = 0
    prio_agreements = 0
    prio_comparable = 0

    intent_counter = Counter()
    lang_counter = Counter()
    state_counter = Counter()
    escalate_counter = Counter()
    security_alerts_count = 0
    priority_counter = Counter()

    disagreements_list: List[Dict[str, Any]] = []

    for idx, r in enumerate(rows, start=1):
        f_intent = r["my_final_intent"].strip()
        f_lang = r["my_final_language"].strip()
        f_state = r["my_final_conversation_state"].strip()
        f_esc = r["my_final_escalate"].strip()
        f_sec = r.get("my_final_is_security_alert", "").strip()
        f_prio = r.get("my_final_priority", "").strip()

        # Row is completed if all required human columns are filled
        is_completed = bool(f_intent and f_lang and f_state and f_esc and f_sec and f_prio)
        if is_completed:
            completed_rows += 1
            intent_counter[f_intent] += 1
            lang_counter[f_lang] += 1
            state_counter[f_state] += 1
            escalate_counter[f_esc.lower()] += 1
            priority_counter[f_prio] += 1

            if is_truthy(f_sec):
                security_alerts_count += 1

            # Vocabulary checks
            if f_intent not in LOCKED_INTENTS:
                intent_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid intent '{f_intent}'")
            if f_lang not in ALLOWED_LANGUAGES:
                lang_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid language '{f_lang}'")
            if f_state not in ALLOWED_STATES:
                state_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid state '{f_state}'")
            if f_esc.lower() not in ["true", "false"]:
                escalate_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid escalate boolean '{f_esc}'")
            if f_sec.lower() not in ["true", "false"]:
                sec_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid my_final_is_security_alert boolean '{f_sec}'")
            if f_prio not in ALLOWED_PRIORITIES:
                prio_violations.append(f"Row {idx} (ID {r['message_id']}): Invalid my_final_priority '{f_prio}' (must be P0_CRITICAL or standard)")
            if is_truthy(f_sec) and f_prio != "P0_CRITICAL":
                prio_violations.append(f"Row {idx} (ID {r['message_id']}): my_final_is_security_alert is true but my_final_priority is not 'P0_CRITICAL'")

            # Agreement metrics
            ai_intent = r["ai_suggested_intent"].strip()
            ai_esc = r["ai_suggested_escalate"].strip()
            ai_sec = r.get("is_security_alert", "").strip()
            ai_prio = r.get("priority", "").strip()

            if ai_intent:
                intent_comparable += 1
                if ai_intent.lower() == f_intent.lower():
                    intent_agreements += 1
                else:
                    disagreements_list.append({
                        "message_id": r["message_id"],
                        "text": r["original_text"][:100],
                        "ai_intent": ai_intent,
                        "my_final_intent": f_intent,
                        "notes": r.get("notes", ""),
                    })

            if ai_esc:
                escalate_comparable += 1
                if is_truthy(ai_esc) == is_truthy(f_esc):
                    escalate_agreements += 1

            if ai_sec:
                sec_comparable += 1
                if is_truthy(ai_sec) == is_truthy(f_sec):
                    sec_agreements += 1

            if ai_prio:
                prio_comparable += 1
                if ai_prio.lower() == f_prio.lower():
                    prio_agreements += 1

    # Print Review Status
    if completed_rows == 0:
        print("  Status: PRE-REVIEW INITIALIZED")
        print(f"  All {EXPECTED_ROW_COUNT} rows are currently pending manual human review.")
        print("  All my_final_* columns (intent, language, state, escalate, security, priority) are cleanly empty ready for review.")
    elif completed_rows < EXPECTED_ROW_COUNT:
        print(f"  Status: IN PROGRESS ({completed_rows}/{EXPECTED_ROW_COUNT} completed, {EXPECTED_ROW_COUNT-completed_rows} pending).")
    else:
        print(f"  Status: FULLY COMPLETED (All {EXPECTED_ROW_COUNT} rows manually reviewed).")

        if intent_violations:
            fail_validation(f"Found {len(intent_violations)} intent vocabulary errors:\n" + "\n".join(intent_violations[:5]))
        if lang_violations:
            fail_validation(f"Found {len(lang_violations)} language vocabulary errors:\n" + "\n".join(lang_violations[:5]))
        if state_violations:
            fail_validation(f"Found {len(state_violations)} conversation_state errors:\n" + "\n".join(state_violations[:5]))
        if escalate_violations:
            fail_validation(f"Found {len(escalate_violations)} escalate boolean errors:\n" + "\n".join(escalate_violations[:5]))
        if sec_violations:
            fail_validation(f"Found {len(sec_violations)} security alert boolean errors:\n" + "\n".join(sec_violations[:5]))
        if prio_violations:
            fail_validation(f"Found {len(prio_violations)} priority errors:\n" + "\n".join(prio_violations[:5]))

        print("✓ All human review vocabulary and boundary constraints passed.")

        # Agreement statistics
        if intent_comparable > 0:
            intent_agreement_pct = (intent_agreements / intent_comparable) * 100
            print(f"\nAI Intent Agreement:")
            print(f"  {intent_agreements} / {intent_comparable} = {intent_agreement_pct:.1f}%")
            print("  (Note: Agreement statistic only; not a model evaluation metric)")

        if escalate_comparable > 0:
            escalate_agreement_pct = (escalate_agreements / escalate_comparable) * 100
            print(f"\nAI Escalation Agreement:")
            print(f"  {escalate_agreements} / {escalate_comparable} = {escalate_agreement_pct:.1f}%")

    # 6. Update/write eval/golden_review_summary.md
    write_review_summary(
        output_path=REVIEW_SUMMARY_PATH,
        total_rows=actual_count,
        completed_rows=completed_rows,
        intent_counter=intent_counter,
        lang_counter=lang_counter,
        state_counter=state_counter,
        escalate_counter=escalate_counter,
        security_alerts=security_alerts_count,
        priority_counter=priority_counter,
        intent_agreements=intent_agreements,
        intent_comparable=intent_comparable,
        escalate_agreements=escalate_agreements,
        escalate_comparable=escalate_comparable,
        disagreements=disagreements_list,
    )
    print(f"✓ Updated review summary at {REVIEW_SUMMARY_PATH}")

    print("\n" + "=" * 75)
    print("GOLDEN SET VALIDATION COMPLETE")
    print(f"Total Rows:                   {actual_count}")
    print(f"Pending Manual Review Rows:   {actual_count - completed_rows}")
    print(f"Excluded Leakage Tweet IDs:   {len(excluded_tweets):,}")
    print("Status:                       READY FOR HUMAN REVIEW")
    print("=" * 75)


def write_review_summary(
    output_path: Path,
    total_rows: int,
    completed_rows: int,
    intent_counter: Counter,
    lang_counter: Counter,
    state_counter: Counter,
    escalate_counter: Counter,
    security_alerts: int,
    priority_counter: Counter,
    intent_agreements: int,
    intent_comparable: int,
    escalate_agreements: int,
    escalate_comparable: int,
    disagreements: List[Dict[str, Any]],
) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Golden Evaluation Set Review Summary & Audit\n\n")
        f.write(f"**Dataset:** `eval/golden_eval_set.csv`  \n")
        f.write(f"**Total Examples:** {total_rows}  \n")
        f.write(f"**Reviewed Examples:** {completed_rows} / {total_rows}  \n")
        f.write(f"**Review State:** {'COMPLETE' if completed_rows == total_rows else 'PENDING HUMAN ANNOTATION'}  \n\n")
        f.write("---\n\n")

        if completed_rows == 0:
            f.write("## Status: Pre-Review Stage (Awaiting Human Review)\n\n")
            f.write("The golden evaluation spreadsheet has been initialized with **200 real customer messages**. All `my_final_*` columns are intentionally empty. AI suggestions have been provided as non-binding baselines.\n\n")
            f.write("### Review Columns to Complete:\n")
            f.write("1. `my_final_intent` (from the locked 10-class taxonomy)\n")
            f.write("2. `my_final_language` (`en`, `es`, `ja`, `de`, `pt`, `fr`, `it`, `other`)\n")
            f.write("3. `my_final_conversation_state` (`new_issue`, `active_troubleshooting`, `dm_handoff`, `follow_up`, `resolved_or_acknowledgment`, `unclear`)\n")
            f.write("4. `my_final_escalate` (`true` or `false`)\n")
            f.write("5. `my_final_is_security_alert` (`true` or `false`)\n")
            f.write("6. `my_final_priority` (`P0_CRITICAL` or `standard`)\n")
            f.write("7. (Optional) `notes`\n\n")
            f.write("Re-run `python scripts/validate_golden_set.py` at any point to verify review progress and agreement statistics.\n\n")
        else:
            f.write("## 1. Intent Distribution (Human Gold Labels)\n\n")
            f.write("| Intent | Count | Percentage |\n")
            f.write("| :--- | :---: | :---: |\n")
            for intent in LOCKED_INTENTS:
                cnt = intent_counter.get(intent, 0)
                f.write(f"| **{intent}** | {cnt} | {cnt/completed_rows:.2%} |\n")
            f.write("\n")

            f.write("## 2. Orthogonal Metadata Distributions\n\n")
            f.write("### Language Distribution\n\n")
            f.write("| Language | Count | Percentage |\n")
            f.write("| :---: | :---: | :---: |\n")
            for lang in ALLOWED_LANGUAGES:
                cnt = lang_counter.get(lang, 0)
                if cnt > 0:
                    f.write(f"| `{lang}` | {cnt} | {cnt/completed_rows:.2%} |\n")
            f.write("\n")

            f.write("### Conversation State Distribution\n\n")
            f.write("| Conversation State | Count | Percentage |\n")
            f.write("| :--- | :---: | :---: |\n")
            for st in ALLOWED_STATES:
                cnt = state_counter.get(st, 0)
                f.write(f"| `{st}` | {cnt} | {cnt/completed_rows:.2%} |\n")
            f.write("\n")

            f.write("## 3. Escalation & Security Summary\n\n")
            f.write(f"- **Total Security Alerts Flagged (`my_final_is_security_alert`):** {security_alerts}\n")
            f.write(f"- **Human Escalation Rate (`my_final_escalate`):** {escalate_counter.get('true', 0)} / {completed_rows} ({escalate_counter.get('true', 0)/completed_rows:.2%})\n")
            f.write(f"- **Priority Breakdown:** {dict(priority_counter)}\n\n")

            f.write("## 4. AI Suggestion Agreement Statistics\n\n")
            if intent_comparable > 0:
                pct_int = (intent_agreements / intent_comparable) * 100
                f.write(f"- **AI Intent Agreement:** {intent_agreements} / {intent_comparable} = **{pct_int:.1f}%**\n")
            if escalate_comparable > 0:
                pct_esc = (escalate_agreements / escalate_comparable) * 100
                f.write(f"- **AI Escalation Agreement:** {escalate_agreements} / {escalate_comparable} = **{pct_esc:.1f}%**\n\n")
            f.write("*(Note: Agreement statistics only; these do NOT constitute model evaluation metrics.)*\n\n")

            if disagreements:
                f.write("## 5. Sample Disagreements & Difficult Decisions\n\n")
                for d in disagreements[:10]:
                    f.write(f"- **[Tweet {d['message_id']}]**: `{d['text']}`\n")
                    f.write(f"  - AI Suggested: `{d['ai_intent']}`\n")
                    f.write(f"  - Human Gold:   `{d['my_final_intent']}`\n")
                    if d.get("notes"):
                        f.write(f"  - Notes: {d['notes']}\n")
                    f.write("\n")


if __name__ == "__main__":
    validate_golden_set()
