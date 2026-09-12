"""Phase 2A.0 — Excel Workbook Inspection Script.
Read-only inspection. No writes, no saves.
"""
import openpyxl
import json
import os

WORKBOOK_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "Developer_Job_Application_Tracker_PRO.xlsx",
)
WORKBOOK_PATH = os.path.normpath(WORKBOOK_PATH)

print(f"Workbook: {WORKBOOK_PATH}")
print(f"Exists: {os.path.exists(WORKBOOK_PATH)}")
print()

wb = openpyxl.load_workbook(WORKBOOK_PATH, read_only=True, data_only=True)

print(f"Sheet count: {len(wb.sheetnames)}")
print(f"Sheet names: {wb.sheetnames}")
print()

report = {}

for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    print(f"{'='*70}")
    print(f"SHEET: {sheet_name}")
    print(f"{'='*70}")

    # Dimensions (read_only mode doesn't support .dimensions, use iter_rows)
    print(f"  Sheet title: {ws.title}")

    sheet_info = {
        "name": sheet_name,
        "headers": [],
        "header_row_index": None,
        "example_rows": [],
        "all_values_empty": True,
        "col_count": 0,
    }

    rows_read = 0
    max_rows_to_read = 8

    for row_idx, row in enumerate(ws.iter_rows(min_row=1, max_row=max_rows_to_read, values_only=True), start=1):
        row_list = list(row)
        # Check if row is completely empty
        is_empty = all(v is None or str(v).strip() == "" for v in row_list)

        if row_idx == 1:
            print(f"  Row 1 (first row): {row_list[:20]}")
        if row_idx == 2:
            print(f"  Row 2: {row_list[:20]}")
        if row_idx == 3:
            print(f"  Row 3: {row_list[:20]}")

        # Detect header row — first non-empty row
        if sheet_info["header_row_index"] is None and not is_empty:
            sheet_info["header_row_index"] = row_idx
            sheet_info["headers"] = [str(v) if v is not None else "" for v in row_list]
            sheet_info["col_count"] = len(row_list)

        # Collect example data rows (after header)
        if sheet_info["header_row_index"] is not None and row_idx > sheet_info["header_row_index"]:
            if not is_empty:
                sheet_info["example_rows"].append(row_list)
                sheet_info["all_values_empty"] = False

        if not is_empty:
            sheet_info["all_values_empty"] = False

        rows_read += 1

    # Print headers
    if sheet_info["headers"]:
        print(f"\n  Detected header row: {sheet_info['header_row_index']}")
        print(f"  Headers ({len(sheet_info['headers'])} cols):")
        for i, h in enumerate(sheet_info["headers"]):
            if h:
                print(f"    [{i}] {h}")
    else:
        print(f"\n  No headers detected (all rows empty or only first {max_rows_to_read} rows read)")

    # Print example data rows
    if sheet_info["example_rows"]:
        print(f"\n  Example data rows ({len(sheet_info['example_rows'])}):")
        for i, er in enumerate(sheet_info["example_rows"][:3]):
            # Truncate long rows
            display = [str(v)[:40] if v is not None else "None" for v in er[:15]]
            print(f"    Row {i+1}: {display}")
    else:
        print(f"\n  No data rows found (sheet may be empty or formula-only)")

    # Check for formulas (data_only=True shows cached values, None if never opened in Excel)
    formula_hints = []
    if sheet_info["example_rows"]:
        for er in sheet_info["example_rows"][:2]:
            for j, v in enumerate(er):
                if v is None and j < len(sheet_info["headers"]) and sheet_info["headers"][j]:
                    formula_hints.append(f"Col [{j}] '{sheet_info['headers'][j]}' has None value (possible uncached formula)")

    if formula_hints:
        print(f"\n  Formula/value observations (data_only mode):")
        for fh in formula_hints[:10]:
            print(f"    {fh}")

    # Relevance assessment
    relevance = []
    name_lower = sheet_name.lower()
    if any(k in name_lower for k in ["application", "tracker", "applied"]):
        relevance.append("applications")
    if "dashboard" in name_lower:
        relevance.append("dashboard")
    if "setting" in name_lower:
        relevance.append("settings")
    if "streak" in name_lower:
        relevance.append("streaks")
    if "interview" in name_lower:
        relevance.append("interviews")
    if "salary" in name_lower:
        relevance.append("salary")
    if "cover" in name_lower:
        relevance.append("cover letters")
    if "linkedin" in name_lower:
        relevance.append("LinkedIn messages")
    if "jd" in name_lower or "job desc" in name_lower:
        relevance.append("JD analysis")
    if "ats" in name_lower:
        relevance.append("ATS scores")
    if "report" in name_lower:
        relevance.append("reports/charts")
    if "backup" in name_lower:
        relevance.append("backup")
    if "valid" in name_lower:
        relevance.append("validation")
    if "email" in name_lower:
        relevance.append("email templates")
    if "notion" in name_lower:
        relevance.append("Notion sync")

    sheet_info["relevance"] = relevance
    print(f"\n  Relevance: {relevance if relevance else 'unclear/other'}")
    print()

    report[sheet_name] = sheet_info

wb.close()

# Save report as JSON for reference
report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "workbook_inspection_report.json")
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False, default=str)
print(f"\nReport saved to: {report_path}")
print(f"\nINSPECTION COMPLETE — no writes to Excel were performed.")
