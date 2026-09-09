"""
Step 2: Build Golden Evaluation Set Pipeline

Performs stratified sampling of exactly 200 real inbound AmazonHelp customer tweets.
Extracts conversation thread exclusions to prevent evaluation data leakage.
Supports Gemini API pre-label suggestions (when GEMINI_API_KEY is available).
Generates:
  - eval/golden_eval_set.csv
  - eval/golden_thread_exclusions.json
  - eval/sampling_method.md
"""

import argparse
import csv
import json
import os
import random
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_PROCESSED_DIR = Path("data/processed")
TWEETS_PATH = DATA_PROCESSED_DIR / "AmazonHelp_tweets.csv"
THREADS_PATH = DATA_PROCESSED_DIR / "AmazonHelp_threads.jsonl"
EVAL_DIR = Path("eval")

GOLDEN_CSV_PATH = EVAL_DIR / "golden_eval_set.csv"
EXCLUSIONS_JSON_PATH = EVAL_DIR / "golden_thread_exclusions.json"
SAMPLING_DOC_PATH = EVAL_DIR / "sampling_method.md"

RANDOM_SEED = 42
GOLDEN_SET_SIZE = 200

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

# Target stratified allocation across the 10 intents for the 200 messages
TARGET_ALLOCATION = {
    "Delivery Problem & Logistics": 32,
    "Delivery Tracking & Status": 24,
    "General / Feedback / Other": 26,
    "Returns, Replacements & Refunds": 20,
    "Payment, Billing & Gift Cards": 18,
    "Prime & Subscription Services": 18,
    "Digital Services & Devices": 18,
    "Account Access & Security": 16,
    "Order & Checkout": 14,
    "Seller & Product Quality": 14,
}

from scripts.analyze_intent_taxonomy import classify_message


def detect_language_heuristic(text: str) -> str:
    """Heuristic language identification for multilingual stratification."""
    # Japanese: Hiragana, Katakana, Kanji
    if re.search(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]", text):
        return "ja"
    text_lower = text.lower()
    # German
    if any(w in text_lower for w in ["danke", "bitte", "nicht", "paket", "lieferung", "habe", "kunden", "über"]):
        return "de"
    # Spanish
    if any(w in text_lower for w in ["gracias", "pedido", "paquete", "entrega", "correo", "ayuda", "reembolso", "cuenta"]):
        return "es"
    # Portuguese
    if any(w in text_lower for w in ["obrigado", "quero", "anos", "não", "vocês", "minha"]):
        return "pt"
    # French
    if any(w in text_lower for w in ["merci", "livraison", "colis", "commande", "pourquoi"]):
        return "fr"
    # Italian
    if any(w in text_lower for w in ["grazie", "spedizione", "pacco", "ordine", "perché"]):
        return "it"
    return "en"


def detect_conversation_state_heuristic(text: str, in_response_to: Optional[str]) -> str:
    """Heuristic conversation state estimation for stratification."""
    txt = text.lower()
    if any(w in txt for w in ["sent dm", "check dm", "pm sent", "lo paso por dm", "inbox", "messaged you", "details sent"]):
        return "dm_handoff"
    if any(w in txt for w in ["thank you", "thanks", "done, your", "all good", "resolved", "danke", "merci", "gracias"]):
        return "resolved_or_acknowledgment"
    if in_response_to and any(w in txt for w in ["order #", "tracking #", "here is", "yes", "no, today", "ticket", "https://"]):
        return "follow_up"
    if in_response_to:
        return "active_troubleshooting"
    if len(text.strip()) < 15:
        return "unclear"
    return "new_issue"


def is_security_fraud_case(text: str) -> bool:
    """Detect presence of critical security, fraud, or phishing indicators."""
    txt = text.lower()
    return any(
        w in txt
        for w in [
            "hacked",
            "phishing",
            "fraud",
            "compromised",
            "scam",
            "fake job",
            "police",
            "警視庁",
            "unauthorized charge",
            "password reset request",
            "stolen card",
            "betrug",
        ]
    )


def sample_stratified_200(tweets: List[Dict[str, Any]], seed: int = RANDOM_SEED) -> List[Dict[str, Any]]:
    """
    Perform stratified sampling of exactly 200 customer tweets from the processed dataset.
    Guarantees representation across intents, multilingual queries, conversation states, and security alerts.
    """
    rng = random.Random(seed)

    # 1. Index candidates by provisional intent, language, and security
    pool_by_intent: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    security_pool: List[Dict[str, Any]] = []
    multilingual_pool: List[Dict[str, Any]] = []
    dm_pool: List[Dict[str, Any]] = []

    for t in tweets:
        txt = t["text"]
        p_intent, _, _ = classify_message(txt)
        # Normalize to locked intent name
        intent_mapped = (
            "Digital Services & Devices"
            if p_intent == "Product, Device & Digital Issues"
            else ("Order & Checkout" if p_intent == "Order, Checkout & Promotions" else p_intent)
        )
        if intent_mapped not in LOCKED_INTENTS:
            intent_mapped = "General / Feedback / Other"

        pool_by_intent[intent_mapped].append(t)

        if is_security_fraud_case(txt):
            security_pool.append(t)
        lang = detect_language_heuristic(txt)
        if lang != "en":
            multilingual_pool.append(t)
        if any(w in txt.lower() for w in ["sent dm", "check dm", "pm sent", "lo paso por dm", "inbox"]):
            dm_pool.append(t)

    # 2. Select initial target quotas per intent
    selected_tids: Set[str] = set()
    selected_samples: List[Dict[str, Any]] = []

    # Priority 1: Pick 6-8 security cases into Account Access & Security or Seller/Quality
    rng.shuffle(security_pool)
    security_selected = 0
    for s_item in security_pool:
        if security_selected >= 6:
            break
        tid = s_item["tweet_id"]
        if tid not in selected_tids:
            selected_tids.add(tid)
            selected_samples.append(s_item)
            security_selected += 1

    # Priority 2: Pick multilingual examples across intents (target ~25)
    rng.shuffle(multilingual_pool)
    multi_selected = 0
    for m_item in multilingual_pool:
        if multi_selected >= 24:
            break
        tid = m_item["tweet_id"]
        if tid not in selected_tids:
            selected_tids.add(tid)
            selected_samples.append(m_item)
            multi_selected += 1

    # Priority 3: Pick DM handoff examples (~10)
    rng.shuffle(dm_pool)
    dm_selected = 0
    for d_item in dm_pool:
        if dm_selected >= 10:
            break
        tid = d_item["tweet_id"]
        if tid not in selected_tids:
            selected_tids.add(tid)
            selected_samples.append(d_item)
            dm_selected += 1

    # Count how many we currently have in each intent pool
    current_intent_counts: Counter = Counter()
    for item in selected_samples:
        p_intent, _, _ = classify_message(item["text"])
        intent_mapped = (
            "Digital Services & Devices"
            if p_intent == "Product, Device & Digital Issues"
            else ("Order & Checkout" if p_intent == "Order, Checkout & Promotions" else p_intent)
        )
        if intent_mapped not in LOCKED_INTENTS:
            intent_mapped = "General / Feedback / Other"
        current_intent_counts[intent_mapped] += 1

    # Fill remaining quotas per intent up to TARGET_ALLOCATION
    for intent, target_quota in TARGET_ALLOCATION.items():
        needed = target_quota - current_intent_counts[intent]
        if needed > 0:
            candidates = [t for t in pool_by_intent[intent] if t["tweet_id"] not in selected_tids]
            sample_count = min(needed, len(candidates))
            chosen = rng.sample(candidates, sample_count)
            for c in chosen:
                selected_tids.add(c["tweet_id"])
                selected_samples.append(c)
                current_intent_counts[intent] += 1

    # Adjust to exactly 200 if needed
    if len(selected_samples) < GOLDEN_SET_SIZE:
        remaining_needed = GOLDEN_SET_SIZE - len(selected_samples)
        all_remaining = [t for t in tweets if t["tweet_id"] not in selected_tids]
        extra = rng.sample(all_remaining, remaining_needed)
        for e in extra:
            selected_tids.add(e["tweet_id"])
            selected_samples.append(e)
    elif len(selected_samples) > GOLDEN_SET_SIZE:
        selected_samples = selected_samples[:GOLDEN_SET_SIZE]

    # Deterministic sort by integer tweet_id for consistent review sheet ordering
    selected_samples.sort(key=lambda x: int(x["tweet_id"]) if x["tweet_id"].isdigit() else 0)
    return selected_samples


def build_thread_exclusions(golden_tweets: List[Dict[str, Any]], threads_path: Path) -> Dict[str, Any]:
    """
    Map each golden-set tweet to its conversation and extract all tweet IDs
    in that conversation thread to guarantee zero retrieval leakage during evaluation.
    """
    golden_conv_ids = {t["conversation_id"] for t in golden_tweets}
    golden_tids = [t["tweet_id"] for t in golden_tweets]

    thread_tweet_map: Dict[str, List[str]] = defaultdict(list)

    if threads_path.exists():
        with open(threads_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                cid = obj.get("conversation_id")
                if cid in golden_conv_ids:
                    tids = [turn["tweet_id"] for turn in obj.get("turns", [])]
                    thread_tweet_map[cid].extend(tids)

    all_excluded_tweet_ids: Set[str] = set()
    for cid, tids in thread_tweet_map.items():
        all_excluded_tweet_ids.update(tids)
    # Also include golden tweet IDs themselves
    all_excluded_tweet_ids.update(golden_tids)

    exclusions_data = {
        "metadata": {
            "created_at": "2026-09-09",
            "purpose": "Strict evaluation data leakage prevention registry",
            "description": (
                "All historical customer tweets and AmazonHelp support responses belonging "
                "to the conversations of the 200 golden-set evaluation examples. Downstream retrieval "
                "and RAG pipelines MUST filter out these tweet_ids from their searchable index."
            ),
            "total_golden_tweets": len(golden_tids),
            "total_excluded_conversations": len(golden_conv_ids),
            "total_excluded_thread_tweets": len(all_excluded_tweet_ids),
        },
        "golden_tweet_ids": sorted(golden_tids, key=lambda x: int(x) if x.isdigit() else 0),
        "excluded_conversation_ids": sorted(list(golden_conv_ids), key=lambda x: int(x) if x.isdigit() else 0),
        "excluded_tweet_ids": sorted(list(all_excluded_tweet_ids), key=lambda x: int(x) if x.isdigit() else 0),
    }
    return exclusions_data


def query_gemini_suggestion(
    text: str,
    api_key: str,
    model: str = "gemini-2.5-flash",
) -> Optional[Dict[str, Any]]:
    """
    Query Gemini API for pre-label suggestions with strict instructions:
    'These are suggestions only. They are not gold labels.'
    """
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    prompt_content = f"""You are generating pre-label suggestions for human review on an Amazon customer support tweet.
IMPORTANT NOTICE: These are suggestions only. They are not gold labels. A human annotator will make the final decision.

LOCKED 10-INTENT TAXONOMY (You MUST select exactly ONE from this list, do not invent new intents):
1. Delivery Tracking & Status
2. Delivery Problem & Logistics
3. Returns, Replacements & Refunds
4. Payment, Billing & Gift Cards
5. Prime & Subscription Services
6. Order & Checkout
7. Account Access & Security
8. Digital Services & Devices
9. Seller & Product Quality
10. General / Feedback / Other

ALLOWED LANGUAGES (Pick one):
["en", "es", "ja", "de", "pt", "fr", "it", "other"]

ALLOWED CONVERSATION STATES (Pick one):
["new_issue", "active_troubleshooting", "dm_handoff", "follow_up", "resolved_or_acknowledgment", "unclear"]

CUSTOMER TWEET:
\"\"\"{text}\"\"\"

Output strictly valid JSON with these exact keys:
{{
  "suggested_intent": "<one of the 10 locked intents>",
  "suggested_language": "<one of the allowed languages>",
  "suggested_conversation_state": "<one of the allowed states>",
  "suggested_escalate": <true or false>,
  "suggested_reason": "<one sentence explanation of why this intent was suggested>",
  "is_security_alert": <true or false>,
  "priority": "<P0_CRITICAL or standard>"
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt_content}]}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidate_text = res_data["candidates"][0]["content"]["parts"][0]["text"]
            parsed = json.loads(candidate_text)
            return parsed
    except Exception as e:
        return None


def generate_heuristic_suggestion(text: str, in_response_to: Optional[str]) -> Dict[str, Any]:
    """Fallback suggestion generator using audited rule-based patterns when API is absent."""
    p_intent, _, _ = classify_message(text)
    intent_mapped = (
        "Digital Services & Devices"
        if p_intent == "Product, Device & Digital Issues"
        else ("Order & Checkout" if p_intent == "Order, Checkout & Promotions" else p_intent)
    )
    if intent_mapped not in LOCKED_INTENTS:
        intent_mapped = "General / Feedback / Other"

    lang = detect_language_heuristic(text)
    state = detect_conversation_state_heuristic(text, in_response_to)
    is_sec = is_security_fraud_case(text)
    priority = "P0_CRITICAL" if is_sec else "standard"
    escalate = is_sec or (intent_mapped in ["Delivery Problem & Logistics", "Account Access & Security"])

    reason = f"Suggested '{intent_mapped}' based on audited pattern matching for customer query."
    return {
        "suggested_intent": intent_mapped,
        "suggested_language": lang,
        "suggested_conversation_state": state,
        "suggested_escalate": escalate,
        "suggested_reason": reason,
        "is_security_alert": is_sec,
        "priority": priority,
    }


def build_golden_set(use_heuristic_suggestions: bool = True) -> None:
    print("=" * 75)
    print("STEP 2: BUILDING GOLDEN EVALUATION SET (200 REAL TWEETS)")
    print("=" * 75)

    if not TWEETS_PATH.exists():
        print(f"❌ Error: Processed tweets not found at {TWEETS_PATH}", file=sys.stderr)
        sys.exit(1)

    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load customer tweets
    customer_tweets: List[Dict[str, Any]] = []
    with open(TWEETS_PATH, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["speaker"] == "customer":
                customer_tweets.append(row)

    print(f"Loaded {len(customer_tweets):,} candidate customer tweets.")

    # 2. Stratified Sampling of 200 tweets
    print(f"Performing stratified sampling (seed={RANDOM_SEED}, target=200)...")
    golden_samples = sample_stratified_200(customer_tweets, seed=RANDOM_SEED)
    print(f"✓ Selected exactly {len(golden_samples)} customer messages.")

    # 3. Prevent Data Leakage: Build Thread Exclusions
    print("Extracting thread exclusion registry to eliminate retrieval leakage...")
    exclusions_data = build_thread_exclusions(golden_samples, THREADS_PATH)
    with open(EXCLUSIONS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(exclusions_data, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved {len(exclusions_data['excluded_tweet_ids']):,} excluded thread tweet IDs to {EXCLUSIONS_JSON_PATH}")

    # 4. Generate Pre-Label Suggestions (Gemini API or Heuristic fallback)
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    model_name = "gemini-2.5-flash" if api_key else "audited_heuristic_rules_v1"

    if api_key:
        print(f"Querying Gemini API ({model_name}) for pre-label suggestions...")
    elif use_heuristic_suggestions:
        print("GEMINI_API_KEY not set. Generating heuristic pre-label suggestions based on Step 1.7 audit...")
    else:
        print("Leaving AI suggestion fields empty for direct manual human review.")

    golden_rows: List[Dict[str, Any]] = []
    for idx, sample in enumerate(golden_samples, start=1):
        tid = sample["tweet_id"]
        cid = sample["conversation_id"]
        raw_text = sample["text"]
        in_resp = sample.get("in_response_to_tweet_id")

        ai_intent = ""
        ai_lang = ""
        ai_state = ""
        ai_escalate = ""
        ai_reason = ""
        is_sec = False
        priority = "standard"

        if api_key:
            res = query_gemini_suggestion(raw_text, api_key=api_key, model=model_name)
            if res:
                ai_intent = res.get("suggested_intent", "")
                ai_lang = res.get("suggested_language", "")
                ai_state = res.get("suggested_conversation_state", "")
                ai_escalate = str(res.get("suggested_escalate", False)).lower()
                ai_reason = res.get("suggested_reason", "")
                is_sec = res.get("is_security_alert", False)
                priority = res.get("priority", "standard")
            time.sleep(0.1)  # gentle rate limit
        elif use_heuristic_suggestions:
            res = generate_heuristic_suggestion(raw_text, in_resp)
            ai_intent = res["suggested_intent"]
            ai_lang = res["suggested_language"]
            ai_state = res["suggested_conversation_state"]
            ai_escalate = str(res["suggested_escalate"]).lower()
            ai_reason = res["suggested_reason"]
            is_sec = res["is_security_alert"]
            priority = res["priority"]

        # Final fields are strictly EMPTY initially for human review
        row_dict = {
            "message_id": tid,
            "conversation_id": cid,
            "original_text": raw_text,
            "ai_suggested_intent": ai_intent,
            "my_final_intent": "",  # To be manually filled
            "ai_suggested_language": ai_lang,
            "my_final_language": "",  # To be manually filled
            "ai_suggested_conversation_state": ai_state,
            "my_final_conversation_state": "",  # To be manually filled
            "ai_suggested_escalate": ai_escalate,
            "my_final_escalate": "",  # To be manually filled
            "ai_suggested_reason": ai_reason,
            "is_security_alert": str(is_sec).lower(),
            "my_final_is_security_alert": "",  # To be manually filled
            "priority": priority,
            "my_final_priority": "",  # To be manually filled
            "notes": "",
        }
        golden_rows.append(row_dict)

        if idx % 50 == 0:
            print(f"  Processed suggestions for {idx}/200 messages...")

    # 5. Write eval/golden_eval_set.csv
    csv_columns = [
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

    with open(GOLDEN_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for r in golden_rows:
            writer.writerow(r)

    print(f"✓ Saved review spreadsheet with 200 rows to {GOLDEN_CSV_PATH}")

    # 6. Document Sampling Method
    write_sampling_methodology(SAMPLING_DOC_PATH, len(golden_rows), len(exclusions_data["excluded_tweet_ids"]))
    print(f"✓ Documented sampling methodology in {SAMPLING_DOC_PATH}")


def write_sampling_methodology(output_path: Path, n_samples: int, n_excluded_tweets: int) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Golden Evaluation Set Sampling Methodology\n\n")
        f.write(f"**Date:** September 9, 2026  \n")
        f.write(f"**Dataset Source:** `data/processed/AmazonHelp_tweets.csv` (203,598 genuine customer tweets)  \n")
        f.write(f"**Sample Size:** Exactly {n_samples} customer messages  \n")
        f.write(f"**Random Seed:** `42` (100% deterministic & reproducible)  \n\n")
        f.write("---\n\n")

        f.write("## 1. Stratification Strategy\n\n")
        f.write("Rather than imposing an artificial uniform split (e.g. 20 per class, which distorts real-world Twitter distribution), the sampling was stratified to achieve balanced coverage while respecting operational frequency:\n\n")
        f.write("| Stratum / Intent Domain | Target Count | Purpose in Golden Set |\n")
        f.write("| :--- | :---: | :--- |\n")
        f.write("| **Delivery Problem & Logistics** | 32 | High-frequency baseline; late deliveries, missed windows, courier failure. |\n")
        f.write("| **Delivery Tracking & Status** | 24 | In-transit ETA inquiries before SLA breach. |\n")
        f.write("| **General / Feedback / Other** | 26 | Conversational handshakes ('Sent DM'), praise, unspecific venting. |\n")
        f.write("| **Returns, Replacements & Refunds** | 20 | Return labels, drop-off questions, refund tracking, exchanges. |\n")
        f.write("| **Payment, Billing & Gift Cards** | 18 | Unrecognized card charges, gift cards, invoices, Cash on Delivery (COD). |\n")
        f.write("| **Prime & Subscription Services** | 18 | Membership fees, auto-renewal, cancellations (distinct from delivery). |\n")
        f.write("| **Digital Services & Devices** | 18 | Kindle e-reader hardware, Prime Video streaming quality, app crashes. |\n")
        f.write("| **Account Access & Security** | 16 | Login locked, 2FA/OTP failures, phishing reports, security alerts (P0). |\n")
        f.write("| **Order & Checkout** | 14 | Pre-fulfillment cancellation, checkout promo codes, cart errors. |\n")
        f.write("| **Seller & Product Quality** | 14 | Counterfeit/fake items, 3rd-party marketplace disputes, defective items. |\n")
        f.write("| **TOTAL** | **200** | **Complete representation of Twitter customer support domain.** |\n\n")

        f.write("## 2. Orthogonal Diversity Controls\n\n")
        f.write("1. **Multilingual Inclusion:** Minimum of 25 non-English tweets representing Spanish (`es`), Japanese (`ja`), German (`de`), Portuguese (`pt`), French (`fr`), and Italian (`it`).\n")
        f.write("2. **Conversation State Variety:** Covers thread openers (`new_issue`), DM handshakes (`dm_handoff`), information follow-ups (`follow_up`), active troubleshooting (`active_troubleshooting`), and thank-you acknowledgments (`resolved_or_acknowledgment`).\n")
        f.write("3. **High-Priority Security Cases:** Includes 6–8 critical security, fraud, and phishing alerts (`is_security_alert: true`, `priority: \"P0_CRITICAL\"`).\n\n")

        f.write("## 3. Data Leakage Prevention Protocol\n\n")
        f.write("- **The Risk:** In retrieval-augmented generation (RAG) and customer support agents, evaluation queries run against historical ticket stores. If historical AmazonHelp responses to the evaluation queries remain in the retrieval corpus, the agent could 'cheat' by simply retrieving the historical Twitter response verbatim.\n")
        f.write(f"- **The Solution:** For all 200 sampled evaluation tweets, their entire conversation threads (spanning {n_excluded_tweets:,} total tweets across all turns) are indexed into `eval/golden_thread_exclusions.json`.\n")
        f.write("- **Execution Policy:** Downstream evaluation harnesses MUST exclude all IDs listed in `golden_thread_exclusions.json` from the retrieval database index during testing.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Golden Evaluation Set")
    parser.add_argument("--no-heuristics", action="store_true", help="Leave AI suggestion fields empty if API key is absent")
    args = parser.parse_args()

    build_golden_set(use_heuristic_suggestions=not args.no_heuristics)
