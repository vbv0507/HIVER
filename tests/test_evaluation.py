"""
Step 4 Test Suite: Evaluation Harness & Metrics Validation

Tests:
1. Golden leakage exclusion enforcement
2. Metric calculations (classification, binary, deterministic checks, retrieval, latency)
3. Judge JSON parsing & rubric validation (1–5 scale)
4. Invalid/edge-case judge responses handling
5. Baseline execution (Rules Baseline & Retrieval Nearest-Neighbor)
6. Missing retrieval evidence handling
7. Escalation logic & security risk triage
8. Reproducibility & deterministic audit sampling (seed=42)
"""

import csv
import json
import random
import unittest
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.classifier.intent_classifier import LOCKED_INTENTS
from src.retrieval.retriever import AmazonHelpRetriever
from src.policy.escalation_policy import AmazonHelpEscalationPolicy
from src.generation.generator import AmazonHelpResponseGenerator
from src.agent.amazon_agent import AmazonHelpAgent
from src.baselines.baseline_rules import RuleTemplateBaseline
from src.baselines.baseline_retrieval_only import NearestNeighborBaseline
from src.evaluation.metrics import (
    compute_classification_metrics,
    compute_binary_metrics,
    compute_deterministic_response_checks,
    compute_retrieval_metrics,
    compute_latency_metrics,
)
from scripts.llm_judge import ResponseQualityJudge, validate_and_parse_judge_json
from src.api.services import EvaluationService


class TestEvaluationHarness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = AmazonHelpRetriever()
        cls.agent = AmazonHelpAgent(retriever=cls.retriever, evaluation_mode=True)
        cls.rules_baseline = RuleTemplateBaseline()
        cls.retrieval_baseline = NearestNeighborBaseline(retriever=cls.retriever, evaluation_mode=True)
        try:
            cls.judge = ResponseQualityJudge()
        except Exception:
            cls.judge = None
        cls.exclusions_path = ROOT_DIR / "eval/golden_thread_exclusions.json"
        cls.golden_path = ROOT_DIR / "eval/golden_eval_set_final.csv"

    # 1. Golden Leakage Exclusion Tests
    def test_golden_leakage_exclusion(self):
        self.assertTrue(self.exclusions_path.exists(), "Exclusions file missing")
        with open(self.exclusions_path, "r", encoding="utf-8") as f:
            exclusions = json.load(f)

        excluded_cids = set(str(x) for x in exclusions.get("excluded_conversation_ids", []))
        excluded_tids = set(str(x) for x in exclusions.get("excluded_tweet_ids", []))

        self.assertGreater(len(excluded_cids), 0)
        self.assertGreater(len(excluded_tids), 0)

        # In evaluation mode, retrieved results must never contain any excluded conversation or tweet
        results = self.retriever.search("where is my order package status", top_k=10, evaluation_mode=True)
        for r in results:
            self.assertNotIn(str(r["conversation_id"]), excluded_cids, "Leakage: Excluded conversation returned")
            for t in r.get("thread_tweets", []):
                self.assertNotIn(str(t), excluded_tids, "Leakage: Excluded tweet ID returned")

    # 2. Metric Calculations Tests
    def test_metric_calculations_classification(self):
        y_true = ["Delivery Tracking & Status", "Delivery Problem & Logistics", "Delivery Tracking & Status"]
        y_pred = ["Delivery Tracking & Status", "General / Feedback / Other", "Delivery Tracking & Status"]
        labels = LOCKED_INTENTS

        m = compute_classification_metrics(y_true, y_pred, labels)
        self.assertIn("accuracy", m)
        self.assertIn("macro_f1", m)
        self.assertIn("per_intent", m)
        self.assertIn("confusion_matrix", m)
        self.assertAlmostEqual(m["accuracy"], 2 / 3, places=3)
        self.assertIn("Delivery Tracking & Status", m["per_intent"])

    def test_metric_calculations_binary(self):
        y_true = [True, False, True, False]
        y_pred = [True, False, False, False]
        m = compute_binary_metrics(y_true, y_pred)
        self.assertEqual(m["accuracy"], 0.75)
        self.assertEqual(m["precision"], 1.0)
        self.assertEqual(m["recall"], 0.5)
        self.assertAlmostEqual(m["f1"], 2 / 3, places=3)

        # Zero-division safety test
        m_zero = compute_binary_metrics([False, False], [False, False])
        self.assertEqual(m_zero["precision"], 0.0)
        self.assertEqual(m_zero["recall"], 0.0)
        self.assertEqual(m_zero["f1"], 0.0)

    def test_metric_calculations_deterministic_checks(self):
        records = [
            {
                "main_agent_output": {
                    "draft_reply": "Please check your order status on your account page.",
                    "auto_handle": True,
                    "retrieved_evidence": [{"score": 0.3}],
                },
                "gold_escalate": False,
                "gold_security_alert": False,
            },
            {
                "main_agent_output": {
                    "draft_reply": "",  # empty failure
                    "auto_handle": False,
                    "retrieved_evidence": [],
                },
                "gold_escalate": True,
                "gold_security_alert": False,
            },
        ]
        checks = compute_deterministic_response_checks(records)
        self.assertEqual(checks["total_evaluated"], 2)
        self.assertEqual(checks["non_empty_count"], 1)
        self.assertEqual(checks["no_hallucination_rate"], 1.0)

    def test_metric_calculations_retrieval_and_latency(self):
        records = [
            {
                "retrieved_evidence": [{"score": 0.25}],
                "gold_intent": "Order & Checkout",
                "main_agent_output": {"intent": "Order & Checkout"},
            },
            {
                "retrieved_evidence": [],
                "gold_intent": "Order & Checkout",
                "main_agent_output": {"intent": "Order & Checkout"},
            },
        ]
        r_metrics = compute_retrieval_metrics(records)
        self.assertEqual(r_metrics["evidence_availability_rate"], 0.5)
        self.assertEqual(r_metrics["top_1_hit_rate"], 0.5)

        l_metrics = compute_latency_metrics([10.0, 20.0, 30.0, 40.0, 50.0])
        self.assertEqual(l_metrics["p50_latency_ms"], 30.0)
        self.assertGreaterEqual(l_metrics["p95_latency_ms"], 40.0)

    # 3. Judge JSON Parsing & Rubric Validation (1–5 scale)
    def test_judge_json_parsing(self):
        if self.judge is None:
            self.skipTest("Live LLM Judge API key not configured in environment")
        customer_msg = "Where is my package? It was supposed to arrive yesterday."
        agent_resp = (
            "Thanks for reaching out! You can track your package under 'Your Orders' on the Amazon app. "
            "If it shows as delayed, please send us a DM with your tracking ID so we can assist. ^AmazonHelp"
        )
        evidence = [{"customer_message": "track my order", "historical_response": "Please check Your Orders", "score": 0.4}]

        judge_out = self.judge.judge_response(
            customer_message=customer_msg,
            agent_response=agent_resp,
            retrieved_evidence=evidence,
            auto_handle=True,
            is_security_alert=False,
        )

        self.assertIn("scores", judge_out)
        self.assertIn("rationale", judge_out)
        for dim in ["correctness", "helpfulness", "groundedness", "policy", "escalation"]:
            score = judge_out["scores"][dim]
            self.assertTrue(1 <= score <= 5, f"Dimension {dim} score {score} outside [1, 5] rubric")

        # Top-level aliases for backward compatibility
        self.assertTrue(1.0 <= judge_out["overall_score"] <= 5.0)
        serialized = json.dumps(judge_out)
        self.assertIsInstance(serialized, str)

    # 4. Critical LLM Judge Unit Tests
    def test_missing_api_key_fails(self):
        """Verify that ResponseQualityJudge fails clearly when API key is missing, without heuristic fallback."""
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {"GEMINI_API_KEY": "", "GOOGLE_API_KEY": ""}, clear=True):
            with patch.object(ResponseQualityJudge, "_load_key_from_env_file", return_value=None):
                with self.assertRaises(ValueError) as ctx:
                    ResponseQualityJudge(api_key=None)
                self.assertIn("CRITICAL: Real LLM Judge requires GEMINI_API_KEY", str(ctx.exception))
                self.assertIn("local heuristic fallback is disabled", str(ctx.exception))

    def test_malformed_judge_json(self):
        """Verify that malformed or non-JSON judge output raises ValueError."""
        with self.assertRaises(ValueError):
            validate_and_parse_judge_json("Not a JSON string at all")

        with self.assertRaises(ValueError):
            validate_and_parse_judge_json("[]")

        with self.assertRaises(ValueError):
            validate_and_parse_judge_json('{"scores": {"correctness": "invalid_number"}}')

    def test_valid_judge_json(self):
        """Verify that valid structured judge JSON parses into standardized schema."""
        raw_json = json.dumps({
            "scores": {
                "correctness": 5,
                "helpfulness": 4,
                "groundedness": 5,
                "policy": 5,
                "escalation": 4
            },
            "rationale": "High quality policy-compliant response with accurate guidance."
        })
        res = validate_and_parse_judge_json(raw_json)
        self.assertIn("scores", res)
        self.assertIn("rationale", res)
        self.assertEqual(res["scores"]["correctness"], 5)
        self.assertEqual(res["scores"]["helpfulness"], 4)
        self.assertEqual(res["scores"]["groundedness"], 5)
        self.assertEqual(res["scores"]["policy"], 5)
        self.assertEqual(res["scores"]["escalation"], 4)
        self.assertEqual(res["rationale"], "High quality policy-compliant response with accurate guidance.")

    def test_score_range_validation(self):
        """Verify that judge scores outside [1, 5] raise ValueError."""
        out_of_bounds_cases = [
            {"correctness": 0, "helpfulness": 3, "groundedness": 3, "policy": 3, "escalation": 3},
            {"correctness": 6, "helpfulness": 3, "groundedness": 3, "policy": 3, "escalation": 3},
            {"correctness": 3, "helpfulness": -1, "groundedness": 3, "policy": 3, "escalation": 3},
            {"correctness": 3, "helpfulness": 3, "groundedness": 10, "policy": 3, "escalation": 3},
        ]
        for scores in out_of_bounds_cases:
            with self.assertRaises(ValueError):
                validate_and_parse_judge_json(json.dumps({"scores": scores}))

    def test_dashboard_reads_actual_stored_scores(self):
        """Verify that EvaluationService reads actual stored judge_evaluation.scores without hardcoded fallback defaults."""
        summary = EvaluationService.get_summary()
        self.assertIn("judge_quality_rubric", summary)
        rubric = summary["judge_quality_rubric"]
        for dim in ["correctness", "helpfulness", "groundedness", "policy_compliance", "escalation_appropriateness"]:
            self.assertIn(dim, rubric)
            self.assertTrue(1.0 <= rubric[dim] <= 5.0, f"Rubric {dim} = {rubric[dim]} outside [1.0, 5.0]")

    # 5. Baseline Execution Tests
    def test_baseline_execution(self):
        msg = "I need to return an item that arrived broken."
        
        # Baseline 1
        b1_res = self.rules_baseline.process_message(msg)
        self.assertIn("intent", b1_res)
        self.assertIn(b1_res["intent"], LOCKED_INTENTS)
        self.assertIn("draft_reply", b1_res)
        self.assertGreater(len(b1_res["draft_reply"]), 0)

        # Baseline 2
        b2_res = self.retrieval_baseline.process_message(msg)
        self.assertIn("intent", b2_res)
        self.assertIn(b2_res["intent"], LOCKED_INTENTS)
        self.assertIn("draft_reply", b2_res)
        self.assertGreater(len(b2_res["draft_reply"]), 0)

    # 6. Missing Retrieval Evidence Handling
    def test_missing_retrieval_evidence(self):
        # Even with empty evidence, agent must succeed without exception
        res = self.agent.process_message("random unmatchable query xyzqwerty12345", top_k_evidence=0)
        self.assertIn("draft_reply", res)
        self.assertIn("auto_handle", res)
        self.assertIsInstance(res["retrieved_evidence"], list)

    # 7. Escalation Logic & Security Risk Triage
    def test_escalation_logic(self):
        # Security breach must trigger P0 critical escalation
        sec_msg = "Help! Someone hacked into my Amazon account and changed my password and email!"
        sec_res = self.agent.process_message(sec_msg)
        self.assertTrue(sec_res["is_security_alert"], "Failed to flag security alert")
        self.assertEqual(sec_res["priority"], "P0_CRITICAL")
        self.assertFalse(sec_res["auto_handle"], "Security breach must not be auto-handled")
        self.assertIn("security", sec_res["escalation_reason"].lower())

    # 8. Reproducibility & Deterministic Audit Sampling
    def test_reproducibility(self):
        self.assertTrue(self.golden_path.exists())
        with open(self.golden_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.assertEqual(len(rows), 200, "Golden set must contain exactly 200 examples")

        # Sampling 50 examples with fixed seed=42
        rng1 = random.Random(42)
        sample1 = sorted(rng1.sample(range(len(rows)), 50))

        rng2 = random.Random(42)
        sample2 = sorted(rng2.sample(range(len(rows)), 50))

        self.assertEqual(sample1, sample2, "Sampling with seed 42 must be strictly deterministic")

        # Verify audit CSV matches the exact sampled message IDs
        audit_csv_path = ROOT_DIR / "eval/judge_human_audit.csv"
        self.assertTrue(audit_csv_path.exists())
        with open(audit_csv_path, "r", encoding="utf-8") as f:
            audit_rows = list(csv.DictReader(f))

        self.assertEqual(len(audit_rows), 50, "Audit CSV must contain exactly 50 examples")
        expected_mids = [str(rows[i]["message_id"]) for i in sample1]
        actual_mids = [str(r["message_id"]) for r in audit_rows]
        self.assertEqual(actual_mids, expected_mids, "Audit CSV must match deterministic seed=42 sample")

        # Verify human columns (valid 1-5 ratings when populated)
        for r in audit_rows:
            if r["human_correctness"].strip():
                self.assertIn(int(r["human_correctness"]), [1, 2, 3, 4, 5])
                self.assertIn(int(r["human_helpfulness"]), [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
