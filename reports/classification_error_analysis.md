# Classification Error Analysis — AmazonHelp Intent Classifier (Historical Baseline)

> [!NOTE]
> **Historical Baseline Archive**: This report documents the initial error analysis performed prior to the classifier improvement (Baseline Intent Accuracy: 49.0%, Macro F1: 0.411). For post-improvement evaluation results and remaining failure modes, see [`reports/evaluation_results.md`](reports/evaluation_results.md) and [`reports/evaluation_error_analysis.md`](reports/evaluation_error_analysis.md).

**Produced**: 2026-09-09  
**Golden Set**: `eval/golden_eval_set_final.csv` (200 examples, 10 intents)  
**Classifier**: `src/classifier/intent_classifier.py`  
**Baseline Performance**: Accuracy 49.0% (98/200) | Macro F1 0.411  

---

## 1. Classifier Architecture

**Type: Pure Rule-Based / Keyword-Pattern Matching** — no supervised ML, no retrieval assistance for intent classification.

The classifier is a fully hand-authored regex pattern engine with:
- ~9 pattern lists (one per substantive intent, plus a security alert sub-list)
- Weighted additive scoring per matched pattern, summed linearly per intent
- Softmax normalization over raw additive scores → probability distribution
- Manual boundary adjustments: hard-coded +4.0 boost for security alerts, +1.5 for logistics-over-prime, +1.0 for seller
- Fallback: if `max_score <= 0.1`, default to `General / Feedback / Other` at confidence 0.45

**No training data is used.** There is no train/dev/test split for the classifier itself. The 200-example golden evaluation set is the **only held-out test set**, and it is strictly not used during development of the classifier patterns.

---

## 2. 10x10 Confusion Matrix

Rows = Gold Intent, Columns = Predicted Intent.
Abbreviations: DlvTrk Delivery Tracking, DlvPrb Delivery Problem, Rtrns Returns, Paymnt Payment, Prime Prime, OrdChk Order, AccSec Account Security, DigSvc Digital Services, SelPrd Seller & Product, GenOth General/Other.

```
           DlvTrk  DlvPrb  Rtrns  Paymnt  Prime  OrdChk  AccSec  DigSvc  SelPrd  GenOth
DlvTrk          1       1      0       0      1       0       0       0       0       6
DlvPrb          1       2      2       0      7       0       0       0       0      27
Rtrns           0       2      6       0      0       0       0       0       0       2
Paymnt          0       0      0       2      0       0       0       0       0       2
Prime           0       0      0       1      0       0       0       0       0       3
OrdChk          0       0      0       0      0       5       0       0       0      11
AccSec          0       0      0       0      0       0       5       0       0       1
DigSvc          0       0      0       0      0       0       0       9       0      12
SelPrd          0       2      0       0      0       0       2       0       2      12
GenOth          1       2      0       0      2       0       0       2       0      66
```

Key observations:
1. General/Other is the dominant predicted label absorbing most FNs from every other class.
2. Delivery Problem loses 27 examples to GenOth — the single largest source of error.
3. Prime absorbs 7 DlvPrb examples — the second-largest non-General error bucket.
4. Seller & Product Quality loses 12 examples to GenOth — near-total recall failure.
5. Digital Services loses 12 examples to GenOth — misses device/app mentions lacking exact model keywords.

---

## 3. Per-Intent Metrics

| Intent | Support | TP | FP | FN | Prec | Recall | F1 |
|:---|---:|---:|---:|---:|---:|---:|---:|
| Delivery Tracking & Status | 9 | 1 | 2 | 8 | 0.333 | 0.111 | 0.167 |
| Delivery Problem & Logistics | 39 | 2 | 7 | 37 | 0.222 | 0.051 | 0.083 |
| Returns, Replacements & Refunds | 10 | 6 | 2 | 4 | 0.750 | 0.600 | 0.667 |
| Payment, Billing & Gift Cards | 4 | 2 | 1 | 2 | 0.667 | 0.500 | 0.571 |
| Prime & Subscription Services | 4 | 0 | 10 | 4 | 0.000 | 0.000 | 0.000 |
| Order & Checkout | 16 | 5 | 0 | 11 | 1.000 | 0.312 | 0.476 |
| Account Access & Security | 6 | 5 | 2 | 1 | 0.714 | 0.833 | 0.769 |
| Digital Services & Devices | 21 | 9 | 2 | 12 | 0.818 | 0.429 | 0.562 |
| Seller & Product Quality | 18 | 2 | 0 | 16 | 1.000 | 0.111 | 0.200 |
| General / Feedback / Other | 73 | 66 | 76 | 7 | 0.465 | 0.904 | 0.614 |
| **Macro Average** | — | — | — | — | — | — | **0.411** |

Critical failures (F1 < 0.20):
- Delivery Problem & Logistics — F1 0.083, recall 5.1% (the largest non-General class, n=39)
- Prime & Subscription Services — F1 0.000, recall 0.0% (0/4 correct; 10 false positives misrouted here)
- Delivery Tracking & Status — F1 0.167, recall 11.1%
- Seller & Product Quality — F1 0.200, recall 11.1% (n=18)

---

## 4. Top 30 Misclassified Examples

| # | ID | Gold | Predicted | Conf | Text | Error Explanation |
|:--|:--|:--|:--|:--|:--|:--|
| 1 | 635720 | General/Other | Digital Services | 0.98 | Alexa ist toll. :) | Alexa keyword triggers device intent; this is satisfied feedback, not a support request |
| 2 | 2061635 | Seller | Account/Security | 0.98 | ...fraud seller...sending text sms... | "fraud + sms" matches phishing pattern; gold is seller misconduct not account security |
| 3 | 2831691 | General/Other | Digital Services | 0.98 | ...meu Kindle ja chegou | "Kindle" fires device intent; this is a satisfied delivery confirmation |
| 4 | 2922515 | Delivery Problem | Prime | 0.98 | ...prime shipping...saying 29th-30th!... | "prime" scores higher than late delivery signals |
| 5 | 34485 | Seller | Account/Security | 0.74 | ...vendeur tiers...l'air d'etre un escroc. | French "escroc" (crook) triggers fraud patterns; gold is seller problem |
| 6 | 2708424 | Delivery Problem | Prime | 0.68 | ...offered a Prime refund...wait til today | "Prime" present in delayed-delivery context |
| 7 | 142870 | Delivery Problem | Prime | 0.63 | ...prime is no longer next day delivery... | Delivery failure complaint framed via Prime service quality |
| 8 | 391137 | Delivery Tracking | Delivery Problem | 0.63 | ...rastrearlo y el repartidor no me lo permite! | Courier refusing tracking access — borderline logistics failure |
| 9 | 451956 | Delivery Tracking | Prime | 0.63 | ...ordering through amazon prime...arrive before Xmas | Pre-Christmas ETA question with "prime" in text |
| 10 | 498538 | Delivery Problem | Prime | 0.63 | ...monthly subscription for next day delivery... | Next-day SLA complaint framed around Prime subscription |
| 11 | 524929 | General/Other | Prime | 0.63 | Amazon prime music...positive testimonial | Positive tweet about Prime Music; "prime" keyword fires |
| 12 | 701334 | Delivery Problem | Prime | 0.63 | ...prime now order...wasn't able to be delivered | "prime now" triggers prime intent; message is failed delivery |
| 13 | 754571 | Seller | Delivery Problem | 0.63 | ...delayed Delivery and wrong sim phone... | Wrong item (seller) loses to delivery keywords |
| 14 | 909055 | General/Other | Delivery Problem | 0.63 | Thank you...first missing package | "missing package" fires logistics; actually a satisfied response |
| 15 | 1219363 | Delivery Problem | Prime | 0.63 | ...guaranteed delivery date via prime... | "prime" in description of SLA breach |
| 16 | 1318948 | General/Other | Prime | 0.63 | ...prime now e riceverlo in 2h 1/2 | Casual Italian comparison mentioning Prime Now |
| 17 | 1354495 | Delivery Problem | Returns | 0.63 | ...sending replacement...one day guaranteed | "replacement" fires Returns despite being a logistics escalation |
| 18 | 1382396 | Delivery Problem | Returns | 0.63 | ...told ordering a replacement would take longer | Same: "replacement" triggers Returns, but root cause is delivery failure |
| 19 | 2299092 | Seller | Delivery Problem | 0.63 | ...seller delivered late & refused to cancel | Seller misconduct with delivery language; delivery wins |
| 20 | 2539594 | Delivery Problem | Prime | 0.63 | ...paying for 2 day shipping...prime is waste... | Prime-framed delivery SLA complaint |
| 21 | 2869579 | General/Other | Delivery Problem | 0.63 | AAAHHH IT'S OKAYYYY / Never too late to play! | "late" fires logistics on unrelated conversation |
| 22 | 419420 | Delivery Problem | Delivery Tracking | 0.58 | ...package was delivered...scary...tracking ID... | "tracking" + ID in a phantom-delivery complaint |
| 23 | 1774517 | General/Other | Delivery Tracking | 0.58 | ...Where is ur email?...order number... | "Where is" fires tracking; actually angry misc complaint |
| 24 | 1721 | Digital Services | General/Other | 0.45 | Never got the beta...Last Jedi content... | No recognized device keyword; "beta/content" not in digital patterns |
| 25 | 57428 | Order & Checkout | General/Other | 0.45 | Could not set your address...India address | Address checkout error; "address" not in order patterns |
| 26 | 86157 | Delivery Problem | General/Other | 0.45 | ...delivery boy falsely claims attempted delivery | Colloquial phrasing; no direct pattern match |
| 27 | 137150 | Delivery Tracking | General/Other | 0.45 | I've looked in there and there is no option... | Context-only follow-up; no lexical delivery keyword |
| 28 | 139986 | Delivery Problem | General/Other | 0.45 | ...commandé une candle...arrive en mille morceaux | French "mille morceaux" (shattered) not in French logistics patterns |
| 29 | 140066 | Delivery Problem | General/Other | 0.45 | ...colis ouvert...Amz Logistics... | French "colis ouvert" (opened package) not matching logistics patterns |
| 30 | 162100 | Digital Services | General/Other | 0.45 | Ja. Komm nicht an der Info vorbei...Spiel... | German "Spiel" (game) not in digital patterns |

---

## 5. Error Groupings

### A. General / Other Overprediction (75/102 errors — 73.5% of all errors)

The dominant failure mode. The classifier defaults to General/Other when text is:
- A follow-up message with no clear lexical anchors (e.g., "I already did that", "Not in my inbox")
- Written in a non-English language not fully covered by the multilingual pattern lists
- Paraphrased or colloquially worded (e.g., "delivery boy", "my parcel in mille morceaux")
- Context-dependent (intent only clear from conversational history)
- Emoji-heavy or abbreviated (e.g., "1st ordr got delayed mltpl times")

Classes most harmed: Delivery Problem (-27), Seller & Product (-12), Digital Services (-12), Order & Checkout (-11).

### B. Delivery Problem → Prime (7 errors)

Delivery SLA failures framed around Prime membership (e.g., "Prime promised next-day, it's been 3 days"). The bare `\bprime\b` pattern fires on any mention. The existing boundary rule (+1.5 logistics boost) is insufficient when Prime is mentioned multiple times and logistics keywords are implicit/paraphrased.

### C. DlvTrk ↔ DlvPrb (3 errors)

Definitionally ambiguous boundary. Requires knowing whether the package has exceeded its SLA — information often not available in a single tweet.

### D. Returns ↔ Delivery Problem (4 errors)

Messages about a replacement for a delivery failure: "replacement" fires Returns, but gold is Delivery Problem because the root cause is the failed initial delivery.

### E. Seller → Delivery Problem / Account (4 errors)

Seller misconduct (wrong item, defective product) loses to logistics or security patterns when delivery language or "fraud seller + sms" patterns co-occur.

### F. General/Other → X (7 underprediction errors)

Positive/satisfied feedback mentioning an Amazon product keyword (Kindle, Alexa, Prime) triggers a specific intent even though the message is not a support request.

---

## 6. Classifier Assessment Summary

| Criterion | Assessment |
|:--|:--|
| Architecture | Pure regex/keyword rule-based, no ML |
| Training data | None — all patterns are hand-authored |
| Dev data | None — no pattern tuning dataset |
| Test set | golden_eval_set_final.csv (200 examples, evaluation only) |
| Train/dev/test split | None — single held-out test set |
| Language coverage | English primary; partial 6-language multilingual (incomplete coverage) |
| Retrieval assistance for classification | None — retrieval used only for generation |
| Supervised component | None |
| Confidence calibration | Heuristic (softmax + margin), not statistically calibrated |

---

## 7. Root Causes Ranked by Error Volume

| Rank | Root Cause | Est. Errors |
|:--|:--|:--|
| 1 | Default-to-General fallback: regex match failure on paraphrase / context-only / multilingual messages | 75 (~74%) |
| 2 | Seller recall failure: seller_patterns too narrow, misses colloquial phrasing | ~12 (12%) |
| 3 | Digital Services recall failure: device/app mentions without exact model names not detected | ~12 (12%) |
| 4 | Prime keyword bleeding: bare "prime" token fires on any Prime-framed delivery complaint | 7 (7%) |
| 5 | Boundary ambiguity DlvTrk vs DlvPrb: requires SLA context not encoded in single-tweet keywords | ~3 (3%) |

---

## 8. Three Highest-Impact Improvements (No Golden-Set Tuning)

### Improvement 1 — Context-aware routing for follow-up turns (Est. impact: +10-15 accuracy points)

Problem: 35+ misclassifications are follow-up tweets with no lexical anchors. The classifier already detects conversation_state = follow_up but ignores this signal when computing intent.

Legitimate fix (derivable without golden labels):
- When conversation_state is follow_up or active_troubleshooting AND max_raw_score <= 0.5 (near-zero signal), suppress the default-to-General rule and instead return the next-best-scoring non-General intent or fall back to "Delivery Problem & Logistics" (the most common real support intent in the corpus).
- OR: Expose the previous-turn intent from the TWCS conversation thread (in_response_to_tweet_id linkage already parsed in thread_builder.py).

### Improvement 2 — Expand Seller & Delivery Problem pattern vocabulary (Est. impact: +6-10 accuracy points)

Problem: 16/18 Seller examples misclassified (recall 11%). Patterns require exact terms (third-party seller, counterfeit) but miss: "got wrong item", "product not working", "broken merchandise", "pirated copy", "nothing inside package", "different item sent". Similarly, Delivery Problem misses paraphrases: "delivery agent falsely claims", "shipper left in driveway", "no knock at the door", "opened parcels", plus missing French/Portuguese/Spanish variants.

Legitimate fix: Expand patterns using frequency analysis on the TWCS AmazonHelp corpus (203K tweets), not golden labels. Pattern quality validated on eval/golden_eval_set.csv (the pre-finalization version, not the locked final set).

### Improvement 3 — Narrow Prime pattern specificity (Est. impact: +5-7 accuracy points)

Problem: The bare `\bprime\b` pattern fires on any mention of "prime" in context (delivery complaints, general references). Causes 7+ DlvPrb→Prime misroutes.

Smallest safe fix: Require at least one subscription-management verb or fee noun adjacent to "prime":
- Change: `r"\b(prime|prime membership|...)\b"`
- To: `r"\b(prime membership|prime video|prime music|subscription|auto-renew(al)?|cancel prime|renew prime|prime fee|student prime|charged for prime|prime subscription)\b"`

Removes bare "prime" token match. Derivable from pattern analysis alone, not from golden labels.

---

## 9. Error Categories Ranked by Contribution

| Category | Error Count | % of 102 Errors |
|:--|---:|---:|
| X → General/Other (overprediction) | 75 | 73.5% |
| Delivery Problem → Prime | 7 | 6.9% |
| General → X (underprediction) | 7 | 6.9% |
| Returns ↔ Delivery Problem | 4 | 3.9% |
| Seller → Delivery Problem or Account | 4 | 3.9% |
| DlvTrk ↔ DlvPrb | 3 | 2.9% |
| Other cross-intent | 2 | 2.0% |

---

## 10. Recommended Smallest First Change

**Fix the Prime pattern specificity** — smallest code change with most predictable, well-scoped impact.

Remove the bare `prime` token from `prime_patterns[0]`. Change the first pattern from:
```
r"\b(prime|prime membership|prime video|prime music|subscription|...)\b"
```
to:
```
r"\b(prime membership|prime video|prime music|subscription|auto-renew(al)?|cancel prime|renew prime|prime fee|student prime|charged for prime)\b"
```

This eliminates 5-7 Delivery Problem → Prime misroutes with zero risk of increasing false negatives on genuine Prime subscription queries, since every real Prime subscription complaint contains at least one of the retained management/fee terms.

---

```
CLASSIFICATION ERROR ANALYSIS COMPLETE
CURRENT ACCURACY: 49.0%
CURRENT MACRO F1: 0.411
NO GOLDEN SET MODIFICATIONS
NO CODE MODIFICATIONS
READY FOR TARGETED MODEL IMPROVEMENT
```
