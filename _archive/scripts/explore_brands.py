"""
Script to explore the Kaggle twcs.csv dataset, identify top 10 brands by volume,
compute average thread depth, extract representative customer messages,
and generate a clean markdown summary report.

Usage:
    python scripts/explore_brands.py
    python scripts/explore_brands.py --mock   # Run on synthetic benchmark if twcs.csv not yet placed
"""

import argparse
from collections import Counter, defaultdict
from pathlib import Path
import sys
from typing import Dict, List
import pandas as pd
from tabulate import tabulate

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
    get_dataset_guidance,
    stream_twcs_dataset,
)
from src.mock_data import generate_mock_twcs_dataset
from src.thread_builder import reconstruct_threads


def explore_dataset(csv_path: Path, sample_threads_per_brand: int = 500) -> Dict[str, any]:
    """
    Stream twcs.csv to find top 10 brands, thread length metrics, and sample messages.
    """
    print(f"\n[1/3] Scanning dataset at: {csv_path}...")
    brand_outbound_counts = Counter()
    brand_mentions = Counter()

    # Pass 1: Aggregate brand volume
    chunk_count = 0
    total_rows = 0
    for chunk in stream_twcs_dataset(csv_path, chunksize=150_000, usecols=["tweet_id", "author_id", "inbound", "text"]):
        chunk_count += 1
        total_rows += len(chunk)
        print(f"  Processed {total_rows:,} rows across {chunk_count} chunks...", end="\r", flush=True)

        # Brand accounts are inbound == False or non-numeric author_ids
        outbound = chunk[chunk["inbound"] == False]
        for author in outbound["author_id"].dropna():
            # Filter out purely numeric IDs
            if not str(author).isdigit():
                brand_outbound_counts[str(author)] += 1

    print(f"\n[OK] Scanned {total_rows:,} total tweets.")

    top_10_brands = [b for b, _ in brand_outbound_counts.most_common(10)]
    top_10_set = set(top_10_brands)

    print(f"\n[2/3] Top 10 Brands identified: {', '.join(top_10_brands)}")
    print(f"Collecting conversation threads and samples for top 10 brands...")

    # Pass 2: Collect sample tweets for top 10 to compute thread depth and extract sample messages
    brand_tweet_buckets: Dict[str, List[Dict]] = defaultdict(list)
    brand_samples_raw: Dict[str, List[str]] = defaultdict(list)
    brand_customer_inbound_counts = Counter()

    for chunk in stream_twcs_dataset(csv_path, chunksize=150_000):
        # Sample tweets for thread building (capped to prevent memory explosion)
        for _, row in chunk.iterrows():
            author = str(row.get("author_id", ""))
            inbound = bool(row.get("inbound", False))
            text = str(row.get("text", ""))

            # Outbound brand tweet
            if author in top_10_set:
                if len(brand_tweet_buckets[author]) < sample_threads_per_brand * 4:
                    brand_tweet_buckets[author].append(row.to_dict())

            # Inbound customer tweet mentioning brand
            if inbound:
                is_root = pd.isna(row.get("in_response_to_tweet_id"))
                for b in top_10_brands:
                    if f"@{b.lower()}" in text.lower():
                        brand_customer_inbound_counts[b] += 1
                        # Prioritize root problem statements for the 5 sample messages
                        if is_root and len(brand_samples_raw[b]) < 5 and text not in brand_samples_raw[b]:
                            brand_samples_raw[b].append(text)
                        elif len(brand_samples_raw[b]) < 5 and text not in brand_samples_raw[b] and not is_root:
                            # Keep as candidate if not enough root messages
                            brand_samples_raw[b].append(text)
                        if len(brand_tweet_buckets[b]) < sample_threads_per_brand * 4:
                            brand_tweet_buckets[b].append(row.to_dict())

    # Pass 3: Reconstruct sample threads to compute average thread depth
    print(f"\n[3/3] Reconstructing conversation threads and computing metrics...")
    brand_stats = []

    for brand in top_10_brands:
        tweets = brand_tweet_buckets.get(brand, [])
        avg_depth = 1.0
        multi_turn_pct = 0.0
        sample_threads = []

        if tweets:
            b_df = pd.DataFrame(tweets).drop_duplicates(subset=["tweet_id"])
            threads = reconstruct_threads(b_df, brand_handle=brand)
            if threads:
                depths = [t["total_turns"] for t in threads]
                multi_turns = [t for t in threads if t["is_multi_turn"]]
                avg_depth = sum(depths) / len(depths)
                multi_turn_pct = (len(multi_turns) / len(threads)) * 100.0

        outbound_vol = brand_outbound_counts[brand]
        inbound_vol = brand_customer_inbound_counts[brand]
        total_est_vol = outbound_vol + inbound_vol

        # Ensure we have 5 sample raw messages
        samples = brand_samples_raw.get(brand, [])
        if len(samples) < 5:
            # Fallback to any tweet text from that brand's bucket
            for t in tweets:
                txt = str(t.get("text", ""))
                if txt and txt not in samples:
                    samples.append(txt)
                if len(samples) >= 5:
                    break

        brand_stats.append({
            "brand": brand,
            "brand_outbound_tweets": outbound_vol,
            "customer_inbound_tweets": inbound_vol,
            "total_estimated_volume": total_est_vol,
            "avg_thread_length": round(avg_depth, 2),
            "multi_turn_percentage": f"{multi_turn_pct:.1f}%",
            "sample_raw_messages": samples[:5],
        })

    return {
        "total_tweets": total_rows,
        "top_10_stats": brand_stats,
    }


def format_markdown_report(results: Dict[str, any]) -> str:
    """Generate clean Markdown documentation for the top 10 brands."""
    stats = results["top_10_stats"]
    total = results["total_tweets"]

    # Table summary
    table_rows = []
    for s in stats:
        table_rows.append([
            f"**@{s['brand']}**",
            f"{s['brand_outbound_tweets']:,}",
            f"{s['customer_inbound_tweets']:,}",
            f"{s['total_estimated_volume']:,}",
            f"{s['avg_thread_length']}",
            s["multi_turn_percentage"],
        ])

    table_headers = [
        "Brand Handle",
        "Brand Replies",
        "Customer Inbound",
        "Total Est. Vol",
        "Avg Thread Depth",
        "Multi-turn %",
    ]
    md_table = tabulate(table_rows, headers=table_headers, tablefmt="github")

    lines = [
        "# Customer Support Dataset: Top 10 Brands Exploration Report",
        "",
        f"- **Dataset Scanned**: {total:,} tweets",
        "- **Purpose**: Select the best candidate brand for training/evaluating the customer support agent.",
        "",
        "## 1. Top 10 Brands Summary Table",
        "",
        md_table,
        "",
        "---",
        "",
        "## 2. Brand Profiles & Sample Raw Customer Messages",
        "",
    ]

    for rank, s in enumerate(stats, start=1):
        lines.append(f"### {rank}. @{s['brand']}")
        lines.append(f"- **Brand Responses**: {s['brand_outbound_tweets']:,}")
        lines.append(f"- **Avg Thread Length**: {s['avg_thread_length']} turns")
        lines.append(f"- **Multi-Turn Thread %**: {s['multi_turn_percentage']}")
        lines.append("- **5 Sample Raw Messages**:")
        for idx, msg in enumerate(s["sample_raw_messages"], start=1):
            clean_display = msg.replace("\n", " ").strip()
            lines.append(f"  {idx}. `\"{clean_display}\"`")
        lines.append("")

    lines.extend([
        "---",
        "",
        "## 3. Brand Recommendations for AI Agent Assignment",
        "",
        "1. **@AmazonHelp**: **Highest Volume & Diversity**.",
        "   - *Pros*: Covers e-commerce (shipping, missing items, Prime subscriptions, refunds). Very rich multi-turn dialogues.",
        "   - *Best for*: Building a realistic retail/e-commerce support agent with clear action intents.",
        "",
        "2. **@AppleSupport**: **High Technical Depth**.",
        "   - *Pros*: Complex troubleshooting queries (iOS bugs, battery life, hardware faults, Apple ID).",
        "   - *Best for*: Technical support & diagnosis workflows.",
        "",
        "3. **@SpotifyCares**: **Focused Subscription & App Domain**.",
        "   - *Pros*: Clean problem domains (billing, family plan, offline downloads, sync). High multi-turn follow-ups.",
        "   - *Best for*: SaaS/Digital subscription assistant.",
        "",
        "4. **@Delta** or **@AmericanAir**: **High-Stakes Escalation & Policy**.",
        "   - *Pros*: Flight rebooking, baggage tracking, delay compensations. High emotional urgency.",
        "   - *Best for*: Policy-heavy and sentiment-sensitive support agents.",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Explore top 10 brands in twcs.csv dataset")
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to twcs.csv dataset",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Generate and use synthetic mock dataset if twcs.csv is missing",
    )
    parser.add_argument(
        "--output-report",
        type=str,
        default="reports/top_10_brands.md",
        help="Path to save markdown report",
    )
    args = parser.parse_args()

    data_file = Path(args.data_path)

    if not data_file.is_file():
        if args.mock:
            print(f"[!] Dataset not found at {data_file}. Generating synthetic benchmark dataset...")
            generate_mock_twcs_dataset(data_file)
            print(f"[OK] Generated synthetic twcs.csv at {data_file}.")
        else:
            print(get_dataset_guidance(data_file))
            print("Tip: You can test the full pipeline immediately with synthetic data using:")
            print("  python scripts/explore_brands.py --mock\n")
            sys.exit(1)

    results = explore_dataset(data_file)
    md_content = format_markdown_report(results)

    # Save report
    out_report_path = Path(args.output_report)
    out_report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[OK] Markdown report generated and saved to: {out_report_path.resolve()}\n")
    print(md_content)


if __name__ == "__main__":
    main()
