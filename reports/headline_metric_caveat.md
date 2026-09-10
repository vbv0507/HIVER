# Headline Metric Caveats & Evaluation Limitations Report (Step 4 — Final Audit)

> [!WARNING]
> **Executive Warning: Why Headline Metrics Can Mislead**
> High-level summary metrics (such as **79.5% Intent Accuracy**, **0.752 Macro F1**, or **3.42/5.0 Response Quality**) provide valuable directional milestones, but hide critical operational nuances, class imbalances, and real-world edge cases. Production deployment decisions must be grounded in granular class-level telemetry and safety guardrails rather than aggregate scores.

---

## 1. Class Imbalance & Flattering Headline Accuracy

In the real TWCS AmazonHelp distribution, conversational pleasantries, gratitude, and generic feedback (`General / Feedback / Other`) comprise **36.5%** (73/200) of all customer contacts. In contrast, mission-critical financial and security intents represent tiny fractions of total volume:
- `Account Access & Security`: **3.0%** (6/200)
- `Payment, Billing & Gift Cards`: **2.0%** (4/200)
- `Prime & Subscription Services`: **2.0%** (4/200)

**The Caveat:** A trivial majority-class classifier that blindly maps ambiguous messages to `General / Feedback / Other` can score ~36.5% accuracy without understanding a single support issue. Conversely, an agent could achieve 90%+ headline accuracy while failing on 100% of phishing attacks and duplicate billing disputes.  
**Operational Guardrail:** Never evaluate support AI on micro-accuracy alone. We enforce **Macro Average F1 (0.752)** and dedicated **P0 Security Recall (100.0%)** as primary non-negotiable release criteria.

---

## 2. Macro vs. Micro Behavior & Weak Class Detection

While overall accuracy reaches **79.5%**, inspecting the per-intent performance table reveals substantial variance across classes:

| Intent Class | Support | Precision | Recall | F1 Score | Diagnostic Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Account Access & Security** | 6 | 0.857 | **1.000** | **0.923** | Excellent safety capture |
| **Order & Checkout** | 16 | 1.000 | 0.812 | 0.897 | High precision |
| **Digital Services & Devices** | 21 | 0.895 | 0.809 | 0.850 | Strong device signal |
| **Seller & Product Quality** | 18 | 0.933 | 0.778 | 0.849 | High marketplace discrimination |
| **General / Feedback / Other** | 73 | 0.753 | 0.918 | 0.827 | Controlled fallback |
| **Delivery Problem & Logistics** | 39 | 0.788 | 0.667 | 0.722 | Good logistics recall |
| **Returns, Replacements & Refunds** | 10 | 0.636 | 0.700 | 0.667 | Good resolution capture |
| **Payment, Billing & Gift Cards** | 4 | 0.600 | 0.750 | 0.667 | Small sample support |
| **Delivery Tracking & Status** | 9 | 1.000 | **0.444** | **0.615** | Tracking vs late delay overlap |
| **Prime & Subscription Services** | 4 | 0.500 | **0.500** | **0.500** | Strict membership boundary |

**The Caveat:** `Delivery Tracking & Status` exhibits 1.000 precision but only 0.444 recall (F1 = 0.615). Why? When customers ask for tracking because a promised delivery date has already passed, our precedence rule intentionally re-routes them to `Delivery Problem & Logistics` to prioritize carrier investigation over passive link provision.

---

## 3. High-Difficulty Semantic Boundaries

Three boundaries present genuine semantic ambiguity that cannot be resolved solely via surface tokens:
1. **Prime Subscription vs. Prime Delivery Logistics:** Customers frequently type `"I pay for Prime delivery and my package is late!"` Matching the token `"Prime"` naively misroutes the ticket to subscription management. Our upgraded classifier requires explicit membership verbs (cancellation, auto-renew, fee) for `Prime & Subscription Services`, preserving delivery failures as `Delivery Problem & Logistics`.
2. **Delivery Tracking vs. Logistics Delay:** Inquiries like `"Where is my order? It was due yesterday"` express both a tracking request and an unfulfilled SLA promise. The agent treats broken delivery windows as logistics failures.
3. **Seller Fraud vs. Ordinary Returns:** Defective or counterfeit marketplace items frequently end with `"I want my money back."` Prioritizing the return demand over seller counterfeit evidence would obscure third-party fraud.

---

## 4. Leakage Prevention Changes Retrieval Reality

During evaluation, our retriever strictly locks **2,027 historical thread tweets** across all 200 benchmark conversations using `eval/golden_thread_exclusions.json`.

- **Naive Evaluation Risk:** If the customer's own historical thread were indexed, a TF-IDF or embedding retriever would trivially match the human agent's original reply with 90%+ cosine similarity, creating an illusion of near-perfect retrieval.
- **Enforced Reality:** With all thread tweets quarantined, the retriever must locate *analogous resolutions from completely unrelated customer interactions*.
- **The Caveat:** The measured Top-1 Hit Rate (**41.5%**) and Evidence Availability Rate (**95.0%**) reflect true out-of-sample retrieval, not memorized data leakage.

---

## 5. LLM Judge Limitations & Bias

Response quality was audited across 200 generated drafts using Google Gemini (`gemini-3.5-flash-lite`) under an explicit 5-dimensional rubric:
- **Composite Quality Score:** **3.42 / 5.0**
- **Policy Compliance:** **3.88 / 5.0** | **Escalation:** **3.98 / 5.0** | **Correctness:** **3.29 / 5.0** | **Groundedness:** **3.17 / 5.0** | **Helpfulness:** **2.78 / 5.0**

**Known Judge Biases:**
1. **Politeness & Formatting Bias:** LLM judges tend to reward long, formal responses even when a short, direct Twitter reply is operationally preferred by real customers.
2. **Score Compression:** Evaluators rarely assign extreme ratings (1 or 5) for grammatically coherent text, clustering results in the 3.0–4.0 range.
3. **Human Audit Grounding:** To anchor the LLM judge, we maintain a 50-example stratified human audit set (`eval/judge_human_audit.csv` and `eval/judge_human_review.xlsx`) where human reviewers independently verified and validated model alignment.

---

## 6. Small Test Set Scale Constraints ($N = 200$)

The golden evaluation benchmark contains exactly 200 carefully audited, authentic customer messages.
- With $N = 200$, the 95% confidence interval margin of error is approximately $\pm 5.7\%$ for binary proportions near 80%.
- Highly specific edge cases (such as SIM swapping, malicious chargebacks, or courier delivery ring theft) occur in small numbers (1 to 4 examples).
- **The Caveat:** The benchmark serves as a reliable regression harness for core intent classification and policy enforcement, but cannot replace continuous online shadow monitoring.

---

## 7. Security Metrics vs. Generic Accuracy

In customer support automation, an agent can maximize intent accuracy by smoothing over edge cases with generic auto-replies. Doing so in security incidents (such as credential phishing or account takeovers) creates catastrophic organizational risk.

- **Our Security Result:** **100.0% Recall** (6/6 golden security alerts detected) and **1.000 Precision** (zero false security panics).
- **Deterministic Override:** All security incidents immediately bypass automated response generation, assign priority `P0_CRITICAL`, set `auto_handle = false`, and enforce human specialist handoff.
- **Rule of Thumb:** We never accept an intent accuracy improvement that causes even a single security alert to be auto-handled.
