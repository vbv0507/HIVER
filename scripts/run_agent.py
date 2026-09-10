"""
Step 3: Run AmazonHelp AI Support Agent CLI Runner

Usage:
  # One-shot inference
  python scripts/run_agent.py --text "Where is my package? Tracking number is 12345"

  # Test escalation behavior on security issue
  python scripts/run_agent.py --text "Someone hacked my account and made purchases!"

  # Test baselines
  python scripts/run_agent.py --baseline 1 --text "I want to return an item"
  python scripts/run_agent.py --baseline 2 --text "Where is my order?"

  # Interactive mode
  python scripts/run_agent.py --interactive
"""

import argparse
import json
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

from src.agent.amazon_agent import AmazonHelpAgent
from src.baselines.baseline_rules import RuleTemplateBaseline
from src.baselines.baseline_retrieval_only import NearestNeighborBaseline


def format_output(result: dict) -> str:
    return json.dumps(result, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Run AmazonHelp AI Support Agent")
    parser.add_argument("--text", type=str, help="Customer input message to process")
    parser.add_argument("--baseline", type=int, choices=[1, 2], help="Run baseline (1: RuleTemplate, 2: NearestNeighbor)")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive chat session")
    parser.add_argument("--no-leakage-filter", action="store_true", help="Disable golden-set leakage filter")

    args = parser.parse_args()

    # Initialize requested agent/baseline
    eval_mode = not args.no_leakage_filter

    if args.baseline == 1:
        print("[Agent Runner] Loading Baseline 1 (Rule-Based + Static Template)...")
        agent = RuleTemplateBaseline()
    elif args.baseline == 2:
        print("[Agent Runner] Loading Baseline 2 (Nearest-Neighbor Retrieval)...")
        agent = NearestNeighborBaseline(evaluation_mode=eval_mode)
    else:
        print(f"[Agent Runner] Loading AmazonHelp AI Support Agent (Evaluation Mode: {eval_mode})...")
        agent = AmazonHelpAgent(evaluation_mode=eval_mode)

    if args.text is not None:
        customer_text = args.text.strip()
        if not customer_text:
            parser.error("--text must contain at least one non-whitespace character")
        print(f"\n[Customer Input]: {customer_text}")
        output = agent.process_message(customer_text)
        print("\n[Structured Agent Output]:")
        print(format_output(output))
        return

    if args.interactive:
        print("\n" + "=" * 70)
        print("AMAZONHELP AI SUPPORT AGENT — INTERACTIVE CONSOLE")
        print("Type your message below (or 'exit' / 'quit' to end):")
        print("=" * 70 + "\n")

        while True:
            try:
                user_msg = input("Customer > ").strip()
                if user_msg.lower() in ["exit", "quit", "q"]:
                    print("Exiting interactive session.")
                    break
                if not user_msg:
                    continue

                output = agent.process_message(user_msg)
                print("\nAgent Output:")
                print(format_output(output))
                print("-" * 70)
            except KeyboardInterrupt:
                print("\nSession ended.")
                break
        return

    # Default demonstration if no arguments provided
    demo_queries = [
        ("Routine Informational (Auto-Handle)", "Where is my package? The tracking hasn't updated in two days."),
        ("P0 Security Alert (Escalation)", "Someone hacked into my account and ordered items with my saved credit card!"),
        ("Return Policy (Auto-Handle)", "I want to return a defective pair of headphones for a refund."),
        ("Human Agent Demanded (Escalation)", "Let me speak to a human representative right now."),
    ]

    print("\nRunning demonstration queries on AmazonHelp AI Agent:\n")
    for title, q in demo_queries:
        print("=" * 70)
        print(f"DEMO: {title}")
        print(f"Query: '{q}'")
        output = agent.process_message(q)
        print("\nResult:")
        print(format_output(output))
        print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
