"""Quick workbook regression test against DEMO workbook."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend_bridge.api import ExcelBridgeAPI

def main():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    wb = os.path.join(project_root, "Developer_Job_Application_Tracker_PRO_DEMO.xlsx")
    api = ExcelBridgeAPI(workbook_path=wb)

    passed = 0
    failed = 0

    def ok(cond, label):
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  PASS: {label}")
        else:
            failed += 1
            print(f"  FAIL: {label}")

    # Test read methods (old format: data/error/count)
    apps = api.get_applications()
    ok(apps.get("error") is None, "get_applications no error")
    ok(len(apps.get("data", [])) > 0, "get_applications returns data")
    print(f"    count={apps.get('count', 0)}")

    kpis = api.get_kpis()
    ok(kpis.get("error") is None, "get_kpis no error")
    ok(len(kpis.get("data", [])) > 0, "get_kpis returns data")

    dash = api.get_dashboard()
    ok(dash.get("error") is None, "get_dashboard no error")
    ok(dash.get("data") is not None, "get_dashboard returns data")

    # Phase 2B methods (new format: success/data/error)
    streak = api.get_streak_data()
    ok(streak.get("success") is True, "get_streak_data success")
    ok("currentStreak" in streak.get("data", {}), "get_streak_data has currentStreak")
    print(f"    streak={streak['data'].get('currentStreak', 'N/A')}")

    actions = api.get_next_actions()
    ok(actions.get("success") is True, "get_next_actions success")
    ok(isinstance(actions.get("data"), list), "get_next_actions returns list")
    print(f"    actions={len(actions.get('data', []))}")

    report = api.export_report({"type": "monthly"})
    ok(report.get("success") is True, "export_report success")
    ok("content" in report.get("data", {}), "export_report has content")
    ok("filename" in report.get("data", {}), "export_report has filename")
    print(f"    filename={report['data'].get('filename', 'N/A')}")

    iq = api.get_interview_questions({"category": "Behavioral"})
    ok(iq.get("success") is True, "get_interview_questions success")
    ok(len(iq.get("data", [])) > 0, "get_interview_questions returns questions")
    print(f"    questions={len(iq.get('data', []))}")

    cl = api.generate_cover_letter({"company": "TestCo", "role": "Dev", "name": "Test"})
    ok(cl.get("success") is True, "generate_cover_letter success")
    ok(cl["data"].get("mode") == "offline", "generate_cover_letter offline mode")
    ok(len(cl["data"].get("content", "")) > 0, "generate_cover_letter has content")

    li = api.generate_linkedin_message({
        "messageType": "connection",
        "recipientName": "Jane",
        "company": "Corp",
        "yourName": "Me",
    })
    ok(li.get("success") is True, "generate_linkedin_message success")
    ok(li["data"].get("characterCount", 0) > 0, "generate_linkedin_message has content")

    ja = api.analyze_job_description({
        "jobDescription": "Looking for a Senior Python Developer with 5+ years experience in Django, PostgreSQL, AWS. Salary $120k-$160k."
    })
    ok(ja.get("success") is True, "analyze_job_description success")
    ok(isinstance(ja["data"].get("fitScore"), int), "analyze_job_description returns fitScore")
    print(f"    fitScore={ja['data'].get('fitScore', 'N/A')}")

    hist = api.get_interview_practice_history()
    ok(hist.get("success") is True, "get_interview_practice_history success")
    ok("stats" in hist.get("data", {}), "get_interview_practice_history has stats")

    print()
    print(f"Results: {passed} passed, {failed} failed")
    if failed == 0:
        print("ALL WORKBOOK REGRESSION TESTS PASSED")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
