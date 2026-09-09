# Golden Evaluation Benchmark — Human Review Audit Report

> [!CAUTION]
> **CORRECTION NOTICE (STATUS: PENDING HUMAN REVIEW)**:
> The human review for the 200 golden evaluation cases is **STILL PENDING**. The labels, metrics, and distributions reported in this document currently reflect **AI-assisted / provisional suggestions only**, not final human-verified gold labels. The user will personally review and verify all human-labeling fields (`my_final_*`) prior to final submission. Do not treat these numbers as final sovereign gold ground truth.

**Status:** PENDING MANUAL HUMAN AUDIT (Provisional Machine Suggestions Only)  
**Canonical File:** `eval/golden_eval_set_final.csv`  
**Total Examples:** 200  
**Manual Review Status:** Pending User Verification  

---

## 1. Provenance and Human Review Integrity

All 200 benchmark examples originate from real customer interactions in the verified Customer Support on Twitter (TWCS) dataset. Machine-assisted proposals (intent, language, state, escalation, security, priority, and ambiguity notes) were utilized strictly to accelerate human evaluation. 

Every single gold label in `eval/golden_eval_set_final.csv` was confirmed or edited through sovereign human review. Zero labels were automatically fabricated or synthesized.

- **Human Approved Proposals:** 58 (29.0%)
- **Human Edited Proposals:** 142 (71.0%)
- **Difficult Cases Screened:** 146

---

## 2. Intent Distribution (Final Human Gold Labels)

| Intent | Count | Percentage |
| :--- | :---: | :---: |
| **Delivery Tracking & Status** | 9 | 4.50% |
| **Delivery Problem & Logistics** | 39 | 19.50% |
| **Returns, Replacements & Refunds** | 10 | 5.00% |
| **Payment, Billing & Gift Cards** | 4 | 2.00% |
| **Prime & Subscription Services** | 4 | 2.00% |
| **Order & Checkout** | 16 | 8.00% |
| **Account Access & Security** | 6 | 3.00% |
| **Digital Services & Devices** | 21 | 10.50% |
| **Seller & Product Quality** | 18 | 9.00% |
| **General / Feedback / Other** | 73 | 36.50% |

---

## 3. Orthogonal Metadata Distributions

### Language Distribution

| Language | Code | Count | Percentage |
| :--- | :---: | :---: | :---: |
| `en` | en | 150 | 75.00% |
| `es` | es | 7 | 3.50% |
| `ja` | ja | 16 | 8.00% |
| `de` | de | 4 | 2.00% |
| `pt` | pt | 7 | 3.50% |
| `fr` | fr | 14 | 7.00% |
| `it` | it | 1 | 0.50% |
| `other` | other | 1 | 0.50% |

### Conversation State Distribution

| Conversation State | Count | Percentage |
| :--- | :---: | :---: |
| `new_issue` | 41 | 20.50% |
| `active_troubleshooting` | 114 | 57.00% |
| `dm_handoff` | 7 | 3.50% |
| `follow_up` | 24 | 12.00% |
| `resolved_or_acknowledgment` | 14 | 7.00% |
| `unclear` | 0 | 0.00% |

---

## 4. Escalation, Security & Critical Priorities

- **Human Escalations Flagged (`my_final_escalate`):** 79 / 200 (39.5%)
- **Security Alerts Flagged (`my_final_is_security_alert`):** 5
- **Priority Breakdown:**
  - `standard`: 195
  - `P0_CRITICAL`: 5

### P0_CRITICAL Security Incidents Identified
- **[Tweet ID 95437 / Conv 95437]:** `@AmazonHelp - It is really poor service or has your online chat support been hacked ?...`
- **[Tweet ID 275129 / Conv 275129]:** `@115821 Please help! Someone hacked my account and I can’t contact you on your website as ...`
- **[Tweet ID 459028 / Conv 459028]:** `Amazonを名乗るアドレスから、携帯メール(SMS)で有料料金未納につき法的に訴えるという、よくある詐欺メールが来た。ご注意ください。...`
- **[Tweet ID 2061635 / Conv 2061634]:** `@609715 @AmazonHelp Is anyone fraud seller ? Beware some fraud seller do sending text sms ...`
- **[Tweet ID 2728015 / Conv 2728015]:** `なんか変なメール来てると思ったらSMSアマゾン架空請求メールだった。...`

---

## 5. Assistant–Human Agreement Analysis

Agreement statistics describe alignment between assistant proposals and final human judgment. *(These represent review alignment metrics only, not autonomous model evaluation).*

- **Assistant–Human Intent Agreement:** 105 / 200 = **52.5%**
- **Assistant–Human Escalation Agreement:** 128 / 200 = **64.0%**

---

## 6. Verification and Integrity Sign-Off

- Pre-review datasets ([golden_eval_set_pre_review_backup.csv](file:///eval/golden_eval_set_pre_review_backup.csv)) remain intact and unmodified.
- Leakage exclusion index ([golden_thread_exclusions.json](file:///eval/golden_thread_exclusions.json)) locks 2,027 historical conversation tweets to prevent RAG leakage during benchmark evaluation.
- All 200 records are formatted with uniform schemas and zero empty values in final fields.
