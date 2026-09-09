"""
Step 3 Test Suite: AmazonHelp AI Support Agent

Tests:
1. Intent classification across locked 10-intent taxonomy
2. Retrieval pipeline & metadata preservation
3. Mandatory golden-set leakage filtering
4. Escalation policy triggers (Security P0, financial disputes, human requests)
5. Structured output contract validation
6. Baseline execution (Baseline 1 & 2)
"""

import json
import unittest
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.classifier.intent_classifier import AmazonHelpIntentClassifier, LOCKED_INTENTS
from src.retrieval.retriever import AmazonHelpRetriever
from src.policy.escalation_policy import AmazonHelpEscalationPolicy
from src.generation.generator import AmazonHelpResponseGenerator
from src.agent.amazon_agent import AmazonHelpAgent
from src.baselines.baseline_rules import RuleTemplateBaseline
from src.baselines.baseline_retrieval_only import NearestNeighborBaseline


class TestAmazonHelpAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classifier = AmazonHelpIntentClassifier()
        cls.retriever = AmazonHelpRetriever()
        cls.policy = AmazonHelpEscalationPolicy()
        cls.generator = AmazonHelpResponseGenerator()
        cls.agent = AmazonHelpAgent(retriever=cls.retriever, evaluation_mode=True)

    # 1. Intent Classification Tests
    def test_intent_classification_taxonomy(self):
        test_cases = [
            ("Where is my package? Can you track my order?", "Delivery Tracking & Status"),
            ("My delivery is three days late and never arrived!", "Delivery Problem & Logistics"),
            ("I want to return this item and get a full refund.", "Returns, Replacements & Refunds"),
            ("You charged my credit card twice for this order!", "Payment, Billing & Gift Cards"),
            ("How do I cancel my Amazon Prime annual subscription?", "Prime & Subscription Services"),
            ("I cannot checkout because the promo code failed.", "Order & Checkout"),
            ("Someone hacked my Amazon account and changed my email!", "Account Access & Security"),
            ("My Kindle Fire TV stick is frozen and apps crash.", "Digital Services & Devices"),
            ("The third-party seller sent a fake counterfeit item.", "Seller & Product Quality"),
            ("Thank you for the information, have a great day!", "General / Feedback / Other"),
        ]

        for text, expected_intent in test_cases:
            res = self.classifier.classify(text)
            self.assertIn(res["intent"], LOCKED_INTENTS, f"Intent {res['intent']} not in locked taxonomy")
            self.assertEqual(res["intent"], expected_intent, f"Failed for '{text}': got {res['intent']}, expected {expected_intent}")
            self.assertTrue(0.0 <= res["confidence"] <= 1.0, "Confidence score out of [0, 1] range")

    # 2. Golden-Set Leakage Filtering
    def test_golden_set_leakage_protection(self):
        exclusions_path = Path("eval/golden_thread_exclusions.json")
        self.assertTrue(exclusions_path.exists(), "golden_thread_exclusions.json must exist")

        with open(exclusions_path, "r", encoding="utf-8") as f:
            ex_data = json.load(f)

        excluded_convs = set(str(c) for c in ex_data.get("excluded_conversation_ids", []))
        excluded_tweets = set(str(t) for t in ex_data.get("excluded_tweet_ids", []))

        # Query known golden set phrases in evaluation mode
        results = self.retriever.search("Never got the beta and now I am told I wont get the stuff", top_k=10, evaluation_mode=True)

        for r in results:
            self.assertNotIn(
                str(r["conversation_id"]),
                excluded_convs,
                f"Leakage detected! Retrieved excluded conversation ID {r['conversation_id']}"
            )

    # 3. Escalation Policy Tests
    def test_security_alert_always_escalates(self):
        sec_query = "Someone hacked my account and made unauthorized charges!"
        res = self.agent.process_message(sec_query)
        self.assertFalse(res["auto_handle"], "Security alerts MUST NOT be auto-handled")
        self.assertIn("security", res["escalation_reason"].lower(), "Escalation reason must state security")

    def test_human_request_escalates(self):
        human_query = "I want to speak with a human agent right now."
        res = self.agent.process_message(human_query)
        self.assertFalse(res["auto_handle"], "Explicit human requests must escalate")
        self.assertIn("human", res["escalation_reason"].lower())

    def test_routine_query_auto_handled(self):
        routine_query = "Where is my package? The tracking number is 987123"
        res = self.agent.process_message(routine_query)
        self.assertTrue(res["auto_handle"], "Routine tracking inquiries should be auto-handled")

    def test_security_phishing_and_takeover_paraphrases(self):
        """Verify generalized security and phishing detection across natural phrasing variations."""
        queries = [
            "I received a fake Amazon SMS asking for my bank details.",
            "Got a suspicious text from Amazon demanding my card details.",
            "Someone sent a phishing email pretending to be Amazon asking for my password.",
            "I got a bogus message with a link asking for my bank account and routing number.",
            "Someone hacked my Amazon account and changed my email.",
            "My account was compromised and the unauthorized user changed my phone number.",
            "Someone hijacked my account and placed orders without my permission.",
        ]
        for q in queries:
            res = self.agent.process_message(q)
            self.assertEqual(
                res["intent"],
                "Account Access & Security",
                f"Expected 'Account Access & Security' for '{q}', got '{res['intent']}'",
            )
            self.assertTrue(
                res["is_security_alert"],
                f"Expected is_security_alert=True for '{q}'",
            )
            self.assertEqual(
                res["priority"],
                "P0_CRITICAL",
                f"Expected priority='P0_CRITICAL' for '{q}'",
            )
            self.assertFalse(
                res["auto_handle"],
                f"Expected auto_handle=False for '{q}'",
            )
            self.assertIn(
                "security",
                res["escalation_reason"].lower(),
                f"Expected security mention in escalation reason for '{q}'",
            )
            # Safe generation assertions
            reply = res["draft_reply"].lower()
            self.assertNotIn("password", reply[:30])
            self.assertIn("direct message", reply)

    def test_financial_duplicate_charge_paraphrases(self):
        """Verify conservative escalation for duplicate charges and billing disputes across phrasing variations."""
        queries = [
            "I was charged twice for Prime membership.",
            "There is a duplicate charge of $14.99 on my credit card.",
            "You billed me double this month and deducted money twice.",
            "Why was my debit card charged two times for the same transaction?",
            "My bank statement shows repeated charges for the same order.",
        ]
        for q in queries:
            res = self.agent.process_message(q)
            self.assertEqual(
                res["intent"],
                "Payment, Billing & Gift Cards",
                f"Expected 'Payment, Billing & Gift Cards' for '{q}', got '{res['intent']}'",
            )
            self.assertFalse(
                res["is_security_alert"],
                f"Expected is_security_alert=False for '{q}'",
            )
            self.assertFalse(
                res["auto_handle"],
                f"Expected auto_handle=False for '{q}'",
            )
            self.assertIn(
                "charge",
                res["escalation_reason"].lower(),
                f"Expected charge/dispute mention in escalation reason for '{q}'",
            )
            # Verify response generation doesn't make false assertions or ask for card numbers publicly
            reply = res["draft_reply"].lower()
            self.assertNotIn("i have refunded", reply)
            self.assertNotIn("i have checked your account", reply)
            self.assertIn("direct message", reply)
            self.assertIn("not post sensitive", reply)

    # 4. Structured Output Contract
    def test_output_contract_schema(self):
        query = "How do I return a damaged jacket for a replacement?"
        res = self.agent.process_message(query)

        required_keys = [
            "intent",
            "confidence",
            "language",
            "conversation_state",
            "auto_handle",
            "escalation_reason",
            "draft_reply",
            "retrieved_evidence",
        ]

        for k in required_keys:
            self.assertIn(k, res, f"Missing key '{k}' in output contract")

        self.assertIsInstance(res["intent"], str)
        self.assertIn(res["intent"], LOCKED_INTENTS)
        self.assertIsInstance(res["confidence"], float)
        self.assertIsInstance(res["language"], str)
        self.assertIsInstance(res["conversation_state"], str)
        self.assertIsInstance(res["auto_handle"], bool)
        self.assertIsInstance(res["escalation_reason"], str)
        self.assertIsInstance(res["draft_reply"], str)
        self.assertIsInstance(res["retrieved_evidence"], list)

        if res["retrieved_evidence"]:
            ev = res["retrieved_evidence"][0]
            for ev_k in ["conversation_id", "customer_message", "historical_response", "score"]:
                self.assertIn(ev_k, ev, f"Missing key '{ev_k}' in retrieved evidence record")

    # 5. Baseline Execution Tests
    def test_baselines_runnable(self):
        b1 = RuleTemplateBaseline()
        out1 = b1.process_message("Where is my package?")
        self.assertEqual(out1["intent"], "Delivery Tracking & Status")
        self.assertIn("track", out1["draft_reply"].lower())

        b2 = NearestNeighborBaseline(retriever=self.retriever, evaluation_mode=True)
        out2 = b2.process_message("Where is my package?")
        self.assertIn("draft_reply", out2)
        self.assertTrue(len(out2["draft_reply"]) > 0)


if __name__ == "__main__":
    unittest.main()
