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
            r"\b(track(ing)? (my |this |the )?(order|package|parcel|item|shipment)|track\b.{0,20}\b(order|package|parcel|item|shipment)|where is (my )?(package|order|parcel|item|shipment|delivery)|eta|estimated delivery|estimated time|dispatch(ed)?|preparing for dispatch|has (it |my order )?shipped|when will (it|my order|the package) (ship|arrive|be delivered)|shipment status|delivery status|status of my (order|package|shipment)|carrier tracking|check (the )?tracking|transit status|tracking (number|id|link|details)|track my delivery|any update on (my )?(order|package|delivery)|to be delivered before|leave my parcel with a neighbour|meant to arrive by|order.*has not been updated since|tracking useless|last.*delivery date|delivery date if ordering)\b",
            r"(いつ.*届|発送.*状況|追跡番号|配送状況|配達状況|荷物.*どこ|いつ発送|トラッキング)",
            r"(dónde está.*(paquete|pedido)|seguimiento|cuándo llega|estado del envío|localizador|número de seguimiento|cuándo se envía|quisiera rastrearlo)",
            r"(wo bleibt.*(paket|bestellung)|sendungsverfolgung|wann kommt|wann wird.*verschickt|sendungsnummer|lieferstatus)",
            r"(onde está.*(encomenda|pedido)|rastreamento|código de rastreio|quando chega|quando vai ser enviado)",
            r"(où est.*(colis|commande)|numéro de suivi|statut de la livraison|quand arrive|quand sera expédié)",
            r"(dove si trova.*(pacco|ordine)|tracciamento|quando arriva|stato della spedizione|numero di tracciamento)",
        ]

        # 2. Delivery Problem & Logistics
        self.logistics_patterns = [
            r"\b(late|delay(ed)?|running late|days? late|hours? late|delayed delivery|delay in delivery|delivery delayed|package delayed|shipment delayed|order delayed|overdue|past (the )?(delivery )?date|missed (the )?(delivery )?(date|time|window)|still waiting|waiting for (my )?(order|package|delivery|item|parcel)|supposed to (arrive|be delivered)|not (yet )?(delivered|arrived|received)|haven't (received|gotten|got)|hasn't (arrived|come|turned up|delivered)|never (arrived|showed up|received|delivered)|didn't (arrive|receive|get|come)|not here yet|package not here|order not here|still not delivered|not dlverd|no sign of my (order|package)|allow a further week for|run past the guaranteed delivery date|guaranteed to take \d+ days|why am I paying for 2 day shipping|paying for 2 day shipping|no longer next day delivery|same day delivery on anything|delivery boy falsely claims|attempted delivery|delivery attempt(ed)?|no one (came|knocked|rang)|no card left|no phone call to advise|reception manned|try again today.*next business day|same shipper left.*driveway|opened my front door.*threw my order|delivered to me in|some guy.*delivered it to me|1 (out )?of 2 parcels delivered.*says both|order reached in city yet delayed|sitting next to the door.*failed delivery|parcel left right by notice saying not to leave|delivery driver is a liar|driver.*never even rang|was delivered saying that I recieved|wasn't able to be delivered|safe place.*door mat)\b",
            r"\b((marked|says|shows|status is)\s+(as\s+)?delivered\b.{0,40}\b(haven't|not|never|didn't|nowhere|no sign|missing|nothing|empty|didn't receive)|delivered\s+(but|yet)\s+(not|nothing|haven't|nowhere|missing|no package|empty)|says? delivered but (it's )?not|fake delivery attempt|driver claimed|claims? delivered|false scan)\b",
            r"\b(missing (package|order|delivery|item|parcel)|lost (package|order|parcel|item)|package (is |was )?stolen|stolen from (my )?(porch|door|mailbox)|package (is |was )?missing|parcel (is |was )?missing|package (is |was )?lost|parcel (is |was )?lost|undelivered|where is my stuff|package nowhere to be found)\b",
            r"\b(delivery (failed|attempt failed|unsuccessful|failure|issue|problem)|failed delivery|couldn't deliver|unable to deliver|attempted delivery|(marked\s+)?delivery attempt(ed)?|delivery boy|delivery person|delivery guy|driver (didn't|never|failed|lied|refused|drove past)|courier (didn't|never|failed|lost|damaged|threw|refused)|driver left (it )?(in the rain|outside|on the street|by the bin|driveway)|in safe place but not there|wrong address|delivered to wrong (house|address|place|door|person)|carrier (lost|damaged|delay)|rescheduled delivery|carrier issue|damaged package|stolen package|broken box|box crushed|box saturated|in the pouring rain)\b",
            r"\b(damaged (box|package|parcel|packaging|shipping)|box (was )?(crushed|damaged|broken|open(ed)?|torn|ripped|wet)|package (was )?(crushed|opened|damaged|torn|wet)|arrived in mille morceaux|colis ouvert|damaged in transit)\b",
            # Multilingual logistics
            r"(届かない|届きません|遅延|未着|届いてない|配達完了.*届いてない|誤配送|配送事故|配達員|持ち戻り|不在票.*入ってない|荷物.*まだ|いつまで待たせる|届く気配がない|破損)",
            r"(retras(o|ado)|no ha llegado|no he recibido|no me ha llegado|paquete perdido|entregado pero no|repartidor (no|nunca|perdió|dejó)|no fue entregado|entrega fallida|dirección incorrecta|paquete dañado|retraso en la entrega|tendría que haber llegado|tendria que haber llegado|el problema es que no llama)",
            r"(verspät(et|ung)|nicht angekommen|paket verloren|nicht erhalten|nicht zugestellt|bote|lieferant|falsche adresse|beschädigtes paket|zustellung fehlgeschlagen|immer noch nicht da|noch nicht geliefert)",
            r"(retard(é)?|pas (encore )?(reçu|arrivé|livré)|non (reçu|arrivé|livré)|colis perdu|livré mais rien|livreur|endommagé|colis ouvert|mille morceaux|échec de livraison|abîmé en transit|cassé en transit|colis privé|était prévue pour aujourd'hui|commandé mon ordi depuis plus d'un mois|colis livré mais pas dans ma boite)",
            r"(atras(o|ado)|não recebi|não chegou|pacote perdido|entregue mas não|entregador|encomenda atrasada|não foi entregue|extraviado|pacote danificado|não entrega meus livros)",
            r"(in ritardo|ritardo|non arrivato|non ho ricevuto|pacco perso|non consegnato|corriere|consegnato ma non|pacco danneggiato|mancata consegna)",
        ]

        # 3. Returns, Replacements & Refunds
        self.returns_patterns = [
            r"\b(return(ing|ed|s)?|refund(s|ed|ing)?|replacement(s)?|replace|exchange|send back|return label|refund status|haven't received my refund|full refund|money back|reimbursement|return drop[- ]off|drop off at (ups|hermes|post office|store)|pick ?up return|return slip|return barcode|want a refund|request(ed)? a refund|give me (my )?refund|release money after an order has been cancelled|told I would be received a refund|product returned without informing|tnc for exchange|waitin fo return pickup|asked for a return|neither refund|still no.*refund)\b",
            r"(返品|返金|交換|返品ラベル|送り返|返金.*まだ|返金手続き|返品受付|集荷返品)",
            r"(devolución|reembolso|devolver|reemplazo|etiqueta de devolución|cambio de producto|cuándo recibiré el reembolso)",
            r"(rücksendung|erstatten|erstattung|umtausch|zurücksenden|rückgabe|retoure|rücksendelabel)",
            r"(retour(ner)?|remboursement|renvoyer|échange|étiquette de retour|quand.*remboursé)",
            r"(devolução|reembolso|devolver|troca|etiqueta de devolução|quando vou receber o reembolso)",
            r"(reso|rimborso|restituire|sostituzione|etichetta di reso|quando riceverò il rimborso)",
        ]

        # 4. Payment, Billing & Gift Cards
        self.payment_patterns = [
            r"\b(charg(ed?|ing)? (twice|double|extra|again|multiple times|individually)|double (charge|billing|debit)|duplicate (charge|billing|payment)|unauthorized (charge|transaction|debit)|overcharg(ed?|ing)?|incorrect amount|payment failed|payment declined|card declined|payment method|billing (issue|error|statement)|bank statement|invoice|tax invoice|gst(in)?|vat (invoice|number)|gift card (balance|code|redeem|error)|gift voucher|promo balance|voucher bal|amazon pay|cod (is harassing|issue|harassment|cash on delivery)|deducted twice|credit card|debit card|credit limit|pay the extra amount|charged again for prime)\b",
            r"(二重請求|二重引き落とし|請求|決済エラー|支払い|ギフト券|残高|領収書)",
            r"(cobro indebido|doble cobro|factura|tarjeta de regalo|pago rechazado)",
            r"(doppelt abgebucht|abbuchung|rechnung|gutschein|zahlung fehlgeschlagen)",
            r"(cobrança indevida|cartão presente|pagamento recusado|fatura)",
            r"(prélèvement|double débit|facture|chèque cadeau|paiement refusé)",
        ]

        # 5. Prime & Subscription Services (Strict subscription intent - NO bare prime token)
        self.prime_patterns = [
            r"\b(prime membership|prime subscription|subscription|auto-renew(al)?|cancel prime|renew prime|renew(al)? of prime|prime fee|prime cost|prime student|prime annual fee|student prime|charged for prime|paying for prime membership|prime trial|prime benefits?|keep prime membership|offer it to your us prime members|cancel prime once the free trial|prime members\?|membership for next day delivery|prime.*membership)\b",
            r"(プライム会員|プライム年会費|プライム解約|自動更新|プライム登録|プライム特典|ミュージックアンリミテッド|解約し忘れて年会費)",
            r"(membresía prime|suscripción prime|cancelar prime|cuota prime)",
            r"(prime mitgliedschaft|prime kündigen|prime abo|prime gebühr)",
            r"(assinatura prime|cancelar prime|membro prime)",
            r"(abonnement prime|résilier prime|frais prime)",
        ]

        # 6. Order & Checkout
        self.order_patterns = [
            r"\b(checkout|promo(tion)? code|voucher code|discount (not applied|missing|coupon)|what a discount|lightning deal|deal gets claimed|deal starts at|list it as a deal|asking for a lightning deal|pre[- ]order|preorder|book preorder|change (shipping |delivery )?address|edit order|cart|basket|can't (place|complete) order|cancel (my )?order|order (was )?cancell?ed|buy now|out of stock|could not set your address|discounted pre-order|price reverts to original on check out|check delivery charge|zip.*state|add on's don't work|immediately go out of stock|so you want me to cancel my order|edit quantities error|not able to buy.*mobile|cant buy|can't buy)\b",
            r"(注文キャンセル|注文できない|プロモーションコード|クーポン|割引|予約注文|購入手続き)",
            r"(cancelar pedido|no puedo comprar|código promocional|descuento|tramitar pedido)",
            r"(bestellung stornieren|kann nicht bestellen|aktionscode|gutschein|rabatt)",
            r"(cancelar pedido|não consigo comprar|cupom|desconto|finalizar compra|codigo postal)",
            r"(annuler commande|impossible de commander|code promo|réduction|panier)",
        ]

        # 7. Account Access & Security
        self.account_patterns = [
            r"\b(login|log[- ]in|sign[- ]in|signed[- ]in|can't log in|unable to sign in|locked out (of my account)?|forgot password|reset password|password reset (link|email)|passcode|otp|two[- ]factor|2fa|verification code|security code|credentials|account (on hold|suspended|blocked|locked|closed)|verify identity|change (my )?(email|mobile|phone number) (on|for) account|problemas con mi cuenta)\b",
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
            r"\b(kindle|fire (tv|stick|tablet)|echo( dot)?|alexa|audible|prime video (streaming|error|playback|quality|buffering)|amazon music (app|error)|e[- ]?book|audiobook|app (crash(es|ed|ing)?|error|not working|freeze|frozen|update)|website (down|error|glitch|broken)|streaming (error|quality|buffering|lag)|can't (play|stream|download|watch)|video quality|firmware|device (frozen|won't turn on|stuck)|never got the beta|beta codes?|psn codes?|whole app seems to run slow|won't save to my nas|app is not working|roku.*amazon video|software on the roku|connected to wifi|content will eventually download)\b",
            r"(キンドル|ファイヤースティック|アレクサ|エコー|端末.*動かない|アプリ.*エラー|再生できない|電子書籍)",
            r"(kindle|fire tv|alexa|error de reproducción|aplicación no funciona|app no funciona)",
            r"(kindle|fire tv|alexa|wiedergabefehler|app stürzt ab|spiel|englisches ebook)",
            r"(kindle|fire tv|alexa|erro de reprodução|aplicativo travando)",
            r"(kindle|fire tv|alexa|erreur de lecture|application plante)",
        ]

        # 9. Seller & Product Quality
        self.seller_patterns = [
            r"\b(fake (item|product|phone|goods|shoes|watch|supplement|review|perfume|charger|cable|beats)|counterfeit|unauthentic|not authentic|replica|knockoff|pirated|duplicate copy|fraud seller|seller scam|unresponsive seller|seller won't reply|fake\b.{0,20}\b(received|bought|sent|sold)|(item is|product is|unit is|is)?\s*(defective|broken merchandise|faulty|damaged product|broken seal)|broken (item|product|piece|seal|screen|merchandise)|damaged (item|product|goods)|poor quality|cheap quality|inferior quality|stopped working|doesn't work|not working properly|product not working|wrong (item|product|color|size|model|phone|sim) sent|recd\. the wrong item|received (a |the )?wrong (item|product)|this was not what I ordered|didn't put one of the items in the box|nothing inside package|seller (won't|refuses to|doesn't|not) (reply|respond|answer|refund|help)|third[- ]party seller|marketplace seller|used item sold as new|expired (item|product|food|date)|merchant (issue|problem|scam)|hologram fake|review (rejected|removed|guidelines?)|complaint against your seller|orders are fulfilled by sellers|the a-z claim|a-to-z guarantee claim|vendeur tiers)\b",
            r"(出品者|マーケットプレイス|偽物|模倣品|不良品|欠陥|違う商品|中古品.*新品として|賞味期限切れ|動かない|壊れて|品質が悪い)",
            r"(vendedor externo|producto defectuoso|falsificación|producto roto|artículo equivocado|producto falso|no funciona|mala calidad|vendedor no contesta|segunda mano como nuevo|reseña.*directrices)",
            r"(drittanbieter|defektes produkt|fälschung|falscher artikel|beschädigt|funktioniert nicht|schlechte qualität|gebrochen|gebraucht als neu)",
            r"(vendedor parceiro|produto defeituoso|falsificado|produto errado|produto falso|não funciona|péssima qualidade|produto quebrado)",
            r"(vendeur tiers|produit défectueux|contrefaçon|mauvais article|produit cassé|faux produit|ne fonctionne pas|mauvaise qualité|usagé vendu comme neuf|impossible de contacter le vendeur)",
            r"(venditore terzo|prodotto difettoso|contraffatto|articolo sbagliato|prodotto rotto|non funziona|pessima qualità|usato per nuovo)",
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
            r"(compte piraté|mail frauduleux|faux sms|hameçonnage)",
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
        raw_scores = {intent: 0.0 for intent in LOCKED_INTENTS}

        def score_matches(patterns, intent, weight=1.5):
            for pat in patterns:
                matches = re.findall(pat, text_clean, re.IGNORECASE)
                if matches:
                    raw_scores[intent] += len(matches) * weight

        score_matches(self.tracking_patterns, "Delivery Tracking & Status", 2.0)
        score_matches(self.logistics_patterns, "Delivery Problem & Logistics", 2.5)
        score_matches(self.returns_patterns, "Returns, Replacements & Refunds", 2.5)
        score_matches(self.payment_patterns, "Payment, Billing & Gift Cards", 2.5)
        score_matches(self.prime_patterns, "Prime & Subscription Services", 2.5)
        score_matches(self.order_patterns, "Order & Checkout", 2.2)
        score_matches(self.account_patterns, "Account Access & Security", 2.8)
        score_matches(self.digital_patterns, "Digital Services & Devices", 2.2)
        score_matches(self.seller_patterns, "Seller & Product Quality", 2.6)

        # Boundary adjustments:
        # If security alert is active, heavily boost Account Access & Security
        if is_sec:
            raw_scores["Account Access & Security"] += 5.0

        # Boundary: Financial dispute
        has_double_charge = bool(re.search(r"\b(twice|double|duplicate|overcharg|two times|unauthorized charge|charged again)\b", text_clean, re.IGNORECASE))
        if has_double_charge:
            raw_scores["Payment, Billing & Gift Cards"] += 3.0

        # Boundary: Logistics takes precedence over Tracking when failure/delay/complaint is indicated
        has_logistics = raw_scores["Delivery Problem & Logistics"] > 0.0
        if has_logistics and raw_scores["Delivery Tracking & Status"] > 0.0:
            raw_scores["Delivery Problem & Logistics"] += 2.0

        # Boundary: Logistics takes precedence over Prime when delivery failure is mentioned
        if has_logistics and raw_scores["Prime & Subscription Services"] > 0.0:
            raw_scores["Delivery Problem & Logistics"] += 3.0

        # Boundary: Seller takes precedence over Returns/Logistics if counterfeit/defect/seller dispute
        has_seller = raw_scores["Seller & Product Quality"] > 0.0
        if has_seller:
            if raw_scores["Returns, Replacements & Refunds"] > 0.0:
                raw_scores["Seller & Product Quality"] += 2.0
            if raw_scores["Delivery Problem & Logistics"] > 0.0 and re.search(r"\b(wrong item|defective|fake|counterfeit|seller)\b", text_clean, re.IGNORECASE):
                raw_scores["Seller & Product Quality"] += 2.0

        # Boundary: Positive praise filter (e.g. "Alexa ist toll", "meu Kindle já chegou")
        is_pure_compliment = bool(re.search(r"\b(ist toll|j[aá] chegou|great|love it|amazing|best app|thank(s| you)|obrigado|danke|merci)\b", text_clean, re.IGNORECASE))
        has_problem_words = bool(re.search(r"\b(problem|error|issue|trouble|broken|fix|help|late|not|doesn't|can't|won't|never|missing|delay|wrong)\b", text_clean, re.IGNORECASE))
        if is_pure_compliment and not has_problem_words:
            raw_scores["General / Feedback / Other"] += 4.0

        max_score = max(raw_scores.values())

        # If no score, default to General / Feedback / Other
        if max_score <= 0.0:
            top_intent = "General / Feedback / Other"
            confidence = 0.45
        else:
            # Softmax probabilities over raw scores
            exp_scores = {intent: math.exp(score - max_score) for intent, score in raw_scores.items()}
            total_exp = sum(exp_scores.values())
            probs = {intent: exp / total_exp for intent, exp in exp_scores.items()}

            sorted_intents = sorted(probs.items(), key=lambda x: x[1], reverse=True)
            top_intent, top_p = sorted_intents[0]
            second_intent, second_p = sorted_intents[1]
            margin = top_p - second_p

            # If multiple distinct intents compete closely (multi-intent ambiguity), drop confidence
            competing_intents = [intent for intent, score in raw_scores.items() if score >= max_score * 0.75]
            if len(competing_intents) > 1 and not is_sec and margin < 0.25:
                confidence = min(0.48, max(0.35, top_p * 0.5))
            else:
                confidence = min(0.98, max(0.35, top_p * 0.7 + margin * 0.3 + 0.15))

            # Disparate domain ambiguity (e.g. broad listing: delivery + billing + return)
            disparate_domains = sum([
                bool(re.search(r"\b(delivery|shipping)\b", text_clean, re.I)),
                bool(re.search(r"\b(billing|payment)\b", text_clean, re.I)),
                bool(re.search(r"\b(return|refund)\b", text_clean, re.I)),
            ])
            if disparate_domains >= 2 and not is_sec and not has_double_charge and not has_logistics:
                confidence = 0.38

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
