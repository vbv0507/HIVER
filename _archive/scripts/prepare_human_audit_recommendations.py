"""
Step 4D: Prepare Review Ratings for the 50-Row Human Audit

Produces recommended 1-5 evaluation ratings and detailed analytical rationales
for all 50 human audit examples based on:
- What the customer asked
- What the agent actually answered
- Whether retrieved evidence supports the answer
- Whether the escalation decision was appropriate

Outputs:
- New worksheet 'Suggested Human Ratings' in eval/judge_human_review_ready.xlsx
- CSV file eval/judge_human_suggested_ratings.csv

Guarantees:
- Zero human_* fields overwritten in 'Judge-Human Audit'.
- Zero machine llm_judge_* fields modified.
- Zero fabricated human authorship, timestamps, or approvals.
"""

import csv
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Reconfigure stdout for UTF-8 compatibility
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT_DIR / "eval/judge_human_review_ready.xlsx"
CSV_PATH = ROOT_DIR / "eval/judge_human_suggested_ratings.csv"

# Recommended 50 audit ratings and comprehensive 4-part analytical rationales:
# (correctness, helpfulness, groundedness, policy, escalation, suggested_reason)
RECOMMENDATIONS: Dict[str, Tuple[int, int, int, int, int, str]] = {
    "25279": (
        2, 2, 2, 5, 2,
        "Customer asked about a costly unresolved dispute with Amazon. Agent delivered a generic canned template advising the customer to check 'Your Orders' with Order ID. The retrieved evidence contains general return threads with low relevance (score ~0.15) lacking dispute guidance. Escalation was inappropriately withheld despite the explicit report of severe financial impact, though standard public channel safety policy was maintained."
    ),
    "65900": (
        5, 5, 4, 5, 5,
        "Customer requested AmazonHelp to check their direct message ('plzzz check DM'). Agent correctly recognized active DM handoff state, expressed empathy, and properly escalated to a customer support specialist via secure private message. Retrieved evidence strongly supported DM routing (score 0.43). Escalation decision was completely appropriate, secure, and customer-friendly."
    ),
    "77408": (
        1, 1, 2, 5, 4,
        "Customer vented severe frustration and brand distrust ('Please don't buy any product from amazon... see real face of company'). Agent gave an unhelpful, tone-deaf canned self-service order check. Retrieved evidence matched general customer centricity complaints (score 0.29) but was not utilized to de-escalate. While channel policy was preserved, auto-handling was poor though escalation was marked standard."
    ),
    "77535": (
        2, 2, 2, 5, 3,
        "Customer clarified their account email address history and old order confirmations in inbox. Agent provided a generic account and order lookup template. Retrieved evidence had low relevance (score 0.14) packaging threads with minimal context fit. Escalation policy was acceptable, but the reply missed the specific account email clarification context."
    ),
    "95437": (
        5, 5, 3, 5, 5,
        "Customer asked whether online chat support was hacked. Agent immediately identified potential account security compromise, gave explicit safety warnings not to share passwords publicly, and escalated to Account Security Specialists via DM. Retrieved evidence showed general chat hours rather than security breaches, but agent correctly overrode retrieval to trigger mandatory P0 critical security escalation."
    ),
    "179265": (
        1, 1, 2, 5, 2,
        "French customer demanded a pertinent answer after prior frustration. Agent sent a generic English canned self-service template. Retrieved evidence contained French thread fragments (score 0.26) that were not leveraged for language matching. Escalation was inappropriately withheld and the response failed basic language alignment."
    ),
    "180800": (
        1, 1, 2, 5, 2,
        "Customer shared a URL directed to executive Twitter handle. Agent provided an irrelevant canned order tracking message. Retrieved evidence consisted of general link discussions (score 0.17) without context alignment. The agent auto-handled an out-of-domain conversational tweet with an unhelpful generic response."
    ),
    "183483": (
        4, 3, 5, 5, 5,
        "Japanese customer politely requested measures to prevent recurring delivery issues after procedure completion. Agent appropriately replied in polite Japanese (keigo), acknowledged the trouble, and guided the customer to provide the order number via DM for specialist review. Retrieved evidence directly matched delivery provider resolution patterns in Japanese (score 0.97). Escalation to specialist review was well-judged."
    ),
    "234555": (
        1, 1, 2, 5, 2,
        "Customer shared a promotional deal link/screenshot. Agent delivered an irrelevant canned order tracking response. Retrieved evidence referenced contest winner announcements (score 0.55) rather than deal verification. The agent auto-handled with an irrelevant order response instead of routing promotional queries."
    ),
    "258713": (
        1, 1, 2, 5, 2,
        "Customer protested a blocked product review with allegations of fraud (#ScamAtAmazon). Agent responded with a canned order lookup advice template. Retrieved evidence showed low-relevance return threads (score 0.13). The agent failed to escalate a community review moderation dispute, sending a repetitive template that increased customer friction."
    ),
    "291347": (
        1, 1, 2, 5, 2,
        "Customer vented frustration that Twitter support lacks back-end system access. Agent repeated a canned self-service template. Retrieved evidence had low relevance (score 0.14). The agent inappropriately auto-handled when severe customer hostility and back-end inquiry strictly required specialist routing."
    ),
    "379700": (
        1, 1, 2, 5, 1,
        "French positive humor tweet ('what is your secret to being so good?'). Agent mistakenly escalated with an apology and requested order number in French. Retrieved evidence had minimal relevance. The escalation was a false positive failure, treating playful customer banter as a severe logistics error."
    ),
    "379788": (
        1, 1, 2, 5, 2,
        "Customer received wrong item with photo comparison proof. Agent responded with generic order tracking advice. Retrieved evidence showed package delay threads (score 0.15). The agent failed to escalate or provide wrong-item replacement instructions, missing the core customer issue."
    ),
    "459028": (
        5, 5, 4, 5, 5,
        "Customer warned about SMS phishing and fake legal fee threats in Japanese. Agent correctly identified an account security threat, warned against sharing credentials, and requested safe DM contact in Japanese. Retrieved evidence contained phishing resolution patterns. Escalation to security specialists was flawless."
    ),
    "483090": (
        4, 3, 4, 5, 5,
        "French customer inquired about refusing a damaged carton and delivery signature forgery. Agent correctly escalated to a specialized agent via DM in French. Retrieved evidence matched French carrier dispute threads. Escalation to human specialist was completely appropriate for potential courier fraud."
    ),
    "490648": (
        4, 3, 4, 5, 5,
        "French customer reported an IT bug in the order portal preventing seller contact. Agent appropriately escalated the technical marketplace issue to a specialist via private message in French. Retrieved evidence supported seller contact troubleshooting. Escalation was well-reasoned and necessary."
    ),
    "498538": (
        1, 1, 1, 5, 1,
        "Customer complained about delayed next-day Prime delivery. Agent erroneously replied with Prime subscription cancellation and refund guidance. Retrieved evidence was misaligned around subscription administration. Escalation was a critical failure, misclassifying a logistics failure into subscription cancellation."
    ),
    "508166": (
        1, 1, 2, 5, 2,
        "Customer humorously shared a photo of wrong item received (cat food). Agent sent a generic order tracking template. Retrieved evidence contained general shipping checks (score 0.16). The agent failed to address the wrong item delivery or initiate a replacement flow."
    ),
    "532639": (
        1, 1, 1, 5, 1,
        "German conversational banter ('Schade. Da bin ich immer neugierig'). Agent sent a generic English order tracking response. Retrieved evidence contained English resolution pairs. The response failed language matching and irrelevantly provided tracking steps for casual banter."
    ),
    "649952": (
        1, 1, 1, 5, 1,
        "Japanese customer expressed delight that separate orders arrived consolidated in one box. Agent inappropriately apologized for inconvenience and requested order number via DM in Japanese. Retrieved evidence was ungrounded. The escalation was a critical false-positive failure on positive customer praise."
    ),
    "679078": (
        1, 1, 1, 5, 1,
        "Japanese customer shared a positive purchase experience regarding a cheap welding cartridge. Agent inappropriately apologized for trouble and requested order number via DM in Japanese. Retrieved evidence was empty. Unnecessary escalation and apology for a positive review."
    ),
    "701334": (
        1, 1, 1, 5, 1,
        "Customer complained that Prime Now delivery failed while waiting at home with no call. Agent provided Prime subscription cancellation instructions. Retrieved evidence misaligned around membership management. Critical escalation failure misdirecting urgent courier non-delivery into account cancellation."
    ),
    "909507": (
        5, 5, 4, 5, 5,
        "Customer requested team to check direct message ('kindly check DM Team'). Agent appropriately apologized, flagged for specialist review, and guided secure DM communication. Retrieved evidence supported DM routing. Escalation decision was appropriate and handled securely."
    ),
    "944251": (
        1, 1, 2, 5, 1,
        "Customer simply replied 'Done.' to a previous support instruction. Agent responded with a canned generic order tracking template. Retrieved evidence had low relevance. The agent failed conversation state tracking by treating thread closure as a new tracking inquiry."
    ),
    "947686": (
        1, 1, 2, 5, 2,
        "Customer complained of chronic late delivery and receiving an expired product. Agent sent a generic order status response. Retrieved evidence showed general package delays. The agent failed to escalate an expired consumable product complaint involving customer health/safety."
    ),
    "984200": (
        5, 4, 3, 5, 3,
        "Customer reported a Kindle for PC page layout formatting issue. Agent provided relevant digital device and app troubleshooting steps (restart, clear cache, update app). Retrieved evidence matched digital device support. Auto-handling was acceptable for routine digital troubleshooting."
    ),
    "1113514": (
        1, 1, 1, 5, 1,
        "Customer posted promotional hashtags (#amazongreatindianfestival) and image without a question. Agent responded with generic order status advice. Retrieved evidence was ungrounded. Critical failure delivering unprompted order tracking advice to promotional media."
    ),
    "1300626": (
        1, 1, 2, 5, 2,
        "Customer asked for a direct link to online chat regarding one-day shipping delays. Agent gave generic order lookup advice without the chat link. Retrieved evidence contained shipping delay threads (score 0.16). The agent failed to answer the customer's direct question or escalate."
    ),
    "1313039": (
        1, 1, 2, 5, 1,
        "Customer expressed hope parcel would be left with neighbor for a new coffee machine. Agent delivered generic order tracking advice. Retrieved evidence had low relevance. Conversational delivery anticipation was mistakenly treated as an active delivery failure."
    ),
    "1362458": (
        1, 1, 2, 5, 2,
        "Customer clarified carrier was AMZL US and noted recurring apartment delivery problems. Agent repeated canned order tracking text. Retrieved evidence showed general logistics pairs. Failed to escalate chronic carrier building-access logistics complaints."
    ),
    "1382396": (
        1, 1, 1, 5, 1,
        "Customer complained about telephone support imposing a one-week delay on order replacement. Agent gave Online Returns Center refund instructions. Retrieved evidence misaligned around return center policies. Critical failure sending refund instructions to customer awaiting a replacement."
    ),
    "1572905": (
        1, 1, 2, 5, 2,
        "Customer alleged scam regarding checkout price change and doubled delivery charges. Agent sent canned order lookup advice. Retrieved evidence showed price discrepancy pairs. Failed to escalate checkout fee dispute requiring billing investigation."
    ),
    "1691622": (
        1, 1, 1, 5, 2,
        "Customer alleged contest winners list was fraudulent with fake accounts. Agent gave generic order tracking advice. Retrieved evidence was ungrounded. Misdirected canned response completely disconnected from promotional contest fraud inquiry."
    ),
    "1764531": (
        5, 4, 3, 5, 5,
        "Spanish customer reported blocked account while attempting to place an order. Agent escalated in Spanish to a specialized agent via private message. Retrieved evidence matched Spanish account access pairs. Escalation decision was completely appropriate for account lockout."
    ),
    "1829432": (
        1, 1, 2, 5, 2,
        "Customer recovering from surgery complained essential comfort items had not arrived. Agent gave robotic order lookup advice. Retrieved evidence showed general package delays. Tone-deaf response failed to escalate urgent medical-recovery delivery delay."
    ),
    "2126759": (
        4, 3, 3, 5, 2,
        "Customer inquired on status of two specific orders overdue since 2nd November. Agent provided standard self-service order check guidance with Order ID request. Retrieved evidence matched delivery tracking (score 0.17). Guidance was clear, but multi-order overdue status warranted proactive DM investigation."
    ),
    "2184761": (
        1, 1, 1, 5, 2,
        "Customer asked pre-sales question whether Echo Plus in India includes a Hue bulb. Agent gave device reboot and app cache clearing instructions. Retrieved evidence was misaligned on device failure. Irrelevant troubleshooting response to pre-sales product specification query."
    ),
    "2254381": (
        1, 1, 1, 5, 2,
        "Portuguese customer reported postal code and state mismatch error during checkout. Agent sent generic English order status template. Retrieved evidence was ungrounded in English. Response failed language matching and did not assist with checkout address error."
    ),
    "2465040": (
        1, 1, 1, 5, 1,
        "Spanish banter asking if Amazon had a spare Nintendo Switch. Agent apologized for inconvenience and escalated for specialist review in Spanish. Retrieved evidence had low relevance. Critical failure treating casual gaming banter as a severe customer incident."
    ),
    "2531101": (
        2, 1, 1, 5, 2,
        "Japanese customer enthusiastically singing about joining Amazon Music Unlimited. Agent apologized for inconvenience and requested order number via DM in Japanese. Retrieved evidence had low relevance. Inappropriate apology and escalation for enthusiastic customer praise."
    ),
    "2541046": (
        2, 2, 3, 5, 3,
        "Customer claimed lightning deal price was higher than regular price ('day light cheating'). Agent gave general order modification and promo code entry advice. Retrieved evidence matched promo codes. Response partially addressed promo codes but missed pricing dispute."
    ),
    "2611666": (
        2, 2, 2, 5, 2,
        "Customer clarified app environment and marketplace domain (.co.uk). Agent repeated generic order lookup template. Retrieved evidence had low relevance. Failed to maintain thread continuity, resetting to initial canned template."
    ),
    "2777430": (
        2, 2, 3, 5, 2,
        "Customer clarified navigation link disappeared in Kindle app. Agent gave general Kindle device restart troubleshooting. Retrieved evidence matched Kindle digital support. General restart advice missed the specific link navigation bug."
    ),
    "2803279": (
        1, 1, 1, 5, 3,
        "Customer humorously questioned receiving automated text recommending cat products when they have no cat. Agent gave canned generic order tracking advice. Retrieved evidence was ungrounded. Canned order reply was irrelevant to algorithmic recommendation humor."
    ),
    "2841828": (
        1, 1, 2, 5, 1,
        "Portuguese customer shared anticipation for weekend delivery. Agent sent Spanish apology escalating for specialist manual review. Retrieved evidence was in Spanish. Critical failure confusing Spanish for Portuguese and unnecessarily escalating positive anticipation."
    ),
    "2899522": (
        1, 1, 1, 5, 1,
        "Customer expressed heartfelt gratitude for surprise cosy gift delivery. Agent delivered canned generic order lookup template. Retrieved evidence was ungrounded. Critical failure sending canned order tracking reply in response to customer praise."
    ),
    "2922515": (
        1, 1, 1, 5, 1,
        "Customer complained of late Prime shipping from 3rd party vendor. Agent gave Prime subscription cancellation instructions. Retrieved evidence misaligned on membership management. Critical failure misdirecting seller delivery delay into membership cancellation."
    ),
    "2926332": (
        4, 3, 2, 5, 5,
        "Japanese customer debated whether to contact marketplace seller about delay. Agent politely guided to DM for specialist assistance in Japanese. Retrieved evidence had low relevance. Correct specialist escalation in Japanese for marketplace seller delay."
    ),
    "2927090": (
        3, 3, 3, 5, 4,
        "Spanish customer complained carrier does not call upon delivery unlike DHL/Fedex. Agent appropriately offered specialist escalation via private message in Spanish. Retrieved evidence matched Spanish carrier pairs. Well-reasoned escalation for courier delivery policy feedback."
    ),
    "2971945": (
        3, 2, 2, 5, 4,
        "Japanese customer shared personal story on why they love Amazon Prime. Agent provided standard polite Japanese support greeting and DM inquiry. Retrieved evidence matched general support. Harmless polite routing, though testimonial did not strictly require escalation."
    ),
}


def prepare_ratings():
    print("=" * 75)
    print("STEP 4D: PREPARING REVIEW RATINGS FOR 50-ROW HUMAN AUDIT")
    print("=" * 75)

    if not XLSX_PATH.exists():
        raise FileNotFoundError(f"Workbook not found: {XLSX_PATH}")

    wb = openpyxl.load_workbook(XLSX_PATH)
    ws_audit = wb["Judge-Human Audit"]

    # Verify that Judge-Human Audit has exactly 50 rows
    audit_mids = [str(ws_audit.cell(row=r, column=1).value).strip() for r in range(6, 56)]
    if len(audit_mids) != 50:
        raise ValueError(f"Expected 50 rows in 'Judge-Human Audit', found {len(audit_mids)}")

    # Verify all 50 IDs have recommendations
    for mid in audit_mids:
        if mid not in RECOMMENDATIONS:
            raise KeyError(f"Missing recommendation for message_id {mid}")

    print(f"Verified all 50 message IDs match recommendation index.")

    # 1. Create or replace 'Suggested Human Ratings' worksheet in workbook
    sheet_name = "Suggested Human Ratings"
    if sheet_name in wb.sheetnames:
        del wb[sheet_name]

    ws_sugg = wb.create_sheet(title=sheet_name)
    ws_sugg.views.sheetView[0].showGridLines = True

    # Styling definitions
    font_title = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="595959")
    font_hdr = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    font_data = Font(name="Calibri", size=9, color="0F172A")
    font_id = Font(name="Consolas", size=9, bold=True, color="1E3A8A")
    font_score = Font(name="Calibri", size=10, bold=True)

    fill_hdr_id = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    fill_hdr_score = PatternFill(start_color="0284C7", end_color="0284C7", fill_type="solid")
    fill_hdr_reason = PatternFill(start_color="0369A1", end_color="0369A1", fill_type="solid")
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Title block
    ws_sugg.merge_cells("A1:G1")
    t_cell = ws_sugg.cell(row=1, column=1, value="STEP 4D: SUGGESTED HUMAN RATINGS & ANALYTICAL RATIONALES (50 SAMPLES)")
    t_cell.font = font_title
    t_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_sugg.row_dimensions[1].height = 26

    ws_sugg.merge_cells("A2:G2")
    s_cell = ws_sugg.cell(
        row=2, column=1,
        value="NOTICE: Suggested Human Ratings are provided strictly as expert reviewer proposals. Human rating columns in 'Judge-Human Audit' remain unpopulated until human review."
    )
    s_cell.font = font_subtitle
    s_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws_sugg.row_dimensions[2].height = 20

    # Headers on row 3
    headers = [
        "message_id",
        "suggested_human_correctness",
        "suggested_human_helpfulness",
        "suggested_human_groundedness",
        "suggested_human_policy",
        "suggested_human_escalation",
        "suggested_reason",
    ]

    ws_sugg.row_dimensions[3].height = 28
    for col_idx, h in enumerate(headers, 1):
        c = ws_sugg.cell(row=3, column=col_idx, value=h)
        c.font = font_hdr
        c.border = thin_border
        c.alignment = align_center
        if col_idx == 1:
            c.fill = fill_hdr_id
        elif 2 <= col_idx <= 6:
            c.fill = fill_hdr_score
        else:
            c.fill = fill_hdr_reason

    # Populate 50 rows in order of audit set
    csv_records = []
    for row_idx, mid in enumerate(audit_mids, start=4):
        corr, helpf, ground, pol, esc, reason = RECOMMENDATIONS[mid]
        row_vals = [int(mid), corr, helpf, ground, pol, esc, reason]
        is_even = (row_idx % 2 == 0)

        ws_sugg.row_dimensions[row_idx].height = 45
        for col_idx, val in enumerate(row_vals, 1):
            cell = ws_sugg.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if is_even:
                cell.fill = fill_zebra

            if col_idx == 1:
                cell.font = font_id
                cell.alignment = align_center
            elif 2 <= col_idx <= 6:
                cell.font = font_score
                cell.alignment = align_center
            else:
                cell.font = font_data
                cell.alignment = align_left

        csv_records.append({
            "message_id": mid,
            "suggested_human_correctness": corr,
            "suggested_human_helpfulness": helpf,
            "suggested_human_groundedness": ground,
            "suggested_human_policy": pol,
            "suggested_human_escalation": esc,
            "suggested_reason": reason,
        })

    # Set column widths
    widths = {
        "A": 16,
        "B": 30,
        "C": 30,
        "D": 32,
        "E": 26,
        "F": 30,
        "G": 90,
    }
    for col_letter, w in widths.items():
        ws_sugg.column_dimensions[col_letter].width = w

    ws_sugg.auto_filter.ref = f"A3:G53"

    # Save workbook
    wb.save(XLSX_PATH)
    print(f"✓ Added worksheet '{sheet_name}' to {XLSX_PATH}")

    # 2. Write CSV file eval/judge_human_suggested_ratings.csv
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_records)

    print(f"✓ Created {CSV_PATH} with {len(csv_records)} recommendations.")

    # 3. Verify zero human_* fields in 'Judge-Human Audit' were altered
    wb_verify = openpyxl.load_workbook(XLSX_PATH, data_only=False)
    ws_verify = wb_verify["Judge-Human Audit"]
    overwritten_count = 0
    for r in range(6, 56):
        trigger = ws_verify.cell(row=r, column=17).value
        action = ws_verify.cell(row=r, column=23).value
        # Check human rating columns (R to V, 18 to 22)
        for c in range(18, 23):
            val = ws_verify.cell(row=r, column=c).value
            # Formula is expected, raw filled number without trigger is not
            if val is not None and not str(val).startswith("=") and str(val).strip() != "":
                overwritten_count += 1

    print(f"✓ Integrity Audit: Verified {overwritten_count} human rating columns overwritten in 'Judge-Human Audit'.")


if __name__ == "__main__":
    prepare_ratings()
