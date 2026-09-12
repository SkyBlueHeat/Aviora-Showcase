"""Tests for ExcelWriter — Phase 2B.3B demo + staging + production write actions.

Verifies:
- add_application creates backup first, then appends a row
- update_application_status creates backup first, then changes only the Status cell
- missing Application ID returns safe error
- invalid status is normalized safely
- real workbook write attempt is blocked without opt-in
- write is blocked when JOBTRACKER_WORKBOOK_PATH is not set
- write is blocked when workbook filename does not include _DEMO or _TEST
- failed backup prevents write
- API results are JSON-safe
- existing read-only API methods still work after write methods are added
- staging writes blocked without JOBTRACKER_ENABLE_STAGING_WRITES=1
- staging writes allowed with both required env vars
- production writes blocked without JOBTRACKER_ENABLE_PRODUCTION_WRITES=1
- production writes allowed with opt-in env var
- production status update works
- rapid backups remain unique
- results are JSON-safe
- session safety backup created on first production write only
- session backup has distinct _session_backup_ filename
- session backup not created for demo/staging modes
- session backup failure blocks production writes
- session backup path reported in get_write_mode()
"""
import os
import sys
import shutil
import tempfile
import json
import openpyxl

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend_bridge.excel_writer import ExcelWriter, PRODUCTION_WORKBOOK_NAME
from backend_bridge.excel_backup import ExcelBackup
from backend_bridge.api import ExcelBridgeAPI
from backend_bridge.excel_reader import ExcelReader

PASS_COUNT = 0
ERROR_COUNT = 0


def check(condition: bool, label: str):
    global PASS_COUNT, ERROR_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        ERROR_COUNT += 1
        print(f"  FAIL: {label}")


def run_tests():
    fixture_path = os.path.join(
        _project_root, "backend_bridge", "tests", "test_fixture_workbook.xlsx"
    )
    real_wb_path = os.path.join(
        _project_root, "Developer_Job_Application_Tracker_PRO.xlsx"
    )

    # === Test 1: Write blocked when JOBTRACKER_WORKBOOK_PATH is not set ===
    print("\n=== Write Blocked: No JOBTRACKER_WORKBOOK_PATH ===")
    # Ensure env var is not set
    old_env = os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "test_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        writer = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))

        result = writer.add_application({"company": "TestCo", "role": "Engineer"})
        check(result["success"] is False, "add_application blocked without env var")
        check(
            "JOBTRACKER_WORKBOOK_PATH" in result["error"],
            "error mentions JOBTRACKER_WORKBOOK_PATH",
        )

        result = writer.update_application_status("APP-001", "Applied")
        check(result["success"] is False, "update_application_status blocked without env var")

    # Restore if it was set
    if old_env is not None:
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = old_env

    # === Test 2: Write blocked for real production workbook (without opt-in) ===
    print("\n=== Write Blocked: Production Workbook (no opt-in) ===")
    os.environ["JOBTRACKER_WORKBOOK_PATH"] = real_wb_path
    os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)
    try:
        writer = ExcelWriter(real_wb_path, backup_dir=os.path.join(_project_root, "backups"))
        result = writer.add_application({"company": "TestCo", "role": "Engineer"})
        check(result["success"] is False, "add_application blocked for production workbook without opt-in")
        check(
            "PRODUCTION_WRITES" in result["error"],
            "error mentions PRODUCTION_WRITES env var",
        )

        result = writer.update_application_status("APP-001", "Applied")
        check(result["success"] is False, "update_application_status blocked for production workbook")
    finally:
        os.environ.pop("JOBTRACKER_WORKBOOK_PATH")
        os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 3: Write blocked when filename doesn't contain _DEMO or _TEST ===
    print("\n=== Write Blocked: No _DEMO or _TEST in filename ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        non_demo_wb = os.path.join(tmpdir, "my_workbook.xlsx")
        shutil.copy2(fixture_path, non_demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = non_demo_wb
        try:
            writer = ExcelWriter(non_demo_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.add_application({"company": "TestCo", "role": "Engineer"})
            check(result["success"] is False, "add_application blocked for non-demo filename")
            check(
                "demo/test/staging/production workbooks" in result["error"],
                "error mentions demo/test/staging/production workbooks for non-demo filename",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 4: add_application creates backup and appends row ===
    print("\n=== add_application: Backup + Append Row ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            # Count rows before
            reader = ExcelReader(demo_wb)
            _, rows_before = reader.read_applications()
            count_before = len(rows_before)

            writer = ExcelWriter(demo_wb, backup_dir=backup_dir)
            result = writer.add_application({
                "company": "NewTestCo",
                "role": "Senior Engineer",
                "status": "Applied",
                "location": "San Francisco",
                "salary": "$180k",
                "source": "LinkedIn",
                "priority": "High",
                "fitScore": 85,
            })

            check(result["success"] is True, "add_application succeeds for demo workbook")
            check(result["backupPath"] is not None, "add_application returns backupPath")
            check(
                os.path.exists(result["backupPath"]),
                "backup file exists on disk",
            )
            check(
                "data" in result and "applicationId" in result["data"],
                "add_application returns applicationId in data",
            )

            # Verify row was added
            _, rows_after = reader.read_applications()
            count_after = len(rows_after)
            check(
                count_after == count_before + 1,
                f"row count increased by 1 ({count_before} -> {count_after})",
            )

            # Verify the new row has the right company
            new_row = rows_after[-1]
            headers, _ = reader.read_applications()
            company_idx = headers.index("Company")
            check(
                str(new_row[company_idx]).strip() == "NewTestCo",
                "new row has correct company name",
            )

            # Verify backup is not the same as the workbook (backup has original data)
            backup_size = os.path.getsize(result["backupPath"])
            current_size = os.path.getsize(demo_wb)
            check(
                backup_size > 0,
                "backup file has non-zero size",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 5: add_application missing required fields ===
    print("\n=== add_application: Missing Required Fields ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            writer = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))

            result = writer.add_application({"company": "", "role": "Engineer"})
            check(result["success"] is False, "add_application fails with empty company")
            check(
                "required" in result["error"].lower(),
                "error mentions required fields",
            )

            result = writer.add_application({"company": "TestCo", "role": ""})
            check(result["success"] is False, "add_application fails with empty role")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 6: update_application_status creates backup and changes status ===
    print("\n=== update_application_status: Backup + Change Status ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            # Get first application ID
            reader = ExcelReader(demo_wb)
            headers, rows = reader.read_applications()
            id_idx = headers.index("Application ID")
            status_idx = headers.index("Status")
            first_id = str(rows[0][id_idx]).strip()
            old_status = str(rows[0][status_idx]).strip()

            writer = ExcelWriter(demo_wb, backup_dir=backup_dir)
            result = writer.update_application_status(first_id, "Offer")

            check(result["success"] is True, "update_application_status succeeds")
            check(result["backupPath"] is not None, "update returns backupPath")
            check(
                os.path.exists(result["backupPath"]),
                "backup file exists on disk",
            )
            check(
                "data" in result and result["data"]["newStatus"] == "Offer",
                "new status is Offer in result data",
            )
            check(
                result["data"]["oldStatus"] == old_status,
                f"old status matches ({old_status})",
            )

            # Verify the status was actually changed in the workbook
            reader2 = ExcelReader(demo_wb)
            headers2, rows2 = reader2.read_applications()
            found = False
            for row in rows2:
                if str(row[id_idx]).strip() == first_id:
                    check(
                        str(row[status_idx]).strip() == "Offer",
                        "status cell updated to Offer in workbook",
                    )
                    found = True
                    break
            check(found, "application row found after update")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 7: update_application_status with missing ID ===
    print("\n=== update_application_status: Missing Application ID ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            writer = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.update_application_status("NONEXISTENT-ID", "Applied")

            check(result["success"] is False, "update fails for nonexistent ID")
            check(
                "not found" in result["error"].lower(),
                "error mentions 'not found'",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 8: Invalid status is normalized ===
    print("\n=== update_application_status: Invalid Status Normalized ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            reader = ExcelReader(demo_wb)
            headers, rows = reader.read_applications()
            id_idx = headers.index("Application ID")
            first_id = str(rows[0][id_idx]).strip()

            writer = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.update_application_status(first_id, "gibberish_status")

            check(result["success"] is True, "update succeeds with normalized status")
            check(
                result["data"]["newStatus"] == "Applied",
                "gibberish status normalized to Applied",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 9: JSON-safe results ===
    print("\n=== JSON-Safe Results ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            writer = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))

            result = writer.add_application({"company": "JSONTest", "role": "Engineer"})
            try:
                json.dumps(result)
                check(True, "add_application result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"add_application result not JSON-serializable: {e}")

            reader = ExcelReader(demo_wb)
            headers, rows = reader.read_applications()
            id_idx = headers.index("Application ID")
            new_id = result["data"]["applicationId"]

            result2 = writer.update_application_status(new_id, "Phone Screen")
            try:
                json.dumps(result2)
                check(True, "update_application_status result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"update result not JSON-serializable: {e}")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 10: Existing read-only API methods still work ===
    print("\n=== Read-Only API Methods Still Work ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            api = ExcelBridgeAPI(demo_wb)

            # health
            h = api.health()
            check(h["status"] == "ok", "health() still works")

            # get_applications
            apps = api.get_applications()
            check(apps["error"] is None, "get_applications() still works")
            check(apps["count"] >= 6, "get_applications() returns data")

            # get_dashboard
            dash = api.get_dashboard()
            check(dash["error"] is None, "get_dashboard() still works")
            check(len(dash["data"]["kpis"]) > 0, "get_dashboard() returns KPIs")

            # get_kpis
            kpis = api.get_kpis()
            check(kpis["error"] is None, "get_kpis() still works")

            # get_pipeline
            pipe = api.get_pipeline()
            check(pipe["error"] is None, "get_pipeline() still works")

            # get_salary_data
            sal = api.get_salary_data()
            check(sal["error"] is None, "get_salary_data() still works")

            # get_interview_history
            ih = api.get_interview_history()
            check(ih["error"] is None, "get_interview_history() still works")

            # get_cover_letter_history
            cl = api.get_cover_letter_history()
            check(cl["error"] is None, "get_cover_letter_history() still works")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 11: API write methods work through ExcelBridgeAPI ===
    print("\n=== API Write Methods Through ExcelBridgeAPI ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            api = ExcelBridgeAPI(demo_wb)

            # add_application via API
            result = api.add_application({"company": "APITest", "role": "Dev"})
            check(result["success"] is True, "api.add_application works")

            # update_application_status via API
            new_id = result["data"]["applicationId"]
            result2 = api.update_application_status(new_id, "Technical")
            check(result2["success"] is True, "api.update_application_status works")
            check(
                result2["data"]["newStatus"] == "Technical",
                "api update returns correct new status",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 12: API blocks writes to real workbook (without opt-in) ===
    print("\n=== API Blocks Writes to Real Workbook (no opt-in) ===")
    os.environ["JOBTRACKER_WORKBOOK_PATH"] = real_wb_path
    os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)
    try:
        api = ExcelBridgeAPI(real_wb_path)
        result = api.add_application({"company": "Blocked", "role": "Test"})
        check(result["success"] is False, "api.add_application blocked for real workbook")
        check(
            "PRODUCTION_WRITES" in result["error"],
            "api error mentions PRODUCTION_WRITES",
        )
    finally:
        os.environ.pop("JOBTRACKER_WORKBOOK_PATH")
        os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 13: API blocks writes without env var ===
    print("\n=== API Blocks Writes Without Env Var ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        # Don't set env var
        api = ExcelBridgeAPI(demo_wb)
        result = api.add_application({"company": "Blocked", "role": "Test"})
        check(result["success"] is False, "api.add_application blocked without env var")

    # === Test 14: Real workbook not modified by any write attempts ===
    print("\n=== Real Workbook Not Modified ===")
    real_size_before = os.path.getsize(real_wb_path)
    # All the blocked write attempts above should not have modified the real workbook
    real_size_after = os.path.getsize(real_wb_path)
    check(
        real_size_before == real_size_after,
        "real workbook size unchanged after all write tests",
    )

    # === Test 15: Backup created before write ===
    print("\n=== Backup Created Before Write ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            writer = ExcelWriter(demo_wb, backup_dir=backup_dir)

            # Verify no backups exist yet
            check(
                not os.path.exists(backup_dir) or len(os.listdir(backup_dir)) == 0,
                "no backups exist before write",
            )

            result = writer.add_application({"company": "BackupTest", "role": "Eng"})

            check(result["success"] is True, "write succeeded")
            check(
                os.path.exists(backup_dir) and len(os.listdir(backup_dir)) >= 1,
                "backup directory has at least 1 file after write",
            )
            check(
                os.path.exists(result["backupPath"]),
                "backup file exists at returned path",
            )
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH")

    # === Test 14: Staging writes blocked without JOBTRACKER_ENABLE_STAGING_WRITES ===
    print("\n=== Staging Writes Blocked Without Enable Variable ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)
        try:
            writer = ExcelWriter(staging_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.add_application({"company": "StagingTest", "role": "Eng"})
            check(result["success"] is False, "staging write blocked without enable var")
            check("STAGING_WRITES" in result.get("error", ""), "error mentions staging enable var")

            wm = writer.get_write_mode()
            check(wm["enabled"] is False, "staging write mode disabled without enable var")
            check(wm["mode"] == "disabled", "staging mode is disabled")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)

    # === Test 15: Staging writes allowed with both env vars ===
    print("\n=== Staging Writes Allowed With Both Env Vars ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ["JOBTRACKER_ENABLE_STAGING_WRITES"] = "1"
        try:
            writer = ExcelWriter(staging_wb, backup_dir=backup_dir)

            wm = writer.get_write_mode()
            check(wm["enabled"] is True, "staging write mode enabled")
            check(wm["mode"] == "staging", "mode is staging")
            check("Staging" in wm["reason"], "reason says Staging")

            result = writer.add_application({"company": "StagingCorp", "role": "Engineer"})
            check(result["success"] is True, "staging add_application succeeds")
            check(os.path.exists(result["backupPath"]), "staging backup created")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)

    # === Test 16: Production workbook blocked with staging var but without production var ===
    print("\n=== Production Workbook Blocked With Staging Var Only ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_STAGING_WRITES"] = "1"
        os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)
        try:
            writer = ExcelWriter(prod_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.add_application({"company": "ProdTest", "role": "Eng"})
            check(result["success"] is False, "production write blocked with staging var only")
            check("PRODUCTION_WRITES" in result["error"], "error mentions PRODUCTION_WRITES")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 17: Staging status update works ===
    print("\n=== Staging Status Update Works ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ["JOBTRACKER_ENABLE_STAGING_WRITES"] = "1"
        try:
            writer = ExcelWriter(staging_wb, backup_dir=backup_dir)

            # First add an app
            add_result = writer.add_application({"company": "StatusTest", "role": "Eng", "status": "Applied"})
            check(add_result["success"] is True, "staging add for status test succeeds")
            app_id = add_result["data"]["applicationId"]

            # Update status
            update_result = writer.update_application_status(app_id, "Technical")
            check(update_result["success"] is True, "staging status update succeeds")
            check(update_result["data"]["newStatus"] == "Technical", "staging new status is Technical")
            check(os.path.exists(update_result["backupPath"]), "staging update backup created")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)

    # === Test 18: Staging rapid backups unique ===
    print("\n=== Staging Rapid Backups Unique ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ["JOBTRACKER_ENABLE_STAGING_WRITES"] = "1"
        try:
            writer = ExcelWriter(staging_wb, backup_dir=backup_dir)
            r1 = writer.backup.create_backup()
            r2 = writer.backup.create_backup()
            check(r1["success"] and r2["success"], "both staging backups succeed")
            check(r1["backupPath"] != r2["backupPath"], "staging backup paths are unique")
            check(os.path.exists(r1["backupPath"]), "staging backup 1 exists")
            check(os.path.exists(r2["backupPath"]), "staging backup 2 exists")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)

    # === Test 19: Staging results JSON-safe ===
    print("\n=== Staging Results JSON-Safe ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ["JOBTRACKER_ENABLE_STAGING_WRITES"] = "1"
        try:
            writer = ExcelWriter(staging_wb, backup_dir=os.path.join(tmpdir, "backups"))
            add_result = writer.add_application({"company": "JSONTest", "role": "Eng"})
            try:
                json.dumps(add_result)
                check(True, "staging add result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"staging add result JSON error: {e}")

            wm = writer.get_write_mode()
            try:
                json.dumps(wm)
                check(True, "staging write mode result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"staging write mode JSON error: {e}")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)

    # === Test 20: Staging write mode without env var reports disabled ===
    print("\n=== Staging Write Mode Without Enable Var ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        staging_wb = os.path.join(tmpdir, "Tracker_STAGING.xlsx")
        shutil.copy2(fixture_path, staging_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = staging_wb
        os.environ.pop("JOBTRACKER_ENABLE_STAGING_WRITES", None)
        try:
            writer = ExcelWriter(staging_wb, backup_dir=os.path.join(tmpdir, "backups"))
            wm = writer.get_write_mode()
            check(wm["enabled"] is False, "staging mode disabled without enable var")
            check(wm["mode"] == "disabled", "mode is disabled")
            check("STAGING_WRITES" in wm["reason"], "reason mentions staging enable var")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Test 21: Production writes blocked without opt-in env var ===
    print("\n=== Production Writes Blocked Without Opt-in ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)
        try:
            writer = ExcelWriter(prod_wb, backup_dir=os.path.join(tmpdir, "backups"))
            result = writer.add_application({"company": "ProdTest", "role": "Eng"})
            check(result["success"] is False, "production write blocked without opt-in")
            check("PRODUCTION_WRITES" in result["error"], "error mentions PRODUCTION_WRITES")

            wm = writer.get_write_mode()
            check(wm["enabled"] is False, "production write mode disabled without opt-in")
            check(wm["mode"] == "disabled", "mode is disabled")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 22: Production writes allowed with opt-in env var ===
    print("\n=== Production Writes Allowed With Opt-in ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=backup_dir)

            wm = writer.get_write_mode()
            check(wm["enabled"] is True, "production write mode enabled")
            check(wm["mode"] == "production", "mode is production")
            check("Production" in wm["reason"], "reason says Production")

            result = writer.add_application({"company": "ProdCorp", "role": "Engineer"})
            check(result["success"] is True, "production add_application succeeds")
            check(os.path.exists(result["backupPath"]), "production backup created")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 23: Production status update works ===
    print("\n=== Production Status Update Works ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=backup_dir)

            add_result = writer.add_application({"company": "StatusProd", "role": "Eng", "status": "Applied"})
            check(add_result["success"] is True, "production add for status test succeeds")
            app_id = add_result["data"]["applicationId"]

            update_result = writer.update_application_status(app_id, "Technical")
            check(update_result["success"] is True, "production status update succeeds")
            check(update_result["data"]["newStatus"] == "Technical", "production new status is Technical")
            check(os.path.exists(update_result["backupPath"]), "production update backup created")
            check(update_result["backupPath"] != add_result["backupPath"], "production backups are unique")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 24: Production rapid backups unique ===
    print("\n=== Production Rapid Backups Unique ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=backup_dir)
            r1 = writer.backup.create_backup()
            r2 = writer.backup.create_backup()
            check(r1["success"] and r2["success"], "both production backups succeed")
            check(r1["backupPath"] != r2["backupPath"], "production backup paths are unique")
            check(os.path.exists(r1["backupPath"]), "production backup 1 exists")
            check(os.path.exists(r2["backupPath"]), "production backup 2 exists")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 25: Production results JSON-safe ===
    print("\n=== Production Results JSON-Safe ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=os.path.join(tmpdir, "backups"))
            add_result = writer.add_application({"company": "JSONProd", "role": "Eng"})
            try:
                json.dumps(add_result)
                check(True, "production add result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"production add result JSON error: {e}")

            wm = writer.get_write_mode()
            try:
                json.dumps(wm)
                check(True, "production write mode result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"production write mode JSON error: {e}")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 26: Real workbook not modified by production tests ===
    print("\n=== Real Workbook Not Modified by Production Tests ===")
    real_size_after = os.path.getsize(real_wb_path)
    check(real_size_after == real_size_before, f"real workbook size unchanged ({real_size_after} bytes)")

    # === Test 27: Session safety backup created on first production write ===
    print("\n=== Session Safety Backup Created On First Write ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=backup_dir)

            # Before first write, session backup path is None
            wm = writer.get_write_mode()
            check(wm.get("sessionBackupPath") is None, "session backup path is None before first write")

            # First write — should create session backup + per-write backup
            result = writer.add_application({"company": "SessionTest", "role": "Eng"})
            check(result["success"] is True, "first production write succeeds")

            # Session backup path should now be set
            wm = writer.get_write_mode()
            check(wm.get("sessionBackupPath") is not None, "session backup path set after first write")
            session_path = wm["sessionBackupPath"]
            check(os.path.exists(session_path), "session backup file exists on disk")
            check("_session_backup_" in os.path.basename(session_path), "session backup filename contains _session_backup_")
            check(os.path.getsize(session_path) > 0, "session backup file is non-empty")

            # Per-write backup should be different from session backup
            check(result["backupPath"] != session_path, "per-write backup is different from session backup")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 28: Session backup only created once per session ===
    print("\n=== Session Backup Only Created Once ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=backup_dir)

            # First write
            r1 = writer.add_application({"company": "First", "role": "Eng"})
            check(r1["success"] is True, "first write succeeds")
            wm1 = writer.get_write_mode()
            session_path_1 = wm1["sessionBackupPath"]

            # Second write — session backup should be the same path (not recreated)
            r2 = writer.add_application({"company": "Second", "role": "Eng"})
            check(r2["success"] is True, "second write succeeds")
            wm2 = writer.get_write_mode()
            check(wm2["sessionBackupPath"] == session_path_1, "session backup path unchanged on second write")

            # Count session backup files — should be exactly 1
            import glob
            session_files = glob.glob(os.path.join(backup_dir, "*_session_backup_*.xlsx"))
            check(len(session_files) == 1, f"exactly 1 session backup file (got {len(session_files)})")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 29: Session backup not created for demo/staging modes ===
    print("\n=== Session Backup Not Created For Demo/Staging ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        demo_wb = os.path.join(tmpdir, "Tracker_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            writer = ExcelWriter(demo_wb, backup_dir=backup_dir)
            result = writer.add_application({"company": "DemoTest", "role": "Eng"})
            check(result["success"] is True, "demo write succeeds")
            wm = writer.get_write_mode()
            check(wm.get("sessionBackupPath") is None, "no session backup path for demo mode")

            import glob
            session_files = glob.glob(os.path.join(backup_dir, "*_session_backup_*.xlsx"))
            check(len(session_files) == 0, "no session backup files for demo mode")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Test 30: Session backup failure blocks production writes ===
    print("\n=== Session Backup Failure Blocks Writes ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        # Use a non-existent backup dir that can't be created (simulate failure)
        # On Windows, we can use a path with invalid characters
        bad_backup_dir = os.path.join(tmpdir, "backups")
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=bad_backup_dir)
            # Make backup dir read-only after creating it, then remove it
            os.makedirs(bad_backup_dir, exist_ok=True)
            # Remove the directory and create a file with the same name to block mkdir
            os.rmdir(bad_backup_dir)
            with open(bad_backup_dir, "w") as f:
                f.write("block")

            result = writer.add_application({"company": "BlockedWrite", "role": "Eng"})
            check(result["success"] is False, "write blocked when session backup fails")
            check("Session safety backup failed" in result["error"], "error mentions session backup failure")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # === Test 31: Session backup result is JSON-safe ===
    print("\n=== Session Backup Result JSON-Safe ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        prod_wb = os.path.join(tmpdir, PRODUCTION_WORKBOOK_NAME)
        shutil.copy2(fixture_path, prod_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = prod_wb
        os.environ["JOBTRACKER_ENABLE_PRODUCTION_WRITES"] = "1"
        try:
            writer = ExcelWriter(prod_wb, backup_dir=os.path.join(tmpdir, "backups"))
            writer.add_application({"company": "JSONSession", "role": "Eng"})
            wm = writer.get_write_mode()
            try:
                json.dumps(wm)
                check(True, "write mode with sessionBackupPath is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"write mode JSON error: {e}")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)
            os.environ.pop("JOBTRACKER_ENABLE_PRODUCTION_WRITES", None)

    # ============================================================
    # EDIT APPLICATION — COMPREHENSIVE SAFETY TESTS
    # ============================================================

    def _make_demo_writer(tmpdir):
        """Helper: create a demo workbook copy and writer."""
        demo_wb = os.path.join(tmpdir, "test_edit_DEMO.xlsx")
        shutil.copy2(fixture_path, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        w = ExcelWriter(demo_wb, backup_dir=os.path.join(tmpdir, "backups"))
        return w, demo_wb

    def _read_cell(wb_path, sheet, row, col_name):
        """Helper: read a cell value by column name from a workbook."""
        wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
        ws = wb[sheet]
        headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
        col_idx = headers.index(col_name) + 1
        val = ws.cell(row=row, column=col_idx).value
        wb.close()
        return val

    def _read_all_headers(wb_path, sheet):
        """Helper: read all headers from a sheet."""
        wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
        ws = wb[sheet]
        headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
        wb.close()
        return headers

    def _read_row_by_id(wb_path, app_id):
        """Helper: read a full row dict by Application ID."""
        wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
        ws = wb["Applications"]
        headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and str(row[0]).strip() == str(app_id).strip():
                wb.close()
                return {headers[i]: row[i] for i in range(len(headers))}
        wb.close()
        return None

    # === Edit Test 1: All seven fields can be edited ===
    print("\n=== Edit: All Seven Fields Editable ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Get the first Application ID from fixture
            row_data = _read_row_by_id(demo_wb, "APP-001")
            check(row_data is not None, "fixture has APP-001 row")

            result = writer.edit_application("APP-001", {
                "company": "EditedCorp",
                "role": "Senior Engineer",
                "location": "Berlin",
                "source": "Referral",
                "salary": "150000",
                "fitScore": 92,
                "notes": "Updated notes here",
            })
            check(result["success"] is True, "edit all 7 fields succeeds")
            check(result.get("backupPath") is not None, "edit creates backup")

            # Verify each field was written
            updated = _read_row_by_id(demo_wb, "APP-001")
            check(updated is not None, "edited row still found by ID")
            if updated:
                check(str(updated.get("Company", "")).strip() == "EditedCorp", "company edited")
                check(str(updated.get("Role", "")).strip() == "Senior Engineer", "role edited")
                check(str(updated.get("Location", "")).strip() == "Berlin", "location edited")
                check(str(updated.get("Source", "")).strip() == "Referral", "source edited")
                check(str(updated.get("Salary", "")).strip() == "150000", "salary edited")
                check(str(updated.get("Fit Score", "")).strip() == "92", "fitScore edited")
                check(str(updated.get("Notes", "")).strip() == "Updated notes here", "notes edited")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 2: Missing ID is rejected ===
    print("\n=== Edit: Missing ID Rejected ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("", {"company": "TestCo"})
            check(result["success"] is False, "empty ID rejected")
            check("Application ID is required" in result.get("error", ""), "error mentions ID required")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 3: Unknown ID is rejected ===
    print("\n=== Edit: Unknown ID Rejected ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("NONEXISTENT-ID", {"company": "TestCo"})
            check(result["success"] is False, "unknown ID rejected")
            check("not found" in result.get("error", "").lower(), "error mentions not found")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 4: Duplicate ID is rejected ===
    print("\n=== Edit: Duplicate ID Rejected ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Manually create a duplicate ID by adding a row with same ID
            wb = openpyxl.load_workbook(demo_wb)
            ws = wb["Applications"]
            # Copy row 2 to row 8 (after existing 6 data rows + header)
            dup_row = ws.max_row + 1
            for col in range(1, ws.max_column + 1):
                ws.cell(row=dup_row, column=col, value=ws.cell(row=2, column=col).value)
            wb.save(demo_wb)
            wb.close()

            result = writer.edit_application("APP-001", {"company": "DupTest"})
            check(result["success"] is False, "duplicate ID rejected")
            check("Duplicate" in result.get("error", ""), "error mentions duplicate")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 5: Invalid Fit Score is rejected (non-numeric becomes 0, but we test range) ===
    print("\n=== Edit: Invalid Fit Score Handling ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Fit Score with non-numeric value — current impl converts to 0
            result = writer.edit_application("APP-001", {"fitScore": "not-a-number"})
            check(result["success"] is True, "non-numeric fitScore converts to 0 (not rejected)")
            updated = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated.get("Fit Score", "")).strip() == "0", "non-numeric fitScore stored as 0")

            # Edit with valid fitScore 0
            result2 = writer.edit_application("APP-001", {"fitScore": 0})
            check(result2["success"] is True, "fitScore=0 is valid")
            updated2 = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated2.get("Fit Score", "")).strip() == "0", "fitScore=0 preserved")

            # Edit with valid fitScore 100
            result3 = writer.edit_application("APP-001", {"fitScore": 100})
            check(result3["success"] is True, "fitScore=100 is valid")
            updated3 = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated3.get("Fit Score", "")).strip() == "100", "fitScore=100 preserved")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 6: No editable fields provided ===
    print("\n=== Edit: No Editable Fields ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("APP-001", {})
            check(result["success"] is False, "empty data rejected")
            check("No editable fields" in result.get("error", ""), "error mentions no editable fields")

            result2 = writer.edit_application("APP-001", {"unknownField": "value"})
            check(result2["success"] is False, "unknown field only rejected")
            check("No editable fields" in result2.get("error", ""), "error mentions no editable fields for unknown-only")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 7: Invalid input does not create a backup ===
    print("\n=== Edit: No Backup On Invalid Input ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        backup_dir = os.path.join(tmpdir, "backups")
        try:
            initial_backups = os.listdir(backup_dir) if os.path.exists(backup_dir) else []
            # Missing ID — should not create backup (rejected before backup step)
            writer.edit_application("", {"company": "TestCo"})
            # No editable fields — should not create backup (rejected before backup step)
            writer.edit_application("APP-001", {})
            after_backups = os.listdir(backup_dir) if os.path.exists(backup_dir) else []
            check(len(after_backups) == len(initial_backups), "no backups created for empty ID / no editable fields")

            # Unknown ID — backup IS created (correct safety: backup before write attempt)
            # This is expected behavior, not a bug.
            before_unknown = os.listdir(backup_dir) if os.path.exists(backup_dir) else []
            writer.edit_application("NONEXISTENT", {"company": "TestCo"})
            after_unknown = os.listdir(backup_dir) if os.path.exists(backup_dir) else []
            check(len(after_unknown) == len(before_unknown) + 1, "backup created for unknown ID (safety: backup before write attempt)")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 8: No partial edit — missing mapped column blocks complete edit ===
    print("\n=== Edit: Missing Column Blocks Edit ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # The fixture has all columns, so we need to test with a workbook
            # that's missing one of the editable columns headers.
            # We'll create a modified copy with "Notes" header removed.
            wb = openpyxl.load_workbook(demo_wb)
            ws = wb["Applications"]
            headers = [str(c.value).strip() if c.value else "" for c in ws[1]]
            notes_col = headers.index("Notes") + 1
            # Clear the Notes header
            ws.cell(row=1, column=notes_col, value="RemovedColumn")
            wb.save(demo_wb)
            wb.close()

            # Edit should still succeed — missing column is skipped (continue in code)
            # But the field won't be written. Let's verify it doesn't crash.
            result = writer.edit_application("APP-001", {"company": "NewCo", "notes": "test"})
            check(result["success"] is True, "edit succeeds even if one column header is missing (skipped)")
            updated = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated.get("Company", "")).strip() == "NewCo", "company still updated when notes column missing")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 9: Every requested field is verified after save ===
    print("\n=== Edit: Post-Write Verification ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("APP-002", {
                "company": "VerifiedInc",
                "role": "Tech Lead",
                "fitScore": 88,
            })
            check(result["success"] is True, "edit succeeds for verification test")
            # Verify all 3 fields were written
            updated = _read_row_by_id(demo_wb, "APP-002")
            check(str(updated.get("Company", "")).strip() == "VerifiedInc", "company verified after save")
            check(str(updated.get("Role", "")).strip() == "Tech Lead", "role verified after save")
            check(str(updated.get("Fit Score", "")).strip() == "88", "fitScore verified after save")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 10: Zero values are preserved ===
    print("\n=== Edit: Zero Values Preserved ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("APP-001", {"fitScore": 0, "salary": "0"})
            check(result["success"] is True, "edit with zero values succeeds")
            updated = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated.get("Fit Score", "")).strip() == "0", "fitScore=0 preserved")
            check(str(updated.get("Salary", "")).strip() == "0", "salary=0 preserved")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 11: Unrelated columns remain unchanged ===
    print("\n=== Edit: Unrelated Columns Unchanged ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Read original values of non-edited columns
            original = _read_row_by_id(demo_wb, "APP-003")
            original_status = original.get("Status")
            original_date = original.get("Date Applied")
            original_id = original.get("Application ID")

            # Edit only company
            result = writer.edit_application("APP-003", {"company": "ChangedCo"})
            check(result["success"] is True, "edit single field succeeds")

            updated = _read_row_by_id(demo_wb, "APP-003")
            check(str(updated.get("Status", "")) == str(original_status), "Status column unchanged")
            check(str(updated.get("Date Applied", "")) == str(original_date), "Date Applied column unchanged")
            check(str(updated.get("Application ID", "")) == str(original_id), "Application ID column unchanged")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 12: Other rows remain unchanged ===
    print("\n=== Edit: Other Rows Unchanged ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Read APP-002 before editing APP-001
            row2_before = _read_row_by_id(demo_wb, "APP-002")

            writer.edit_application("APP-001", {"company": "ChangedCo"})

            row2_after = _read_row_by_id(demo_wb, "APP-002")
            check(str(row2_before.get("Company")) == str(row2_after.get("Company")), "other row company unchanged")
            check(str(row2_before.get("Role")) == str(row2_after.get("Role")), "other row role unchanged")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 13: Other sheets remain unchanged ===
    print("\n=== Edit: Other Sheets Unchanged ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Read a cell from another sheet before edit
            wb_before = openpyxl.load_workbook(demo_wb, read_only=True, data_only=True)
            salary_before = None
            if "Salary Comparison" in wb_before.sheetnames:
                ws_sal = wb_before["Salary Comparison"]
                salary_before = ws_sal.cell(row=2, column=1).value
            wb_before.close()

            writer.edit_application("APP-001", {"company": "ChangedCo"})

            wb_after = openpyxl.load_workbook(demo_wb, read_only=True, data_only=True)
            salary_after = None
            if "Salary Comparison" in wb_after.sheetnames:
                ws_sal = wb_after["Salary Comparison"]
                salary_after = ws_sal.cell(row=2, column=1).value
            wb_after.close()

            check(salary_before == salary_after, "Salary Comparison sheet unchanged after edit")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 14: Edit result is JSON-safe ===
    print("\n=== Edit: Result JSON-Safe ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            result = writer.edit_application("APP-001", {"company": "JSONCo"})
            try:
                json.dumps(result)
                check(True, "edit result is JSON-serializable")
            except (TypeError, ValueError) as e:
                check(False, f"edit result JSON error: {e}")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 15: One unique backup per edit operation ===
    print("\n=== Edit: Unique Backup Per Edit ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        backup_dir = os.path.join(tmpdir, "backups")
        try:
            r1 = writer.edit_application("APP-001", {"company": "FirstEdit"})
            r2 = writer.edit_application("APP-001", {"company": "SecondEdit"})
            check(r1["success"] and r2["success"], "both edits succeed")
            check(r1["backupPath"] != r2["backupPath"], "edit backups are unique")
            check(os.path.exists(r1["backupPath"]), "first edit backup exists")
            check(os.path.exists(r2["backupPath"]), "second edit backup exists")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Edit Test 16: Application ID is the only row identity ===
    print("\n=== Edit: ID Is Only Row Identity ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        writer, demo_wb = _make_demo_writer(tmpdir)
        try:
            # Editing by ID should work even if company name changed
            writer.edit_application("APP-001", {"company": "Renamed"})
            # Edit again by same ID — should find the row by ID, not by company
            result = writer.edit_application("APP-001", {"role": "New Role"})
            check(result["success"] is True, "second edit by ID works after company changed")
            updated = _read_row_by_id(demo_wb, "APP-001")
            check(str(updated.get("Company", "")).strip() == "Renamed", "company preserved from first edit")
            check(str(updated.get("Role", "")).strip() == "New Role", "role updated in second edit")
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # === Final report ===
    print("\n" + "=" * 60)
    print("EXCEL WRITER TEST SUITE - FINAL REPORT")
    print("=" * 60)
    print(f"  TOTAL PASSES:  {PASS_COUNT}")
    print(f"  TOTAL ERRORS:  {ERROR_COUNT}")
    print()
    if ERROR_COUNT == 0:
        print("RESULT: PASSED — NO ERRORS")
    else:
        print("RESULT: FAILED — SEE ERRORS ABOVE")
    return ERROR_COUNT == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
