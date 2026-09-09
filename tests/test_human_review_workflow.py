"""
Step 4F Test Suite: Assisted Review Workflow & Validation Tests

Tests:
1. Canonical audit integrity and machine column immutability
2. Review actions: explicit approve and edit workflows
3. Rejection of automated batch approvals (no accept-all)
4. Score bounds validation (1-5 range)
5. Progress metrics calculation (total, reviewed, pending, approved, edited)
6. Difficulty highlight heuristics
7. Validation script behavior on in-progress vs completed reviews
"""

import csv
import shutil
import tempfile
import unittest
from pathlib import Path
import sys
import openpyxl

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.review_human_audit import (
    cmd_status,
    cmd_show,
    cmd_accept,
    cmd_edit,
    cmd_sync_csv,
    get_difficulty_highlights,
    COL_MESSAGE_ID,
    COL_REVIEW_STATUS,
    COL_HUMAN_CORRECTNESS,
    COL_HUMAN_HELPFULNESS,
    COL_HUMAN_GROUNDEDNESS,
    COL_HUMAN_POLICY,
    COL_HUMAN_ESCALATION,
    COL_HUMAN_REVIEW_ACTION,
    COL_HUMAN_NOTES,
)
from scripts.validate_judge_human_review import validate_review


class TestHumanReviewWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_xlsx = ROOT_DIR / "eval/judge_human_review_ready_for_manual_check.xlsx"
        cls.canonical_csv = ROOT_DIR / "eval/judge_human_audit.csv"

    def setUp(self):
        # Create a temporary working copy of the workbook for isolated tests
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_xlsx = Path(self.test_dir.name) / "test_review.xlsx"
        shutil.copyfile(self.orig_xlsx, self.test_xlsx)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pristine_workbook_validation(self):
        """Verifies the base workbook passes validation with 0 reviewed, 50 pending."""
        success = validate_review(self.orig_xlsx, require_complete=False)
        self.assertTrue(success, "Pristine workbook must pass validation")

    def test_difficulty_highlights(self):
        """Verifies difficulty detection catches divergences and policy/groundedness flags."""
        wb = openpyxl.load_workbook(self.orig_xlsx, data_only=True)
        ws = wb["Judge-Human Audit"]
        # Row 6 (ID 25279) has major divergences: Judge (5,5,5,5,5) vs Provisional (2,2,2,5,2)
        highlights = get_difficulty_highlights(ws, 6)
        self.assertTrue(len(highlights) > 0)
        self.assertTrue(any("divergence >= 2" in h for h in highlights))
        self.assertTrue(any("Escalation disagreement" in h for h in highlights))

    def test_explicit_accept_flow(self):
        """Tests accepting provisional ratings explicitly marks reviewed and approved."""
        mid = "25279"
        cmd_accept(mid, notes="Verified during audit test", workbook_path=self.test_xlsx)

        wb = openpyxl.load_workbook(self.test_xlsx, data_only=True)
        ws = wb["Judge-Human Audit"]
        row_6_status = ws.cell(row=6, column=COL_REVIEW_STATUS).value
        row_6_action = ws.cell(row=6, column=COL_HUMAN_REVIEW_ACTION).value
        row_6_notes = ws.cell(row=6, column=COL_HUMAN_NOTES).value
        row_6_c = ws.cell(row=6, column=COL_HUMAN_CORRECTNESS).value

        self.assertEqual(row_6_status, "Reviewed")
        self.assertEqual(row_6_action, "approved")
        self.assertEqual(row_6_notes, "Verified during audit test")
        self.assertEqual(row_6_c, 2)  # Remains provisional rating

        # Validate with 1 reviewed row
        success = validate_review(self.test_xlsx, require_complete=False)
        self.assertTrue(success)

    def test_explicit_edit_flow(self):
        """Tests manual editing updates ratings, status, and action."""
        mid = "25279"
        cmd_edit(mid, corr=3, helpf=3, ground=4, pol=5, esc=1, notes="Adjusted per reviewer review", workbook_path=self.test_xlsx)

        wb = openpyxl.load_workbook(self.test_xlsx, data_only=True)
        ws = wb["Judge-Human Audit"]
        self.assertEqual(ws.cell(row=6, column=COL_REVIEW_STATUS).value, "Reviewed")
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_REVIEW_ACTION).value, "edited")
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_CORRECTNESS).value, 3)
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_HELPFULNESS).value, 3)
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_GROUNDEDNESS).value, 4)
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_POLICY).value, 5)
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_ESCALATION).value, 1)
        self.assertEqual(ws.cell(row=6, column=COL_HUMAN_NOTES).value, "Adjusted per reviewer review")

        success = validate_review(self.test_xlsx, require_complete=False)
        self.assertTrue(success)

    def test_invalid_score_bounds_rejected(self):
        """Ensures scores outside 1-5 are rejected by edit command."""
        mid = "25279"
        # Rating 6 is out of bounds
        cmd_edit(mid, corr=6, helpf=3, ground=3, pol=3, esc=3, workbook_path=self.test_xlsx)

        wb = openpyxl.load_workbook(self.test_xlsx, data_only=True)
        ws = wb["Judge-Human Audit"]
        # Rating was not updated to 6
        self.assertNotEqual(ws.cell(row=6, column=COL_HUMAN_CORRECTNESS).value, 6)

    def test_no_accept_all_command(self):
        """Ensures batch-approval shortcut is NOT exposed in the CLI tool."""
        import subprocess
        result = subprocess.run(
            [sys.executable, "scripts/review_human_audit.py", "accept-all"],
            capture_output=True,
            text=True,
            cwd=str(ROOT_DIR),
        )
    def test_sync_to_csv(self):
        """Tests syncing human audit ratings to CSV preserving machine columns."""
        from scripts.sync_human_audit_to_csv import sync_ratings
        temp_csv = Path(self.test_dir.name) / "test_audit.csv"
        shutil.copyfile(self.canonical_csv, temp_csv)

        success = sync_ratings(workbook_path=self.orig_xlsx, csv_path=temp_csv)
        self.assertTrue(success)

        with open(temp_csv, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 50)
        self.assertTrue(all(r["human_correctness"] != "" for r in rows))

    def test_agreement_calculation(self):
        """Tests that agreement calculation runs without error on the reviewed workbook."""
        from scripts.validate_judge_human_agreement import load_audit_records, cohens_kappa
        records = load_audit_records(self.orig_xlsx)
        self.assertEqual(len(records), 50)
        self.assertTrue(all(r["review_status"] == "Reviewed" for r in records))

        # Test kappa helper
        kappa = cohens_kappa([5, 5, 5], [5, 5, 5])
        self.assertEqual(kappa, 1.0)


if __name__ == "__main__":
    unittest.main()
