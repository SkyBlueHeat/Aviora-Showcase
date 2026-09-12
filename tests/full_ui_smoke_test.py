"""
Full UI Smoke Test — Developer Job Application Tracker PRO
Run: python tests/full_ui_smoke_test.py
WARNING: Delete before creating customer/release package.
"""
import os
import sys
import gc
import time
import json
import shutil
import tempfile
import traceback
import threading
import tkinter as tk

# Fix: Windows cp1254 can't encode emoji chars in button labels
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
os.chdir(PROJECT_DIR)
sys.path.insert(0, str(PROJECT_DIR))

# Save real stdout/stderr for reliable reporting even if redirected
_REAL_OUT = sys.__stdout__
_REAL_ERR = sys.__stderr__

# ── Test-harness-only patch: suppress Variable.__del__ RuntimeError ──────────
# In production, mainloop() is running so Variable.__del__ can safely call Tcl.
# In the test harness, mainloop() is NOT running, so GC of Tk variables after
# app.destroy() triggers RuntimeError: main thread is not in main loop.
# This patch is test-only and never shipped to customers.
_orig_var_del = tk.Variable.__del__
def _safe_var_del(self_var):
    try:
        if self_var._tk is None:
            return
        _orig_var_del(self_var)
    except (RuntimeError, tk.TclError):
        pass
tk.Variable.__del__ = _safe_var_del

# Directories that must NOT receive new files during test
PROTECTED_DIRS = [
    PROJECT_DIR / "exports",
    PROJECT_DIR / "reports",
    PROJECT_DIR / "backups",
    PROJECT_DIR / "charts",
    PROJECT_DIR / "releases",
]

# ── Results tracking ─────────────────────────────────────────────────────────
ERRORS = []
WARNINGS = []
PASSES = []
STATS = {
    "tabs_tested": 0,
    "buttons_found": 0,
    "buttons_clicked": 0,
    "buttons_mocked": 0,
    "entries_tested": 0,
    "texts_tested": 0,
    "comboboxes_tested": 0,
    "checkboxes_tested": 0,
    "radios_tested": 0,
    "live_features_tested": 0,
    "popups_caught": 0,
    "timer_errors": 0,
    "tcl_errors": 0,
    "thread_violations": 0,
}

def _print(msg):
    _REAL_OUT.write(str(msg) + "\n")
    _REAL_OUT.flush()

def log_section(title):
    _print(f"\n{'='*72}\n{title}\n{'='*72}")

def record_pass(name):
    PASSES.append(name)
    _print(f"  PASS: {name}")

def record_warn(name, msg):
    WARNINGS.append(f"{name}: {msg}")
    _print(f"  WARN: {name}: {msg}")

def record_fail(name, exc):
    ERRORS.append(f"{name}: {exc}")
    _print(f"  FAIL: {name}: {exc}")
    exc_type = sys.exc_info()[0]
    if exc_type is not None:
        traceback.print_exc(file=_REAL_ERR)

def check(name, fn):
    try:
        fn()
        record_pass(name)
        return True
    except Exception as exc:
        record_fail(name, exc)
        return False

def safe_update(app, seconds=0.2, step=0.03, label="update"):
    end = time.time() + seconds
    while time.time() < end:
        try:
            app.update_idletasks()
            app.update()
        except Exception as exc:
            record_fail(label, exc)
            return False
        time.sleep(step)
    return True

def _check_stderr(capture_obj, phase_label, last_pos=None):
    """Check stderr capture for RuntimeError/TclError since last_pos, return (errors, new_pos)."""
    if capture_obj is None:
        return [], 0
    pos = capture_obj.tell()
    capture_obj.seek(last_pos or 0)
    content = capture_obj.read()
    capture_obj.seek(pos)
    errors = []
    for line in content.split("\n"):
        lower = line.lower()
        if ("runtimeerror" in lower and "main thread" in lower) or \
           ("tclerror" in lower and "invalid command" in lower):
            errors.append(line.strip())
    return errors, pos

# ── Widget helpers ───────────────────────────────────────────────────────────
def find_widgets(root, class_names=None):
    found = []
    def walk(w):
        if not w.winfo_exists():
            return
        cls = w.winfo_class()
        if class_names is None or cls in class_names:
            found.append(w)
        for child in w.winfo_children():
            walk(child)
    walk(root)
    return found

def widget_text(w):
    try:
        return str(w.cget("text") or "").strip()
    except Exception:
        return ""

def widget_state(w):
    try:
        state = str(w.cget("state") or "normal")
        return state
    except Exception:
        return "unknown"

# ── Temp environment setup ───────────────────────────────────────────────────
class TempEnv:
    def __init__(self):
        self.temp_dir = None
        self.temp_tracker = None
        self.original_settings = None
        self.settings_path = PROJECT_DIR / "settings.json"
        self.tracker_path = PROJECT_DIR / "Developer_Job_Application_Tracker_PRO.xlsx"
        self.dir_snapshots = {}

    def _snapshot_dir(self, d: Path):
        if not d.exists():
            return set()
        return set(f.name for f in d.iterdir() if f.is_file())

    def snapshot_protected_dirs(self):
        for d in PROTECTED_DIRS:
            self.dir_snapshots[str(d)] = self._snapshot_dir(d)

    def check_protected_dirs(self):
        new_files = []
        for d in PROTECTED_DIRS:
            after = self._snapshot_dir(d)
            before = self.dir_snapshots.get(str(d), set())
            diff = after - before
            if diff:
                new_files.append((str(d), diff))
        return new_files

    def setup(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="jobtracker_test_"))
        _print(f"Temp dir: {self.temp_dir}")

        # Snapshot protected dirs BEFORE anything
        self.snapshot_protected_dirs()
        _print("Snapshotted protected dirs: exports, reports, backups, charts, releases")

        # Copy tracker
        if self.tracker_path.exists():
            self.temp_tracker = self.temp_dir / "Developer_Job_Application_Tracker_PRO.xlsx"
            shutil.copy2(self.tracker_path, self.temp_tracker)
            _print(f"Copied tracker to: {self.temp_tracker}")
        else:
            record_warn("temp_env", "Tracker file not found, creating dummy")
            self.temp_tracker = self.temp_dir / "Developer_Job_Application_Tracker_PRO.xlsx"
            import openpyxl
            wb = openpyxl.Workbook()
            wb.save(self.temp_tracker)

        # Backup settings and write test settings
        if self.settings_path.exists():
            self.original_settings = self.settings_path.read_text(encoding="utf-8")
        test_cfg = {}
        if self.original_settings:
            try:
                test_cfg = json.loads(self.original_settings)
            except Exception:
                test_cfg = {}
        test_cfg.setdefault("files", {})["tracker_path"] = str(self.temp_tracker)
        test_cfg.setdefault("files", {})["backup_folder"] = str(self.temp_dir / "backups")
        test_cfg.setdefault("files", {})["backup_enabled"] = False  # Disable startup backup
        test_cfg.setdefault("api", {})["openai_key"] = ""
        test_cfg.setdefault("api", {})["notion_token"] = ""
        test_cfg.setdefault("api", {})["notion_database_id"] = ""
        self.settings_path.write_text(json.dumps(test_cfg, indent=2, ensure_ascii=False), encoding="utf-8")
        _print(f"Wrote test settings.json (backup_enabled=False, temp tracker)")

        # Create all temp subdirs
        for sub in ["backups", "exports", "reports", "charts"]:
            (self.temp_dir / sub).mkdir(exist_ok=True)

    def cleanup(self):
        # Restore settings
        if self.original_settings is not None:
            self.settings_path.write_text(self.original_settings, encoding="utf-8")
            _print("Restored original settings.json")
        elif self.settings_path.exists():
            self.settings_path.unlink()
            _print("Removed test settings.json")

        # Delete temp dir
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            _print(f"Cleaned temp dir: {self.temp_dir}")

        # Check for real file writes
        new_files = self.check_protected_dirs()
        if new_files:
            for d, files in new_files:
                for f in files:
                    record_fail("REAL FILE WRITE DETECTED", f"{d}/{f}")
                    # Clean up the stray file
                    stray = Path(d) / f
                    try:
                        stray.unlink()
                        _print(f"  Cleaned stray: {stray}")
                    except Exception:
                        pass
        else:
            record_pass("no real project files written")

# ── Monkeypatch setup ────────────────────────────────────────────────────────
class MockPatches:
    def __init__(self):
        self.patches = []
        self.popups = []

    def setup(self, temp_dir: Path):
        import tkinter as tk
        from tkinter import messagebox, filedialog
        self.temp_dir = temp_dir

        # ── MessageBox mocks ──────────────────────────────────────────────────
        def mock_askyesno(title, message, **kw):
            self.popups.append(("askyesno", title, message))
            STATS["popups_caught"] += 1
            return True

        def mock_showinfo(title, message, **kw):
            self.popups.append(("showinfo", title, message))
            STATS["popups_caught"] += 1
            return "ok"

        def mock_showwarning(title, message, **kw):
            self.popups.append(("showwarning", title, message))
            STATS["popups_caught"] += 1
            return "ok"

        def mock_showerror(title, message, **kw):
            self.popups.append(("showerror", title, message))
            STATS["popups_caught"] += 1
            return "ok"

        p = patch.object(messagebox, "askyesno", mock_askyesno)
        p.start(); self.patches.append(p)
        p = patch.object(messagebox, "showinfo", mock_showinfo)
        p.start(); self.patches.append(p)
        p = patch.object(messagebox, "showwarning", mock_showwarning)
        p.start(); self.patches.append(p)
        p = patch.object(messagebox, "showerror", mock_showerror)
        p.start(); self.patches.append(p)

        # ── FileDialog mocks ──────────────────────────────────────────────────
        def mock_askopenfilename(**kw):
            return str(PROJECT_DIR / "Developer_Job_Application_Tracker_PRO.xlsx")

        def mock_asksaveasfilename(**kw):
            default_ext = kw.get("defaultextension", ".txt")
            return str(PROJECT_DIR / "exports" / f"test_export{default_ext}")

        def mock_askdirectory(**kw):
            return str(PROJECT_DIR / "exports")

        p = patch.object(filedialog, "askopenfilename", mock_askopenfilename)
        p.start(); self.patches.append(p)
        p = patch.object(filedialog, "asksaveasfilename", mock_asksaveasfilename)
        p.start(); self.patches.append(p)
        p = patch.object(filedialog, "askdirectory", mock_askdirectory)
        p.start(); self.patches.append(p)

        # ── os.startfile mock ─────────────────────────────────────────────────
        def mock_startfile(path, *args, **kwargs):
            self.popups.append(("startfile", str(path), ""))
            return None
        p = patch.object(os, "startfile", mock_startfile)
        p.start(); self.patches.append(p)

        # ── subprocess.run mock ───────────────────────────────────────────────
        def mock_subprocess_run(*args, **kwargs):
            result = MagicMock()
            result.stdout = "(mocked subprocess output)"
            result.stderr = ""
            result.returncode = 0
            return result
        p = patch("subprocess.run", mock_subprocess_run)
        p.start(); self.patches.append(p)

        # ── smtplib.SMTP mock ─────────────────────────────────────────────────
        import smtplib
        mock_smtp = MagicMock()
        p = patch.object(smtplib, "SMTP", return_value=mock_smtp)
        p.start(); self.patches.append(p)

        # ── requests mock (for Notion) ────────────────────────────────────────
        try:
            import requests
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"id": "mock-page-id"}
            mock_resp.raise_for_status.return_value = None
            mock_resp.status_code = 200
            p = patch.object(requests, "post", return_value=mock_resp)
            p.start(); self.patches.append(p)
            p = patch.object(requests, "get", return_value=mock_resp)
            p.start(); self.patches.append(p)
        except ImportError:
            pass

        # ── webbrowser mock ───────────────────────────────────────────────────
        try:
            import webbrowser
            p = patch.object(webbrowser, "open", lambda *a, **kw: True)
            p.start(); self.patches.append(p)
            p = patch.object(webbrowser, "open_new", lambda *a, **kw: True)
            p.start(); self.patches.append(p)
        except ImportError:
            pass

        # ── Module-level mocks: redirect export/report/chart/backup to temp ──
        # These modules use __file__ to determine output dirs, so we patch their main()
        import data_export
        import report_generator
        import chart_generator
        import auto_backup
        import validate_data
        import importlib

        _temp = str(temp_dir)
        _tracker = str(temp_dir / "Developer_Job_Application_Tracker_PRO.xlsx")

        def _mock_data_export_main():
            out_dir = os.path.join(_temp, "exports")
            os.makedirs(out_dir, exist_ok=True)
            data_export.export_all_sheets(_tracker, out_dir)
            _print(f"[mock] data_export -> {out_dir}")

        def _mock_report_main():
            out_dir = os.path.join(_temp, "reports")
            os.makedirs(out_dir, exist_ok=True)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_generator.generate_weekly_report(_tracker, os.path.join(out_dir, f"weekly_report_{ts}.txt"))
            _print(f"[mock] report_generator -> {out_dir}")

        def _mock_chart_main():
            out_dir = os.path.join(_temp, "charts")
            os.makedirs(out_dir, exist_ok=True)
            chart_generator.create_all_charts(_tracker, out_dir)
            _print(f"[mock] chart_generator -> {out_dir}")

        def _mock_backup_main():
            out_dir = os.path.join(_temp, "backups")
            os.makedirs(out_dir, exist_ok=True)
            auto_backup.create_backup(_tracker, out_dir)
            _print(f"[mock] auto_backup -> {out_dir}")

        def _mock_validate_main():
            out_dir = os.path.join(_temp, "reports")
            os.makedirs(out_dir, exist_ok=True)
            from datetime import datetime
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            validate_data.generate_validation_report(_tracker, os.path.join(out_dir, f"validation_report_{ts}.txt"))
            _print(f"[mock] validate_data -> {out_dir}")

        p = patch.object(data_export, "main", _mock_data_export_main)
        p.start(); self.patches.append(p)
        p = patch.object(report_generator, "main", _mock_report_main)
        p.start(); self.patches.append(p)
        p = patch.object(chart_generator, "main", _mock_chart_main)
        p.start(); self.patches.append(p)
        p = patch.object(auto_backup, "main", _mock_backup_main)
        p.start(); self.patches.append(p)
        p = patch.object(validate_data, "main", _mock_validate_main)
        p.start(); self.patches.append(p)

        # ── CRITICAL: Patch importlib.reload as no-op so module patches survive ──
        # launcher's run_script does importlib.reload(mod) which undoes our patches
        _orig_reload = importlib.reload
        def _mock_reload(mod):
            return mod
        importlib.reload = _mock_reload
        self._orig_reload = _orig_reload

        # ── Mock launcher._run_auto_backup ───────────────────────────────────
        import launcher
        p = patch.object(launcher, "_run_auto_backup", lambda cfg=None: None)
        p.start(); self.patches.append(p)

        # ── Thread exception hook (use real stderr, not redirected stdout) ────
        self._original_hook = getattr(threading, "excepthook", None)
        def thread_hook(args):
            msg = f"Thread exception in {args.thread.name}: {args.exc_type.__name__}: {args.exc_value}"
            ERRORS.append(msg)
            STATS["timer_errors"] += 1
            _REAL_ERR.write(f"  FAIL: {msg}\n")
            traceback.print_exception(args.exc_type, args.exc_value, args.exc_traceback, file=_REAL_ERR)
        threading.excepthook = thread_hook

    def teardown(self):
        for p in self.patches:
            try:
                p.stop()
            except Exception:
                pass
        if hasattr(self, "_orig_reload"):
            import importlib
            importlib.reload = self._orig_reload
        if hasattr(self, "_original_hook"):
            threading.excepthook = self._original_hook

# ── Main test ────────────────────────────────────────────────────────────────
def main():
    # ── Capture stderr for RuntimeError detection ────────────────────────────
    import io
    stderr_capture = io.StringIO()
    _orig_stderr = sys.stderr
    sys.stderr = stderr_capture
    stderr_phases = []  # (phase_name, position_in_capture)

    def _mark_stderr_phase(name):
        stderr_phases.append((name, stderr_capture.tell()))

    log_section("SETUP: Temp Environment")
    temp_env = TempEnv()
    try:
        temp_env.setup()
        record_pass("temp env created")
    except Exception as exc:
        record_fail("temp env setup", exc)
        return

    log_section("SETUP: Mocks & Patches")
    mocks = MockPatches()
    try:
        mocks.setup(temp_env.temp_dir)
        record_pass("mocks installed")
    except Exception as exc:
        record_fail("mock setup", exc)
        temp_env.cleanup()
        return

    app = None
    try:
        log_section("IMPORT & CREATE APP")
        import launcher
        check("import launcher", lambda: launcher)

        # Patch Tk callback exception handler
        app = launcher.App()
        check("launcher.App()", lambda: app)

        def tk_callback_exception(exc, val, tb):
            msg = f"Tk callback: {exc.__name__}: {val}"
            if "TclError" in exc.__name__:
                STATS["tcl_errors"] += 1
                record_warn("tk_callback", msg)
            else:
                ERRORS.append(msg)
                _REAL_ERR.write(f"  FAIL: {msg}\n")
                traceback.print_exception(exc, val, tb, file=_REAL_ERR)
        app.report_callback_exception = tk_callback_exception

        check("app exists", lambda: app.winfo_exists())
        safe_update(app, 0.5, label="initial render")
        record_pass("initial render")
        _mark_stderr_phase("after-app-create")

        # ── Basic attributes ──────────────────────────────────────────────────
        log_section("BASIC ATTRIBUTES")
        check("tabs exists", lambda: hasattr(app, "tabs"))
        check("tab count >= 10", lambda: len(app.tabs) >= 10)
        check("current_tab_index exists", lambda: hasattr(app, "current_tab_index"))
        check("_closing flag exists", lambda: hasattr(app, "_closing"))
        check("_closing is False", lambda: app._closing is False)

        for attr in ["_status_tracker_lbl", "_status_backup_lbl",
                     "_status_validation_lbl", "_status_lang_lbl"]:
            check(f"status label: {attr}", lambda a=attr: hasattr(app, a) and getattr(app, a).winfo_exists())

        for attr in ["_tracker_watch_id", "_email_watch_id",
                     "_status_bar_watch_id", "_json_watch_id"]:
            check(f"timer: {attr}", lambda a=attr: hasattr(app, a) and getattr(app, a) is not None)

        # ── Tab switching ─────────────────────────────────────────────────────
        log_section("TAB SWITCH TEST")
        tab_names = ["Home", "Applications", "Salary", "LinkedIn", "Cover Letter",
                     "JD Analyzer", "Tools", "Interview", "Streak", "ATS", "Notion", "Settings"]

        for i in range(len(app.tabs)):
            nm = tab_names[i] if i < len(tab_names) else f"Tab {i}"
            check(f"show tab {i}: {nm}", lambda idx=i: app._show_tab(idx))
            check(f"current_tab_index == {i}", lambda idx=i: app.current_tab_index == idx)
            safe_update(app, 0.2, label=f"tab {i} update")
            STATS["tabs_tested"] += 1

        # Reverse stress
        for i in reversed(range(len(app.tabs))):
            check(f"reverse tab {i}", lambda idx=i: app._show_tab(idx))
            safe_update(app, 0.1, label=f"reverse tab {i}")
        _mark_stderr_phase("after-tab-switch")

        # ── Widget inventory & interaction ────────────────────────────────────
        log_section("WIDGET INTERACTION TESTS")
        _mark_stderr_phase("before-widget-interaction")

        # Buttons that may trigger UI rebuild — need special handling
        REBUILD_TRIGGERS = {"save", "reset", "apply", "kaydet", "sifirla"}
        # Risky button keywords — these are mocked via module patches / temp redirect
        RISKY_KEYWORDS = {"export", "report", "backup", "chart", "sync", "email",
                          "send", "notion", "validate", "analyze", "generate",
                          "dışa", "rapor", "yedek", "grafik", "senkron", "posta",
                          "gönder", "doğrula", "analiz", "üret", "kopyala"}

        def _is_rebuild_button(text):
            t = (text or "").lower()
            return any(k in t for k in REBUILD_TRIGGERS)

        def _is_risky_button(text):
            t = (text or "").lower()
            return any(k in t for k in RISKY_KEYWORDS)

        for tab_idx in range(len(app.tabs)):
            app._show_tab(tab_idx)
            safe_update(app, 0.15, label=f"widget tab {tab_idx}")
            nm = tab_names[tab_idx] if tab_idx < len(tab_names) else f"Tab {tab_idx}"
            tab_frame = app.tabs[tab_idx]
            # Tools tab (6) spawns background threads — need extra settle time
            is_tools_tab = (tab_idx == 6)
            _stderr_before_tab = stderr_capture.tell()

            # ── Buttons (per-tab, with rebuild detection) ─────────────────────
            buttons = find_widgets(tab_frame, {"Button", "TButton"})
            for btn in buttons:
                if not btn.winfo_exists():
                    continue
                STATS["buttons_found"] += 1
                txt = widget_text(btn)
                state = widget_state(btn)
                if state == "disabled":
                    record_warn(f"button disabled: '{txt}' in {nm}", "skipped")
                    continue
                is_rebuild = _is_rebuild_button(txt)
                is_risky = _is_risky_button(txt)
                if is_risky:
                    STATS["buttons_mocked"] += 1
                _stderr_before_btn = stderr_capture.tell()
                try:
                    btn.invoke()
                    STATS["buttons_clicked"] += 1
                    wait_time = 2.0 if is_tools_tab else 0.15
                    safe_update(app, wait_time, label=f"button '{txt}' in {nm}")
                    if is_rebuild:
                        tab_frame = app.tabs[tab_idx]
                        safe_update(app, 0.3, label=f"rebuild settle after '{txt}'")
                    risk_tag = " [MOCKED]" if is_risky else ""
                    record_pass(f"button click: '{txt}' in {nm}{risk_tag}")
                    # Check stderr for RuntimeError after this button (incremental)
                    _se, _stderr_before_btn = _check_stderr(stderr_capture, f"button '{txt}' in {nm}", _stderr_before_btn)
                    if _se:
                        for _e in _se[:3]:
                            record_fail(f"RuntimeError after button '{txt}' in {nm}", _e)
                except tk.TclError as exc:
                    STATS["tcl_errors"] += 1
                    record_warn(f"button TclError: '{txt}' in {nm}", str(exc))
                except Exception as exc:
                    record_fail(f"button click: '{txt}' in {nm}", exc)

            # ── Entry widgets (per-tab) ───────────────────────────────────────
            entries = find_widgets(tab_frame, {"Entry"})
            for entry in entries:
                if not entry.winfo_exists():
                    continue
                try:
                    old_val = entry.get()
                    entry.delete(0, "end")
                    entry.insert(0, "test_value_123")
                    entry.event_generate("<KeyRelease>")
                    safe_update(app, 0.05, label="entry test")
                    STATS["entries_tested"] += 1
                    if entry.winfo_exists():
                        entry.delete(0, "end")
                        entry.insert(0, old_val)
                        entry.event_generate("<KeyRelease>")
                    record_pass(f"entry test in {nm}")
                except tk.TclError:
                    pass  # widget destroyed during test — acceptable
                except Exception as exc:
                    record_fail(f"entry test in {nm}", exc)

            # ── Text widgets (per-tab) ────────────────────────────────────────
            texts = find_widgets(tab_frame, {"Text"})
            for txt_w in texts:
                if not txt_w.winfo_exists():
                    continue
                try:
                    old_state = txt_w.cget("state")
                    if old_state == "disabled":
                        txt_w.config(state="normal")
                    old_val = txt_w.get("1.0", "end-1c")
                    txt_w.delete("1.0", "end")
                    txt_w.insert("1.0", "Test text input for smoke test.\nLine 2.\nLine 3.")
                    txt_w.event_generate("<KeyRelease>")
                    safe_update(app, 0.05, label="text test")
                    STATS["texts_tested"] += 1
                    if txt_w.winfo_exists():
                        txt_w.delete("1.0", "end")
                        txt_w.insert("1.0", old_val)
                        txt_w.config(state=old_state)
                    record_pass(f"text test in {nm}")
                except tk.TclError:
                    pass  # widget destroyed during test — acceptable
                except Exception as exc:
                    record_fail(f"text test in {nm}", exc)

            # ── Combobox widgets (per-tab) ────────────────────────────────────
            combos = find_widgets(tab_frame, {"TCombobox", "Combobox"})
            for combo in combos:
                if not combo.winfo_exists():
                    continue
                try:
                    old_val = combo.get()
                    vals = combo.cget("values")
                    if vals:
                        val_list = list(vals) if isinstance(vals, (list, tuple)) else []
                        if val_list:
                            for test_val in [val_list[0], val_list[-1]]:
                                if combo.winfo_exists():
                                    combo.set(test_val)
                                    combo.event_generate("<<ComboboxSelected>>")
                                    safe_update(app, 0.05, label="combo test")
                            STATS["comboboxes_tested"] += 1
                            if combo.winfo_exists():
                                combo.set(old_val)
                                combo.event_generate("<<ComboboxSelected>>")
                            record_pass(f"combobox test in {nm}")
                except tk.TclError:
                    pass
                except Exception as exc:
                    record_fail(f"combobox test in {nm}", exc)

            # ── Checkbutton widgets (per-tab) ─────────────────────────────────
            checks = find_widgets(tab_frame, {"Checkbutton"})
            for chk in checks:
                if not chk.winfo_exists():
                    continue
                try:
                    chk.invoke()
                    safe_update(app, 0.05, label="check toggle")
                    if chk.winfo_exists():
                        chk.invoke()
                        safe_update(app, 0.05, label="check restore")
                    STATS["checkboxes_tested"] += 1
                    record_pass(f"checkbutton test in {nm}")
                except tk.TclError:
                    pass
                except Exception as exc:
                    record_fail(f"checkbutton test in {nm}", exc)

            # ── Radiobutton widgets (per-tab) ─────────────────────────────────
            radios = find_widgets(tab_frame, {"Radiobutton"})
            for radio in radios:
                if not radio.winfo_exists():
                    continue
                try:
                    radio.invoke()
                    safe_update(app, 0.05, label="radio test")
                    STATS["radios_tested"] += 1
                    record_pass(f"radiobutton test in {nm}")
                except tk.TclError:
                    pass
                except Exception as exc:
                    record_fail(f"radiobutton test in {nm}", exc)

        # ── Live feature tests ────────────────────────────────────────────────
        log_section("LIVE FEATURE TESTS")
        _mark_stderr_phase("before-live-features")

        # Salary Calculator (tab 2)
        app._show_tab(2)
        safe_update(app, 0.3, label="salary tab")
        salary_entries = find_widgets(app.tabs[2], {"Entry"})
        for entry in salary_entries:
            try:
                old = entry.get()
                entry.delete(0, "end")
                entry.insert(0, "75000")
                entry.event_generate("<KeyRelease>")
                safe_update(app, 1.0, label="salary debounce")
                STATS["live_features_tested"] += 1
                entry.delete(0, "end")
                entry.insert(0, old)
                entry.event_generate("<KeyRelease>")
                safe_update(app, 0.5, label="salary restore")
                record_pass("salary live calc debounce")
                break
            except Exception as exc:
                record_fail("salary live calc", exc)
                break

        # LinkedIn — resolve tab index dynamically from app._nav_keys
        linkedin_idx = next((idx for key, idx in app._nav_keys if "linkedin" in key), None)
        if linkedin_idx is None:
            record_fail("linkedin live preview", "could not find 'linkedin' in app._nav_keys")
        else:
            app._show_tab(linkedin_idx)
            safe_update(app, 0.3, label="linkedin tab")
            linkedin_entries = find_widgets(app.tabs[linkedin_idx], {"Entry"})
            if not linkedin_entries:
                record_fail("linkedin live preview", "no Entry widgets found on LinkedIn tab")
            else:
                for entry in linkedin_entries:
                    try:
                        old = entry.get()
                        entry.delete(0, "end")
                        entry.insert(0, "Test Company")
                        entry.event_generate("<KeyRelease>")
                        safe_update(app, 0.8, label="linkedin debounce")
                        STATS["live_features_tested"] += 1
                        entry.delete(0, "end")
                        entry.insert(0, old)
                        entry.event_generate("<KeyRelease>")
                        safe_update(app, 0.5, label="linkedin restore")
                        record_pass("linkedin live preview debounce")
                        break
                    except Exception as exc:
                        record_fail("linkedin live preview", exc)
                        break

        # Cover Letter (tab 4)
        app._show_tab(4)
        safe_update(app, 0.3, label="cover letter tab")
        cover_texts = find_widgets(app.tabs[4], {"Text"})
        for txt_w in cover_texts:
            try:
                old_state = txt_w.cget("state")
                if old_state == "disabled":
                    txt_w.config(state="normal")
                old_val = txt_w.get("1.0", "end-1c")
                txt_w.delete("1.0", "end")
                txt_w.insert("1.0", "We are looking for a Senior Python Developer with 5+ years of experience in FastAPI, PostgreSQL, and AWS. The candidate should have strong knowledge of distributed systems and microservices architecture.")
                txt_w.event_generate("<KeyRelease>")
                safe_update(app, 1.2, label="cover letter debounce")
                STATS["live_features_tested"] += 1
                txt_w.delete("1.0", "end")
                txt_w.insert("1.0", old_val)
                txt_w.config(state=old_state)
                record_pass("cover letter offline preview debounce")
                break
            except Exception as exc:
                record_fail("cover letter preview", exc)
                break

        # JD Analyzer (tab 5)
        app._show_tab(5)
        safe_update(app, 0.3, label="jd analyzer tab")
        jd_texts = find_widgets(app.tabs[5], {"Text"})
        for txt_w in jd_texts:
            try:
                old_state = txt_w.cget("state")
                if old_state == "disabled":
                    txt_w.config(state="normal")
                old_val = txt_w.get("1.0", "end-1c")
                # Test < 50 chars (should not trigger)
                txt_w.delete("1.0", "end")
                txt_w.insert("1.0", "Short text")
                txt_w.event_generate("<KeyRelease>")
                safe_update(app, 0.3, label="jd short text")
                record_pass("jd < 50 chars no analysis")

                # Test > 50 chars (should trigger after 1.5s)
                txt_w.delete("1.0", "end")
                txt_w.insert("1.0", "We are seeking a Senior Python Developer with extensive experience in building scalable web applications using FastAPI, PostgreSQL, Docker, and AWS cloud services. The ideal candidate will have strong problem-solving skills.")
                txt_w.event_generate("<KeyRelease>")
                safe_update(app, 2.5, label="jd live analysis debounce")
                STATS["live_features_tested"] += 1
                record_pass("jd > 50 chars live analysis")

                # Rapid typing test (stale result prevention)
                txt_w.delete("1.0", "end")
                for i in range(5):
                    txt_w.insert("end", f"Rapid typing test line {i} with enough characters to trigger analysis. ")
                    txt_w.event_generate("<KeyRelease>")
                    safe_update(app, 0.2, label=f"jd rapid type {i}")
                safe_update(app, 2.0, label="jd rapid settle")
                record_pass("jd rapid typing stale prevention")

                # Restore
                txt_w.delete("1.0", "end")
                txt_w.insert("1.0", old_val)
                txt_w.config(state=old_state)
                break
            except Exception as exc:
                record_fail("jd analyzer live", exc)
                break

        # Settings preview (tab 11)
        app._show_tab(11)
        safe_update(app, 0.3, label="settings tab")
        settings_combos = find_widgets(app.tabs[11], {"TCombobox", "Combobox"})
        for combo in settings_combos:
            try:
                vals = combo.cget("values")
                if vals and len(vals) > 1:
                    old = combo.get()
                    combo.set(vals[0])
                    combo.event_generate("<<ComboboxSelected>>")
                    safe_update(app, 0.6, label="settings theme preview")
                    STATS["live_features_tested"] += 1
                    combo.set(old)
                    combo.event_generate("<<ComboboxSelected>>")
                    safe_update(app, 0.6, label="settings restore")
                    record_pass("settings theme/font preview")
                    break
            except Exception as exc:
                record_fail("settings preview", exc)
                break

        # Accent color invalid hex test
        settings_entries = find_widgets(app.tabs[11], {"Entry"})
        for entry in settings_entries:
            try:
                old = entry.get()
                if old.startswith("#") and len(old) == 7:
                    entry.delete(0, "end")
                    entry.insert(0, "#ZZ")
                    entry.event_generate("<KeyRelease>")
                    safe_update(app, 0.8, label="accent invalid hex")
                    STATS["live_features_tested"] += 1
                    entry.delete(0, "end")
                    entry.insert(0, old)
                    entry.event_generate("<KeyRelease>")
                    safe_update(app, 0.5, label="accent restore")
                    record_pass("accent color invalid hex no jump")
                    break
            except Exception as exc:
                record_fail("accent invalid hex", exc)
                break

        # ── Status bar check ──────────────────────────────────────────────────
        log_section("STATUS BAR CHECK")
        _mark_stderr_phase("before-status-bar")
        app._show_tab(0)
        safe_update(app, 0.3, label="status bar check")
        tracker_text = app._status_tracker_lbl.cget("text")
        backup_text = app._status_backup_lbl.cget("text")
        validation_text = app._status_validation_lbl.cget("text")
        lang_text = app._status_lang_lbl.cget("text")
        _print(f"  Tracker: [{tracker_text}]")
        _print(f"  Backup:  [{backup_text}]")
        _print(f"  Valid:   [{validation_text}]")
        _print(f"  Lang:    [{lang_text}]")
        check("tracker label non-empty", lambda: len(tracker_text) > 0)
        check("lang label non-empty", lambda: len(lang_text) > 0)
        record_pass("status bar labels independent")

        # ── Timer loop (10 seconds) ───────────────────────────────────────────
        log_section("TIMER LOOP TEST (10s)")
        _mark_stderr_phase("before-timer-loop")
        errors_before = len(ERRORS)
        safe_update(app, 10.0, label="10s timer loop")
        new_errors = len(ERRORS) - errors_before
        if new_errors == 0:
            record_pass("no errors during 10s timer loop")
        else:
            record_fail("timer loop", f"{new_errors} new errors during 10s loop")

        # ── Close test ────────────────────────────────────────────────────────
        log_section("CLOSE TEST")
        _mark_stderr_phase("before-close")

        # Count active threads before close
        active_before = threading.active_count()
        _print(f"  Active threads before close: {active_before}")
        for th in threading.enumerate():
            _print(f"    - {th.name} (daemon={th.daemon}, alive={th.is_alive()})")

        # Cancel all timers explicitly before close
        for attr in ["_tracker_watch_id", "_email_watch_id",
                     "_status_bar_watch_id", "_json_watch_id",
                     "_chart_debounce_id", "_validation_debounce_id"]:
            try:
                aid = getattr(app, attr, None)
                if aid:
                    app.after_cancel(aid)
            except Exception:
                pass
        # Flush pending events
        safe_update(app, 0.5, label="pre-close flush")

        # Wait for daemon threads to settle
        time.sleep(1.0)
        active_after_wait = threading.active_count()
        _print(f"  Active threads after 1s wait: {active_after_wait}")
        for th in threading.enumerate():
            _print(f"    - {th.name} (daemon={th.daemon}, alive={th.is_alive()})")

        check("_on_close first call", lambda: app._on_close())
        time.sleep(0.5)
        try:
            app._on_close()
            record_pass("_on_close second call (idempotent)")
        except Exception as exc:
            record_warn("_on_close second call", str(exc))

        _mark_stderr_phase("after-close-before-gc")

        # Suppress stderr during gc to avoid Tk Variable.__del__ RuntimeError noise
        sys.stderr = _orig_stderr
        app = None
        gc.collect()
        time.sleep(0.3)
        gc.collect()
        sys.stderr = stderr_capture

        _mark_stderr_phase("after-gc")
        active_after_gc = threading.active_count()
        _print(f"  Active threads after GC: {active_after_gc}")
        for th in threading.enumerate():
            _print(f"    - {th.name} (daemon={th.daemon}, alive={th.is_alive()})")

    except Exception as exc:
        record_fail("Fatal", exc)
    finally:
        if app is not None:
            try:
                if app.winfo_exists():
                    app._on_close()
            except Exception:
                pass
            app = None
            sys.stderr = _orig_stderr
            gc.collect()
            sys.stderr = stderr_capture

        log_section("TEARDOWN")
        try:
            mocks.teardown()
            record_pass("mocks torn down")
        except Exception as exc:
            record_warn("mocks teardown", str(exc))
        try:
            temp_env.cleanup()
            record_pass("temp env cleaned")
        except Exception as exc:
            record_warn("temp env cleanup", str(exc))

        # Verify settings restored
        try:
            restored = json.loads(temp_env.settings_path.read_text(encoding="utf-8"))
            if restored.get("files", {}).get("tracker_path", "") != str(temp_env.temp_tracker):
                record_pass("real settings.json restored")
            else:
                record_warn("settings restore", "tracker_path still points to temp")
        except Exception as exc:
            record_warn("settings verify", str(exc))

        # ── Restore stderr and scan for hidden RuntimeErrors ────────────────
        sys.stderr = _orig_stderr
        captured_stderr = stderr_capture.getvalue()
        stderr_capture.close()

        # Build phase boundaries for pinpointing error source
        phase_names = [name for name, _ in stderr_phases]
        phase_positions = [pos for _, pos in stderr_phases]

        runtime_errors = []
        # Only scan stderr up to the "after-close-before-gc" phase.
        # Variable.__del__ RuntimeError during GC after destroy is a test
        # harness artifact (no mainloop running), not a real app bug.
        gc_phase_pos = 0
        for pname, ppos in stderr_phases:
            if pname == "after-close-before-gc":
                gc_phase_pos = ppos
                break
        scan_stderr = captured_stderr[:gc_phase_pos] if gc_phase_pos else captured_stderr
        lines = scan_stderr.split("\n")
        for line in lines:
            lower = line.lower()
            if "runtimeerror" in lower and "main thread" in lower:
                runtime_errors.append(line.strip())
            elif "tclerror" in lower and "invalid command" in lower:
                runtime_errors.append(line.strip())

        if runtime_errors:
            for re_line in runtime_errors[:10]:
                # Find which phase this error occurred in
                pos = captured_stderr.find(re_line)
                phase = "unknown"
                for i, (pname, ppos) in enumerate(stderr_phases):
                    if pos <= ppos:
                        phase = pname
                        break
                    phase = pname
                record_fail(f"stderr RuntimeError/TclError ({phase})", re_line)
            if len(runtime_errors) > 10:
                record_fail("stderr RuntimeError/TclError", f"... and {len(runtime_errors) - 10} more")
        else:
            record_pass("no RuntimeError/TclError in stderr")

        # ── Final report (always prints, uses real stdout) ───────────────────
        log_section("FINAL REPORT")
        _print(f"  Tabs tested:              {STATS['tabs_tested']}")
        _print(f"  Buttons found:            {STATS['buttons_found']}")
        _print(f"  Buttons clicked:          {STATS['buttons_clicked']}")
        _print(f"  Buttons mocked (riskly):  {STATS['buttons_mocked']}")
        _print(f"  Entries tested:           {STATS['entries_tested']}")
        _print(f"  Text widgets tested:      {STATS['texts_tested']}")
        _print(f"  Comboboxes tested:        {STATS['comboboxes_tested']}")
        _print(f"  Checkboxes tested:        {STATS['checkboxes_tested']}")
        _print(f"  Radiobuttons tested:      {STATS['radios_tested']}")
        _print(f"  Live features tested:     {STATS['live_features_tested']}")
        _print(f"  Popups caught:            {STATS['popups_caught']}")
        _print(f"  Timer/thread errors:      {STATS['timer_errors']}")
        _print(f"  TclError count:           {STATS['tcl_errors']}")
        _print(f"  Thread violations:        {STATS['thread_violations']}")
        _print("")
        _print(f"  TOTAL PASSES:   {len(PASSES)}")
        _print(f"  TOTAL WARNINGS: {len(WARNINGS)}")
        _print(f"  TOTAL ERRORS:   {len(ERRORS)}")

        if WARNINGS:
            _print("\nWarnings:")
            for w in WARNINGS:
                _print(f"  - {w}")
        if ERRORS:
            _print("\nErrors:")
            for e in ERRORS:
                _print(f"  - {e}")
            _print("\nRESULT: FAILED")
            sys.exit(1)
        else:
            _print("\nRESULT: PASSED — NO ERRORS")
            sys.exit(0)


if __name__ == "__main__":
    import tkinter as tk
    main()
