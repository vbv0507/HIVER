"""
Baseline 1: Rule-Based Classifier + Static Template Response

A non-retrieval heuristic baseline using keyword matching to pick one of the 10 intents
and return a static template response.
"""

import re
from typing import Dict, Any, List

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

STATIC_TEMPLATES = {
    "Delivery Tracking & Status": "You can track your delivery in 'Your Orders' > 'Track Package'. Let us know if you need more help! ^AmazonHelp",
    "Delivery Problem & Logistics": "We're sorry your package is delayed or missing. Please contact customer service with your order ID. ^AmazonHelp",
    "Returns, Replacements & Refunds": "To return an item or request a refund, please visit our Online Returns Center under 'Your Orders'. ^AmazonHelp",
    "Payment, Billing & Gift Cards": "For payment and billing issues, please review your payment methods under 'Your Account'. ^AmazonHelp",
    "Prime & Subscription Services": "You can manage or cancel your Amazon Prime membership under 'Your Account' > 'Prime'. ^AmazonHelp",
    "Order & Checkout": "You can view or cancel unshipped items in 'Your Orders'. ^AmazonHelp",
    "Account Access & Security": "If you are having trouble signing in, please use the password assistance page on our website. ^AmazonHelp",
    "Digital Services & Devices": "Please try restarting your Amazon device or re-installing the application to resolve playback issues. ^AmazonHelp",
    "Seller & Product Quality": "For items sold by third-party sellers, you can contact the seller directly through 'Your Orders'. ^AmazonHelp",
    "General / Feedback / Other": "Thank you for reaching out to Amazon. Please let us know how we can help you today! ^AmazonHelp",
}


class RuleTemplateBaseline:
    """
    Baseline 1: Rule-based intent classifier + static template response.
    """

    def __init__(self):
        pass

    def classify_intent(self, text: str) -> str:
        t = text.lower()
        if re.search(r"\b(where is|track(ing)?|eta|shipped)\b", t):
            return "Delivery Tracking & Status"
        if re.search(r"\b(delay|late|missing|not received|never received)\b", t):
            return "Delivery Problem & Logistics"
        if re.search(r"\b(return|refund|replacement|replace)\b", t):
            return "Returns, Replacements & Refunds"
        if re.search(r"\b(charge|charged|double|invoice|billing|gift card)\b", t):
            return "Payment, Billing & Gift Cards"
        if re.search(r"\b(prime|membership|subscription)\b", t):
            return "Prime & Subscription Services"
        if re.search(r"\b(cancel order|checkout|cart|promo)\b", t):
            return "Order & Checkout"
        if re.search(r"\b(password|login|hacked|sign in|otp)\b", t):
            return "Account Access & Security"
        if re.search(r"\b(kindle|fire|echo|alexa|app|device)\b", t):
            return "Digital Services & Devices"
        if re.search(r"\b(seller|fake|defective|damaged product)\b", t):
            return "Seller & Product Quality"
        return "General / Feedback / Other"

    def process_message(self, customer_text: str) -> Dict[str, Any]:
        intent = self.classify_intent(customer_text)
        reply = STATIC_TEMPLATES.get(intent, STATIC_TEMPLATES["General / Feedback / Other"])

        return {
            "intent": intent,
            "confidence": 0.50,
            "language": "en",
            "conversation_state": "new_issue",
            "auto_handle": True,
            "escalation_reason": "None. Baseline rule matched.",
            "draft_reply": reply,
            "retrieved_evidence": [],
        }
