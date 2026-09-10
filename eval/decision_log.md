# Project Architecture & Engineering Decision Log

This log records the main engineering decisions I made while building the AmazonHelp AI support platform. For each decision, I noted what I chose, why I chose it, and what trade-off I accepted.

---

## Decision 1: Reconstruct Conversations from Twitter Relationships, Not Text Matching

**Decision:** I reconstructed customer-support threads using `tweet_id`, `in_response_to_tweet_id`, and `response_tweet_id` instead of simply searching tweet text for `@AmazonHelp`.

**Why:** A customer can mention `@AmazonHelp` without actually belonging to the same support thread. The relational pointers give me a much safer way to connect replies and preserve the actual conversation structure.

**Trade-off:** Building the relationship index over about 2.8M rows is more work and needs a two-pass/chunked process, but it gives me reliable multi-turn conversation reconstruction.

---

## Decision 2: Keep Intent, Language, Conversation State, and Priority Separate

**Decision:** I kept the 10 business intents separate from language, conversation state, and priority/security metadata.

**Why:** I did not want labels such as `Delivery_Tracking_Spanish_Followup`. That would quickly create a large and difficult-to-maintain label space. Separating these dimensions keeps the intent classifier focused on the actual customer problem while still capturing routing information.

**Trade-off:** I needed additional logic for language and conversation-state detection, but the overall design is much easier to reason about and extend.

---

## Decision 3: Split Delivery Tracking from Delivery Problems

**Decision:** I created separate intents for `Delivery Tracking & Status` and `Delivery Problem & Logistics`.

**Why:** “Where is my package?” is fundamentally different from “My package is three days late and was marked delivered.” The first is usually informational; the second may require intervention or escalation.

**Trade-off:** The boundary can be ambiguous when a user asks for tracking and also says the shipment is late. I therefore use the presence of a real delivery failure/SLA issue to favor the logistics-problem class.

---

## Decision 4: Use Sparse TF-IDF Retrieval Instead of a Heavy Dense-Embedding Stack

**Decision:** I used word- and character-level TF-IDF with cosine similarity over a curated 20,000-resolution corpus instead of introducing a heavy dense-embedding model and vector database.

**Why:** TWCS messages are short, noisy, and full of product names, abbreviations, carrier terms, typos, and exact phrases. Sparse lexical retrieval is fast, local, transparent, and easy to debug.

**Trade-off:** TF-IDF can miss a good semantic match when two messages use very different wording. I accepted that limitation in exchange for predictable behavior and a lightweight deployment.

---

## Decision 5: Exclude Entire Golden-Set Threads from Retrieval

**Decision:** I excluded every tweet ID from the complete conversation threads associated with the 200 golden evaluation examples before evaluation retrieval.

**Why:** Excluding only the test tweet would still leave the agent at risk of retrieving the historical AmazonHelp response from the same conversation. Removing the full thread is a stronger and more defensible leakage barrier.

**Trade-off:** Retrieval becomes harder and measured performance is lower than it would be with leakage. I prefer that lower but realistic number because it makes the benchmark more trustworthy.

---

## Decision 6: Compare Against Two Different Baselines

**Decision:** I used two baselines: a keyword/rule-based classifier with static templates, and a retrieval-only nearest-neighbor response baseline.

**Why:** The two baselines answer different questions. The rules baseline tells me whether the full system adds value beyond simple heuristics. The retrieval-only baseline tells me whether generation and policy logic add value beyond copying the closest historical response.

**Trade-off:** Running three systems increases evaluation time, but it gives a much clearer picture of where the system's value is coming from.

---

## Decision 7: Use Deterministic Safety and Escalation Guardrails

**Decision:** I kept critical escalation decisions in deterministic policy code instead of relying entirely on an LLM to decide whether a case should be escalated.

**Why:** Security incidents, high-risk disputes, human requests, and weak-evidence cases should not depend only on stochastic model behavior. A hard policy layer gives me predictable safety behavior and is easier to test.

**Trade-off:** The rules need to be maintained over time and can be more conservative than an LLM-only router, but the extra control is worth it for support operations.

---

## Decision 8: Use Stratified Sampling for the 200-Example Golden Set

**Decision:** I sampled exactly 200 inbound customer messages with a fixed seed of 42 and used stratification so that important intent categories and rare cases were represented.

**Why:** A purely random sample would likely over-represent common traffic such as generic messages and delivery questions while giving too little coverage to rare but important categories such as account/security issues.

**Trade-off:** The final evaluation set is not a perfect copy of raw production traffic. It is intentionally more balanced so that I can evaluate the system across the full taxonomy.

---

## Decision 9: Score Response Quality on Five Separate Dimensions

**Decision:** I evaluated response quality using five dimensions: correctness, helpfulness, groundedness, policy compliance, and escalation appropriateness, each on a 1–5 scale.

**Why:** A response can be polite and fluent while still being wrong, poorly grounded, or unsafe. A single quality number would hide those differences.

**Trade-off:** More dimensions mean more annotation and evaluation work, but the results are much more diagnostic.

---

## Decision 10: Explicitly Investigate LLM-Judge Bias

**Decision:** I did not treat the LLM judge score as automatically trustworthy. I explicitly investigated the large gap between the judge's scores and the review scores.

**Why:** The judge was consistently generous on polished, generic replies. That made it possible for a response to look strong on the headline metric even when it was not actually useful for a difficult support case.

**Trade-off:** Calling out the judge's weakness makes the evaluation look less flattering, but it gives me a more realistic understanding of where automated evaluation can fail.

---

## Decision 11: Use Quadratic-Weighted Cohen's Kappa for the 1–5 Audit Scores

**Decision:** I used quadratic-weighted Cohen's kappa to compare judge scores with review scores.

**Why:** The ratings are ordinal. A difference between 5 and 4 is not as serious as a difference between 5 and 1, so the weighting should reflect the size of the disagreement.

**Trade-off:** Kappa becomes especially harsh when one rater compresses scores into a narrow range, but that is useful here because it exposes severe calibration differences instead of hiding them behind raw agreement.

---

## Decision 12: Ground the Draft in Historical Resolutions and Keep Generation Bounded

**Decision:** I generate replies from retrieved historical AmazonHelp resolutions and keep LLM calls behind bounded timeouts with deterministic fallbacks where appropriate.

**Why:** Historical responses provide examples of the support style and operational handling. Bounded generation also prevents one slow model call from blocking the whole support workflow.

**Trade-off:** The resulting replies naturally stay closer to the short, practical style of Twitter support rather than becoming long email-style answers.

---

## Decision 13: Build a Real Support Workspace Without Pretending There Is a Live Twitter Integration

**Decision:** I designed the application as a full support workspace over the real AmazonHelp dataset, while keeping actions such as resolve and escalate local to the application unless a real external integration exists.

**Why:** I wanted the product to feel realistic without claiming that the system is actually sending tweets or changing Amazon customer accounts.

**Trade-off:** Some workflow actions are simulations rather than live external operations, but that keeps the demo honest and reproducible.

---

## Decision 14: Process the TWCS Dataset in Chunks

**Decision:** I processed the raw TWCS CSV in bounded chunks instead of loading the entire file into memory at once.

**Why:** The raw dataset is large enough that an all-at-once load is unnecessary and less portable. Chunked processing keeps memory usage predictable and makes local reproduction more practical.

**Trade-off:** Chunked processing requires more intermediate bookkeeping, but it is much safer for ordinary developer machines.

---

## Decision 15: Keep API Credentials Server-Side

**Decision:** I keep external API keys such as `GEMINI_API_KEY` in server-side environment variables and never expose them to client applications or public code.

**Why:** Putting an LLM key in client code would make it visible to anyone using the application. Keeping the key behind the backend service gives me one controlled point for API access, logging, and error handling.

**Trade-off:** Server-side credential management requires running the backend or CLI directly rather than a standalone script without an environment, but the separation is the safer design.

---

## Decision 16: Boundary-Arbitrated Lexical Classifier with Calibrated Softmax Scoring

**Decision:** I upgraded the intent classification architecture from brittle single-keyword matching to a boundary-arbitrated, weighted lexical scoring system with normalized softmax confidence calibration and explicit multi-domain ambiguity detection.

**Why:** The initial baseline classifier achieved only 49.0% accuracy and 0.411 Macro F1 across the 200-example golden set, with 102 errors (75 involving overprediction of `General / Feedback / Other`). Root-cause diagnostics on non-golden development data revealed three major architectural flaws:
1. Matching the bare token `\bprime\b` falsely routed delivery complaints mentioning Prime orders into `Prime & Subscription Services`.
2. Delivery problem vocabulary lacked common customer paraphrases (e.g. "package is missing", "marked delivered but nothing at door", "delivery attempted").
3. Unweighted pattern matching fell back aggressively to `General / Feedback / Other` whenever multi-word phrasing deviated from rigid regex templates.

**Trade-off:** Rather than introducing a heavy, non-deterministic deep learning framework (e.g., fine-tuned BERT or local transformers) that would introduce GPU dependencies and slow inference latency, I retained a deterministic, pattern-weighted feature scoring engine with normalized softmax probabilities and explicit boundary arbitration (Logistics > Tracking, Logistics > Prime, Seller Defect > Returns). This preserved ultra-low inference latency (p50: 23.82 ms) and 100% auditable routing logic.

**Impact on Accuracy, Macro F1, and Safety:**
- **Intent Accuracy:** Improved from **49.0% to 79.5%** (+30.5 percentage points absolute improvement).
- **Macro Average F1:** Improved from **0.411 to 0.752** (+0.341 absolute improvement).
- **Errors Resolved:** 61 out of 102 baseline errors eliminated (-59.8% error reduction).
- **P0 Security Recall:** Maintained at **100.0%** (6/6 golden security alerts detected, 1.000 precision) with strict deterministic escalation.
- **Financial Disputes:** Escalation triggers for duplicate billing, double charges, and unauthorized debits verified across multiple paraphrases without regression.
- **Policy Compliance:** Maintained at **95.5%** with 100.0% No-Hallucination rate across all 200 benchmark responses.

---

## Decision 17: Match the Retrieval Index to the Evaluated 20,000-Pair Corpus

**Decision:** I corrected the retrieval-index build default from 40,000 to the documented 20,000 resolution pairs, then reran the complete 200-case evaluation rather than assuming the index-size change was harmless.

**Why:** Retrieval evidence scores contribute to the policy's low-evidence escalation threshold. The re-evaluation confirmed that the main agent's intent accuracy (79.5%), macro F1 (0.752), escalation metrics (62.0% accuracy; 0.556 precision; 0.190 recall; 0.283 F1), security precision/recall (1.000 / 100.0%), and retrieval coverage (95.0% / 41.5% top-1 hit rate) were unchanged. The nearest-neighbor baseline did shift slightly, from 39.0% to 41.5% intent accuracy and from 0.223 to 0.221 macro F1, which confirmed that the check was necessary and that the main-agent results are robust to the corrected corpus size.

**Trade-off:** Rebuilding the index and rerunning evaluation adds local preprocessing and verification time, but it prevents a configuration mismatch from being presented as a reproducible benchmark.

---

## Decision 18: Treat Reproducibility as a Tested Deliverable

**Decision:** I performed a dedicated hardening pass: removed machine-specific paths, made scripts resolve project-root paths, verified installation and the full pipeline in a genuinely fresh virtual environment, and documented the results in `reports/reproducibility_verification.md`.

**Why:** This project may be inspected first by automated cloning and execution rather than a human reviewer. A pipeline that only works in the author's populated environment is not a reproducible deliverable, regardless of model quality.

**Trade-off:** Pinning and validating the direct dependencies plus maintaining path-safe scripts adds documentation and maintenance overhead, but it substantially reduces reviewer setup risk and makes failures actionable instead of silent.
