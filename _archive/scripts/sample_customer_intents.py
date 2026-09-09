"""
Script to sample ~150 customer messages (not brand replies) for a chosen brand,
formatted and grouped for visual scanning to define an intent taxonomy manually.

Usage:
    python scripts/sample_customer_intents.py --brand AmazonHelp --sample-size 150
"""

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Dict, List, Optional
import pandas as pd

# Add workspace root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.data_loader import DEFAULT_DATA_PATH, get_dataset_guidance
from src.text_cleaner import clean_tweet_text


def sample_customer_messages(
    brand: str,
    processed_csv: Optional[Path] = None,
    raw_csv: Path = DEFAULT_DATA_PATH,
    sample_size: int = 150,
    random_seed: int = 42,
    output_dir: Path = Path("reports"),
) -> List[Dict]:
    """
    Extract and sample customer messages from processed brand conversations
    or directly from raw dataset.
    """
    clean_brand = brand.lstrip("@").strip()
    random.seed(random_seed)

    candidate_records = []

    # 1. Check if processed CSV exists first
    expected_processed = Path(f"data/processed/{clean_brand}_conversations.csv")
    csv_to_use = processed_csv if (processed_csv and processed_csv.is_file()) else expected_processed

    if csv_to_use.is_file():
        print(f"[i] Loading from processed conversation file: {csv_to_use}")
        df = pd.read_csv(csv_to_use)
        # Filter to customer only
        customer_df = df[df["role"] == "customer"].copy()

        for _, row in customer_df.iterrows():
            txt = str(row.get("text_clean", "")).strip()
            if txt and len(txt) > 10:  # exclude empty or trivial noise
                candidate_records.append({
                    "tweet_id": str(row.get("tweet_id", "")),
                    "created_at": str(row.get("created_at", "")),
                    "turn_index": int(row.get("turn_index", 1)),
                    "total_turns": int(row.get("total_turns", 1)),
                    "is_multi_turn": bool(row.get("is_multi_turn", False)),
                    "text_clean": txt,
                    "text_raw": str(row.get("text_raw", "")),
                })
    elif raw_csv.is_file():
        print(f"[i] Processed file not found. Sampling directly from raw dataset: {raw_csv}")
        # Stream raw dataset and extract customer tweets for this brand
        brand_lower = clean_brand.lower()
        chunk_size = 150_000
        from src.data_loader import stream_twcs_dataset

        for chunk in stream_twcs_dataset(raw_csv, chunksize=chunk_size):
            # Customer tweets (inbound == True) mentioning brand
            inbound_chunk = chunk[chunk["inbound"] == True]
            for _, row in inbound_chunk.iterrows():
                raw_text = str(row.get("text", ""))
                if f"@{brand_lower}" in raw_text.lower():
                    clean_text = clean_tweet_text(raw_text, brand_handle=clean_brand)
                    if len(clean_text) > 10:
                        candidate_records.append({
                            "tweet_id": str(row.get("tweet_id", "")),
                            "created_at": str(row.get("created_at", "")),
                            "turn_index": 1,
                            "total_turns": 1,
                            "is_multi_turn": False,
                            "text_clean": clean_text,
                            "text_raw": raw_text,
                        })
            if len(candidate_records) >= sample_size * 10:
                break
    else:
        print(get_dataset_guidance(raw_csv))
        sys.exit(1)

    if not candidate_records:
        print(f"[!] No customer messages found for @{clean_brand}.")
        return []

    # Sample randomly without replacement
    actual_sample_size = min(sample_size, len(candidate_records))
    sampled = random.sample(candidate_records, actual_sample_size)

    # Organize / Group for easy visual scanning:
    # Group 1: Initial Problem Statements (Turn 1 / Root customer requests)
    # Group 2: Follow-up Messages (Turn >= 2 / Mid-dialogue customer responses)
    root_inquiries = [s for s in sampled if s.get("turn_index", 1) == 1]
    follow_up_inquiries = [s for s in sampled if s.get("turn_index", 1) > 1]

    # Further partition initial inquiries by length/complexity to aid scanning:
    # Short (< 60 chars), Medium (60 - 140 chars), Long / Detailed (> 140 chars)
    short_inquiries = [s for s in root_inquiries if len(s["text_clean"]) < 60]
    medium_inquiries = [s for s in root_inquiries if 60 <= len(s["text_clean"]) <= 140]
    long_inquiries = [s for s in root_inquiries if len(s["text_clean"]) > 140]

    # Save to Markdown Report
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{clean_brand}_intent_samples.md"

    md_lines = [
        f"# Customer Inquiries Dossier: @{clean_brand}",
        f"**Sample Size**: {actual_sample_size} customer messages | **Source**: Customer Support on Twitter",
        "",
        "> [!TIP]",
        "> **How to use this dossier**:",
        "> Read through these categorized customer messages to define your intent taxonomy.",
        "> Look for recurring issue types (e.g. *Order Tracking*, *Delivery Delay*, *Billing Dispute*, *Damaged Item*, *Cancellation*, *Account Access*).",
        "",
        "---",
        "",
        f"## Group 1: Initial Problem Statements - Long & Detailed ({len(long_inquiries)} messages)",
        "*Multi-sentence complaints, complex issues, and escalations.*",
        "",
    ]

    counter = 1
    for item in long_inquiries:
        turn_badge = " [Multi-turn Thread]" if item["is_multi_turn"] else ""
        md_lines.append(f"### [#{counter:03d}] Tweet ID: `{item['tweet_id']}`{turn_badge}")
        md_lines.append(f"> \"{item['text_clean']}\"")
        md_lines.append("")
        counter += 1

    md_lines.extend([
        "---",
        "",
        f"## Group 2: Initial Problem Statements - Medium Length ({len(medium_inquiries)} messages)",
        "*Standard single-issue customer inquiries.*",
        "",
    ])

    for item in medium_inquiries:
        turn_badge = " [Multi-turn Thread]" if item["is_multi_turn"] else ""
        md_lines.append(f"### [#{counter:03d}] Tweet ID: `{item['tweet_id']}`{turn_badge}")
        md_lines.append(f"> \"{item['text_clean']}\"")
        md_lines.append("")
        counter += 1

    md_lines.extend([
        "---",
        "",
        f"## Group 3: Initial Problem Statements - Short / Direct ({len(short_inquiries)} messages)",
        "*Quick status checks, one-liners, and concise questions.*",
        "",
    ])

    for item in short_inquiries:
        turn_badge = " [Multi-turn Thread]" if item["is_multi_turn"] else ""
        md_lines.append(f"### [#{counter:03d}] Tweet ID: `{item['tweet_id']}`{turn_badge}")
        md_lines.append(f"> \"{item['text_clean']}\"")
        md_lines.append("")
        counter += 1

    if follow_up_inquiries:
        md_lines.extend([
            "---",
            "",
            f"## Group 4: Customer Follow-up & Clarification Messages ({len(follow_up_inquiries)} messages)",
            "*Customer responses to agent replies (e.g., providing order info, confirming DM, asking for ETA).*",
            "",
        ])
        for item in follow_up_inquiries:
            md_lines.append(f"### [#{counter:03d}] Turn #{item['turn_index']} | Tweet ID: `{item['tweet_id']}`")
            md_lines.append(f"> \"{item['text_clean']}\"")
            md_lines.append("")
            counter += 1

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    # Also save structured JSON for downstream evaluation/taxonomy work
    json_path = Path("data/processed") / f"{clean_brand}_intent_samples.json"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sampled, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Sampled {actual_sample_size} customer messages for @{clean_brand}.")
    print(f"    - Saved visual Markdown dossier: {report_path.resolve()}")
    print(f"    - Saved structured JSON:        {json_path.resolve()}\n")

    # Print representative preview to terminal
    print("=" * 75)
    print(f"SAMPLE PREVIEW (First 15 of {actual_sample_size} messages for @{clean_brand}):")
    print("=" * 75)
    for i, item in enumerate(sampled[:15], start=1):
        context = f"[Turn {item.get('turn_index', 1)}]" if item.get("turn_index", 1) > 1 else "[Initial]"
        print(f"#{i:02d} {context} {item['text_clean']}")
        print("-" * 75)

    print(f"\nFull visual dossier with all {actual_sample_size} messages available in:")
    print(f"  --> {report_path.resolve()}")

    return sampled


def main():
    parser = argparse.ArgumentParser(description="Sample customer messages to define an intent taxonomy manually")
    parser.add_argument(
        "--brand",
        type=str,
        default="AmazonHelp",
        help="Brand handle (e.g., AmazonHelp, AppleSupport, SpotifyCares)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=150,
        help="Number of random customer messages to sample (default 150)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--processed-csv",
        type=str,
        default=None,
        help="Path to processed brand conversations CSV",
    )
    args = parser.parse_args()

    processed_path = Path(args.processed_csv) if args.processed_csv else None
    sample_customer_messages(
        brand=args.brand,
        processed_csv=processed_path,
        sample_size=args.sample_size,
        random_seed=args.seed,
    )


if __name__ == "__main__":
    main()
