# Headline Metric Caveats & Evaluation Limitations Report (Step 4)

> [!WARNING]
> **Executive Warning: Why Headline Metrics Can Mislead**
> High-level summary metrics (e.g. 49.0% Intent Accuracy or 3.42/5.0 Response Quality) appear reassuring on executive slides, but mask critical operational nuances and deployment failure modes.

---

## 1. Class Imbalance & Flattering Accuracy

In natural customer support distributions, conversational pleasantries, gratitude, and generic feedback (`General / Feedback / Other`) comprise **36.5%** of all incoming messages. 

- A naive classifier predicting `General / Feedback / Other` for ambiguous messages naturally achieves an inflated baseline accuracy.
- **The Caveat:** High accuracy does not imply operational efficacy on low-volume, high-consequence intents like `Account Access & Security` (3.0% of data) or `Payment, Billing & Gift Cards` (2.0% of data).
- **Remedy:** Always inspect **Macro F1 (0.411)** and per-class recall rather than raw accuracy.

---

## 2. Leakage Prevention Changes Retrieval Reality

During evaluation, our system strictly locks **2,027 historical thread tweets** from retrieval via `eval/golden_thread_exclusions.json`.

- In a naive or improperly sandboxed evaluation, the agent could easily achieve 90%+ retrieval similarity by matching the historical `@AmazonHelp` reply from its own past thread.
- With leakage protection enforced, the agent is forced to generalize to *unrelated historical threads* from different customers.
- **The Caveat:** Real-world retrieval scores (49.0%) appear lower on paper, but reflect true generalization rather than memorized cheating.

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

The main agent achieved an **Escalation Accuracy of 60.0%** with **100.0% Security Recall**.

- In automated customer support, an agent can achieve 100% security recall by simply escalating everything to humans. Doing so, however, destroys customer self-service ROI.
- Conversely, maximizing auto-handling can lead to catastrophic brand and security breaches if account takeover reports are handled by a bot.
- **The True Operational Metric:** Balancing high security recall (100%) while preserving routine informational auto-handling (39.5% human escalation rate).
