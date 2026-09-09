"""
Step 3: AmazonHelp Intent Classifier & Metadata Detector

Authoritative specification: reports/AmazonHelp_final_taxonomy.md
Classifies customer text into exactly one of the 10 locked intents, detects language,
conversation state, security alert flag, and computes calibrated confidence scores.
"""

import math
import re
from typing import Dict, Any, List, Tuple

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


class AmazonHelpIntentClassifier:
    """
    10-Class Intent Classifier with calibrated feature matching and confidence scoring.
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        # 1. Delivery Tracking & Status
        self.tracking_patterns = [
            r"\b(where is|track(ing)?|eta|estimated delivery|dispatch(ed)?|has.*shipped|shipment status|when will.*arrive|where.*package|status of my order|tracking number|carrier tracking)\b",
            r"(いつ.*届|発送.*状況|追跡番号|配送状況|配達状況|荷物.*どこ)",
            r"(dónde está.*(paquete|pedido)|seguimiento|cuándo llega|estado del envío|localizador)",
            r"(wo bleibt.*(paket|bestellung)|sendungsverfolgung|wann kommt)",
            r"(onde está.*(encomenda|pedido)|rastreamento|código de rastreio)",
            r"(où est.*(colis|commande)|numéro de suivi|statut de la livraison)",
        ]

        # 2. Delivery Problem & Logistics
        self.logistics_patterns = [
            r"\b(late|delay(ed)?|not received|never received|never arrived|missing package|lost package|package.*not delivered|failed delivery|courier issue|wrong address|delivered but not there|delivered.*haven't received|carrier claim|undelivered|damaged package|stolen package|broken box)\b",
            r"(届かない|遅延|未着|荷物.*届いてない|配達完了.*届いてない|誤配送|破損)",
            r"(retras(o|ado)|no ha llegado|no he recibido|paquete perdido|entregado pero no|repartidor)",
            r"(verspät(et|ung)|nicht angekommen|paket verloren|nicht erhalten|bote)",
            r"(atras(o|ado)|não recebi|pacote perdido|entregue mas não|entregador)",
            r"(retard|pas reçu|colis perdu|livré mais rien|livreur|endommagé)",
        ]

        # 3. Returns, Replacements & Refunds
        self.returns_patterns = [
            r"\b(return|refund|replacement|replace|exchange|send back|drop off|return label|refund status|haven't received my refund|money back|reimbursement|pick ?up return)\b",
            r"(返品|返金|交換|返品ラベル|送り返|返金.*まだ)",
            r"(devolución|reembolso|devolver|reemplazo|etiqueta de devolución)",
            r"(rücksendung|erstatten|erstattung|umtausch|zurücksenden|rückgabe)",
            r"(devolução|reembolso|devolver|troca|etiqueta de devolução)",
            r"(retour|remboursement|renvoyer|échange|étiquette de retour)",
        ]

        # 4. Payment, Billing & Gift Cards
        self.payment_patterns = [
            r"\b(charg(ed?|ing)?|credit card|debit card|double charge|unauthorized charge|overcharged|payment failed|payment method|declined|invoice|billing|bank statement|gift card|gift voucher|promo balance|deducted|twice)\b",
            r"(二重請求|二重引き落とし|請求|決済エラー|支払い|ギフト券|残高|領収書)",
            r"(cobro indebido|doble cobro|factura|tarjeta de regalo|pago rechazado)",
            r"(doppelt abgebucht|abbuchung|rechnung|gutschein|zahlung fehlgeschlagen)",
            r"(cobrança indevida|cartão presente|pagamento recusado|fatura)",
            r"(prélèvement|double débit|facture|chèque cadeau|paiement refusé)",
        ]

        # 5. Prime & Subscription Services
        self.prime_patterns = [
            r"\b(prime|prime membership|prime video|prime music|subscription|auto-renew(al)?|cancel prime|renew prime|prime fee|student prime|charged for prime)\b",
            r"(プライム会員|プライム年会費|プライム解約|自動更新|プライム登録|プライム特典)",
            r"(membresía prime|suscripción prime|cancelar prime|cuota prime)",
            r"(prime mitgliedschaft|prime kündigen|prime abo|prime gebühr)",
            r"(assinatura prime|cancelar prime|membro prime)",
            r"(abonnement prime|résilier prime|frais prime)",
        ]

        # 6. Order & Checkout
        self.order_patterns = [
            r"\b(cancel order|order cancelled|checkout|can't place order|promo code|voucher code|discount not applied|lightning deal|pre-order|change address|edit order|cart|basket|buy now)\b",
            r"(注文キャンセル|注文できない|プロモーションコード|クーポン|割引|予約注文|購入手続き)",
            r"(cancelar pedido|no puedo comprar|código promocional|descuento|tramitar pedido)",
            r"(bestellung stornieren|kann nicht bestellen|aktionscode|gutschein|rabatt)",
            r"(cancelar pedido|não consigo comprar|cupom|desconto|finalizar compra)",
            r"(annuler commande|impossible de commander|code promo|réduction|panier)",
        ]

        # 7. Account Access & Security
        self.account_patterns = [
            r"\b(login|log[- ]in|sign[- ]in|signed[- ]in|locked out|password|passcode|otp|two[- ]factor|2fa|verification code|security code|credentials)\b",
            r"\b(hacked|compromis(ed?|ing)|hijack(ed?|ing)|breach(ed)?|stolen account|account takeover)\b",
            r"\b(unauthori[zs]ed|unrecogni[zs]ed|unapproved|suspicious)\s+(access|login|user|activity|changes?|order[s]?|purchase[s]?|transaction[s]?|device[s]?)\b",
            r"\b(fake|scam|fraud(ulent)?|spoof(ed)?|bogus|phish(ing)?|malicious|suspicious|pretend(ed|ing)?)\b.{0,60}\b(sms|text|email|message|link|url|website|call|voicemail|communication)\b",
            r"\b(sms|text|email|message|link|url|website|call)\b.{0,60}\b(fake|scam|fraud(ulent)?|spoof(ed)?|bogus|phish(ing)?|suspicious)\b",
            r"\b(impersonat(ing|ed|e)|pretend(ing|ed)? to be|claimed to be|claiming to be)\b.{0,40}\b(amazon|customer support|support|representative)\b",
            r"\b(ask(ed|ing)?|request(ed|ing)?|demand(ed|ing)?|want(ed|ing)?|solicit(ing)?|requiring)\b.{0,60}\b(bank details|bank account|card details|credit card|debit card|password|passcode|otp|pin|credentials|cvv|security code)\b",
            r"\b(someone|somebody|hacker|intruder|unknown (person|user))\b.{0,50}\b(changed|accessed|logged into|in my account|stole|used my account|hijacked|swapped|reset)\b",
            r"\b(changed|modified|updated|reset)\b.{0,30}\b(my\s+)?(email|password|phone( number)?|credentials|recovery)\b.{0,40}\b(without (my |permission|authorization)|not me|unauthori[zs]ed)\b",
            r"\b(without (my |permission|authorization)|not me|unauthori[zs]ed)\b.{0,40}\b(changed|modified|updated|reset)\b.{0,30}\b(my\s+)?(email|password|phone|credentials)\b",
            r"(ログインできない|パスワード再設定|認証コード|2段階認証|アカウント停止|不正アクセス|乗っ取り|詐欺メール|架空請求)",
            r"(iniciar sesión|bloqueada|contraseña|código de verificación|cuenta hackeada|phishing|suplantación)",
            r"(einloggen|passwort vergessen|verifizierungscode|gehackt|konto gesperrt|phishing|betrug)",
            r"(fazer login|bloqueada|senha|código de verificação|conta hackeada|golpe|phishing)",
            r"(connexion|mot de passe oublié|code de vérification|compte piraté|hameçonnage|usurpation)",
        ]

        # 8. Digital Services & Devices
        self.digital_patterns = [
            r"\b(kindle|fire tv|fire stick|echo|alexa|audible|amazon music|app error|download error|streaming error|ebook|e-book|firmware|device frozen|can't play|video error|app crash)\b",
            r"(キンドル|ファイヤースティック|アレクサ|エコー|端末.*動かない|アプリ.*エラー|再生できない|電子書籍)",
            r"(kindle|fire tv|alexa|error de reproducción|aplicación no funciona)",
            r"(kindle|fire tv|alexa|wiedergabefehler|app stürzt ab)",
            r"(kindle|fire tv|alexa|erro de reprodução|aplicativo travando)",
            r"(kindle|fire tv|alexa|erreur de lecture|application plante)",
        ]

        # 9. Seller & Product Quality
        self.seller_patterns = [
            r"\b(third[- ]party seller|marketplace seller|seller won't reply|fake item|counterfeit|defective product|broken product|wrong item sent|used item sold as new|expired product|poor quality|merchant)\b",
            r"(出品者|マーケットプレイス|偽物|模倣品|不良品|欠陥|違う商品|中古品|賞味期限切れ)",
            r"(vendedor externo|producto defectuoso|falsificación|producto roto|artículo equivocado)",
            r"(drittanbieter|defektes produkt|fälschung|falscher artikel|beschädigt)",
            r"(vendedor parceiro|produto defeituoso|falsificado|produto errado)",
            r"(vendeur tiers|produit défectueux|contrefaçon|mauvais article|produit cassé)",
        ]

        # 10. Security Alert Specific Patterns (Strict subset)
        self.security_alert_patterns = [
            r"\b(hacked|compromis(ed?|ing)|hijack(ed?|ing)|breach(ed)?|stolen account|account takeover)\b",
            r"\b(someone|somebody|hacker|intruder|unknown (person|user)|unauthori[zs]ed person)\b.{0,60}\b(accessed|logged into|in my account|stole|using my account|placed order|bought|changed)\b",
            r"\b(unauthori[zs]ed|unrecogni[zs]ed|fraudulent)\s+(access|login|user|activity|changes?|order[s]?|purchase[s]?)\b",
            r"\b(someone|hacker|unauthori[zs]ed.*)\b.{0,50}\b(changed|swapped|reset)\b.{0,30}\b(my\s+)?(email|password|login|credentials|phone)\b",
            r"\b(changed|modified|reset)\b.{0,30}\b(my\s+)?(email|password|phone)\b.{0,40}\b(without (my |permission)|unauthori[zs]ed|not by me)\b",
            r"\b(fake|scam|fraud(ulent)?|spoof(ed)?|bogus|phish(ing)?|malicious|suspicious)\b.{0,60}\b(sms|text|email|message|link|url|website|call)\b",
            r"\b(sms|text|email|message|link|url|website|call)\b.{0,60}\b(fake|scam|fraud(ulent)?|spoof(ed)?|bogus|phish(ing)?)\b",
            r"\b(impersonat(ing|ed|e)|pretend(ing|ed)? to be|claimed to be)\b.{0,40}\b(amazon|customer support|support|representative)\b",
            r"\b(ask(ed|ing)?|request(ed|ing)?|demand(ed|ing)?|want(ed|ing)?|solicit(ing)?)\b.{0,60}\b(bank details|bank account|card details|credit card|debit card|password|passcode|otp|pin|credentials|cvv|security code)\b",
            r"\b(suspicious|unrecogni[zs]ed)\b.{0,40}\b(charge|transaction|payment|login|activity|link)\b",
            r"\b(unauthori[zs]ed charge|credit card fraud|stolen card|identity theft)\b",
            r"(アカウント.*乗っ取り|不正アクセス|詐欺メール|架空請求|身に覚えのない請求)",
            r"(cuenta hackeada|me han hackeado|mensaje fraudulento|correo falso|suplantación)",
            r"(konto gehackt|unbefugter zugriff|betrugs-email|fake sms|phishing)",
            r"(conta hackeada|golpe do sms|mensagem falsa|clonaram minha conta)",
            r"(compte piraté|mail frauduleux|faux sms|escroc|hameçonnage)",
        ]

    def detect_language(self, text: str) -> str:
        """Heuristic language detection based on character scripts and core vocabulary counts."""
        # Japanese (Hiragana / Katakana / Kanji)
        if re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text):
            return "ja"

        words = set(re.findall(r"\b[a-zà-ÿ]+\b", text.lower()))
        if not words:
            return "en"

        # English indicator words
        en_markers = {"the", "my", "is", "have", "not", "this", "package", "order", "delivery", "help", "can", "with", "for", "you", "your", "want", "refund", "return", "where"}
        es_markers = {"el", "la", "los", "las", "un", "una", "pedido", "paquete", "dónde", "cuándo", "gracias", "hola", "por", "favor", "ayuda", "reembolso"}
        fr_markers = {"le", "la", "les", "des", "du", "dans", "pour", "commande", "colis", "bonjour", "merci", "où", "quand", "livraison", "vendeur"}
        de_markers = {"der", "die", "das", "und", "für", "von", "mit", "bestellung", "paket", "hallo", "danke", "bitte", "wann", "stornieren"}
        pt_markers = {"não", "obrigado", "encomenda", "entrega", "código", "rastreio", "comprei", "chegou", "vocês", "está"}
        it_markers = {"il", "gli", "perché", "ordine", "pacco", "ciao", "dove", "quando", "spedizione", "arrivato"}

        counts = {
            "en": len(words & en_markers) * 1.5,
            "es": len(words & es_markers) * 2.0,
            "fr": len(words & fr_markers) * 2.0,
            "de": len(words & de_markers) * 2.0,
            "pt": len(words & pt_markers) * 2.0,
            "it": len(words & it_markers) * 2.0,
        }

        top_lang, top_score = max(counts.items(), key=lambda x: x[1])
        if top_score > 0:
            return top_lang
        return "en"

    def detect_conversation_state(self, text: str) -> str:
        """Determines dialogue turn state."""
        t = text.lower()
        if re.search(r"\b(dm('d)?|sent (a )?dm|check (your )?dm|messaged you|sent message|privado)\b", t):
            return "dm_handoff"
        if re.search(r"\b(thank(s| you)|resolved|fixed|all good|appreciate it|much better|solved|gracias|merci|danke)\b", t) and len(t) < 60:
            return "resolved_or_acknowledgment"
        if re.search(r"\b(yes|no|tried that|already did|still not|didn't work|as i said|called|spoke to|replied)\b", t):
            return "follow_up"
        if re.search(r"\b(can you help|having trouble|error|issue|problem|broken|doesn't work|not working)\b", t):
            return "active_troubleshooting"
        return "new_issue"

    def is_security_alert(self, text: str) -> bool:
        """Checks for phishing, fraud, account compromise, or scam threats."""
        for pat in self.security_alert_patterns:
            if re.search(pat, text, re.IGNORECASE):
                return True
        return False

    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classifies incoming text into exactly one locked intent with calibrated confidence.
        """
        text_clean = text.strip()
        lang = self.detect_language(text_clean)
        conv_state = self.detect_conversation_state(text_clean)
        is_sec = self.is_security_alert(text_clean)

        # Compute raw scores for each intent
        raw_scores = {intent: 0.1 for intent in LOCKED_INTENTS}

        def score_matches(patterns, intent, weight=1.5):
            for pat in patterns:
                matches = re.findall(pat, text_clean, re.IGNORECASE)
                if matches:
                    raw_scores[intent] += len(matches) * weight

        score_matches(self.tracking_patterns, "Delivery Tracking & Status", 2.0)
        score_matches(self.logistics_patterns, "Delivery Problem & Logistics", 2.2)
        score_matches(self.returns_patterns, "Returns, Replacements & Refunds", 2.2)
        score_matches(self.payment_patterns, "Payment, Billing & Gift Cards", 2.2)
        score_matches(self.prime_patterns, "Prime & Subscription Services", 2.2)
        score_matches(self.order_patterns, "Order & Checkout", 1.8)
        score_matches(self.account_patterns, "Account Access & Security", 2.5)
        score_matches(self.digital_patterns, "Digital Services & Devices", 2.0)
        score_matches(self.seller_patterns, "Seller & Product Quality", 2.0)

        # Boundary adjustments:
        # If security alert is active, heavily boost Account Access & Security
        if is_sec:
            raw_scores["Account Access & Security"] += 4.0

        # Boundary: Payment dispute on subscription (e.g. "charged twice for Prime")
        # Rule: Financial dispute / duplicate billing takes precedence over subscription info
        has_double_charge = bool(re.search(r"\b(twice|double|duplicate|overcharg|two times|unauthorized charge)\b", text_clean, re.IGNORECASE))
        if has_double_charge and raw_scores["Payment, Billing & Gift Cards"] > 0.1:
            raw_scores["Payment, Billing & Gift Cards"] += 2.0

        # Boundary: Prime vs Delivery Problem (e.g. "My Prime package is late")
        # Rule: Logistics failure takes precedence over subscription status
        has_logistics = any(re.search(p, text_clean, re.IGNORECASE) for p in self.logistics_patterns)
        if has_logistics and raw_scores["Prime & Subscription Services"] > 0.1:
            raw_scores["Delivery Problem & Logistics"] += 1.5

        # Boundary: Returns vs Seller Conduct (e.g. "Seller sent wrong item, want refund")
        has_seller = any(re.search(p, text_clean, re.IGNORECASE) for p in self.seller_patterns)
        if has_seller:
            raw_scores["Seller & Product Quality"] += 1.0

        # Calculate Softmax Probabilities over raw scores
        max_score = max(raw_scores.values())
        exp_scores = {intent: math.exp(score - max_score) for intent, score in raw_scores.items()}
        total_exp = sum(exp_scores.values())
        probs = {intent: exp / total_exp for intent, exp in exp_scores.items()}

        # Sort by probability descending
        sorted_intents = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        top_intent, top_p = sorted_intents[0]
        second_intent, second_p = sorted_intents[1]

        # Calculate Confidence:
        # High when top intent dominates and margin is wide
        margin = top_p - second_p

        # If no significant pattern matched, default to General / Feedback / Other
        if max_score <= 0.1:
            top_intent = "General / Feedback / Other"
            confidence = 0.45
        else:
            confidence = min(0.98, max(0.30, top_p * 0.7 + margin * 0.3 + 0.15))

        confidence = round(confidence, 2)
        priority = "P0_CRITICAL" if is_sec else "standard"

        return {
            "intent": top_intent,
            "confidence": confidence,
            "language": lang,
            "conversation_state": conv_state,
            "is_security_alert": is_sec,
            "priority": priority,
        }
