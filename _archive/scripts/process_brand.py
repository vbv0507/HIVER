"""
Script to filter dataset for a chosen brand, reconstruct multi-turn conversations,
apply tone-preserving text cleaning, and save processed artifacts.

Usage:
    python scripts/process_brand.py --brand AmazonHelp
    python scripts/process_brand.py --brand AppleSupport --data-path data/raw/twcs.csv
"""

import argparse
import json
from pathlib import Path
import sys
from typing import Optional
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

from src.data_loader import (
    DEFAULT_DATA_PATH,
    check_dataset_exists,
    get_brand_tweets,
    get_dataset_guidance,
)
from src.thread_builder import reconstruct_threads


def process_brand_dataset(
    brand: str,
    data_path: Path = DEFAULT_DATA_PATH,
    output_dir: Path = Path("data/processed"),
    max_conversations: Optional[int] = None,
):
    """
    Filter, reconstruct, clean, and persist conversational threads for a chosen brand.
    """
    clean_brand = brand.lstrip("@").strip()
    print(f"\n{'='*70}")
    print(f"PROCESSING CONVERSATIONS FOR BRAND: @{clean_brand}")
    print(f"{'='*70}")

    if not data_path.is_file():
        print(get_dataset_guidance(data_path))
        sys.exit(1)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Filter tweets for brand
    print(f"\n[1/4] Filtering dataset for brand @{clean_brand}...")
    brand_df = get_brand_tweets(clean_brand, filepath=data_path)

    if brand_df.empty:
        print(f"[!] No tweets found for brand '{clean_brand}'. Check spelling (e.g. AmazonHelp, AppleSupport, SpotifyCares).")
        return

    print(f"[OK] Found {len(brand_df):,} tweets related to @{clean_brand}.")

    # Step 2: Reconstruct multi-turn threads & clean text
    print(f"\n[2/4] Reconstructing multi-turn conversation threads & cleaning text...")
    threads = reconstruct_threads(brand_df, brand_handle=clean_brand)

    if max_conversations:
        threads = threads[:max_conversations]

    total_threads = len(threads)
    multi_turn_threads = [t for t in threads if t["is_multi_turn"]]
    total_turns = sum(t["total_turns"] for t in threads)
    avg_depth = (total_turns / total_threads) if total_threads > 0 else 0

    print(f"[OK] Reconstructed {total_threads:,} conversation threads.")
    print(f"    - Multi-turn threads (>=3 turns): {len(multi_turn_threads):,} ({(len(multi_turn_threads)/total_threads*100):.1f}%)")
    print(f"    - Average thread depth: {avg_depth:.2f} turns")

    # Step 3: Save JSONL format (rich hierarchical format for LLM pipelines)
    jsonl_filename = output_dir / f"{clean_brand}_threads.jsonl"
    print(f"\n[3/4] Saving structured threads to JSONL: {jsonl_filename}...")
    with open(jsonl_filename, "w", encoding="utf-8") as f:
        for t in threads:
            f.write(json.dumps(t, ensure_ascii=False) + "\n")

    # Step 4: Save flattened CSV format (easy for pandas/tabular inspection)
    csv_filename = output_dir / f"{clean_brand}_conversations.csv"
    print(f"[4/4] Saving flattened turns to CSV: {csv_filename}...")
    flat_rows = []
    for t in threads:
        conv_id = t["conversation_id"]
        is_multi = t["is_multi_turn"]
        total_t = t["total_turns"]
        for turn in t["turns"]:
            flat_rows.append({
                "conversation_id": conv_id,
                "brand": clean_brand,
                "total_turns": total_t,
                "is_multi_turn": is_multi,
                "turn_index": turn["turn_index"],
                "role": turn["role"],
                "author_id": turn["author_id"],
                "inbound": turn["inbound"],
                "created_at": turn["created_at"],
                "in_response_to_tweet_id": turn["in_response_to_tweet_id"],
                "tweet_id": turn["tweet_id"],
                "text_clean": turn["text_clean"],
                "text_raw": turn["text_raw"],
            })

    flat_df = pd.DataFrame(flat_rows)
    flat_df.to_csv(csv_filename, index=False, encoding="utf-8")

    print(f"\n{'='*70}")
    print(f"SUCCESS: Processed data saved successfully!")
    print(f"  - Threads JSONL: {jsonl_filename.resolve()}")
    print(f"  - Turns CSV:     {csv_filename.resolve()}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Filter and process conversations for a specific brand")
    parser.add_argument(
        "--brand",
        type=str,
        default="AmazonHelp",
        help="Brand handle (e.g., AmazonHelp, AppleSupport, SpotifyCares, Delta)",
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to twcs.csv dataset",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Directory to save processed files",
    )
    parser.add_argument(
        "--max-conversations",
        type=int,
        default=None,
        help="Limit number of conversations to process (optional)",
    )
    args = parser.parse_args()

    process_brand_dataset(
        brand=args.brand,
        data_path=Path(args.data_path),
        output_dir=Path(args.output_dir),
        max_conversations=args.max_conversations,
    )


if __name__ == "__main__":
    main()
