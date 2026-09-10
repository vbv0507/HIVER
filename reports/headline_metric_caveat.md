# Headline Metric Caveats & Evaluation Limitations Report (Step 4)

> [!WARNING]
> **Executive Warning: Why Headline Metrics Can Mislead**
> High-level summary metrics (e.g. 79.5% Intent Accuracy or 3.42/5.0 Response Quality) appear reassuring on executive slides, but mask critical operational nuances and deployment failure modes.

---

## 1. Class Imbalance & Flattering Accuracy

In natural customer support distributions, conversational pleasantries, gratitude, and generic feedback (`General / Feedback / Other`) comprise **36.5%** of all incoming messages. 

- A naive classifier predicting `General / Feedback / Other` for ambiguous messages naturally achieves an inflated baseline accuracy.
- **The Caveat:** High accuracy does not imply operational efficacy on low-volume, high-consequence intents like `Account Access & Security` (3.0% of data) or `Payment, Billing & Gift Cards` (2.0% of data).
- **Remedy:** Always inspect **Macro F1 (0.752)** and per-class recall rather than raw accuracy.

---

## 2. Leakage Prevention Changes Retrieval Reality

During evaluation, our system strictly locks **2,027 historical thread tweets** from retrieval via `eval/golden_thread_exclusions.json`.

- In a naive or improperly sandboxed evaluation, the agent could easily achieve 90%+ retrieval similarity by matching the historical `@AmazonHelp` reply from its own past thread.
- With leakage protection enforced, the agent is forced to generalize to *unrelated historical threads* from different customers.
- **The Caveat:** Real-world retrieval scores (79.5%) appear lower on paper, but reflect true generalization rather than memorized cheating.

---

## 3. LLM Judge Bias & Score Compression

Our LLM response quality judge scored the main agent at **3.42 / 5.0**.

- LLM judges have a well-documented **politeness and length bias**, favoring formal, longer, well-formatted responses even when a short, direct answer would suffice.
- **Score Compression:** Judges rarely assign scores of 1 or 2 to grammatically coherent drafts, compressing variance between 3.5 and 4.8.
- **Remedy:** We maintain a dedicated **50-example human audit sample** (`eval/judge_human_audit.csv`) where human reviewers calibrate and validate judge alignment independently.

---

## 4. Evaluation Set Scale Constraints ($N = 200$)

The golden evaluation benchmark contains exactly 200 high-fidelity, hand-audited real customer messages.

- While sufficient for statistical benchmarking (margin of error $\approx \pm 6.9%$ at 95% confidence interval), rare failure modes (such as edge-case SIM swapping or courier theft rings) appear infrequently.
- Benchmark metrics should be treated as a **regression guardrail**, not an exhaustive guarantee of production robustness across millions of daily interactions.

---

## 5. Escalation vs Auto-Handling Trade-Off

The main agent achieved an **Escalation Accuracy of 62.0%** with **100.0% Security Recall (5/5 final human-reviewed alerts)**.

- In automated customer support, an agent can achieve 100% security recall by simply escalating everything to humans. Doing so, however, destroys customer self-service ROI.
- Conversely, maximizing auto-handling can lead to catastrophic brand and security breaches if account takeover reports are handled by a bot.
- **The True Operational Metric:** Balancing high security recall (100%) while preserving routine informational auto-handling (39.5% human escalation rate).

---

## 6. Why Escalation Accuracy Is a Misleading Headline

The final human labels contain **79/200 (39.5%)** escalation cases and **121/200 (60.5%)** non-escalation cases. Both baselines hardcode `auto_handle=True`, so they never escalate. Their apparent accuracy is therefore simply the non-escalation base rate: **60.5%** for Rules and **60.5%** for Nearest Neighbor, versus the main agent's **62.0%**.

| Escalation metric | Main agent | Rules baseline | Nearest-neighbor baseline |
| :--- | :---: | :---: | :---: |
| Accuracy | 62.0% | 60.5% | 60.5% |
| Precision | 0.556 | 0.000 | 0.000 |
| Recall | 0.190 | 0.000 | 0.000 |
| F1 | 0.283 | 0.000 | 0.000 |

Accuracy rewards the majority “do not escalate” outcome and does not show whether a system identifies any cases that need a human. For this operational decision, escalation **F1** (with its precision and recall components) is the meaningful comparison: the baselines score zero because they identify none of the 79 required escalations, while the main agent has non-zero precision, recall, and F1 from its deterministic security, financial-dispute, human-request, and low-evidence policy rules.
