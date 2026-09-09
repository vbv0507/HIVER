"""
Step 4C: Build Human Review Ready Workbook

Creates eval/judge_human_review_ready.xlsx:
1. Preserves machine/LLM judge columns unchanged.
2. Preserves Assistant Suggestions sheet with enhanced visual presentation.
3. Implements on 'Judge-Human Audit':
   - Frozen header row and frozen message context panes
   - Clear 1-5 dropdown data validations for all five human rating columns
   - Side-by-side comparison section (LLM Judge vs Assistant Suggestion vs Human Rating)
   - Explicit "Accept Assistant Suggestion" action trigger workflow
   - Automatic recording of human_review_action = approved / edited
   - Zero fabricated human notes
   - Dynamic progress dashboard (Total, Reviewed, Pending, Progress %)
   - Visible integrity callout:
     "Assistant Suggestions are review aids only. Human ratings must be independently reviewed."
4. Implements a dedicated 'Difficult Cases' sheet highlighting:
   - High divergence (diff >= 2 between Judge and Assistant)
   - Escalation disagreements
   - Policy score below 4
   - Groundedness score below 4
"""

import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# UTF-8 stdout configuration
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
SRC_XLSX_1 = ROOT_DIR / "eval/judge_human_review(1).xlsx"
SRC_XLSX_2 = ROOT_DIR / "eval/judge_human_review.xlsx"
OUTPUT_XLSX = ROOT_DIR / "eval/judge_human_review_ready.xlsx"


def load_source_workbook():
    if SRC_XLSX_1.exists():
        print(f"Loading source workbook from: {SRC_XLSX_1}")
        return openpyxl.load_workbook(SRC_XLSX_1)
    elif SRC_XLSX_2.exists():
        print(f"Loading source workbook from: {SRC_XLSX_2}")
        return openpyxl.load_workbook(SRC_XLSX_2)
    else:
        raise FileNotFoundError(f"Neither {SRC_XLSX_1} nor {SRC_XLSX_2} found!")


def build_ready_workbook():
    print("=" * 75)
    print("STEP 4C: CREATING IMPROVED HUMAN REVIEW WORKBOOK (EASY REVIEW INTERFACE)")
    print("=" * 75)

    src_wb = load_source_workbook()

    # Extract source data from 'Judge-Human Audit'
    ws_src_audit = src_wb["Judge-Human Audit"]
    ws_src_sugg = src_wb["Assistant Suggestions"]

    # Read audit items (50 rows starting at row 4)
    audit_rows = []
    for r in range(4, ws_src_audit.max_row + 1):
        mid = ws_src_audit.cell(row=r, column=1).value
        text = ws_src_audit.cell(row=r, column=2).value
        resp = ws_src_audit.cell(row=r, column=3).value
        ev = ws_src_audit.cell(row=r, column=4).value
        judge = [
            int(ws_src_audit.cell(row=r, column=5).value or 5),
            int(ws_src_audit.cell(row=r, column=6).value or 5),
            int(ws_src_audit.cell(row=r, column=7).value or 5),
            int(ws_src_audit.cell(row=r, column=8).value or 5),
            int(ws_src_audit.cell(row=r, column=9).value or 5),
        ]
        audit_rows.append({
            "mid": mid,
            "text": text,
            "resp": resp,
            "ev": ev,
            "judge": judge,
        })

    # Read assistant suggestions
    sugg_dict = {}
    for r in range(4, ws_src_sugg.max_row + 1):
        mid = ws_src_sugg.cell(row=r, column=1).value
        scores = [
            int(ws_src_sugg.cell(row=r, column=2).value),
            int(ws_src_sugg.cell(row=r, column=3).value),
            int(ws_src_sugg.cell(row=r, column=4).value),
            int(ws_src_sugg.cell(row=r, column=5).value),
            int(ws_src_sugg.cell(row=r, column=6).value),
        ]
        reason = ws_src_sugg.cell(row=r, column=7).value
        sugg_dict[mid] = {"scores": scores, "reason": reason}

    if len(audit_rows) != 50:
        raise ValueError(f"Expected 50 audit items, found {len(audit_rows)}")

    # Analyze difficult cases
    for item in audit_rows:
        mid = item["mid"]
        j = item["judge"]
        s = sugg_dict[mid]["scores"]
        diff_reasons = []
        diffs = [abs(j_score - s_score) for j_score, s_score in zip(j, s)]
        max_diff = max(diffs)
        if max_diff >= 3:
            diff_reasons.append(f"Severe divergence (diff {max_diff})")
        elif max_diff >= 2:
            diff_reasons.append(f"Moderate divergence (diff {max_diff})")
        if j[4] != s[4]:
            diff_reasons.append(f"Escalation dispute (J:{j[4]} vs A:{s[4]})")
        if j[3] < 4 or s[3] < 4:
            diff_reasons.append(f"Policy risk (J:{j[3]}, A:{s[3]})")
        if j[2] < 4 or s[2] < 4:
            diff_reasons.append(f"Groundedness gap (J:{j[2]}, A:{s[2]})")

        item["diff_reasons"] = diff_reasons
        item["is_difficult"] = len(diff_reasons) > 0
        item["asst_scores"] = s
        item["asst_reason"] = sugg_dict[mid]["reason"]

    difficult_count = sum(1 for item in audit_rows if item["is_difficult"])
    print(f"Identified {difficult_count} / 50 difficult cases for targeted review.")

    # Create new clean workbook
    wb = openpyxl.Workbook()

    # Styling Palettes
    font_bold_title = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    font_banner = Font(name="Calibri", size=10, bold=True, color="991B1B")
    font_section = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_hdr = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=9, color="0F172A")
    font_mono = Font(name="Consolas", size=9, bold=True, color="1E3A8A")
    font_flag_diff = Font(name="Calibri", size=9, bold=True, color="991B1B")
    font_flag_normal = Font(name="Calibri", size=9, color="475569")
    font_score = Font(name="Calibri", size=10, bold=True)

    fill_banner = PatternFill(start_color="FEF2F2", end_color="FEF2F2", fill_type="solid")
    fill_sec_context = PatternFill(start_color="334155", end_color="334155", fill_type="solid")  # Slate
    fill_sec_comp = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")     # Sky Blue
    fill_sec_human = PatternFill(start_color="059669", end_color="059669", fill_type="solid")    # Emerald Green

    fill_hdr_context = PatternFill(start_color="475569", end_color="475569", fill_type="solid")
    fill_hdr_llm = PatternFill(start_color="0369A1", end_color="0369A1", fill_type="solid")
    fill_hdr_asst = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    fill_hdr_human = PatternFill(start_color="059669", end_color="059669", fill_type="solid")

    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_diff_cell = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    fill_human_input = PatternFill(start_color="ECFDF5", end_color="ECFDF5", fill_type="solid")

    thin_border_side = Side(style="thin", color="CBD5E1")
    border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    thick_right_border = Border(
        left=thin_border_side,
        right=Side(style="medium", color="475569"),
        top=thin_border_side,
        bottom=thin_border_side,
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # -------------------------------------------------------------------------
    # SHEET 1: README & Instructions
    # -------------------------------------------------------------------------
    ws_readme = wb.active
    ws_readme.title = "README & Instructions"
    ws_readme.views.sheetView[0].showGridLines = True
    ws_readme.column_dimensions["A"].width = 24
    ws_readme.column_dimensions["B"].width = 95

    r = 1
    ws_readme.cell(row=r, column=1, value="STEP 4C: HUMAN AUDIT WORKBOOK — REVIEW GUIDE").font = font_bold_title
    ws_readme.row_dimensions[r].height = 28
    r += 2

    # Mandatory callouts
    callouts = [
        ("MANDATORY INTEGRITY NOTICE", "Assistant Suggestions are review aids only. Human ratings must be independently reviewed."),
        ("EXPLICIT ACTION REQUIREMENT", "Clicking 'Accept Assistant Suggestion' or selecting scores is an explicit human action. No fields are filled automatically."),
        ("ZERO FABRICATION", "Do not invent human notes, timestamps, or approvals. Every rating represents sovereign human judgment."),
    ]
    for title, text in callouts:
        c1 = ws_readme.cell(row=r, column=1, value=title)
        c1.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
        c2 = ws_readme.cell(row=r, column=2, value=text)
        c2.font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")
        ws_readme.row_dimensions[r].height = 22
        r += 1

    r += 1
    ws_readme.cell(row=r, column=1, value="WORKBOOK STRUCTURE").font = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    r += 1
    sheets_info = [
        ("1. README & Instructions", "Overview, operational integrity rules, scoring scale, and workflow instructions."),
        ("2. Judge-Human Audit", "Active review interface with frozen panes, 1–5 dropdown validations, side-by-side comparison, explicit 'Accept Assistant Suggestion' trigger, and progress dashboard."),
        ("3. Difficult Cases", "Pre-filtered priority view isolating cases with large Judge-Assistant divergences (diff >= 2), escalation disputes, or low groundedness/policy scores."),
        ("4. Assistant Suggestions", "Reference library with all 50 assistant suggestions, breakdown across 5 dimensions, and detailed context rationales."),
    ]
    for name, desc in sheets_info:
        ws_readme.cell(row=r, column=1, value=name).font = Font(name="Calibri", size=10, bold=True)
        ws_readme.cell(row=r, column=2, value=desc).font = font_data
        ws_readme.row_dimensions[r].height = 20
        r += 1

    r += 1
    ws_readme.cell(row=r, column=1, value="SCORING RUBRIC (Scale 1 to 5)").font = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    r += 1
    rubric_info = [
        ("5 = Excellent", "Flawless execution; completely accurate policy advice, customer-friendly, grounded, safe DM transfer."),
        ("4 = Good", "Accurate with clear next steps and polite tone; minor cosmetic room for improvement."),
        ("3 = Acceptable / Mixed", "Partially correct or general advice; misses specific nuances or requires customer follow-up."),
        ("2 = Poor", "Misleading instructions, contradicts evidence, or sends generic canned response for a complex dispute."),
        ("1 = Critical Failure", "Erroneous advice, critical security breach, or failed escalation on security/safety incidents."),
    ]
    for score_lbl, desc in rubric_info:
        ws_readme.cell(row=r, column=1, value=score_lbl).font = Font(name="Calibri", size=10, bold=True, color="0284C7")
        ws_readme.cell(row=r, column=2, value=desc).font = font_data
        ws_readme.row_dimensions[r].height = 20
        r += 1

    r += 1
    ws_readme.cell(row=r, column=1, value="HOW TO CONDUCT REVIEW").font = Font(name="Calibri", size=11, bold=True, color="1E3A8A")
    r += 1
    workflow_steps = [
        ("Method A: In Excel", "On 'Judge-Human Audit', select 'Accept Assistant Suggestion' in Action column (Q) to approve, or manually pick 1–5 from dropdowns (Cols R-V) to edit."),
        ("Method B: Via CLI Tool", "Run `python scripts/review_human_audit.py accept <message_id>` or `python scripts/review_human_audit.py edit <message_id> ...`."),
        ("Verification Command", "Run `python scripts/validate_judge_human_review.py` to audit completion, schema integrity, and rule conformance."),
    ]
    for method, desc in workflow_steps:
        ws_readme.cell(row=r, column=1, value=method).font = Font(name="Calibri", size=10, bold=True)
        ws_readme.cell(row=r, column=2, value=desc).font = font_data
        ws_readme.row_dimensions[r].height = 20
        r += 1

    # -------------------------------------------------------------------------
    # SHEET 2: Judge-Human Audit (Primary Interactive Review Sheet)
    # -------------------------------------------------------------------------
    ws_audit = wb.create_sheet(title="Judge-Human Audit")
    ws_audit.views.sheetView[0].showGridLines = True

    # Row 1: Header Banner & Mandatory Warning
    ws_audit.merge_cells("A1:D1")
    cell_a1 = ws_audit.cell(row=1, column=1, value="STEP 4C: HUMAN AUDIT REVIEW INTERFACE")
    cell_a1.font = Font(name="Calibri", size=12, bold=True, color="FFFFFF")
    cell_a1.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    cell_a1.alignment = align_center

    ws_audit.merge_cells("E1:X1")
    cell_e1 = ws_audit.cell(
        row=1, column=5,
        value="NOTICE: Assistant Suggestions are review aids only. Human ratings must be independently reviewed."
    )
    cell_e1.font = Font(name="Calibri", size=10, bold=True, color="991B1B")
    cell_e1.fill = fill_banner
    cell_e1.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_audit.row_dimensions[1].height = 26

    # Row 2: Live Progress Dashboard (Dynamic Excel Formulas)
    ws_audit.cell(row=2, column=1, value="PROGRESS:").font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")
    ws_audit.cell(row=2, column=2, value="Total = 50").font = Font(name="Calibri", size=10, bold=True)

    ws_audit.cell(row=2, column=3, value="Reviewed:").font = Font(name="Calibri", size=10, bold=True, color="059669")
    # Reviewed formula: rows 6 to 55 where human ratings are non-empty
    ws_audit.cell(row=2, column=4, value='=COUNTIFS(R6:R55,"<>",S6:S55,"<>",T6:T55,"<>",U6:U55,"<>",V6:V55,"<>")').font = Font(name="Calibri", size=10, bold=True, color="059669")

    ws_audit.cell(row=2, column=5, value="Pending:").font = Font(name="Calibri", size=10, bold=True, color="D97706")
    ws_audit.cell(row=2, column=6, value='=50-D2').font = Font(name="Calibri", size=10, bold=True, color="D97706")

    ws_audit.cell(row=2, column=7, value="Progress %:").font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")
    ws_audit.cell(row=2, column=8, value='=D2/50').font = Font(name="Calibri", size=10, bold=True, color="1E3A8A")
    ws_audit.cell(row=2, column=8).number_format = "0.0%"

    ws_audit.cell(row=2, column=9, value="Approved:").font = Font(name="Calibri", size=10, bold=True, color="059669")
    ws_audit.cell(row=2, column=10, value='=COUNTIF(W6:W55, "approved")').font = Font(name="Calibri", size=10, bold=True)

    ws_audit.cell(row=2, column=11, value="Edited:").font = Font(name="Calibri", size=10, bold=True, color="2563EB")
    ws_audit.cell(row=2, column=12, value='=COUNTIF(W6:W55, "edited")').font = Font(name="Calibri", size=10, bold=True)

    ws_audit.row_dimensions[2].height = 22

    # Row 3: Human Review Instruction Box
    ws_audit.merge_cells("A3:X3")
    inst_box = ws_audit.cell(
        row=3, column=1,
        value="HUMAN REVIEW INSTRUCTIONS: To approve, choose 'Accept Assistant Suggestion' in Action (Col Q). To edit, select scores 1–5 from dropdowns (Cols R-V). Human review action will record as 'approved' or 'edited'. No notes are invented."
    )
    inst_box.font = Font(name="Calibri", size=9, italic=True, color="334155")
    inst_box.fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")
    inst_box.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws_audit.row_dimensions[3].height = 22

    # Row 4: Super-Headers
    super_sections = [
        ("A4:E4", "1. CONTEXT & ORIGINAL QUERY (MACHINE TRACES)", fill_sec_context),
        ("F4:P4", "2. SIDE-BY-SIDE COMPARISON: LLM JUDGE vs ASSISTANT SUGGESTION", fill_sec_comp),
        ("Q4:X4", "3. HUMAN AUDIT REVIEW & EXPLICIT WORKFLOW (SOVEREIGN HUMAN ACTION)", fill_sec_human),
    ]
    for cell_range, label, fill in super_sections:
        ws_audit.merge_cells(cell_range)
        top_cell = ws_audit[cell_range.split(":")[0]]
        top_cell.value = label
        top_cell.font = font_section
        top_cell.fill = fill
        top_cell.alignment = align_center
    ws_audit.row_dimensions[4].height = 24

    # Row 5: Column Headers
    headers = [
        # Context (A - E)
        ("message_id", fill_hdr_context),
        ("original_text", fill_hdr_context),
        ("agent_response", fill_hdr_context),
        ("retrieved_evidence", fill_hdr_context),
        ("audit_difficulty_flag", fill_hdr_context),
        # Comparison (F - P)
        ("llm_correctness", fill_hdr_llm),
        ("asst_correctness", fill_hdr_asst),
        ("llm_helpfulness", fill_hdr_llm),
        ("asst_helpfulness", fill_hdr_asst),
        ("llm_groundedness", fill_hdr_llm),
        ("asst_groundedness", fill_hdr_asst),
        ("llm_policy", fill_hdr_llm),
        ("asst_policy", fill_hdr_asst),
        ("llm_escalation", fill_hdr_llm),
        ("asst_escalation", fill_hdr_asst),
        ("assistant_reason", fill_hdr_asst),
        # Human Review (Q - X)
        ("review_action_trigger", fill_hdr_human),
        ("human_correctness", fill_hdr_human),
        ("human_helpfulness", fill_hdr_human),
        ("human_groundedness", fill_hdr_human),
        ("human_policy", fill_hdr_human),
        ("human_escalation", fill_hdr_human),
        ("human_review_action", fill_hdr_human),
        ("human_notes", fill_hdr_human),
    ]

    for col_idx, (h_title, h_fill) in enumerate(headers, 1):
        cell = ws_audit.cell(row=5, column=col_idx, value=h_title)
        cell.font = font_hdr
        cell.fill = h_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_cell
    ws_audit.row_dimensions[5].height = 30

    # Data Validation Rules
    # Action trigger validation
    dv_action = DataValidation(
        type="list",
        formula1='"Accept Assistant Suggestion,Manual Edit"',
        allow_blank=True,
    )
    dv_action.errorTitle = "Invalid Action"
    dv_action.error = "Please select 'Accept Assistant Suggestion' or 'Manual Edit'."
    ws_audit.add_data_validation(dv_action)
    dv_action.add("Q6:Q55")

    # Score validation (1 to 5) for human ratings
    dv_score = DataValidation(
        type="list",
        formula1='"1,2,3,4,5"',
        allow_blank=True,
    )
    dv_score.errorTitle = "Invalid Rating"
    dv_score.error = "Rating must be an integer between 1 (Critical Failure) and 5 (Excellent)."
    ws_audit.add_data_validation(dv_score)
    dv_score.add("R6:V55")

    # Populate 50 rows (rows 6 to 55)
    for idx, item in enumerate(audit_rows, start=6):
        mid = int(item["mid"])
        text = str(item["text"] or "")
        resp = str(item["resp"] or "")
        ev = str(item["ev"] or "")
        is_diff = item["is_difficult"]
        diff_str = " | ".join(item["diff_reasons"]) if is_diff else "NORMAL"

        j = item["judge"]
        s = item["asst_scores"]
        reason = item["asst_reason"]

        is_even = (idx % 2 == 0)
        row_fill = fill_zebra if is_even else PatternFill(fill_type=None)

        # Context cells
        ws_audit.cell(row=idx, column=1, value=mid).font = font_mono
        ws_audit.cell(row=idx, column=1).alignment = align_center

        ws_audit.cell(row=idx, column=2, value=text).font = font_data
        ws_audit.cell(row=idx, column=2).alignment = align_left

        ws_audit.cell(row=idx, column=3, value=resp).font = font_data
        ws_audit.cell(row=idx, column=3).alignment = align_left

        ws_audit.cell(row=idx, column=4, value=ev).font = font_data
        ws_audit.cell(row=idx, column=4).alignment = align_left

        # Audit Flag
        flag_cell = ws_audit.cell(row=idx, column=5, value=diff_str)
        flag_cell.font = font_flag_diff if is_diff else font_flag_normal
        flag_cell.alignment = align_left
        if is_diff:
            flag_cell.fill = fill_diff_cell

        # Side-by-side comparison cells
        # Correctness (LLM vs Asst)
        ws_audit.cell(row=idx, column=6, value=j[0]).font = font_score
        ws_audit.cell(row=idx, column=6).alignment = align_center
        ws_audit.cell(row=idx, column=7, value=s[0]).font = font_score
        ws_audit.cell(row=idx, column=7).alignment = align_center

        # Helpfulness (LLM vs Asst)
        ws_audit.cell(row=idx, column=8, value=j[1]).font = font_score
        ws_audit.cell(row=idx, column=8).alignment = align_center
        ws_audit.cell(row=idx, column=9, value=s[1]).font = font_score
        ws_audit.cell(row=idx, column=9).alignment = align_center

        # Groundedness (LLM vs Asst)
        ws_audit.cell(row=idx, column=10, value=j[2]).font = font_score
        ws_audit.cell(row=idx, column=10).alignment = align_center
        ws_audit.cell(row=idx, column=11, value=s[2]).font = font_score
        ws_audit.cell(row=idx, column=11).alignment = align_center

        # Policy (LLM vs Asst)
        ws_audit.cell(row=idx, column=12, value=j[3]).font = font_score
        ws_audit.cell(row=idx, column=12).alignment = align_center
        ws_audit.cell(row=idx, column=13, value=s[3]).font = font_score
        ws_audit.cell(row=idx, column=13).alignment = align_center

        # Escalation (LLM vs Asst)
        ws_audit.cell(row=idx, column=14, value=j[4]).font = font_score
        ws_audit.cell(row=idx, column=14).alignment = align_center
        ws_audit.cell(row=idx, column=15, value=s[4]).font = font_score
        ws_audit.cell(row=idx, column=15).alignment = align_center

        # Assistant Reason
        ws_audit.cell(row=idx, column=16, value=reason).font = font_data
        ws_audit.cell(row=idx, column=16).alignment = align_left

        # Explicit Workflow Columns (Cols Q to X)
        # Col Q: Action Trigger (empty string initially)
        act_cell = ws_audit.cell(row=idx, column=17, value="")
        act_cell.font = Font(name="Calibri", size=9, bold=True, color="059669")
        act_cell.alignment = align_center

        # Col R to V: Human Ratings formulas linked to Action Trigger
        # If Q is "Accept Assistant Suggestion", populate with assistant score, else blank
        ws_audit.cell(row=idx, column=18, value=f'=IF(Q{idx}="Accept Assistant Suggestion", G{idx}, "")')
        ws_audit.cell(row=idx, column=19, value=f'=IF(Q{idx}="Accept Assistant Suggestion", I{idx}, "")')
        ws_audit.cell(row=idx, column=20, value=f'=IF(Q{idx}="Accept Assistant Suggestion", K{idx}, "")')
        ws_audit.cell(row=idx, column=21, value=f'=IF(Q{idx}="Accept Assistant Suggestion", M{idx}, "")')
        ws_audit.cell(row=idx, column=22, value=f'=IF(Q{idx}="Accept Assistant Suggestion", O{idx}, "")')

        for c_idx in range(18, 23):
            cell = ws_audit.cell(row=idx, column=c_idx)
            cell.font = Font(name="Calibri", size=10, bold=True, color="059669")
            cell.alignment = align_center
            cell.fill = fill_human_input

        # Col W: human_review_action formula
        ws_audit.cell(
            row=idx, column=23,
            value=f'=IF(Q{idx}="Accept Assistant Suggestion", "approved", IF(COUNTA(R{idx}:V{idx})=5, "edited", ""))'
        ).font = Font(name="Calibri", size=9, bold=True, color="0F172A")
        ws_audit.cell(row=idx, column=23).alignment = align_center

        # Col X: human_notes (blank initially)
        ws_audit.cell(row=idx, column=24, value="").font = font_data
        ws_audit.cell(row=idx, column=24).alignment = align_left

        # Borders and heights
        ws_audit.row_dimensions[idx].height = 42
        for col_i in range(1, 25):
            c = ws_audit.cell(row=idx, column=col_i)
            c.border = border_cell
            if col_i in [5, 16]:
                c.border = thick_right_border
            if row_fill.fill_type and col_i not in [5, 18, 19, 20, 21, 22]:
                c.fill = row_fill

    # Set column widths
    widths = {
        "A": 13, "B": 38, "C": 42, "D": 36, "E": 26,
        "F": 14, "G": 14, "H": 14, "I": 14, "J": 14, "K": 14,
        "L": 13, "M": 13, "N": 13, "O": 13, "P": 60,
        "Q": 24, "R": 16, "S": 16, "T": 16, "U": 15, "V": 16, "W": 18, "X": 25,
    }
    for col_letter, w in widths.items():
        ws_audit.column_dimensions[col_letter].width = w

    # Freeze Panes: Row 5 frozen, so headers + dashboard stay visible
    ws_audit.freeze_panes = "F6"

    # -------------------------------------------------------------------------
    # SHEET 3: Difficult Cases (Priority Filtered View)
    # -------------------------------------------------------------------------
    ws_diff = wb.create_sheet(title="Difficult Cases")
    ws_diff.views.sheetView[0].showGridLines = True

    ws_diff.merge_cells("A1:K1")
    d_title = ws_diff.cell(row=1, column=1, value="DIFFICULT CASES FOR PRIORITIZED HUMAN AUDIT (46 SAMPLES)")
    d_title.font = font_bold_title
    d_title.alignment = align_center
    ws_diff.row_dimensions[1].height = 28

    ws_diff.merge_cells("A2:K2")
    d_sub = ws_diff.cell(
        row=2, column=1,
        value="Filter criteria: Score divergence >= 2, escalation disagreement, policy score < 4, or groundedness score < 4."
    )
    d_sub.font = Font(name="Calibri", size=10, italic=True, color="64748B")
    d_sub.alignment = align_center
    ws_diff.row_dimensions[2].height = 20

    diff_headers = [
        "message_id", "audit_flag_reasons", "customer_text", "agent_response",
        "llm_scores (C,H,G,P,E)", "asst_scores (C,H,G,P,E)", "assistant_reason"
    ]
    ws_diff.row_dimensions[3].height = 26
    for col_i, dh in enumerate(diff_headers, 1):
        cell = ws_diff.cell(row=3, column=col_i, value=dh)
        cell.font = font_hdr
        cell.fill = PatternFill(start_color="B91C1C", end_color="B91C1C", fill_type="solid")
        cell.alignment = align_center
        cell.border = border_cell

    d_row = 4
    for item in audit_rows:
        if not item["is_difficult"]:
            continue

        ws_diff.cell(row=d_row, column=1, value=int(item["mid"])).font = font_mono
        ws_diff.cell(row=d_row, column=1).alignment = align_center

        ws_diff.cell(row=d_row, column=2, value=" | ".join(item["diff_reasons"])).font = font_flag_diff
        ws_diff.cell(row=d_row, column=2).alignment = align_left

        ws_diff.cell(row=d_row, column=3, value=item["text"]).font = font_data
        ws_diff.cell(row=d_row, column=3).alignment = align_left

        ws_diff.cell(row=d_row, column=4, value=item["resp"]).font = font_data
        ws_diff.cell(row=d_row, column=4).alignment = align_left

        ws_diff.cell(row=d_row, column=5, value=str(item["judge"])).font = font_score
        ws_diff.cell(row=d_row, column=5).alignment = align_center

        ws_diff.cell(row=d_row, column=6, value=str(item["asst_scores"])).font = font_score
        ws_diff.cell(row=d_row, column=6).alignment = align_center

        ws_diff.cell(row=d_row, column=7, value=item["asst_reason"]).font = font_data
        ws_diff.cell(row=d_row, column=7).alignment = align_left

        ws_diff.row_dimensions[d_row].height = 42
        for c in range(1, 8):
            ws_diff.cell(row=d_row, column=c).border = border_cell

        d_row += 1

    diff_widths = {"A": 14, "B": 32, "C": 40, "D": 45, "E": 22, "F": 22, "G": 65}
    for col_l, w in diff_widths.items():
        ws_diff.column_dimensions[col_l].width = w

    # -------------------------------------------------------------------------
    # SHEET 4: Assistant Suggestions (Preserved Reference Sheet)
    # -------------------------------------------------------------------------
    ws_asst = wb.create_sheet(title="Assistant Suggestions")
    ws_asst.views.sheetView[0].showGridLines = True

    # Copy exact content from source suggestions sheet with visual polish
    ws_asst.merge_cells("A1:G1")
    ws_asst.cell(row=1, column=1, value="STEP 4B/4C: ASSISTANT SUGGESTIONS REFERENCE LIBRARY (50 SAMPLES)").font = font_bold_title
    ws_asst.row_dimensions[1].height = 25

    ws_asst.merge_cells("A2:G2")
    ws_asst.cell(
        row=2, column=1,
        value="Assistant Suggestions are provided strictly as an audit reference. Human ratings must be independently verified."
    ).font = Font(name="Calibri", size=10, italic=True, color="595959")
    ws_asst.row_dimensions[2].height = 20

    s_headers = [
        "message_id",
        "assistant_suggested_correctness",
        "assistant_suggested_helpfulness",
        "assistant_suggested_groundedness",
        "assistant_suggested_policy",
        "assistant_suggested_escalation",
        "assistant_reason",
    ]
    ws_asst.row_dimensions[3].height = 28
    for col_i, sh in enumerate(s_headers, 1):
        cell = ws_asst.cell(row=3, column=col_i, value=sh)
        cell.font = font_hdr
        cell.fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid") if col_i in [1, 7] else PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
        cell.alignment = align_center

    for r_idx, item in enumerate(audit_rows, start=4):
        mid = int(item["mid"])
        s = item["asst_scores"]
        reason = item["asst_reason"]
        vals = [mid, s[0], s[1], s[2], s[3], s[4], reason]

        ws_asst.row_dimensions[r_idx].height = 36
        for col_i, v in enumerate(vals, 1):
            c = ws_asst.cell(row=r_idx, column=col_i, value=v)
            c.font = font_mono if col_i == 1 else font_data
            c.border = border_cell
            if col_i == 1:
                c.alignment = align_center
            elif 2 <= col_i <= 6:
                c.alignment = align_center
            else:
                c.alignment = align_left

    s_widths = {"A": 16, "B": 32, "C": 32, "D": 34, "E": 28, "F": 32, "G": 85}
    for col_l, w in s_widths.items():
        ws_asst.column_dimensions[col_l].width = w

    # Save finalized workbook
    wb.save(OUTPUT_XLSX)
    print(f"✓ Created {OUTPUT_XLSX} with 4 comprehensive sheets:")
    print("  1. README & Instructions")
    print("  2. Judge-Human Audit (with dropdown validations, formulas, dashboard, and comparison)")
    print("  3. Difficult Cases (46 prioritized audit cases)")
    print("  4. Assistant Suggestions (reference library)")


if __name__ == "__main__":
    build_ready_workbook()
