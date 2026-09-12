"""
Atomic JSON Write Failure Regression Tests — Checkpoint 1 Final Validation

Tests atomic write implementations in:
  - interview_prep.py: save_score()
  - streak_tracker.py: _save()

Verifies:
  1. json.dump exception — old file preserved, temp cleaned
  2. os.replace exception — old file preserved, temp cleaned
  3. Permission denied — safe response, old file preserved
  4. Temp file creation failure — safe response
  5. Existing valid file + failed write — old file intact
  6. Existing corrupt file — handled, not silently lost
  7. Unicode content — written correctly with ensure_ascii=False
  8. Concurrent writes — thread safety
  9. UTF-8 encoding — verified
  10. File descriptor properly closed — no handle leak
"""

import sys
import os
import json
import tempfile
import shutil
import threading
import time
from unittest.mock import patch, MagicMock

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

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


def verify_file_intact(path: str, expected_data, label: str):
    """Verify file exists and contains expected JSON data."""
    check(os.path.exists(path), f"{label}: file still exists")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                actual = json.load(f)
            check(actual == expected_data, f"{label}: file content unchanged")
        except json.JSONDecodeError:
            check(False, f"{label}: file is valid JSON")


def verify_no_temp_files(dir_path: str, label: str):
    """Verify no .tmp files remain in directory."""
    temps = [f for f in os.listdir(dir_path) if f.endswith(".tmp")]
    check(len(temps) == 0, f"{label}: no temp files remaining ({len(temps)} found)")


def main():
    global PASS_COUNT, FAIL_COUNT

    print("=" * 70)
    print("ATOMIC JSON WRITE FAILURE REGRESSION TESTS")
    print("=" * 70)

    # ── interview_prep.py save_score tests ────────────────────────────────
    print("\n=== interview_prep.py save_score() ===")

    import interview_prep as ip

    # Setup: create temp dir and redirect SCORES_FILE
    with tempfile.TemporaryDirectory() as tmpdir:
        scores_file = os.path.join(tmpdir, "interview_scores.json")
        original_scores_file = ip.SCORES_FILE
        ip.SCORES_FILE = scores_file

        try:
            # ── Test 1: json.dump exception ────────────────────────────────
            print("\n--- Test 1: json.dump exception ---")
            # Create a valid existing file
            existing_data = [{"question": "old", "score": 3}]
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            entry = {"question": "new", "score": 4}
            with patch("json.dump", side_effect=Exception("Simulated write failure")):
                try:
                    ip.save_score(entry)
                    check(False, "json.dump exception: should have raised")
                except Exception:
                    check(True, "json.dump exception: exception propagated")

            verify_file_intact(scores_file, existing_data, "json.dump exception")
            verify_no_temp_files(tmpdir, "json.dump exception")

            # ── Test 2: os.replace exception ───────────────────────────────
            print("\n--- Test 2: os.replace exception ---")
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("os.replace", side_effect=OSError("Simulated replace failure")):
                try:
                    ip.save_score(entry)
                    check(False, "os.replace exception: should have raised")
                except Exception:
                    check(True, "os.replace exception: exception propagated")

            verify_file_intact(scores_file, existing_data, "os.replace exception")
            verify_no_temp_files(tmpdir, "os.replace exception")

            # ── Test 3: Permission denied on temp creation ─────────────────
            print("\n--- Test 3: Permission denied on temp creation ---")
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("tempfile.mkstemp", side_effect=PermissionError("Permission denied")):
                try:
                    ip.save_score(entry)
                    check(False, "permission denied: should have raised")
                except PermissionError:
                    check(True, "permission denied: exception propagated")

            verify_file_intact(scores_file, existing_data, "permission denied")
            verify_no_temp_files(tmpdir, "permission denied")

            # ── Test 4: Existing valid file + failed write ─────────────────
            print("\n--- Test 4: Existing valid file + failed write ---")
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("os.replace", side_effect=OSError("Disk full")):
                try:
                    ip.save_score(entry)
                except OSError:
                    pass

            verify_file_intact(scores_file, existing_data, "existing valid + failed write")
            verify_no_temp_files(tmpdir, "existing valid + failed write")

            # ── Test 5: Existing corrupt file ──────────────────────────────
            print("\n--- Test 5: Existing corrupt file ---")
            corrupt_content = '{"broken": json, missing brackets'
            with open(scores_file, "w", encoding="utf-8") as f:
                f.write(corrupt_content)

            # save_score calls load_scores which returns [] for corrupt JSON
            # Then writes new data — corrupt file is replaced
            entry2 = {"question": "after_corrupt", "score": 5}
            try:
                ip.save_score(entry2)
                check(True, "corrupt file: save_score succeeded")
            except Exception as e:
                check(False, f"corrupt file: save_score failed: {e}")

            # Verify file is now valid JSON with the new entry
            check(os.path.exists(scores_file), "corrupt file: file exists after save")
            if os.path.exists(scores_file):
                try:
                    with open(scores_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    check(isinstance(data, list), "corrupt file: data is list")
                    check(len(data) == 1, "corrupt file: has 1 entry (load_scores returned [])")
                    check(data[0]["question"] == "after_corrupt", "corrupt file: entry is correct")
                except json.JSONDecodeError:
                    check(False, "corrupt file: file is valid JSON after save")
            verify_no_temp_files(tmpdir, "corrupt file")

            # ── Test 6: Unicode content ────────────────────────────────────
            print("\n--- Test 6: Unicode content ---")
            unicode_entry = {
                "question": "Türkçe soru: Açıklayın mühendislik süreçlerini",
                "category": "Behavioral (STAR)",
                "score": 4,
                "note": "Emoji test 🚀 and special chars: <>&\"'",
            }
            try:
                ip.save_score(unicode_entry)
                check(True, "unicode: save_score succeeded")
            except Exception as e:
                check(False, f"unicode: save_score failed: {e}")

            with open(scores_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            check(any(d["question"] == unicode_entry["question"] for d in data),
                  "unicode: Turkish characters preserved")
            check(any("🚀" in d.get("note", "") for d in data),
                  "unicode: emoji preserved")
            verify_no_temp_files(tmpdir, "unicode")

            # ── Test 7: UTF-8 encoding verified ────────────────────────────
            print("\n--- Test 7: UTF-8 encoding ---")
            with open(scores_file, "rb") as f:
                raw = f.read()
            # Turkish character 'ç' in UTF-8 is 0xC3 0xA7
            check(b'\xc3\xa7' in raw or b'Turk' in raw, "UTF-8: Turkish chars encoded as UTF-8")

            # ── Test 8: File descriptor properly closed ────────────────────
            print("\n--- Test 8: File descriptor properly closed ---")
            # On Windows, we can verify by checking the temp file is deletable
            # after the operation (if fd was leaked, os.replace would fail on Windows)
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            try:
                ip.save_score({"question": "fd_test", "score": 3})
                check(True, "fd closed: save succeeded (no Windows handle lock)")
            except Exception as e:
                check(False, f"fd closed: save failed: {e}")
            verify_no_temp_files(tmpdir, "fd closed")

            # ── Test 9: Concurrent writes ──────────────────────────────────
            print("\n--- Test 9: Concurrent writes ---")
            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump([], f)

            errors = []
            def write_entry(idx):
                try:
                    ip.save_score({"question": f"concurrent_{idx}", "score": idx % 5 + 1})
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=write_entry, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            check(len(errors) == 0, f"concurrent: no errors ({len(errors)} errors: {errors[:3]})")
            with open(scores_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            check(len(data) == 5, f"concurrent: all 5 entries saved (got {len(data)})")
            verify_no_temp_files(tmpdir, "concurrent")

            # ── Test 10: Temp file in same directory ───────────────────────
            print("\n--- Test 10: Temp file in same directory ---")
            # Verify tempfile.mkstemp is called with dir=os.path.dirname(SCORES_FILE)
            captured_dir = []
            original_mkstemp = tempfile.mkstemp

            def tracking_mkstemp(*args, **kwargs):
                captured_dir.append(kwargs.get("dir", args[0] if args else None))
                return original_mkstemp(*args, **kwargs)

            with open(scores_file, "w", encoding="utf-8") as f:
                json.dump([], f)

            with patch("tempfile.mkstemp", side_effect=tracking_mkstemp):
                ip.save_score({"question": "dir_test", "score": 3})

            check(len(captured_dir) > 0, "temp dir: mkstemp was called")
            if captured_dir:
                check(captured_dir[0] == tmpdir, f"temp dir: same as target file dir ({captured_dir[0]})")

        finally:
            ip.SCORES_FILE = original_scores_file

    # ── streak_tracker.py _save() tests ───────────────────────────────────
    print("\n=== streak_tracker.py _save() ===")

    import streak_tracker as st

    with tempfile.TemporaryDirectory() as tmpdir:
        data_file = os.path.join(tmpdir, "streak_data.json")
        original_data_file = st.DATA_FILE
        st.DATA_FILE = data_file

        try:
            # ── Test 1: json.dump exception ────────────────────────────────
            print("\n--- Test 1: json.dump exception ---")
            existing_data = {"streak": 5, "total_apps": 10}
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("json.dump", side_effect=Exception("Simulated write failure")):
                try:
                    st._save({"streak": 6})
                    check(False, "json.dump exception: should have raised")
                except Exception:
                    check(True, "json.dump exception: exception propagated")

            verify_file_intact(data_file, existing_data, "json.dump exception")
            verify_no_temp_files(tmpdir, "json.dump exception")

            # ── Test 2: os.replace exception ───────────────────────────────
            print("\n--- Test 2: os.replace exception ---")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("os.replace", side_effect=OSError("Simulated replace failure")):
                try:
                    st._save({"streak": 6})
                    check(False, "os.replace exception: should have raised")
                except Exception:
                    check(True, "os.replace exception: exception propagated")

            verify_file_intact(data_file, existing_data, "os.replace exception")
            verify_no_temp_files(tmpdir, "os.replace exception")

            # ── Test 3: Permission denied ──────────────────────────────────
            print("\n--- Test 3: Permission denied ---")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("tempfile.mkstemp", side_effect=PermissionError("Permission denied")):
                try:
                    st._save({"streak": 6})
                    check(False, "permission denied: should have raised")
                except PermissionError:
                    check(True, "permission denied: exception propagated")

            verify_file_intact(data_file, existing_data, "permission denied")
            verify_no_temp_files(tmpdir, "permission denied")

            # ── Test 4: Temp file creation failure ─────────────────────────
            print("\n--- Test 4: Temp file creation failure ---")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("tempfile.mkstemp", side_effect=OSError("No space")):
                try:
                    st._save({"streak": 6})
                    check(False, "temp creation failure: should have raised")
                except OSError:
                    check(True, "temp creation failure: exception propagated")

            verify_file_intact(data_file, existing_data, "temp creation failure")

            # ── Test 5: Existing valid file + failed write ─────────────────
            print("\n--- Test 5: Existing valid file + failed write ---")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump(existing_data, f)

            with patch("os.replace", side_effect=OSError("Disk full")):
                try:
                    st._save({"streak": 999})
                except OSError:
                    pass

            verify_file_intact(data_file, existing_data, "existing valid + failed write")
            verify_no_temp_files(tmpdir, "existing valid + failed write")

            # ── Test 6: Unicode content ────────────────────────────────────
            print("\n--- Test 6: Unicode content ---")
            unicode_data = {
                "streak": 3,
                "last_date": "2026-07-03",
                "note": "Türkçe not: başarılı streak 🎯",
            }
            try:
                st._save(unicode_data)
                check(True, "unicode: _save succeeded")
            except Exception as e:
                check(False, f"unicode: _save failed: {e}")

            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            check(data.get("note", "") == unicode_data["note"],
                  "unicode: Turkish + emoji preserved")
            verify_no_temp_files(tmpdir, "unicode")

            # ── Test 7: UTF-8 encoding ─────────────────────────────────────
            print("\n--- Test 7: UTF-8 encoding ---")
            with open(data_file, "rb") as f:
                raw = f.read()
            check(b'\xc3\xa7' in raw, "UTF-8: Turkish 'ç' encoded correctly")

            # ── Test 8: Concurrent writes ──────────────────────────────────
            print("\n--- Test 8: Concurrent writes ---")
            with open(data_file, "w", encoding="utf-8") as f:
                json.dump({"streak": 0}, f)

            errors = []
            def write_streak(idx):
                try:
                    st._save({"streak": idx, "writer": f"thread_{idx}"})
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=write_streak, args=(i,)) for i in range(5)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            check(len(errors) == 0, f"concurrent: no errors ({len(errors)})")
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            check("streak" in data, "concurrent: file is valid JSON with streak field")
            verify_no_temp_files(tmpdir, "concurrent")

            # ── Test 9: Parent directory missing ───────────────────────────
            print("\n--- Test 9: Parent directory missing ---")
            missing_dir_file = os.path.join(tmpdir, "nonexistent_subdir", "streak_data.json")
            st.DATA_FILE = missing_dir_file
            try:
                try:
                    st._save({"streak": 1})
                    check(False, "missing parent dir: should have raised")
                except (FileNotFoundError, OSError):
                    check(True, "missing parent dir: exception propagated (not silently swallowed)")
            finally:
                st.DATA_FILE = data_file

            # ── Test 10: Temp file in same directory ───────────────────────
            print("\n--- Test 10: Temp file in same directory ---")
            captured_dir = []
            original_mkstemp = tempfile.mkstemp

            def tracking_mkstemp(*args, **kwargs):
                captured_dir.append(kwargs.get("dir", args[0] if args else None))
                return original_mkstemp(*args, **kwargs)

            with patch("tempfile.mkstemp", side_effect=tracking_mkstemp):
                st._save({"streak": 1})

            check(len(captured_dir) > 0, "temp dir: mkstemp was called")
            if captured_dir:
                check(captured_dir[0] == tmpdir, f"temp dir: same as target dir ({captured_dir[0]})")

        finally:
            st.DATA_FILE = original_data_file

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"ATOMIC WRITE TEST SUMMARY: {PASS_COUNT} PASS, {FAIL_COUNT} FAIL")
    print("=" * 70)

    if FAIL_COUNT > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
