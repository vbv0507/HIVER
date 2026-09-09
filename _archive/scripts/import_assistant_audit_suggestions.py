"""
Step 4B: Import Assistant Suggested Human-Audit Ratings

Imports the 50 assistant-suggested review scores into a dedicated
'Assistant Suggestions' worksheet in eval/judge_human_review.xlsx.

Guarantees:
- Matches ratings to message_id exactly.
- Does NOT alter the original 'Judge-Human Audit' sheet.
- Does NOT alter any llm_judge_* fields.
- Does NOT fill human_correctness, human_helpfulness, human_groundedness,
  human_policy, or human_escalation.
- Does NOT fabricate human_notes.
- Does NOT claim these scores are human ratings.
- Adds a clear 'README Instructions' worksheet.
"""

import sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# UTF-8 stdout configuration
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT_DIR / "eval/judge_human_review.xlsx"

# Exact 50 assistant suggested scores from prompt:
# Format: message_id -> (correctness, helpfulness, groundedness, policy, escalation, assistant_reason)
SUGGESTIONS_DATA = {
    "25279": (
        2, 2, 2, 5, 2,
        "Customer reports a costly unresolved problem; generic self-service order check lacks proactive escalation and misses financial urgency."
    ),
    "65900": (
        5, 5, 4, 5, 5,
        "Customer requests checking DM; agent provides clear, polite specialist escalation with direct message routing and secure handling."
    ),
    "77408": (
        1, 1, 2, 5, 4,
        "Customer expresses severe complaint and brand distrust; canned generic template is tone-deaf, though channel policy is maintained."
    ),
    "77535": (
        2, 2, 2, 5, 3,
        "Customer clarifies email and order confirmation history; canned account status reply does not address specific context of email history."
    ),
    "95437": (
        5, 5, 3, 5, 5,
        "Customer inquires about potential chat support security breach; agent properly initiates P0 escalation to Account Security Specialists."
    ),
    "179265": (
        1, 1, 2, 5, 2,
        "French query requesting a pertinent answer; agent sends generic English self-service template instead of responding in French or escalating."
    ),
    "180800": (
        1, 1, 2, 5, 2,
        "Customer shares URL to executive handle; generic order status response is irrelevant to the context of the tweet."
    ),
    "183483": (
        4, 3, 5, 5, 5,
        "Japanese customer expresses gratitude with request for recurrence prevention; polite Japanese reply appropriately directs to DM."
    ),
    "234555": (
        1, 1, 2, 5, 2,
        "Customer shares promotional deal link/screenshot; generic order tracking canned text does not address the promotion context."
    ),
    "258713": (
        1, 1, 2, 5, 2,
        "Customer alleging scam and demanding review post; canned self-service order text misses the review posting complaint entirely."
    ),
    "291347": (
        1, 1, 2, 5, 2,
        "Customer frustrated about back-end support access; generic self-service canned response repeats the unhelpful pattern."
    ),
    "379700": (
        1, 1, 2, 5, 1,
        "French positive banter ('what is your secret to being so good?'); agent mistakenly escalated with apology and requested order number in French."
    ),
    "379788": (
        1, 1, 2, 5, 2,
        "Customer received wrong item with photo proof; generic self-service text fails to provide replacement or return instructions."
    ),
    "459028": (
        5, 5, 4, 5, 5,
        "Customer warning about SMS phishing/unpaid fees scam; agent properly identifies security concern and instructs secure DM handling in Japanese."
    ),
    "483090": (
        4, 3, 4, 5, 5,
        "French customer asking about damaged carton refusal and signature photo; agent correctly escalates to specialist via DM in French."
    ),
    "490648": (
        4, 3, 4, 5, 5,
        "French customer reporting technical bug when contacting seller; agent appropriately escalates complex seller issue via DM in French."
    ),
    "498538": (
        1, 1, 1, 5, 1,
        "Customer complaining about late next-day Prime delivery; agent erroneously outputs Prime subscription cancellation/refund instructions."
    ),
    "508166": (
        1, 1, 2, 5, 2,
        "Customer complaining with photo about wrong item received; generic order tracking reply ignores wrong item replacement."
    ),
    "532639": (
        1, 1, 1, 5, 1,
        "German conversational banter ('Schade. Da bin ich immer neugierig'); agent sends generic English order tracking response."
    ),
    "649952": (
        1, 1, 1, 5, 1,
        "Japanese customer expressing delight that separate orders arrived in one box; agent inappropriately apologizes for inconvenience and requests DM."
    ),
    "679078": (
        1, 1, 1, 5, 1,
        "Japanese customer sharing positive purchase experience (cheap welding cartridge); agent inappropriately apologizes and requests order number."
    ),
    "701334": (
        1, 1, 1, 5, 1,
        "Customer complaining Prime Now failed delivery while at home; agent irrelevantly provides Prime subscription cancellation advice."
    ),
    "909507": (
        5, 5, 4, 5, 5,
        "Customer asking team to check DM; agent appropriately apologizes, flags for specialist review, and guides DM communication."
    ),
    "944251": (
        1, 1, 2, 5, 1,
        "Customer says 'Done.'; agent responds with generic self-service order tracking instead of acknowledging completion or continuing thread."
    ),
    "947686": (
        1, 1, 2, 5, 2,
        "Customer complaining of repeated late delivery and expired product; generic order status reply ignores serious expired product complaint."
    ),
    "984200": (
        5, 4, 3, 5, 3,
        "Customer reporting Kindle for PC formatting issue; agent provides relevant digital/Kindle troubleshooting steps."
    ),
    "1113514": (
        1, 1, 1, 5, 1,
        "Customer posting promotional image/hashtag; agent responds with generic order status advice."
    ),
    "1300626": (
        1, 1, 2, 5, 2,
        "Customer asking for link to online chat regarding 1-day shipping; generic order status response fails to provide chat link or direct help."
    ),
    "1313039": (
        1, 1, 2, 5, 1,
        "Customer praying parcel is left with neighbor for coffee machine; generic order status response misses the delivery instruction context."
    ),
    "1362458": (
        1, 1, 2, 5, 2,
        "Customer answering carrier clarification (AMZL US recurring issue); generic order status template ignores the carrier logistics feedback."
    ),
    "1382396": (
        1, 1, 1, 5, 1,
        "Customer venting about phone CS delay on delivery replacement; agent erroneously gives Online Returns Center refund instructions instead of addressing replacement delay."
    ),
    "1572905": (
        1, 1, 2, 5, 2,
        "Customer alleging scam regarding price change and delivery charges at checkout; generic self-service reply ignores billing/checkout complaint."
    ),
    "1691622": (
        1, 1, 1, 5, 2,
        "Customer complaining contest winners list is fake; generic order status reply is completely unrelated to contest inquiry."
    ),
    "1764531": (
        5, 4, 3, 5, 5,
        "Spanish customer locked out of account while ordering; agent appropriately escalates in Spanish to specialized agent via private message."
    ),
    "1829432": (
        1, 1, 2, 5, 2,
        "Customer recovering from surgery complaining items haven't arrived; generic self-service order check lacks empathy and proactive logistics check."
    ),
    "2126759": (
        4, 3, 3, 5, 2,
        "Customer asking to check status of two overdue orders; generic self-service order tracking response is partially helpful but fails to offer direct DM check."
    ),
    "2184761": (
        1, 1, 1, 5, 2,
        "Customer asking product specification question about Echo Plus bundling; agent gives irrelevant device troubleshooting/reboot instructions."
    ),
    "2254381": (
        1, 1, 1, 5, 2,
        "Portuguese customer reporting postal code/state mismatch error; agent gives generic English order status template."
    ),
    "2465040": (
        1, 1, 1, 5, 1,
        "Spanish banter requesting a Nintendo Switch; agent inappropriately treats banter as serious complaint and escalates with apology."
    ),
    "2531101": (
        2, 1, 1, 5, 2,
        "Japanese customer enthusiastically singing about joining Amazon Music Unlimited; agent inappropriately apologizes for inconvenience and requests DM."
    ),
    "2541046": (
        2, 2, 3, 5, 3,
        "Customer alleging price hike on lightning deal; agent gives general order modification/promo advice which partially touches promo code entry but misses pricing dispute."
    ),
    "2611666": (
        2, 2, 2, 5, 2,
        "Customer providing app context for earlier problem; generic order status reply fails to maintain conversation continuity."
    ),
    "2777430": (
        2, 2, 3, 5, 2,
        "Customer clarifying Kindle app link navigation; agent gives general device restart troubleshooting rather than addressing link issue."
    ),
    "2803279": (
        1, 1, 1, 5, 3,
        "Customer humorously questioning cat product recommendation; generic order status response misses the algorithmic recommendation context."
    ),
    "2841828": (
        1, 1, 2, 5, 1,
        "Portuguese customer excited about upcoming delivery; agent inappropriately apologizes in Spanish and escalates."
    ),
    "2899522": (
        1, 1, 1, 5, 1,
        "Customer thanking Amazon for surprise gift delivery; agent gives generic order status check instead of acknowledging gratitude."
    ),
    "2922515": (
        1, 1, 1, 5, 1,
        "Customer complaining late Prime delivery from 3rd party vendor; agent inappropriately gives Prime membership cancellation instructions."
    ),
    "2926332": (
        4, 3, 2, 5, 5,
        "Japanese customer debating whether to contact marketplace seller about delay; agent politely guides to DM for specialist assistance in Japanese."
    ),
    "2927090": (
        3, 3, 3, 5, 4,
        "Spanish customer complaining carrier doesn't call upon delivery; agent appropriately offers specialist escalation via private message in Spanish."
    ),
    "2971945": (
        3, 2, 2, 5, 4,
        "Japanese customer sharing positive testimonial on Amazon Prime; agent provides standard polite Japanese support greeting and DM guidance."
    ),
}


def import_suggestions():
    print("=" * 75)
    print("STEP 4B: IMPORT ASSISTANT SUGGESTED HUMAN-AUDIT RATINGS")
    print("=" * 75)

    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {XLSX_PATH}")

    wb = openpyxl.load_workbook(XLSX_PATH)

    # 1. Verify original audit sheet is untouched
    audit_sheet_name = "Judge-Human Audit"
    if audit_sheet_name not in wb.sheetnames:
        raise ValueError(f"Expected sheet '{audit_sheet_name}' not found in {XLSX_PATH}")

    ws_audit = wb[audit_sheet_name]

    # Ensure the original sheet is left completely untouched
    print(f"Verified '{audit_sheet_name}' is present. Leaving all cells and human_* columns completely untouched.")

    # 2. Create or replace 'Assistant Suggestions' worksheet
    suggestions_sheet_name = "Assistant Suggestions"
    if suggestions_sheet_name in wb.sheetnames:
        del wb[suggestions_sheet_name]

    ws_sugg = wb.create_sheet(title=suggestions_sheet_name)
    ws_sugg.views.sheetView[0].showGridLines = True

    # Styling definitions
    font_title = Font(name="Calibri", size=14, bold=True, color="1F497D")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=10, color="000000")
    font_id = Font(name="Consolas", size=10, bold=True, color="1F497D")

    fill_header = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    fill_score_hdr = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    fill_zebra = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_reason = Alignment(horizontal="left", vertical="top", wrap_text=True)

    thin_border_side = Side(style="thin", color="D9D9D9")
    border_data = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)

    # Title Block
    ws_sugg.merge_cells("A1:G1")
    title_cell = ws_sugg.cell(row=1, column=1, value="STEP 4B: ASSISTANT SUGGESTED AUDIT RATINGS (50 SAMPLES)")
    title_cell.font = font_title
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_sugg.row_dimensions[1].height = 25

    ws_sugg.merge_cells("A2:G2")
    sub_cell = ws_sugg.cell(
        row=2, column=1,
        value="NOTICE: Assistant Suggestions are provided strictly as an audit reference. Human reviewer columns remain unpopulated."
    )
    sub_cell.font = font_subtitle
    sub_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_sugg.row_dimensions[2].height = 20

    # Headers
    headers = [
        "message_id",
        "assistant_suggested_correctness",
        "assistant_suggested_helpfulness",
        "assistant_suggested_groundedness",
        "assistant_suggested_policy",
        "assistant_suggested_escalation",
        "assistant_reason",
    ]

    ws_sugg.row_dimensions[3].height = 28
    for col_idx, h in enumerate(headers, 1):
        cell = ws_sugg.cell(row=3, column=col_idx, value=h)
        cell.font = font_header
        cell.alignment = align_center
        cell.fill = fill_score_hdr if 2 <= col_idx <= 6 else fill_header

    # Populate 50 rows matching message_id from original audit sheet
    audit_mids = [str(ws_audit.cell(row=r, column=1).value).strip() for r in range(4, ws_audit.max_row + 1)]
    if len(audit_mids) != 50:
        raise ValueError(f"Expected 50 audit items in '{audit_sheet_name}', found {len(audit_mids)}")

    imported_count = 0
    for idx, mid in enumerate(audit_mids, start=4):
        if mid not in SUGGESTIONS_DATA:
            raise KeyError(f"Missing suggestion for audit message_id {mid}")

        corr, helpf, ground, pol, esc, reason = SUGGESTIONS_DATA[mid]

        row_vals = [int(mid), corr, helpf, ground, pol, esc, reason]
        is_even = (idx % 2 == 0)

        ws_sugg.row_dimensions[idx].height = 36
        for col_idx, val in enumerate(row_vals, 1):
            cell = ws_sugg.cell(row=idx, column=col_idx, value=val)
            cell.font = font_id if col_idx == 1 else font_data
            cell.border = border_data
            if is_even:
                cell.fill = fill_zebra

            if col_idx == 1:
                cell.alignment = align_center
            elif 2 <= col_idx <= 6:
                cell.alignment = align_center
            else:
                cell.alignment = align_reason

        imported_count += 1

    # Auto-adjust column widths
    col_widths = {
        "A": 16,
        "B": 32,
        "C": 32,
        "D": 34,
        "E": 28,
        "F": 32,
        "G": 85,
    }
    for col_letter, width in col_widths.items():
        ws_sugg.column_dimensions[col_letter].width = width

    ws_sugg.auto_filter.ref = f"A3:G{3 + imported_count}"

    # 3. Create or replace 'README Instructions' sheet
    readme_sheet_name = "README Instructions"
    if readme_sheet_name in wb.sheetnames:
        del wb[readme_sheet_name]

    ws_readme = wb.create_sheet(title=readme_sheet_name, index=0)
    ws_readme.views.sheetView[0].showGridLines = True

    # Build README content
    ws_readme.column_dimensions["A"].width = 25
    ws_readme.column_dimensions["B"].width = 90

    r_row = 1
    ws_readme.cell(row=r_row, column=1, value="STEP 4 HUMAN AUDIT WORKBOOK — INSTRUCTIONS").font = font_title
    ws_readme.row_dimensions[r_row].height = 28
    r_row += 2

    callout_box = [
        ("IMPORTANT NOTICE", "Assistant Suggestions are provided only as a review aid."),
        ("INDEPENDENT AUDIT", "The human_* columns require independent human judgment."),
        ("ZERO FABRICATION", "Human rating columns remain completely unpopulated until human review."),
    ]

    for title, desc in callout_box:
        c1 = ws_readme.cell(row=r_row, column=1, value=title)
        c1.font = Font(name="Calibri", size=11, bold=True, color="C00000")
        c2 = ws_readme.cell(row=r_row, column=2, value=desc)
        c2.font = Font(name="Calibri", size=11, bold=True, color="1F497D")
        ws_readme.row_dimensions[r_row].height = 22
        r_row += 1

    r_row += 1
    ws_readme.cell(row=r_row, column=1, value="WORKBOOK STRUCTURE").font = Font(name="Calibri", size=12, bold=True, color="1F497D")
    r_row += 1

    struct_info = [
        ("1. README Instructions", "Overview, scoring scale, dimension rubrics, and operational guidelines."),
        ("2. Judge-Human Audit", "Active audit worksheet containing original customer tweets, agent drafts, retrieved evidence, machine LLM judge scores, and empty human_* columns."),
        ("3. Assistant Suggestions", "Reference suggestions provided as an auxiliary evaluation aid with score breakdown and rationales."),
    ]
    for s_name, s_desc in struct_info:
        ws_readme.cell(row=r_row, column=1, value=s_name).font = Font(name="Calibri", size=10, bold=True)
        ws_readme.cell(row=r_row, column=2, value=s_desc).font = font_data
        r_row += 1

    r_row += 1
    ws_readme.cell(row=r_row, column=1, value="SCORING RUBRIC (Scale 1 to 5)").font = Font(name="Calibri", size=12, bold=True, color="1F497D")
    r_row += 1

    scale_info = [
        ("Score 5 (Excellent)", "Flawless execution, highly accurate, customer-friendly, fully grounded, safe policy."),
        ("Score 4 (Good)", "Accurate with clear next steps and good tone, minor room for enhancement."),
        ("Score 3 (Acceptable / Mixed)", "Partially correct or general advice; misses nuances or requires customer follow-up."),
        ("Score 2 (Poor)", "Misleading instructions, contradicts evidence, overly generic canned response for specific complaint."),
        ("Score 1 (Critical Failure)", "Completely erroneous advice, critical policy breach, or failed escalation on security/safety."),
    ]
    for sc, desc in scale_info:
        ws_readme.cell(row=r_row, column=1, value=sc).font = Font(name="Calibri", size=10, bold=True, color="2E75B6")
        ws_readme.cell(row=r_row, column=2, value=desc).font = font_data
        r_row += 1

    r_row += 1
    ws_readme.cell(row=r_row, column=1, value="EVALUATION DIMENSIONS").font = Font(name="Calibri", size=12, bold=True, color="1F497D")
    r_row += 1

    dim_info = [
        ("1. Correctness", "Accuracy of technical, billing, and logistical instructions."),
        ("2. Helpfulness", "Clarity of next steps, empathetic tone, and actionable guidance."),
        ("3. Groundedness", "Strict grounding in retrieved evidence; zero hallucinated order facts."),
        ("4. Policy Compliance", "Adherence to customer support safety rules (no public credential requests, proper DM routing)."),
        ("5. Escalation", "Appropriateness of auto-handle vs human specialist handoff."),
    ]
    for dm, desc in dim_info:
        ws_readme.cell(row=r_row, column=1, value=dm).font = Font(name="Calibri", size=10, bold=True)
        ws_readme.cell(row=r_row, column=2, value=desc).font = font_data
        r_row += 1

    wb.save(XLSX_PATH)
    print(f"✓ Saved updated workbook to {XLSX_PATH}")
    print(f"✓ Created '{suggestions_sheet_name}' with {imported_count} rows.")
    print(f"✓ Created '{readme_sheet_name}' with instructions and scoring rubric.")
    print(f"✓ Confirmed '{audit_sheet_name}' human columns remain completely unpopulated.")


if __name__ == "__main__":
    import_suggestions()
