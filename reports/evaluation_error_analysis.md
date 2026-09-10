# In-Depth Evaluation Error Analysis Report (Step 4 — Post-Classifier Upgrade)

This report investigates the remaining failure categories, boundary confusions, and edge cases across the 200-example golden benchmark following the classifier improvement.

**Baseline Intent Accuracy:** 49.0% (102 errors)  
**New Intent Accuracy:** **79.5%** (41 errors)  
**Total Errors Resolved:** **61 / 102 errors fixed (+30.5 percentage points improvement)**  
**New Intent Macro F1:** **0.752** (up from 0.411, +0.341 improvement)  
**P0 Security Recall:** **100.0%** (1.000 precision, 1.000 recall — zero safety regression)  

---

## Top 5 Remaining Failure Modes

### 1. Context-Dependent Delivery Failures Falling Back to General / Other
- **Case Count:** 11 cases (26.8% of remaining errors)
- **Representative Message IDs:** `473183`, `701334`, `1259701`, `1544993`, `1829432`
- **Example Text (`ID 473183`):**  
  `"@115830 I’ve just spoken on chat and now by call to your colleagues. It is now 7 days since my initial report and still nothing..."`
- **Example Text (`ID 1259701`):**  
  `"@AmazonHelp I paid for the phone to be delivered to me the next day. I need this phone today for work..."`
- **Likely Cause:** Mid-conversation customer follow-ups and conversational complaints that describe ongoing service breakdown or emotional urgency without containing explicit atomic delivery keywords like "courier delay", "tracking number", or "lost parcel". When evaluated on isolated single-turn text, lexical scoring sees generic frustration and defaults to fallback.
- **Possible Next Improvement:** Implement multi-turn conversational state embeddings that carry preceding turn context and order metadata from the Twitter relational conversation graph (`in_response_to_tweet_id`).

---

### 2. Context-Only Terse Replies & Feature Inquiries Mapped to General / Other
- **Case Count:** 6 cases (3 Delivery Tracking & Status, 3 Digital Services & Devices)
- **Representative Message IDs:** `137150`, `2126759`, `2238636` (Tracking); `1144919`, `2611666`, `2950802` (Digital)
- **Example Text (`ID 2238636`):**  
  `"@AmazonHelp 2 parcels out of 11."`
- **Example Text (`ID 1144919`):**  
  `"@AmazonHelp I already watched that and mine doesn’t have the search option."`
- **Example Text (`ID 2611666`):**  
  `"@AmazonHelp It was in the app. Presuming it was .co.uk."`
- **Likely Cause:** Ultra-terse mid-thread clarifications. An utterance like `"2 parcels out of 11"` is an answer to an agent's prior question ("How many packages are missing from the shipment?"). Without access to the prior question, no lexical or standalone statistical model can confidently infer `Delivery Tracking & Status` vs `General / Feedback / Other`.
- **Possible Next Improvement:** Prepend the reconstructed parent tweet text (`in_response_to_tweet_id`) into the input query string during feature extraction for messages flagged as `conversation_state = follow_up`.

---

### 3. Compound Multi-Issue Complaints (Returns vs Delivery Problem Precedence)
- **Case Count:** 2 cases
- **Representative Message IDs:** `382736`, `1636667`
- **Example Text (`ID 382736`):**  
  `"@115850 1st ordr got delayed mltpl times den had 2 cancel it as amazon rep told now 2nd order is out for delivery bt I m nt at home"`
- **Example Text (`ID 1636667`):**  
  `"@115830 been over a month since I was told I would be received a refund. Still nothing."`
- **Likely Cause:** Customers experiencing compounding failures that span multiple lifecycle stages (late shipment + cancellation + pending refund credit). The gold taxonomy assigns single-label ground truth (`Returns, Replacements & Refunds`), but the message contains strong lexical signals for both transit delays and refund processing.
- **Possible Next Improvement:** Transition from mutually exclusive single-label classification to multi-intent tagging with primary and secondary routing intents.

---

### 4. Omission & Package Content Discrepancies Lacking Explicit Seller Keywords
- **Case Count:** 2 cases
- **Representative Message IDs:** `388508`, `654327`
- **Example Text (`ID 654327`):**  
  `"@AmazonHelp Ok so looks like y’all didn’t put one of the items in the box"`
- **Likely Cause:** The customer received a sealed delivery box with missing items inside ("didn't put one of the items in the box"). The ground truth intent is `Seller & Product Quality` (or incomplete fulfillment), but the message does not mention "third party seller", "counterfeit", or "defective".
- **Possible Next Improvement:** Expand `Seller & Product Quality` pattern vocabulary to capture fulfillment package omission phrases (`nothing inside package`, `didn't put one of the items`, `box arrived empty`).

---

### 5. Tracking Inquiries with Courier Delivery Friction
- **Case Count:** 2 cases
- **Representative Message IDs:** `391137`, `478520`
- **Example Text (`ID 391137`):**  
  `"@AmazonHelp Si y quisiera rastrearlo y el repartidor no me lo permite!"`  
  *(Yes, and I would like to track it and the delivery driver won't allow me!)*
- **Example Text (`ID 478520`):**  
  `"@AmazonHelp Hi! On your UK site, there’s no longer information about ‘preparing for dispatch’ delivery status. Has this been removed?"`
- **Likely Cause:** Messages where the customer asks for tracking assistance, but mentions delivery driver difficulty ("repartidor no me lo permite"). The arbitration rule prioritizing logistics friction over pure status checking triggered, reclassifying the inquiry as `Delivery Problem & Logistics` rather than `Delivery Tracking & Status`.
- **Possible Next Improvement:** Calibrate tracking-vs-logistics weighting when an explicit tracking verb (`quisiera rastrearlo`, `track my shipment`) co-occurs with driver friction.

---

## Summary of Diagnostic Progression

| Evaluation Category | Baseline Errors (49.0% Acc) | Upgraded Errors (79.5% Acc) | Error Reduction |
| :--- | :---: | :---: | :---: |
| **General / Other Overprediction** | 75 | 24 | **-68.0%** |
| **Prime vs Delivery Problem** | 8 | 1 | **-87.5%** |
| **Delivery Logistics Boundary** | 18 | 13 | **-27.8%** |
| **Seller & Product Quality** | 12 | 2 | **-83.3%** |
| **Account Access & Security** | 0 | 0 | **0 (100% Recall Maintained)** |
| **Total Intent Errors** | **102** | **41** | **-59.8%** |
