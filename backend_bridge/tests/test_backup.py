"""Tests for ExcelBackup helper module.

Verifies:
- Backup is created from a fixture/demo workbook
- Backup file exists and has non-zero size
- Backup does not modify source workbook
- Missing workbook returns safe error
- Invalid backup directory handled safely
- JSON-safe result format
- No workbook save/write operation happens
"""
import os
import sys
import shutil
import tempfile
import json

# Ensure project root is on sys.path
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend_bridge.excel_backup import ExcelBackup

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

    # === Test 1: Create backup from fixture workbook ===
    print("\n=== Backup Creation ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(fixture_path, backup_dir=backup_dir)
        result = eb.create_backup()

        check(result["success"] is True, "backup creation succeeds")
        check(result["backupPath"] is not None, "backupPath is not None")
        check(result["error"] is None, "error is None")
        check(os.path.exists(result["backupPath"]), "backup file exists on disk")
        check(
            os.path.getsize(result["backupPath"]) > 0,
            "backup file has non-zero size",
        )
        check(
            os.path.getsize(result["backupPath"]) == os.path.getsize(fixture_path),
            "backup file size matches source",
        )

    # === Test 2: Backup does not modify source ===
    print("\n=== Source Workbook Not Modified ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy fixture to temp so we can compare
        temp_wb = os.path.join(tmpdir, "test_wb.xlsx")
        shutil.copy2(fixture_path, temp_wb)
        original_size = os.path.getsize(temp_wb)
        original_mtime = os.path.getmtime(temp_wb)

        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(temp_wb, backup_dir=backup_dir)
        result = eb.create_backup()

        check(result["success"] is True, "backup succeeds for temp workbook")
        check(
            os.path.getsize(temp_wb) == original_size,
            "source workbook size unchanged after backup",
        )
        # mtime should not change (copy2 on source doesn't touch it)
        check(
            os.path.getmtime(temp_wb) == original_mtime,
            "source workbook mtime unchanged after backup",
        )

    # === Test 3: Missing workbook ===
    print("\n=== Missing Workbook ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(os.path.join(tmpdir, "nonexistent.xlsx"), backup_dir=backup_dir)
        result = eb.create_backup()

        check(result["success"] is False, "missing workbook returns success=False")
        check(result["backupPath"] is None, "missing workbook returns backupPath=None")
        check(result["error"] is not None, "missing workbook returns error message")
        check(
            "not found" in result["error"].lower(),
            "error message mentions 'not found'",
        )

    # === Test 4: Invalid backup directory ===
    print("\n=== Invalid Backup Directory ===")
    # Use a path that cannot be created (e.g., inside a file)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a file and try to use it as a directory
        blocking_file = os.path.join(tmpdir, "blocker")
        with open(blocking_file, "w") as f:
            f.write("not a directory")

        backup_dir = os.path.join(blocking_file, "backups")
        eb = ExcelBackup(fixture_path, backup_dir=backup_dir)
        result = eb.create_backup()

        check(result["success"] is False, "invalid backup dir returns success=False")
        check(result["backupPath"] is None, "invalid backup dir returns backupPath=None")
        check(result["error"] is not None, "invalid backup dir returns error message")

    # === Test 5: JSON-safe result ===
    print("\n=== JSON-Safe Result ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(fixture_path, backup_dir=backup_dir)
        result = eb.create_backup()

        try:
            json_str = json.dumps(result)
            check(True, "create_backup result is JSON-serializable")
        except (TypeError, ValueError) as e:
            check(False, f"create_backup result is JSON-serializable: {e}")

        # Also test list_backups
        list_result = eb.list_backups()
        try:
            json_str = json.dumps(list_result)
            check(True, "list_backups result is JSON-serializable")
        except (TypeError, ValueError) as e:
            check(False, f"list_backups result is JSON-serializable: {e}")

    # === Test 6: No save/write on ExcelBackup class ===
    print("\n=== Read-Only Safety: No Write Methods ===")
    eb = ExcelBackup(fixture_path)
    check(
        not hasattr(eb, "save"),
        "ExcelBackup has no save method",
    )
    check(
        not hasattr(eb, "write"),
        "ExcelBackup has no write method",
    )
    check(
        not hasattr(eb, "write_cell"),
        "ExcelBackup has no write_cell method",
    )
    check(
        not hasattr(eb, "modify_workbook"),
        "ExcelBackup has no modify_workbook method",
    )

    # === Test 7: list_backups ===
    print("\n=== List Backups ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(fixture_path, backup_dir=backup_dir)

        # Before any backup
        result = eb.list_backups()
        check(result["success"] is True, "list_backups succeeds on empty dir")
        check(result["count"] == 0, "list_backups returns 0 for empty dir")

        # Create two backups
        eb.create_backup()
        import time
        time.sleep(1)  # Ensure different timestamps
        eb.create_backup()

        result = eb.list_backups()
        check(result["success"] is True, "list_backups succeeds after backups")
        check(result["count"] == 2, "list_backups returns 2 after two backups")
        check(
            len(result["backups"]) == 2,
            "backups list has 2 entries",
        )
        check(
            all("filename" in b for b in result["backups"]),
            "each backup entry has filename",
        )
        check(
            all("sizeBytes" in b for b in result["backups"]),
            "each backup entry has sizeBytes",
        )
        check(
            all("modified" in b for b in result["backups"]),
            "each backup entry has modified",
        )

    # === Test 8: Backup filename format ===
    print("\n=== Backup Filename Format ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(fixture_path, backup_dir=backup_dir)
        result = eb.create_backup()

        filename = os.path.basename(result["backupPath"])
        check(
            filename.startswith("test_fixture_workbook_backup_"),
            "filename starts with workbook name + _backup_",
        )
        check(
            filename.endswith(".xlsx"),
            "filename ends with .xlsx",
        )
        # Check timestamp format: YYYYMMDD_HHMMSS_microseconds
        timestamp_part = filename.replace("test_fixture_workbook_backup_", "").replace(".xlsx", "")
        # Expected format: YYYYMMDD_HHMMSS_ffffff (22 chars, underscores at positions 8 and 15)
        check(
            len(timestamp_part) == 22 and timestamp_part[8] == "_" and timestamp_part[15] == "_",
            "filename contains YYYYMMDD_HHMMSS_microseconds timestamp",
        )

    # === Test 9: Restore from backup ===
    print("\n=== Restore From Backup ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy fixture to temp
        temp_wb = os.path.join(tmpdir, "test_wb.xlsx")
        shutil.copy2(fixture_path, temp_wb)
        original_size = os.path.getsize(temp_wb)

        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(temp_wb, backup_dir=backup_dir)

        # Create a backup
        backup_result = eb.create_backup()
        check(backup_result["success"] is True, "backup created for restore test")

        # Modify the temp workbook (simulate a write)
        with open(temp_wb, "wb") as f:
            f.write(b"modified")

        # Restore from backup
        restore_result = eb.restore_from_backup(backup_result["backupPath"])
        check(restore_result["success"] is True, "restore succeeds")
        check(
            os.path.getsize(temp_wb) == original_size,
            "workbook size matches original after restore",
        )

    # === Test 10: Restore from missing backup ===
    print("\n=== Restore From Missing Backup ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_wb = os.path.join(tmpdir, "test_wb.xlsx")
        shutil.copy2(fixture_path, temp_wb)
        eb = ExcelBackup(temp_wb, backup_dir=os.path.join(tmpdir, "backups"))

        result = eb.restore_from_backup(os.path.join(tmpdir, "nonexistent_backup.xlsx"))
        check(result["success"] is False, "restore from missing backup returns False")
        check(result["error"] is not None, "restore from missing backup returns error")

    # === Test 11: Real workbook not modified ===
    print("\n=== Real Workbook Not Modified ===")
    real_wb = os.path.join(
        _project_root, "Developer_Job_Application_Tracker_PRO.xlsx"
    )
    if os.path.exists(real_wb):
        original_size = os.path.getsize(real_wb)
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_dir = os.path.join(tmpdir, "backups")
            eb = ExcelBackup(real_wb, backup_dir=backup_dir)
            result = eb.create_backup()
            check(result["success"] is True, "backup of real workbook succeeds")
            check(
                os.path.getsize(real_wb) == original_size,
                "real workbook size unchanged after backup",
            )
    else:
        check(False, "real workbook exists for backup test")

    # === Test 12: Rapid-succession backups don't collide ===
    print("\n=== Rapid-Succession Backup Collision Test ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_wb = os.path.join(tmpdir, "test_wb.xlsx")
        shutil.copy2(fixture_path, temp_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(temp_wb, backup_dir=backup_dir)

        # Create two backups in rapid succession (same second is likely)
        result1 = eb.create_backup()
        result2 = eb.create_backup()

        check(result1["success"] is True, "first rapid backup succeeds")
        check(result2["success"] is True, "second rapid backup succeeds")

        path1 = result1["backupPath"]
        path2 = result2["backupPath"]

        check(path1 != path2, "two rapid backups have different paths")
        check(os.path.exists(path1), "first rapid backup file exists")
        check(os.path.exists(path2), "second rapid backup file exists")

        # Confirm neither overwrote the other (both have non-zero size)
        check(os.path.getsize(path1) > 0, "first rapid backup has non-zero size")
        check(os.path.getsize(path2) > 0, "second rapid backup has non-zero size")

        # Confirm backup count increased by 2
        listing = eb.list_backups()
        check(listing["count"] == 2, f"backup count is 2 (got {listing['count']})")

        # Confirm both are JSON-safe
        try:
            json.dumps(result1)
            check(True, "first rapid backup result is JSON-serializable")
        except (TypeError, ValueError) as e:
            check(False, f"first rapid backup result is JSON-serializable: {e}")
        try:
            json.dumps(result2)
            check(True, "second rapid backup result is JSON-serializable")
        except (TypeError, ValueError) as e:
            check(False, f"second rapid backup result is JSON-serializable: {e}")

    # === Test 13: Three rapid backups all unique ===
    print("\n=== Three Rapid Backups All Unique ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_wb = os.path.join(tmpdir, "test_wb.xlsx")
        shutil.copy2(fixture_path, temp_wb)
        backup_dir = os.path.join(tmpdir, "backups")
        eb = ExcelBackup(temp_wb, backup_dir=backup_dir)

        results = [eb.create_backup() for _ in range(3)]
        paths = [r["backupPath"] for r in results]

        check(all(r["success"] for r in results), "all three rapid backups succeed")
        check(len(set(paths)) == 3, "all three paths are unique")
        check(all(os.path.exists(p) for p in paths), "all three backup files exist")

        listing = eb.list_backups()
        check(listing["count"] == 3, f"backup count is 3 (got {listing['count']})")

    # === Final report ===
    print("\n" + "=" * 60)
    print("BACKUP HELPER TEST SUITE - FINAL REPORT")
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
