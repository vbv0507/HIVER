# Repository Audit Before Cleanup (Step 4.5)

**Audit Date:** September 2026  
**Scope:** Complete repository scan (106 files across data, eval, reports, scripts, src, tests, notebooks)  
**Status:** Audit Phase Complete — Zero Deletions Performed During Audit  

---

## 1. Executive Audit Summary

The repository was systematically scanned to trace all dependencies, imports, markdown references, and evaluation linkages.

- **Total Files Audited:** 106
- **Core Production Files to Preserve:** 63 files (including 100% of core source, canonical evaluation datasets, final audit workbooks, validation scripts, unit tests, and key audit reports)
- **Obsolete / Duplicate Files to Remove:** 4 files (e.g., duplicate Excel upload `judge_human_review(1).xlsx`, unused `sample.csv`, obsolete `twcs_mock.csv`)
- **Intermediate / Provenance Files to Archive (`_archive/`):** 21 files (e.g., intermediate review iterations from Steps 2C, 4B, 4C, 4D, 4E and superseded one-off scripts)
- **Local Large Dataset (`data/raw/twcs.csv`):** Preserved locally on disk, protected from Git via `.gitignore`.
- **Secrets / Credentials Scan:** 0 hard-coded secrets or API tokens found across all files.

---

## 2. Comprehensive File-by-File Audit Table

| File Path | Purpose | Referenced By | Used By | Action | Rationale |
| :--- | :--- | :--- | :--- | :---: | :--- |
| `README.md` | Primary project documentation & reproduction guide | User, IDE, GitHub | Documentation | **KEEP** | Essential entrypoint; will update references after cleanup. |
| `requirements.txt` | Python package dependency specification | Environment setup, README | Setup / CI | **KEEP** | Cleaned and validated dependencies. |
| `.gitignore` | Git exclusion rules | Git VCS | Development | **KEEP** | Protects large raw dataset (`twcs.csv`) and local caches. |
| `.env.example` | Placeholder environment variables template | README, Setup | Configuration | **KEEP** | Safe template for API credentials. |
| `data/raw/twcs.csv` | Genuine Kaggle TWCS raw dataset (516.5 MB) | `verify_twcs.py`, `extract_amazonhelp.py`, `data_loader.py` | Data Pipeline | **KEEP (LOCAL)** | **CRITICAL DATASET**. Kept on disk, ignored by Git. |
| `data/raw/twcs_mock.csv` | Synthetic mock dataset (4.4 MB) created before Kaggle verification | `verify_twcs.py` (error message reference only) | None | **REMOVE** | Obsolete synthetic test data. Production strictly uses real `twcs.csv`. |
| `data/raw/sample.csv` | 17 KB arbitrary sample snippet | None | None | **REMOVE** | Unreferenced early exploratory file. |
| `data/raw/.gitkeep` | Git directory preservation | Git | Structure | **KEEP** | Keeps empty directory structure in Git. |
| `data/processed/AmazonHelp_tweets.csv` | 373,438 extracted AmazonHelp tweets (78.9 MB) | `validate_amazonhelp.py`, `build_retrieval_index.py`, `build_golden_set.py` | Data Pipeline | **KEEP** | Core processed artifact for Step 1.5. |
| `data/processed/AmazonHelp_conversations.csv` | Graph-linked conversation map (77.7 MB) | `validate_amazonhelp.py`, `build_golden_set.py` | Data Pipeline | **KEEP** | Core processed artifact for Step 1.5. |
| `data/processed/AmazonHelp_threads.jsonl` | 82,556 reconstructed dialogue threads (103.8 MB) | `build_retrieval_index.py`, `validate_amazonhelp.py` | Data Pipeline / Retrieval | **KEEP** | Primary retrieval corpus source for Step 3 agent. |
| `data/processed/retrieval_index.joblib` | Precomputed TF-IDF index & 20k resolutions (6.5 MB) | `src/retrieval/retriever.py`, Agent, Baselines, Tests | Runtime / Eval | **KEEP** | Production retrieval index used by agent and evaluation. |
| `data/processed/evaluation_results.jsonl` | Complete Step 4 benchmark outputs (340 KB) | `reports/evaluation_results.md`, Evaluation analysis | Results / Audit | **KEEP** | Evaluated outputs across 200 golden examples. |
| `data/processed/resolution_pairs.jsonl` | Extracted customer-resolution pairs (3.7 MB) | `build_retrieval_index.py`, `corpus_builder.py` | Retrieval Build | **KEEP** | Intermediate corpus artifact required to rebuild index. |
| `data/processed/AmazonHelp_intent_samples.json` | 500 sampled tweets for taxonomy audit (2.7 MB) | `analyze_intent_taxonomy.py` | Step 1.6 Analysis | **ARCHIVE** | Historical audit sampling artifact. Preserved in `_archive/`. |
| `data/processed/audit_50_full.json` | Stratified 50 audit sample JSON dump (62 KB) | `run_evaluation.py` | Step 4 Audit | **ARCHIVE** | Intermediate JSON dump; canonical data is in Excel/CSV. |
| `data/processed/scratch_audit_50.json` | Scratch audit sample JSON dump (61 KB) | None | Step 4 Audit | **ARCHIVE** | Scratch file from Step 4 audit setup. |
| `data/processed/.gitkeep` | Git directory preservation | Git | Structure | **KEEP** | Preserves processed directory in Git. |
| `eval/golden_eval_set_final.csv` | Final canonical 200 golden evaluation records | `run_evaluation.py`, `test_evaluation.py`, `validate_golden_set.py` | Core Evaluation | **KEEP** | **CANONICAL GOLDEN SET**. Must never be modified or deleted. |
| `eval/golden_thread_exclusions.json` | 200 excluded conversation IDs & 2,027 tweet IDs | `retriever.py`, `test_evaluation.py`, `run_evaluation.py` | Leakage Guard | **KEEP** | **CRITICAL LEAKAGE GUARD**. Enforces zero golden leakage in retrieval. |
| `eval/golden_review_final_report.md` | Final audit report of golden set review | `README.md`, Reports | Documentation | **KEEP** | Provenance report for the finalized golden evaluation set. |
| `eval/evaluation_config.json` | Configuration parameters for 200-run benchmark | `run_evaluation.py`, `metrics.py` | Evaluation | **KEEP** | Configuration for reproducibility of evaluation harness. |
| `eval/judge_human_audit.csv` | Synchronized 50-example judge-human audit dataset | `validate_judge_human_agreement.py`, `sync_human_audit_to_csv.py` | Audit Pipeline | **KEEP** | Canonical CSV representation of the 50 human audit ratings. |
| `eval/judge_human_review_ready_for_manual_check.xlsx` | Canonical reviewed 50-case workbook with 50/50 reviews | `validate_judge_human_review.py`, `validate_judge_human_agreement.py`, `review_human_audit.py` | Audit Pipeline | **KEEP** | **CANONICAL HUMAN AUDIT WORKBOOK**. Primary source of truth. |
| `eval/README.md` | Documentation for evaluation methodology | User, Reviewers | Documentation | **KEEP** | High-level evaluation overview. |
| `eval/sampling_method.md` | Documentation of stratified sampling strategy | `README.md` | Documentation | **KEEP** | Essential documentation for sampling methodology. |
| `eval/golden_review_summary.md` | Summary of golden set assisted annotation review | `README.md` | Documentation | **KEEP** | Review workflow summary document. |
| `eval/assistant_annotation_summary.md` | Documentation of assistant suggestions for golden set | `README.md` | Documentation | **KEEP** | Provenance documentation. |
| `eval/golden_eval_set.csv` | Intermediate golden set before finalization (86 KB) | Step 2C scripts | Step 2C | **ARCHIVE** | Pre-finalization review CSV. Canonical version is `_final.csv`. |
| `eval/golden_eval_set_reviewed.csv` | Intermediate reviewed golden set CSV (86 KB) | Step 2C scripts | Step 2C | **ARCHIVE** | Intermediate state during Step 2C review. |
| `eval/golden_eval_set_pre_review_backup.csv` | Backup copy of golden set before review (86 KB) | Step 2C scripts | Step 2C | **ARCHIVE** | Intermediate backup from Step 2C. |
| `eval/golden_eval_set_assistant_filled.xlsx` | Step 2C source workbook for human annotation (42 KB) | Step 2C scripts | Step 2C | **ARCHIVE** | Provenance workbook for human review proposals. |
| `eval/golden_review_assisted.xlsx` | Step 2C assisted review workbook (45 KB) | Step 2C scripts | Step 2C | **ARCHIVE** | Intermediate review workbook. |
| `eval/golden_review_state.json` | Web review app state file (52 KB) | `review_server.py` | Step 2C App | **ARCHIVE** | Web UI state file from Step 2C. |
| `eval/golden_threads_cache.json` | Reconstructed thread cache for review UI (1.4 MB) | `review_server.py` | Step 2C App | **ARCHIVE** | Cache file for local web review app. |
| `eval/review_app/index.html` | Step 2C local web review application UI (21 KB) | `review_server.py` | Step 2C App | **ARCHIVE** | Local browser UI used during Step 2C annotation. |
| `eval/judge_human_review(1).xlsx` | Duplicate download copy of audit workbook (47 KB) | None | None | **REMOVE** | Exact duplicate of `judge_human_review.xlsx`. |
| `eval/judge_human_review.xlsx` | Initial unpopulated audit workbook from Step 4B (47 KB) | Step 4B | Step 4B | **ARCHIVE** | Pre-filled template; superseded by `_ready_for_manual_check.xlsx`. |
| `eval/judge_human_review_ready.xlsx` | Intermediate audit workbook from Step 4C (48 KB) | Step 4C | Step 4C | **ARCHIVE** | Intermediate workbook; superseded by `_ready_for_manual_check.xlsx`. |
| `eval/judge_human_review_prefilled_for_review.xlsx` | Intermediate audit workbook from Step 4D (49 KB) | Step 4D | Step 4D | **ARCHIVE** | Intermediate workbook; superseded by `_ready_for_manual_check.xlsx`. |
| `eval/judge_human_suggested_ratings.csv` | Exported suggested ratings CSV from Step 4D (14 KB) | Step 4D | Step 4D | **ARCHIVE** | Intermediate export file. |
| `eval/.gitkeep` | Git directory preservation | Git | Structure | **KEEP** | Keeps eval directory tracked in Git. |
| `reports/data_verification.md` | Step 1 Kaggle dataset verification report | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Proves genuine TWCS dataset integrity. |
| `reports/AmazonHelp_data_profile.md` | Step 1.5 AmazonHelp relational data profile | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Volume, multi-turn dialogue metrics. |
| `reports/AmazonHelp_final_taxonomy.md` | Finalized 10-intent locked taxonomy specification | `README.md`, `src/classifier/` | Core Report | **KEEP** | **REQUIRED REPORT**. Locked 10-intent taxonomy specification. |
| `reports/AmazonHelp_taxonomy_audit.md` | Detailed rationale and audit of taxonomy design | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Boundary rules and confusion matrices. |
| `reports/evaluation_results.md` | Comprehensive Step 4 benchmark comparison report | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Agent vs Baselines evaluation metrics. |
| `reports/evaluation_error_analysis.md` | Deep dive into errors, failure modes, and edge cases | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Categorized error analysis and mitigations. |
| `reports/headline_metric_caveat.md` | Critique of accuracy metric & alignment trade-offs | `README.md` | Core Report | **KEEP** | **REQUIRED REPORT**. Analysis of evaluation metrics validity. |
| `reports/top_10_brands.md` | Volume & dialogue depth ranking across all TWCS brands | `README.md` | Reference Report | **KEEP** | Explains selection of AmazonHelp as the target brand. |
| `reports/AmazonHelp_intent_samples.md` | Representative quotes and borderline examples | `README.md` | Reference Report | **KEEP** | Reference quotes supporting taxonomy boundary definitions. |
| `src/__init__.py` | Package initialization and top-level exports | Modules | Package | **KEEP** | Package root. |
| `src/data_loader.py` | Chunked streaming loader for TWCS CSV | `explore_brands.py`, `01_data_exploration.ipynb` | Core Utility | **KEEP** | Memory-efficient dataset streaming utility. |
| `src/text_cleaner.py` | Tweet sanitization, emoji preservation, handle cleaning | `extract_amazonhelp.py`, `retriever.py`, `test_pipeline.py` | Core Utility | **KEEP** | Production text cleaner used throughout pipeline. |
| `src/thread_builder.py` | Conversation graph construction and thread reassembly | `extract_amazonhelp.py`, `test_pipeline.py` | Core Utility | **KEEP** | Core conversation tree reconstruction logic. |
| `src/mock_data.py` | Synthetic dataset generator (6.2 KB) | `scripts/explore_brands.py` | Obsolete | **ARCHIVE** | Synthetic generator from early prototype. Never used in production. |
| `src/classifier/__init__.py` | Classifier package export | Agent, Eval | Package | **KEEP** | Package root. |
| `src/classifier/intent_classifier.py` | Few-shot & keyword intent classifier (10 locked classes) | Agent, Baselines, Eval, Tests | Core Source | **KEEP** | Production intent classification engine. |
| `src/retrieval/__init__.py` | Retrieval package export | Agent, Eval | Package | **KEEP** | Package root. |
| `src/retrieval/retriever.py` | TF-IDF historical resolution retriever with leakage guard | Agent, Baselines, Eval, Tests | Core Source | **KEEP** | Production retriever with strict leakage protection. |
| `src/retrieval/corpus_builder.py` | Resolution corpus extractor from conversation threads | `build_retrieval_index.py` | Core Source | **KEEP** | Builds resolution pairs from threads. |
| `src/generation/__init__.py` | Generation package export | Agent, Eval | Package | **KEEP** | Package root. |
| `src/generation/generator.py` | Grounded response generator with policy constraints | Agent, Eval, Tests | Core Source | **KEEP** | Production response generation module. |
| `src/policy/__init__.py` | Policy package export | Agent, Eval | Package | **KEEP** | Package root. |
| `src/policy/escalation_policy.py` | Deterministic safety, privacy, & escalation policy engine | Agent, Baselines, Eval, Tests | Core Source | **KEEP** | Production policy & escalation engine. |
| `src/agent/__init__.py` | Agent package export | Scripts, Eval, Tests | Package | **KEEP** | Package root. |
| `src/agent/amazon_agent.py` | Full AmazonHelp customer support agent orchestrator | `run_agent.py`, `run_evaluation.py`, `test_agent.py` | Core Source | **KEEP** | Production customer support AI agent. |
| `src/baselines/__init__.py` | Baselines package export | Eval, Tests | Package | **KEEP** | Package root. |
| `src/baselines/baseline_rules.py` | Baseline 1: Rule & keyword template baseline | `run_evaluation.py`, `test_evaluation.py` | Core Source | **KEEP** | Evaluation baseline 1. |
| `src/baselines/baseline_retrieval_only.py` | Baseline 2: Nearest historical neighbor retriever | `run_evaluation.py`, `test_evaluation.py` | Core Source | **KEEP** | Evaluation baseline 2. |
| `src/evaluation/__init__.py` | Evaluation package export | Harness, Tests | Package | **KEEP** | Package root. |
| `src/evaluation/metrics.py` | Evaluation metrics suite (accuracy, F1, latency, checks) | `run_evaluation.py`, `test_evaluation.py` | Core Source | **KEEP** | Metric computation library. |
| `scripts/verify_twcs.py` | Step 1 Kaggle TWCS verification script | `README.md`, Pipeline | Core Script | **KEEP** | Verifies 2.8M row Kaggle dataset integrity. |
| `scripts/extract_amazonhelp.py` | Step 1.5 AmazonHelp extraction & thread reconstruction | `README.md`, Pipeline | Core Script | **KEEP** | Extracts 373k tweets & 82.5k conversations. |
| `scripts/validate_amazonhelp.py` | Step 1.5 AmazonHelp processed data integrity validator | `README.md`, Pipeline | Core Script | **KEEP** | Validates relational integrity and schema. |
| `scripts/analyze_intent_taxonomy.py` | Step 1.6 10-intent taxonomy validation script | `README.md`, Pipeline | Core Script | **KEEP** | Reproduces taxonomy frequency and confusion analysis. |
| `scripts/build_golden_set.py` | Step 2 Stratified golden set sampler (seed=42) | `README.md`, Pipeline | Core Script | **KEEP** | Samples 200 evaluation messages and builds exclusions. |
| `scripts/validate_golden_set.py` | Step 2/2C Golden set completeness & schema validator | `README.md`, Pipeline | Core Script | **KEEP** | Validates the 200 golden set rows. |
| `scripts/finalize_golden_set.py` | Step 2C Finalizer for canonical golden set CSV | `README.md`, Pipeline | Core Script | **KEEP** | Exports `eval/golden_eval_set_final.csv`. |
| `scripts/build_retrieval_index.py` | Step 3 Precomputes TF-IDF retrieval index (20k pairs) | `README.md`, Pipeline | Core Script | **KEEP** | Builds `retrieval_index.joblib`. |
| `scripts/run_agent.py` | Step 3 Interactive CLI customer support agent runner | `README.md`, User | Core Script | **KEEP** | Interactive demo runner for the AmazonHelp agent. |
| `scripts/run_evaluation.py` | Step 4 200-example benchmark harness (Agent vs Baselines) | `README.md`, Evaluation | Core Script | **KEEP** | Executes evaluation across 200 golden examples. |
| `scripts/llm_judge.py` | Step 4 Response quality judge with 5-dimension rubric | `run_evaluation.py`, `test_evaluation.py` | Core Script | **KEEP** | 5-dimension LLM judge evaluation engine. |
| `scripts/review_human_audit.py` | Step 4F Assisted review tool for 50 human audit cases | `README.md`, Audit | Core Script | **KEEP** | Interactive CLI review tool (show, accept, edit, status). |
| `scripts/validate_judge_human_review.py` | Step 4F Validator for human audit workbook integrity | `README.md`, Audit | Core Script | **KEEP** | Validates 50 audit cases and machine immutability. |
| `scripts/sync_human_audit_to_csv.py` | Step 4F Synchronizes reviewed human ratings to CSV | `README.md`, Audit | Core Script | **KEEP** | Mirrors Excel reviews into `judge_human_audit.csv`. |
| `scripts/validate_judge_human_agreement.py` | Step 4F Judge vs Human agreement metrics & kappa | `README.md`, Audit | Core Script | **KEEP** | Calculates exact, within-1, and Cohen's Kappa agreement. |
| `scripts/explore_brands.py` | Early pre-verification brand volume explorer (11 KB) | `README.md` (legacy) | Legacy | **ARCHIVE** | Early script with mock fallback; archived for provenance. |
| `scripts/process_brand.py` | Early generic brand processor (5.6 KB) | None | Superseded | **ARCHIVE** | Superseded by `scripts/extract_amazonhelp.py`. |
| `scripts/sample_customer_intents.py` | Step 1.6 intent sampling script (6.8 KB) | None | Superseded | **ARCHIVE** | One-off sampling script used during taxonomy design. |
| `scripts/generate_assisted_review.py` | Step 2C assisted review generator (11.8 KB) | None | Superseded | **ARCHIVE** | One-off workbook generator from Step 2C. |
| `scripts/build_full_annotations.py` | Step 2C annotation batch script (5.4 KB) | None | Superseded | **ARCHIVE** | One-off annotation script from Step 2C. |
| `scripts/generate_all_annotations.py` | Step 2C annotation generator (9.3 KB) | None | Superseded | **ARCHIVE** | One-off annotation script from Step 2C. |
| `scripts/init_review_state.py` | Step 2C review state initializer (2.3 KB) | None | Superseded | **ARCHIVE** | One-off initializer for local review web app. |
| `scripts/populate_golden_set_from_xlsx.py` | Step 2C import script from XLSX to CSV (6.1 KB) | None | Superseded | **ARCHIVE** | One-off import script from Step 2C. |
| `scripts/review_cli.py` | Step 2C CLI review tool for golden set (10.9 KB) | None | Superseded | **ARCHIVE** | Golden set review CLI; review is already finalized. |
| `scripts/review_server.py` | Step 2C local web review server (7.1 KB) | None | Superseded | **ARCHIVE** | Golden set review web server; review is already finalized. |
| `scripts/import_assistant_audit_suggestions.py` | Step 4B assistant suggestion import script (5.7 KB) | None | Superseded | **ARCHIVE** | One-off script from Step 4B; suggestions imported. |
| `scripts/build_human_review_ready_workbook.py` | Step 4C workbook enhancer (13.7 KB) | None | Superseded | **ARCHIVE** | One-off script from Step 4C; superseded by Step 4E. |
| `scripts/prepare_human_audit_recommendations.py` | Step 4D recommendation generator (15.5 KB) | None | Superseded | **ARCHIVE** | One-off script from Step 4D. |
| `scripts/prefill_audit_ratings_for_review.py` | Step 4E provisional rating prefill script (10.7 KB) | None | Superseded | **ARCHIVE** | One-off script from Step 4E; workbook populated. |
| `tests/test_agent.py` | Unit tests for AmazonHelp agent components | CI / Test Suite | Tests | **KEEP** | **REQUIRED TEST**. Verifies agent, policy, classifier, and retrieval. |
| `tests/test_evaluation.py` | Unit tests for evaluation harness, metrics, baselines | CI / Test Suite | Tests | **KEEP** | **REQUIRED TEST**. Verifies metrics, exclusions, leakage guard. |
| `tests/test_human_review_workflow.py` | Unit tests for Step 4F human audit workflow & sync | CI / Test Suite | Tests | **KEEP** | **REQUIRED TEST**. Verifies audit validation, actions, and kappa. |
| `tests/test_pipeline.py` | Unit tests for text cleaning and thread building | CI / Test Suite | Tests | **KEEP** | **REQUIRED TEST**. Verifies thread graph reconstruction & text cleaner. |
| `notebooks/01_data_exploration.ipynb` | Exploratory data analysis notebook for TWCS | User / Portfolio | Analysis | **KEEP** | Demonstrates dataset exploration and characterization. |

---

## 3. Action Plan & Classification Breakdown

### Category A: Files to REMOVE (4 files)
These files are clearly obsolete, unreferenced duplicates, or synthetic mock files with no dependencies:
1. `data/raw/twcs_mock.csv` — Synthetic mock dataset (4.4 MB)
2. `data/raw/sample.csv` — Unreferenced 17 KB sample
3. `eval/judge_human_review(1).xlsx` — Duplicate workbook copy
4. `audit_map.json` — Temporary audit scratch file

### Category B: Files to ARCHIVE in `_archive/` (21 files)
These files represent valuable iteration history and provenance, but are not needed for runtime reproduction or test suites:
- **Intermediate Golden Set Review Files (Step 2C):**
  - `eval/golden_eval_set.csv`
  - `eval/golden_eval_set_reviewed.csv`
  - `eval/golden_eval_set_pre_review_backup.csv`
  - `eval/golden_eval_set_assistant_filled.xlsx`
  - `eval/golden_review_assisted.xlsx`
  - `eval/golden_review_state.json`
  - `eval/golden_threads_cache.json`
  - `eval/review_app/index.html`
- **Intermediate Audit Review Workbooks (Steps 4B–4E):**
  - `eval/judge_human_review.xlsx`
  - `eval/judge_human_review_ready.xlsx`
  - `eval/judge_human_review_prefilled_for_review.xlsx`
  - `eval/judge_human_suggested_ratings.csv`
- **Intermediate Data Dumps:**
  - `data/processed/AmazonHelp_intent_samples.json`
  - `data/processed/audit_50_full.json`
  - `data/processed/scratch_audit_50.json`
  - `src/mock_data.py`
- **Superseded One-Off Scripts:**
  - `scripts/explore_brands.py`
  - `scripts/process_brand.py`
  - `scripts/sample_customer_intents.py`
  - `scripts/generate_assisted_review.py`
  - `scripts/build_full_annotations.py`
  - `scripts/generate_all_annotations.py`
  - `scripts/init_review_state.py`
  - `scripts/populate_golden_set_from_xlsx.py`
  - `scripts/review_cli.py`
  - `scripts/review_server.py`
  - `scripts/import_assistant_audit_suggestions.py`
  - `scripts/build_human_review_ready_workbook.py`
  - `scripts/prepare_human_audit_recommendations.py`
  - `scripts/prefill_audit_ratings_for_review.py`

### Category C: Core Files PRESERVED (63 files)
All core pipeline components, canonical evaluations, required reports, and test suites are strictly preserved.
