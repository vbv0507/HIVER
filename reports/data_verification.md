# TWCS Raw Dataset Verification Report (Step 1)

**Verification Date:** September 9, 2026  
**Target File:** `data/raw/twcs.csv`  
**Verification Script:** [`scripts/verify_twcs.py`](../scripts/verify_twcs.py)  
**Status:** **PASSED — REAL TWCS DATASET VERIFIED**

---

## 1. Dataset Provenance & Source

- **Dataset Name:** Customer Support on Twitter (TWCS)
- **Source Repository:** [Kaggle: thoughtvector/customer-support-on-twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
- **Local Path:** `data/raw/twcs.csv`
- **Confirmation of Integrity:** Completely isolated from and independent of `data/raw/twcs_mock.csv`. No mock generators, sample fallbacks, or synthetic row generation were utilized.

---

## 2. Expected vs. Actual Characteristics

| Metric | Expected TWCS Benchmark | Actual Observed Value | Status |
| :--- | :--- | :--- | :--- |
| **Total Rows** | ~2.81 Million rows | **2,811,774 rows** | PASS |
| **File Size** | ~500 MB to 1 GB uncompressed | **516,508,641 bytes** (492.58 MB) | PASS |
| **Columns Count** | Exactly 7 standard columns | **7 columns** | PASS |
| **Inbound Tweets** | ~50% – 55% customer tweets | **1,537,843** (54.69%) | PASS |
| **Outbound Tweets** | ~45% – 50% brand replies | **1,273,931** (45.31%) | PASS |
| **Unique Authors** | ~700,000 authors | **702,777** | PASS |
| **Missing Text Entries** | 0 or near 0 | **0** | PASS |
| **Duplicate `tweet_id`s** | 0 | **0** | PASS |
| **Overall Unique Texts** | High natural language variance (>95%) | **2,782,618** (98.96%) | PASS |
| **AmazonHelp Rows** | >100,000 tweets | **169,840** | PASS |
| **AmazonHelp Unique Texts**| High diversity (>90%) | **169,805** (99.98%) | PASS |

---

## 3. Schema Validation

The dataset header was inspected and validated against the official TWCS schema:

| Column Name | Expected | Actual | Description |
| :--- | :--- | :--- | :--- |
| `tweet_id` | Required | Found | Unique identifier for each tweet |
| `author_id` | Required | Found | Anonymized customer ID (numeric) or brand handle (e.g., `AmazonHelp`) |
| `inbound` | Required | Found | Boolean (`True` for customer, `False` for brand response) |
| `created_at` | Required | Found | Twitter timestamp string (`%a %b %d %H:%M:%S %z %Y`) |
| `text` | Required | Found | Raw tweet message text |
| `response_tweet_id` | Required | Found | Comma-separated child reply tweet IDs |
| `in_response_to_tweet_id`| Required | Found | Parent tweet ID being responded to |

Schema conformity is **100% exact**. No missing columns, no unexpected extraneous columns.

---

## 4. AmazonHelp Deep-Dive Inspection

Official brand author ID in TWCS: **`AmazonHelp`**

- **Total AmazonHelp Tweets:** `169,840`
- **Unique AmazonHelp Message Texts:** `169,805`
- **AmazonHelp Diversity Ratio:** `99.98%`
- **Linguistic Pattern Assessment:**
  - In contrast to synthetic/mock datasets where a small pool of 5–10 canned responses are repeated thousands of times, the real TWCS dataset exhibits genuine human and customer support diversity.
  - AmazonHelp tweets dynamically reference customer @mentions (e.g., `@115712`), issue-specific diagnostic links, case routing instructions, and distinct representative sign-offs (e.g., `^SK`, `-BM`, `^KC`).
  - This confirms the presence of natural, authentic dialogue interactions rather than templated mock data.

---

## 5. Synthetic-Data Sanity Checks

1. **Dataset Volume Sanity:**  
   The dataset comprises **2,811,774 rows** ($> 1,000,000$ sanity threshold), ruling out truncated sample datasets.
2. **Exact-Text Repetition Check:**  
   Overall text diversity across the entire dataset is **98.96%** (2,782,618 distinct texts out of 2,811,774 rows). Zero evidence of loop generation or synthetic duplication.
3. **Primary Key Integrity:**  
   Zero duplicate `tweet_id` records were found across all 2.81 million rows.
4. **Data Completeness:**  
   Zero rows contain empty or missing text.

---

## 6. Execution Summary

- **Script:** `scripts/verify_twcs.py`
- **Execution Mode:** Memory-safe chunked streaming (Python `csv.reader` streaming without in-memory CSV ballooning)
- **Runtime:** 22.53 seconds
- **Exit Status:** `0` (Success)
- **Terminal Confirmation Output:**
  ```text
  REAL TWCS DATASET VERIFIED
  ```
