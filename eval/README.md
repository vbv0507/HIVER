# Golden Evaluation Benchmark (Step 2)

> [!CAUTION]
> **INTEGRITY NOTICE (STATUS: PENDING HUMAN REVIEW)**:
> Columns named `my_final_*` and `human_*` currently contain **provisional AI-assisted suggestions only**. The user will personally perform the human review and verification before final submission. All metrics reported against this dataset reflect these provisional baselines and are subject to final manual review.

---

## 1. Benchmark Overview

| Specification | Value |
| :--- | :--- |
| **Source Dataset** | `data/processed/AmazonHelp_tweets.csv` (203,598 real customer tweets) |
| **Benchmark Size** | Exactly **200 customer messages** |
| **Sampling Random Seed** | `42` (100% deterministic & reproducible) |
| **Sampling Strategy** | Stratified across 10 intents, languages, conversation states, and security alerts |
| **Taxonomy Version** | Locked 10-Intent System (`reports/AmazonHelp_final_taxonomy.md`) |
| **AI Pre-Label Model** | `gemini-2.5-flash` / audited heuristic rules (pre-label suggestions only) |
| **Human Review Authority** | Human review is sovereign (`my_final_*` columns) |
| **Leakage Exclusion Total**| **2,027 historical thread tweets** excluded from retrieval |

---

## 2. File Manifest

- **`eval/golden_eval_set_final.csv`**: The finalized canonical 200-example golden benchmark with human gold labels and review actions.
- **`eval/golden_review_final_report.md`**: Comprehensive final audit report covering distributions, agreement statistics, and provenance.
- **`eval/golden_eval_set.csv`**: The 200-message review spreadsheet.
- **`eval/golden_eval_set_pre_review_backup.csv`**: Pristine pre-review backup with untouched empty human fields.
- **`eval/golden_review_assisted.xlsx`**: Multi-tab assisted review workbook with machine proposals and study guide.
- **`eval/golden_threads_cache.json`**: Pre-extracted cache of conversation threads for all 200 golden examples.
- **`eval/golden_thread_exclusions.json`**: Registry of 2,027 tweet IDs across all turns of the 200 conversations to prevent retrieval leakage.
- **`eval/review_app/index.html`**: Interactive web review interface.
- **`scripts/review_server.py`**: Local zero-dependency review web server (`http://127.0.0.1:8765`).
- **`scripts/review_cli.py`**: Terminal review CLI for status, thread lookup, approval, and editing.
- **`scripts/finalize_golden_set.py`**: Finalization and validation suite generating the final dataset and audit report.

---

## 3. Review Columns & Schema

In `eval/golden_eval_set_final.csv`:

| Column | Description | State |
| :--- | :--- | :--- |
| `message_id` | Original Twitter `tweet_id` | Verified Genuine |
| `conversation_id` | Root conversation ID | Verified Genuine |
| `original_text` | Exact raw tweet text (preserves typos, emojis, URLs) | Authentic UTF-8 |
| `ai_suggested_intent` | AI proposal (from locked 10-class taxonomy) | Proposal |
| `my_final_intent` | **Human sovereign gold label** | **Complete (200/200)** |
| `ai_suggested_language` | AI suggested language code | Proposal |
| `my_final_language` | **Human gold language** (`en`, `es`, `ja`, `de`, `pt`, `fr`, `it`, `other`) | **Complete (200/200)** |
| `ai_suggested_conversation_state` | AI suggested dialogue state | Proposal |
| `my_final_conversation_state` | **Human gold state** (`new_issue`, `dm_handoff`, `follow_up`, etc.) | **Complete (200/200)** |
| `ai_suggested_escalate` | AI suggested escalation flag (`true`/`false`) | Proposal |
| `my_final_escalate` | **Human gold escalation** (`true`/`false`) | **Complete (200/200)** |
| `ai_suggested_reason` | Short explanatory rationale for AI suggestion | Documented |
| `is_security_alert` | Security/fraud alert flag | Proposal |
| `my_final_is_security_alert` | **Human gold security alert** (`true` or `false`) | **Complete (200/200)** |
| `priority` | Escalation priority (`P0_CRITICAL` vs `standard`) | Proposal |
| `my_final_priority` | **Human gold priority** (`P0_CRITICAL` or `standard`) | **Complete (200/200)** |
| `notes` | Human annotation notes and boundary rationale | Populated |
| `human_review_action` | Audit trail (`approved` or `edited`) | **Audited (200/200)** |

---

## 4. Step 2C Review & Finalization Workflow

### Web UI Workflow
Launch the local review server:
```bash
python scripts/review_server.py
```
Open `http://127.0.0.1:8765` in your browser to view the interactive dashboard:
- One-click **Approve Proposal** (`[A]`) or **Save Custom Edits** (`[E]`).
- Expand full conversation context (`[T]`) with customer vs brand dialogue turns.
- Filter by pending, reviewed, difficult cases, security alerts, or multilingual tweets.

### CLI Workflow
Check review progress and inspect threads directly from the terminal:
```bash
python scripts/review_cli.py status
python scripts/review_cli.py thread <conv_id>
python scripts/review_cli.py approve <message_id>
python scripts/review_cli.py batch-unflagged
python scripts/review_cli.py sync
```

### Finalization
Run final constraint validation and generate the audited benchmark deliverable:
```bash
python scripts/finalize_golden_set.py
```

---

## 5. Leakage Prevention Protocol

To ensure rigorous evaluation:
- Downstream RAG and support-agent retrieval indices must load `eval/golden_thread_exclusions.json`.
- When retrieving historical context for an evaluation query, any candidate tweet whose `tweet_id` appears in `excluded_tweet_ids` MUST be filtered out.
- This guarantees the agent is evaluated on genuine reasoning and general knowledge rather than regurgitating the exact historical AmazonHelp response.
