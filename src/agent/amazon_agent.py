"""
Step 3: Main AmazonHelp AI Support Agent

Integrates:
1. AmazonHelpIntentClassifier (locked 10 intents, confidence, language, state, security alert)
2. AmazonHelpRetriever (historical resolution evidence with golden-set leakage filter)
3. AmazonHelpEscalationPolicy (auto_handle decision + explicit escalation reason)
4. AmazonHelpResponseGenerator (grounded, transparent customer-facing reply)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.classifier.intent_classifier import AmazonHelpIntentClassifier
from src.retrieval.retriever import AmazonHelpRetriever
from src.policy.escalation_policy import AmazonHelpEscalationPolicy
from src.generation.generator import AmazonHelpResponseGenerator


class AmazonHelpAgent:
    """
    Production-ready AI customer-support agent for AmazonHelp.
    """

    def __init__(
        self,
        retriever: Optional[AmazonHelpRetriever] = None,
        evaluation_mode: bool = True,
    ):
        self.evaluation_mode = evaluation_mode
        self.classifier = AmazonHelpIntentClassifier()
        self.retriever = retriever if retriever is not None else AmazonHelpRetriever()
        self.policy = AmazonHelpEscalationPolicy()
        self.generator = AmazonHelpResponseGenerator()

    def process_message(
        self,
        customer_text: str,
        top_k_evidence: int = 3,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end agent inference on incoming customer message.
        Guarantees exact output contract.
        """
        clean_text = customer_text.strip()

        # 1. Classify intent, language, conversation state, security alert
        classification = self.classifier.classify(clean_text)

        # 2. Retrieve relevant historical resolution pairs
        retrieved = self.retriever.search(
            query=clean_text,
            top_k=top_k_evidence,
            intent_filter=classification["intent"],
            evaluation_mode=self.evaluation_mode,
        )

        # 3. Format evidence for contract
        evidence_list = []
        for r in retrieved:
            evidence_list.append({
                "conversation_id": str(r["conversation_id"]),
                "customer_message": str(r["customer_message"]),
                "historical_response": str(r["historical_response"]),
                "score": float(r["score"]),
            })

        # 4. Evaluate escalation policy
        auto_handle, escalation_reason = self.policy.evaluate(
            customer_text=clean_text,
            classification=classification,
            retrieved_evidence=evidence_list,
        )

        # 5. Generate grounded response draft
        draft_reply = self.generator.generate(
            customer_text=clean_text,
            classification=classification,
            retrieved_evidence=evidence_list,
            auto_handle=auto_handle,
            escalation_reason=escalation_reason,
        )

        # 6. Return exact structured output contract
        return {
            "intent": classification["intent"],
            "confidence": classification["confidence"],
            "language": classification["language"],
            "conversation_state": classification["conversation_state"],
            "is_security_alert": classification["is_security_alert"],
            "priority": classification["priority"],
            "auto_handle": auto_handle,
            "escalation_reason": escalation_reason,
            "draft_reply": draft_reply,
            "retrieved_evidence": evidence_list,
        }
