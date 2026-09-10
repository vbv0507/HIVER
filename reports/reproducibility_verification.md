# Reproducibility Hardening Verification

## Commands exercised from the repository root

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\verify_twcs.py
.\.venv\Scripts\python.exe scripts\extract_amazonhelp.py
.\.venv\Scripts\python.exe scripts\validate_amazonhelp.py
.\.venv\Scripts\python.exe scripts\build_retrieval_index.py
.\.venv\Scripts\python.exe scripts\run_agent.py --text "Where is my package? The tracking has not updated in two days."
.\.venv\Scripts\python.exe -m unittest discover tests -q
```

The raw Kaggle file at `data/raw/twcs.csv` is intentionally an external prerequisite and is not committed. All generated processed artifacts are rebuilt from it.

## Measured verification results

| Step | Result | Measured wall time |
| :--- | :--- | :---: |
| Fresh `pip install -r requirements.txt` | PASS: all declared direct imports succeeded in a newly created virtual environment | Completed in staged background runs; a single end-to-end stopwatch was not retained after the earlier interrupted attempts |
| `verify_twcs.py` | PASS: 2,811,774 rows; genuine-schema and diversity checks passed | 21.76 s |
| `extract_amazonhelp.py` | PASS: regenerated AmazonHelp corpus | 86.88 s |
| `validate_amazonhelp.py` | PASS: 373,438 tweets and 82,556 threads | 7.93 s |
| `build_retrieval_index.py` | PASS: rebuilt documented 20,000-pair index | 40.94 s |
| CLI inference | PASS: structured response with retrieval evidence | 5.29 s |
| Full test suite | PASS: 60 tests | 18.94 s |
| `run_evaluation.py` against rebuilt 20,000-pair index | PASS: 200 cases; reused completed judge traces | 16.60 s |

All listed pipeline timings use the genuinely fresh `%TEMP%/hiver-repro-venv` interpreter on Python 3.14.6. The dependency installation itself completed successfully, but its exact elapsed duration was not retained across the prior interrupted tool sessions; this is the sole timing value intentionally not presented as exact.

## 20,000-pair index re-evaluation

The rebuilt `retrieval_index.joblib` contains exactly **20,000** records. Re-running the 200-case evaluation against it left every requested main-agent headline metric unchanged:

| Metric | Before correction | After 20,000-pair rebuild |
| :--- | :---: | :---: |
| Intent accuracy | 79.5% | 79.5% |
| Intent macro F1 | 0.752 | 0.752 |
| Escalation accuracy / precision / recall / F1 | 62.0% / 0.556 / 0.190 / 0.283 | 62.0% / 0.556 / 0.190 / 0.283 |
| P0 security precision / recall | 1.000 (5/5) / 100.0% (5/5) | 1.000 (5/5) / 100.0% (5/5) |
| Retrieval evidence availability / top-1 hit rate | 95.0% / 41.5% | 95.0% / 41.5% |

The generated report refresh did change non-headline nearest-neighbor baseline intent accuracy from 39.0% to **41.5%**, its macro F1 from 0.223 to **0.221**, runtime latency observations, and two low-evidence score examples. `reports/evaluation_results.md` and `reports/evaluation_error_analysis.md` were regenerated; `reports/headline_metric_caveat.md` was regenerated but its numbers did not change.

## Hardening fixes

1. Replaced Windows-machine paths in `eval/evaluation_config.json` with project-relative paths, and fixed `run_evaluation.py` so it continues to write relative paths on every later evaluation run.
2. Removed machine-specific file-URI report links.
3. Made data-loader and pipeline-script data paths derive from each script's repository root rather than the caller's current working directory.
4. Fixed `scripts/run_agent.py --text "   "`: it now exits with an argparse validation error instead of silently running demo queries.
5. Added a clear, non-zero (`2`) missing-key exit path to `scripts/run_evaluation.py`; offline pipeline components remain usable without an LLM key.
6. Aligned the retrieval-index build default with the documented/evaluated 20,000-pair corpus (it had defaulted to 40,000).
7. Removed unused direct dependencies and pinned the direct runtime dependencies to the tested versions.

## Robustness checks

`/agent/respond` and `/classify` returned successful, non-empty outputs for a 6,000-character input, emoji-only text, Arabic text, no-evidence text, and regex metacharacters. Empty/whitespace and malformed JSON requests returned HTTP 422 rather than HTTP 500. `/health` returned HTTP 200 before inference requests.

With `.env` temporarily removed and both key environment variables cleared, `scripts/run_evaluation.py` returned exit code 2 and printed actionable configuration guidance; it did not silently fall back to heuristic judging.

## Repository hygiene

- `git log --all --full-history -- data/raw/twcs.csv` returned no history.
- No tracked `.env`, raw dataset, `__pycache__`, or notebook checkpoint files were found.
- The credential-pattern scan found no credential value. The only match was the intentional `your_gemini_api_key_here` placeholder in README documentation.
- No hardcoded Windows, macOS/Linux home-directory, or file-URI paths remain in project code, configuration, or documentation.

## Remaining risks

The lock versions were tested on Python 3.14.6 on Windows. The project has not been run here on macOS/Linux or older Python versions. Full response-quality evaluation requires a valid Gemini key and network access by design; the core classifier, retrieval, policy, baselines, API, and non-live tests do not.
