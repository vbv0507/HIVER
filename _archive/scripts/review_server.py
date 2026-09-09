"""
Step 2C: Local Human Review Web Server

Zero-dependency HTTP server using Python's standard library `http.server`.
Serves the interactive Golden Evaluation Set Human Review Dashboard on http://127.0.0.1:8765.

Endpoints:
  GET  /                            -> Serves eval/review_app/index.html
  GET  /api/data                    -> Returns all 200 items + live dashboard metrics
  GET  /api/thread?conv_id=...      -> Returns turns for requested conversation
  POST /api/approve_row             -> One-click human approval of assistant proposal
  POST /api/save_row                -> Saves custom human edits with constraint enforcement
  POST /api/reset_row               -> Resets a row back to unreviewed
  POST /api/batch_approve_unflagged -> Approves remaining non-difficult items
  POST /api/batch_approve_all       -> Explicitly approves all remaining items
  POST /api/sync                    -> Syncs review progress to CSV & Excel
"""

import csv
import json
import os
import sys
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

EVAL_DIR = ROOT_DIR / "eval"
APP_DIR = EVAL_DIR / "review_app"
STATE_PATH = EVAL_DIR / "golden_review_state.json"
THREADS_CACHE_PATH = EVAL_DIR / "golden_threads_cache.json"

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

ALLOWED_PRIORITIES = ["P0_CRITICAL", "standard"]


def load_state() -> dict:
    if not STATE_PATH.exists():
        from scripts.init_review_state import init_review_state
        init_review_state()
    with open(STATE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict) -> None:
    # Recalculate metrics
    items = state.get("items", [])
    total = len(items)
    reviewed = sum(1 for item in items if item.get("is_reviewed"))
    pending = total - reviewed
    approved = sum(1 for item in items if item.get("human_review_action") == "approved")
    edited = sum(1 for item in items if item.get("human_review_action") == "edited")
    difficult = sum(1 for item in items if item.get("is_difficult"))

    # Agreement tracking
    intent_agreements = 0
    intent_comparable = 0
    escalate_agreements = 0
    escalate_comparable = 0

    intent_counts = {}
    lang_counts = {}
    state_counts = {}
    escalation_count = 0
    security_count = 0
    p0_count = 0

    for item in items:
        if item.get("is_reviewed"):
            f_intent = item.get("my_final_intent")
            f_lang = item.get("my_final_language")
            f_state = item.get("my_final_conversation_state")
            f_esc = item.get("my_final_escalate")
            f_sec = item.get("my_final_is_security_alert")
            f_prio = item.get("my_final_priority")

            if f_intent:
                intent_counts[f_intent] = intent_counts.get(f_intent, 0) + 1
                intent_comparable += 1
                if str(f_intent).lower() == str(item.get("assistant_proposed_intent", "")).lower():
                    intent_agreements += 1

            if f_lang:
                lang_counts[f_lang] = lang_counts.get(f_lang, 0) + 1

            if f_state:
                state_counts[f_state] = state_counts.get(f_state, 0) + 1

            if f_esc is not None:
                escalate_comparable += 1
                if bool(f_esc):
                    escalation_count += 1
                if bool(f_esc) == bool(item.get("assistant_proposed_escalate")):
                    escalate_agreements += 1

            if f_sec:
                security_count += 1

            if f_prio == "P0_CRITICAL":
                p0_count += 1

    intent_agreement_pct = (intent_agreements / intent_comparable * 100) if intent_comparable > 0 else 0.0
    escalate_agreement_pct = (escalate_agreements / escalate_comparable * 100) if escalate_comparable > 0 else 0.0

    state["metadata"] = {
        "total_examples": total,
        "reviewed_count": reviewed,
        "pending_count": pending,
        "approved_count": approved,
        "edited_count": edited,
        "difficult_count": difficult,
        "intent_agreements": intent_agreements,
        "intent_comparable": intent_comparable,
        "intent_agreement_pct": round(intent_agreement_pct, 1),
        "escalate_agreements": escalate_agreements,
        "escalate_comparable": escalate_comparable,
        "escalate_agreement_pct": round(escalate_agreement_pct, 1),
        "intent_distribution": intent_counts,
        "language_distribution": lang_counts,
        "conversation_state_distribution": state_counts,
        "escalation_count": escalation_count,
        "security_count": security_count,
        "p0_count": p0_count,
    }

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def load_threads() -> dict:
    if not THREADS_CACHE_PATH.exists():
        from scripts.init_review_state import init_review_state
        init_review_state()
    with open(THREADS_CACHE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class ReviewRequestHandler(BaseHTTPRequestHandler):
    threads_cache = None

    def _send_json(self, data: dict, status: int = 200):
        content = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def _send_html(self, content_bytes: bytes, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content_bytes)))
        self.end_headers()
        self.wfile.write(content_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path in ["/", "/index.html"]:
            html_file = APP_DIR / "index.html"
            if html_file.exists():
                with open(html_file, "rb") as f:
                    self._send_html(f.read())
            else:
                self.send_error(404, "Frontend UI not found")
            return

        if path == "/api/data":
            state = load_state()
            self._send_json(state)
            return

        if path == "/api/thread":
            conv_id = query.get("conv_id", [""])[0]
            if not conv_id:
                self._send_json({"error": "Missing conv_id"}, 400)
                return
            if ReviewRequestHandler.threads_cache is None:
                ReviewRequestHandler.threads_cache = load_threads()
            thread = ReviewRequestHandler.threads_cache.get(conv_id)
            if thread:
                self._send_json(thread)
            else:
                self._send_json({"error": "Thread not found", "conversation_id": conv_id, "turns": []})
            return

        self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len)
        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        state = load_state()
        items = state.get("items", [])
        mid_map = {item["message_id"]: item for item in items}

        if path == "/api/approve_row":
            mid = body.get("message_id")
            if mid not in mid_map:
                self._send_json({"error": f"Message ID {mid} not found"}, 400)
                return

            item = mid_map[mid]
            # Copy assistant proposals into human fields
            item["my_final_intent"] = item["assistant_proposed_intent"]
            item["my_final_language"] = item["assistant_proposed_language"]
            item["my_final_conversation_state"] = item["assistant_proposed_conversation_state"]
            item["my_final_escalate"] = item["assistant_proposed_escalate"]
            item["my_final_is_security_alert"] = item["assistant_proposed_is_security_alert"]
            item["my_final_priority"] = item["assistant_proposed_priority"]
            if body.get("notes"):
                item["notes"] = body.get("notes")
            item["human_review_action"] = "approved"
            item["is_reviewed"] = True

            save_state(state)
            self._send_json({"status": "ok", "item": item, "metadata": state["metadata"]})
            return

        if path == "/api/save_row":
            mid = body.get("message_id")
            if mid not in mid_map:
                self._send_json({"error": f"Message ID {mid} not found"}, 400)
                return

            item = mid_map[mid]
            final_intent = body.get("my_final_intent")
            final_lang = body.get("my_final_language")
            final_state = body.get("my_final_conversation_state")
            final_esc = body.get("my_final_escalate")
            final_sec = body.get("my_final_is_security_alert")
            final_prio = body.get("my_final_priority")
            notes = body.get("notes", "")

            # Security Constraint enforcement:
            # If security alert == true => priority must be P0_CRITICAL
            if final_sec:
                final_prio = "P0_CRITICAL"
            elif not final_prio:
                final_prio = "standard"

            item["my_final_intent"] = final_intent
            item["my_final_language"] = final_lang
            item["my_final_conversation_state"] = final_state
            item["my_final_escalate"] = bool(final_esc)
            item["my_final_is_security_alert"] = bool(final_sec)
            item["my_final_priority"] = final_prio
            item["notes"] = notes

            # Audit check: Was it approved verbatim or edited?
            matches_assistant = (
                item["my_final_intent"] == item["assistant_proposed_intent"]
                and item["my_final_language"] == item["assistant_proposed_language"]
                and item["my_final_conversation_state"] == item["assistant_proposed_conversation_state"]
                and item["my_final_escalate"] == item["assistant_proposed_escalate"]
                and item["my_final_is_security_alert"] == item["assistant_proposed_is_security_alert"]
                and item["my_final_priority"] == item["assistant_proposed_priority"]
            )
            item["human_review_action"] = "approved" if matches_assistant else "edited"
            item["is_reviewed"] = True

            save_state(state)
            self._send_json({"status": "ok", "item": item, "metadata": state["metadata"]})
            return

        if path == "/api/reset_row":
            mid = body.get("message_id")
            if mid not in mid_map:
                self._send_json({"error": f"Message ID {mid} not found"}, 400)
                return

            item = mid_map[mid]
            item["my_final_intent"] = None
            item["my_final_language"] = None
            item["my_final_conversation_state"] = None
            item["my_final_escalate"] = None
            item["my_final_is_security_alert"] = None
            item["my_final_priority"] = None
            item["human_review_action"] = None
            item["is_reviewed"] = False

            save_state(state)
            self._send_json({"status": "ok", "item": item, "metadata": state["metadata"]})
            return

        if path == "/api/batch_approve_unflagged":
            approved_count = 0
            for item in items:
                # Approve if unreviewed, not difficult, and not low confidence
                if not item.get("is_reviewed") and not item.get("is_difficult") and item.get("assistant_confidence") != "LOW":
                    item["my_final_intent"] = item["assistant_proposed_intent"]
                    item["my_final_language"] = item["assistant_proposed_language"]
                    item["my_final_conversation_state"] = item["assistant_proposed_conversation_state"]
                    item["my_final_escalate"] = item["assistant_proposed_escalate"]
                    item["my_final_is_security_alert"] = item["assistant_proposed_is_security_alert"]
                    item["my_final_priority"] = item["assistant_proposed_priority"]
                    item["human_review_action"] = "approved"
                    item["is_reviewed"] = True
                    approved_count += 1

            save_state(state)
            self._send_json({"status": "ok", "batch_approved": approved_count, "metadata": state["metadata"]})
            return

        if path == "/api/batch_approve_all":
            approved_count = 0
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
                    approved_count += 1

            save_state(state)
            self._send_json({"status": "ok", "batch_approved": approved_count, "metadata": state["metadata"]})
            return

        if path == "/api/sync":
            # Flushes to eval/golden_eval_set_reviewed.csv
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

            self._send_json({"status": "ok", "synced_file": str(out_csv)})
            return

        self.send_error(404, "Endpoint not found")


def run_server(port: int = 8765):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, ReviewRequestHandler)
    print(f"Human Review Server running on http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nReview server stopped.")
        httpd.server_close()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    run_server(port)
