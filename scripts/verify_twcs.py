"""
Step 1: Raw TWCS Dataset Verification Script

Strictly validates data/raw/twcs.csv against the Kaggle Customer Support on Twitter specification.
Never uses synthetic/mock fallback data.
Never silently substitutes another dataset.
Fails fast with non-zero exit status if verification fails.
Prints 'REAL TWCS DATASET VERIFIED' upon full success.
"""

import csv
import os
import sys
import time
from pathlib import Path
from typing import Dict, Set

# Ensure terminal encoding compatibility on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_DATA_PATH = ROOT_DIR / "data" / "raw" / "twcs.csv"

EXPECTED_COLUMNS = [
    "tweet_id",
    "author_id",
    "inbound",
    "created_at",
    "text",
    "response_tweet_id",
    "in_response_to_tweet_id",
]

# Reasonable sanity bounds (used as sanity checks, not arbitrary proofs)
SANITY_MIN_ROWS = 1_000_000
SANITY_MIN_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MB
SANITY_MIN_DIVERSITY_RATIO = 0.30  # At least 30% distinct text


def fail_verification(reason: str) -> None:
    """Print error explanation and exit with a non-zero exit code."""
    print("\n" + "!" * 75, file=sys.stderr)
    print("❌ TWCS DATASET VALIDATION FAILED", file=sys.stderr)
    print("!" * 75, file=sys.stderr)
    print(f"Reason: {reason}\n", file=sys.stderr)
    print("IMPORTANT RULES ENFORCED:", file=sys.stderr)
    print(" - data/raw/twcs.csv must be the genuine Kaggle TWCS dataset.", file=sys.stderr)
    print(" - Do NOT use twcs_mock.csv or any synthetic data.", file=sys.stderr)
    print(" - Do NOT fall back to sample or mock generators.", file=sys.stderr)
    print(" - Download from: https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter", file=sys.stderr)
    print("!" * 75 + "\n", file=sys.stderr)
    sys.exit(1)


def verify_twcs(filepath: Path = RAW_DATA_PATH) -> Dict[str, object]:
    t_start = time.time()
    print("=" * 75)
    print(f"STEP 1: VERIFYING REAL TWCS DATASET: {filepath}")
    print("=" * 75)

    # 1. Verify file exists
    if not filepath.exists():
        fail_verification(f"File not found: '{filepath}'. Please place the real Kaggle twcs.csv here.")
    if not filepath.is_file():
        fail_verification(f"Path exists but is not a regular file: '{filepath}'.")

    file_size_bytes = filepath.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    print(f"✓ File exists: {filepath}")
    print(f"✓ File size: {file_size_bytes:,} bytes ({file_size_mb:.2f} MB)")

    # Basic file size sanity check
    if file_size_bytes < SANITY_MIN_FILE_SIZE_BYTES:
        fail_verification(
            f"File size ({file_size_mb:.2f} MB) is unexpectedly small. "
            f"The real TWCS dataset is ~500 MB. Detected mock or truncated file."
        )

    # 2 & 3. Validate CSV format and exact columns
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = next(reader)
    except Exception as e:
        fail_verification(f"Failed to read CSV header or parse CSV structure: {e}")

    print(f"Found columns: {header}")
    if header != EXPECTED_COLUMNS:
        diff_missing = [c for c in EXPECTED_COLUMNS if c not in header]
        diff_extra = [c for c in header if c not in EXPECTED_COLUMNS]
        fail_verification(
            f"CSV columns do not match expected TWCS schema.\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual:   {header}\n"
            f"Missing columns: {diff_missing}\n"
            f"Extra columns:   {diff_extra}"
        )
    print("✓ Schema validation passed: Exactly matches all 7 TWCS columns.")

    # 4 & 5. Count rows efficiently without loading entire dataset into memory
    print("\nStreaming rows to compute dataset statistics (memory-safe streaming)...")

    total_rows = 0
    inbound_count = 0
    outbound_count = 0
    missing_text_count = 0
    duplicate_tweet_ids = 0
    
    seen_tweet_ids: Set[str] = set()
    unique_authors: Set[str] = set()
    unique_text_hashes: Set[int] = set()
    
    # AmazonHelp specific tracking
    amazon_help_rows = 0
    amazon_help_texts: Set[str] = set()

    progress_step = 500_000

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        # Skip header
        next(reader)
        
        for row in reader:
            total_rows += 1
            if len(row) < 7:
                # Row format anomaly
                continue

            tid, aid, inb, created, txt, resp_id, in_resp_id = (
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                row[5],
                row[6],
            )

            # Check duplicate tweet_id
            if tid in seen_tweet_ids:
                duplicate_tweet_ids += 1
            else:
                seen_tweet_ids.add(tid)

            # Track unique authors
            unique_authors.add(aid)

            # Inbound vs Outbound
            is_inbound = inb.strip().lower() == "true"
            if is_inbound:
                inbound_count += 1
            else:
                outbound_count += 1

            # Missing or empty text
            txt_clean = txt.strip()
            if not txt_clean:
                missing_text_count += 1
            else:
                unique_text_hashes.add(hash(txt_clean))

            # AmazonHelp tracking
            if aid.strip() == "AmazonHelp":
                amazon_help_rows += 1
                if txt_clean:
                    amazon_help_texts.add(txt_clean)

            if total_rows % progress_step == 0:
                print(f"  Processed {total_rows:,} rows...")

    elapsed = time.time() - t_start
    print(f"✓ Streaming completed: {total_rows:,} rows processed in {elapsed:.2f} seconds.")

    unique_texts_count = len(unique_text_hashes)
    unique_amazon_texts_count = len(amazon_help_texts)
    overall_text_diversity = (unique_texts_count / total_rows) if total_rows > 0 else 0
    amazon_text_diversity = (unique_amazon_texts_count / amazon_help_rows) if amazon_help_rows > 0 else 0

    # 6. Inspect AmazonHelp natural diversity
    amazon_is_diverse = amazon_text_diversity > SANITY_MIN_DIVERSITY_RATIO
    diversity_assessment = (
        "Naturally diverse (individualized customer service replies with handles/links/reps)"
        if amazon_is_diverse
        else "Suspiciously templated / repetitive (characteristic of mock data)"
    )

    # 7. Basic synthetic-data sanity checks
    print("\nRunning synthetic-data sanity checks:")

    # Check: Dataset size
    if total_rows < SANITY_MIN_ROWS:
        fail_verification(
            f"Row count ({total_rows:,}) is below the sanity threshold ({SANITY_MIN_ROWS:,}). "
            f"Synthetic or truncated dataset detected."
        )
    print(f"✓ Row count sanity check passed: {total_rows:,} rows (expected ~2.8M).")

    # Check: Text repetition
    if overall_text_diversity < SANITY_MIN_DIVERSITY_RATIO:
        fail_verification(
            f"Extremely high exact-text repetition detected: "
            f"Only {unique_texts_count:,} unique texts out of {total_rows:,} "
            f"({overall_text_diversity:.2%}). Likely synthetic template generation."
        )
    print(f"✓ Overall text diversity sanity check passed: {overall_text_diversity:.2%} unique texts.")

    # Check: AmazonHelp presence and diversity
    if amazon_help_rows == 0:
        fail_verification("No AmazonHelp tweets found. The TWCS dataset must contain AmazonHelp.")
    if not amazon_is_diverse:
        fail_verification(
            f"AmazonHelp text diversity ({amazon_text_diversity:.2%}) is suspiciously low. "
            f"Found only {unique_amazon_texts_count:,} unique texts for {amazon_help_rows:,} tweets."
        )
    print(f"✓ AmazonHelp diversity sanity check passed: {amazon_text_diversity:.2%} unique texts.")

    # Check: Missing text
    if missing_text_count > (total_rows * 0.05):
        fail_verification(f"Excessive missing text rows: {missing_text_count:,} ({missing_text_count/total_rows:.2%}).")
    print(f"✓ Text completeness passed: {missing_text_count:,} missing text entries.")

    # 8. Formatted Report
    print("\n" + "=" * 75)
    print("TWCS DATASET VERIFICATION REPORT (STEP 1)")
    print("=" * 75)
    print(f"{'Metric':<35} | {'Value':<35}")
    print("-" * 75)
    print(f"{'Total Rows':<35} | {total_rows:<35,}")
    print(f"{'File Size':<35} | {file_size_bytes:<35,} bytes ({file_size_mb:.2f} MB)")
    print(f"{'Inbound Tweets (Customer)':<35} | {inbound_count:<35,} ({inbound_count/total_rows:.2%})")
    print(f"{'Outbound Tweets (Brand)':<35} | {outbound_count:<35,} ({outbound_count/total_rows:.2%})")
    print(f"{'Unique Authors Count':<35} | {len(unique_authors):<35,}")
    print(f"{'Missing Text Count':<35} | {missing_text_count:<35,}")
    print(f"{'Duplicate Tweet IDs Count':<35} | {duplicate_tweet_ids:<35,}")
    print(f"{'Unique Text Count':<35} | {unique_texts_count:<35,} ({overall_text_diversity:.2%})")
    print(f"{'AmazonHelp Rows':<35} | {amazon_help_rows:<35,}")
    print(f"{'AmazonHelp Unique Texts':<35} | {unique_amazon_texts_count:<35,}")
    print(f"{'AmazonHelp Diversity Ratio':<35} | {amazon_text_diversity:<35.2%}")
    print(f"{'AmazonHelp Pattern':<35} | {diversity_assessment:<35}")
    print(f"{'Synthetic Fallback Used':<35} | {'NO (Genuine Kaggle TWCS Dataset)':<35}")
    print("-" * 75)
    print("\nREAL TWCS DATASET VERIFIED\n")
    print("=" * 75)

    return {
        "total_rows": total_rows,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": file_size_mb,
        "inbound_count": inbound_count,
        "outbound_count": outbound_count,
        "unique_authors": len(unique_authors),
        "missing_text_count": missing_text_count,
        "duplicate_tweet_ids": duplicate_tweet_ids,
        "unique_texts_count": unique_texts_count,
        "overall_text_diversity": overall_text_diversity,
        "amazon_help_rows": amazon_help_rows,
        "unique_amazon_texts_count": unique_amazon_texts_count,
        "amazon_text_diversity": amazon_text_diversity,
        "amazon_assessment": diversity_assessment,
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    verify_twcs()
