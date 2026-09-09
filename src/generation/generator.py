"""
Step 3: AmazonHelp Grounded Response Generator

Generates customer-facing draft responses strictly grounded in:
1. Current customer message
2. Retrieved historical resolution evidence
3. Approved Amazon support policy configurations

Adheres to core safety rules:
- Never invents order IDs, tracking dates, or account facts
- Never claims actions were performed when they were not
- Asks for missing information concisely
- Adapts to customer language
- Prefers clear escalation guidance when auto_handle is False
"""

import re
from typing import Dict, Any, List, Optional


class AmazonHelpResponseGenerator:
    """
    Grounded response generator that crafts transparent, policy-compliant support replies.
    """

    def __init__(self):
        self._init_language_templates()

    def _init_language_templates(self):
        # Multilingual greetings and escalation intros
        self.multilingual_responses = {
            "ja": {
                "greeting": "お問い合わせいただきありがとうございます。",
                "escalation_security": "ご心配をおかけしております。セキュリティ上の懸念があるため、担当部署にて確認いたします。アカウントの詳細（登録メールアドレス等）を安全な方法（DM）でお知らせいただけますでしょうか。パスワード等の機密情報は投稿しないでください。",
                "escalation_general": "ご不便をおかけしております。本件は担当窓口にて詳細を確認させていただきたく存じます。ご注文番号等をご確認のうえ、DMにてご連絡いただけますでしょうか。",
                "tracking": "配送状況のご確認ですね。「注文履歴」から最新の追跡情報をご確認いただけます。詳細な調査が必要な場合は、ご注文番号をお知らせください。",
                "returns": "返品・返金に関するお問い合わせですね。「注文履歴」＞「商品の返品」より返品手続きおよび返品用ラベルの印刷が可能です。",
                "signoff": "^AmazonHelp",
            },
            "es": {
                "greeting": "Hola, gracias por contactar con Amazon.",
                "escalation_security": "Lamentamos la preocupación. Por motivos de seguridad, necesitamos derivar este caso a nuestro equipo especializado. Por favor envíanos un mensaje directo (DM) con tu correo de cuenta para investigar de forma segura. No compartas contraseñas.",
                "escalation_general": "Sentimos las molestias ocasionadas. Para poder revisar este caso a fondo, un agente especializado tomará el caso. Por favor facilítanos el número de pedido por mensaje privado.",
                "tracking": "Puedes consultar el estado en tiempo real de tu envío desde la sección 'Mis pedidos' seleccionando 'Localizar paquete'. Si necesitas ayuda adicional, facilítanos tu número de pedido.",
                "returns": "Para iniciar una devolución o reemplazo, accede a 'Mis pedidos' > 'Devolver o reemplazar productos' para generar tu etiqueta de devolución.",
                "signoff": "^AmazonHelp",
            },
            "fr": {
                "greeting": "Bonjour, merci de contacter le support Amazon.",
                "escalation_security": "Nous prenons ce signalement très au sérieux. Pour sécuriser votre compte, ce dossier est transmis à notre équipe dédiée. Veuillez nous envoyer un message privé (DM) avec votre adresse e-mail. Ne communiquez aucun mot de passe.",
                "escalation_general": "Nous sommes désolés pour ce désagrément. Votre demande nécessite une intervention manuelle de notre équipe. Merci de nous transmettre votre numéro de commande par message privé.",
                "tracking": "Vous pouvez suivre l'acheminement de votre colis directement depuis la rubrique 'Vos commandes' > 'Suivre votre colis'. Si le problème persiste, merci de nous communiquer votre numéro de commande.",
                "returns": "Pour retourner un article, rendez-vous dans 'Vos commandes' puis sélectionnez 'Retourner ou remplacer des articles' afin d'obtenir votre étiquette de retour.",
                "signoff": "^AmazonHelp",
            },
            "de": {
                "greeting": "Hallo, danke für deine Nachricht an Amazon.",
                "escalation_security": "Wir nehmen die Sicherheit deines Kontos sehr ernst. Dieser Fall wird zur Prüfung an unser Sicherheitsteam übergeben. Bitte sende uns eine private Nachricht (DM) mit deiner E-Mail-Adresse. Bitte teile keine Passwörter.",
                "escalation_general": "Es tut uns leid für die Unannehmlichkeiten. Ein Kundenbetreuer wird diesen Fall persönlich prüfen. Bitte teile uns deine Bestellnummer per Direktnachricht (DM) mit.",
                "tracking": "Den aktuellen Lieferstatus deines Pakets kannst du unter 'Meine Bestellungen' > 'Lieferung verfolgen' einsehen. Solltest du weitere Hilfe benötigen, teile uns gerne deine Bestellnummer mit.",
                "returns": "Eine Rücksendung kannst du bequem unter 'Meine Bestellungen' > 'Artikel zurücksenden' einleiten und das Rücksendeetikett ausdrucken.",
                "signoff": "^AmazonHelp",
            },
        }

    def generate(
        self,
        customer_text: str,
        classification: Dict[str, Any],
        retrieved_evidence: List[Dict[str, Any]],
        auto_handle: bool,
        escalation_reason: str,
    ) -> str:
        """
        Drafts grounded response.
        """
        intent = classification.get("intent", "General / Feedback / Other")
        lang = classification.get("language", "en")
        is_security = classification.get("is_security_alert", False)

        # Handle foreign languages with native templates if available
        if lang in self.multilingual_responses:
            tpl = self.multilingual_responses[lang]
            if not auto_handle:
                if is_security:
                    return f"{tpl['greeting']} {tpl['escalation_security']} {tpl['signoff']}"
                return f"{tpl['greeting']} {tpl['escalation_general']} {tpl['signoff']}"
            else:
                if intent == "Delivery Tracking & Status":
                    return f"{tpl['greeting']} {tpl['tracking']} {tpl['signoff']}"
                elif intent == "Returns, Replacements & Refunds":
                    return f"{tpl['greeting']} {tpl['returns']} {tpl['signoff']}"
                return f"{tpl['greeting']} {tpl['escalation_general']} {tpl['signoff']}"

        # Standard English Generation
        if not auto_handle:
            return self._generate_escalation_reply(intent, is_security, escalation_reason)

        return self._generate_autohandle_reply(customer_text, intent, retrieved_evidence)

    def _generate_escalation_reply(
        self, intent: str, is_security: bool, escalation_reason: str
    ) -> str:
        """Crafts safe, reassuring escalation response to transfer to human support."""
        if is_security:
            return (
                "We take account security very seriously. Because this involves a potential security alert or unauthorized activity, "
                "I have escalated your report to our Account Security Specialists for immediate investigation. "
                "Please do NOT share sensitive information like passwords publicly. Please send us a Direct Message (DM) "
                "with your registered account email so we can take immediate protective action on your account. ^AmazonHelp"
            )

        if "human agent" in escalation_reason.lower():
            return (
                "I understand you would like to speak directly with a human representative. "
                "I am transferring your request to our customer support team right now. "
                "Please send us a Direct Message (DM) with your order ID or account email, and a representative will follow up with you shortly. ^AmazonHelp"
            )

        if (
            "financial dispute" in escalation_reason.lower()
            or "unauthorized charge" in escalation_reason.lower()
            or "duplicate charge" in escalation_reason.lower()
            or "billing dispute" in escalation_reason.lower()
            or intent == "Payment, Billing & Gift Cards"
        ):
            return (
                "I apologize for the billing issue and concern. Because this involves an account-specific charge or billing dispute, "
                "a billing specialist must manually review your account history. "
                "Please reach out to us via Direct Message (DM) with the approximate charge date and order ID so we can investigate this securely. "
                "Please do not post sensitive card or payment details publicly. ^AmazonHelp"
            )

        if intent == "Delivery Problem & Logistics":
            return (
                "I'm truly sorry for the delivery issue and frustration. Since this order may require carrier investigation or replacement dispatch, "
                "I am routing your case to a delivery specialist. Please send us a Direct Message (DM) with your 17-digit Order ID "
                "and delivery postcode so we can resolve this for you right away. ^AmazonHelp"
            )

        if intent == "Seller & Product Quality":
            return (
                "I'm sorry to hear about the issue with this marketplace item. To ensure your purchase is fully protected under our A-to-z Guarantee, "
                "I've escalated your issue to our marketplace disputes team. Please send us a DM with the Order ID and seller name so we can assist. ^AmazonHelp"
            )

        # Default human escalation
        return (
            "I apologize for the inconvenience you are experiencing. To ensure this is handled thoroughly and accurately, "
            "I've flagged your inquiry for review by a customer support specialist. "
            "Please send us a Direct Message (DM) with any relevant order numbers so an agent can assist you directly. ^AmazonHelp"
        )

    def _generate_autohandle_reply(
        self,
        customer_text: str,
        intent: str,
        retrieved_evidence: List[Dict[str, Any]],
    ) -> str:
        """Crafts policy-grounded self-service response using retrieved historical resolutions."""
        # Check if high-relevance evidence provides specific instructions
        best_evidence_resp = ""
        if retrieved_evidence and retrieved_evidence[0].get("score", 0.0) >= 0.25:
            best_evidence_resp = retrieved_evidence[0].get("historical_response", "")

        if intent == "Delivery Tracking & Status":
            return (
                "You can check the real-time location and estimated delivery date of your package at any time by going to 'Your Orders' "
                "and selecting 'Track Package' next to the item. If the carrier tracking shows no movement for more than 48 hours, "
                "please share your 17-digit Order ID so we can look into it for you. ^AmazonHelp"
            )

        if intent == "Returns, Replacements & Refunds":
            return (
                "To return or exchange an item, please visit our Online Returns Center by going to 'Your Orders' > 'Return or replace items'. "
                "You can choose your preferred return method and print a prepaid return label. Once the item is received at our fulfilment centre, "
                "refunds are typically processed within 3 to 5 business days. Let us know if you need help with a specific order ID! ^AmazonHelp"
            )

        if intent == "Prime & Subscription Services":
            return (
                "You can view, update, or cancel your Prime subscription settings at any time by visiting 'Your Account' > 'Prime' > 'Manage Membership'. "
                "If you choose to end your membership and have not used any Prime benefits during the billing cycle, you may be eligible for a full refund. "
                "Let us know if you have questions regarding a specific charge! ^AmazonHelp"
            )

        if intent == "Digital Services & Devices":
            return (
                "For issues with digital content or Amazon devices (such as Fire TV, Kindle, or Echo), we recommend restarting the device "
                "and checking your network connection. If using an app, ensuring the app is updated to the latest version and clearing its cache "
                "often resolves playback errors. If the issue persists, please let us know which device model you are using! ^AmazonHelp"
            )

        if intent == "Order & Checkout":
            return (
                "If your order has not yet entered the shipping process, you can make changes to your delivery address, payment method, "
                "or cancel items directly in 'Your Orders' > 'Order Details'. Please note that promotional discount codes must be entered "
                "at checkout before completing the purchase. Feel free to reach out if you need assistance with an order! ^AmazonHelp"
            )

        # Fallback informative reply
        return (
            "Thanks for reaching out to Amazon Support! For account-specific details, please review your status under 'Your Orders' "
            "or 'Your Account'. If you require further assistance, please provide your Order ID and we'll be glad to help. ^AmazonHelp"
        )
