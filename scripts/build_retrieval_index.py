"""
Step 3: Build Retrieval Index Script

Offline execution script to:
1. Extract resolution pairs from data/processed/AmazonHelp_threads.jsonl
2. Fit TF-IDF index
3. Save data/processed/resolution_pairs.jsonl and data/processed/retrieval_index.joblib
"""

import sys
from pathlib import Path

# Add project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Reconfigure stdout for UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.retrieval.corpus_builder import build_resolution_corpus
from src.retrieval.retriever import AmazonHelpRetriever, DEFAULT_CORPUS_PATH, DEFAULT_INDEX_PATH


def main():
    print("=" * 75)
    print("STEP 3: BUILDING AMAZONHELP RESOLUTION RETRIEVAL INDEX")
    print("=" * 75)

    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    print(f"Targeting up to {limit:,} informative resolution pairs...")

    # 1. Build corpus
    build_resolution_corpus(output_path=DEFAULT_CORPUS_PATH, max_pairs=limit)

    # 2. Build and cache index
    retriever = AmazonHelpRetriever(corpus_path=DEFAULT_CORPUS_PATH, index_path=DEFAULT_INDEX_PATH)
    retriever.build_and_save_index()

    # 3. Quick test retrieval
    test_query = "Where is my package? Tracking says delivered but I did not get it"
    results = retriever.search(test_query, top_k=2, evaluation_mode=True)

    print("\nSmoke Test Retrieval Result:")
    print(f"Query: '{test_query}'")
    for i, r in enumerate(results, 1):
        print(f"\nResult {i} (Score: {r['score']}, Conv: {r['conversation_id']}, Intent: {r['intent']}):")
        print(f"  Customer: {r['customer_message'][:80]}...")
        print(f"  Response: {r['historical_response'][:100]}...")

    print("\n" + "=" * 75)
    print("RETRIEVAL INDEX BUILD COMPLETE")
    print("=" * 75)


if __name__ == "__main__":
    main()
