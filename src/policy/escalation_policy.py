"""
Step 3: AmazonHelp Escalation Policy Engine

Determines auto_handle (True/False) and provides explicit escalation reasons.
Enforces strict rules for security alerts, financial disputes, human intervention requests,
insufficient evidence, and ambiguity.
"""

import re
from typing import Dict, Any, List, Tuple


class AmazonHelpEscalationPolicy:
    """
    Evaluates customer requests, classifier output, and retrieved evidence to decide
    whether the issue can be safely auto-handled or must be escalated to a human specialist.
    """

    def __init__(self, min_evidence_score: float = 0.12, min_confidence: float = 0.40):
        self.min_evidence_score = min_evidence_score
        self.min_confidence = min_confidence

        # Patterns demanding explicit human contact
        self.human_request_pattern = re.compile(
            r"\b(human|agent|representative|real person|speak to (someone|a human)|talk to (someone|a person)|supervisor|advisor|manager)\b",
            re.IGNORECASE,
        )

        # High-risk financial & dispute patterns (generalized across multiple natural phrasings)
        self.high_risk_financial_pattern = re.compile(
            r"\b("
            r"(charg(ed?|ing)?|bill(ed?|ing)?|debit(ed)?|deduct(ed)?)\s+.*?\b(twice|double|again|two\s+times|multiple\s+times|repeatedly)\b|"
            r"\b(double|duplicate|repeat(ed)?|second|extra|two)\s+(charge[s]?|billing|debit[s]?|payment[s]?|fee[s]?|transactions?)\b|"
            r"\bseeing\s+(double|two|multiple)\s+charges\b|"
            r"\b(unauthorized|unrecognized|unknown|fraudulent|incorrect|disputed?|wrong|unexpected)\s+(charge[s]?|billing|debit[s]?|payment[s]?|fee[s]?|transactions?)\b|"
            r"\b(charg(ed?|ing)?|bill(ed?|ing)?)\s+without\s+(my\s+)?(permission|consent|knowledge|ordering)\b|"
            r"\bdidn'?t\s+authorize\s+this\b|"
            r"\bovercharg(ed?|ing)?\b|\bcharged\s+(too\s+much|more\s+than|extra)\b|"
            r"\b(credit\s+card\s+fraud|stolen\s+card|bank\s+dispute|chargeback|stolen\s+money|police|lawyer|sue|legal\s+action)\b"
            r")",
            re.IGNORECASE,
        )

        # Privileged account intervention patterns
        self.privileged_action_pattern = re.compile(
            r"\b(unban|reinstate account|cancel order.*already shipped|change delivery address.*in transit|manual refund|override)\b",
            re.IGNORECASE,
        )

    def evaluate(
        self,
        customer_text: str,
        classification: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
    ) -> Tuple[bool, str]:
        """
        Returns (auto_handle: bool, escalation_reason: str).
        """
        intent = classification.get("intent", "General / Feedback / Other")
        confidence = float(classification.get("confidence", 0.0))
        is_security = bool(classification.get("is_security_alert", False))
        conv_state = classification.get("conversation_state", "new_issue")

        # 1. Mandatory Security Alert Trigger (P0_CRITICAL)
        if is_security:
            return (
                False,
                "CRITICAL P0: Suspected account takeover, phishing communication, or security breach requires human specialist investigation.",
            )

        # 2. Customer explicitly requests human intervention
        if self.human_request_pattern.search(customer_text):
            return (
                False,
                "Customer explicitly requested to communicate with a human agent or representative.",
            )

        # 3. High-risk financial dispute, duplicate charge, or unauthorized transaction
        if self.high_risk_financial_pattern.search(customer_text):
            return (
                False,
                "High-risk financial dispute, duplicate charge, or unauthorized transaction requires verified account investigation.",
            )

        # 4. Privileged internal action required (beyond automated agent capabilities)
        if self.privileged_action_pattern.search(customer_text):
            return (
                False,
                "Action requires internal account privileges (e.g. manual dispatch rerouting or account unblocking).",
            )

        # 5. DM handoff / ongoing agent conversation state
        if conv_state == "dm_handoff":
            return (
                False,
                "Conversation state indicates active private DM handoff with human support.",
            )

        # 6. Low classification confidence / Ambiguity
        if confidence < self.min_confidence:
            return (
                False,
                f"Customer intent is ambiguous (classifier confidence {confidence:.2f} < {self.min_confidence:.2f}).",
            )

        # 7. Insufficient retrieval evidence
        if not retrieved_evidence:
            return (
                False,
                "No relevant historical resolution evidence found in knowledge base.",
            )

        top_score = retrieved_evidence[0].get("score", 0.0)
        if top_score < self.min_evidence_score:
            return (
                False,
                f"Top retrieved resolution evidence relevance score ({top_score:.2f}) is below confidence threshold ({self.min_evidence_score:.2f}).",
            )

        # 8. Intent-Specific Escalation Constraints:
        # Delivery Problem & Logistics with damaged/missing claims often requires courier claim filing
        if intent == "Delivery Problem & Logistics":
            if re.search(r"\b(stolen|lost|damaged|broken|courier stole|never showed up)\b", customer_text, re.IGNORECASE):
                # If courier investigation is explicitly indicated
                if re.search(r"\b(investigation|claim|report|police)\b", customer_text, re.IGNORECASE):
                    return (
                        False,
                        "Delivery logistics issue requires filing a carrier claim or investigation.",
                    )

        # Seller & Product Quality with counterfeit or unresponsive seller
        if intent == "Seller & Product Quality":
            if re.search(r"\b(fake|counterfeit|scam|unresponsive seller|seller won't reply|won't refund)\b", customer_text, re.IGNORECASE):
                return (
                    False,
                    "Third-party marketplace dispute or suspected counterfeit item requires A-to-z Guarantee claim review.",
                )

        # Routine Informational Queries Safe for Auto-Handling:
        # - Delivery tracking inquiries with valid evidence
        # - Return instructions / online returns center navigation
        # - Prime cancellation self-service navigation
        # - Basic device/app restart instructions
        return (
            True,
            f"None. Routine informational request for '{intent}' safely addressed via verified historical guidance.",
        )
