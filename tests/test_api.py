"""
Backend API Unit Tests using FastAPI TestClient
"""

import unittest
from fastapi.testclient import TestClient
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.api.main import app
from src.api.services import TicketService, AgentService


class TestSupportPlatformAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        # Pre-initialize services
        AgentService.get_agent()
        TicketService.initialize(max_threads=20)

    def test_health_check(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["retrieval_index_loaded"])
        self.assertGreater(data["retrieval_records_count"], 0)
        self.assertTrue(data["evaluation_artifacts_ready"])

    def test_get_tickets_pagination(self):
        resp = self.client.get("/api/tickets?page=1&limit=5")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total", data)
        self.assertIn("tickets", data)
        self.assertLessEqual(len(data["tickets"]), 5)
        if data["tickets"]:
            t = data["tickets"][0]
            self.assertIn("conversation_id", t)
            self.assertIn("preview", t)
            self.assertIn("status", t)
            self.assertIn("intent", t)

    def test_get_ticket_detail_found_and_not_found(self):
        # First get an existing ID
        resp = self.client.get("/api/tickets?limit=1")
        self.assertEqual(resp.status_code, 200)
        tickets = resp.json().get("tickets", [])
        if tickets:
            conv_id = tickets[0]["conversation_id"]
            detail_resp = self.client.get(f"/api/tickets/{conv_id}")
            self.assertEqual(detail_resp.status_code, 200)
            detail = detail_resp.json()
            self.assertEqual(detail["conversation_id"], conv_id)
            self.assertTrue(len(detail["turns"]) > 0)
            self.assertIn("speaker", detail["turns"][0])

        # Test 404 for invalid ID
        resp_404 = self.client.get("/api/tickets/999999999999")
        self.assertEqual(resp_404.status_code, 404)

    def test_analyze_routine_query(self):
        payload = {"text": "Where is my package? The tracking has not updated in two days."}
        resp = self.client.post("/api/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "Delivery Tracking & Status")
        self.assertEqual(data["language"], "en")
        self.assertTrue(data["auto_handle"])
        self.assertFalse(data["is_security_alert"])
        self.assertEqual(data["priority"], "standard")
        self.assertTrue(len(data["draft_reply"]) > 0)
        self.assertTrue(len(data["retrieved_evidence"]) > 0)

    def test_analyze_security_p0_query(self):
        payload = {"text": "URGENT! Someone hacked my account, changed the password and bought expensive electronics!"}
        resp = self.client.post("/api/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_security_alert"])
        self.assertEqual(data["priority"], "P0_CRITICAL")
        self.assertFalse(data["auto_handle"])
        self.assertIn("P0", data["escalation_reason"])

    def test_analyze_multilingual_query(self):
        payload = {"text": "¿Dónde está mi paquete? Todavía no ha llegado a mi casa."}
        resp = self.client.post("/api/analyze", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["language"], "es")

    def test_analyze_empty_input_rejected(self):
        resp = self.client.post("/api/analyze", json={"text": "   "})
        self.assertIn(resp.status_code, [400, 422])

    def test_draft_action_workflow(self):
        resp = self.client.get("/api/tickets?limit=1")
        tickets = resp.json().get("tickets", [])
        if tickets:
            conv_id = tickets[0]["conversation_id"]
            action_payload = {
                "conversation_id": conv_id,
                "draft_text": "We apologize for the delay. We are looking into this.",
                "action": "approve",
                "notes": "Verified by agent in simulation test",
            }
            resp_action = self.client.post("/api/reply/draft", json=action_payload)
            self.assertEqual(resp_action.status_code, 200)
            data = resp_action.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["new_status"], "resolved")

    def test_evaluation_summary_endpoint(self):
        resp = self.client.get("/api/evaluation/summary")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("headline_metrics", data)
        self.assertIn("system_comparison", data)
        self.assertIn("intent_breakdown", data)
        self.assertGreater(data["total_benchmark_records"], 0)

    def test_evaluation_errors_endpoint(self):
        resp = self.client.get("/api/evaluation/errors")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("top_confusion_pairs", data)
        self.assertIn("security_p0_cases", data)


    def test_classify_endpoint(self):
        resp = self.client.post("/classify", json={"text": "How do I return a damaged shirt?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "Returns, Replacements & Refunds")
        self.assertIn("confidence", data)
        self.assertEqual(data["language"], "en")
        self.assertIn("conversation_state", data)

    def test_agent_respond_endpoint(self):
        resp = self.client.post("/agent/respond", json={"text": "Where is my order?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["intent"], "Delivery Tracking & Status")
        self.assertIn("draft_reply", data)
        self.assertIn("retrieved_evidence", data)
        self.assertIn("auto_handle", data)

    def test_evaluation_confusion_matrix_endpoint(self):
        resp = self.client.get("/evaluation/confusion-matrix")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("intents", data)
        self.assertEqual(len(data["intents"]), 10)
        self.assertIn("matrix", data)
        self.assertEqual(len(data["matrix"]), 10)
        self.assertIn("accuracy", data)
        self.assertIn("macro_f1", data)
        self.assertIn("top_confusion_pairs", data)


if __name__ == "__main__":
    unittest.main()
