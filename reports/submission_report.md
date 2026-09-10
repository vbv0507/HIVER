# AmazonHelp AI Support Agent — Submission Report

## Problem and scope

This project turns real AmazonHelp conversations from the TWCS dataset into a support-agent pipeline. Given an incoming customer message, it classifies one of 10 data-derived intents, retrieves historically similar AmazonHelp resolutions, decides whether to auto-handle or escalate with an explicit reason, and drafts a grounded reply.

The verified source dataset contains 2.81M TWCS rows. The final AmazonHelp corpus contains 373,438 tweets and 82,556 reconstructed threads. The retrieval index uses 20,000 resolution pairs. I intentionally did not build live Amazon/Twitter actions, customer-account mutations, or a general-purpose chatbot; the application is a reproducible support-decision demo over the supplied historical data.

## Evaluation design

The benchmark is 200 real messages in `eval/golden_eval_set_final.csv`, with final human labels for intent, language, conversation state, escalation, security, and priority. Full golden-set threads (2,027 tweets) are excluded from retrieval to prevent leakage. A separate 50-case human audit evaluates the LLM response-quality judge.

The system is compared with two deliberately simpler baselines: a keyword/regex rule-template responder and a top-1 nearest-neighbor retrieval responder.

## Final benchmark results

| Metric | Main agent | Rule-template baseline | Nearest-neighbor baseline |
| :--- | :---: | :---: | :---: |
| Intent accuracy | 79.5% (159/200) | 45.0% | 41.5% |
| Intent macro F1 | 0.752 | 0.304 | 0.221 |
| Escalation accuracy | 62.0% (124/200) | 60.5% | 60.5% |
| Escalation precision | 0.556 | 0.000 | 0.000 |
| Escalation recall | 0.190 | 0.000 | 0.000 |
| Escalation F1 | 0.283 | 0.000 | 0.000 |
| P0 security recall | 100.0% (5/5) | 0.0% | 0.0% |

The full metrics, error examples, and generated artifacts are in `reports/evaluation_results.md`, `reports/evaluation_error_analysis.md`, and `reports/headline_metric_caveat.md`.

## Failure analysis

The primary failure modes are ambiguous tracking-versus-logistics language, Prime mentioned in delivery complaints, seller-quality versus refund cases, low-evidence terse messages, multilingual lexical mismatch, and context-poor follow-up/DM messages. The error analysis includes real examples and hypotheses for each category. The policy is intentionally conservative when evidence is weak; this improves safety but contributes to the modest 19.0% escalation recall.

## The misleading headline number

Escalation accuracy is not a useful standalone headline. The human labels have 121 non-escalations and 79 escalations. Both baselines always auto-handle, so they obtain 60.5% accuracy by predicting only the majority class while identifying none of the required escalations. The main agent's 62.0% accuracy is only slightly higher, but its non-zero escalation precision, recall, and F1 demonstrate actual policy behavior. Escalation F1 is the decision metric to use.

## Human audit caveat

The 50/50 judge-human audit is complete. It finds 19.6% exact agreement, 58.0% within-one agreement, and macro quadratic kappa of 0.233. This supports treating LLM-as-judge output as a diagnostic signal rather than a substitute for human evaluation. The audit's policy rating has no score variance (all human scores are 5), which limits interpretability for that single dimension.

## If I had one more week

1. Add multilingual semantic retrieval and evaluate it separately from English lexical retrieval.
2. Use thread context for follow-ups instead of single-message classification.
3. Tune escalation recall with more independently reviewed high-risk cases, while tracking the human-review workload created by false positives.
4. Expand the human audit with multiple reviewers and adjudication, especially for policy and escalation ratings.
5. Add regression fixtures for the highest-impact real errors and a lightweight dashboard export for review sessions.
