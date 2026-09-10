"""
Step 1.5: AmazonHelp Data Validation Script

Rigorously verifies extracted AmazonHelp artifacts:
  - data/processed/AmazonHelp_tweets.csv
  - data/processed/AmazonHelp_conversations.csv
  - data/processed/AmazonHelp_threads.jsonl
  - reports/AmazonHelp_data_profile.md

Fails fast with non-zero exit code if:
  - extracted files are empty or missing
  - no AmazonHelp author ID is identified
  - suspiciously high text repetition appears
  - tweet IDs are duplicated
  - customer/support speaker assignment is inconsistent
  - conversation references are malformed
"""

import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, Set

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DIR = ROOT_DIR / "data" / "processed"
REPORTS_DIR = ROOT_DIR / "reports"

TWEETS_CSV = PROCESSED_DIR / "AmazonHelp_tweets.csv"
CONVERSATIONS_CSV = PROCESSED_DIR / "AmazonHelp_conversations.csv"
THREADS_JSONL = PROCESSED_DIR / "AmazonHelp_threads.jsonl"
PROFILE_REPORT = REPORTS_DIR / "AmazonHelp_data_profile.md"


def fail_validation(reason: str) -> None:
    print(f"\n❌ [VALIDATION ERROR] {reason}", file=sys.stderr)
    print("=" * 75, file=sys.stderr)
    print("FAILED: AmazonHelp extracted data did not pass validation.", file=sys.stderr)
    print("=" * 75, file=sys.stderr)
    sys.exit(1)


def validate_amazonhelp() -> None:
    print("=" * 75)
    print("STEP 1.5: VALIDATING AMAZONHELP EXTRACTED DATA & CONVERSATIONS")
    print("=" * 75)

    # 1. Verify existence and non-empty size of all files
    required_files = [TWEETS_CSV, CONVERSATIONS_CSV, THREADS_JSONL, PROFILE_REPORT]
    for p in required_files:
        if not p.exists():
            fail_validation(f"Required artifact does not exist: {p}")
        if not p.is_file():
            fail_validation(f"Required artifact path is not a file: {p}")
        size = p.stat().st_size
        if size == 0:
            fail_validation(f"Artifact is completely empty (0 bytes): {p}")
        print(f"✓ File exists and is non-empty: {p} ({size:,} bytes)")

    # 2. Validate AmazonHelp_tweets.csv schema, deduplication, speaker consistency
    print("\n--- Validating AmazonHelp_tweets.csv ---")
    expected_headers = [
        "tweet_id",
        "author_id",
        "inbound",
        "created_at",
        "text",
        "response_tweet_id",
        "in_response_to_tweet_id",
        "speaker",
        "conversation_id",
    ]

    total_tweets = 0
    amazon_tweets = 0
    customer_tweets = 0
    duplicate_tweet_ids = 0
    empty_texts = 0
    seen_tweet_ids: Set[str] = set()
    text_hashes: Set[int] = set()
    amazon_texts: Set[str] = set()
    speaker_inconsistencies = 0

    with open(TWEETS_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader)
        if header != expected_headers:
            fail_validation(f"Schema mismatch in {TWEETS_CSV}.\nExpected: {expected_headers}\nActual:   {header}")

        for row_idx, row in enumerate(reader, start=2):
            total_tweets += 1
            if len(row) < 9:
                fail_validation(f"Malformed row at line {row_idx} in {TWEETS_CSV}: {row}")

            tid, aid, inb, created, txt, resp_id, in_resp_id, spk, cid = row

            # Duplicate check
            if tid in seen_tweet_ids:
                duplicate_tweet_ids += 1
            else:
                seen_tweet_ids.add(tid)

            # Text completeness
            txt_clean = txt.strip()
            if not txt_clean:
                empty_texts += 1
            else:
                text_hashes.add(hash(txt_clean))

            # Speaker & Author consistency
            is_inb = inb.strip().lower() == "true"
            if aid == "AmazonHelp":
                amazon_tweets += 1
                if spk != "amazonhelp":
                    speaker_inconsistencies += 1
                if is_inb:
                    speaker_inconsistencies += 1
                if txt_clean:
                    amazon_texts.add(txt_clean)
            else:
                customer_tweets += 1
                if spk != "customer":
                    speaker_inconsistencies += 1
                if not is_inb:
                    speaker_inconsistencies += 1

            if not cid:
                fail_validation(f"Missing conversation_id for tweet_id {tid} at line {row_idx}")

    print(f"✓ Total tweets verified: {total_tweets:,}")
    print(f"  - Customer tweets:   {customer_tweets:,}")
    print(f"  - AmazonHelp tweets: {amazon_tweets:,}")

    if amazon_tweets == 0:
        fail_validation("No AmazonHelp author ID was identified in the extracted dataset.")
    if duplicate_tweet_ids > 0:
        fail_validation(f"Found {duplicate_tweet_ids:,} duplicate tweet IDs in {TWEETS_CSV}.")
    if speaker_inconsistencies > 0:
        fail_validation(f"Found {speaker_inconsistencies:,} speaker assignment inconsistencies.")
    if empty_texts > 0:
        fail_validation(f"Found {empty_texts:,} empty or null text rows in {TWEETS_CSV}.")

    # Text diversity / mock checks
    overall_diversity = len(text_hashes) / total_tweets if total_tweets > 0 else 0
    amazon_diversity = len(amazon_texts) / amazon_tweets if amazon_tweets > 0 else 0
    print(f"✓ Overall text diversity: {overall_diversity:.2%}")
    print(f"✓ AmazonHelp text diversity: {amazon_diversity:.2%}")

    if overall_diversity < 0.30:
        fail_validation(f"Suspiciously low overall text diversity ({overall_diversity:.2%}). Likely synthetic mock data.")
    if amazon_diversity < 0.30:
        fail_validation(f"Suspiciously low AmazonHelp text diversity ({amazon_diversity:.2%}). Likely repetitive mock data.")

    # 3. Validate AmazonHelp_conversations.csv
    print("\n--- Validating AmazonHelp_conversations.csv ---")
    conv_rows = 0
    with open(CONVERSATIONS_CSV, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        c_header = next(reader)
        for _ in reader:
            conv_rows += 1
    if conv_rows != total_tweets:
        fail_validation(f"Row count mismatch: {TWEETS_CSV} has {total_tweets:,} rows, but {CONVERSATIONS_CSV} has {conv_rows:,} rows.")
    print(f"✓ Conversations CSV verified: {conv_rows:,} total turn rows.")

    # 4. Validate AmazonHelp_threads.jsonl
    print("\n--- Validating AmazonHelp_threads.jsonl ---")
    threads_count = 0
    jsonl_turns_count = 0
    threads_with_support = 0
    threads_with_customer = 0

    with open(THREADS_JSONL, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            threads_count += 1
            try:
                obj = json.loads(line_str)
            except Exception as e:
                fail_validation(f"Malformed JSON on line {line_num} of {THREADS_JSONL}: {e}")

            cid = obj.get("conversation_id")
            turns = obj.get("turns")

            if not cid:
                fail_validation(f"Missing conversation_id on line {line_num} of {THREADS_JSONL}")
            if not isinstance(turns, list) or len(turns) == 0:
                fail_validation(f"Malformed or empty turns list for conversation '{cid}' on line {line_num}")

            jsonl_turns_count += len(turns)
            has_sup = any(t.get("speaker") == "amazonhelp" for t in turns)
            has_cust = any(t.get("speaker") == "customer" for t in turns)
            if has_sup:
                threads_with_support += 1
            if has_cust:
                threads_with_customer += 1

            # Validate each turn object
            for t in turns:
                if not t.get("tweet_id") or not t.get("speaker") or not t.get("text"):
                    fail_validation(f"Turn missing required fields in conversation '{cid}': {t}")

    print(f"✓ Total threads verified: {threads_count:,}")
    print(f"✓ Total turn objects in JSONL: {jsonl_turns_count:,}")
    if jsonl_turns_count != total_tweets:
        fail_validation(
            f"Total turns in JSONL ({jsonl_turns_count:,}) does not match tweets in CSV ({total_tweets:,})."
        )
    if threads_with_support == 0:
        fail_validation("No threads contained AmazonHelp turns.")

    print(f"✓ Threads containing AmazonHelp turns: {threads_with_support:,} ({threads_with_support/threads_count:.2%})")

    # 5. Check reports/AmazonHelp_data_profile.md contents
    print("\n--- Validating reports/AmazonHelp_data_profile.md ---")
    report_text = PROFILE_REPORT.read_text(encoding="utf-8")
    required_sections = [
        "## 1. Dataset Source & Provenance",
        "## 2. Extraction Methodology",
        "## 3. Identified AmazonHelp Author ID(s)",
        "## 4. Tweet Volume & Role Distribution",
        "## 5. Conversation Thread Statistics",
        "## 6. Response Coverage & Customer Reach",
        "## 7. Data Quality Audit",
        "## 8. 20 Random Real Customer Messages",
        "## 9. 20 Random Customer → AmazonHelp Response Examples",
        "## 10. 10 Random Multi-Turn Conversations",
    ]
    for section in required_sections:
        if section not in report_text:
            fail_validation(f"Report missing required section: '{section}'")
    print("✓ All 10 required report profile sections verified.")

    # 6. Final success
    print("\n" + "=" * 75)
    print("VALIDATION SUMMARY")
    print("=" * 75)
    print(f"Tweets CSV Rows:               {total_tweets:,}")
    print(f"Reconstructed Threads (JSONL): {threads_count:,}")
    print(f"Duplicate Tweet IDs:           {duplicate_tweet_ids}")
    print(f"Speaker Inconsistencies:       {speaker_inconsistencies}")
    print(f"Overall Text Diversity:        {overall_diversity:.2%}")
    print(f"AmazonHelp Text Diversity:     {amazon_diversity:.2%}")
    print("Status:                        PASSED")
    print("-" * 75)
    print("\nAMAZONHELP EXTRACTION VERIFIED\n")
    print("=" * 75)


if __name__ == "__main__":
    validate_amazonhelp()
