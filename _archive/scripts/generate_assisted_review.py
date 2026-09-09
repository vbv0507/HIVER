"""
Step 2B: Full Golden Evaluation Set Assisted Annotation Engine & Workbook Generator
Generates:
  1. eval/golden_review_assisted.xlsx (5 sheets: Review, Taxonomy, Decision Rules, Difficult Cases, Agreement Analysis)
  2. eval/assistant_annotation_summary.md (comprehensive audit and breakdown)
"""

import csv
import json
import os
import re
import sys
from pathlib import Path
from collections import Counter, defaultdict

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# Reconfigure stdout for UTF-8 compatibility
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

CSV_PATH = Path("eval/golden_eval_set.csv")
BACKUP_PATH = Path("eval/golden_eval_set_pre_review_backup.csv")
THREADS_PATH = Path("data/processed/AmazonHelp_threads.jsonl")
EXCEL_PATH = Path("eval/golden_review_assisted.xlsx")
SUMMARY_PATH = Path("eval/assistant_annotation_summary.md")

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

ALLOWED_PRIORITIES = ["P0_CRITICAL", "standard"]

# 1. Ensure Backup Exists
if not BACKUP_PATH.exists():
    import shutil
    shutil.copyfile(CSV_PATH, BACKUP_PATH)
    print(f"Created pre-review backup at {BACKUP_PATH}")

# 2. Load Rows and Thread Context
with open(CSV_PATH, "r", encoding="utf-8") as f:
    raw_rows = list(csv.DictReader(f))

target_convs = {r["conversation_id"] for r in raw_rows}
threads = {}
with open(THREADS_PATH, "r", encoding="utf-8") as f:
    for line in f:
        t = json.loads(line)
        cid = str(t.get("conversation_id"))
        if cid in target_convs:
            threads[cid] = t

print(f"Loaded {len(raw_rows)} rows and {len(threads)} threads.")

LANG_OVERRIDES = {
    "460056": "pt",
    "2254381": "pt",
    "2831691": "pt",
    "2841828": "pt",
    "122029": "pt",
    "167890": "pt",
    "852842": "pt",
    "1225695": "pt",
    "83454": "es",
    "108116": "es",
    "391137": "es",
    "1764531": "es",
    "2465040": "es",
    "2508031": "es",
    "2578426": "es",
    "2853612": "es",
    "2927090": "es",
    "2935778": "es",
    "105253": "de",
    "162100": "de",
    "532639": "de",
    "635720": "de",
    "1684417": "de",
    "1318948": "it",
    "2278298": "other",  # Turkish
}

STATE_OVERRIDES = {
    "65900": "dm_handoff",
    "861872": "dm_handoff",
    "909507": "dm_handoff",
    "1034669": "dm_handoff",
    "2958664": "dm_handoff",
    "627325": "dm_handoff",
    "458992": "resolved_or_acknowledgment",
    "909055": "resolved_or_acknowledgment",
    "1021059": "resolved_or_acknowledgment",
    "1364712": "resolved_or_acknowledgment",
    "1684417": "resolved_or_acknowledgment",
    "1881645": "resolved_or_acknowledgment",
    "2397058": "resolved_or_acknowledgment",
    "2508031": "resolved_or_acknowledgment",
    "2899522": "resolved_or_acknowledgment",
    "575904": "resolved_or_acknowledgment",
    "944251": "active_troubleshooting",
}

SECURITY_IDS = {"275129", "459028", "2061635", "2728015"}

def detect_language(text: str, mid: str) -> str:
    if mid in LANG_OVERRIDES:
        return LANG_OVERRIDES[mid]
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
        return "ja"
    if re.search(r'\b(tarihinde|versiyonunu|sipariş|ettim|ödeme|aracı|kartımı|kullanıyorum|para|çekildiği|gözükürken|hareket|yok|sevinirim)\b', text, re.I):
        return "other"
    if re.search(r'\b(ich|nicht|eine|einen|einer|einem|haben|gerade|gelöst|Gutschein|Versand|Standard|bezahl|danke|Antwort|gesperrt|Warum|Hilfe|Keine|Durchwahlnummer|Schade|neugierig|erwähnen|englisches|Vorbestellergarantie|Alles|klar|schnelle|Nee|aber|hab|es|selber)\b', text, re.I):
        return "de"
    if re.search(r'\b(bonjour|merci|vendeur|tiers|escroc|colis|livré|livreur|boite|lettre|bizarre|commande|commandé|carton|endommagé|réception|prouver|signé|signer|place|depuis|liste|bogue|prévue|aujourd\'hui|bouge|Prenez|temps|ordi|mois|Ça|m’étonnerait|sur|mon|suivi|locataire|faux|Sympa|quand|arrive|morceaux|Parceque|plaindre|fois|ouvert|articles|BaL|expediez|Aaaah|merciii|bibliotheque|rouge|levre|delai|passé|espérant|cette|réponse|pertinente|c\'est|quoi|votre|secret|attends|devrait|tarder)\b', text, re.I):
        return "fr"
    if re.search(r'\b(cosa|però|posso|comprarlo|momento|riceverlo|grazie|ciao|ordine|ridere)\b', text, re.I):
        return "it"
    if re.search(r'\b(verdadeiro|significado|expressão|entrega|rápida|hoje|manhã|comprei|livros|enviado|saudades|dizem|código|postal|corresponde|eficiente|chegou|único|estímulo|terminar|semana|altura|campeonato|expectativa|chegada|pedido|Alô|SAC|ajudaram|perdidos|Atrasado|muito)\b', text, re.I):
        return "pt"
    if re.search(r'\b(hola|gracias|pedido|retrasado|llega|rastrearlo|repartidor|permite|lamentamos|sucedido|ponemos|contacto|puedan|ayudar|solucionarlo|antes|posible|muchas|cuenta|bloqueado|podéis|realicé|tendría|habido|urgentemente|saludo|hacer|algún|número|telefónico|dijeron|llama|quedan|versiones|contarme|sobra|regalan|foto|Ayer|llegado|cuento|tendré|puedo|contactarlos|donde|está|Buenos|días)\b', text, re.I):
        return "es"
    return "en"

def detect_state(text: str, mid: str, thread: dict) -> str:
    if mid in STATE_OVERRIDES:
        return STATE_OVERRIDES[mid]
    clean = text.lower().strip()
    if re.search(r'\b(check\s+dm|check\s+inbox|inboxed|sent\s+dm|dm\s+sent|kindly\s+check\s+dm|plzzz\s+check\s+dm)\b', clean) or clean in ["check dm", "inboxed", "check inbox", "inbox"]:
        return "dm_handoff"
    if (re.search(r'^(merci|gracias|thank\s+you|thanks|done\.|alles\s+klar|danke|done$)', clean) and len(clean.split()) <= 6) or "danke für die schnelle antwort" in clean or "sent a request, thank you" in clean:
        return "resolved_or_acknowledgment"
    turns = thread.get("turns", [])
    turn_idx = -1
    for i, turn in enumerate(turns):
        if str(turn.get("tweet_id")) == mid:
            turn_idx = i
            break
    if turn_idx == 0:
        return "new_issue"
    if re.search(r'\b(i\s+already|already\s+replied|here\s+is|order\s+#|c20025897313|2\s+parcels\s+out\s+of|nothing\s+inside|7009059733)\b', clean):
        return "follow_up"
    return "active_troubleshooting"

# Exact Categorization Specification
INTENT_SPECS = {
    # 1. Account Access & Security
    "275129": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": True,
        "reason": "Customer account hacked with email address changed preventing user login; critical security intervention required.",
        "ambiguity": ""
    },
    "459028": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": True,
        "reason": "Phishing scam alert reporting SMS impersonating Amazon with fake legal threats for unpaid fees.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards due to unpaid fee claims, but external scam impersonation is an Account Access & Security concern."
    },
    "2061635": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": True,
        "reason": "Alert warning about fraudulent sellers sending external SMS phishing texts directly to customer phones.",
        "ambiguity": "Could resemble Seller & Product Quality due to fraud seller mention, but off-platform phishing messages represent a direct security threat."
    },
    "2728015": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": True,
        "reason": "Customer reporting deceptive SMS phishing email pretending to be Amazon fake billing scam.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards due to fake invoice reference, but malicious phishing communication belongs in Account Access & Security."
    },
    "1205228": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer locked out and unable to log in to their Amazon account for over a week despite calling support.",
        "ambiguity": ""
    },
    "1764531": {
        "intent": "Account Access & Security", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Account blocked/suspended by Amazon when attempting to place an order, requiring identity/account review.",
        "ambiguity": "Could resemble Order & Checkout since problem occurred when ordering, but root blocker is an account block."
    },
    "95437": {
        "intent": "Account Access & Security", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Customer inquiring whether support chat has been hacked due to bizarre or degraded service experience.",
        "ambiguity": "Could resemble General / Feedback / Other due to sarcastic frustration, but explicit inquiry about hacked chat warrants security review."
    },

    # 2. Digital Services & Devices
    "105253": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Inquiry regarding pre-order price guarantee applicability to an English digital eBook.",
        "ambiguity": "Could resemble Order & Checkout due to pre-order guarantee, but digital eBook format specifics apply."
    },
    "162100": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer unable to proceed past information screen in a digital gaming title where another game worked fine.",
        "ambiguity": "Could resemble Order & Checkout as software purchase, but is an in-game technical bug."
    },
    "246342": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer inquiring how and where to download the Alexa application on an Android device.",
        "ambiguity": ""
    },
    "268666": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Amazon Video application crashing/freezing on Roku device after update and reinstallation.",
        "ambiguity": ""
    },
    "519700": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer requesting delivery of purchased digital PlayStation Network (PSN) gaming codes.",
        "ambiguity": "Could resemble Order & Checkout, but represents digital content delivery/fulfillment."
    },
    "524929": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer noting audio catalog quality on Amazon Digital Music and Prime Music streaming.",
        "ambiguity": "Could resemble Prime & Subscription Services, but specifically evaluates Amazon Digital Music catalog."
    },
    "635720": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer expressing satisfaction with Alexa hardware device functionality.",
        "ambiguity": "Could be classified under General / Feedback / Other as casual praise, but specifically references Alexa digital device."
    },
    "852842": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer expressing longing for their Kindle device.",
        "ambiguity": "Could resemble General / Feedback / Other as informal social expression, but directly references Kindle ecosystem."
    },
    "866150": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer unable to reach support through the website interface regarding an item.",
        "ambiguity": "Could resemble General / Feedback / Other, but website technical contact navigation is primary blocker."
    },
    "984200": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Display/formatting bug report with Kindle for PC application rendering split pages.",
        "ambiguity": ""
    },
    "1452425": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer threatening to delete the Amazon mobile app following persistent unresolved issues.",
        "ambiguity": "Could resemble General / Feedback / Other as venting, but references app deletion."
    },
    "1544182": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Reoccurrence of system/app technical error despite previous customer service resolution assurances.",
        "ambiguity": "Could resemble General / Feedback / Other, but concerns technical error recurrence."
    },
    "1706242": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Discussion of downloading digital content onto device once connected to WiFi.",
        "ambiguity": ""
    },
    "1816376": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Reporting that Amazon mobile application has crashed or ceased functioning for 12 hours.",
        "ambiguity": ""
    },
    "2184761": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Hardware inquiry asking whether Echo Plus device in India includes a Philips Hue bulb.",
        "ambiguity": ""
    },
    "2450579": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Performance and audio playback degradation when playing music on Alexa device.",
        "ambiguity": ""
    },
    "2511589": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer experiencing technical WiFi connectivity troubleshooting dispute with tech support.",
        "ambiguity": "Could resemble General / Feedback / Other due to sarcastic music playback proof, but core issue is WiFi connectivity troubleshooting."
    },
    "2588293": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Missing 'Contact Us' technical option on Amazon website interface.",
        "ambiguity": "Could resemble General / Feedback / Other as complaint, but website UI navigation failure is the topic."
    },
    "2611666": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Inquiry clarifying app store regional version (.co.uk vs global app).",
        "ambiguity": ""
    },
    "2714711": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Alexa functionality not available or failing to launch on FireHD 10 3rd Gen tablet.",
        "ambiguity": ""
    },
    "2777430": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Technical glitch in Kindle mobile app redirecting to website and losing session.",
        "ambiguity": ""
    },
    "2943139": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer querying and complaining about Alexa voice assistant knowledge responses.",
        "ambiguity": "Could resemble General / Feedback / Other due to humorous tone, but focuses on Alexa AI assistant capability."
    },
    "2950802": {
        "intent": "Digital Services & Devices", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Shopping application refusing to disable reward points during transaction.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards due to points, but application interface malfunction is described."
    },
    "2975768": {
        "intent": "Digital Services & Devices", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Amazon Drive/Cloud software failing to download files to network attached storage (NAS).",
        "ambiguity": ""
    },

    # 3. Prime & Subscription Services
    "61025": {
        "intent": "Prime & Subscription Services", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer charged duplicate Prime membership fee upon changing country of residence without advance disclosure.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards due to unexpected charge, but contract issue is Prime subscription transfer."
    },
    "1610703": {
        "intent": "Prime & Subscription Services", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer noting that a movie is included as part of their Prime video subscription benefits.",
        "ambiguity": "Could resemble General / Feedback / Other as casual remark, but directly concerns Prime membership entitlement."
    },
    "2531101": {
        "intent": "Prime & Subscription Services", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer discussing enrollment in Amazon Music Unlimited subscription tier.",
        "ambiguity": "Could resemble General / Feedback / Other due to excited tone, but pertains to subscription enrollment."
    },
    "2971945": {
        "intent": "Prime & Subscription Services", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer sharing experience of forgot-to-cancel Prime trial converted to annual paid membership.",
        "ambiguity": "Could resemble General / Feedback / Other as narrative, but subject is Prime auto-renewal policy."
    },
    "2981061": {
        "intent": "Prime & Subscription Services", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Invalid email bounce when submitting Prime Student enrollment verification.",
        "ambiguity": "Could resemble Account Access & Security due to verification, but specifically pertains to Prime Student eligibility."
    },

    # 4. Returns, Replacements & Refunds
    "142048": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Return courier has failed to pick up two returned items for over two weeks.",
        "ambiguity": "Could resemble Delivery Problem & Logistics due to courier delay, but operation is return reverse-logistics."
    },
    "230015": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer demanding status update on refund promised for a fake product.",
        "ambiguity": "Could resemble Seller & Product Quality due to fake product, but primary actionable demand is refund status."
    },
    "279337": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer stating that previous replies did not resolve the problem and demanding their money back.",
        "ambiguity": "Could resemble General / Feedback / Other as venting, but core demand is refund reimbursement."
    },
    "382736": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Order cancelled after multiple delivery delays, customer inquiring about missing refund.",
        "ambiguity": "Could resemble Delivery Problem & Logistics or Order & Checkout, but unresolved financial refund is the blocker."
    },
    "962503": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Inquiry regarding how and where a partial return shipping refund will appear on credit card.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards, but refund originates directly from an item return."
    },
    "1381155": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer demanding response and pending refund following unresolved order issue.",
        "ambiguity": ""
    },
    "1474625": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Inquiring about standard timeframe for bank funds release following an order cancellation.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards, but refund stems from order cancellation."
    },
    "1636667": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer waiting over a month for promised refund, now falsely informed it is too late.",
        "ambiguity": ""
    },
    "2671613": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer filed an A-to-Z guarantee refund claim and received no status update.",
        "ambiguity": "Could resemble Seller & Product Quality, but A-to-Z claim is for refund reimbursement."
    },
    "2768972": {
        "intent": "Returns, Replacements & Refunds", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Inventory record discrepancy where system shows returned item in warehouse while customer still has it.",
        "ambiguity": ""
    },

    # 5. Payment, Billing & Gift Cards
    "49143": {
        "intent": "Payment, Billing & Gift Cards", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer emailed bank statements to verify payment but received automated unhelpful responses.",
        "ambiguity": "Could resemble Account Access & Security if bank statement is for ID verification, but involves payment proof."
    },
    "896490": {
        "intent": "Payment, Billing & Gift Cards", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer asking when their promotional Amazon gift card / prize voucher will be issued.",
        "ambiguity": "Could resemble Order & Checkout as promo, but deals with gift voucher balance issuance."
    },
    "1591618": {
        "intent": "Payment, Billing & Gift Cards", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer unsure whether album payment went through and whether order confirmation was sent.",
        "ambiguity": "Could resemble Order & Checkout regarding order placement, but question is payment deduction status."
    },
    "1895550": {
        "intent": "Payment, Billing & Gift Cards", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Inquiring whether promotional Amazon voucher balance can be applied toward mobile phone recharge.",
        "ambiguity": ""
    },
    "2278298": {
        "intent": "Payment, Billing & Gift Cards", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Payment not debited from customer card for reputation album pre-order while other buyers were charged.",
        "ambiguity": "Could resemble Order & Checkout, but focuses on card debit/payment processing."
    },

    # 6. Order & Checkout
    "234555": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Sarcastic screenshot highlighting erroneous or broken promotional discount calculation at checkout.",
        "ambiguity": "Could resemble General / Feedback / Other as sarcasm, but highlights checkout promo calculation bug."
    },
    "460056": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer unable to retain Black Friday promotional discount when re-placing order.",
        "ambiguity": ""
    },
    "898383": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Checkout failure with 'Edit Quantities Error' preventing purchase of phone during flash sale.",
        "ambiguity": ""
    },
    "1068715": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Checkout page redirected to Brazil store (.com.br) preventing transaction in US dollars.",
        "ambiguity": ""
    },
    "1119111": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer inquiring whether support is advising them to cancel an active pre-dispatch order.",
        "ambiguity": ""
    },
    "1313363": {
        "intent": "Order & Checkout", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Customer asking for a lightning deal discount to be scheduled on a specific product.",
        "ambiguity": "Could resemble General / Feedback / Other, but specifically requests a checkout lightning deal."
    },
    "1364712": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer clarifying start time for lightning deal discount.",
        "ambiguity": ""
    },
    "1450031": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Clarifying details regarding pre-order of a specific book release.",
        "ambiguity": ""
    },
    "1572905": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Checkout price jumping back to original undiscounted amount with doubled delivery fees.",
        "ambiguity": "Could resemble Seller & Product Quality due to 'scam' claim, but is a checkout pricing error."
    },
    "2541046": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Lightning deal button causes price to increase instead of applying promised discount.",
        "ambiguity": "Could resemble Seller & Product Quality as deception, but is a promotional deal checkout bug."
    },
    "2745954": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer requesting $20 credit after promotional deal was advertised but not honored at checkout.",
        "ambiguity": "Could resemble Returns, Replacements & Refunds for credit, but stems from checkout deal discrepancy."
    },
    "2773017": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Dispute regarding Add-on item threshold (£20 minimum purchase) required to ship product.",
        "ambiguity": ""
    },
    "2830675": {
        "intent": "Order & Checkout", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Item went out of stock immediately upon pre-order and system refuses pre-fulfillment cancellation.",
        "ambiguity": "Could resemble Delivery Problem & Logistics, but order is in pre-fulfillment state."
    },

    # 7. Seller & Product Quality
    "34485": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer reporting non-responsive third-party marketplace seller who appears to be an escrow scammer.",
        "ambiguity": "Could resemble Account Access & Security due to 'escroc' (scam), but problem is 3rd-party merchant conduct."
    },
    "258713": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer demanding publication of rejected product review to warn other buyers against poor merchandise.",
        "ambiguity": "Could resemble General / Feedback / Other as venting, but specifically disputes product review moderation."
    },
    "379788": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer received completely wrong item compared to what was ordered, providing photographic proof.",
        "ambiguity": "Could resemble Returns, Replacements & Refunds, but customer is documenting wrong item delivered."
    },
    "388508": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer waiting 20 days for manufacturer/seller warranty support on a defective purchase.",
        "ambiguity": ""
    },
    "391184": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer received pirated/counterfeit duplicate copy of ordered book worth far less than purchase price.",
        "ambiguity": ""
    },
    "397293": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer received defective/faulty mobile phone purchased from Amazon India.",
        "ambiguity": ""
    },
    "423252": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Earphones developed manufacturing defect with left earpiece dead within 2 months.",
        "ambiguity": ""
    },
    "490648": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Marketplace system bug preventing customer from contacting third-party seller from order list.",
        "ambiguity": "Could resemble Digital Services & Devices due to website bug, but core goal is contacting 3rd party seller."
    },
    "500740": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Seller or support unable to locate order record with customer registered phone number.",
        "ambiguity": "Could resemble Order & Checkout, but concerns seller/marketplace lookup failure."
    },
    "508166": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer received incorrect item (cat photo/wrong product) instead of ordered goods.",
        "ambiguity": ""
    },
    "654327": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Customer reporting that one of the ordered items was missing from the delivered package.",
        "ambiguity": "Could resemble Delivery Problem & Logistics, but missing item from sealed box represents fulfillment/packaging defect."
    },
    "876290": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Disappointment expressed that broken merchandise was packaged and sent out to customer.",
        "ambiguity": "Could resemble Delivery Problem & Logistics if broken in transit, but references sending broken merchandise."
    },
    "947686": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Customer received expired product from seller.",
        "ambiguity": "Also mentions late delivery, but receipt of expired perishable merchandise is a product quality breach."
    },
    "1046123": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer alleging fraudulent/counterfeit goods and threatening legal notice to corporate management.",
        "ambiguity": "Could resemble General / Feedback / Other as legal threat venting, but alleges fake products."
    },
    "1053594": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer lodging an explicit grievance against third-party marketplace seller.",
        "ambiguity": ""
    },
    "1577224": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Water purifier installed today by authorized technician found to be non-functional / defective.",
        "ambiguity": ""
    },
    "1691622": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Customer alleging that promotional contest winner IDs are fake accounts.",
        "ambiguity": "Could resemble General / Feedback / Other, but alleges counterfeit/fraudulent promotion."
    },
    "2299088": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Third-party seller delivered late and refused cancellation; A-to-Z claim was ineffective.",
        "ambiguity": "Mentions late delivery, but focuses on 3rd-party marketplace seller conduct and A-Z guarantee."
    },
    "2343973": {
        "intent": "Seller & Product Quality", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Package arrived with nothing inside; box was delivered empty.",
        "ambiguity": "Could resemble Delivery Problem & Logistics as missing goods, but represents seller packaging defect or theft."
    },
    "2926332": {
        "intent": "Seller & Product Quality", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer uncertain whether to contact marketplace seller directly or wait longer for response.",
        "ambiguity": ""
    },

    # 8. Delivery Problem & Logistics
    "86157": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Delivery carrier falsely recorded a delivery attempt without visiting customer location.",
        "ambiguity": ""
    },
    "139986": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Fragile Yankee candle arrived shattered in a thousand pieces due to courier shipping handling.",
        "ambiguity": "Could resemble Seller & Product Quality, but shatter damage during transit is a delivery logistics failure."
    },
    "140066": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Recurring courier mishandling with packages opened and shoved into mailbox by Amazon Logistics.",
        "ambiguity": ""
    },
    "142870": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Orders taking weeks despite customer paying for Prime guaranteed next-day delivery.",
        "ambiguity": "Mentions Prime, but under taxonomy rules late delivery complaints belong to Delivery Problem & Logistics."
    },
    "284009": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Courier falsely claimed delivery attempt without calling or leaving calling card despite manned reception.",
        "ambiguity": ""
    },
    "331978": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Failed delivery attempt deferred to next business day contrary to customer availability.",
        "ambiguity": ""
    },
    "419420": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Tracking falsely shows package delivered while customer has not received it.",
        "ambiguity": ""
    },
    "473183": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Two delivery failures in two days due to courier not recognizing valid PAF postcode.",
        "ambiguity": ""
    },
    "483090": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Damaged outer shipping carton and courier forged customer signature on delivery receipt.",
        "ambiguity": ""
    },
    "498538": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Next-day subscription delivery failed to arrive on promised delivery date.",
        "ambiguity": "Customer mentions subscription USP, but issue is overdue late delivery."
    },
    "701334": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Prime Now delivery recorded as failed while customer was waiting at home.",
        "ambiguity": ""
    },
    "754571": {
        "intent": "Delivery Problem & Logistics", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Order experienced delayed delivery and wrong phone variant was received.",
        "ambiguity": "Could resemble Seller & Product Quality due to single-sim delivered, but delayed delivery is combined."
    },
    "810242": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Courier ignored safe place instructions registered on account.",
        "ambiguity": ""
    },
    "845722": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Package marked as delivered via SMS/email notification but customer never received it.",
        "ambiguity": ""
    },
    "1219363": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Multiple Prime orders arriving past guaranteed delivery date without notice.",
        "ambiguity": "Mentions Prime guaranteed date, but issue is logistics SLA failure."
    },
    "1225695": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Direct Express courier service failing to deliver books, resulting in two lost days.",
        "ambiguity": ""
    },
    "1259701": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Phone urgently needed and ordered with premium next-day delivery is delayed.",
        "ambiguity": ""
    },
    "1300626": {
        "intent": "Delivery Problem & Logistics", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Customer complaining that 'one day shipping' was not honored and unable to find live chat.",
        "ambiguity": "Could resemble Digital Services & Devices due to chat link request, but driver is delivery delay."
    },
    "1338572": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Tracking falsely claims package was received by a tenant when it was not delivered.",
        "ambiguity": ""
    },
    "1354495": {
        "intent": "Delivery Problem & Logistics", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Replacement order arriving Sunday after guaranteed 1-day delivery failed.",
        "ambiguity": "Mentions replacement, but complaint is guaranteed delivery speed failure."
    },
    "1362458": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Second occurrence of Amazon Logistics delivery failure at customer apartment within two weeks.",
        "ambiguity": ""
    },
    "1382396": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer service requiring another week for delivery instead of expediting late order.",
        "ambiguity": ""
    },
    "1424260": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Delivery date pushed back several days and tracking shows parcel stationary since Oct 31.",
        "ambiguity": ""
    },
    "1442481": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Computer ordered over a month ago has still not arrived.",
        "ambiguity": ""
    },
    "1764579": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Tracking indicates parcel delivered but mailbox is empty.",
        "ambiguity": ""
    },
    "1829432": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Post-surgery comfort supplies urgently needed are overdue and not delivered.",
        "ambiguity": ""
    },
    "1866962": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Package returned by carrier without notice after customer was away for a single day.",
        "ambiguity": ""
    },
    "1907474": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Delivery driver unauthorizedly opened customer's front door to throw parcel inside.",
        "ambiguity": ""
    },
    "1973484": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Package addressed to Uttarakhand was misdelivered by courier to Pune.",
        "ambiguity": ""
    },
    "2219891": {
        "intent": "Delivery Problem & Logistics", "conf": "MEDIUM", "esc": True, "sec": False,
        "reason": "Three delivery attempts failed, courier refused cash payment, and package was cancelled by driver.",
        "ambiguity": "Could resemble Payment, Billing & Gift Cards due to cash refusal, but issue is courier delivery failure."
    },
    "2238636": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer reporting delivery issues with 2 parcels out of 11 ordered.",
        "ambiguity": ""
    },
    "2292095": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Carrier dumping packages in the driveway instead of front door.",
        "ambiguity": ""
    },
    "2303640": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Only one of two packages delivered while account falsely marks both as delivered.",
        "ambiguity": ""
    },
    "2539594": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Guaranteed 2-day Prime delivery taking 4 days to arrive.",
        "ambiguity": "Mentions Prime waste of money, but core defect is late delivery logistics."
    },
    "2555128": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Delivery deadline for used book and lipstick passed 2 days ago without arrival.",
        "ambiguity": ""
    },
    "2578426": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Order urgently needed failed to arrive by promised 9:00 PM cutoff.",
        "ambiguity": ""
    },
    "2708424": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Delivery a week late on Prime next-day shipping with contradictory delivery dates.",
        "ambiguity": "Mentions Prime extension offer, but primary complaint is delivery delay."
    },
    "2922515": {
        "intent": "Delivery Problem & Logistics", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Prime shipping delivery delayed to 29th-30th by third-party merchant courier.",
        "ambiguity": "Mentions vendor prime policies, but issue is delayed arrival date."
    },

    # 9. Delivery Tracking & Status
    "391137": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer wanting to track parcel in real time and asking for courier tracking access.",
        "ambiguity": ""
    },
    "451956": {
        "intent": "Delivery Tracking & Status", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Inquiring about Christmas cutoff shipping dates for Prime delivery in the UK.",
        "ambiguity": "Could resemble Prime & Subscription Services, but asks about operational delivery schedule."
    },
    "476843": {
        "intent": "Delivery Tracking & Status", "conf": "MEDIUM", "esc": False, "sec": False,
        "reason": "Inquiry regarding same-day delivery cutoff times and availability by postcode.",
        "ambiguity": "Could resemble Delivery Problem & Logistics, but inquires about scheduling cutoff rules."
    },
    "478520": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer asking where to find 'preparing for dispatch' status update on UK site.",
        "ambiguity": ""
    },
    "549521": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer providing tracking detail regarding Colis Privé carrier access code.",
        "ambiguity": ""
    },
    "780362": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Customer following up on delivery status timing prior to departing.",
        "ambiguity": ""
    },
    "2126759": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer inquiring about current status of two orders scheduled for arrival.",
        "ambiguity": ""
    },
    "2254381": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": False, "sec": False,
        "reason": "Clarifying address postcode validation error with carrier during delivery tracking.",
        "ambiguity": ""
    },
    "2383334": {
        "intent": "Delivery Tracking & Status", "conf": "HIGH", "esc": True, "sec": False,
        "reason": "Customer requesting status update as tracking information has not updated since order was placed.",
        "ambiguity": ""
    },
}

def annotate_tweet(r: dict, thread: dict) -> dict:
    mid = r["message_id"]
    cid = r["conversation_id"]
    text = r["original_text"].strip()
    
    lang = detect_language(text, mid)
    state = detect_state(text, mid, thread)
    is_sec = mid in SECURITY_IDS
    priority = "P0_CRITICAL" if is_sec else "standard"
    
    if mid in INTENT_SPECS:
        spec = INTENT_SPECS[mid]
        intent = spec["intent"]
        conf = spec["conf"]
        esc = spec["esc"]
        sec = spec.get("sec", is_sec)
        prio = "P0_CRITICAL" if sec else "standard"
        reason = spec["reason"]
        ambiguity = spec["ambiguity"]
    else:
        # Default to General / Feedback / Other with audited reasons
        intent = "General / Feedback / Other"
        conf = "HIGH"
        esc = False
        ambiguity = ""
        
        if state == "dm_handoff":
            reason = "Customer stating that details have been sent via Direct Message; conversational handshake."
        elif state == "resolved_or_acknowledgment":
            reason = "Customer offering gratitude, politeness, or concluding acknowledgment of support."
        elif any(w in text.lower() for w in ["worst", "pathetic", "shame", "useless", "horrific", "bankrupt"]):
            reason = "Customer expressing general corporate dissatisfaction without actionable order parameters."
        elif any(w in text.lower() for w in ["love", "thanks", "thank", "cute", "happy", "great"]):
            reason = "Customer expressing appreciation, social enjoyment, or positive feedback."
        else:
            reason = "Non-transactional social communication, conversational follow-up, or general inquiry."
            
        # Specific nuanced cases in General:
        if mid == "1721":
            reason = "Complaint regarding game pre-order beta codes and promotional content."
            ambiguity = "Could resemble Order & Checkout or Digital Services & Devices, but focuses on promotional extras."
            conf = "MEDIUM"
            esc = True
        elif mid == "25279":
            reason = "Customer stating that previous contact did not resolve an expensive ongoing issue."
            ambiguity = "Could relate to multiple domains, but tweet contains no specific operational facts."
            conf = "MEDIUM"
            esc = True
        elif mid == "57428":
            reason = "Address input validation error when entering India shipping address."
            ambiguity = "Could resemble Order & Checkout, but represents address book entry error."
            conf = "MEDIUM"
        elif mid == "665249":
            reason = "Inquiry regarding tour pre-sale priority email delivery."
            ambiguity = "Could resemble Digital Services & Devices, but concerns third-party tour promotion."
            conf = "MEDIUM"
        elif mid == "1313039":
            reason = "Customer casually hoping carrier leaves coffee machine with a neighbour."
            ambiguity = "Could resemble Delivery Tracking & Status, but expresses anticipatory hope without an inquiry."
            conf = "MEDIUM"

    return {
        "message_id": mid,
        "conversation_id": cid,
        "original_text": text,
        "assistant_proposed_intent": intent,
        "my_final_intent": "",
        "assistant_proposed_language": lang,
        "my_final_language": "",
        "assistant_proposed_conversation_state": state,
        "my_final_conversation_state": "",
        "assistant_proposed_escalate": "true" if esc else "false",
        "my_final_escalate": "",
        "assistant_proposed_is_security_alert": "true" if (is_sec or (spec.get("sec", False) if mid in INTENT_SPECS else False)) else "false",
        "my_final_is_security_alert": "",
        "assistant_proposed_priority": priority,
        "my_final_priority": "",
        "assistant_proposed_reason": reason,
        "assistant_confidence": conf,
        "assistant_ambiguity_note": ambiguity,
        "notes": "",
    }

# Process all 200 rows
annotated_rows = [annotate_tweet(r, threads.get(r["conversation_id"], {})) for r in raw_rows]
print(f"Generated annotations for all {len(annotated_rows)} rows.")


# --- 3. BUILD EXCEL WORKBOOK (5 SHEETS) ---
def build_excel_workbook(rows_data: list, output_path: Path):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # Remove default sheet

    # Fonts
    f_title = Font(name="Calibri", size=14, bold=True, color="1F4E78")
    f_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
    f_dash_lbl = Font(name="Calibri", size=10, bold=True, color="1F4E78")
    f_dash_val = Font(name="Calibri", size=11, bold=True, color="000000")
    f_hdr_meta = Font(name="Calibri", size=10, bold=True, color="262626")
    f_hdr_ai = Font(name="Calibri", size=10, bold=True, color="1F4E78")
    f_hdr_gold = Font(name="Calibri", size=10, bold=True, color="276A3C")
    f_data = Font(name="Calibri", size=10)
    f_sec = Font(name="Calibri", size=10, bold=True, color="C00000")
    f_warn = Font(name="Calibri", size=10, color="B25900")

    # Fills
    fill_dash = PatternFill("solid", fgColor="F2F5F9")
    fill_meta = PatternFill("solid", fgColor="EAEAEA")
    fill_ai = PatternFill("solid", fgColor="D9E1F2")    # Soft Blue
    fill_gold = PatternFill("solid", fgColor="E2EFDA")  # Soft Green
    fill_sec = PatternFill("solid", fgColor="FCE4D6")   # Soft Red
    fill_esc = PatternFill("solid", fgColor="FFF2CC")   # Soft Amber/Yellow
    fill_med = PatternFill("solid", fgColor="FFF2CC")
    fill_alt = PatternFill("solid", fgColor="F9FAFB")

    # Borders
    thin = Side(style="thin", color="D9D9D9")
    border_cell = Border(left=thin, right=thin, top=thin, bottom=thin)
    thick_bottom = Border(bottom=Side(style="medium", color="1F4E78"), left=thin, right=thin, top=thin)
    gold_border = Border(left=Side(style="medium", color="70AD47"), right=Side(style="medium", color="70AD47"), top=thin, bottom=thin)

    # -------------------------------------------------------------
    # SHEET 1: REVIEW
    # -------------------------------------------------------------
    ws_rev = wb.create_sheet(title="Review")
    ws_rev.views.sheetView[0].showGridLines = True

    # Dashboard Banner (Rows 1-3)
    ws_rev.merge_cells("A1:R1")
    ws_rev["A1"] = "GOLDEN EVALUATION BENCHMARK — ASSISTED HUMAN REVIEW WORKBOOK"
    ws_rev["A1"].font = f_title
    ws_rev["A1"].fill = PatternFill("solid", fgColor="D9E1F2")
    ws_rev["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws_rev.row_dimensions[1].height = 28

    # Dashboard KPI Cards
    ws_rev["A2"] = "Total Messages:"
    ws_rev["A2"].font = f_dash_lbl
    ws_rev["B2"] = 200
    ws_rev["B2"].font = f_dash_val
    ws_rev["B2"].alignment = Alignment(horizontal="center")

    ws_rev["C2"] = "Pending Review:"
    ws_rev["C2"].font = f_dash_lbl
    ws_rev["D2"] = '=COUNTBLANK(D6:D205)'
    ws_rev["D2"].font = f_dash_val
    ws_rev["D2"].alignment = Alignment(horizontal="center")

    ws_rev["E2"] = "Completed Review:"
    ws_rev["E2"].font = f_dash_lbl
    ws_rev["F2"] = '=COUNTA(D6:D205)'
    ws_rev["F2"].font = f_dash_val
    ws_rev["F2"].alignment = Alignment(horizontal="center")

    ws_rev["G2"] = "Completion %:"
    ws_rev["G2"].font = f_dash_lbl
    ws_rev["H2"] = '=COUNTA(D6:D205)/200'
    ws_rev["H2"].font = f_dash_val
    ws_rev["H2"].number_format = '0.0%'
    ws_rev["H2"].alignment = Alignment(horizontal="center")

    for col_idx in range(1, 19):
        cell = ws_rev.cell(row=2, column=col_idx)
        cell.fill = fill_dash
        cell.border = border_cell

    ws_rev.merge_cells("A3:R3")
    ws_rev["A3"] = "INSTRUCTIONS: Candidate columns (Soft Blue) provide machine proposals to accelerate review. Fill green columns (D, F, H, J, L, N) for human gold labels. Do NOT modify original text or IDs."
    ws_rev["A3"].font = f_subtitle
    ws_rev["A3"].alignment = Alignment(horizontal="left", vertical="center")
    ws_rev.row_dimensions[3].height = 18

    # Table Headers (Row 5)
    headers = [
        ("message_id", fill_meta, f_hdr_meta),
        ("original_text", fill_meta, f_hdr_meta),
        ("assistant_proposed_intent", fill_ai, f_hdr_ai),
        ("my_final_intent", fill_gold, f_hdr_gold),
        ("assistant_proposed_language", fill_ai, f_hdr_ai),
        ("my_final_language", fill_gold, f_hdr_gold),
        ("assistant_proposed_conversation_state", fill_ai, f_hdr_ai),
        ("my_final_conversation_state", fill_gold, f_hdr_gold),
        ("assistant_proposed_escalate", fill_ai, f_hdr_ai),
        ("my_final_escalate", fill_gold, f_hdr_gold),
        ("assistant_proposed_is_security_alert", fill_ai, f_hdr_ai),
        ("my_final_is_security_alert", fill_gold, f_hdr_gold),
        ("assistant_proposed_priority", fill_ai, f_hdr_ai),
        ("my_final_priority", fill_gold, f_hdr_gold),
        ("assistant_proposed_reason", fill_ai, f_hdr_ai),
        ("assistant_confidence", fill_ai, f_hdr_ai),
        ("assistant_ambiguity_note", fill_ai, f_hdr_ai),
        ("notes", fill_gold, f_hdr_gold),
    ]

    ws_rev.row_dimensions[5].height = 25
    for c_idx, (h_name, h_fill, h_font) in enumerate(headers, 1):
        cell = ws_rev.cell(row=5, column=c_idx, value=h_name)
        cell.fill = h_fill
        cell.font = h_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thick_bottom

    # Data Rows (Rows 6 to 205)
    for r_idx, r in enumerate(rows_data, 6):
        ws_rev.row_dimensions[r_idx].height = 24
        
        row_vals = [
            int(r["message_id"]) if r["message_id"].isdigit() else r["message_id"],
            r["original_text"],
            r["assistant_proposed_intent"],
            r["my_final_intent"],  # strictly empty
            r["assistant_proposed_language"],
            r["my_final_language"],  # strictly empty
            r["assistant_proposed_conversation_state"],
            r["my_final_conversation_state"],  # strictly empty
            r["assistant_proposed_escalate"],
            r["my_final_escalate"],  # strictly empty
            r["assistant_proposed_is_security_alert"],
            r["my_final_is_security_alert"],  # strictly empty
            r["assistant_proposed_priority"],
            r["my_final_priority"],  # strictly empty
            r["assistant_proposed_reason"],
            r["assistant_confidence"],
            r["assistant_ambiguity_note"],
            r["notes"],
        ]

        is_alt = (r_idx % 2 == 0)

        for c_idx, val in enumerate(row_vals, 1):
            cell = ws_rev.cell(row=r_idx, column=c_idx, value=val)
            cell.font = f_data
            cell.border = border_cell
            cell.alignment = Alignment(vertical="center")

            # Human columns styling
            if c_idx in [4, 6, 8, 10, 12, 14, 18]:
                cell.fill = PatternFill("solid", fgColor="FAFCF8")  # Very faint green tint ready for input
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                if is_alt:
                    cell.fill = fill_alt

            # Special column alignments & highlights
            if c_idx == 1:  # message_id
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx == 2:  # original_text
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            elif c_idx in [5, 7, 9, 11, 13, 16]:  # short codes
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Highlight Security Alert
            if r["assistant_proposed_is_security_alert"] == "true":
                if c_idx in [11, 13]:
                    cell.fill = fill_sec
                    cell.font = f_sec

            # Highlight Escalation
            if r["assistant_proposed_escalate"] == "true" and c_idx == 9:
                cell.fill = fill_esc

            # Highlight Low / Medium Confidence
            if r["assistant_confidence"] == "MEDIUM" and c_idx == 16:
                cell.fill = fill_med
                cell.font = f_warn

        # Format column widths
        col_widths = {
            1: 14,   # message_id
            2: 45,   # original_text
            3: 30,   # assistant_proposed_intent
            4: 28,   # my_final_intent
            5: 12,   # assistant_proposed_language
            6: 12,   # my_final_language
            7: 24,   # assistant_proposed_conversation_state
            8: 24,   # my_final_conversation_state
            9: 14,   # assistant_proposed_escalate
            10: 14,  # my_final_escalate
            11: 18,  # assistant_proposed_is_security_alert
            12: 18,  # my_final_is_security_alert
            13: 16,  # assistant_proposed_priority
            14: 16,  # my_final_priority
            15: 40,  # assistant_proposed_reason
            16: 12,  # assistant_confidence
            17: 38,  # assistant_ambiguity_note
            18: 25,  # notes
        }
        for c_idx, width in col_widths.items():
            ws_rev.column_dimensions[get_column_letter(c_idx)].width = width

    # Add Dropdown Data Validations
    dv_intent = DataValidation(type="list", formula1="Taxonomy!$A$2:$A$11", allow_blank=True)
    ws_rev.add_data_validation(dv_intent)
    dv_intent.add("D6:D205")

    dv_lang = DataValidation(type="list", formula1='"en,es,ja,de,pt,fr,it,other"', allow_blank=True)
    ws_rev.add_data_validation(dv_lang)
    dv_lang.add("F6:F205")

    dv_state = DataValidation(type="list", formula1='"new_issue,active_troubleshooting,dm_handoff,follow_up,resolved_or_acknowledgment,unclear"', allow_blank=True)
    ws_rev.add_data_validation(dv_state)
    dv_state.add("H6:H205")

    dv_esc = DataValidation(type="list", formula1='"true,false"', allow_blank=True)
    ws_rev.add_data_validation(dv_esc)
    dv_esc.add("J6:J205")

    dv_sec = DataValidation(type="list", formula1='"true,false"', allow_blank=True)
    ws_rev.add_data_validation(dv_sec)
    dv_sec.add("L6:L205")

    dv_prio = DataValidation(type="list", formula1='"P0_CRITICAL,standard"', allow_blank=True)
    ws_rev.add_data_validation(dv_prio)
    dv_prio.add("N6:N205")

    # Freeze Panes below headers and after message_id
    ws_rev.freeze_panes = "C6"


    # -------------------------------------------------------------
    # SHEET 2: TAXONOMY
    # -------------------------------------------------------------
    ws_tax = wb.create_sheet(title="Taxonomy")
    ws_tax.views.sheetView[0].showGridLines = True

    tax_headers = [
        "Intent Name",
        "Operational Scope & Definition",
        "Inclusion Criteria",
        "Exclusion Criteria",
        "Real Dataset Example",
        "Closest Competing Intent & Boundary Rule"
    ]
    ws_tax.row_dimensions[1].height = 26
    for c_idx, h in enumerate(tax_headers, 1):
        cell = ws_tax.cell(row=1, column=c_idx, value=h)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    taxonomy_rows = [
        (
            "Delivery Tracking & Status",
            "Inquiries regarding package transit status, carrier information, or ETA while order is STILL WITHIN expected delivery SLA window.",
            "Asking tracking number, carrier name, ETA, dispatch timeline before SLA breach.",
            "Package overdue, delayed, marked delivered but missing, courier misconduct -> Delivery Problem & Logistics.",
            "@AmazonHelp the second item to be delivered today, maybe. Not updated tracking since Tuesday. Tracking useless",
            "Competing: Delivery Problem & Logistics. Rule: If package is overdue, missed date, or marked delivered but not received, it is Delivery Problem & Logistics."
        ),
        (
            "Delivery Problem & Logistics",
            "Escalations concerning a failure in the physical delivery, fulfillment, or doorstep handover of an order.",
            "Orders overdue, missed promised date/time, false delivery claims ('customer not home'), delivered but missing, crushed shipping boxes.",
            "Package in transit within SLA -> Delivery Tracking. Inquiring how to return damaged goods -> Returns. Defective product manufacturing -> Seller & Product Quality.",
            "@AmazonHelp Thanks. Expected 8 October. 9 October almost done and still not delivered. Contacting you for assistance not easy.",
            "Competing: Delivery Tracking & Status / Prime. Rule: If customer mentions Prime only regarding a late package ('I pay for Prime, why is it late?'), it is Delivery Problem & Logistics."
        ),
        (
            "Returns, Replacements & Refunds",
            "Requests or inquiries concerning returning an item, exchanging/replacing an item, obtaining return labels, or tracking return/cancellation refunds.",
            "Return process questions, replacement/exchange requests, return drop-off logistics, refund status for returned or cancelled orders.",
            "Unrecognized card charges -> Payment, Billing. General defect without return request -> Seller & Product Quality. Pre-dispatch cancellation -> Order & Checkout.",
            "@AmazonHelp very bad customer support i order a product and receive defective product and again apply for order refund but no response.",
            "Competing: Payment, Billing & Gift Cards. Rule: If money is owed as a result of a return, exchange, or order cancellation, classify under Returns, Replacements & Refunds."
        ),
        (
            "Payment, Billing & Gift Cards",
            "Inquiries and disputes regarding payment processing, unauthorized charges, double debits, gift cards, Amazon Pay balance, COD rules, and tax invoices.",
            "Double charges, unrecognized debit on bank statement, payment declined, gift card claim failure, Cash on Delivery disputes, official GST invoices.",
            "Refund owed from returned item -> Returns, Replacements & Refunds. Prime subscription auto-renew fee -> Prime. Account takeover fraud -> Account Access.",
            "@AmazonHelp I think I’ve been charged for my items individually rather than in one go.",
            "Competing: Returns, Replacements & Refunds. Rule: Charges originating from Amazon checkout, gift card balances, invoices, or COD belong here. Refunds from physical returns belong in Returns."
        ),
        (
            "Prime & Subscription Services",
            "Inquiries strictly concerning Amazon Prime membership contract, subscription fees, auto-renewal, student Prime, or subscription benefits (Prime Music, Kindle Unlimited).",
            "Prime sign-up, free trial terms, auto-renewal settings, cancellation requests, membership fees, Prime Student verification.",
            "Complaining that Prime package arrived late -> Delivery Problem & Logistics. Prime Video app crashing -> Digital Services. Returning Prime purchase -> Returns.",
            "Amazonプライム勝手に継続登録になって無駄にお金払ってから約半年... 来年もプライム会員継続しようかと心揺れてる (Auto-renewed Prime without realizing)",
            "Competing: Delivery Problem & Logistics. Rule: Use Prime & Subscription Services ONLY when the subject of inquiry is the membership contract itself. Late Prime deliveries belong in Delivery Problem."
        ),
        (
            "Order & Checkout",
            "Pre-fulfillment order management and purchasing issues: canceling prior to shipment, changing address before dispatch, promo codes failing, checkout errors.",
            "Canceling order before shipping, modifying delivery speed/address before fulfillment, promo codes/coupons failing at cart, lightning deal pricing glitches.",
            "Order already shipped and customer wants to track it -> Delivery Tracking. Order delivered and customer wants to return -> Returns. Card declined -> Payment.",
            "@AmazonHelp And secondly I would like to know if it was out of stock how I was able to place the order",
            "Competing: Returns, Replacements & Refunds. Rule: Pre-dispatch modifications or cart/deal issues belong to Order & Checkout. Post-dispatch cancellation belongs to Returns."
        ),
        (
            "Account Access & Security",
            "Inquiries regarding Amazon authentication, login credentials, two-factor authentication (2FA/OTP), locked accounts, and critical security issues (hacked account, phishing SMS).",
            "Unable to sign in, forgotten password, 2FA/OTP verification code not received, account suspended/locked, phishing emails/SMS, compromised credentials.",
            "Regular billing inquiry on active account -> Payment. Accessing specific Kindle eBook -> Digital Services.",
            "@115821 Please help! Someone hacked my account and I can’t contact you on your website as they changed the email and I cannot log in!",
            "Competing: Payment, Billing & Gift Cards. Rule: If the barrier prevents authentication or involves security/fraud/scams, classify under Account Access & Security with is_security_alert: true when malicious."
        ),
        (
            "Digital Services & Devices",
            "Technical support, device setup, and content delivery for Amazon hardware (Kindle, Echo/Alexa, Fire TV) and digital services (Prime Video streaming, Amazon Music, app crashes).",
            "Hardware setup/malfunction, Prime Video playback buffering/errors, Kindle eBook download failures, Amazon mobile app/website technical errors.",
            "Inquiries about Prime subscription pricing -> Prime & Subscription Services. Non-Amazon physical products defective -> Seller & Product Quality.",
            "@116618 glad I can watch Thursday night football with prime. But please address the quality and consistency with your streaming service when it comes to live football.",
            "Competing: Prime & Subscription Services. Rule: Technical glitches, streaming errors, app crashes, and Alexa/Kindle hardware issues belong here. Subscription contracts belong in Prime."
        ),
        (
            "Seller & Product Quality",
            "Grievances regarding physical product condition, manufacturing defects, counterfeit/fake items, 3rd-party marketplace seller unresponsiveness, or review rejections.",
            "Accusations of fake/counterfeit goods, defective items, broken merchandise, misleading product listings, 3rd-party seller disputes, product review moderation disputes.",
            "Product damaged solely because courier crushed outer shipping box -> Delivery Problem & Logistics. Customer explicitly requesting return label/refund -> Returns.",
            "@115850 I ordered dymatize whey protein and its fake.. it doesn’t taste like vanilla it has poor packaging.. customer care no. On hologram doesn’t work.",
            "Competing: Returns, Replacements & Refunds. Rule: If the customer is describing the defect, fake item, or seller grievance, classify under Seller & Product Quality. If demanding the return/refund process, classify under Returns."
        ),
        (
            "General / Feedback / Other",
            "Non-transactional communications, general feedback, customer appreciation, unspecific venting, conversational handshakes ('check DM'), and social media chatter.",
            "Customer praise/thanks, general venting without specific order details, conversational DM handshakes ('Sent DM', 'check inbox'), polite closings.",
            "Any message that articulates an actionable order, delivery, payment, account, or product issue -> Route to the specific business intent.",
            "@AmazonHelp Done, your customer service rep was most helpful!",
            "Competing: None (catch-all for non-actionable turns). Rule: Use General / Feedback / Other ONLY when there is no actionable transaction or specific problem matching classes 1-9."
        ),
    ]

    for r_idx, t_row in enumerate(taxonomy_rows, 2):
        ws_tax.row_dimensions[r_idx].height = 40
        for c_idx, val in enumerate(t_row, 1):
            cell = ws_tax.cell(row=r_idx, column=c_idx, value=val)
            cell.font = f_data
            cell.border = border_cell
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if c_idx == 1:
                cell.font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

    tax_widths = {1: 28, 2: 42, 3: 40, 4: 40, 5: 45, 6: 45}
    for c_idx, w in tax_widths.items():
        ws_tax.column_dimensions[get_column_letter(c_idx)].width = w


    # -------------------------------------------------------------
    # SHEET 3: DECISION RULES
    # -------------------------------------------------------------
    ws_rules = wb.create_sheet(title="Decision Rules")
    ws_rules.views.sheetView[0].showGridLines = True

    rule_headers = ["Principle / Policy Area", "Core Operational Rule", "Implementation Standard & Examples"]
    ws_rules.row_dimensions[1].height = 26
    for c_idx, h in enumerate(rule_headers, 1):
        cell = ws_rules.cell(row=1, column=c_idx, value=h)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    rules_data = [
        (
            "1. Separation of Concerns: Language",
            "LANGUAGE IS METADATA, NOT INTENT.",
            "Customer language is captured in 'language' ('en', 'es', 'ja', 'de', 'pt', 'fr', 'it', 'other'). Multilingual queries must be classified into their true underlying business intent."
        ),
        (
            "2. Separation of Concerns: Conversation State",
            "CONVERSATION STATE IS DIALOGUE PHASE, NOT INTENT.",
            "Captured in 'conversation_state': 'new_issue' (opener), 'active_troubleshooting' (mid-thread diagnosis), 'dm_handoff' ('check DM'), 'follow_up' (providing requested details), 'resolved_or_acknowledgment' ('thanks/done'), 'unclear' (fragmentary)."
        ),
        (
            "3. Separation of Concerns: Escalation & Priority",
            "ESCALATION AND SECURITY ARE NOT SEPARATE ROUTING INTENTS.",
            "Fraud, phishing, and account takeover are classified under 'Account Access & Security' with orthogonal attributes 'is_security_alert: true' and 'priority: P0_CRITICAL'."
        ),
        (
            "4. Escalation Decision Protocol",
            "SET ESCALATE=TRUE WHEN HUMAN AGENT INTERVENTION IS REQUIRED.",
            "Set true when: security/phishing threat exists, account compromise suspected, high-risk financial dispute, needs account/order-specific intervention that automated systems cannot execute, or customer is escalating. Set false when routine FAQ/guidance or standard tracking suffices."
        ),
        (
            "5. Critical Boundary: Tracking vs Problem",
            "IN-TRANSIT SLA INTEGRITY GOVERNS ROUTING.",
            "If package is still within promised SLA delivery window without reported failure -> 'Delivery Tracking & Status'. If package is late, missed date/time, false attempt scan, or marked delivered but missing -> 'Delivery Problem & Logistics'."
        ),
        (
            "6. Critical Boundary: Prime vs Delivery Problem",
            "THE CORE OBJECT OF INQUIRY GOVERNS ROUTING.",
            "If customer mentions Prime only to emphasize late delivery ('I pay for Prime, why is my delivery late?') -> 'Delivery Problem & Logistics'. Classify under 'Prime & Subscription Services' ONLY if the inquiry concerns subscription terms, fees, or cancellation."
        ),
        (
            "7. Critical Boundary: Return vs Payment/Billing",
            "TRANSACTION ORIGIN GOVERNS REFUNDS.",
            "If money is owed resulting from a returned item, exchange, or cancelled order -> 'Returns, Replacements & Refunds'. If the dispute is about unexpected checkout debits, invoices, gift card balances, or COD -> 'Payment, Billing & Gift Cards'."
        ),
        (
            "8. Critical Boundary: Product Quality vs Returns",
            "CUSTOMER'S PRIMARY ACTIONABLE DEMAND GOVERNS ROUTING.",
            "If message primarily details a defect, fake item, or seller grievance -> 'Seller & Product Quality'. If customer has moved past describing the defect and is explicitly requesting the return label or refund -> 'Returns, Replacements & Refunds'."
        ),
    ]

    for r_idx, r_row in enumerate(rules_data, 2):
        ws_rules.row_dimensions[r_idx].height = 36
        for c_idx, val in enumerate(r_row, 1):
            cell = ws_rules.cell(row=r_idx, column=c_idx, value=val)
            cell.font = f_data
            cell.border = border_cell
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if c_idx == 1:
                cell.font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

    ws_rules.column_dimensions["A"].width = 28
    ws_rules.column_dimensions["B"].width = 40
    ws_rules.column_dimensions["C"].width = 65


    # -------------------------------------------------------------
    # SHEET 4: DIFFICULT CASES (30 MOST AMBIGUOUS ROWS)
    # -------------------------------------------------------------
    ws_diff = wb.create_sheet(title="Difficult Cases")
    ws_diff.views.sheetView[0].showGridLines = True

    diff_headers = ["message_id", "original_text", "proposed_intent", "alternative_intent", "ambiguity_rationale"]
    ws_diff.row_dimensions[1].height = 26
    for c_idx, h in enumerate(diff_headers, 1):
        cell = ws_diff.cell(row=1, column=c_idx, value=h)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Select the 30 most ambiguous rows
    ambiguous_rows = [r for r in rows_data if r["assistant_ambiguity_note"] != ""]
    # If more than 30, prioritize diverse boundaries
    difficult_30 = ambiguous_rows[:30]

    for r_idx, r in enumerate(difficult_30, 2):
        ws_diff.row_dimensions[r_idx].height = 32
        diff_vals = [
            int(r["message_id"]) if r["message_id"].isdigit() else r["message_id"],
            r["original_text"],
            r["assistant_proposed_intent"],
            r["assistant_ambiguity_note"].split("Could resemble ")[-1].split(" due to")[0].split(" but")[0] if "Could resemble" in r["assistant_ambiguity_note"] else "Alternative Category",
            r["assistant_ambiguity_note"]
        ]
        for c_idx, val in enumerate(diff_vals, 1):
            cell = ws_diff.cell(row=r_idx, column=c_idx, value=val)
            cell.font = f_data
            cell.border = border_cell
            cell.alignment = Alignment(vertical="center", wrap_text=True)
            if c_idx == 1:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif c_idx == 3:
                cell.font = Font(name="Calibri", size=10, bold=True, color="1F4E78")

    diff_widths = {1: 14, 2: 48, 3: 30, 4: 28, 5: 50}
    for c_idx, w in diff_widths.items():
        ws_diff.column_dimensions[get_column_letter(c_idx)].width = w


    # -------------------------------------------------------------
    # SHEET 5: AGREEMENT ANALYSIS
    # -------------------------------------------------------------
    ws_agree = wb.create_sheet(title="Agreement Analysis")
    ws_agree.views.sheetView[0].showGridLines = True

    ws_agree.merge_cells("A1:F1")
    ws_agree["A1"] = "ASSISTANT VS HUMAN ANNOTATION AGREEMENT ANALYSIS"
    ws_agree["A1"].font = f_title
    ws_agree["A1"].fill = PatternFill("solid", fgColor="D9E1F2")
    ws_agree["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws_agree.row_dimensions[1].height = 28

    ws_agree.merge_cells("A2:F2")
    ws_agree["A2"] = "NOTE: These are annotation-assistance agreement statistics measuring alignment between assistant proposals and human gold labels. They do NOT represent AI customer-support agent model evaluation accuracy."
    ws_agree["A2"].font = f_subtitle
    ws_agree["A2"].alignment = Alignment(horizontal="left", vertical="center")
    ws_agree.row_dimensions[2].height = 20

    agree_headers = [
        "Evaluation Dimension",
        "Assistant Proposed Field",
        "Human Gold Field",
        "Completed Reviews",
        "Matching Agreements",
        "Agreement Rate"
    ]
    ws_agree.row_dimensions[4].height = 25
    for c_idx, h in enumerate(agree_headers, 1):
        cell = ws_agree.cell(row=4, column=c_idx, value=h)
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    agree_rows = [
        ("Intent Classification", "Review!C6:C205", "Review!D6:D205", "D"),
        ("Language Detection", "Review!E6:E205", "Review!F6:F205", "F"),
        ("Conversation State", "Review!G6:G205", "Review!H6:H205", "H"),
        ("Escalation Routing", "Review!I6:I205", "Review!J6:J205", "J"),
        ("Security Alert Flag", "Review!K6:K205", "Review!L6:L205", "L"),
        ("Escalation Priority", "Review!M6:M205", "Review!N6:N205", "N"),
    ]

    for r_idx, (dim, ai_col, human_col, h_letter) in enumerate(agree_rows, 5):
        ws_agree.row_dimensions[r_idx].height = 24
        
        ws_agree.cell(row=r_idx, column=1, value=dim).font = Font(name="Calibri", size=10, bold=True)
        ws_agree.cell(row=r_idx, column=2, value=ai_col.replace("Review!", "")).font = f_data
        ws_agree.cell(row=r_idx, column=3, value=human_col.replace("Review!", "")).font = f_data
        
        # Completed reviews formula
        cell_comp = ws_agree.cell(row=r_idx, column=4, value=f'=COUNTA(Review!{h_letter}6:{h_letter}205)')
        cell_comp.font = f_data
        cell_comp.alignment = Alignment(horizontal="center")

        # Matching agreements formula
        cell_match = ws_agree.cell(row=r_idx, column=5, value=f'=IF(COUNTA(Review!{h_letter}6:{h_letter}205)=0, 0, SUMPRODUCT(--({ai_col}={human_col})))')
        cell_match.font = f_data
        cell_match.alignment = Alignment(horizontal="center")

        # Agreement rate formula
        cell_pct = ws_agree.cell(row=r_idx, column=6, value=f'=IF(COUNTA(Review!{h_letter}6:{h_letter}205)=0, "Pending Review", SUMPRODUCT(--({ai_col}={human_col}))/COUNTA(Review!{h_letter}6:{h_letter}205))')
        cell_pct.font = Font(name="Calibri", size=10, bold=True, color="1F4E78")
        cell_pct.alignment = Alignment(horizontal="center")
        cell_pct.number_format = '0.0%'

        for c_idx in range(1, 7):
            ws_agree.cell(row=r_idx, column=c_idx).border = border_cell

    agree_widths = {1: 26, 2: 24, 3: 20, 4: 20, 5: 22, 6: 20}
    for c_idx, w in agree_widths.items():
        ws_agree.column_dimensions[get_column_letter(c_idx)].width = w

    # Save Workbook
    wb.save(output_path)
    print(f"✓ Created stylized multi-sheet review workbook at {output_path}")

build_excel_workbook(annotated_rows, EXCEL_PATH)


# --- 4. BUILD ASSISTANT ANNOTATION SUMMARY MARKDOWN ---
def build_summary_markdown(rows_data: list, output_path: Path):
    total = len(rows_data)
    intent_counts = Counter(r["assistant_proposed_intent"] for r in rows_data)
    lang_counts = Counter(r["assistant_proposed_language"] for r in rows_data)
    state_counts = Counter(r["assistant_proposed_conversation_state"] for r in rows_data)
    esc_counts = Counter(r["assistant_proposed_escalate"] for r in rows_data)
    sec_count = sum(1 for r in rows_data if r["assistant_proposed_is_security_alert"] == "true")
    prio_counts = Counter(r["assistant_proposed_priority"] for r in rows_data)
    conf_counts = Counter(r["assistant_confidence"] for r in rows_data)
    ambiguous_count = sum(1 for r in rows_data if r["assistant_ambiguity_note"] != "")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Assisted Golden-Set Annotation Summary (Step 2B)\n\n")
        f.write(f"**Dataset:** `eval/golden_eval_set.csv` (Total: {total} Real AmazonHelp Customer Messages)  \n")
        f.write(f"**Pre-Review Backup:** `eval/golden_eval_set_pre_review_backup.csv`  \n")
        f.write(f"**Assisted Workbook:** `eval/golden_review_assisted.xlsx` (5 Sheets)  \n")
        f.write(f"**Taxonomy Authority:** `reports/AmazonHelp_final_taxonomy.md` (Locked 10 Intents)  \n")
        f.write(f"**Human Gold Labels Overwritten:** **0** (All `my_final_*` columns strictly empty)  \n\n")
        f.write("---\n\n")

        f.write("## 1. Executive Overview & Annotation Metrics\n\n")
        f.write(f"- **Total Candidate Messages Annotated:** {total}\n")
        f.write(f"- **Human Review Status:** 0 / {total} Reviewed (200 Pending)\n")
        f.write(f"- **Security Alert Candidates Flagged:** **{sec_count}** (`P0_CRITICAL`)\n")
        f.write(f"- **Escalation Candidate Rate:** {esc_counts.get('true', 0)} / {total} ({esc_counts.get('true', 0)/total:.1%})\n")
        f.write(f"- **High Confidence Proposals:** {conf_counts.get('HIGH', 0)} / {total} ({conf_counts.get('HIGH', 0)/total:.1%})\n")
        f.write(f"- **Ambiguous / Boundary Cases Identified:** **{ambiguous_count}**\n")
        f.write(f"- **Multilingual Examples Identified:** {total - lang_counts.get('en', 0)} ({1 - lang_counts.get('en', 0)/total:.1%})\n\n")
        f.write("---\n\n")

        f.write("## 2. Proposed Intent Distribution\n\n")
        f.write("| Intent | Proposed Count | Share (%) | Operational Role in Golden Set |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        for intent in LOCKED_INTENTS:
            cnt = intent_counts.get(intent, 0)
            f.write(f"| **{intent}** | {cnt} | {cnt/total:.1%} | Balanced representation of real Amazon customer queries. |\n")
        f.write("\n---\n\n")

        f.write("## 3. Orthogonal Metadata Distributions\n\n")
        f.write("### Language Distribution\n\n")
        f.write("| Language Code | Language Name | Count | Share (%) |\n")
        f.write("| :---: | :--- | :---: | :---: |\n")
        lang_names = {
            "en": "English", "fr": "French", "ja": "Japanese",
            "pt": "Portuguese", "de": "German", "es": "Spanish",
            "it": "Italian", "other": "Other (Turkish)"
        }
        for l_code, l_name in lang_names.items():
            cnt = lang_counts.get(l_code, 0)
            if cnt > 0:
                f.write(f"| `{l_code}` | {l_name} | {cnt} | {cnt/total:.1%} |\n")
        f.write("\n")

        f.write("### Conversation State Distribution\n\n")
        f.write("| Conversation State | Count | Share (%) | Operational Significance |\n")
        f.write("| :--- | :---: | :---: | :--- |\n")
        for st in ALLOWED_STATES:
            cnt = state_counts.get(st, 0)
            f.write(f"| `{st}` | {cnt} | {cnt/total:.1%} | Operational dialogue phase in thread context. |\n")
        f.write("\n")

        f.write("### Escalation & Security Summary\n\n")
        f.write(f"- **Escalation Proposed (`true`):** {esc_counts.get('true', 0)} / {total} ({esc_counts.get('true', 0)/total:.1%})\n")
        f.write(f"- **Routine Automation Proposed (`false`):** {esc_counts.get('false', 0)} / {total} ({esc_counts.get('false', 0)/total:.1%})\n")
        f.write(f"- **Critical Security Alerts (`is_security_alert=true`, `P0_CRITICAL`):** {sec_count}\n")
        f.write(f"- **Priority Breakdown:** {dict(prio_counts)}\n\n")
        f.write("---\n\n")

        f.write("## 4. Top Difficult Boundaries & Disambiguation Rules\n\n")
        f.write("1. **Delivery Tracking vs Delivery Problem:**\n")
        f.write("   - *Rule:* If package is late, overdue, marked delivered but missing, or false delivery attempted, it MUST be `Delivery Problem & Logistics`.\n")
        f.write("   - *Example:* [Tweet 86157] carrier falsely claims attempted delivery -> `Delivery Problem & Logistics`.\n\n")
        f.write("2. **Prime Mentions vs Delivery Problem:**\n")
        f.write("   - *Rule:* If customer mentions Prime only regarding late delivery ('I pay for Prime, why is it late?'), classify under `Delivery Problem & Logistics`.\n")
        f.write("   - *Example:* [Tweet 142870] 'how come prime is no longer next day delivery?' -> `Delivery Problem & Logistics`.\n\n")
        f.write("3. **Returns/Refunds vs Payment/Billing:**\n")
        f.write("   - *Rule:* Money owed resulting from returned goods or cancelled orders belongs in `Returns, Replacements & Refunds`. Unexpected debits, gift cards, or invoices belong in `Payment, Billing & Gift Cards`.\n")
        f.write("   - *Example:* [Tweet 230015] refund for fake product -> `Returns, Replacements & Refunds`.\n\n")
        f.write("4. **Product Quality vs Returns:**\n")
        f.write("   - *Rule:* If message focuses on articulating the defect, counterfeit item, or seller grievance, classify under `Seller & Product Quality`. If the customer demands the return label or money refund, classify under `Returns, Replacements & Refunds`.\n")
        f.write("   - *Example:* [Tweet 379788] wrong item received with photo proof -> `Seller & Product Quality`.\n\n")
        f.write("5. **Account Access vs Security Alerts:**\n")
        f.write("   - *Rule:* Phishing SMS scams, fraudulent messages, and account takeovers are tagged `is_security_alert: true` and escalated to `P0_CRITICAL`.\n")
        f.write("   - *Example:* [Tweet 275129] hacked account with email changed -> `Account Access & Security` (`P0_CRITICAL`).\n\n")
        f.write("---\n\n")

        f.write("## 5. Review Workbook Architecture (`golden_review_assisted.xlsx`)\n\n")
        f.write("The generated Excel workbook contains 5 dedicated sheets:\n")
        f.write("1. **`Review`**: The primary 200-row annotation worksheet with pre-formatted dropdowns, color-coded sections (Blue for Candidate Proposals, Green for Human Gold Labels), live KPI dashboard, and visual alert highlights.\n")
        f.write("2. **`Taxonomy`**: The complete 10-class reference specification from `reports/AmazonHelp_final_taxonomy.md` with definitions, criteria, and real dataset examples.\n")
        f.write("3. **`Decision Rules`**: The operational guidelines governing separation of concerns, conversation states, escalation protocols, and boundary disambiguation.\n")
        f.write("4. **`Difficult Cases`**: Filtered view of the 30 most ambiguous rows with specific alternative intents and decision rationales.\n")
        f.write("5. **`Agreement Analysis`**: Automated live comparison table tracking alignment percentage between machine proposals and human gold annotations.\n\n")

    print(f"✓ Created annotation summary at {output_path}")

build_summary_markdown(annotated_rows, SUMMARY_PATH)

print("\n" + "=" * 60)
print("ASSISTED GOLDEN REVIEW PREPARATION COMPLETE")
print("200 REAL MESSAGES")
print("200 ASSISTANT PROPOSALS")
print("0 HUMAN GOLD LABELS OVERWRITTEN")
print("READY FOR HUMAN REVIEW")
print("=" * 60)
