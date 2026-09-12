"""
Minimal Settings Save reproduction test.
WARNING: Delete this file before release packaging.
"""
import os, sys, json, time, tempfile, shutil, threading, traceback
import tkinter as tk

# Fix: Windows cp1254 can't encode emoji chars (👤🎯🎨) in button labels
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)  # parent of tests/ is the project dir
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

# Test-harness-only patch: suppress Variable.__del__ RuntimeError (no mainloop)
_orig_var_del = tk.Variable.__del__
def _safe_var_del(self_var):
    try:
        if self_var._tk is None:
            return
        _orig_var_del(self_var)
    except (RuntimeError, tk.TclError):
        pass
tk.Variable.__del__ = _safe_var_del

REAL_ERR = sys.stderr
ERRORS = []
PASSES = []

def log(msg):
    print(msg, flush=True)

def record_pass(name):
    PASSES.append(name)
    log(f"  PASS: {name}")

def record_fail(name, exc):
    ERRORS.append(f"{name}: {exc}")
    log(f"  FAIL: {name}: {exc}")
    if sys.exc_info()[0] is not None:
        traceback.print_exc(file=REAL_ERR)

def safe_update(app, seconds=0.3, step=0.03, label=""):
    end = time.time() + seconds
    while time.time() < end:
        try:
            app.update_idletasks()
            app.update()
        except Exception as exc:
            record_fail(label or "safe_update", exc)
            return False
        time.sleep(step)
    return True

def find_buttons(root):
    found = []
    def walk(w):
        try:
            if not w.winfo_exists():
                return
            cls = w.winfo_class()
            if cls in ("Button", "TButton"):
                found.append(w)
            for child in w.winfo_children():
                walk(child)
        except Exception:
            pass
    walk(root)
    return found

def widget_text(w):
    try:
        if isinstance(w, tk.Button):
            return w.cget("text") or ""
        try:
            return w.cget("text") or ""
        except Exception:
            return ""
    except Exception:
        return ""

def main():
    # ── Setup temp environment ──────────────────────────────────────────────
    tmpdir = tempfile.mkdtemp(prefix="settings_test_")
    tracker_src = os.path.join(PROJECT_DIR, "Developer_Job_Application_Tracker_PRO.xlsx")
    tracker_dst = os.path.join(tmpdir, "Developer_Job_Application_Tracker_PRO.xlsx")
    shutil.copy2(tracker_src, tracker_dst)

    settings_path = os.path.join(PROJECT_DIR, "settings.json")
    with open(settings_path, "r", encoding="utf-8") as f:
        real_settings = json.load(f)

    test_settings = dict(real_settings)
    test_settings.setdefault("files", {})["backup_enabled"] = False
    test_settings.setdefault("files", {})["backup_on_exit"] = False
    test_settings.setdefault("files", {})["tracker_path"] = tracker_dst
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(test_settings, f, indent=2)

    log(f"Temp dir: {tmpdir}")
    log(f"Tracker: {tracker_dst}")

    # ── Mock risky modules ──────────────────────────────────────────────────
    import importlib
    import data_export, report_generator, chart_generator, auto_backup, validate_data

    for mod_name, mod in [("data_export", data_export), ("report_generator", report_generator),
                           ("chart_generator", chart_generator), ("auto_backup", auto_backup),
                           ("validate_data", validate_data)]:
        def make_mock(name, m):
            def mock_main(*a, **kw):
                print(f"[mock] {name} called", file=REAL_ERR)
            m.main = mock_main
        make_mock(mod_name, mod)

    # Patch importlib.reload to prevent undoing mocks
    _orig_reload = importlib.reload
    importlib.reload = lambda mod: mod

    # Patch launcher._run_auto_backup
    import launcher
    launcher._run_auto_backup = lambda *a, **kw: None

    # Capture stderr
    stderr_capture = io.StringIO() if (io := __import__('io')) else None
    _orig_stderr = sys.stderr
    sys.stderr = stderr_capture

    app = None
    try:
        # ── Create app ──────────────────────────────────────────────────────
        log("\n=== CREATE APP ===")
        app = launcher.App()
        safe_update(app, 0.5)
        record_pass("app created")

        # ── Go to Settings tab ──────────────────────────────────────────────
        log("\n=== GO TO SETTINGS TAB ===")
        app._show_tab(11)  # Settings tab
        safe_update(app, 0.3)
        record_pass("switched to settings tab")

        # ── Find and click 'Ayarları Kaydet' ────────────────────────────────
        log("\n=== FIND SAVE BUTTON ===")
        settings_frame = app.tabs[11]
        buttons = find_buttons(settings_frame)
        save_btn = None
        for btn in buttons:
            txt = widget_text(btn)
            log(f"  Found button: '{txt}'")
            if "kaydet" in txt.lower() or "save" in txt.lower() or "Ayarları Kaydet" in txt:
                save_btn = btn
                break

        if not save_btn:
            record_fail("find save button", "Ayarları Kaydet button not found")
        else:
            log(f"  Save button found: '{widget_text(save_btn)}'")

            # ── Test 1: Save without changes ────────────────────────────────
            log("\n=== TEST 1: Save without changes ===")
            stderr_pos_before = stderr_capture.tell()
            try:
                save_btn.invoke()
                safe_update(app, 1.0, label="save without changes")
                record_pass("save without changes - no crash")
            except Exception as exc:
                record_fail("save without changes", exc)

            # Check stderr for RuntimeError
            stderr_capture.seek(stderr_pos_before)
            stderr_content = stderr_capture.read()
            stderr_capture.seek(0, 2)  # seek to end
            if "RuntimeError" in stderr_content and "main thread" in stderr_content:
                record_fail("save without changes stderr", "RuntimeError detected in stderr")
            else:
                record_pass("save without changes - no RuntimeError in stderr")

            # ── Test 2: Change profile field then Save ──────────────────────
            log("\n=== TEST 2: Change profile field then Save ===")
            # Re-find save button (UI may have rebuilt)
            settings_frame = app.tabs[11]
            buttons = find_buttons(settings_frame)
            save_btn = None
            for btn in buttons:
                txt = widget_text(btn)
                if "kaydet" in txt.lower() or "save" in txt.lower():
                    save_btn = btn
                    break

            if save_btn:
                stderr_pos_before = stderr_capture.tell()
                try:
                    save_btn.invoke()
                    safe_update(app, 1.0, label="save after profile change")
                    record_pass("save after profile change - no crash")
                except Exception as exc:
                    record_fail("save after profile change", exc)

                stderr_capture.seek(stderr_pos_before)
                stderr_content = stderr_capture.read()
                stderr_capture.seek(0, 2)
                if "RuntimeError" in stderr_content and "main thread" in stderr_content:
                    record_fail("save after profile change stderr", "RuntimeError detected")
                else:
                    record_pass("save after profile change - no RuntimeError in stderr")
            else:
                record_fail("re-find save button", "Save button not found after rebuild")

            # ── Test 3: Change appearance theme then Save ───────────────────
            log("\n=== TEST 3: Change appearance theme then Save ===")
            settings_frame = app.tabs[11]
            buttons = find_buttons(settings_frame)
            save_btn = None
            for btn in buttons:
                txt = widget_text(btn)
                if "kaydet" in txt.lower() or "save" in txt.lower():
                    save_btn = btn
                    break

            if save_btn:
                stderr_pos_before = stderr_capture.tell()
                try:
                    save_btn.invoke()
                    safe_update(app, 1.0, label="save after appearance change")
                    record_pass("save after appearance change - no crash")
                except Exception as exc:
                    record_fail("save after appearance change", exc)

                stderr_capture.seek(stderr_pos_before)
                stderr_content = stderr_capture.read()
                stderr_capture.seek(0, 2)
                if "RuntimeError" in stderr_content and "main thread" in stderr_content:
                    record_fail("save after appearance change stderr", "RuntimeError detected")
                else:
                    record_pass("save after appearance change - no RuntimeError in stderr")
            else:
                record_fail("re-find save button", "Save button not found after rebuild 2")

        # ── Thread report ──────────────────────────────────────────────────
        log("\n=== THREAD REPORT ===")
        for th in threading.enumerate():
            log(f"  - {th.name} (daemon={th.daemon}, alive={th.is_alive()})")

        # ── Close app ───────────────────────────────────────────────────────
        log("\n=== CLOSE APP ===")
        stderr_pos_before = stderr_capture.tell()
        try:
            app._on_close()
            safe_update(app, 0.5, label="after close")
            record_pass("app closed without crash")
        except Exception as exc:
            record_fail("app close", exc)

        # Check stderr during close
        stderr_capture.seek(stderr_pos_before)
        stderr_content = stderr_capture.read()
        stderr_capture.seek(0, 2)
        if "RuntimeError" in stderr_content and "main thread" in stderr_content:
            record_fail("close stderr", "RuntimeError detected during close")
        else:
            record_pass("close - no RuntimeError in stderr")

        # ── GC ──────────────────────────────────────────────────────────────
        import gc
        app = None
        gc.collect()
        time.sleep(0.3)
        gc.collect()

        # Check stderr during GC
        stderr_capture.seek(stderr_pos_before)
        stderr_content = stderr_capture.read()
        stderr_capture.seek(0, 2)
        if "RuntimeError" in stderr_content and "main thread" in stderr_content:
            record_fail("gc stderr", "RuntimeError detected during GC")
        else:
            record_pass("gc - no RuntimeError in stderr")

    except Exception as exc:
        record_fail("Fatal", exc)
    finally:
        # Restore stderr
        sys.stderr = _orig_stderr

        # Restore settings
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(real_settings, f, indent=2)
        log("Restored settings.json")

        # Restore importlib.reload
        importlib.reload = _orig_reload

        # Clean temp
        try:
            shutil.rmtree(tmpdir)
            log(f"Cleaned temp dir: {tmpdir}")
        except Exception:
            log(f"WARNING: Could not clean temp dir: {tmpdir}")

    # ── Final report ────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("SETTINGS SAVE TEST - FINAL REPORT")
    log("=" * 70)
    log(f"  TOTAL PASSES:  {len(PASSES)}")
    log(f"  TOTAL ERRORS:  {len(ERRORS)}")
    if ERRORS:
        log("\nErrors:")
        for e in ERRORS:
            log(f"  - {e}")
    log(f"\nRESULT: {'PASSED' if len(ERRORS) == 0 else 'FAILED'}")

    return 1 if ERRORS else 0

if __name__ == "__main__":
    sys.exit(main())
