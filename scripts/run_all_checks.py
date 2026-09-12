"""Unified verification script for JobTracker PRO Core MVP.

Runs all required regression tests and build checks, then prints a pass/fail summary.

Required checks (in order):
    1. Backup tests       (python -m backend_bridge.tests.test_backup)
    2. Bridge tests       (python -m backend_bridge.tests.test_bridge)
    3. Writer tests       (python -m backend_bridge.tests.test_writer)
    4. Workbook selection tests (python -m backend_bridge.tests.test_workbook_selection)
    5. Python compile     (python -m py_compile launcher.py)
    6. Settings tests     (python tests/test_settings_save.py)
    7. UI smoke tests     (python tests/full_ui_smoke_test.py)
    8. React build        (cd webui && npm run build)

Continue-on-failure: all checks run regardless of earlier failures.
Exit code 0 only when all checks pass.

Usage:
    python scripts/run_all_checks.py
"""
import os
import sys
import subprocess
import time
from datetime import datetime

# Fix: runner's own stdout must be UTF-8 to print subprocess output containing emoji
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

RESULTS = []


def _clean_env():
    """Return a copy of os.environ with JOBTRACKER_* vars removed and UTF-8 forced."""
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("JOBTRACKER_")}
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _run_subprocess(label: str, cmd: list, cwd: str, timeout: int = 120) -> bool:
    """Run a subprocess command, print output, return True if exit code 0."""
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
            env=_clean_env(),
            encoding="utf-8",
        )
        elapsed = time.time() - start
        # Print stdout
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print("  STDERR:", result.stderr[:1000])
        passed = result.returncode == 0
        status = "PASS" if passed else "FAIL"
        print(f"  -> {status} ({elapsed:.1f}s)")
        RESULTS.append({"label": label, "status": status, "elapsed": elapsed,
                         "cmd": " ".join(cmd), "passed": passed})
        return passed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"  -> TIMEOUT after {timeout}s")
        RESULTS.append({"label": label, "status": "TIMEOUT", "elapsed": elapsed,
                         "cmd": " ".join(cmd), "passed": False})
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"  -> ERROR: {e}")
        RESULTS.append({"label": label, "status": "ERROR", "elapsed": elapsed,
                         "cmd": " ".join(cmd), "passed": False})
        return False


def check_backup_tests() -> bool:
    """Run ExcelBackup test suite."""
    print(f"\n{'='*60}")
    print("  CHECK: Backup Tests")
    print(f"{'='*60}")
    return _run_subprocess(
        "BACKUP TESTS",
        [sys.executable, "-m", "backend_bridge.tests.test_backup"],
        cwd=_PROJECT_ROOT,
        timeout=60,
    )


def check_bridge_tests() -> bool:
    """Run bridge read-only test suite."""
    print(f"\n{'='*60}")
    print("  CHECK: Bridge Tests")
    print(f"{'='*60}")
    return _run_subprocess(
        "BRIDGE TESTS",
        [sys.executable, "-m", "backend_bridge.tests.test_bridge"],
        cwd=_PROJECT_ROOT,
        timeout=60,
    )


def check_writer_tests() -> bool:
    """Run ExcelWriter test suite."""
    print(f"\n{'='*60}")
    print("  CHECK: Writer Tests")
    print(f"{'='*60}")
    return _run_subprocess(
        "WRITER TESTS",
        [sys.executable, "-m", "backend_bridge.tests.test_writer"],
        cwd=_PROJECT_ROOT,
        timeout=120,
    )


def check_workbook_selection_tests() -> bool:
    """Run workbook selection, concurrency, and invalidation tests."""
    print(f"\n{'='*60}")
    print("  CHECK: Workbook Selection + Invalidation Tests")
    print(f"{'='*60}")
    return _run_subprocess(
        "WORKBOOK SELECTION TESTS",
        [sys.executable, "-m", "backend_bridge.tests.test_workbook_selection"],
        cwd=_PROJECT_ROOT,
        timeout=120,
    )


def check_py_compile() -> bool:
    """Compile-check launcher.py."""
    print(f"\n{'='*60}")
    print("  CHECK: Python Compile (launcher.py)")
    print(f"{'='*60}")
    launcher_path = os.path.join(_PROJECT_ROOT, "launcher.py")
    return _run_subprocess(
        "PYTHON COMPILE",
        [sys.executable, "-m", "py_compile", launcher_path],
        cwd=_PROJECT_ROOT,
        timeout=30,
    )


def check_settings_tests() -> bool:
    """Run settings save/load tests."""
    print(f"\n{'='*60}")
    print("  CHECK: Settings Tests")
    print(f"{'='*60}")
    test_path = os.path.join(_PROJECT_ROOT, "tests", "test_settings_save.py")
    return _run_subprocess(
        "SETTINGS TESTS",
        [sys.executable, test_path],
        cwd=_PROJECT_ROOT,
        timeout=30,
    )


def check_ui_smoke_tests() -> bool:
    """Run full UI smoke tests."""
    print(f"\n{'='*60}")
    print("  CHECK: UI Smoke Tests")
    print(f"{'='*60}")
    test_path = os.path.join(_PROJECT_ROOT, "tests", "full_ui_smoke_test.py")
    return _run_subprocess(
        "UI SMOKE TESTS",
        [sys.executable, test_path],
        cwd=_PROJECT_ROOT,
        timeout=180,
    )


def check_react_build() -> bool:
    """Run React production build."""
    print(f"\n{'='*60}")
    print("  CHECK: React Production Build")
    print(f"{'='*60}")
    webui_dir = os.path.join(_PROJECT_ROOT, "webui")
    if not os.path.exists(os.path.join(webui_dir, "package.json")):
        print("  webui/package.json not found — skipping.")
        RESULTS.append({"label": "REACT BUILD", "status": "SKIP", "elapsed": 0,
                         "cmd": "npm run build", "passed": True})
        return True
    # npm on Windows requires shell=True to resolve npm.cmd
    start = time.time()
    try:
        result = subprocess.run(
            "npm run build",
            capture_output=True,
            text=True,
            cwd=webui_dir,
            timeout=180,
            env=_clean_env(),
            encoding="utf-8",
            shell=True,
        )
        elapsed = time.time() - start
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            for line in lines[-30:]:
                print(f"  {line}")
        if result.stderr:
            print("  STDERR:", result.stderr[:1000])
        passed = result.returncode == 0
        status = "PASS" if passed else "FAIL"
        print(f"  -> {status} ({elapsed:.1f}s)")
        RESULTS.append({"label": "REACT BUILD", "status": status, "elapsed": elapsed,
                         "cmd": "npm run build", "passed": passed})
        return passed
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"  -> TIMEOUT after 180s")
        RESULTS.append({"label": "REACT BUILD", "status": "TIMEOUT", "elapsed": elapsed,
                         "cmd": "npm run build", "passed": False})
        return False
    except Exception as e:
        elapsed = time.time() - start
        print(f"  -> ERROR: {e}")
        RESULTS.append({"label": "REACT BUILD", "status": "ERROR", "elapsed": elapsed,
                         "cmd": "npm run build", "passed": False})
        return False


def main():
    print(f"\n{'#'*60}")
    print("  JobTracker PRO — Core MVP Verification")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    print(f"  Continue-on-failure: all checks run regardless of earlier results.")
    print(f"  Exit code 0 only when ALL checks pass.")

    # Required regression suite — all run regardless of earlier failures
    check_backup_tests()
    check_bridge_tests()
    check_writer_tests()
    check_workbook_selection_tests()
    check_py_compile()
    check_settings_tests()
    check_ui_smoke_tests()
    check_react_build()

    # Summary
    print(f"\n{'='*60}")
    print("  FINAL RESULTS")
    print(f"{'='*60}")
    all_passed = True
    for r in RESULTS:
        dots = "." * max(1, 25 - len(r["label"]))
        status = r["status"]
        if not r["passed"]:
            all_passed = False
        print(f"  {r['label']} {dots} {status}")
    print(f"{'='*60}")

    if all_passed:
        print("\n  FINAL RESULT: PASS\n")
        sys.exit(0)
    else:
        failed = [r for r in RESULTS if not r["passed"]]
        print(f"\n  FINAL RESULT: FAIL ({len(failed)} check(s) failed)\n")
        for r in failed:
            print(f"    FAILED: {r['label']} — {r['cmd']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
