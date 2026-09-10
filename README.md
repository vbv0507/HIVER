# HIVER — AmazonHelp AI Support Agent

A reproducible AI customer support agent for **AmazonHelp**, developed from the Kaggle **Customer Support on Twitter (TWCS)** dataset (`twcs.csv`).

The system classifies incoming customer messages into a locked 10-intent taxonomy, retrieves verified historical resolutions with strict golden-set leakage exclusion, evaluates deterministic safety and financial escalation rules, and generates grounded customer responses.

---

## 1. What this project does

Given a customer support message directed at AmazonHelp from the TWCS dataset, the system:
- **Classifies the issue** into exactly one of 10 locked customer intents with calibrated confidence.
- **Detects metadata**: language (EN, ES, JA, DE, PT, FR, IT), dialogue state (`new_issue`, `dm_handoff`, etc.), and security alert status.
- **Retrieves relevant evidence**: searches 20,000 indexed historical AmazonHelp resolution pairs using TF-IDF and cosine similarity, constrained by predicted intent.
- **Decides auto-handle vs. escalate**: runs a deterministic escalation policy that flags security risks (account takeover, phishing), financial disputes (duplicate charges), ambiguous queries, and requests requiring human intervention.
- **Explains the escalation decision**: provides an explicit textual reason for why a case was escalated or auto-handled.
- **Drafts a grounded response**: synthesizes a customer-facing reply adhering to AmazonHelp public channel policies without requesting sensitive credentials.

The project is built on the real TWCS dataset (2.81M tweets) without synthetic fallbacks.

---

## 2. Why AmazonHelp

AmazonHelp was selected as the focal brand for this project because:
- **Highest support volume in TWCS**: 169,840 brand response tweets and 373,438 total conversation tweets across 82,556 multi-turn threads.
- **Diverse operational scope**: covers logistics, returns, subscriptions, billing disputes, hardware/Kindle troubleshooting, marketplace seller disputes, and security incidents.
- **Multi-turn dialogue trees**: contains complete customer-agent interaction threads, making it possible to reconstruct realistic resolution pairs and evaluate conversation state transitions.

---

## 3. Architecture

```
customer message
    ↓
intent / language / state
    ↓
retrieval
    ↓
escalation policy
    ↓
grounded response generation
    ↓
structured output
```

### Module Overview

- `src/classifier/intent_classifier.py`: 10-class intent classifier with calibrated softmax scoring, regex safety patterns, language detection, dialogue state tracking, and security alert detection.
- `src/retrieval/retriever.py`: TF-IDF vector space retriever searching 20,000 historical `@AmazonHelp` resolution pairs with intent filtering and strict golden-set exclusion.
- `src/policy/escalation_policy.py`: Deterministic safety policy evaluating P0 security incidents, financial disputes, human intervention requests, low confidence, and insufficient evidence.
- `src/generation/generator.py`: Response synthesis engine generating transparent customer replies and safe DM handoff drafts.
- `src/agent/amazon_agent.py`: Unified orchestrator integrating classification, retrieval, policy, and generation into a structured output contract.
- `src/api/`: FastAPI REST application (`main.py`, `models.py`, `services.py`) providing HTTP endpoints for ticket triage, message analysis, and benchmark telemetry.

---

## 4. Intent Taxonomy

The system enforces a locked 10-intent taxonomy:

1. **Delivery Tracking & Status**: Where is my package, tracking updates, carrier status inquiries.
2. **Delivery Problem & Logistics**: Late packages, missing/stolen deliveries, damaged shipments, carrier failures.
3. **Returns, Replacements & Refunds**: Return label generation, refund status, item exchanges, drop-off questions.
4. **Payment, Billing & Gift Cards**: Duplicate charges, unauthorized transactions, gift card balances, payment failures.
5. **Prime & Subscription Services**: Prime benefits, membership cancellation, fee inquiries, auto-renewal settings.
6. **Order & Checkout**: Pre-dispatch order cancellation, cart errors, address changes, promo code failures.
7. **Account Access & Security**: Password resets, login lockouts, account takeover, phishing, credential compromise.
8. **Digital Services & Devices**: Kindle, Fire TV, Echo/Alexa, digital video/music streaming, app crashes.
9. **Seller & Product Quality**: Third-party marketplace disputes, counterfeit items, defective goods, unresponsive sellers.
10. **General / Feedback / Other**: Conversational pleasantries, general feedback, unspecific venting, conversational handshakes.

### Orthogonal Metadata
Language (`en`, `es`, `ja`, `de`, `pt`, `fr`, `it`, `other`), conversation state (`new_issue`, `dm_handoff`, `follow_up`, `active_troubleshooting`, `resolved_or_acknowledgment`), and priority (`P0_CRITICAL` vs. `standard`) are tracked independently of the intent label to prevent combinatorial explosion in the label space.

---

## 5. Data Pipeline

The data pipeline extracts, structures, and validates the AmazonHelp dataset from raw TWCS data:

```bash
# 1. Verify the raw TWCS dataset (expects data/raw/twcs.csv)
python scripts/verify_twcs.py

# 2. Extract AmazonHelp tweets, reconstruct conversation trees, and build resolution pairs
python scripts/extract_amazonhelp.py

# 3. Validate extracted conversation trees, text diversity, and schema integrity
python scripts/validate_amazonhelp.py
```

- Raw dataset location: `data/raw/twcs.csv` (516 MB, ~2.81M rows; not committed to Git).
- Processed artifacts:
  - `data/processed/AmazonHelp_tweets.csv`: 373,438 extracted tweets.
  - `data/processed/AmazonHelp_conversations.csv`: 373,438 turn rows with graph links.
  - `data/processed/AmazonHelp_threads.jsonl`: 82,556 reconstructed dialogue trees.
  - `data/processed/resolution_pairs.jsonl`: Filtered customer-response pairs for retrieval.

---

## 6. Retrieval

- **Resolution Corpus**: 20,000 historical AmazonHelp resolution pairs indexed into a sparse TF-IDF n-gram vectorizer.
- **Index Location**: `data/processed/retrieval_index.joblib` (generated via `scripts/build_retrieval_index.py`).
- **Retrieval Mechanism**: Given a customer query, the retriever filters the corpus by predicted intent and performs cosine similarity search to return the top-$k$ historical resolutions.
- **Golden-Set Leakage Prevention**: `eval/golden_thread_exclusions.json` locks 200 golden evaluation conversation IDs and 2,027 total thread tweets.

### Why Entire Threads Are Excluded
During evaluation, the retriever excludes every tweet belonging to any conversation in the golden evaluation set. If only the specific test tweet were removed, sibling tweets or the agent's historical answer from the same support thread would remain in the retrieval pool. The retriever could then retrieve the exact historical resolution from the same thread, artificially inflating retrieval and correctness scores. Excluding entire conversation threads guarantees honest out-of-sample evaluation.

---

## 7. Agent Usage

Run inference on a single customer message:

```bash
python scripts/run_agent.py --text "Where is my package? The tracking hasn't updated in two days."
```

### Representative Output

```json
{
  "intent": "Delivery Tracking & Status",
  "confidence": 0.98,
  "language": "en",
  "conversation_state": "new_issue",
  "is_security_alert": false,
  "priority": "standard",
  "auto_handle": true,
  "escalation_reason": "None. Routine informational request for 'Delivery Tracking & Status' safely addressed via verified historical guidance.",
  "draft_reply": "You can check the real-time location and estimated delivery date of your package at any time by going to 'Your Orders' and selecting 'Track Package' next to the item. If the carrier tracking shows no movement for more than 48 hours, please share your 17-digit Order ID so we can look into it for you. ^AmazonHelp",
  "retrieved_evidence": [
    {
      "conversation_id": "210328",
      "customer_message": "WHERE IS MY PACKAGE @AmazonHelp",
      "historical_response": "@165781 Hey, we'd like to help out! Most deliveries are made until 8 PM. What does the tracking say here: https://t.co/Y5jpI9gRhE? ^WJ",
      "score": 0.3436
    }
  ]
}
```

### Output Field Specification
- `intent`: Classified intent from the 10 locked categories.
- `confidence`: Softmax probability score [0.0, 1.0].
- `language`: Detected ISO 639-1 language code.
- `conversation_state`: Dialogue stage (`new_issue`, `active_troubleshooting`, `dm_handoff`, etc.).
- `is_security_alert`: Boolean indicating account takeover, phishing, or credential harvesting risk.
- `priority`: Priority classification (`P0_CRITICAL` or `standard`).
- `auto_handle`: Boolean indicating whether the agent can resolve the query automatically.
- `escalation_reason`: Textual rationale for the escalation or auto-handling decision.
- `draft_reply`: Grounded customer-facing reply text.
- `retrieved_evidence`: Top matching historical resolution records with relevance scores.

---

## 8. Escalation

The agent employs a deterministic safety layer in `src/policy/escalation_policy.py`:

- **P0 Security Escalation**: Triggers when patterns indicate account takeover, phishing messages, credential harvesting, or unauthorized contact changes. Sets `is_security_alert=True`, `priority="P0_CRITICAL"`, and `auto_handle=False`. Draft responses direct the customer to security specialists via private channels and explicitly warn against sharing passwords publicly.
- **Financial Dispute Escalation**: Triggers on duplicate charges, double debits, or unauthorized billing. Sets `auto_handle=False` and routes to a billing specialist for manual account review. The agent never claims a refund was processed or that account records were inspected.
- **Marketplace Dispute Escalation**: Triggers on counterfeit claims or unresponsive third-party sellers, routing to A-to-z Guarantee specialists (`auto_handle=False`).
- **Insufficient Evidence Escalation**: Triggers when top retrieval relevance is below threshold (`< 0.12`) or when no matching evidence exists (`auto_handle=False`).
- **Low Confidence / Ambiguity Escalation**: Triggers when competing intent signals result in classifier confidence `< 0.40`.
- **Explicit Human Requests**: Triggers when the customer asks to speak with a person, representative, or manager.

The system never claims to perform live account mutations (e.g., executing actual refunds or account bans).

---

## 9. Evaluation

The evaluation harness (`scripts/run_evaluation.py`) benchmarks the agent against two baselines across a 200-example golden set (`eval/golden_eval_set_final.csv`):

- **Baseline 1 (Rules + Templates)**: Keyword regex classifier paired with static canned responses (`src/baselines/baseline_rules.py`).
- **Baseline 2 (Nearest-Neighbor Retrieval)**: Direct top-1 resolution pair reuse (`src/baselines/baseline_retrieval_only.py`).
- **Main Agent**: Hybrid intent classifier, TF-IDF retrieval, deterministic policy, and grounded generator.

### Benchmark Results (from `reports/evaluation_results.md`)

| Evaluation Dimension | Metric | Main Agent | Baseline 1 (Rules) | Baseline 2 (Nearest-Neighbor) |
| :--- | :--- | :---: | :---: | :---: |
| **Intent Classification** | Accuracy | **79.5%** | 45.0% | 39.0% |
| | Macro F1 | **0.752** | 0.304 | 0.223 |
| **Language & State** | Language Accuracy | **94.5%** | N/A | N/A |
| | State Macro F1 | **0.338** | N/A | N/A |
| **Escalation Decision** | Accuracy | **62.0%** | 60.5% | 60.5% |
| | Precision | **0.556** | 0.000 | 0.000 |
| | Recall | **0.190** | 0.000 | 0.000 |
| | F1 Score | **0.283** | 0.000 | 0.000 |
| **Security Risk (P0)** | Precision | **1.000** | 0.000 | 0.000 |
| | Recall | **100.0%** | 0.0% | 0.0% |
| **Response Quality (Judge)**| Overall Score (1–5) | **3.42** | 3.10 | 2.65 |
| | Correctness | **3.29** | 3.20 | 2.50 |
| | Helpfulness | **2.78** | 3.40 | 2.80 |
| | Groundedness | **3.17** | 2.50 | 3.90 |
| | Policy Compliance | **3.88** | 3.80 | 2.70 |
| | Escalation Appropriateness | **3.98** | 2.80 | 2.10 |
| **Deterministic Checks** | Existence Rate | **100.0%** | 100.0% | 100.0% |
| | No Hallucination Rate | **100.0%** | 100.0% | 78.0% |
| | Policy Compliance Rate | **95.5%** | 62.0% | 45.0% |
| **Retrieval** | Evidence Availability Rate| **95.0%** | N/A | 100.0% |
| | Top-1 Hit Rate | **41.5%** | N/A | 34.0% |
| **Latency** | Median (p50) | **24.46 ms** | 0.08 ms | 22.41 ms |
| | 95th Percentile (p95) | **31.76 ms** | 0.16 ms | 29.64 ms |

### LLM-as-a-Judge Rubric
The LLM judge (`scripts/llm_judge.py`) evaluates response quality using Google Gemini (`gemini-3.5-flash-lite`) across 5 dimensions on a 1–5 scale:
1. **Correctness**: Accuracy of advice according to AmazonHelp domain policies.
2. **Helpfulness**: Clear and actionable next steps.
3. **Groundedness**: Faithfulness to retrieved historical evidence without inventing policies.
4. **Policy Compliance**: Safe routing, privacy protection, and refusal to collect sensitive credentials publicly.
5. **Escalation Appropriateness**: Accurate calibration between self-service guidance and specialist transfer.

### Judge vs. Human Audit Results (50 Cases)
A stratified subset of 50 golden cases was audited against human reviews (`eval/judge_human_audit.csv`, validated via `scripts/validate_judge_human_agreement.py`):
- Overall Exact Agreement: **19.6%** (49 / 250 ratings)
- Overall Within-1 Agreement: **58.0%** (145 / 250 ratings)
- Macro Quadratic Kappa: **0.233**
- Score distribution comparison:
  - Correctness: Judge mean 3.24 vs. Human mean 1.98
  - Helpfulness: Judge mean 2.80 vs. Human mean 1.80
  - Groundedness: Judge mean 3.08 vs. Human mean 2.10
  - Policy: Judge mean 3.90 vs. Human mean 5.00
  - Escalation: Judge mean 3.84 vs. Human mean 2.46

*Analysis*: The LLM judge scores higher on average than human reviewers for correctness and escalation, exhibiting leniency on ambiguous turns, but aligns closely on policy compliance where rules are explicit.

---

## 10. Known Limitations

- **Historical Twitter Domain**: The dataset consists of public tweets from 2017–2018 with anonymized customer handles (`@115770`). It lacks private account context, order databases, or real-time CRM integrations.
- **Draft-Only Generation**: The system produces draft replies and transfer recommendations. It does not interface with live Twitter/X APIs or Amazon internal systems.
- **Retrieval Coverage Dependency**: Resolution retrieval is bounded by the 20,000 historical pairs in the index. Unprecedented queries or rare issues outside historical distribution can yield low evidence scores.
- **Golden Evaluation Set Size**: The 200-example golden set provides focused benchmarking, but low-support categories (e.g., Prime has 4 cases, Payment has 4 cases) have wider error bounds.
- **Judge-Human Divergence**: The LLM judge is more lenient than human auditors on borderline responses, confirming that automated LLM evaluation requires human calibration on high-risk support categories.
- **API Rate Limits**: The live LLM judge is subject to provider rate limits (HTTP 429), requiring sequential execution with delay and exponential backoff during large evaluations.

---

## 11. Reproduction

Step-by-step reproduction from scratch:

```bash
# 1. Place raw TWCS dataset at data/raw/twcs.csv
# (Obtain twcs.csv from Kaggle: "Customer Support on Twitter")

# 2. Install dependencies
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt

# 3. Verify raw dataset integrity
python scripts/verify_twcs.py

# 4. Extract AmazonHelp corpus and validate
python scripts/extract_amazonhelp.py
python scripts/validate_amazonhelp.py

# 5. Build retrieval index
python scripts/build_retrieval_index.py

# 6. Run agent CLI test
python scripts/run_agent.py --text "Where is my package? The tracking hasn't updated in two days."

# 7. Run consolidated manual smoke tests (30 cases across 18 categories)
python scripts/run_manual_smoke_tests.py

# 8. Run full automated test suite (60 unit tests)
python -m unittest discover tests

# 9. (Optional) Run 200-example evaluation harness with LLM judge
# Requires GEMINI_API_KEY in .env
python scripts/run_evaluation.py

# 10. Start the API and open the live dashboard
python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
# Browse to http://127.0.0.1:8000/dashboard
```

---

## 12. Project Structure

```
HIVER/
├── .env.example                        # Template for optional API credentials
├── .gitignore                          # Exclusions (protects raw data, cache, .env)
├── requirements.txt                    # Validated package dependencies
├── README.md                           # Master project documentation
│
├── src/                                # Core agent modules
│   ├── agent/
│   │   └── amazon_agent.py             # End-to-end agent orchestrator
│   ├── api/                            # FastAPI backend service
│   │   ├── main.py                     # API router & endpoints
│   │   ├── models.py                   # Pydantic request/response schemas
│   │   └── services.py                 # TicketService, AgentService, EvaluationService
│   ├── baselines/
│   │   ├── baseline_rules.py           # Baseline 1: Rule & template responder
│   │   └── baseline_retrieval_only.py  # Baseline 2: Nearest-neighbor retrieval
│   ├── classifier/
│   │   └── intent_classifier.py        # Locked 10-intent classifier & security guard
│   ├── evaluation/
│   │   └── metrics.py                  # Evaluation metrics suite
│   ├── generation/
│   │   └── generator.py                # Grounded multilingual response generator
│   ├── policy/
│   │   └── escalation_policy.py        # Deterministic safety & escalation policy
│   └── retrieval/
│       ├── corpus_builder.py           # Resolution pair corpus builder
│       └── retriever.py                # Semantic TF-IDF retriever with leakage filter
│
├── scripts/                            # Operational & benchmark CLI scripts
│   ├── build_retrieval_index.py        # Precompute TF-IDF vectorizer matrix
│   ├── extract_amazonhelp.py           # Extract AmazonHelp conversation threads from TWCS
│   ├── llm_judge.py                    # Real LLM judge using Google GenAI SDK
│   ├── review_human_audit.py           # Interactive CLI tool for human audit review
│   ├── run_agent.py                    # Canonical single-query / interactive agent runner
│   ├── run_evaluation.py               # 200-case comparative evaluation harness
│   ├── run_manual_smoke_tests.py       # Consolidated smoke test suite (30 cases)
│   ├── sync_human_audit_to_csv.py      # Synchronize reviewed Excel audit to CSV
│   ├── validate_amazonhelp.py          # Validation checks for extracted corpus
│   ├── validate_golden_set.py          # Validation checks for golden evaluation set
│   ├── validate_judge_human_agreement.py # Compute Cohen's Kappa & judge agreement
│   ├── validate_judge_human_review.py  # Validate human audit workbook integrity
│   └── verify_twcs.py                  # Raw TWCS dataset validator
│
├── tests/                              # Automated test suite (60 tests)
│   ├── test_agent.py                   # Intent routing, safety, paraphrase regressions
│   ├── test_api.py                     # FastAPI routes, schemas, and error states
│   ├── test_evaluation.py              # Metrics, baselines, leakage exclusion, judge
│   ├── test_generalization.py          # Multi-paraphrase generalization & safety tests
│   ├── test_human_review_workflow.py   # Human review actions, validation, agreement
│   └── test_pipeline.py                # Text normalization & thread reconstruction
│
├── eval/                               # Evaluation & audit assets
│   ├── decision_log.md                 # Architecture & design trade-off log
│   ├── evaluation_config.json          # Benchmark configuration & judge settings
│   ├── golden_eval_set_final.csv       # Curated 200-example golden evaluation set
│   ├── golden_thread_exclusions.json   # 200 conversations / 2,027 tweets excluded
│   └── judge_human_audit.csv           # 50 audit cases with synchronized human ratings
│
├── data/
│   ├── raw/                            # Place raw twcs.csv here
│   └── processed/                      # Generated processed artifacts
│
└── reports/                            # Detailed analytical reports
    ├── AmazonHelp_data_profile.md      # Data profile of AmazonHelp support interactions
    ├── AmazonHelp_final_taxonomy.md    # Authoritative 10-intent taxonomy specification
    ├── evaluation_results.md           # Benchmark evaluation report with baseline comparison
    ├── evaluation_error_analysis.md    # Categorized failure modes & boundary audits
    └── headline_metric_caveat.md       # Caveat analysis on support distribution skew
```

---

## 13. Configuration / API Keys

The core agent, classifier, retriever, policy engine, test suite, API backend, and smoke tests run **100% locally** with zero external API dependencies.

An API key is only required if running the live LLM judge in `scripts/run_evaluation.py`:

```bash
# Copy template
cp .env.example .env

# Edit .env and supply your Gemini API key:
GEMINI_API_KEY=your_gemini_api_key_here
```

### Security Rules
- `.env` is listed in `.gitignore` and is never committed to Git.
- The LLM judge fails clearly with an informative error if `GEMINI_API_KEY` is not set—it does not silently substitute fake judge scores.

---

## 14. Testing

### Run Full Test Suite (60 Unit Tests)
```bash
python -m unittest discover tests
```
Covers agent routing, paraphrase regressions, leakage prevention, API endpoints, evaluation metrics, and human audit review flows.

### Run Consolidated Smoke Tests (30 Cases Across 18 Categories)
```bash
python scripts/run_manual_smoke_tests.py
```
Validates end-to-end agent behavior across:
1. Delivery tracking
2. Late/delayed delivery
3. Prime order late (logistics boundary precedence)
4. Return/refund
5. Duplicate Prime charges (3 paraphrases)
6. Prime cancellation
7. Login/password assistance
8. Account takeover (3 paraphrases)
9. Fake Amazon / phishing SMS (3 paraphrases)
10. OTP / credential phishing (3 paraphrases)
11. Kindle / digital device troubleshooting
12. Counterfeit / marketplace seller disputes
13. Order cancellation
14. Checkout / promo code errors
15. Ambiguous multi-intent requests
16. Multilingual requests (Spanish)
17. Low-evidence / out-of-domain requests
18. Prompt-injection-style requests

### Validation Scripts
```bash
python scripts/verify_twcs.py
python scripts/validate_amazonhelp.py
python scripts/validate_golden_set.py
python scripts/validate_judge_human_review.py
python scripts/validate_judge_human_agreement.py
```

---

## 15. Evaluation Reproducibility

- **Random Seed**: `EVALUATION_SEED=42` across sampling, dataset splitting, and baseline execution.
- **Judge Model**: Google Gemini `gemini-3.5-flash-lite` via the `google-genai` SDK.
- **Judge Parameters**: Single worker (`judge_max_workers=1`), rate-limiting request delay (`judge_delay_seconds=1.5`), exponential backoff with jitter (`judge_max_retries=6`).
- **Retrieval Settings**: Sparse TF-IDF n-gram matrix, top-$k=3$ resolution pairs, intent-filtered search space, strict exclusion of all 2,027 golden thread tweets.
- **Configuration File**: `eval/evaluation_config.json`.
- **Output File**: `data/processed/evaluation_results.jsonl`.

---

## 16. Assignment Deliverables

- **Runnable Support Agent**: Complete Python implementation with CLI (`scripts/run_agent.py`), API service (`src/api/`), and modular components (`src/`).
- **Golden Evaluation Set**: `eval/golden_eval_set_final.csv` (200 real, verified AmazonHelp customer messages).
- **Evaluation Harness**: `scripts/run_evaluation.py` with leakage filtering, automated metrics, and live Gemini judge.
- **Two Baselines**: Rule-based template baseline (`src/baselines/baseline_rules.py`) and nearest-neighbor retrieval baseline (`src/baselines/baseline_retrieval_only.py`).
- **Analytical Reports**: Submission-ready overview (`reports/submission_report.md`), intent taxonomy specification (`reports/AmazonHelp_final_taxonomy.md`), comparative benchmark evaluation (`reports/evaluation_results.md`), error analysis (`reports/evaluation_error_analysis.md`), and metric caveat analysis (`reports/headline_metric_caveat.md`).
- **Engineering Decision Log**: `eval/decision_log.md` detailing architectural choices and trade-offs.
