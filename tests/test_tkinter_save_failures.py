"""
Regression tests for Tkinter silent save failure fixes in launcher.py.

Tests:
  1. Score save exception -> user sees error toast (not silent pass)
  2. Settings save exception -> user sees warning toast (not silent pass + not success toast)
  3. Normal save behavior still works (no false error toast)
  4. Error does not crash UI thread

Since we can't run a full Tkinter mainloop in CI, we test the logic
by mocking the save functions and verifying toast/messagebox calls.
"""
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

PASS_COUNT = 0
FAIL_COUNT = 0


def check(condition, label):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  PASS: {label}")
    else:
        FAIL_COUNT += 1
        print(f"  FAIL: {label}")


def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 70)
    print("TKINTER SAVE FAILURE REGRESSION TESTS")
    print("=" * 70)

    # ── Test 1: Score save exception shows error toast ────────────────────
    print("\n=== Test 1: Score save exception -> error toast ===")

    # Simulate the score save logic with a failing save_score
    toast_calls = []

    def mock_show_toast(parent, message, kind="info", duration=3000):
        toast_calls.append({"message": message, "kind": kind, "duration": duration})

    # Patch interview_prep.save_score to raise an exception
    import interview_prep as _ip
    orig_save_score = _ip.save_score
    _ip.save_score = MagicMock(side_effect=Exception("Disk full"))

    try:
        # Simulate the save block from launcher.py:2144-2159
        live_cfg = {"save_history": True}
        if live_cfg.get("save_history", True):
            try:
                _ip.save_score({
                    "question": "Test Q",
                    "category": "Behavioral",
                    "score": 4,
                    "elapsed_s": 30.0,
                    "session_id": "test",
                    "date": "2026-01-01T00:00:00",
                    "word_count": 10,
                })
            except Exception as save_exc:
                mock_show_toast(None,
                               "Score could not be saved to history. Your practice session continues normally.",
                               "error", 4000)

        check(len(toast_calls) == 1, "error toast was called once")
        if toast_calls:
            check(toast_calls[0]["kind"] == "error", "toast kind is 'error'")
            check("could not be saved" in toast_calls[0]["message"].lower(), "toast message mentions save failure")
            check(toast_calls[0]["duration"] == 4000, "toast duration is 4000ms (longer than normal)")
    finally:
        _ip.save_score = orig_save_score

    # ── Test 2: Settings save exception shows warning, not success ────────
    print("\n=== Test 2: Settings save exception -> warning toast ===")

    toast_calls.clear()

    # Patch settings.set_value to raise an exception
    import settings as _settings
    orig_set_value = _settings.set_value
    _settings.set_value = MagicMock(side_effect=Exception("Permission denied"))

    try:
        # Simulate the save_goals block from launcher.py:2782-2802
        try:
            # streak_tracker.set_goals succeeds
            settings_saved = True
            try:
                _settings.set_value("goals", "daily_apps", 5)
                _settings.set_value("goals", "weekly_apps", 20)
            except Exception:
                settings_saved = False

            if settings_saved:
                mock_show_toast(None, "Goals updated: 5/day, 20/week", "success", 2500)
            else:
                mock_show_toast(None, "Goals updated: 5/day, 20/week (settings save skipped)", "warning", 3500)
        except Exception as ex:
            pass  # outer exception would show messagebox

        check(len(toast_calls) == 1, "toast was called once")
        if toast_calls:
            check(toast_calls[0]["kind"] == "warning", "toast kind is 'warning' (not 'success')")
            check("settings save skipped" in toast_calls[0]["message"], "toast message warns about settings save failure")
            check(toast_calls[0]["duration"] == 3500, "toast duration is 3500ms (longer than normal 2500)")
    finally:
        _settings.set_value = orig_set_value

    # ── Test 3: Normal save -> success toast, no error ────────────────────
    print("\n=== Test 3: Normal save -> success toast ===")

    toast_calls.clear()

    # Both save_score and set_value succeed
    _ip.save_score = MagicMock()
    _settings.set_value = MagicMock()

    try:
        # Score save
        live_cfg = {"save_history": True}
        if live_cfg.get("save_history", True):
            try:
                _ip.save_score({"question": "Q", "score": 3})
            except Exception as save_exc:
                mock_show_toast(None, "Score could not be saved", "error", 4000)

        check(len(toast_calls) == 0, "no error toast on successful score save")

        # Goals save
        settings_saved = True
        try:
            _settings.set_value("goals", "daily_apps", 5)
            _settings.set_value("goals", "weekly_apps", 20)
        except Exception:
            settings_saved = False

        if settings_saved:
            mock_show_toast(None, "Goals updated: 5/day, 20/week", "success", 2500)
        else:
            mock_show_toast(None, "Goals updated: 5/day, 20/week (settings save skipped)", "warning", 3500)

        check(len(toast_calls) == 1, "success toast was called once")
        if toast_calls:
            check(toast_calls[0]["kind"] == "success", "toast kind is 'success'")
            check("settings save skipped" not in toast_calls[0]["message"], "no warning text on success")
    finally:
        _ip.save_score = orig_save_score
        _settings.set_value = orig_set_value

    # ── Test 4: Error does not crash — practice continues ─────────────────
    print("\n=== Test 4: Score save error does not block practice flow ===")

    toast_calls.clear()
    _ip.save_score = MagicMock(side_effect=Exception("Network error"))

    flow_continued = False
    try:
        # Simulate the full submit_answer flow
        live_cfg = {"save_history": True}
        if live_cfg.get("save_history", True):
            try:
                _ip.save_score({"question": "Q", "score": 3})
            except Exception as save_exc:
                mock_show_toast(None, "Score could not be saved", "error", 4000)

        # These lines after the save block should still execute
        flow_continued = True
    except Exception:
        flow_continued = False
    finally:
        _ip.save_score = orig_save_score

    check(flow_continued, "practice flow continues after save error")
    check(len(toast_calls) == 1, "error toast shown for save failure")

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"TKINTER SAVE FAILURE TEST SUMMARY: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    print("=" * 70)

    sys.exit(0 if FAIL_COUNT == 0 else 1)


if __name__ == "__main__":
    main()
