"""PyWebView API for JobTracker PRO desktop bridge.
Exposes read methods and Core MVP write methods (add_application, update_application_status, edit_application).
Write methods are gated by safety checks — demo/test/staging/production workbooks with proper env vars.
Runtime-selected workbooks are forced read-only regardless of env vars.
Phase 2B: Bridge methods for Job Analysis, Cover Letter, LinkedIn, Interview Prep, Streak, Next Actions.
"""
import os
import re
import sys
import json
import math
import threading
import tempfile
from datetime import datetime, date, timedelta
from .excel_reader import ExcelReader
from .excel_writer import ExcelWriter
from .data_mapper import (
    map_applications,
    compute_kpis,
    compute_pipeline,
    compute_monthly_chart,
    compute_source_chart,
    map_salary_data,
    map_interview_history,
    map_cover_letter_history,
)
from .services.streak_service import compute_streak_data, extract_app_dates
from .services.action_service import generate_next_actions

# Ensure project root is on sys.path so feature modules can be imported
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


class ExcelBridgeAPI:
    """PyWebView API class — registered as js_api in PyWebView.
    All methods return JSON-serializable dicts.
    Read methods are always available.
    Write methods (add_application, update_application_status, edit_application) are safety-gated.
    Workbook switching is thread-safe via RLock and atomic reader/writer replacement.
    Runtime-selected workbooks are forced read-only.
    """

    def __init__(self, workbook_path: str = None, data_dir: str = None):
        if workbook_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            workbook_path = os.path.join(
                project_root,
                "Developer_Job_Application_Tracker_PRO.xlsx",
            )
        self._data_dir = data_dir or _PROJECT_ROOT
        self._lock = threading.RLock()
        self._window = None
        self.reader = ExcelReader(workbook_path)
        self.writer = ExcelWriter(workbook_path)
        self._json_lock = threading.Lock()

    def attach_window(self, window) -> None:
        """Attach the PyWebView Window instance for native dialog access."""
        self._window = window

    def _check_workbook(self) -> str | None:
        """Check if workbook exists. Returns error string or None."""
        if not os.path.exists(self.reader.workbook_path):
            return "Workbook not found. Please select a workbook."
        return None

    @staticmethod
    def _sanitize_error(e: Exception) -> str:
        """Sanitize error messages — remove file paths, tracebacks, and secrets."""
        msg = str(e)
        # Remove Windows file paths
        msg = re.sub(r'[A-Za-z]:\\[^\s"\'<>]+', '[path]', msg)
        # Remove Unix file paths
        msg = re.sub(r'/[^\s"\'<>]+', '[path]', msg)
        # Remove env var names
        msg = re.sub(r'JOBTRACKER_\w+', '[env-var]', msg)
        # Remove API key patterns
        msg = re.sub(r'sk-[A-Za-z0-9]{20,}', '[redacted]', msg)
        # Remove password/secret/token patterns — only when assigned with = or :
        msg = re.sub(r'(password|secret|token|apikey|api_key)\s*[=:]\s*\S+', r'\1=[redacted]', msg, flags=re.IGNORECASE)
        # Remove Authorization: Bearer patterns
        msg = re.sub(r'(Authorization\s*:\s*Bearer\s+)\S+', r'\1[redacted]', msg, flags=re.IGNORECASE)
        msg = re.sub(r'(Bearer\s+)\S+', r'\1[redacted]', msg, flags=re.IGNORECASE)
        # Remove URL query tokens (e.g. ?token=abc123)
        msg = re.sub(r'[?&](token|key|api_key|secret)=[^\s&]+', r'?\1=[redacted]', msg, flags=re.IGNORECASE)
        # Remove traceback text
        msg = re.sub(r'Traceback \(most recent call last\):.*?(?=\n[A-Za-z]|\Z)', '[traceback]', msg, flags=re.DOTALL)
        # Truncate
        if len(msg) > 200:
            msg = msg[:200] + '...'
        return msg.strip() or 'An unexpected error occurred'

    @staticmethod
    def _ok(data) -> dict:
        """Standard success response."""
        return {"success": True, "data": data, "error": None}

    @staticmethod
    def _err(code: str, message: str) -> dict:
        """Standard error response."""
        return {"success": False, "data": None, "error": {"code": code, "message": message}}

    def health(self) -> dict:
        """Health check — returns workbook status."""
        status = self.reader.get_workbook_status()
        return {
            "status": "ok" if status["exists"] and not status.get("error") else "error",
            "workbook_exists": status["exists"],
            "sheet_count": status.get("sheet_count", 0),
            "sheets": status.get("sheets", []),
            "error": status.get("error"),
        }

    def get_applications(self) -> dict:
        """Return all applications from the Applications sheet."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err, "count": 0}
        try:
            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)
            return {"data": applications, "error": None, "count": len(applications)}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e), "count": 0}

    def get_dashboard(self) -> dict:
        """Return dashboard summary: KPIs + charts."""
        err = self._check_workbook()
        if err:
            return {"data": None, "error": err}
        try:
            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)
            return {
                "data": {
                    "kpis": compute_kpis(applications),
                    "monthlyChart": compute_monthly_chart(applications),
                    "sourceChart": compute_source_chart(applications),
                    "pipeline": compute_pipeline(applications),
                },
                "error": None,
            }
        except Exception as e:
            return {"data": None, "error": self._sanitize_error(e)}

    def get_kpis(self) -> dict:
        """Return computed KPIs."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err}
        try:
            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)
            return {"data": compute_kpis(applications), "error": None}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e)}

    def get_pipeline(self) -> dict:
        """Return pipeline column counts."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err}
        try:
            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)
            return {"data": compute_pipeline(applications), "error": None}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e)}

    def get_salary_data(self) -> dict:
        """Return salary comparison entries."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err, "count": 0}
        try:
            headers, rows = self.reader.read_salary_comparison()
            salaries = map_salary_data(headers, rows)
            return {"data": salaries, "error": None, "count": len(salaries)}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e), "count": 0}

    def get_interview_history(self) -> dict:
        """Return interview history entries."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err, "count": 0}
        try:
            headers, rows = self.reader.read_interview_history()
            history = map_interview_history(headers, rows)
            return {"data": history, "error": None, "count": len(history)}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e), "count": 0}

    def get_cover_letter_history(self) -> dict:
        """Return cover letter history entries."""
        err = self._check_workbook()
        if err:
            return {"data": [], "error": err, "count": 0}
        try:
            headers, rows = self.reader.read_cover_letter_history()
            history = map_cover_letter_history(headers, rows)
            return {"data": history, "error": None, "count": len(history)}
        except Exception as e:
            return {"data": [], "error": self._sanitize_error(e), "count": 0}

    # ── Phase 2B.2: Write mode check (read-only) ─────────────────────────────

    def get_write_mode(self) -> dict:
        """Return write mode status. Read-only — never modifies anything.

        Returns:
            { enabled, reason, workbookPath, workbookName }
        """
        try:
            return self.writer.get_write_mode()
        except Exception as e:
            return {"enabled": False, "reason": self._sanitize_error(e), "workbookPath": None, "workbookName": None}

    # ── Phase 2B.2: Demo-only write methods ──────────────────────────────────

    def add_application(self, data: dict) -> dict:
        """Add a new application row. Demo/test workbooks only — safety gated.

        Args:
            data: dict with application fields (company, role required).

        Returns:
            { success, data, backupPath, error }
        """
        try:
            return self.writer.add_application(data)
        except Exception as e:
            return {"success": False, "error": self._sanitize_error(e)}

    def update_application_status(self, application_id: str, status: str) -> dict:
        """Update an application's status. Demo/test workbooks only — safety gated.

        Args:
            application_id: The Application ID to update.
            status: New status value.

        Returns:
            { success, data, backupPath, error }
        """
        try:
            return self.writer.update_application_status(application_id, status)
        except Exception as e:
            return {"success": False, "error": self._sanitize_error(e)}

    def edit_application(self, application_id: str, data: dict) -> dict:
        """Edit specified fields for an existing application. Safety gated.

        Only these fields can be edited: company, role, location, source, salary, fitScore, notes.

        Args:
            application_id: The stable Application ID to find and update.
            data: dict with fields to update.

        Returns:
            { success, data, backupPath, error }
        """
        try:
            return self.writer.edit_application(application_id, data)
        except Exception as e:
            return {"success": False, "error": self._sanitize_error(e)}

    # ── Workbook selection and status (read-only) ────────────────────────────

    def select_workbook(self) -> dict:
        """Open a native file dialog to select a workbook.

        Validates the selected file (read-only) and, if valid, atomically
        replaces the reader and writer for the new path. Runtime-selected
        workbooks are forced read-only regardless of environment variables.

        Thread-safe: the file dialog is opened without holding the lock.
        Reader/writer replacement is atomic under RLock.

        Returns a consistent JSON-safe response:
            Success: { success, selected, cancelled, workbookName, mode, schemaValid, writeEnabled, message, error }
            Cancel:  { success, selected, cancelled, workbookName, mode, schemaValid, writeEnabled, message, error }
            Failure: { success, selected, cancelled, workbookName, mode, schemaValid, writeEnabled, message, error }
        """
        # Check for attached window
        if self._window is None:
            return {
                "success": False,
                "selected": False,
                "cancelled": False,
                "workbookName": None,
                "mode": None,
                "schemaValid": False,
                "writeEnabled": False,
                "message": None,
                "error": "Workbook selection is not available in this mode.",
            }

        # Open file dialog WITHOUT holding the lock (user interaction)
        try:
            import webview as _wv

            # Version-safe dialog constant
            if hasattr(_wv, 'FileDialog') and hasattr(_wv.FileDialog, 'OPEN'):
                dialog_type = _wv.FileDialog.OPEN
            elif hasattr(_wv, 'OPEN_DIALOG'):
                dialog_type = _wv.OPEN_DIALOG
            else:
                return {
                    "success": False,
                    "selected": False,
                    "cancelled": False,
                    "workbookName": None,
                    "mode": None,
                    "schemaValid": False,
                    "writeEnabled": False,
                    "message": None,
                    "error": "File dialog is not supported in this PyWebView version.",
                }

            result = self._window.create_file_dialog(
                dialog_type,
                allow_multiple=False,
                file_types=('Excel Workbooks (*.xlsx)',),
            )
        except Exception:
            return {
                "success": False,
                "selected": False,
                "cancelled": False,
                "workbookName": None,
                "mode": None,
                "schemaValid": False,
                "writeEnabled": False,
                "message": None,
                "error": "Could not open the file dialog.",
            }

        # Normalize result safely (may be None, tuple, list, or string)
        if result is None or (isinstance(result, (tuple, list)) and len(result) == 0):
            return {
                "success": True,
                "selected": False,
                "cancelled": True,
                "workbookName": None,
                "mode": None,
                "schemaValid": None,
                "writeEnabled": False,
                "message": "Workbook selection cancelled.",
                "error": None,
            }

        if isinstance(result, (tuple, list)):
            file_path = str(result[0]) if len(result) > 0 else ""
        elif isinstance(result, str):
            file_path = result
        else:
            file_path = str(result)

        if not file_path or not file_path.strip():
            return {
                "success": True,
                "selected": False,
                "cancelled": True,
                "workbookName": None,
                "mode": None,
                "schemaValid": None,
                "writeEnabled": False,
                "message": "Workbook selection cancelled.",
                "error": None,
            }

        # Validate the selected workbook (read-only — never modifies)
        validation = self.validate_workbook(file_path)
        if not validation.get("valid"):
            return {
                "success": False,
                "selected": False,
                "cancelled": False,
                "workbookName": validation.get("workbookName"),
                "mode": None,
                "schemaValid": False,
                "writeEnabled": False,
                "message": None,
                "error": validation.get("error", "The selected workbook is not compatible with JobTracker PRO."),
            }

        # Construct new reader and writer BEFORE replacing (atomic switch)
        try:
            new_reader = ExcelReader(file_path)
            new_writer = ExcelWriter(file_path, force_read_only=True)
        except Exception:
            # Construction failed — keep existing workbook active
            return {
                "success": False,
                "selected": False,
                "cancelled": False,
                "workbookName": os.path.basename(file_path),
                "mode": None,
                "schemaValid": True,
                "writeEnabled": False,
                "message": None,
                "error": "Failed to initialize the selected workbook. The previous workbook remains active.",
            }

        # Atomic replacement under lock
        with self._lock:
            self.reader = new_reader
            self.writer = new_writer
            # Reset all workbook-dependent state
            self.writer._session_backup_done = False
            self.writer._session_backup_path = None

        return {
            "success": True,
            "selected": True,
            "cancelled": False,
            "workbookName": os.path.basename(file_path),
            "mode": "read-only",
            "schemaValid": True,
            "writeEnabled": False,
            "message": "Workbook selected successfully in read-only mode. Restart JobTracker PRO with an explicit write-mode configuration to enable changes.",
            "error": None,
        }

    def validate_workbook(self, file_path: str) -> dict:
        """Validate a workbook file for compatibility. Read-only — never modifies the file.

        Checks:
        - Path is present
        - Path exists
        - Path is a regular file (not a directory)
        - File extension is .xlsx, case-insensitive
        - Workbook opens successfully (not corrupted)
        - Applications sheet exists
        - Required headers present (Application ID, Company, Role, Status)
        - Application ID header exists explicitly

        Returns:
            { valid, workbookName, sheets, missingHeaders, error }
        """
        try:
            if not file_path or not str(file_path).strip():
                return {"valid": False, "error": "No file path provided."}

            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found. Please check the path and try again."}

            if not os.path.isfile(file_path):
                return {"valid": False, "error": "The selected path is not a file. Please select an .xlsx workbook."}

            if not file_path.lower().endswith(".xlsx"):
                return {"valid": False, "error": "Invalid file type. Please select an .xlsx workbook."}

            import openpyxl
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            sheets = wb.sheetnames

            if "Applications" not in sheets:
                wb.close()
                return {
                    "valid": False,
                    "workbookName": os.path.basename(file_path),
                    "sheets": sheets,
                    "error": "The 'Applications' sheet was not found in this workbook.",
                }

            ws = wb["Applications"]
            headers = []
            for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                headers = [str(v).strip() if v is not None else "" for v in row]
            wb.close()

            required = {"Application ID", "Company", "Role", "Status"}
            header_set = set(headers)
            missing = required - header_set

            if missing:
                return {
                    "valid": False,
                    "workbookName": os.path.basename(file_path),
                    "sheets": sheets,
                    "missingHeaders": sorted(missing),
                    "error": f"Required headers missing: {', '.join(sorted(missing))}",
                }

            # Explicit Application ID check
            if "Application ID" not in header_set:
                return {
                    "valid": False,
                    "workbookName": os.path.basename(file_path),
                    "sheets": sheets,
                    "error": "The 'Application ID' header is required but was not found.",
                }

            return {
                "valid": True,
                "workbookName": os.path.basename(file_path),
                "sheets": sheets,
                "missingHeaders": [],
                "error": None,
            }
        except Exception:
            return {"valid": False, "error": "Could not read workbook. The file may be corrupted or incompatible."}

    def get_workbook_status(self) -> dict:
        """Return current workbook status for UI display. Read-only.

        Returns:
            {
                workbookName, mode, available, schemaValid,
                writeEnabled, lastBackupFilename, error
            }
        """
        with self._lock:
            wb_path = self.reader.workbook_path
            filename = os.path.basename(wb_path) if wb_path else None
            available = os.path.exists(wb_path) if wb_path else False

            # Determine mode
            if not wb_path or not available:
                mode = "mock"
            elif getattr(self.writer, '_force_read_only', False):
                mode = "read-only"
            else:
                upper = filename.upper()
                if filename == "Developer_Job_Application_Tracker_PRO.xlsx":
                    mode = "production"
                elif "_STAGING" in upper:
                    mode = "staging"
                elif "_DEMO" in upper or "_TEST" in upper:
                    mode = "demo"
                else:
                    mode = "read-only"

            # Check schema
            schema_valid = False
            if available:
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(wb_path, read_only=True, data_only=True)
                    if "Applications" in wb.sheetnames:
                        ws = wb["Applications"]
                        headers = []
                        for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                            headers = [str(v).strip() if v is not None else "" for v in row]
                        wb.close()
                        required = {"Application ID", "Company", "Role", "Status"}
                        schema_valid = required.issubset(set(headers))
                    else:
                        wb.close()
                except Exception:
                    schema_valid = False

            # Check write mode
            write_mode = self.writer.get_write_mode()

            # Find latest backup filename
            last_backup = None
            try:
                backup_list = self.writer.backup.list_backups()
                if backup_list.get("success") and backup_list.get("backups"):
                    last_backup = backup_list["backups"][0].get("filename")
            except Exception:
                pass

            return {
                "workbookName": filename,
                "mode": mode,
                "available": available,
                "schemaValid": schema_valid,
                "writeEnabled": write_mode.get("enabled", False),
                "writeMode": write_mode.get("mode", "disabled"),
                "lastBackupFilename": last_backup,
                "error": None,
            }

    # ── Phase 2B: Feature Bridge Methods ──────────────────────────────────────

    # ── 4.1 Job Analysis ──────────────────────────────────────────────────────

    def analyze_job_description(self, payload: dict) -> dict:
        """Analyze a job description using the Python analysis module.

        Args:
            payload: { jobDescription: str, candidateSkills: [str] }

        Returns:
            { success, data: { fitScore, seniority, salaryEstimate, matchedKeywords,
              missingKeywords, techStack, greenFlags, redFlags, recommendedKeywords, summary }, error }
        """
        try:
            jd_text = (payload or {}).get("jobDescription", "").strip()
            if not jd_text:
                return self._err("VALIDATION_ERROR", "Job description text is required.")
            if len(jd_text) < 20:
                return self._err("VALIDATION_ERROR", "Job description must contain at least 20 characters.")

            candidate_skills = (payload or {}).get("candidateSkills", [])
            if not isinstance(candidate_skills, list):
                candidate_skills = []
            skills_str = ", ".join(candidate_skills)

            import job_description_analyzer as jda
            import io as _io
            import contextlib

            # Suppress print output from the analyzer
            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                result = jda.analyze(jd_text, my_skills_input=skills_str)

            # Normalize the result to frontend format
            fit_score = result.get("fit_score")
            if fit_score is None:
                fit_score = 0

            jd_skills = result.get("skills", [])
            candidate_skills_lower = [s.strip().lower() for s in candidate_skills]
            matched = [s for s in jd_skills if s in candidate_skills_lower]
            missing = [s for s in jd_skills if s not in candidate_skills_lower]

            salary_posted = result.get("salary_posted")
            est_min, est_max = result.get("salary_estimate", (0, 0))
            if salary_posted:
                salary_est = salary_posted
            else:
                salary_est = f"${est_min:,} - ${est_max:,} USD/year (estimated)"

            seniority = result.get("seniority", "mid")
            seniority_display = {
                "intern": "Intern (0-1 year)",
                "junior": "Junior (1-2 years)",
                "mid": "Mid-level (2-5 years)",
                "senior": "Senior (5+ years)",
                "staff": "Staff/Principal (10+ years)",
                "manager": "Engineering Manager",
            }.get(seniority, seniority)

            cl_keywords = result.get("cover_letter_keywords", [])

            summary = (
                f"Detected {seniority_display} role. "
                f"Fit score: {fit_score}/100. "
                f"Estimated salary: {salary_est}. "
                f"Found {len(jd_skills)} tech keywords, {len(result.get('red_flags', []))} red flags, "
                f"{len(result.get('green_flags', []))} green flags."
            )

            data = {
                "fitScore": fit_score,
                "seniority": seniority_display,
                "salaryEstimate": salary_est,
                "matchedKeywords": matched,
                "missingKeywords": missing,
                "techStack": jd_skills,
                "greenFlags": result.get("green_flags", []),
                "redFlags": result.get("red_flags", []),
                "recommendedKeywords": cl_keywords,
                "summary": summary,
            }
            return self._ok(data)
        except Exception as e:
            return self._err("ANALYSIS_ERROR", self._sanitize_error(e))

    # ── 4.2 Cover Letter ──────────────────────────────────────────────────────

    def generate_cover_letter(self, payload: dict) -> dict:
        """Generate a cover letter using the Python cover letter module.

        Uses OpenAI if API key is configured in settings, otherwise offline template.
        API key is never sent to frontend.

        Args:
            payload: { name, company, role, years, currentRole, field, achievement, tone, jobDescription, notes }

        Returns:
            { success, data: { content, mode, wordCount }, error }
        """
        try:
            p = payload or {}
            company = (p.get("company") or "").strip()
            role = (p.get("role") or "").strip()
            name = (p.get("name") or "").strip()

            if not company:
                return self._err("VALIDATION_ERROR", "Company name is required.")
            if not role:
                return self._err("VALIDATION_ERROR", "Job title is required.")
            if not name:
                return self._err("VALIDATION_ERROR", "Your name is required.")

            years = (p.get("years") or "3").strip()
            field = (p.get("field") or "software development").strip()
            tone = (p.get("tone") or "professional").strip()
            jd_text = (p.get("jobDescription") or "").strip()
            notes = (p.get("notes") or "").strip()
            achievement = (p.get("achievement") or "").strip()
            extra_notes = notes or achievement

            # Get API key from settings (never expose to frontend)
            api_key = ""
            try:
                import settings
                api_key = settings.get_openai_key() or ""
            except Exception:
                pass

            import cover_letter_generator as clg
            import io as _io
            import contextlib

            # Determine mode before generation
            use_ai = bool(api_key and api_key.strip())

            buf = _io.StringIO()
            with contextlib.redirect_stdout(buf):
                letter = clg.generate(
                    company=company,
                    role=role,
                    jd_text=jd_text or f"{role} at {company}",
                    your_name=name,
                    years=years,
                    field=field,
                    tone=tone,
                    extra_notes=extra_notes,
                    api_key=api_key,
                )

            # Detect if fallback was used by checking the stdout output
            stdout_output = buf.getvalue()
            used_ai = use_ai and "falling back" not in stdout_output.lower()
            mode = "ai" if used_ai else "offline"

            word_count = len(letter.split())

            data = {
                "content": letter,
                "mode": mode,
                "wordCount": word_count,
            }
            return self._ok(data)
        except Exception as e:
            return self._err("GENERATION_ERROR", self._sanitize_error(e))

    # ── 4.3 LinkedIn Message ──────────────────────────────────────────────────

    # Mapping from frontend message types to Python template names
    _LINKEDIN_TYPE_MAP = {
        "connection": "Cold Connection",
        "referral": "Referral Request",
        "recruiter": "Cold Connection",
        "follow-up": "Follow-Up After Applying",
        "informational": "Reconnecting",
    }

    def generate_linkedin_message(self, payload: dict) -> dict:
        """Generate a LinkedIn message using the Python module.

        Args:
            payload: { messageType, recipientName, recipientRole, company, targetRole,
                       yourName, yourRole, field, years, highlight, notes }

        Returns:
            { success, data: { content, messageType, characterCount, characterLimit }, error }
        """
        try:
            p = payload or {}
            msg_type_frontend = (p.get("messageType") or "connection").strip()
            python_type = self._LINKEDIN_TYPE_MAP.get(msg_type_frontend, "Cold Connection")

            recipient_name = (p.get("recipientName") or "").strip()
            company = (p.get("company") or "").strip()
            your_name = (p.get("yourName") or "").strip()

            if not recipient_name:
                return self._err("VALIDATION_ERROR", "Recipient name is required.")
            if not company:
                return self._err("VALIDATION_ERROR", "Company name is required.")
            if not your_name:
                return self._err("VALIDATION_ERROR", "Your name is required.")

            your_role = (p.get("yourRole") or "Software Developer").strip()
            your_field = (p.get("field") or "software development").strip()
            years = (p.get("years") or "3").strip()
            target_role = (p.get("targetRole") or "").strip()
            highlight = (p.get("highlight") or "").strip()
            notes = (p.get("notes") or "").strip()

            # Use recipient's first name (first word)
            first_name = recipient_name.split()[0] if recipient_name else "there"

            import linkedin_message_generator as lmg

            message = lmg.generate(
                message_type=python_type,
                your_name=your_name,
                your_role=your_role,
                your_field=your_field,
                years=years,
                first_name=first_name,
                company=company,
                target_role=target_role,
                their_field=your_field,
                highlight=highlight or notes,
                reason=notes,
                shared_context=notes,
            )

            char_limit = lmg.get_char_limit(python_type)

            data = {
                "content": message,
                "messageType": msg_type_frontend,
                "characterCount": len(message),
                "characterLimit": char_limit,
            }
            return self._ok(data)
        except Exception as e:
            return self._err("GENERATION_ERROR", self._sanitize_error(e))

    # ── 4.4 Interview Prep ────────────────────────────────────────────────────

    # Mapping from Python categories to frontend categories
    _INTERVIEW_CATEGORY_MAP = {
        "Behavioral (STAR)": "Behavioral",
        "Technical / Problem Solving": "Technical",
        "Motivation & Culture Fit": "Behavioral",
        "Salary & Logistics": "Behavioral",
    }

    def get_interview_questions(self, payload: dict = None) -> dict:
        """Get interview questions from the Python question bank.

        Args:
            payload: { category, role, technologyStack, difficulty, count }

        Returns:
            { success, data: [{ id, category, difficulty, question, tips, starRelevant }], error }
        """
        try:
            p = payload or {}
            requested_category = (p.get("category") or "all").strip().lower()
            count = p.get("count", 10)
            try:
                count = int(count)
            except (ValueError, TypeError):
                count = 10

            import interview_prep as ip

            python_categories = ip.get_categories()
            questions = []

            for cat in python_categories:
                frontend_cat = self._INTERVIEW_CATEGORY_MAP.get(cat, "Behavioral")
                # Filter by category if not "all"
                if requested_category != "all" and frontend_cat.lower() != requested_category:
                    continue

                cat_questions = ip.get_questions(cat)
                tip = ip.get_tip(cat)
                tips_list = [tip] if tip else []

                for i, q_text in enumerate(cat_questions):
                    # Determine STAR relevance from QUESTION_KEYWORDS
                    qk = ip.QUESTION_KEYWORDS.get(q_text, {})
                    star_relevant = qk.get("star_expected", cat == "Behavioral (STAR)")

                    # Assign difficulty heuristically
                    if cat == "Technical / Problem Solving":
                        difficulty = "Hard" if i < 3 else "Medium"
                    elif cat == "Behavioral (STAR)":
                        difficulty = "Medium"
                    else:
                        difficulty = "Easy"

                    q_id = f"{frontend_cat.lower().replace(' ', '-')}-{i}"

                    questions.append({
                        "id": q_id,
                        "category": frontend_cat,
                        "difficulty": difficulty,
                        "question": q_text,
                        "tips": tips_list,
                        "starRelevant": star_relevant,
                    })

            # Limit count
            questions = questions[:count]

            return self._ok(questions)
        except Exception as e:
            return self._err("LOAD_ERROR", self._sanitize_error(e))

    def save_interview_practice(self, payload: dict) -> dict:
        """Save an interview practice entry to JSON with atomic write.

        Args:
            payload: { questionId, question, category, answer, elapsedSeconds, selfRating, notes }

        Returns:
            { success, data: { saved: true }, error }
        """
        try:
            p = payload or {}
            question = (p.get("question") or "").strip()
            answer = (p.get("answer") or "").strip()
            category = (p.get("category") or "Behavioral").strip()

            if not question:
                return self._err("VALIDATION_ERROR", "Question text is required.")
            if not answer:
                return self._err("VALIDATION_ERROR", "Answer text is required.")

            self_rating = p.get("selfRating", 0)
            try:
                self_rating = int(self_rating)
            except (ValueError, TypeError):
                self_rating = 0
            if self_rating < 1 or self_rating > 5:
                return self._err("VALIDATION_ERROR", "Self-rating must be between 1 and 5.")

            elapsed = p.get("elapsedSeconds", 0)
            try:
                elapsed = float(elapsed)
            except (ValueError, TypeError):
                elapsed = 0.0
            if math.isnan(elapsed) or math.isinf(elapsed):
                elapsed = 0.0

            notes = (p.get("notes") or "").strip()
            word_count = len(answer.split())

            # Map frontend category back to Python category for storage
            reverse_cat_map = {v: k for k, v in self._INTERVIEW_CATEGORY_MAP.items()}
            python_category = reverse_cat_map.get(category, "Behavioral (STAR)")

            entry = {
                "question": question,
                "category": python_category,
                "score": self_rating,
                "elapsed_s": elapsed,
                "note": notes,
                "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "date": datetime.now().isoformat(),
                "word_count": word_count,
                "self_rating": self_rating,
            }

            # Atomic write
            scores_file = os.path.join(self._data_dir, "interview_scores.json")
            with self._json_lock:
                existing = []
                if os.path.exists(scores_file):
                    try:
                        with open(scores_file, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    except (json.JSONDecodeError, Exception):
                        # Corrupt JSON — backup and start fresh
                        try:
                            backup_path = scores_file + ".corrupt_backup"
                            os.replace(scores_file, backup_path)
                        except Exception:
                            pass  # Best effort — can't recover corrupt file, proceed with empty list
                        existing = []
                existing.append(entry)
                # Atomic write: temp file + os.replace
                tmp_fd, tmp_path = tempfile.mkstemp(
                    dir=os.path.dirname(scores_file),
                    suffix=".tmp",
                )
                try:
                    with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                        json.dump(existing, f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, scores_file)
                except Exception:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    raise

            return self._ok({"saved": True})
        except Exception as e:
            return self._err("SAVE_ERROR", self._sanitize_error(e))

    def get_interview_practice_history(self) -> dict:
        """Get interview practice history from JSON.

        Returns:
            { success, data: { entries: [...], stats: { totalAnswers, avgScore, byCategory } }, error }
        """
        try:
            scores_file = os.path.join(self._data_dir, "interview_scores.json")
            entries = []
            if os.path.exists(scores_file):
                try:
                    with open(scores_file, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                except (json.JSONDecodeError, Exception):
                    entries = []

            # Normalize entries for frontend
            normalized = []
            for i, entry in enumerate(entries):
                cat = entry.get("category", "Behavioral (STAR)")
                frontend_cat = self._INTERVIEW_CATEGORY_MAP.get(cat, "Behavioral")
                normalized.append({
                    "id": f"entry-{i}",
                    "question": entry.get("question", ""),
                    "category": frontend_cat,
                    "answer": entry.get("note", ""),
                    "score": entry.get("score", 0),
                    "selfRating": entry.get("self_rating", entry.get("score", 0)),
                    "elapsedSeconds": entry.get("elapsed_s", 0),
                    "wordCount": entry.get("word_count", 0),
                    "completedAt": entry.get("date", ""),
                    "notes": entry.get("note", ""),
                })

            # Compute stats
            total = len(normalized)
            avg_score = 0
            if total > 0:
                scores = [e.get("score", 0) for e in normalized]
                avg_score = round(sum(scores) / total, 1)

            by_category = {}
            for e in normalized:
                cat = e.get("category", "Unknown")
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(e.get("score", 0))
            cat_avgs = {c: round(sum(v) / len(v), 1) for c, v in by_category.items()}

            data = {
                "entries": normalized,
                "stats": {
                    "totalAnswers": total,
                    "avgScore": avg_score,
                    "byCategory": cat_avgs,
                },
            }
            return self._ok(data)
        except Exception as e:
            return self._err("LOAD_ERROR", self._sanitize_error(e))

    # ── 4.5 Streak Data ───────────────────────────────────────────────────────

    def get_streak_data(self) -> dict:
        """Get streak data from Excel applications + streak_data.json + settings.

        Computes daily/weekly counts from Date Applied column in Applications sheet.
        Falls back to streak_data.json entries if Excel data is unavailable.
        Reads goals from settings.json.

        Returns:
            { success, data: { todayCount, weekCount, dailyGoal, weeklyGoal, currentStreak, longestStreak, lastActiveDate }, error }
        """
        try:
            # Get goals from settings
            daily_goal = 5
            weekly_goal = 20
            try:
                import settings
                daily_goal = int(settings.get_daily_goal())
                weekly_goal = int(settings.get_weekly_goal())
            except Exception:
                pass

            # Try to get dates from Excel Applications sheet
            app_dates = []
            err = self._check_workbook()
            if not err:
                try:
                    headers, rows = self.reader.read_applications()
                    app_dates = extract_app_dates(headers, rows)
                except Exception:
                    pass

            streak_json = os.path.join(self._data_dir, "streak_data.json")
            data = compute_streak_data(
                app_dates=app_dates,
                daily_goal=daily_goal,
                weekly_goal=weekly_goal,
                streak_json_path=streak_json,
            )
            return self._ok(data)
        except Exception as e:
            return self._err("LOAD_ERROR", self._sanitize_error(e))

    # ── 4.6 Next Best Actions ─────────────────────────────────────────────────

    def get_next_actions(self) -> dict:
        """Generate deterministic next actions from real Excel application data.

        Rules:
        1. Overdue follow-up on active applications
        2. Follow-up due today
        3. Upcoming interviews
        4. Interview status but missing interview date
        5. Offer status but missing salary/notes
        6. Stale active applications (no update in 14+ days)
        7. High fit score but still in Saved status
        8. Active applications missing Application URL

        Returns:
            { success, data: [{ id, type, priority, title, description, applicationId, company, role, dueDate }], error }
        """
        try:
            err = self._check_workbook()
            if err:
                return self._ok([])

            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)

            actions = generate_next_actions(applications, rows, headers)
            return self._ok(actions)
        except Exception as e:
            return self._err("LOAD_ERROR", self._sanitize_error(e))

    # ── Export Report ──────────────────────────────────────────────────────────

    def export_report(self, payload: dict = None) -> dict:
        """Export a text report from Excel data.

        Args:
            payload: { type: "monthly" | "weekly" }

        Returns:
            { success, data: { content, filename }, error }
        """
        try:
            err = self._check_workbook()
            if err:
                return self._err("WORKBOOK_ERROR", err)

            p = payload or {}
            report_type = (p.get("type") or "monthly").strip()

            headers, rows = self.reader.read_applications()
            applications = map_applications(headers, rows)

            total = len(applications)
            active = sum(1 for a in applications if a["status"] not in ("Rejected", "Ghosted"))
            interviews = sum(1 for a in applications if a["status"] in ("Phone Screen", "Technical", "Onsite"))
            offers = sum(1 for a in applications if a["status"] == "Offer")
            rejected = sum(1 for a in applications if a["status"] == "Rejected")
            ghosted = sum(1 for a in applications if a["status"] == "Ghosted")

            response_rate = 0
            if total > 0:
                responded = sum(1 for a in applications if a["status"] not in ("Saved", "Applied", "Ghosted"))
                response_rate = round((responded / total) * 100)

            today_str = datetime.now().strftime("%Y-%m-%d")

            content = f"""JobTracker PRO — {report_type.title()} Report
Generated: {today_str}
{'=' * 50}

SUMMARY
-------
Total Applications:  {total}
Active:              {active}
Interviews:          {interviews}
Offers:              {offers}
Rejected:            {rejected}
Ghosted:             {ghosted}
Response Rate:       {response_rate}%

RECENT APPLICATIONS
-------------------
"""

            # Show top 10 most recent
            sorted_apps = sorted(applications, key=lambda a: a.get("appliedDate", ""), reverse=True)
            for a in sorted_apps[:10]:
                content += f"\n  {a.get('company', '?')} — {a.get('role', '?')}\n"
                content += f"    Status: {a.get('status', '?')}  |  Applied: {a.get('appliedDate', 'N/A')}  |  Fit: {a.get('fitScore', 0)}/100\n"

            if not sorted_apps:
                content += "  No applications recorded yet.\n"

            content += f"\n{'=' * 50}\nGenerated by JobTracker PRO\n"

            filename = f"report_{report_type}_{today_str}.txt"

            return self._ok({"content": content, "filename": filename})
        except Exception as e:
            return self._err("EXPORT_ERROR", self._sanitize_error(e))
