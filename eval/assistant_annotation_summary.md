# Assisted Golden-Set Annotation Summary (Step 2B)

**Dataset:** `eval/golden_eval_set.csv` (Total: 200 Real AmazonHelp Customer Messages)  
**Pre-Review Backup:** `eval/golden_eval_set_pre_review_backup.csv`  
**Assisted Workbook:** `eval/golden_review_assisted.xlsx` (5 Sheets)  
**Taxonomy Authority:** `reports/AmazonHelp_final_taxonomy.md` (Locked 10 Intents)  
**Human Gold Labels Overwritten:** **0** (All `my_final_*` columns strictly empty)  

---

## 1. Executive Overview & Annotation Metrics

- **Total Candidate Messages Annotated:** 200
- **Human Review Status:** 0 / 200 Reviewed (200 Pending)
- **Security Alert Candidates Flagged:** **4** (`P0_CRITICAL`)
- **Escalation Candidate Rate:** 93 / 200 (46.5%)
- **High Confidence Proposals:** 166 / 200 (83.0%)
- **Ambiguous / Boundary Cases Identified:** **69**
- **Multilingual Examples Identified:** 63 (31.5%)

---

## 2. Proposed Intent Distribution

| Intent | Proposed Count | Share (%) | Operational Role in Golden Set |
| :--- | :---: | :---: | :--- |
| **Delivery Tracking & Status** | 9 | 4.5% | Balanced representation of real Amazon customer queries. |
| **Delivery Problem & Logistics** | 38 | 19.0% | Balanced representation of real Amazon customer queries. |
| **Returns, Replacements & Refunds** | 10 | 5.0% | Balanced representation of real Amazon customer queries. |
| **Payment, Billing & Gift Cards** | 5 | 2.5% | Balanced representation of real Amazon customer queries. |
| **Prime & Subscription Services** | 5 | 2.5% | Balanced representation of real Amazon customer queries. |
| **Order & Checkout** | 13 | 6.5% | Balanced representation of real Amazon customer queries. |
| **Account Access & Security** | 7 | 3.5% | Balanced representation of real Amazon customer queries. |
| **Digital Services & Devices** | 24 | 12.0% | Balanced representation of real Amazon customer queries. |
| **Seller & Product Quality** | 19 | 9.5% | Balanced representation of real Amazon customer queries. |
| **General / Feedback / Other** | 70 | 35.0% | Balanced representation of real Amazon customer queries. |

---

## 3. Orthogonal Metadata Distributions

### Language Distribution

| Language Code | Language Name | Count | Share (%) |
| :---: | :--- | :---: | :---: |
| `en` | English | 137 | 68.5% |
| `fr` | French | 22 | 11.0% |
| `ja` | Japanese | 16 | 8.0% |
| `pt` | Portuguese | 8 | 4.0% |
| `de` | German | 5 | 2.5% |
| `es` | Spanish | 10 | 5.0% |
| `it` | Italian | 1 | 0.5% |
| `other` | Other (Turkish) | 1 | 0.5% |

### Conversation State Distribution

| Conversation State | Count | Share (%) | Operational Significance |
| :--- | :---: | :---: | :--- |
| `new_issue` | 75 | 37.5% | Operational dialogue phase in thread context. |
| `active_troubleshooting` | 101 | 50.5% | Operational dialogue phase in thread context. |
| `dm_handoff` | 6 | 3.0% | Operational dialogue phase in thread context. |
| `follow_up` | 8 | 4.0% | Operational dialogue phase in thread context. |
| `resolved_or_acknowledgment` | 10 | 5.0% | Operational dialogue phase in thread context. |
| `unclear` | 0 | 0.0% | Operational dialogue phase in thread context. |

### Escalation & Security Summary

- **Escalation Proposed (`true`):** 93 / 200 (46.5%)
- **Routine Automation Proposed (`false`):** 107 / 200 (53.5%)
- **Critical Security Alerts (`is_security_alert=true`, `P0_CRITICAL`):** 4
- **Priority Breakdown:** {'standard': 196, 'P0_CRITICAL': 4}

---

## 4. Top Difficult Boundaries & Disambiguation Rules

1. **Delivery Tracking vs Delivery Problem:**
   - *Rule:* If package is late, overdue, marked delivered but missing, or false delivery attempted, it MUST be `Delivery Problem & Logistics`.
   - *Example:* [Tweet 86157] carrier falsely claims attempted delivery -> `Delivery Problem & Logistics`.

2. **Prime Mentions vs Delivery Problem:**
   - *Rule:* If customer mentions Prime only regarding late delivery ('I pay for Prime, why is it late?'), classify under `Delivery Problem & Logistics`.
   - *Example:* [Tweet 142870] 'how come prime is no longer next day delivery?' -> `Delivery Problem & Logistics`.

3. **Returns/Refunds vs Payment/Billing:**
   - *Rule:* Money owed resulting from returned goods or cancelled orders belongs in `Returns, Replacements & Refunds`. Unexpected debits, gift cards, or invoices belong in `Payment, Billing & Gift Cards`.
   - *Example:* [Tweet 230015] refund for fake product -> `Returns, Replacements & Refunds`.

4. **Product Quality vs Returns:**
   - *Rule:* If message focuses on articulating the defect, counterfeit item, or seller grievance, classify under `Seller & Product Quality`. If the customer demands the return label or money refund, classify under `Returns, Replacements & Refunds`.
   - *Example:* [Tweet 379788] wrong item received with photo proof -> `Seller & Product Quality`.

5. **Account Access vs Security Alerts:**
   - *Rule:* Phishing SMS scams, fraudulent messages, and account takeovers are tagged `is_security_alert: true` and escalated to `P0_CRITICAL`.
   - *Example:* [Tweet 275129] hacked account with email changed -> `Account Access & Security` (`P0_CRITICAL`).

---

## 5. Review Workbook Architecture (`golden_review_assisted.xlsx`)

The generated Excel workbook contains 5 dedicated sheets:
1. **`Review`**: The primary 200-row annotation worksheet with pre-formatted dropdowns, color-coded sections (Blue for Candidate Proposals, Green for Human Gold Labels), live KPI dashboard, and visual alert highlights.
2. **`Taxonomy`**: The complete 10-class reference specification from `reports/AmazonHelp_final_taxonomy.md` with definitions, criteria, and real dataset examples.
3. **`Decision Rules`**: The operational guidelines governing separation of concerns, conversation states, escalation protocols, and boundary disambiguation.
4. **`Difficult Cases`**: Filtered view of the 30 most ambiguous rows with specific alternative intents and decision rationales.
5. **`Agreement Analysis`**: Automated live comparison table tracking alignment percentage between machine proposals and human gold annotations.

