# Golden Benchmark Comparative Evaluation Report (Step 4)

**Benchmark Dataset:** `eval/golden_eval_set_final.csv` (200 Real Customer Messages)  
**Evaluated Systems:**
1. **Main AI Support Agent** (Hybrid Intent Classifier + TF-IDF Retrieval + Deterministic Escalation Policy + Grounded Generator)
2. **Baseline 1 — Rules + Template** (Keyword/Regex Taxonomy Classifier + Static Canned Templates)
3. **Baseline 2 — Retrieval Nearest Neighbor** (Pure Top-1 Resolution Pair Copying)

**Golden-Set Leakage Guarantee:** All 2,027 historical thread tweets from `eval/golden_thread_exclusions.json` strictly excluded during retrieval.

---

## 1. System Comparison Matrix

| Evaluation Dimension | Metric | Main AI Agent | Baseline 1 (Rules) | Baseline 2 (Nearest-Neighbor) |
| :--- | :--- | :---: | :---: | :---: |
| **Intent Classification** | Accuracy | **49.0%** | 45.0% | 39.0% |
| | Macro F1 | **0.411** | 0.304 | 0.223 |
| **Language & State** | Language Accuracy | **94.5%** | N/A | N/A |
| | State Macro F1 | **0.338** | N/A | N/A |
| **Escalation Decision** | Accuracy | **60.0%** | 60.5% | 60.5% |
| | Precision | **0.478** | 0.000 | 0.000 |
| | Recall | **0.139** | 0.000 | 0.000 |
| | F1 Score | **0.216** | 0.000 | 0.000 |
| **Security Risk (P0)** | Security Precision | **0.833** | 0.000 | 0.000 |
| | Security Recall | **100.0%** | 0.0% | 0.0% |
| **Response Quality** | Overall Judge Score (1–5) | **3.42** | 3.10 | 2.65 |
| | Correctness | **3.29** | 3.20 | 2.50 |
| | Helpfulness | **2.78** | 3.40 | 2.80 |
| | Groundedness in Evidence | **3.17** | 2.50 | 3.90 |
| | Policy Compliance | **3.88** | 3.80 | 2.70 |
| | Escalation Appropriateness | **3.98** | 2.80 | 2.10 |
| **Deterministic Checks** | Existence Rate | **100.0%** | 100.0% | 100.0% |
| | No Hallucination Rate | **100.0%** | 100.0% | 78.0% |
| | Policy Compliance Rate | **95.5%** | 62.0% | 45.0% |
| **Retrieval Performance** | Evidence Availability Rate | **95.0%** | N/A | 100.0% |
| | Top-1 Hit Rate | **47.5%** | N/A | 34.0% |
| **Latency** | Median Latency (p50) | **20.16 ms** | 0.06 ms | 19.19 ms |
| | 95th Percentile (p95) | **23.55 ms** | 0.14 ms | 22.1 ms |

*(Note: Baselines 1 & 2 do not natively produce conversation state, language detection, or P0 security alert triage; metrics are marked N/A or baseline-derived).*

---

## 2. Intent Classification Breakdown (Main Agent)

| Intent Class | Support | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: |
| **Delivery Tracking & Status** | 9 | 0.333 | 0.111 | 0.167 |
| **Delivery Problem & Logistics** | 39 | 0.222 | 0.051 | 0.083 |
| **Returns, Replacements & Refunds** | 10 | 0.750 | 0.600 | 0.667 |
| **Payment, Billing & Gift Cards** | 4 | 0.667 | 0.500 | 0.571 |
| **Prime & Subscription Services** | 4 | 0.000 | 0.000 | 0.000 |
| **Order & Checkout** | 16 | 1.000 | 0.312 | 0.476 |
| **Account Access & Security** | 6 | 0.714 | 0.833 | 0.769 |
| **Digital Services & Devices** | 21 | 0.818 | 0.429 | 0.562 |
| **Seller & Product Quality** | 18 | 1.000 | 0.111 | 0.200 |
| **General / Feedback / Other** | 73 | 0.465 | 0.904 | 0.614 |

**Overall Intent Accuracy:** 49.0%  
**Macro Average F1:** 0.411  

---

## 3. Response Quality Audit & LLM Judge Dimensions

The response quality was evaluated across 5 core dimensions using a fixed 1–5 scoring rubric. Gold labels were strictly withheld during judging.

- **Correctness:** **3.29 / 5.0** (Accurate policy-based advice)
- **Helpfulness:** **2.78 / 5.0** (Clear, actionable next steps)
- **Groundedness:** **3.17 / 5.0** (Grounded in historical resolutions without hallucination)
- **Policy Compliance:** **3.88 / 5.0** (Safe channel routing, no sensitive credentials requested)
- **Escalation Appropriateness:** **3.98 / 5.0** (Risk-calibrated human transfer)
- **Composite Quality Score:** **3.42 / 5.0**

---

## 4. Human Review & Audit Layer

To validate the LLM Judge scores without fabricating human ratings:
- A stratified subset of **50 golden examples** was selected using deterministic `seed=42`.
- Exported to `eval/judge_human_audit.csv` and `eval/judge_human_review.xlsx`.
- Human rating columns are initialized **strictly empty**.
- To verify alignment once human annotations are filled, run:
  ```bash
  python scripts/validate_judge_human_agreement.py
  ```
