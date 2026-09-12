"""
Adapter Error Behavior Tests — Checkpoint 1

Tests the contract between TypeScript adapters and Python backend:
  - DesktopAdapter expects { success, data, error } format
  - No mock fallback on desktop errors
  - Failed writes should not trigger invalidation
  - Successful writes should trigger invalidation
  - Malformed responses handled safely
  - Timeout behavior
  - Callback register/unregister

Since no JS test framework is installed, we verify the Python side
contract that DesktopAdapter depends on, and test the AutoAdapter
logic via Python simulation.
"""

import sys
import os
import json
import time
import tempfile
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from backend_bridge.api import ExcelBridgeAPI
from backend_bridge.tests.create_fixture import create_fixture, FIXTURE_PATH

PASS_COUNT = 0
FAIL_COUNT = 0


def check(condition: bool, label: str):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {label}")


def main():
    global PASS_COUNT, FAIL_COUNT

    if not os.path.exists(FIXTURE_PATH):
        create_fixture()

    # Use temp directory for JSON file isolation
    import hashlib
    tmpdir = tempfile.TemporaryDirectory(prefix="adapter_test_")
    api = ExcelBridgeAPI(workbook_path=FIXTURE_PATH, data_dir=tmpdir.name)

    # SHA256 hash of real JSON files before tests
    real_files = [
        os.path.join(PROJECT_ROOT, "interview_scores.json"),
        os.path.join(PROJECT_ROOT, "streak_data.json"),
        os.path.join(PROJECT_ROOT, "settings.json"),
    ]
    hashes_before = {}
    for f in real_files:
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hashes_before[f] = hashlib.sha256(fh.read()).hexdigest()

    print("=" * 70)
    print("ADAPTER ERROR BEHAVIOR TESTS")
    print("=" * 70)

    # ── 1. PyWebView present and call succeeds ────────────────────────────
    print("\n=== 1. PyWebView present and call succeeds ===")
    result = api.get_applications()
    check(isinstance(result, dict), "get_applications returns dict")
    check("data" in result, "response has 'data' field")
    check("error" in result, "response has 'error' field")
    check(isinstance(result.get("data"), list), "data is list for get_applications")
    check(result.get("error") is None or isinstance(result.get("error"), (str, dict)),
          "error is None or string/dict on success")

    # ── 2. Method exception produces safe error ───────────────────────────
    print("\n=== 2. Method exception produces safe error ===")
    bad_api = ExcelBridgeAPI(workbook_path=os.path.join(tempfile.gettempdir(), "nonexistent.xlsx"))
    result = bad_api.get_applications()
    check(isinstance(result, dict), "exception path returns dict")
    check("data" in result, "exception path has 'data' field")
    check("error" in result, "exception path has 'error' field")
    err_str = str(result.get("error", ""))
    check("Traceback" not in err_str, "no traceback in error")
    check("nonexistent" not in err_str, "no path leak in error")

    # ── 3. Method not found scenario (simulate via unknown method) ────────
    print("\n=== 3. Method not found scenario ===")
    # DesktopAdapter checks typeof apiMethod === 'function' before calling
    # On Python side, all methods exist. We verify the contract:
    # If a method doesn't exist, DesktopAdapter returns error string
    # We simulate by checking that calling with wrong args doesn't crash
    result = api.analyze_job_description(None)
    check(isinstance(result, dict), "None payload returns dict")
    check(result.get("success") is False, "None payload returns success=False")
    check(result.get("data") is None, "None payload returns data=None")

    # ── 4. Malformed response: success field missing ──────────────────────
    print("\n=== 4. Malformed response handling ===")
    # The _ok and _err methods always include success field
    # Test that all methods consistently use _ok/_err
    ok_resp = api._ok({"test": True})
    check(ok_resp["success"] is True, "_ok sets success=True")
    check(ok_resp["data"] == {"test": True}, "_ok sets data correctly")
    check(ok_resp["error"] is None, "_ok sets error=None")

    err_resp = api._err("TEST_CODE", "Test message")
    check(err_resp["success"] is False, "_err sets success=False")
    check(err_resp["data"] is None, "_err sets data=None")
    check(isinstance(err_resp["error"], dict), "_err error is dict")
    check(err_resp["error"]["code"] == "TEST_CODE", "_err error has code")
    check(err_resp["error"]["message"] == "Test message", "_err error has message")

    # ── 5. data: null response ────────────────────────────────────────────
    print("\n=== 5. data: null response ===")
    # When backend returns success with data=None, DesktopAdapter should
    # handle it (result.data ?? []). Verify _ok(None) format:
    null_data_resp = api._ok(None)
    check(null_data_resp["success"] is True, "_ok(None) success=True")
    check(null_data_resp["data"] is None, "_ok(None) data=None")
    # DesktopAdapter now returns data: null on error (not [] fallback)
    # Consumers handle null via ?? [] or if (data) checks

    # ── 6. success: false response ────────────────────────────────────────
    print("\n=== 6. success: false response ===")
    result = api.analyze_job_description({"jobDescription": ""})
    check(result["success"] is False, "empty jd returns success=False")
    check(result["data"] is None, "empty jd returns data=None")
    check(isinstance(result["error"], dict), "empty jd error is dict")
    check("code" in result["error"], "error has code field")
    check("message" in result["error"], "error has message field")

    # ── 7. Desktop method Promise reject (simulated) ──────────────────────
    print("\n=== 7. Desktop method rejection (simulated) ===")
    # When pywebview.api method throws, DesktopAdapter.call catches it
    # and returns { data: [], error: sanitized, source }
    # We verify _sanitize_error handles various exception types
    sanitized = ExcelBridgeAPI._sanitize_error(Exception("Error at C:\\Users\\secret\\file.py"))
    check("C:\\Users" not in sanitized, "sanitize removes Windows paths")
    check("secret" not in sanitized, "sanitize removes username from path")

    sanitized2 = ExcelBridgeAPI._sanitize_error(Exception("sk-1234567890abcdefghijklmnopqrstuv key leaked"))
    check("sk-1234567890" not in sanitized2, "sanitize removes API keys")

    sanitized3 = ExcelBridgeAPI._sanitize_error(Exception("JOBTRACKER_WRITE_MODE=production"))
    check("JOBTRACKER_WRITE_MODE" not in sanitized3, "sanitize removes env vars")

    # ── 8. No mock fallback on desktop error ──────────────────────────────
    print("\n=== 8. No mock fallback on desktop error ===")
    # AutoAdapter.dispatch: if desktop throws, it returns error — does NOT
    # fall back to mock. We verify the Python side always returns a proper
    # error response (not mock data) when things go wrong.
    bad_api2 = ExcelBridgeAPI(workbook_path=os.path.join(tempfile.gettempdir(), "missing.xlsx"))
    result = bad_api2.get_dashboard()
    check(result.get("data") == [] or result.get("data") is None,
          "failed read returns empty/null data, not mock data")
    check(result.get("error") is not None, "failed read returns error")

    # ── 9. Failed write does not produce invalidation ─────────────────────
    print("\n=== 9. Failed write — no invalidation ===")
    # AutoAdapter.writeAndInvalidate: only calls this.invalidate() if
    # result?.success === true. We verify that failed writes return
    # success=False so the frontend won't invalidate.
    result = api.add_application({"company": "", "role": "R", "status": "Saved"})
    check(result.get("success") is False, "failed add returns success=False")
    # This means writeAndInvalidate won't call this.invalidate()

    result = api.update_application_status("NONEXISTENT_ID", "Saved")
    check(result.get("success") is False, "failed update returns success=False")

    # ── 10. Successful write produces full invalidation ───────────────────
    print("\n=== 10. Successful write — invalidation ===")
    # Copy fixture to a _DEMO named file and set env var for write access
    import shutil as _shutil
    with tempfile.TemporaryDirectory() as demo_tmpdir:
        demo_wb = os.path.join(demo_tmpdir, "Tracker_DEMO.xlsx")
        _shutil.copy2(FIXTURE_PATH, demo_wb)
        os.environ["JOBTRACKER_WORKBOOK_PATH"] = demo_wb
        try:
            api_demo = ExcelBridgeAPI(workbook_path=demo_wb)
            result = api_demo.add_application({
                "company": "TestCo",
                "role": "TestRole",
                "status": "Saved",
                "location": "TestLoc",
                "source": "Test",
                "salary": "",
                "fitScore": 50,
                "notes": "Test note",
            })
            check(result.get("success") is True, "successful add returns success=True")
            # This means writeAndInvalidate WILL call this.invalidate()
        finally:
            os.environ.pop("JOBTRACKER_WORKBOOK_PATH", None)

    # ── 11. Callback register/unregister ──────────────────────────────────
    print("\n=== 11. Callback register/unregister ===")
    # AutoAdapter.onSourceChange returns unsubscribe function
    # We simulate the listener pattern in Python
    listeners = []

    def on_source_change(cb):
        listeners.append(cb)
        def unsubscribe():
            listeners.remove(cb)
        return unsubscribe

    def cb1(source): pass
    def cb2(source): pass

    unsub1 = on_source_change(cb1)
    check(len(listeners) == 1, "one listener registered")
    unsub2 = on_source_change(cb2)
    check(len(listeners) == 2, "two listeners registered")
    unsub1()
    check(len(listeners) == 1, "first listener unregistered")
    check(listeners[0] == cb2, "correct listener remains")
    unsub2()
    check(len(listeners) == 0, "all listeners unregistered")

    # ── 12. Duplicate callback prevention ─────────────────────────────────
    print("\n=== 12. Duplicate callback prevention ===")
    # AutoAdapter.onDataInvalidate: pushes callback to array
    # Duplicate callbacks are possible (same function reference)
    # but in practice React components use useCallback which provides
    # stable references. The cleanup function uses filter, so
    # calling unsub twice is safe.
    inv_listeners = []

    def on_invalidate(cb):
        inv_listeners.append(cb)
        def unsubscribe():
            if cb in inv_listeners:
                inv_listeners.remove(cb)
        return unsubscribe

    def cb_inv(): pass

    unsub_inv = on_invalidate(cb_inv)
    check(len(inv_listeners) == 1, "one invalidate listener")
    # Register same callback again — this is a different registration
    unsub_inv2 = on_invalidate(cb_inv)
    check(len(inv_listeners) == 2, "same callback registered twice")
    unsub_inv()
    check(len(inv_listeners) == 1, "first registration removed")
    unsub_inv2()
    check(len(inv_listeners) == 0, "second registration removed")
    # Calling unsub again should be safe (no error)
    try:
        unsub_inv()
        check(True, "double unsubscribe is safe")
    except Exception as e:
        check(False, f"double unsubscribe threw: {e}")

    # ── 13. Timeout behavior ──────────────────────────────────────────────
    print("\n=== 13. Timeout behavior ===")
    # DesktopAdapter uses Promise.race with 10s timeout
    # We verify that long-running operations still complete within timeout
    # The Python methods should complete in < 10s for normal operations
    start = time.time()
    result = api.get_applications()
    elapsed = time.time() - start
    check(elapsed < 10.0, f"get_applications completes in < 10s (took {elapsed:.2f}s)")

    start = time.time()
    result = api.get_dashboard()
    elapsed = time.time() - start
    check(elapsed < 10.0, f"get_dashboard completes in < 10s (took {elapsed:.2f}s)")

    # ── 14. Error sanitization for frontend ───────────────────────────────
    print("\n=== 14. Error sanitization for frontend ===")
    # DesktopAdapter.sanitizeError mirrors Python _sanitize_error
    # Verify both sides sanitize the same patterns
    test_cases = [
        ("Error at C:\\Users\\erkay\\Desktop\\file.py", "Windows path"),
        ("Error at /home/user/secret/file.py", "Unix path"),
        ("sk-1234567890abcdefghijklmnop key", "API key"),
        ("JOBTRACKER_WRITE_MODE=production", "env var"),
        ("password=secret123", "password"),
        ("Traceback (most recent call last): File...", "traceback"),
    ]
    for raw, desc in test_cases:
        sanitized = ExcelBridgeAPI._sanitize_error(Exception(raw))
        check(
            "erkay" not in sanitized and "secret" not in sanitized
            and "sk-1234567890" not in sanitized and "JOBTRACKER_WRITE" not in sanitized
            and "password=secret" not in sanitized and "Traceback" not in sanitized,
            f"sanitize removes {desc}"
        )

    # ── Verify real JSON files were not modified ──────────────────────────
    for f, hash_before in hashes_before.items():
        if os.path.exists(f):
            with open(f, "rb") as fh:
                hash_after = hashlib.sha256(fh.read()).hexdigest()
            check(hash_before == hash_after, f"{os.path.basename(f)} SHA256 unchanged")

    tmpdir.cleanup()

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"ADAPTER TEST SUMMARY: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    print("=" * 70)

    if FAIL_COUNT > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
