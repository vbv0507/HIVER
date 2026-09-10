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
| **Intent Classification** | Accuracy | **79.5%** | 45.0% | 39.0% |
| | Macro F1 | **0.752** | 0.304 | 0.223 |
| **Language & State** | Language Accuracy | **94.5%** | N/A | N/A |
| | State Macro F1 | **0.338** | N/A | N/A |
| **Escalation Decision** | Accuracy | **62.0%** | 60.5% | 60.5% |
| | Precision | **0.556** | 0.000 | 0.000 |
| | Recall | **0.190** | 0.000 | 0.000 |
| | F1 Score | **0.283** | 0.000 | 0.000 |
| **Security Risk (P0)** | Security Precision | **1.000** | 0.000 | 0.000 |
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
| | Top-1 Hit Rate | **41.5%** | N/A | 34.0% |
| **Latency** | Median Latency (p50) | **24.46 ms** | 0.08 ms | 22.41 ms |
| | 95th Percentile (p95) | **31.76 ms** | 0.16 ms | 29.64 ms |

*(Note: Baselines 1 & 2 do not natively produce conversation state, language detection, or P0 security alert triage; metrics are marked N/A or baseline-derived).*

---

## 2. Intent Classification Breakdown (Main Agent)

| Intent Class | Support | Precision | Recall | F1 Score |
| :--- | :---: | :---: | :---: | :---: |
| **Delivery Tracking & Status** | 9 | 1.000 | 0.444 | 0.615 |
| **Delivery Problem & Logistics** | 39 | 0.788 | 0.667 | 0.722 |
| **Returns, Replacements & Refunds** | 10 | 0.636 | 0.700 | 0.667 |
| **Payment, Billing & Gift Cards** | 4 | 0.600 | 0.750 | 0.667 |
| **Prime & Subscription Services** | 4 | 0.500 | 0.500 | 0.500 |
| **Order & Checkout** | 16 | 1.000 | 0.812 | 0.897 |
| **Account Access & Security** | 6 | 0.857 | 1.000 | 0.923 |
| **Digital Services & Devices** | 21 | 0.895 | 0.809 | 0.850 |
| **Seller & Product Quality** | 18 | 0.933 | 0.778 | 0.849 |
| **General / Feedback / Other** | 73 | 0.753 | 0.918 | 0.827 |

**Overall Intent Accuracy:** 79.5%  
**Macro Average F1:** 0.752  

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
