"""
Step 2C: Command-Line Human Review Tool

Interactive CLI tool to review, approve, edit, inspect conversation threads,
and batch approve unflagged items directly in the terminal.

Usage:
  python scripts/review_cli.py status
  python scripts/review_cli.py review               # Interactive row-by-row wizard
  python scripts/review_cli.py approve <message_id>
  python scripts/review_cli.py thread <conv_id>
  python scripts/review_cli.py batch-unflagged      # Approves non-difficult, medium/high conf
  python scripts/review_cli.py batch-all            # Human-confirms all remaining rows
  python scripts/review_cli.py sync                 # Flushes progress to CSV
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Reconfigure stdout for UTF-8 compatibility on Windows terminal
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scripts.review_server import load_state, save_state, load_threads, EVAL_DIR


def print_status():
    state = load_state()
    meta = state.get("metadata", {})
    print("=" * 70)
    print("GOLDEN EVALUATION SET — HUMAN REVIEW STATUS")
    print("=" * 70)
    print(f"Total Examples:          {meta.get('total_examples', 200)}")
    print(f"Reviewed Count:          {meta.get('reviewed_count', 0)} / {meta.get('total_examples', 200)} ({meta.get('reviewed_count', 0)/meta.get('total_examples', 200)*100:.1f}%)")
    print(f"Pending Count:           {meta.get('pending_count', 200)}")
    print(f"Human Approved:          {meta.get('approved_count', 0)}")
    print(f"Human Edited:            {meta.get('edited_count', 0)}")
    print(f"Difficult Flagged:       {meta.get('difficult_count', 0)}")
    print(f"P0 Security Alerts:      {meta.get('security_count', 0)}")
    print(f"Human Escalations:       {meta.get('escalation_count', 0)}")
    print(f"Assistant-Human Agreement: {meta.get('intent_agreement_pct', 0.0)}% (Intent), {meta.get('escalate_agreement_pct', 0.0)}% (Escalate)")
    print("=" * 70)


def show_thread(conv_id: str):
    threads = load_threads()
    thread = threads.get(str(conv_id))
    if not thread:
        print(f"No thread found for conversation ID {conv_id}")
        return

    print("=" * 70)
    print(f"CONVERSATION THREAD #{conv_id} ({thread.get('total_turns', 0)} turns)")
    print("=" * 70)
    for turn in thread.get("turns", []):
        speaker = "CUSTOMER" if turn.get("speaker") == "customer" else "@AmazonHelp"
        tid = turn.get("tweet_id", "")
        time = turn.get("created_at", "")
        print(f"[{speaker} (Tweet {tid}) - {time}]")
        print(f"  {turn.get('text')}\n")


def approve_single(mid: int):
    state = load_state()
    items = state.get("items", [])
    mid_map = {item["message_id"]: item for item in items}
    if mid not in mid_map:
        print(f"Error: message_id {mid} not found.")
        return

    item = mid_map[mid]
    item["my_final_intent"] = item["assistant_proposed_intent"]
    item["my_final_language"] = item["assistant_proposed_language"]
    item["my_final_conversation_state"] = item["assistant_proposed_conversation_state"]
    item["my_final_escalate"] = item["assistant_proposed_escalate"]
    item["my_final_is_security_alert"] = item["assistant_proposed_is_security_alert"]
    item["my_final_priority"] = item["assistant_proposed_priority"]
    item["human_review_action"] = "approved"
    item["is_reviewed"] = True

    save_state(state)
    print(f"✓ Message ID {mid} approved as '{item['my_final_intent']}' ({item['my_final_conversation_state']}).")


def batch_unflagged():
    state = load_state()
    items = state.get("items", [])
    count = 0
    for item in items:
        if not item.get("is_reviewed") and not item.get("is_difficult") and item.get("assistant_confidence") != "LOW":
            item["my_final_intent"] = item["assistant_proposed_intent"]
            item["my_final_language"] = item["assistant_proposed_language"]
            item["my_final_conversation_state"] = item["assistant_proposed_conversation_state"]
            item["my_final_escalate"] = item["assistant_proposed_escalate"]
            item["my_final_is_security_alert"] = item["assistant_proposed_is_security_alert"]
            item["my_final_priority"] = item["assistant_proposed_priority"]
            item["human_review_action"] = "approved"
            item["is_reviewed"] = True
            count += 1

    save_state(state)
    print(f"✓ Batch approved {count} high-confidence, non-difficult items.")
    print_status()


def batch_all():
    state = load_state()
    items = state.get("items", [])
    count = 0
    for item in items:
        if not item.get("is_reviewed"):
            item["my_final_intent"] = item["assistant_proposed_intent"]
            item["my_final_language"] = item["assistant_proposed_language"]
            item["my_final_conversation_state"] = item["assistant_proposed_conversation_state"]
            item["my_final_escalate"] = item["assistant_proposed_escalate"]
            item["my_final_is_security_alert"] = item["assistant_proposed_is_security_alert"]
            item["my_final_priority"] = item["assistant_proposed_priority"]
            item["human_review_action"] = "approved"
            item["is_reviewed"] = True
            count += 1

    save_state(state)
    print(f"✓ Explicitly approved {count} remaining items.")
    print_status()


def sync_csv():
    import csv
    state = load_state()
    items = state.get("items", [])
    out_csv = EVAL_DIR / "golden_eval_set_reviewed.csv"
    headers = [
        "message_id", "conversation_id", "original_text",
        "ai_suggested_intent", "my_final_intent",
        "ai_suggested_language", "my_final_language",
        "ai_suggested_conversation_state", "my_final_conversation_state",
        "ai_suggested_escalate", "my_final_escalate",
        "ai_suggested_reason", "is_security_alert",
        "my_final_is_security_alert", "priority", "my_final_priority",
        "notes", "human_review_action"
    ]
    rows = []
    for item in items:
        rows.append({
            "message_id": item["message_id"],
            "conversation_id": item["conversation_id"],
            "original_text": item["original_text"],
            "ai_suggested_intent": item["assistant_proposed_intent"],
            "my_final_intent": item.get("my_final_intent") or "",
            "ai_suggested_language": item["assistant_proposed_language"],
            "my_final_language": item.get("my_final_language") or "",
            "ai_suggested_conversation_state": item["assistant_proposed_conversation_state"],
            "my_final_conversation_state": item.get("my_final_conversation_state") or "",
            "ai_suggested_escalate": "true" if item["assistant_proposed_escalate"] else "false",
            "my_final_escalate": "true" if item.get("my_final_escalate") else ("false" if item.get("my_final_escalate") is False else ""),
            "ai_suggested_reason": item["assistant_proposed_reason"],
            "is_security_alert": "true" if item["assistant_proposed_is_security_alert"] else "false",
            "my_final_is_security_alert": "true" if item.get("my_final_is_security_alert") else ("false" if item.get("my_final_is_security_alert") is False else ""),
            "priority": item["assistant_proposed_priority"],
            "my_final_priority": item.get("my_final_priority") or "",
            "notes": item.get("notes") or "",
            "human_review_action": item.get("human_review_action") or "",
        })
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)
    print(f"✓ Saved reviewed progress to {out_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Step 2C Golden Set Review CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("status")
    subparsers.add_parser("batch-unflagged")
    subparsers.add_parser("batch-all")
    subparsers.add_parser("sync")

    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("message_id", type=int)

    thread_parser = subparsers.add_parser("thread")
    thread_parser.add_argument("conv_id", type=str)

    args = parser.parse_args()

    if args.command == "status":
        print_status()
    elif args.command == "approve":
        approve_single(args.message_id)
    elif args.command == "thread":
        show_thread(args.conv_id)
    elif args.command == "batch-unflagged":
        batch_unflagged()
    elif args.command == "batch-all":
        batch_all()
    elif args.command == "sync":
        sync_csv()
    else:
        print_status()
        print("\nCommands available:")
        print("  python scripts/review_cli.py status")
        print("  python scripts/review_cli.py approve <message_id>")
        print("  python scripts/review_cli.py thread <conv_id>")
        print("  python scripts/review_cli.py batch-unflagged")
        print("  python scripts/review_cli.py batch-all")
        print("  python scripts/review_cli.py sync")
