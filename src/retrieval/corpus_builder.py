"""
Step 3: Historical Resolution Corpus Builder

Extracts customer -> AmazonHelp interaction pairs and resolution-bearing turns
from data/processed/AmazonHelp_threads.jsonl.

Preserves:
  - conversation_id
  - customer_tweet_id
  - amazon_tweet_id
  - customer_message
  - amazon_response
  - timestamp
  - intent
  - metadata (turn index, length, language)
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from tqdm import tqdm

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.classifier.intent_classifier import AmazonHelpIntentClassifier

DEFAULT_THREADS_PATH = ROOT_DIR / "data/processed/AmazonHelp_threads.jsonl"
DEFAULT_OUTPUT_CORPUS = ROOT_DIR / "data/processed/resolution_pairs.jsonl"


def is_informative_pair(cust_text: str, resp_text: str) -> bool:
    """Filters out trivial greetings, bare emojis, or low-information acknowledgments."""
    c_clean = re.sub(r"@\w+", "", cust_text).strip()
    r_clean = re.sub(r"@\w+", "", resp_text).strip()

    # Minimum substantive length
    if len(c_clean) < 12 or len(r_clean) < 15:
        return False

    # Avoid pairs where response is just a sign-off
    if re.fullmatch(r"(?i)(thanks|thank you|have a (great|nice) day|yw|you're welcome|de rien|bitte|gerne)[.!]?\s*(\^[a-z]{2})?", r_clean):
        return False

    return True


def build_resolution_corpus(
    threads_path: Path = DEFAULT_THREADS_PATH,
    output_path: Path = DEFAULT_OUTPUT_CORPUS,
    max_pairs: Optional[int] = 50000,
) -> int:
    """
    Builds the retrieval corpus of resolution pairs from conversation threads.
    """
    if not threads_path.exists():
        raise FileNotFoundError(f"Threads file not found: {threads_path}")

    classifier = AmazonHelpIntentClassifier()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Building resolution corpus from {threads_path}...")
    pair_count = 0

    with open(threads_path, "r", encoding="utf-8") as in_f, open(output_path, "w", encoding="utf-8") as out_f:
        for line in tqdm(in_f, desc="Scanning threads"):
            if not line.strip():
                continue
            data = json.loads(line)
            conv_id = str(data.get("conversation_id"))
            turns = data.get("turns", [])

            for i in range(len(turns) - 1):
                t_curr = turns[i]
                t_next = turns[i + 1]

                # Match customer query directly followed by official AmazonHelp response
                if t_curr.get("speaker") == "customer" and t_next.get("speaker") == "amazonhelp":
                    c_text = t_curr.get("text", "").strip()
                    r_text = t_next.get("text", "").strip()

                    if is_informative_pair(c_text, r_text):
                        clf_res = classifier.classify(c_text)
                        
                        record = {
                            "conversation_id": conv_id,
                            "customer_tweet_id": str(t_curr.get("tweet_id")),
                            "amazon_tweet_id": str(t_next.get("tweet_id")),
                            "customer_message": c_text,
                            "amazon_response": r_text,
                            "timestamp": t_curr.get("created_at", ""),
                            "intent": clf_res["intent"],
                            "confidence": clf_res["confidence"],
                            "language": clf_res["language"],
                            "is_security_alert": clf_res["is_security_alert"],
                        }
                        out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
                        pair_count += 1

                        if max_pairs and pair_count >= max_pairs:
                            break
            if max_pairs and pair_count >= max_pairs:
                break

    print(f"✓ Resolution corpus built: {pair_count:,} pairs saved to {output_path}")
    return pair_count


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    build_resolution_corpus(max_pairs=limit)
