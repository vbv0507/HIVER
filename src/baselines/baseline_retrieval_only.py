"""
Baseline 2: Retrieval-Only Nearest Historical Response Baseline

Direct nearest-neighbor baseline: retrieves the single most similar historical
customer query and copies the historical AmazonHelp response directly without
generation or escalation policies.
"""

import re
import sys
from pathlib import Path
from typing import Dict, Any, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.retrieval.retriever import AmazonHelpRetriever


class NearestNeighborBaseline:
    """
    Baseline 2: Pure retrieval nearest-neighbor baseline.
    """

    def __init__(self, retriever: Optional[AmazonHelpRetriever] = None, evaluation_mode: bool = True):
        self.retriever = retriever if retriever is not None else AmazonHelpRetriever()
        self.evaluation_mode = evaluation_mode

    def process_message(self, customer_text: str) -> Dict[str, Any]:
        retrieved = self.retriever.search(
            query=customer_text,
            top_k=1,
            evaluation_mode=self.evaluation_mode,
        )

        if not retrieved:
            return {
                "intent": "General / Feedback / Other",
                "confidence": 0.20,
                "language": "en",
                "conversation_state": "new_issue",
                "auto_handle": True,
                "escalation_reason": "None. No retrieval match found.",
                "draft_reply": "Thanks for contacting Amazon. Please check 'Your Orders' or contact us for help. ^AmazonHelp",
                "retrieved_evidence": [],
            }

        top_match = retrieved[0]
        raw_resp = top_match["historical_response"]

        # Clean off foreign @handles from historical response
        clean_resp = re.sub(r"^@\w+\s*", "", raw_resp).strip()

        return {
            "intent": top_match.get("intent", "General / Feedback / Other"),
            "confidence": float(top_match["score"]),
            "language": "en",
            "conversation_state": "new_issue",
            "auto_handle": True,
            "escalation_reason": "None. Copied nearest historical response directly.",
            "draft_reply": clean_resp,
            "retrieved_evidence": [
                {
                    "conversation_id": str(top_match["conversation_id"]),
                    "customer_message": str(top_match["customer_message"]),
                    "historical_response": str(top_match["historical_response"]),
                    "score": float(top_match["score"]),
                }
            ],
        }
