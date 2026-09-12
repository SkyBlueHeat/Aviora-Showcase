"""Backend bridge tests — read-only safety, mapping, and API tests.
Run: python -m backend_bridge.tests.test_bridge
"""
import os
import sys
import tempfile
import openpyxl

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from backend_bridge.excel_reader import ExcelReader
from backend_bridge.data_mapper import (
    map_application,
    map_applications,
    compute_kpis,
    compute_pipeline,
    map_salary_entry,
    map_interview_history,
    map_cover_letter_history,
    _normalize_status,
    _normalize_date,
    _normalize_remote,
    _normalize_priority,
)
from backend_bridge.api import ExcelBridgeAPI

FIXTURE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_fixture_workbook.xlsx")
REAL_WORKBOOK = os.path.join(PROJECT_ROOT, "Developer_Job_Application_Tracker_PRO.xlsx")

passes = 0
errors = 0


def check(name, condition, detail=""):
    global passes, errors
    if condition:
        passes += 1
        print(f"  PASS: {name}")
    else:
        errors += 1
        print(f"  FAIL: {name} — {detail}")


def test_fixture_exists():
    print("\n=== Fixture Workbook ===")
    check("fixture workbook exists", os.path.exists(FIXTURE_PATH), f"Path: {FIXTURE_PATH}")


def test_workbook_status():
    print("\n=== Workbook Status ===")
    reader = ExcelReader(FIXTURE_PATH)
    status = reader.get_workbook_status()
    check("fixture exists in status", status["exists"])
    check("fixture has sheets", len(status["sheets"]) > 0)
    check("fixture sheet count", status.get("sheet_count", 0) >= 4, f"Got {status.get('sheet_count')}")
    check("fixture has Applications sheet", "Applications" in status["sheets"])
    check("fixture has Salary Comparison sheet", "Salary Comparison" in status["sheets"])
    check("fixture no error", status.get("error") is None, f"Error: {status.get('error')}")


def test_missing_workbook():
    print("\n=== Missing Workbook Handling ===")
    reader = ExcelReader("/nonexistent/path/workbook.xlsx")
    status = reader.get_workbook_status()
    check("missing workbook returns exists=False", status["exists"] is False)
    check("missing workbook has error", status.get("error") is not None)
    
    headers, rows = reader.read_applications()
    check("missing workbook returns empty headers", headers == [])
    check("missing workbook returns empty rows", rows == [])


def test_read_applications_fixture():
    print("\n=== Read Applications (Fixture) ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_applications()
    check("fixture has 33 headers", len(headers) == 33, f"Got {len(headers)}")
    check("fixture has 6 data rows", len(rows) == 6, f"Got {len(rows)}")
    check("first header is Application ID", headers[0] == "Application ID")
    check("second header is Company", headers[1] == "Company")


def test_read_applications_real():
    print("\n=== Read Applications (Real Workbook) ===")
    if not os.path.exists(REAL_WORKBOOK):
        check("real workbook exists", False, "File not found")
        return
    reader = ExcelReader(REAL_WORKBOOK)
    headers, rows = reader.read_applications()
    check("real workbook has headers", len(headers) > 0)
    check("real workbook returns list (may have data)", isinstance(rows, list))


def test_map_applications():
    print("\n=== Map Applications ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_applications()
    applications = map_applications(headers, rows)
    check("mapped 6 applications", len(applications) == 6)
    
    app = applications[0]
    check("app 0 id", app["id"] == "APP-001")
    check("app 0 company", app["company"] == "Tech Corp")
    check("app 0 role", app["role"] == "Senior Frontend Developer")
    check("app 0 status", app["status"] == "Technical")
    check("app 0 priority", app["priority"] == "High")
    check("app 0 workType", app["workType"] == "Remote")
    check("app 0 fitScore", app["fitScore"] == 85)
    check("app 0 appliedDate", app["appliedDate"] == "2026-06-15")
    check("app 0 followUpDate", app["followUpDate"] == "2026-07-01")
    check("app 0 nextAction not empty", len(app["nextAction"]) > 0)
    check("app 0 qualityScore is 0 (not in Excel)", app["qualityScore"] == 0)
    check("app 0 techStack is empty list", app["techStack"] == [])
    
    # Check offer app
    offer_app = applications[2]
    check("app 2 status is Offer", offer_app["status"] == "Offer")
    check("app 2 workType is Hybrid", offer_app["workType"] == "Hybrid")
    
    # Check rejected app
    rejected_app = applications[4]
    check("app 4 status is Rejected", rejected_app["status"] == "Rejected")
    check("app 4 workType is On-site", rejected_app["workType"] == "On-site")


def test_empty_applications_mapping():
    print("\n=== Empty Applications Mapping ===")
    # Empty headers/rows
    result = map_applications([], [])
    check("empty input returns []", result == [])
    
    # Headers only, no rows
    result = map_applications(["Application ID", "Company"], [])
    check("headers only returns []", result == [])


def test_status_normalization():
    print("\n=== Status Normalization ===")
    check("Saved", _normalize_status("Saved") == "Saved")
    check("Applied", _normalize_status("Applied") == "Applied")
    check("Phone Screen", _normalize_status("Phone Screen") == "Phone Screen")
    check("Technical", _normalize_status("Technical") == "Technical")
    check("Onsite", _normalize_status("Onsite") == "Onsite")
    check("Offer", _normalize_status("Offer") == "Offer")
    check("Rejected", _normalize_status("Rejected") == "Rejected")
    check("Ghosted", _normalize_status("Ghosted") == "Ghosted")
    check("case insensitive 'applied'", _normalize_status("applied") == "Applied")
    check("case insensitive 'OFFER'", _normalize_status("OFFER") == "Offer")
    check("empty returns Saved", _normalize_status("") == "Saved")
    check("None returns Saved", _normalize_status(None) == "Saved")
    check("unknown status defaults to Applied", _normalize_status("Withdrawn") == "Applied")
    check("unknown gibberish defaults to Applied", _normalize_status("xyz123") == "Applied")


def test_date_normalization():
    print("\n=== Date Normalization ===")
    check("ISO date", _normalize_date("2026-06-15") == "2026-06-15")
    check("US date", _normalize_date("06/15/2026") == "2026-06-15")
    check("None returns empty", _normalize_date(None) == "")
    check("empty returns empty", _normalize_date("") == "")


def test_remote_normalization():
    print("\n=== Remote Normalization ===")
    check("Yes -> Remote", _normalize_remote("Yes") == "Remote")
    check("No -> On-site", _normalize_remote("No") == "On-site")
    check("Hybrid -> Hybrid", _normalize_remote("Hybrid") == "Hybrid")
    check("empty -> On-site", _normalize_remote("") == "On-site")
    check("None -> On-site", _normalize_remote(None) == "On-site")


def test_priority_normalization():
    print("\n=== Priority Normalization ===")
    check("Critical", _normalize_priority("Critical") == "Critical")
    check("High", _normalize_priority("High") == "High")
    check("Medium", _normalize_priority("Medium") == "Medium")
    check("Low", _normalize_priority("Low") == "Low")
    check("empty -> Low", _normalize_priority("") == "Low")


def test_compute_kpis():
    print("\n=== Compute KPIs ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_applications()
    applications = map_applications(headers, rows)
    kpis = compute_kpis(applications)
    check("6 KPIs returned", len(kpis) == 6)
    check("Total Applications = 6", kpis[0]["value"] == 6)
    check("Active = 4 (not Rejected/Ghosted)", kpis[1]["value"] == 4, f"Got {kpis[1]['value']}")
    check("Interviews = 1 (Technical)", kpis[2]["value"] == 1, f"Got {kpis[2]['value']}")
    check("Offers = 1", kpis[3]["value"] == 1, f"Got {kpis[3]['value']}")
    check("Response Rate > 0", int(str(kpis[4]["value"]).replace("%", "")) > 0)
    check("Ghosted = 1", kpis[5]["value"] == 1, f"Got {kpis[5]['value']}")
    
    # Empty KPIs
    empty_kpis = compute_kpis([])
    check("empty KPIs Total = 0", empty_kpis[0]["value"] == 0)


def test_compute_pipeline():
    print("\n=== Compute Pipeline ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_applications()
    applications = map_applications(headers, rows)
    pipeline = compute_pipeline(applications)
    check("8 pipeline columns", len(pipeline) == 8)
    check("Saved count = 1", pipeline[0]["count"] == 1)
    check("Applied count = 1", pipeline[1]["count"] == 1)
    check("Technical count = 1", pipeline[3]["count"] == 1)
    check("Offer count = 1", pipeline[5]["count"] == 1)
    check("Rejected count = 1", pipeline[6]["count"] == 1)
    check("Ghosted count = 1", pipeline[7]["count"] == 1)


def test_salary_mapping():
    print("\n=== Salary Mapping ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_salary_comparison()
    check("salary has 2 data rows", len(rows) == 2, f"Got {len(rows)}")
    
    from backend_bridge.data_mapper import map_salary_data
    salaries = map_salary_data(headers, rows)
    check("mapped 2 salary entries", len(salaries) == 2)
    
    s = salaries[0]
    check("company Tech Corp", s["company"] == "Tech Corp")
    check("baseSalary 150000", s["baseSalary"] == 150000)
    check("bonusAbsolute 20000", s["bonusAbsolute"] == 20000)
    check("bonusPct computed", s["bonusPct"] > 0, f"Got {s['bonusPct']}")
    check("totalComp computed (formula recomputed)", s["totalComp"] > 150000, f"Got {s['totalComp']}")
    check("netAnnual computed", s["netAnnual"] > 0, f"Got {s['netAnnual']}")
    check("netMonthly computed", s["netMonthly"] > 0, f"Got {s['netMonthly']}")
    check("taxBracket is 25%", s["taxBracket"] == "25%")


def test_interview_history():
    print("\n=== Interview History ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_interview_history()
    check("interview has 2 data rows", len(rows) == 2)
    history = map_interview_history(headers, rows)
    check("mapped 2 interview entries", len(history) == 2)
    check("first company Tech Corp", history[0]["company"] == "Tech Corp")
    check("first stage Technical", history[0]["stage"] == "Technical")
    check("first date normalized", history[0]["date"] == "2026-06-20")


def test_cover_letter_history():
    print("\n=== Cover Letter History ===")
    reader = ExcelReader(FIXTURE_PATH)
    headers, rows = reader.read_cover_letter_history()
    check("cover letter has 2 data rows", len(rows) == 2)
    history = map_cover_letter_history(headers, rows)
    check("mapped 2 cover letter entries", len(history) == 2)
    check("first company Tech Corp", history[0]["company"] == "Tech Corp")
    check("first dateCreated normalized", history[0]["dateCreated"] == "2026-06-14")


def test_api_health():
    print("\n=== API Health ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    health = api.health()
    check("health status ok", health["status"] == "ok")
    check("health workbook exists", health["workbook_exists"] is True)
    check("health has sheets", len(health["sheets"]) > 0)


def test_api_get_applications():
    print("\n=== API get_applications ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    result = api.get_applications()
    check("no error", result["error"] is None)
    check("6 applications", result["count"] == 6)
    check("data is list", isinstance(result["data"], list))
    check("first app has id", "id" in result["data"][0])
    check("first app has company", "company" in result["data"][0])


def test_api_get_dashboard():
    print("\n=== API get_dashboard ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    result = api.get_dashboard()
    check("no error", result["error"] is None)
    check("data has kpis", "kpis" in result["data"])
    check("data has monthlyChart", "monthlyChart" in result["data"])
    check("data has sourceChart", "sourceChart" in result["data"])
    check("data has pipeline", "pipeline" in result["data"])
    check("kpis is list", isinstance(result["data"]["kpis"], list))


def test_api_get_kpis():
    print("\n=== API get_kpis ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    result = api.get_kpis()
    check("no error", result["error"] is None)
    check("6 kpis", len(result["data"]) == 6)


def test_api_get_pipeline():
    print("\n=== API get_pipeline ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    result = api.get_pipeline()
    check("no error", result["error"] is None)
    check("8 pipeline columns", len(result["data"]) == 8)


def test_api_get_salary_data():
    print("\n=== API get_salary_data ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    result = api.get_salary_data()
    check("no error", result["error"] is None)
    check("2 salary entries", result["count"] == 2)


def test_api_missing_workbook():
    print("\n=== API with Missing Workbook ===")
    api = ExcelBridgeAPI("/nonexistent/workbook.xlsx")
    health = api.health()
    check("health status error", health["status"] == "error")
    
    result = api.get_applications()
    check("missing workbook returns empty data", result["data"] == [])
    check("missing workbook has error", result["error"] is not None)
    check("missing workbook count 0", result["count"] == 0)


def test_api_json_safe():
    print("\n=== API JSON-Safe Output ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    
    import json
    # All API methods should return JSON-serializable dicts
    for method_name in ["health", "get_applications", "get_dashboard", "get_kpis",
                        "get_pipeline", "get_salary_data", "get_interview_history",
                        "get_cover_letter_history"]:
        try:
            method = getattr(api, method_name)
            result = method()
            json.dumps(result)
            check(f"{method_name} is JSON-safe", True)
        except (TypeError, ValueError) as e:
            check(f"{method_name} is JSON-safe", False, str(e))


def test_no_write_methods():
    print("\n=== Read-Only Safety: No Write Methods ===")
    api = ExcelBridgeAPI(FIXTURE_PATH)
    
    # Phase 2B.2: add_application and update_application_status are now intentionally
    # present on ExcelBridgeAPI — they are demo-only and safety-gated.
    # All other write/save/delete methods must NOT exist.
    forbidden_methods = ["save", "write", "update", "delete",
                         "update_application", "delete_application", "save_application",
                         "update_status", "remove_application",
                         "delete_application", "archive_application"]
    for wm in forbidden_methods:
        check(f"no {wm} method", not hasattr(api, wm), f"Found {wm} method!")
    
    # Verify Phase 2B.2 write methods exist (they should be safety-gated)
    check("add_application method exists (Phase 2B.2)", hasattr(api, "add_application"))
    check("update_application_status method exists (Phase 2B.2)", hasattr(api, "update_application_status"))
    
    # Check ExcelReader has no save method
    reader = ExcelReader(FIXTURE_PATH)
    check("ExcelReader has no save method", not hasattr(reader, "save"))
    check("ExcelReader has no write method", not hasattr(reader, "write"))
    check("ExcelReader has no write_cell method", not hasattr(reader, "write_cell"))


def test_real_workbook_api():
    print("\n=== Real Workbook API ===")
    if not os.path.exists(REAL_WORKBOOK):
        check("real workbook exists", False, "File not found")
        return
    api = ExcelBridgeAPI(REAL_WORKBOOK)
    result = api.get_applications()
    check("real workbook applications readable", isinstance(result.get("data"), list))
    check("real workbook no error", result["error"] is None)
    
    kpis = api.get_kpis()
    check("real workbook KPIs no error", kpis["error"] is None)
    check("real workbook KPIs has data", isinstance(kpis.get("data"), list) and len(kpis["data"]) > 0)


def run_all():
    print("=" * 60)
    print("BACKEND BRIDGE TEST SUITE")
    print("=" * 60)
    
    test_fixture_exists()
    test_workbook_status()
    test_missing_workbook()
    test_read_applications_fixture()
    test_read_applications_real()
    test_map_applications()
    test_empty_applications_mapping()
    test_status_normalization()
    test_date_normalization()
    test_remote_normalization()
    test_priority_normalization()
    test_compute_kpis()
    test_compute_pipeline()
    test_salary_mapping()
    test_interview_history()
    test_cover_letter_history()
    test_api_health()
    test_api_get_applications()
    test_api_get_dashboard()
    test_api_get_kpis()
    test_api_get_pipeline()
    test_api_get_salary_data()
    test_api_missing_workbook()
    test_api_json_safe()
    test_no_write_methods()
    test_real_workbook_api()
    
    print("\n" + "=" * 60)
    print(f"TOTAL PASSES:  {passes}")
    print(f"TOTAL ERRORS:  {errors}")
    print("=" * 60)
    
    if errors == 0:
        print("RESULT: PASSED — NO ERRORS")
        sys.exit(0)
    else:
        print("RESULT: FAILED")
        sys.exit(1)


if __name__ == "__main__":
    run_all()
