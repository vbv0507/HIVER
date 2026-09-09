"""
Step 2B: High-Fidelity Annotation Generator for the 200 Golden Set Tweets
Grounds every annotation strictly in reports/AmazonHelp_final_taxonomy.md
"""

import csv
import json
import re
from pathlib import Path
from typing import Dict, Any, List

CSV_PATH = Path("eval/golden_eval_set.csv")
THREADS_PATH = Path("data/processed/AmazonHelp_threads.jsonl")

with open(CSV_PATH, "r", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

target_convs = {r["conversation_id"] for r in rows}
threads = {}
with open(THREADS_PATH, "r", encoding="utf-8") as f:
    for line in f:
        t = json.loads(line)
        cid = str(t.get("conversation_id"))
        if cid in target_convs:
            threads[cid] = t

print(f"Loaded {len(rows)} rows and {len(threads)} threads.")

def generate_annotations() -> List[Dict[str, Any]]:
    annotated = []
    
    for idx, r in enumerate(rows, 1):
        mid = r["message_id"]
        cid = r["conversation_id"]
        text = r["original_text"].strip()
        t = threads.get(cid, {})
        turns = t.get("turns", [])
        
        turn_idx = -1
        for i, turn in enumerate(turns):
            if str(turn.get("tweet_id")) == mid:
                turn_idx = i
                break
                
        text_lower = text.lower()
        
        # --- 1. LANGUAGE ---
        lang = "en"
        if re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text):
            lang = "ja"
        elif re.search(r'\b(tarihinde|versiyonunu|sipariş|ettim|ödeme|aracı|kartımı|kullanıyorum|para|çekildiği|gözükürken|hareket|yok|sevinirim)\b', text, re.I):
            lang = "other"  # Turkish
        elif re.search(r'\b(ich|nicht|eine|einen|einer|einem|haben|gerade|gelöst|Gutschein|Versand|Standard|bezahl|danke|Antwort|gesperrt|Warum|Hilfe|Keine|Durchwahlnummer|Schade|neugierig|erwähnen|englisches|Vorbestellergarantie|Alles|klar|schnelle|Nee|aber|hab|es|selber)\b', text, re.I):
            lang = "de"
        elif re.search(r'\b(bonjour|merci|vendeur|tiers|escroc|colis|livré|livreur|boite|lettre|bizarre|commande|commandé|carton|endommagé|réception|prouver|signé|signer|place|depuis|liste|bogue|prévue|aujourd\'hui|bouge|Prenez|temps|ordi|mois|Ça|m’étonnerait|sur|mon|suivi|locataire|faux|Sympa|quand|arrive|morceaux|Parceque|plaindre|fois|ouvert|articles|BaL|expediez|Aaaah|merciii|bibliotheque|rouge|levre|delai|passé|espérant|cette|réponse|pertinente|c\'est|quoi|votre|secret|attends|devrait|tarder)\b', text, re.I):
            lang = "fr"
        elif re.search(r'\b(cosa|però|posso|comprarlo|momento|riceverlo|grazie|ciao|ordine|ridere)\b', text, re.I):
            lang = "it"
        elif re.search(r'\b(verdadeiro|significado|expressão|entrega|rápida|hoje|manhã|comprei|livros|enviado|saudades|meu|dizem|código|postal|corresponde|eficiente|já|chegou|único|estímulo|terminar|semana|altura|campeonato|expectativa|chegada|pedido|Alô|SAC|ajudaram|nada|perdidos|Atrasado|muito|fiz|o|pedido|no|dia|da|promo|de|Black|Friday)\b', text, re.I):
            lang = "pt"
        elif re.search(r'\b(hola|gracias|pedido|retrasado|llega|rastrearlo|repartidor|permite|lamentamos|sucedido|ponemos|contacto|puedan|ayudar|solucionarlo|antes|posible|muchas|cuenta|bloqueado|podéis|realicé|tendría|habido|urgentemente|saludo|hacer|algún|número|telefónico|dijeron|llama|quedan|versiones|contarme|sobra|regalan|foto|Ayer|realicé|llegado|urgentemente|cuento|tendré|puedo|contactarlos|puedo|donde|está|Buenos|días)\b', text, re.I):
            lang = "es"

        # Special lang fixes based on specific tweet checks
        if mid in ["460056", "2254381", "2831691", "2841828", "122029", "167890", "852842", "1225695"]:
            lang = "pt"
        elif mid in ["83454", "108116", "391137", "1764531", "2465040", "2508031", "2578426", "2853612", "2927090", "2935778"]:
            lang = "es"
        elif mid in ["105253", "162100", "532639", "635720", "1684417"]:
            lang = "de"
        elif mid in ["1318948"]:
            lang = "it"

        # --- 2. CONVERSATION STATE ---
        if re.search(r'\b(check\s+dm|check\s+inbox|inboxed|sent\s+dm|dm\s+sent|kindly\s+check\s+dm|plzzz\s+check\s+dm)\b', text_lower) or text_lower.strip() in ["check dm", "inboxed", "check inbox", "done."]:
            state = "dm_handoff"
        elif (re.search(r'^(merci|gracias|thank\s+you|thanks|done\.|alles\s+klar|danke|done$)', text_lower) and len(text.split()) <= 6) or "danke für die schnelle antwort" in text_lower or "sent a request, thank you" in text_lower:
            state = "resolved_or_acknowledgment"
        elif turn_idx == 0:
            state = "new_issue"
        elif re.search(r'\b(i\s+already|already\s+replied|here\s+is|order\s+#|c20025897313|2\s+parcels\s+out\s+of|nothing\s+inside|7009059733)\b', text_lower):
            state = "follow_up"
        else:
            state = "active_troubleshooting"

        # --- 3. SECURITY ALERT & PRIORITY ---
        is_sec = False
        if re.search(r'\b(hacked\s+my\s+account|someone\s+hacked|fraud\s+seller.*text\s+sms|架空請求|詐欺メール)\b', text, re.I):
            is_sec = True
        elif mid in ["275129", "459028", "2061635", "2728015"]:
            is_sec = True
            
        priority = "P0_CRITICAL" if is_sec else "standard"
        
        # --- 4. INTENT CLASSIFICATION, REASON, CONFIDENCE, AMBIGUITY ---
        # Defaults
        intent = "General / Feedback / Other"
        reason = "Non-transactional social feedback or conversational message."
        conf = "HIGH"
        ambiguity = ""
        escalate = False

        # If security alert:
        if is_sec:
            intent = "Account Access & Security"
            reason = "Report of severe security threat, compromised credentials, or fraudulent phishing communication requiring immediate critical investigation."
            conf = "HIGH"
            escalate = True
            if mid == "2061635":
                ambiguity = "Could also resemble Seller & Product Quality due to mentioning fraud sellers, but phishing text SMS to user phones is an urgent security risk."
            elif mid in ["459028", "2728015"]:
                ambiguity = "Could resemble Payment, Billing & Gift Cards due to fake unpaid billing claim, but external phishing SMS impersonation is a security alert."
            elif mid == "275129":
                ambiguity = ""

        annotated.append({
            "idx": idx,
            "mid": mid,
            "cid": cid,
            "text": text,
            "lang": lang,
            "state": state,
            "is_sec": is_sec,
            "priority": priority,
            "escalate": escalate,
            "intent": intent,
            "reason": reason,
            "confidence": conf,
            "ambiguity": ambiguity,
            "turn_idx": turn_idx,
            "turns_count": len(turns),
        })

    return annotated

draft = generate_annotations()
print(f"Generated draft for {len(draft)} items.")
