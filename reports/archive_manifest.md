# Archive Manifest

**Archive Date:** September 2026  
**Archive Directory:** `_archive/`  
**Purpose:** Stores intermediate exploration scripts, historical annotation iterations, and legacy review artifacts to keep the primary repository clean, modular, and focused while preserving provenance.

---

## 1. Archived Data Artifacts (`_archive/data/processed/`)

| File | Size | Description & Original Role |
| :--- | :---: | :--- |
| `AmazonHelp_intent_samples.json` | 2.7 MB | 500 sampled AmazonHelp customer tweets used during Step 1.6 taxonomy analysis. Canonical taxonomy is documented in `reports/AmazonHelp_final_taxonomy.md`. |
| `audit_50_full.json` | 62 KB | Stratified 50 audit sample JSON dump generated during Step 4. Superseded by canonical CSV/Excel audit files. |
| `scratch_audit_50.json` | 61 KB | Intermediate scratch JSON dump from Step 4 audit setup. |

---

## 2. Archived Evaluation Artifacts (`_archive/eval/`)

| File | Size | Description & Original Role |
| :--- | :---: | :--- |
| `golden_eval_set.csv` | 86 KB | Intermediate unreviewed golden set CSV prior to Step 2C finalization. Canonical file is `eval/golden_eval_set_final.csv`. |
| `golden_eval_set_reviewed.csv` | 86 KB | Intermediate reviewed state of the 200 golden examples. Superseded by `eval/golden_eval_set_final.csv`. |
| `golden_eval_set_pre_review_backup.csv` | 86 KB | Pre-review backup of the 200 golden samples created during Step 2C. |
| `golden_eval_set_assistant_filled.xlsx` | 42 KB | Assistant proposals workbook used during Step 2C human review. |
| `golden_review_assisted.xlsx` | 45 KB | Assisted review workbook from Step 2C with proposed intent and escalation labels. |
| `golden_review_state.json` | 52 KB | Local web review application state file tracking reviewer selections during Step 2C. |
| `golden_threads_cache.json` | 1.4 MB | Reconstructed dialogue threads cache used by the Step 2C review server. |
| `review_app/index.html` | 21 KB | Single-page HTML/JS interface for the Step 2C local web annotation tool. |
| `judge_human_review.xlsx` | 47 KB | Initial 50-example audit workbook template created in Step 4B. Superseded by `eval/judge_human_review_ready_for_manual_check.xlsx`. |
| `judge_human_review_ready.xlsx` | 48 KB | Intermediate audit review workbook created in Step 4C with conditional formatting and data validation. |
| `judge_human_review_prefilled_for_review.xlsx` | 49 KB | Intermediate audit workbook created in Step 4D with provisional assistant drafts. |
| `judge_human_suggested_ratings.csv` | 14 KB | CSV export of recommended 1–5 human audit scores from Step 4D. |

---

## 3. Archived Scripts (`_archive/scripts/`)

| File | Size | Description & Original Role |
| :--- | :---: | :--- |
| `explore_brands.py` | 11.0 KB | Early brand volume & thread depth explorer created before genuine Kaggle dataset verification. |
| `process_brand.py` | 5.6 KB | Early generic brand filtering script; superseded by canonical `scripts/extract_amazonhelp.py`. |
| `sample_customer_intents.py` | 6.8 KB | Stratified intent sampler used for Step 1.6 taxonomy design. |
| `generate_assisted_review.py` | 11.8 KB | Step 2C generator for `golden_review_assisted.xlsx`. |
| `build_full_annotations.py` | 5.4 KB | Batch annotation helper from Step 2C. |
| `generate_all_annotations.py` | 9.3 KB | Full annotation generator from Step 2C. |
| `init_review_state.py` | 2.3 KB | Step 2C state initializer for local review server. |
| `populate_golden_set_from_xlsx.py` | 6.1 KB | Step 2C importer transferring reviewed XLSX labels to golden CSV. |
| `review_cli.py` | 10.9 KB | Interactive terminal review tool for the 200 golden examples (Step 2C). |
| `review_server.py` | 7.1 KB | Local HTTP server providing browser review interface for Step 2C. |
| `import_assistant_audit_suggestions.py` | 5.7 KB | Step 4B script that added Assistant Suggestions sheet to audit workbook. |
| `build_human_review_ready_workbook.py` | 13.7 KB | Step 4C script that created comparison view in audit workbook. |
| `prepare_human_audit_recommendations.py` | 15.5 KB | Step 4D script analyzing 50 audit cases and generating recommendations. |
| `prefill_audit_ratings_for_review.py` | 10.7 KB | Step 4E script populating provisional ratings into the audit workbook. |

---

## 4. Archived Source Modules (`_archive/src/`)

| File | Size | Description & Original Role |
| :--- | :---: | :--- |
| `mock_data.py` | 6.2 KB | Synthetic TWCS mock generator used during initial repository scaffolding before real TWCS dataset verification. Production strictly uses genuine `data/raw/twcs.csv`. |
