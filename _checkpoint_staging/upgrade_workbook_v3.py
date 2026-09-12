"""
Developer Job Application Tracker PRO v3.0
Premium Workbook Upgrade Script

Upgrades the existing workbook with:
- Executive Dashboard with KPI cards, progress widgets, and 13 charts
- Full Statistics & Analytics page with 25+ formulas
- Enhanced Applications sheet with 30+ columns and data validation
- Improved Interview Tracker, Recruiter CRM, Target Companies, Salary Comparison
- Enhanced Networking, Skill Gap, Offer Decision Matrix
- Premium UX/UI: professional palette, fonts, borders, freeze panes, filters
- Conditional formatting throughout
- No VBA — pure Excel formulas
"""

import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, NamedStyle, Color
)
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.formatting.rule import (
    CellIsRule, FormulaRule, ColorScaleRule, DataBarRule, IconSetRule
)
from openpyxl.chart import BarChart, PieChart, LineChart, DoughnutChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.table import Table, TableStyleInfo
import copy
import os

# ── Premium Color Palette ──────────────────────────────────────────────
COLORS = {
    # Primary
    "navy":       "1B2A4A",
    "blue":       "2E5BBA",
    "light_blue": "4A7FDB",
    "accent":     "00A3FF",
    # Neutrals
    "dark":       "1E2A38",
    "surface":    "F8F9FB",
    "surface2":   "EDF0F5",
    "surface3":   "DDE3EC",
    "white":      "FFFFFF",
    "gray":       "6B7B8D",
    "light_gray": "C4CCD7",
    "border":     "D0D7E2",
    # Status
    "green":      "22C55E",
    "green_bg":   "E8FBEF",
    "yellow":     "F59E0B",
    "yellow_bg":  "FEF7E6",
    "red":        "EF4444",
    "red_bg":     "FDEAEA",
    "purple":     "8B5CF6",
    "purple_bg":  "F3EEFE",
    "teal":       "14B8A6",
    "teal_bg":    "E6FAF7",
    # KPI card colors
    "kpi_blue":   "EFF6FF",
    "kpi_green":  "ECFDF5",
    "kpi_amber":  "FFFBEB",
    "kpi_red":    "FEF2F2",
    "kpi_purple": "F5F3FF",
    "kpi_teal":   "F0FDFA",
}

# ── Font presets ───────────────────────────────────────────────────────
def font(size=10, bold=False, color="1E2A38", name="Segoe UI"):
    return Font(name=name, size=size, bold=bold, color=color)

# ── Fill presets ───────────────────────────────────────────────────────
def fill(color):
    return PatternFill(start_color=color, end_color=color, fill_type="solid")

# ── Border presets ─────────────────────────────────────────────────────
thin_border = Border(
    left=Side(style="thin", color="D0D7E2"),
    right=Side(style="thin", color="D0D7E2"),
    top=Side(style="thin", color="D0D7E2"),
    bottom=Side(style="thin", color="D0D7E2"),
)

bottom_border = Border(bottom=Side(style="medium", color="2E5BBA"))

card_border = Border(
    left=Side(style="thin", color="C4CCD7"),
    right=Side(style="thin", color="C4CCD7"),
    top=Side(style="thin", color="C4CCD7"),
    bottom=Side(style="thin", color="C4CCD7"),
)

# ── Alignment presets ──────────────────────────────────────────────────
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
right = Alignment(horizontal="right", vertical="center")

# ── Constants ──────────────────────────────────────────────────────────
APP_SHEET = "Applications"
APP_RANGE = "Applications!A2:AF500"
MAX_ROW = 500

# Data validation lists
DV_STATUS = '"Applied,Screening,Phone Screen,Technical Interview,HR Interview,Final Interview,Offer,Accepted,Rejected,Ghosted,Withdrawn"'
DV_PRIORITY = '"Low,Medium,High,Critical"'
DV_REMOTE = '"Remote,Hybrid,Onsite,Flexible"'
DV_SOURCE = '"LinkedIn,Indeed,AngelList,Glassdoor,Company Website,Referral,Recruiter,Job Fair,Other"'
DV_YESNO = '"Yes,No"'
DV_LEVEL = '"Beginner,Intermediate,Advanced,Expert"'
DV_INTERVIEW_STAGE = '"Phone Screen,HR Interview,Technical Interview,System Design,Behavioral,Final Interview,Take-Home,Onsite"'
DV_RESULT = '"Pending,Passed,Failed,Cancelled,Rescheduled"'
DV_RATING = '"1,2,3,4,5"'
DV_EMP_TYPE = '"Full-time,Part-time,Contract,Internship,Freelance"'
DV_RELATIONSHIP = '"Cold Connection,Warm Connection,Mutual Contact,Mentor,Referral Source"'
DV_HIRING = '"Not Hiring,Researching,Applied,Interviewing,Offer,Rejected"'
DV_COMPANY_SIZE = '"Startup (1-50),Small (51-200),Medium (201-1000),Large (1001-5000),Enterprise (5000+)"'


def apply_header_style(ws, row=1, max_col=None):
    """Apply premium header styling to a row."""
    if max_col is None:
        max_col = ws.max_column
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = font(10, bold=True, color="FFFFFF")
        cell.fill = fill(COLORS["navy"])
        cell.alignment = center
        cell.border = thin_border
    ws.row_dimensions[row].height = 28


def apply_data_row_style(ws, row, max_col, alternate=False):
    """Apply data row styling with optional alternating color."""
    bg = COLORS["surface2"] if alternate else COLORS["white"]
    for col in range(1, max_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = font(10, color="1E2A38")
        cell.fill = fill(bg)
        cell.alignment = left
        cell.border = thin_border
    ws.row_dimensions[row].height = 22


def set_col_widths(ws, widths):
    """Set column widths from a dict {col_letter: width}."""
    for col_letter, width in widths.items():
        ws.column_dimensions[col_letter].width = width


def add_dv(ws, formula, col_letter, start_row=2, end_row=500):
    """Add data validation to a column range."""
    dv = DataValidation(type="list", formula1=formula, allow_blank=True)
    dv.error = "Please select a value from the dropdown"
    dv.errorTitle = "Invalid Entry"
    dv.prompt = "Select from dropdown"
    dv.promptTitle = "Choose"
    ws.add_data_validation(dv)
    dv.add(f"{col_letter}{start_row}:{col_letter}{end_row}")


def kpi_card(ws, row, col, label, formula, value_color="2E5BBA", bg="EFF6FF"):
    """Create a KPI card at the given position (2 cols wide, 2 rows tall)."""
    # Label cell
    lbl_cell = ws.cell(row=row, column=col, value=label)
    lbl_cell.font = font(9, bold=True, color="6B7B8D")
    lbl_cell.fill = fill(bg)
    lbl_cell.alignment = Alignment(horizontal="center", vertical="center")
    lbl_cell.border = Border(
        top=Side(style="thin", color="C4CCD7"),
        left=Side(style="thin", color="C4CCD7"),
        right=Side(style="thin", color="C4CCD7"),
    )

    # Merge label across 2 cols
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col + 1)

    # Value cell
    val_cell = ws.cell(row=row + 1, column=col, value=formula)
    val_cell.font = font(22, bold=True, color=value_color)
    val_cell.fill = fill(bg)
    val_cell.alignment = Alignment(horizontal="center", vertical="center")
    val_cell.border = Border(
        bottom=Side(style="thin", color="C4CCD7"),
        left=Side(style="thin", color="C4CCD7"),
        right=Side(style="thin", color="C4CCD7"),
    )
    val_cell.number_format = "0"

    # Merge value across 2 cols
    ws.merge_cells(start_row=row + 1, start_column=col, end_row=row + 1, end_column=col + 1)

    ws.row_dimensions[row].height = 20
    ws.row_dimensions[row + 1].height = 40


def progress_widget(ws, row, col, label, formula, target_formula, bg="EFF6FF"):
    """Create a progress widget: label, value/target, and percentage."""
    lbl_cell = ws.cell(row=row, column=col, value=label)
    lbl_cell.font = font(9, bold=True, color="6B7B8D")
    lbl_cell.fill = fill(bg)
    lbl_cell.alignment = left
    lbl_cell.border = Border(
        top=Side(style="thin", color="C4CCD7"),
        left=Side(style="thin", color="C4CCD7"),
        right=Side(style="thin", color="C4CCD7"),
    )

    val_cell = ws.cell(row=row + 1, column=col, value=formula)
    val_cell.font = font(16, bold=True, color="2E5BBA")
    val_cell.fill = fill(bg)
    val_cell.alignment = left
    val_cell.border = Border(
        bottom=Side(style="thin", color="C4CCD7"),
        left=Side(style="thin", color="C4CCD7"),
        right=Side(style="thin", color="C4CCD7"),
    )

    target_cell = ws.cell(row=row + 1, column=col + 1, value=target_formula)
    target_cell.font = font(10, color="6B7B8D")
    target_cell.fill = fill(bg)
    target_cell.alignment = right
    target_cell.border = Border(
        bottom=Side(style="thin", color="C4CCD7"),
        right=Side(style="thin", color="C4CCD7"),
    )

    ws.row_dimensions[row].height = 20
    ws.row_dimensions[row + 1].height = 32


# ────────────────────────────────────────────────────────────────────────
# MAIN UPGRADE FUNCTION
# ────────────────────────────────────────────────────────────────────────
def upgrade_workbook(filepath):
    print("Loading workbook...")
    wb = openpyxl.load_workbook(filepath, data_only=False)

    # ===================================================================
    # 1. UPGRADE APPLICATIONS SHEET
    # ===================================================================
    print("Upgrading Applications sheet...")
    ws = wb["Applications"]

    # Define new column layout (30+ columns)
    app_headers = [
        "Application ID", "Company", "Role", "Location", "Country", "Remote",
        "Salary", "Source", "Date Applied", "Status", "Priority", "Fit Score",
        "Follow-up Date", "Recruiter", "LinkedIn Recruiter", "Interview Date",
        "Offer", "Application URL", "Company Career Page", "Resume Version",
        "Cover Letter Version", "Visa Sponsorship", "Employment Type",
        "Work Authorization", "Referral", "Expected Salary", "Current Stage",
        "Days Since Applied", "Days Until Follow-up", "Interview Count",
        "Favorite", "Archive", "Notes"
    ]

    # Write headers
    for i, h in enumerate(app_headers, 1):
        ws.cell(row=1, column=i, value=h)

    apply_header_style(ws, row=1, max_col=len(app_headers))

    # Move existing data to new column positions
    # Old: Company(A), Role(B), Location(C), Remote(D), Salary(E), Source(F),
    #      Date Applied(G), Status(H), Priority(I), Fit Score(J), Follow-up(K),
    #      Recruiter(L), Interview Date(M), Offer(N), Notes(O)
    # New: Application ID(A), Company(B), Role(C), Location(D), Country(E), Remote(F),
    #      Salary(G), Source(H), Date Applied(I), Status(J), Priority(K), Fit Score(L),
    #      Follow-up(M), Recruiter(N), LinkedIn Recruiter(O), Interview Date(P),
    #      Offer(Q), Application URL(R), Career Page(S), Resume Ver(T), Cover Letter Ver(U),
    #      Visa(V), Employment Type(W), Work Auth(X), Referral(Y), Expected Salary(Z),
    #      Current Stage(AA), Days Since(AB), Days Until Follow-up(AC), Interview Count(AD),
    #      Favorite(AE), Archive(AF), Notes(AG)

    # We need to read existing data first, then reorganize
    existing_data = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            existing_data.append(row_data)

    # Clear all data rows
    for row in range(2, ws.max_row + 1):
        for col in range(1, 20):
            ws.cell(row=row, column=col).value = None

    # Map old columns to new positions
    # Old col -> New col
    col_map = {
        1: 2,   # Company -> B
        2: 3,   # Role -> C
        3: 4,   # Location -> D
        4: 6,   # Remote -> F
        5: 7,   # Salary -> G
        6: 8,   # Source -> H
        7: 9,   # Date Applied -> I
        8: 10,  # Status -> J
        9: 11,  # Priority -> K
        10: 12, # Fit Score -> L
        11: 13, # Follow-up -> M
        12: 14, # Recruiter -> N
        13: 16, # Interview Date -> P
        14: 17, # Offer -> Q
        15: 33, # Notes -> AG
    }

    for row_idx, row_data in enumerate(existing_data, 2):
        for old_col, new_col in col_map.items():
            if old_col in row_data:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    # Add formulas for new computed columns
    data_end = max(len(existing_data) + 1, 500)
    for r in range(2, data_end + 1):
        # Application ID (A) = "APP-" + row number
        ws.cell(row=r, column=1, value=f'="APP-"&TEXT(ROW()-1,"000")')
        # Days Since Applied (AB) = TODAY() - Date Applied
        ws.cell(row=r, column=28, value=f'=IF(I{r}="","",TODAY()-I{r})')
        # Days Until Follow-up (AC) = Follow-up Date - TODAY()
        ws.cell(row=r, column=29, value=f'=IF(M{r}="","",M{r}-TODAY())')
        # Interview Count (AD) = COUNTIFS on Interview Tracker
        ws.cell(row=r, column=30, value=f'=IF(B{r}="","",COUNTIFS(\'Interview Tracker\'!A:A,B{r}))')

    # Column widths
    app_widths = {
        "A": 14, "B": 20, "C": 25, "D": 18, "E": 14, "F": 10,
        "G": 12, "H": 14, "I": 14, "J": 16, "K": 10, "L": 10,
        "M": 14, "N": 18, "O": 18, "P": 14, "Q": 10, "R": 28,
        "S": 28, "T": 14, "U": 14, "V": 12, "W": 14, "X": 14,
        "Y": 14, "Z": 14, "AA": 16, "AB": 14, "AC": 16, "AD": 12,
        "AE": 8, "AF": 8, "AG": 30,
    }
    set_col_widths(ws, app_widths)

    # Data validations
    add_dv(ws, DV_STATUS, "J")       # Status
    add_dv(ws, DV_PRIORITY, "K")     # Priority
    add_dv(ws, DV_REMOTE, "F")       # Remote
    add_dv(ws, DV_SOURCE, "H")       # Source
    add_dv(ws, DV_YESNO, "Q")        # Offer
    add_dv(ws, DV_YESNO, "V")        # Visa Sponsorship
    add_dv(ws, DV_EMP_TYPE, "W")     # Employment Type
    add_dv(ws, DV_YESNO, "X")        # Work Authorization
    add_dv(ws, DV_YESNO, "AE")       # Favorite
    add_dv(ws, DV_YESNO, "AF")       # Archive

    # Conditional formatting on Status column (J)
    status_colors = [
        ("Applied", COLORS["kpi_blue"], "1E40AF"),
        ("Screening", COLORS["kpi_purple"], "6B21A8"),
        ("Phone Screen", COLORS["kpi_purple"], "6B21A8"),
        ("Technical Interview", COLORS["yellow_bg"], "92400E"),
        ("HR Interview", COLORS["yellow_bg"], "92400E"),
        ("Final Interview", COLORS["yellow_bg"], "92400E"),
        ("Offer", COLORS["green_bg"], "166534"),
        ("Accepted", COLORS["green_bg"], "166534"),
        ("Rejected", COLORS["red_bg"], "991B1B"),
        ("Ghosted", COLORS["surface2"], "6B7B8D"),
        ("Withdrawn", COLORS["surface2"], "6B7B8D"),
    ]
    for status, bg, fg in status_colors:
        ws.conditional_formatting.add(
            f"J2:J500",
            CellIsRule(
                operator="equal",
                formula=[f'"{status}"'],
                fill=fill(bg),
                font=Font(name="Segoe UI", size=10, bold=True, color=fg),
            ),
        )

    # Conditional formatting on Priority (K)
    for priority, bg, fg in [
        ("Critical", COLORS["red_bg"], "991B1B"),
        ("High", COLORS["yellow_bg"], "92400E"),
        ("Medium", COLORS["kpi_blue"], "1E40AF"),
        ("Low", COLORS["surface2"], "6B7B8D"),
    ]:
        ws.conditional_formatting.add(
            "K2:K500",
            CellIsRule(
                operator="equal",
                formula=[f'"{priority}"'],
                fill=fill(bg),
                font=Font(name="Segoe UI", size=10, bold=True, color=fg),
            ),
        )

    # Data bar on Fit Score (L)
    ws.conditional_formatting.add(
        "L2:L500",
        DataBarRule(
            start_type="num", start_value=0,
            end_type="num", end_value=100,
            color="4A7FDB",
        ),
    )

    # Conditional formatting on Days Until Follow-up (AC) - red if overdue
    ws.conditional_formatting.add(
        "AC2:AC500",
        CellIsRule(
            operator="lessThan",
            formula=["0"],
            fill=fill(COLORS["red_bg"]),
            font=Font(name="Segoe UI", size=10, bold=True, color="991B1B"),
        ),
    )

    # Freeze panes and auto-filter
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(app_headers))}500"

    # Apply alternating row colors
    for r in range(2, 501):
        apply_data_row_style(ws, r, len(app_headers), alternate=(r % 2 == 0))

    print(f"  Applications: {len(app_headers)} columns, DV, CF, freeze, filter applied")

    # ===================================================================
    # 2. UPGRADE INTERVIEW TRACKER
    # ===================================================================
    print("Upgrading Interview Tracker...")
    ws = wb["Interview Tracker"]

    iv_headers = [
        "Company", "Role", "Interview Stage", "Interviewer", "Interview Date",
        "Interview Number", "Duration (min)", "Preparation Status", "Confidence Score",
        "Difficulty", "Result", "Technical Topics", "Coding Questions",
        "Behavioral Questions", "Next Step", "Notes", "Lessons Learned"
    ]

    # Read existing data
    iv_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            iv_existing.append(row_data)

    # Write new headers
    for i, h in enumerate(iv_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(iv_headers))

    # Map old data: Company(A->A), Role(B->B), Stage(C->C), Interviewer(D->D),
    # Date(E->E), Prep Notes(F->P), Result(G->K), Rating(H->removed), Lessons(I->Q)
    iv_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 16, 7: 11, 9: 17}

    for row_idx, row_data in enumerate(iv_existing, 2):
        for old_col, new_col in iv_col_map.items():
            if old_col in row_data:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    # Add formulas
    for r in range(2, 501):
        # Interview Number (F) = COUNTIFS up to current row
        ws.cell(row=r, column=6, value=f'=IF(A{r}="","",COUNTIFS($A$2:A{r},A{r}))')

    # Column widths
    iv_widths = {
        "A": 20, "B": 25, "C": 18, "D": 18, "E": 14, "F": 12,
        "G": 12, "H": 16, "I": 12, "J": 12, "K": 12, "L": 25,
        "M": 25, "N": 25, "O": 20, "P": 30, "Q": 30,
    }
    set_col_widths(ws, iv_widths)

    # Data validations
    add_dv(ws, DV_INTERVIEW_STAGE, "C")
    add_dv(ws, DV_RESULT, "K")
    add_dv(ws, '"Not Started,In Progress,Completed"', "H")  # Prep Status
    add_dv(ws, '"Easy,Medium,Hard"', "J")  # Difficulty
    add_dv(ws, DV_RATING, "I")  # Confidence Score

    # Conditional formatting on Result
    for result, bg, fg in [
        ("Passed", COLORS["green_bg"], "166534"),
        ("Failed", COLORS["red_bg"], "991B1B"),
        ("Pending", COLORS["kpi_blue"], "1E40AF"),
        ("Cancelled", COLORS["surface2"], "6B7B8D"),
        ("Rescheduled", COLORS["yellow_bg"], "92400E"),
    ]:
        ws.conditional_formatting.add(
            "K2:K500",
            CellIsRule(operator="equal", formula=[f'"{result}"'],
                       fill=fill(bg), font=Font(name="Segoe UI", size=10, bold=True, color=fg)),
        )

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(iv_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(iv_headers), alternate=(r % 2 == 0))

    print(f"  Interview Tracker: {len(iv_headers)} columns, DV, CF, freeze, filter applied")

    # ===================================================================
    # 3. UPGRADE RECRUITER CRM
    # ===================================================================
    print("Upgrading Recruiter CRM...")
    ws = wb["Recruiter CRM"]

    crm_headers = [
        "Recruiter Name", "Company", "Email", "LinkedIn", "Position",
        "Last Contact", "Last Reply", "Avg Response Time (days)",
        "Next Follow-up", "Relationship Status", "Company Rating",
        "Priority", "Reminder Status", "Next Action", "Notes"
    ]

    # Read existing
    crm_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            crm_existing.append(row_data)

    for i, h in enumerate(crm_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(crm_headers))

    # Map: Name(A->A), Company(B->B), Email(C->C), LinkedIn(D->D), Position(E->E),
    # Last Contact(F->F), Next Follow-up(G->I), Score(H->L), Notes(I->O)
    crm_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 9, 8: 15, 9: 15}
    for row_idx, row_data in enumerate(crm_existing, 2):
        for old_col, new_col in crm_col_map.items():
            if old_col in row_data and row_data[old_col] is not None:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    crm_widths = {
        "A": 20, "B": 20, "C": 25, "D": 28, "E": 20, "F": 14,
        "G": 14, "H": 16, "I": 14, "J": 18, "K": 12, "L": 10,
        "M": 14, "N": 20, "O": 30,
    }
    set_col_widths(ws, crm_widths)

    add_dv(ws, '"Cold,Warm,Hot,Inactive"', "J")  # Relationship Status
    add_dv(ws, DV_RATING, "K")  # Company Rating
    add_dv(ws, DV_PRIORITY, "L")  # Priority
    add_dv(ws, '"None,Sent,Overdue,Completed"', "M")  # Reminder Status

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(crm_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(crm_headers), alternate=(r % 2 == 0))

    print(f"  Recruiter CRM: {len(crm_headers)} columns, DV, freeze, filter applied")

    # ===================================================================
    # 4. UPGRADE TARGET COMPANIES
    # ===================================================================
    print("Upgrading Target Companies...")
    ws = wb["Target Companies"]

    tc_headers = [
        "Company", "Industry", "Location", "Remote", "Size", "Website",
        "Career Page", "Status", "Priority", "Hiring Status", "Visa Sponsor",
        "Remote Friendly", "Tech Stack", "Glassdoor Rating",
        "LinkedIn Followers", "Company Size Category", "Dream Company",
        "Priority Score", "Notes"
    ]

    tc_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            tc_existing.append(row_data)

    for i, h in enumerate(tc_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(tc_headers))

    tc_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 8, 8: 9, 9: 19}
    for row_idx, row_data in enumerate(tc_existing, 2):
        for old_col, new_col in tc_col_map.items():
            if old_col in row_data:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    tc_widths = {
        "A": 20, "B": 16, "C": 18, "D": 10, "E": 12, "F": 22,
        "G": 22, "H": 14, "I": 10, "J": 14, "K": 10, "L": 12,
        "M": 20, "N": 12, "O": 14, "P": 18, "Q": 10, "R": 10, "S": 30,
    }
    set_col_widths(ws, tc_widths)

    add_dv(ws, DV_HIRING, "J")  # Hiring Status
    add_dv(ws, DV_PRIORITY, "I")  # Priority
    add_dv(ws, DV_YESNO, "K")  # Visa Sponsor
    add_dv(ws, DV_YESNO, "L")  # Remote Friendly
    add_dv(ws, DV_YESNO, "Q")  # Dream Company
    add_dv(ws, DV_COMPANY_SIZE, "P")  # Company Size Category

    # Priority Score formula = IF Dream Company +5, High +3, Medium +2, Low +1
    for r in range(2, 501):
        ws.cell(row=r, column=18, value=f'=IF(A{r}="","",IF(Q{r}="Yes",5,0)+IF(I{r}="Critical",4,IF(I{r}="High",3,IF(I{r}="Medium",2,IF(I{r}="Low",1,0)))))')

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(tc_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(tc_headers), alternate=(r % 2 == 0))

    print(f"  Target Companies: {len(tc_headers)} columns, DV, freeze, filter applied")

    # ===================================================================
    # 5. UPGRADE SALARY COMPARISON
    # ===================================================================
    print("Upgrading Salary Comparison...")
    ws = wb["Salary Comparison"]

    sc_headers = [
        "Company", "Base Salary", "Bonus", "Equity", "Benefits Value",
        "PTO Days", "Remote", "Visa Sponsorship", "Signing Bonus",
        "Relocation Bonus", "Annual Compensation", "Monthly Income",
        "Hourly Rate", "Total Compensation", "Estimated Tax (25%)",
        "Net Salary", "Decision Score", "Weighted Score", "Offer Ranking"
    ]

    sc_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            sc_existing.append(row_data)

    for i, h in enumerate(sc_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(sc_headers))

    # Map old data
    sc_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8}
    for row_idx, row_data in enumerate(sc_existing, 2):
        for old_col, new_col in sc_col_map.items():
            if old_col in row_data:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    # Add formulas
    for r in range(2, 501):
        # Annual Compensation (K) = Base + Bonus
        ws.cell(row=r, column=11, value=f'=IF(A{r}="","",B{r}+C{r})')
        # Monthly Income (L) = Annual / 12
        ws.cell(row=r, column=12, value=f'=IF(A{r}="","",K{r}/12)')
        # Hourly Rate (M) = Annual / 2080
        ws.cell(row=r, column=13, value=f'=IF(A{r}="","",K{r}/2080)')
        # Total Compensation (N) = Base + Bonus + Equity + Benefits + Signing + Relocation
        ws.cell(row=r, column=14, value=f'=IF(A{r}="","",B{r}+C{r}+D{r}+E{r}+I{r}+J{r})')
        # Estimated Tax (O) = Total * 25%
        ws.cell(row=r, column=15, value=f'=IF(A{r}="","",N{r}*0.25)')
        # Net Salary (P) = Total - Tax
        ws.cell(row=r, column=16, value=f'=IF(A{r}="","",N{r}-O{r})')
        # Decision Score (Q) = weighted: Base 40% + Bonus 10% + Equity 10% + Benefits 10% + Remote 10% + PTO 10% + Visa 10%
        ws.cell(row=r, column=17, value=f'=IF(A{r}="","",ROUND(B{r}*0.4+C{r}*0.1+D{r}*0.1+E{r}*0.1+IF(G{r}="Yes",5000,0)*0.1+F{r}*500*0.1+IF(H{r}="Yes",5000,0)*0.1,0))')
        # Weighted Score (R) = Decision Score / 1000 (normalized)
        ws.cell(row=r, column=18, value=f'=IF(A{r}="","",ROUND(Q{r}/1000,1))')
        # Offer Ranking (S) = RANK of Weighted Score
        ws.cell(row=r, column=19, value=f'=IF(A{r}="","",RANK(R{r},$R$2:$R$500,0))')

    sc_widths = {
        "A": 20, "B": 14, "C": 12, "D": 12, "E": 14, "F": 10,
        "G": 10, "H": 12, "I": 12, "J": 14, "K": 16, "L": 14,
        "M": 12, "N": 16, "O": 14, "P": 14, "Q": 14, "R": 12, "S": 12,
    }
    set_col_widths(ws, sc_widths)

    add_dv(ws, DV_YESNO, "G")   # Remote
    add_dv(ws, DV_YESNO, "H")   # Visa

    # Conditional formatting on Offer Ranking - highlight #1
    ws.conditional_formatting.add(
        "S2:S500",
        CellIsRule(operator="equal", formula=["1"],
                   fill=fill(COLORS["green_bg"]),
                   font=Font(name="Segoe UI", size=10, bold=True, color="166534")),
    )

    # Currency format
    for col in ["B", "C", "D", "E", "I", "J", "K", "L", "M", "N", "O", "P", "Q"]:
        for r in range(2, 501):
            ws.cell(row=r, column=openpyxl.utils.column_index_from_string(col)).number_format = '$#,##0'

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(sc_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(sc_headers), alternate=(r % 2 == 0))

    print(f"  Salary Comparison: {len(sc_headers)} columns, formulas, DV, freeze, filter applied")

    # ===================================================================
    # 6. UPGRADE NETWORKING TRACKER
    # ===================================================================
    print("Upgrading Networking Tracker...")
    ws = wb["Networking Tracker"]

    nt_headers = [
        "Contact Name", "Company", "LinkedIn", "Email", "Connection Date",
        "Connection Type", "Platform", "Relationship Type", "Last Contact",
        "Next Follow-up", "Follow-up Status", "Meeting Scheduled",
        "Coffee Chat", "Referral Requested", "Referral Received",
        "Priority", "Network Score", "Relationship Score", "Notes"
    ]

    nt_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            nt_existing.append(row_data)

    for i, h in enumerate(nt_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(nt_headers))

    nt_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 8, 7: 9, 8: 10, 9: 17, 10: 19, 11: 19, 12: 19, 13: 19}
    for row_idx, row_data in enumerate(nt_existing, 2):
        for old_col, new_col in nt_col_map.items():
            if old_col in row_data and row_data[old_col] is not None:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    nt_widths = {
        "A": 20, "B": 20, "C": 28, "D": 25, "E": 14, "F": 16,
        "G": 14, "H": 18, "I": 14, "J": 14, "K": 14, "L": 14,
        "M": 10, "N": 14, "O": 14, "P": 10, "Q": 10, "R": 10, "S": 30,
    }
    set_col_widths(ws, nt_widths)

    add_dv(ws, '"LinkedIn,Twitter,GitHub,Discord,Slack,Meetup,Conference,Other"', "G")  # Platform
    add_dv(ws, DV_RELATIONSHIP, "H")  # Relationship Type
    add_dv(ws, '"None,Due,Overdue,Completed"', "K")  # Follow-up Status
    add_dv(ws, DV_YESNO, "L")  # Meeting Scheduled
    add_dv(ws, DV_YESNO, "M")  # Coffee Chat
    add_dv(ws, DV_YESNO, "N")  # Referral Requested
    add_dv(ws, DV_YESNO, "O")  # Referral Received
    add_dv(ws, DV_PRIORITY, "P")  # Priority
    add_dv(ws, DV_RATING, "R")  # Relationship Score

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(nt_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(nt_headers), alternate=(r % 2 == 0))

    print(f"  Networking Tracker: {len(nt_headers)} columns, DV, freeze, filter applied")

    # ===================================================================
    # 7. UPGRADE SKILL GAP ANALYSIS
    # ===================================================================
    print("Upgrading Skill Gap Analysis...")
    ws = wb["Skill Gap Analysis"]

    sg_headers = [
        "Skill Category", "Skill Name", "Current Level", "Target Level",
        "Gap", "Gap Level", "Learning Resource", "Priority", "Status",
        "Difficulty", "Start Date", "Target Date", "Estimated Hours",
        "Hours Invested", "Estimated Completion", "Progress %",
        "Progress Bar", "Notes"
    ]

    sg_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            sg_existing.append(row_data)

    for i, h in enumerate(sg_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(sg_headers))

    sg_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 7, 7: 8, 8: 9, 9: 13, 10: 14, 11: 16, 12: 17, 13: 18}
    for row_idx, row_data in enumerate(sg_existing, 2):
        for old_col, new_col in sg_col_map.items():
            if old_col in row_data and row_data[old_col] is not None:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    # Add formulas
    level_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3, "Expert": 4}
    for r in range(2, 501):
        # Gap Level (F) = numeric gap
        ws.cell(row=r, column=6, value=f'=IF(C{r}="","",IF(D{r}="","",IF(C{r}="Beginner",1,IF(C{r}="Intermediate",2,IF(C{r}="Advanced",3,4)))-IF(D{r}="Beginner",1,IF(D{r}="Intermediate",2,IF(D{r}="Advanced",3,4)))))')
        # Progress % (P) = Hours Invested / Estimated Hours
        ws.cell(row=r, column=16, value=f'=IF(N{r}="","",IF(M{r}=0,0,MIN(N{r}/M{r},1)))')
        ws.cell(row=r, column=16).number_format = '0%'
        # Progress Bar (Q) = REPT("█", Progress * 20)
        ws.cell(row=r, column=17, value=f'=IF(P{r}="","",REPT("\u2588",ROUND(P{r}*20,0))&REPT("\u2591",20-ROUND(P{r}*20,0)))')

    sg_widths = {
        "A": 16, "B": 18, "C": 14, "D": 14, "E": 10, "F": 10,
        "G": 25, "H": 10, "I": 14, "J": 12, "K": 14, "L": 14,
        "M": 14, "N": 14, "O": 16, "P": 10, "Q": 24, "R": 30,
    }
    set_col_widths(ws, sg_widths)

    add_dv(ws, DV_LEVEL, "C")  # Current Level
    add_dv(ws, DV_LEVEL, "D")  # Target Level
    add_dv(ws, DV_PRIORITY, "H")  # Priority
    add_dv(ws, '"Not Started,In Progress,Completed,On Hold"', "I")  # Status
    add_dv(ws, '"Easy,Medium,Hard"', "J")  # Difficulty

    # Data bar on Progress %
    ws.conditional_formatting.add(
        "P2:P500",
        DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color="22C55E"),
    )

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(sg_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(sg_headers), alternate=(r % 2 == 0))

    print(f"  Skill Gap Analysis: {len(sg_headers)} columns, formulas, progress bars, DV, freeze, filter applied")

    # ===================================================================
    # 8. UPGRADE OFFER DECISION MATRIX
    # ===================================================================
    print("Upgrading Offer Decision Matrix...")
    ws = wb["Offer Decision Matrix"]

    odm_headers = [
        "Company", "Base Salary", "Bonus", "Equity", "Benefits Value",
        "Remote Flexibility", "Visa Sponsorship", "Career Growth",
        "Manager Quality", "Engineering Culture", "Tech Stack",
        "Learning Potential", "Work-Life Balance", "Location",
        "Promotion Opportunities", "Company Stability",
        "PTO Days", "Weighted Score", "Rank"
    ]

    odm_existing = []
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=False):
        row_data = {}
        for cell in row:
            if cell.value is not None:
                row_data[cell.column] = cell.value
        if row_data:
            odm_existing.append(row_data)

    for i, h in enumerate(odm_headers, 1):
        ws.cell(row=1, column=i, value=h)
    apply_header_style(ws, row=1, max_col=len(odm_headers))

    # Map old data
    odm_col_map = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 13, 9: 8, 10: 9, 11: 10, 12: 11, 13: 14, 14: 15, 15: 16, 16: 17}
    for row_idx, row_data in enumerate(odm_existing, 2):
        for old_col, new_col in odm_col_map.items():
            if old_col in row_data and row_data[old_col] is not None:
                ws.cell(row=row_idx, column=new_col, value=row_data[old_col])

    # Add weighted score formula
    # Weights: Salary 25%, Bonus 5%, Equity 5%, Benefits 5%, Remote 10%, Visa 5%,
    #          Career Growth 10%, Manager 10%, Culture 5%, Tech Stack 5%,
    #          Learning 5%, WLB 5%, Location 3%, Promotion 2%, Stability 5%
    # Score columns are 1-10 scale (H-R), Salary/Bonus/Equity are numeric
    for r in range(2, 501):
        ws.cell(row=r, column=18, value=(
            f'=IF(A{r}="","",ROUND('
            f'B{r}/10000*0.25+'  # Salary weight
            f'C{r}/10000*0.05+'  # Bonus weight
            f'D{r}/10000*0.05+'  # Equity weight
            f'E{r}/10000*0.05+'  # Benefits weight
            f'IF(F{r}="Yes",10,IF(F{r}="No",0,5))*0.10+'  # Remote
            f'IF(G{r}="Yes",10,IF(G{r}="No",0,5))*0.05+'  # Visa
            f'H{r}*0.10+'  # Career Growth
            f'I{r}*0.10+'  # Manager Quality
            f'J{r}*0.05+'  # Engineering Culture
            f'K{r}*0.05+'  # Tech Stack
            f'L{r}*0.05+'  # Learning Potential
            f'M{r}*0.05+'  # Work-Life Balance
            f'N{r}*0.03+'  # Location
            f'O{r}*0.02+'  # Promotion Opportunities
            f'P{r}*0.05'   # Company Stability
            f',1))'
        ))
        ws.cell(row=r, column=19, value=f'=IF(A{r}="","",RANK(R{r},$R$2:$R$500,0))')

    odm_widths = {
        "A": 20, "B": 14, "C": 12, "D": 12, "E": 14, "F": 12,
        "G": 12, "H": 12, "I": 12, "J": 12, "K": 12, "L": 12,
        "M": 12, "N": 12, "O": 12, "P": 12, "Q": 10, "R": 12, "S": 8,
    }
    set_col_widths(ws, odm_widths)

    add_dv(ws, DV_YESNO, "F")  # Remote Flexibility
    add_dv(ws, DV_YESNO, "G")  # Visa Sponsorship
    for col in ["H", "I", "J", "K", "L", "M", "N", "O", "P"]:
        add_dv(ws, '"1,2,3,4,5,6,7,8,9,10"', col)

    # Conditional formatting on Rank - highlight #1
    ws.conditional_formatting.add(
        "S2:S500",
        CellIsRule(operator="equal", formula=["1"],
                   fill=fill(COLORS["green_bg"]),
                   font=Font(name="Segoe UI", size=10, bold=True, color="166534")),
    )

    # Data bar on Weighted Score
    ws.conditional_formatting.add(
        "R2:R500",
        DataBarRule(start_type="num", start_value=0, end_type="num", end_value=100, color="4A7FDB"),
    )

    for col in ["B", "C", "D", "E"]:
        for r in range(2, 501):
            ws.cell(row=r, column=openpyxl.utils.column_index_from_string(col)).number_format = '$#,##0'

    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(odm_headers))}500"

    for r in range(2, 501):
        apply_data_row_style(ws, r, len(odm_headers), alternate=(r % 2 == 0))

    print(f"  Offer Decision Matrix: {len(odm_headers)} columns, weighted scoring, DV, CF, freeze, filter applied")

    # ===================================================================
    # 9. UPGRADE REMAINING SHEETS (formatting + DV)
    # ===================================================================
    print("Upgrading remaining sheets (Weekly Planner, Portfolio, Cover Letters, Calendar, Learning, Notes)...")

    for sheet_name in ["Weekly Planner", "Portfolio Projects", "Cover Letter Tracker",
                       "Job Search Calendar", "Learning Resources", "Notes"]:
        ws = wb[sheet_name]
        max_col = ws.max_column
        apply_header_style(ws, row=1, max_col=max_col)
        ws.freeze_panes = "B2"
        if sheet_name != "Notes":
            ws.auto_filter.ref = f"A1:{get_column_letter(max_col)}500"
        for r in range(2, min(ws.max_row + 1, 501)):
            apply_data_row_style(ws, r, max_col, alternate=(r % 2 == 0))

        # Specific DVs
        if sheet_name == "Portfolio Projects":
            add_dv(ws, '"Not Started,In Progress,Completed,On Hold"', "C")
            add_dv(ws, DV_YESNO, "M")  # Showcase Ready
            add_dv(ws, DV_YESNO, "N")  # Interview Worthy
        elif sheet_name == "Cover Letter Tracker":
            add_dv(ws, DV_YESNO, "H")  # Response Received
            add_dv(ws, DV_YESNO, "I")  # Interview Scheduled
            add_dv(ws, '"None,Light,Medium,Heavy"', "G")  # Customization Level
        elif sheet_name == "Job Search Calendar":
            add_dv(ws, '"Interview,Assessment,Deadline,Follow-up,Networking,Other"', "B")
            add_dv(ws, '"Scheduled,Completed,Cancelled,Rescheduled"', "H")
            add_dv(ws, DV_PRIORITY, "I")
            add_dv(ws, DV_YESNO, "J")
        elif sheet_name == "Learning Resources":
            add_dv(ws, '"Course,Book,Video,Documentation,Tutorial,Bootcamp,Certification"', "B")
            add_dv(ws, DV_PRIORITY, "L")
            add_dv(ws, DV_RATING, "M")

    print("  Remaining sheets: headers, freeze, filter, alternating rows applied")

    # ===================================================================
    # 10. REBUILD DASHBOARD
    # ===================================================================
    print("Rebuilding Dashboard...")
    # Delete old Dashboard and create a fresh one
    dash_idx = wb.sheetnames.index("Dashboard")
    wb.remove(wb["Dashboard"])
    ws = wb.create_sheet("Dashboard", dash_idx)

    # Set column widths - 4 KPI cards at B:C, D:E, F:G, H:I
    dash_widths = {"A": 2, "B": 18, "C": 18, "D": 18, "E": 18, "F": 18, "G": 18, "H": 18, "I": 18, "J": 2}
    set_col_widths(ws, dash_widths)

    # Title
    ws.cell(row=2, column=2, value="Developer Job Application Tracker PRO").font = font(20, bold=True, color="1B2A4A")
    ws.merge_cells("B2:H2")
    ws.cell(row=2, column=2).alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[2].height = 36

    ws.cell(row=3, column=2, value="Executive Dashboard  ·  v3.0  ·  CreatorDockStudio").font = font(10, color="6B7B8D")
    ws.merge_cells("B3:H3")
    ws.cell(row=3, column=2).alignment = Alignment(horizontal="left", vertical="center")

    # Separator
    ws.cell(row=4, column=2).border = bottom_border
    ws.merge_cells("B4:H4")
    ws.row_dimensions[4].height = 4

    # ── KPI Cards Row 1 (row 6-7) ──
    kpi_defs_row1 = [
        ("Total Applications", f'=COUNTA(Applications!B2:B500)', "2E5BBA", "EFF6FF"),
        ("Active Applications", f'=COUNTIFS(Applications!J2:J500,"<>Rejected",Applications!J2:J500,"<>Ghosted",Applications!J2:J500,"<>Withdrawn",Applications!J2:J500,"<>Accepted",Applications!B2:B500,"<>")', "8B5CF6", "F5F3FF"),
        ("Interviews", f'=COUNTIFS(Applications!J2:J500,"*Interview*",Applications!B2:B500,"<>")', "F59E0B", "FFFBEB"),
        ("Offers", f'=COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")', "22C55E", "ECFDF5"),
    ]

    for i, (label, formula, color, bg) in enumerate(kpi_defs_row1):
        col = 2 + i * 3  # B, E, H... but we want B, E(skip), use B, F
        # Actually use cols B, E (skip D as spacer), F... let's do B,D,F,H
        col = 2 + i * 2  # B, D, F, H
        kpi_card(ws, 6, col, label, formula, color, bg)

    # ── KPI Cards Row 2 (row 9-10) ──
    kpi_defs_row2 = [
        ("Technical Interviews", f'=COUNTIFS(Applications!J2:J500,"Technical Interview",Applications!B2:B500,"<>")', "F59E0B", "FFFBEB"),
        ("HR Interviews", f'=COUNTIFS(Applications!J2:J500,"HR Interview",Applications!B2:B500,"<>")', "14B8A6", "F0FDFA"),
        ("Final Interviews", f'=COUNTIFS(Applications!J2:J500,"Final Interview",Applications!B2:B500,"<>")', "8B5CF6", "F5F3FF"),
        ("Accepted Offers", f'=COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")', "22C55E", "ECFDF5"),
    ]

    for i, (label, formula, color, bg) in enumerate(kpi_defs_row2):
        col = 2 + i * 2
        kpi_card(ws, 9, col, label, formula, color, bg)

    # ── KPI Cards Row 3 (row 12-13) ──
    kpi_defs_row3 = [
        ("Rejections", f'=COUNTIFS(Applications!J2:J500,"Rejected",Applications!B2:B500,"<>")', "EF4444", "FEF2F2"),
        ("Ghosted", f'=COUNTIFS(Applications!J2:J500,"Ghosted",Applications!B2:B500,"<>")', "6B7B8D", "EDF0F5"),
        ("Pending Responses", f'=COUNTIFS(Applications!J2:J500,"Applied",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Screening",Applications!B2:B500,"<>")', "2E5BBA", "EFF6FF"),
        ("Response Rate", f'=IFERROR(ROUND((COUNTIFS(Applications!J2:J500,"<>Applied",Applications!J2:J500,"<>",Applications!B2:B500,"<>")-COUNTIFS(Applications!J2:J500,"Ghosted",Applications!B2:B500,"<>"))/COUNTA(Applications!B2:B500),2),0)', "2E5BBA", "EFF6FF"),
    ]

    for i, (label, formula, color, bg) in enumerate(kpi_defs_row3):
        col = 2 + i * 2
        kpi_card(ws, 12, col, label, formula, color, bg)

    # Set Response Rate as percentage
    ws.cell(row=13, column=8).number_format = '0%'

    # ── Performance Metrics (row 15-16) ──
    ws.cell(row=15, column=2, value="Performance Metrics").font = font(12, bold=True, color="1B2A4A")
    ws.merge_cells("B15:H15")

    perf_metrics = [
        ("Interview Rate", f'=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"*Interview*",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Offer Rate", f'=IFERROR(ROUND((COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>"))/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Success Rate", f'=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Avg Fit Score", f'=IFERROR(ROUND(AVERAGEIF(Applications!L2:L500,">0"),0),0)', "0"),
        ("Avg Decision Score", f'=IFERROR(ROUND(AVERAGE(\'Offer Decision Matrix\'!R2:R500),1),0)', "0.0"),
        ("Ghost Rate", f'=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"Ghosted",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
    ]

    for i, (label, formula, fmt) in enumerate(perf_metrics):
        col = 2 + (i % 3) * 2
        row = 16 + (i // 3) * 3
        kpi_card(ws, row, col, label, formula, "2E5BBA", "EFF6FF")
        ws.cell(row=row + 1, column=col).number_format = fmt

    # ── Progress Widgets (row 22) ──
    ws.cell(row=22, column=2, value="Goal Progress").font = font(12, bold=True, color="1B2A4A")
    ws.merge_cells("B22:H22")

    progress_defs = [
        ("Monthly Goal", f'=COUNTIFS(Applications!I2:I500,">="&EOMONTH(TODAY(),-1)+1,Applications!I2:I500,"<="&EOMONTH(TODAY(),0))', f'="/ "&50'),
        ("Weekly Goal", f'=COUNTIFS(Applications!I2:I500,">="&TODAY()-WEEKDAY(TODAY())+1,Applications!I2:I500,"<="&TODAY()-WEEKDAY(TODAY())+7)', f'="/ "&10'),
        ("Interviews Goal", f'=COUNTIFS(Applications!J2:J500,"*Interview*",Applications!I2:I500,">="&EOMONTH(TODAY(),-1)+1)', f'="/ "&5'),
        ("Networking Goal", f'=COUNTA(\'Networking Tracker\'!A2:A500)', f'="/ "&20'),
    ]

    for i, (label, formula, target) in enumerate(progress_defs):
        col = 2 + i * 2
        progress_widget(ws, 23, col, label, formula, target)

    # ── Dashboard background ──
    for r in range(1, 30):
        for c in range(1, 10):
            cell = ws.cell(row=r, column=c)
            if cell.fill.fill_type is None:
                cell.fill = fill(COLORS["surface"])

    ws.sheet_view.showGridLines = False

    print("  Dashboard: KPI cards, performance metrics, progress widgets built")

    # ===================================================================
    # 11. REBUILD STATISTICS PAGE
    # ===================================================================
    print("Rebuilding Statistics page...")
    stat_idx = wb.sheetnames.index("Statistics")
    wb.remove(wb["Statistics"])
    ws = wb.create_sheet("Statistics", stat_idx)

    stat_widths = {"A": 2, "B": 28, "C": 16, "D": 4, "E": 28, "F": 16, "G": 2}
    set_col_widths(ws, stat_widths)

    # Title
    ws.cell(row=2, column=2, value="Job Search Statistics & Analytics").font = font(18, bold=True, color="1B2A4A")
    ws.merge_cells("B2:F2")
    ws.row_dimensions[2].height = 32

    ws.cell(row=3, column=2, value="Automatically calculated from your Applications data").font = font(10, color="6B7B8D")
    ws.merge_cells("B3:F3")

    # Separator
    ws.cell(row=4, column=2).border = bottom_border
    ws.merge_cells("B4:F4")
    ws.row_dimensions[4].height = 4

    # ── Section: Application Metrics ──
    ws.cell(row=6, column=2, value="Application Metrics").font = font(12, bold=True, color="2E5BBA")
    ws.merge_cells("B6:C6")

    app_metrics = [
        ("Applications Submitted", '=COUNTA(Applications!B2:B500)', "0"),
        ("Applications per Week", '=IFERROR(ROUND(COUNTA(Applications!B2:B500)/MAX(1,ROUND((TODAY()-MIN(Applications!I2:I500))/7,0)),1),0)', "0.0"),
        ("Applications per Month", '=IFERROR(ROUND(COUNTA(Applications!B2:B500)/MAX(1,ROUND((TODAY()-MIN(Applications!I2:I500))/30,0)),1),0)', "0.0"),
        ("Avg Time Until Response (days)", '=IFERROR(ROUND(AVERAGEIFS(Applications!I2:I500,Applications!J2:J500,"<>Applied",Applications!J2:J500,"<>")-MIN(Applications!I2:I500),0),0)', "0"),
        ("Avg Time Until Interview (days)", '=IFERROR(ROUND(AVERAGEIFS(Applications!I2:I500,Applications!J2:J500,"*Interview*")-AVERAGEIFS(Applications!I2:I500,Applications!J2:J500,"*Interview*"),0),0)', "0"),
        ("Avg Time Until Offer (days)", '=IFERROR(ROUND(AVERAGEIFS(Applications!I2:I500,Applications!J2:J500,"Offer")-AVERAGEIFS(Applications!I2:I500,Applications!J2:J500,"Offer"),0),0)', "0"),
    ]

    for i, (label, formula, fmt) in enumerate(app_metrics):
        r = 7 + i
        ws.cell(row=r, column=2, value=label).font = font(10, color="1E2A38")
        ws.cell(row=r, column=2).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=2).border = thin_border
        ws.cell(row=r, column=2).alignment = left

        ws.cell(row=r, column=3, value=formula).font = font(12, bold=True, color="2E5BBA")
        ws.cell(row=r, column=3).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=3).border = thin_border
        ws.cell(row=r, column=3).alignment = center
        ws.cell(row=r, column=3).number_format = fmt
        ws.row_dimensions[r].height = 24

    # ── Section: Rates ──
    ws.cell(row=6, column=5, value="Conversion Rates").font = font(12, bold=True, color="2E5BBA")
    ws.merge_cells("E6:F6")

    rate_metrics = [
        ("Response Rate", '=IFERROR(ROUND((COUNTA(Applications!B2:B500)-COUNTIFS(Applications!J2:J500,"Applied",Applications!B2:B500,"<>")-COUNTIFS(Applications!J2:J500,"Ghosted",Applications!B2:B500,"<>"))/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Interview Rate", '=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"*Interview*",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Offer Rate", '=IFERROR(ROUND((COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>"))/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Acceptance Rate", '=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")/(COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")),2),0)', "0%"),
        ("Ghost Rate", '=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"Ghosted",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
        ("Rejection Rate", '=IFERROR(ROUND(COUNTIFS(Applications!J2:J500,"Rejected",Applications!B2:B500,"<>")/COUNTA(Applications!B2:B500),2),0)', "0%"),
    ]

    for i, (label, formula, fmt) in enumerate(rate_metrics):
        r = 7 + i
        ws.cell(row=r, column=5, value=label).font = font(10, color="1E2A38")
        ws.cell(row=r, column=5).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=5).border = thin_border
        ws.cell(row=r, column=5).alignment = left

        ws.cell(row=r, column=6, value=formula).font = font(12, bold=True, color="2E5BBA")
        ws.cell(row=r, column=6).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=6).border = thin_border
        ws.cell(row=r, column=6).alignment = center
        ws.cell(row=r, column=6).number_format = fmt

    # ── Section: Salary Analytics ──
    ws.cell(row=14, column=2, value="Salary Analytics").font = font(12, bold=True, color="2E5BBA")
    ws.merge_cells("B14:C14")

    salary_metrics = [
        ("Highest Salary", '=IFERROR(MAX(Applications!G2:G500),0)', "$#,##0"),
        ("Lowest Salary", '=IFERROR(MINIFS(Applications!G2:G500,Applications!G2:G500,">0"),0)', "$#,##0"),
        ("Average Salary", '=IFERROR(AVERAGEIF(Applications!G2:G500,">0"),0)', "$#,##0"),
        ("Median Salary", '=IFERROR(MEDIAN(IF(Applications!G2:G500>0,Applications!G2:G500)),0)', "$#,##0"),
        ("Avg Fit Score", '=IFERROR(ROUND(AVERAGEIF(Applications!L2:L500,">0"),1),0)', "0.0"),
        ("Avg Decision Score", '=IFERROR(ROUND(AVERAGE(\'Offer Decision Matrix\'!R2:R500),1),0)', "0.0"),
    ]

    for i, (label, formula, fmt) in enumerate(salary_metrics):
        r = 15 + i
        ws.cell(row=r, column=2, value=label).font = font(10, color="1E2A38")
        ws.cell(row=r, column=2).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=2).border = thin_border
        ws.cell(row=r, column=2).alignment = left

        ws.cell(row=r, column=3, value=formula).font = font(12, bold=True, color="2E5BBA")
        ws.cell(row=r, column=3).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=3).border = thin_border
        ws.cell(row=r, column=3).alignment = center
        ws.cell(row=r, column=3).number_format = fmt
        ws.row_dimensions[r].height = 24

    # ── Section: Top Insights ──
    ws.cell(row=14, column=5, value="Top Insights").font = font(12, bold=True, color="2E5BBA")
    ws.merge_cells("E14:F14")

    insight_metrics = [
        ("Most Common Job Title", '=IFERROR(INDEX(Applications!C2:C500,MODE.MATCH(Applications!C2:C500)),0)', "0"),
        ("Most Common Location", '=IFERROR(INDEX(Applications!D2:D500,MODE.MATCH(Applications!D2:D500)),0)', "0"),
        ("Most Successful Source", '=IFERROR(INDEX(Applications!H2:H500,MATCH(MAX(COUNTIFS(Applications!H2:H500,Applications!H2:H500,Applications!J2:J500,"Offer")+COUNTIFS(Applications!H2:H500,Applications!H2:H500,Applications!J2:J500,"Accepted")),COUNTIFS(Applications!H2:H500,Applications!H2:H500,Applications!J2:J500,"Offer")+COUNTIFS(Applications!H2:H500,Applications!H2:H500,Applications!J2:J500,"Accepted"),0)),0)', "0"),
        ("Most Applied Company", '=IFERROR(INDEX(Applications!B2:B500,MATCH(MAX(COUNTIF(Applications!B2:B500,Applications!B2:B500)),COUNTIF(Applications!B2:B500,Applications!B2:B500),0)),0)', "0"),
        ("Total Companies", '=IFERROR(SUMPRODUCT(1/COUNTIF(Applications!B2:B500,Applications!B2:B500&"")),0)', "0"),
        ("Avg Days Active", '=IFERROR(ROUND(AVERAGE(Applications!AB2:AB500),0),0)', "0"),
    ]

    for i, (label, formula, fmt) in enumerate(insight_metrics):
        r = 15 + i
        ws.cell(row=r, column=5, value=label).font = font(10, color="1E2A38")
        ws.cell(row=r, column=5).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=5).border = thin_border
        ws.cell(row=r, column=5).alignment = left

        ws.cell(row=r, column=6, value=formula).font = font(12, bold=True, color="2E5BBA")
        ws.cell(row=r, column=6).fill = fill(COLORS["surface"] if i % 2 == 0 else COLORS["surface2"])
        ws.cell(row=r, column=6).border = thin_border
        ws.cell(row=r, column=6).alignment = center
        ws.cell(row=r, column=6).number_format = fmt

    # Background
    for r in range(1, 25):
        for c in range(1, 8):
            cell = ws.cell(row=r, column=c)
            if cell.fill.fill_type is None:
                cell.fill = fill(COLORS["surface"])

    ws.sheet_view.showGridLines = False

    print("  Statistics: 24+ formulas across 4 sections built")

    # ===================================================================
    # 12. ADD CHARTS TO DASHBOARD
    # ===================================================================
    print("Adding charts to Dashboard...")

    # We need a hidden data area for charts. Put it below row 30 on Dashboard
    ws = wb["Dashboard"]

    # Chart data area (rows 30+)
    # Status breakdown
    statuses = ["Applied", "Screening", "Phone Screen", "Technical Interview",
                "HR Interview", "Final Interview", "Offer", "Accepted", "Rejected", "Ghosted", "Withdrawn"]
    ws.cell(row=30, column=2, value="Status")
    ws.cell(row=30, column=3, value="Count")
    for i, s in enumerate(statuses):
        ws.cell(row=31 + i, column=2, value=s)
        ws.cell(row=31 + i, column=3, value=f'=COUNTIFS(Applications!J2:J500,"{s}",Applications!B2:B500,"<>")')

    # Source breakdown
    sources = ["LinkedIn", "Indeed", "AngelList", "Glassdoor", "Company Website", "Referral", "Recruiter", "Job Fair", "Other"]
    ws.cell(row=30, column=5, value="Source")
    ws.cell(row=30, column=6, value="Count")
    for i, s in enumerate(sources):
        ws.cell(row=31 + i, column=5, value=s)
        ws.cell(row=31 + i, column=6, value=f'=COUNTIFS(Applications!H2:H500,"{s}",Applications!B2:B500,"<>")')

    # Remote breakdown
    remote_types = ["Remote", "Hybrid", "Onsite", "Flexible"]
    ws.cell(row=45, column=2, value="Work Type")
    ws.cell(row=45, column=3, value="Count")
    for i, rt in enumerate(remote_types):
        ws.cell(row=46 + i, column=2, value=rt)
        ws.cell(row=46 + i, column=3, value=f'=COUNTIFS(Applications!F2:F500,"{rt}",Applications!B2:B500,"<>")')

    # Priority breakdown
    priorities = ["Critical", "High", "Medium", "Low"]
    ws.cell(row=45, column=5, value="Priority")
    ws.cell(row=45, column=6, value="Count")
    for i, p in enumerate(priorities):
        ws.cell(row=46 + i, column=5, value=p)
        ws.cell(row=46 + i, column=6, value=f'=COUNTIFS(Applications!K2:K500,"{p}",Applications!B2:B500,"<>")')

    # Monthly applications (last 6 months)
    ws.cell(row=52, column=2, value="Month")
    ws.cell(row=52, column=3, value="Count")
    for i in range(6):
        month_label = f'=TEXT(EOMONTH(TODAY(),-{5-i}),"MMM YYYY")'
        ws.cell(row=53 + i, column=2, value=month_label)
        ws.cell(row=53 + i, column=3, value=f'=COUNTIFS(Applications!I2:I500,">="&EOMONTH(TODAY(),-{5-i}-1)+1,Applications!I2:I500,"<="&EOMONTH(TODAY(),-{5-i}))')

    # Interview funnel
    funnel = [
        ("Applied", '=COUNTA(Applications!B2:B500)'),
        ("Screening", '=COUNTIFS(Applications!J2:J500,"Screening",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Phone Screen",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"*Interview*",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")'),
        ("Interview", '=COUNTIFS(Applications!J2:J500,"*Interview*",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")'),
        ("Offer", '=COUNTIFS(Applications!J2:J500,"Offer",Applications!B2:B500,"<>")+COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")'),
        ("Accepted", '=COUNTIFS(Applications!J2:J500,"Accepted",Applications!B2:B500,"<>")'),
    ]
    ws.cell(row=52, column=5, value="Funnel Stage")
    ws.cell(row=52, column=6, value="Count")
    for i, (label, formula) in enumerate(funnel):
        ws.cell(row=53 + i, column=5, value=label)
        ws.cell(row=53 + i, column=6, value=formula)

    # Hide chart data area
    for r in range(30, 62):
        ws.row_dimensions[r].hidden = True

    # ── Create Charts ──
    # 1. Applications per Month (Bar Chart)
    chart_monthly = BarChart()
    chart_monthly.type = "col"
    chart_monthly.style = 2
    chart_monthly.title = "Applications per Month"
    chart_monthly.y_axis.title = "Count"
    chart_monthly.x_axis.title = "Month"
    data = Reference(ws, min_col=3, min_row=52, max_row=58, max_col=3)
    cats = Reference(ws, min_col=2, min_row=53, max_row=58)
    chart_monthly.add_data(data, titles_from_data=True)
    chart_monthly.set_categories(cats)
    chart_monthly.height = 7
    chart_monthly.width = 14
    ws.add_chart(chart_monthly, "B27")

    # 2. Applications by Status (Pie Chart)
    chart_status = PieChart()
    chart_status.title = "Applications by Status"
    data = Reference(ws, min_col=3, min_row=30, max_row=41, max_col=3)
    cats = Reference(ws, min_col=2, min_row=31, max_row=41)
    chart_status.add_data(data, titles_from_data=True)
    chart_status.set_categories(cats)
    chart_status.height = 7
    chart_status.width = 12
    ws.add_chart(chart_status, "F27")

    # 3. Applications by Source (Bar Chart)
    chart_source = BarChart()
    chart_source.type = "bar"
    chart_source.style = 3
    chart_source.title = "Applications by Source"
    data = Reference(ws, min_col=6, min_row=30, max_row=39, max_col=6)
    cats = Reference(ws, min_col=5, min_row=31, max_row=39)
    chart_source.add_data(data, titles_from_data=True)
    chart_source.set_categories(cats)
    chart_source.height = 7
    chart_source.width = 14
    ws.add_chart(chart_source, "B40")

    # 4. Remote vs Hybrid vs Onsite (Doughnut)
    chart_remote = DoughnutChart()
    chart_remote.title = "Work Type Distribution"
    data = Reference(ws, min_col=3, min_row=45, max_row=49, max_col=3)
    cats = Reference(ws, min_col=2, min_row=46, max_row=49)
    chart_remote.add_data(data, titles_from_data=True)
    chart_remote.set_categories(cats)
    chart_remote.height = 7
    chart_remote.width = 12
    ws.add_chart(chart_remote, "F40")

    # 5. Applications by Priority (Bar Chart)
    chart_priority = BarChart()
    chart_priority.type = "col"
    chart_priority.style = 5
    chart_priority.title = "Applications by Priority"
    data = Reference(ws, min_col=6, min_row=45, max_row=49, max_col=6)
    cats = Reference(ws, min_col=5, min_row=46, max_row=49)
    chart_priority.add_data(data, titles_from_data=True)
    chart_priority.set_categories(cats)
    chart_priority.height = 7
    chart_priority.width = 14
    ws.add_chart(chart_priority, "B53")

    # 6. Interview Funnel (Bar Chart)
    chart_funnel = BarChart()
    chart_funnel.type = "bar"
    chart_funnel.style = 6
    chart_funnel.title = "Interview Funnel"
    data = Reference(ws, min_col=6, min_row=52, max_row=57, max_col=6)
    cats = Reference(ws, min_col=5, min_row=53, max_row=57)
    chart_funnel.add_data(data, titles_from_data=True)
    chart_funnel.set_categories(cats)
    chart_funnel.height = 7
    chart_funnel.width = 12
    ws.add_chart(chart_funnel, "F53")

    print("  Charts: 6 charts added to Dashboard (Monthly, Status, Source, Work Type, Priority, Funnel)")

    # ===================================================================
    # 13. APPLY GLOBAL UX/UI
    # ===================================================================
    print("Applying global UX/UI polish...")

    # Set tab colors
    tab_colors = {
        "Dashboard": "1B2A4A",
        "Applications": "2E5BBA",
        "Interview Tracker": "F59E0B",
        "Recruiter CRM": "8B5CF6",
        "Target Companies": "14B8A6",
        "Salary Comparison": "22C55E",
        "Weekly Planner": "6B7B8D",
        "Statistics": "2E5BBA",
        "Notes": "6B7B8D",
        "Portfolio Projects": "8B5CF6",
        "Networking Tracker": "14B8A6",
        "Skill Gap Analysis": "F59E0B",
        "Cover Letter Tracker": "8B5CF6",
        "Job Search Calendar": "2E5BBA",
        "Learning Resources": "22C55E",
        "Offer Decision Matrix": "EF4444",
    }

    for name, color in tab_colors.items():
        if name in wb.sheetnames:
            wb[name].sheet_properties.tabColor = color

    # Set default font for all sheets
    for name in wb.sheetnames:
        ws = wb[name]
        ws.sheet_view.showGridLines = False if name in ["Dashboard", "Statistics"] else True
        # Set default row height
        if name not in ["Dashboard", "Statistics"]:
            ws.row_dimensions[1].height = 28

    # Move Dashboard to first position
    wb.move_sheet("Dashboard", offset=-wb.sheetnames.index("Dashboard"))

    # Set active sheet to Dashboard
    wb.active = wb.sheetnames.index("Dashboard")

    print("  Tab colors, gridlines, sheet order applied")

    # ===================================================================
    # SAVE
    # ===================================================================
    output_path = filepath.replace(".xlsx", "_v3.xlsx")
    if os.path.exists(output_path):
        os.remove(output_path)

    print(f"\nSaving upgraded workbook to: {output_path}")
    wb.save(output_path)
    print("Done! Workbook upgraded to v3.0")
    print(f"\nOutput: {output_path}")
    return output_path


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tracker_path = os.path.join(base_dir, "Developer_Job_Application_Tracker_PRO.xlsx")
    result = upgrade_workbook(tracker_path)
