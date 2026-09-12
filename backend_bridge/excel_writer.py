"""Excel writer for JobTracker PRO — Core MVP demo + staging + production writes.

Implements add_application, update_application_status, and edit_application with strict safety:
- Backup before write (via ExcelBackup)
- Safety gate: demo/test always allowed; staging requires env var; production requires explicit opt-in
- Atomic save via temp file + os.replace
- Post-write validation
- Rollback from backup if validation fails
"""
import os
import shutil
import tempfile
from datetime import datetime
from typing import Any

import openpyxl

from .excel_backup import ExcelBackup
from .data_mapper import _normalize_status


# Required headers in the Applications sheet
REQUIRED_HEADERS = {
    "Application ID", "Company", "Role", "Status",
}

# All known headers in column order (from fixture/real workbook)
KNOWN_HEADERS = [
    "Application ID", "Company", "Role", "Location", "Country", "Remote",
    "Salary", "Source", "Date Applied", "Status", "Priority", "Fit Score",
    "Follow-up Date", "Recruiter", "LinkedIn Recruiter", "Interview Date",
    "Offer", "Application URL", "Company Career Page", "Resume Version",
    "Cover Letter Version", "Visa Sponsorship", "Employment Type",
    "Work Authorization", "Referral", "Expected Salary", "Current Stage",
    "Days Since Applied", "Days Until Follow-up", "Interview Count",
    "Favorite", "Archive", "Notes",
]

# Production workbook basename — writes are blocked for this file
PRODUCTION_WORKBOOK_NAME = "Developer_Job_Application_Tracker_PRO.xlsx"


class ExcelWriter:
    """Safe Excel writer with backup-before-write and multi-tier safety gate."""

    def __init__(self, workbook_path: str, backup_dir: str = "backups", force_read_only: bool = False):
        self.workbook_path = workbook_path
        self.backup = ExcelBackup(workbook_path, backup_dir=backup_dir)
        self._session_backup_done = False
        self._session_backup_path = None
        self._force_read_only = force_read_only

    def _ensure_session_backup(self) -> dict | None:
        """Create a session safety backup before the first production write.

        Returns error dict if session backup fails (blocking the write), None if OK.
        Only runs once per instance (session). Non-production modes skip this.
        """
        filename = os.path.basename(self.workbook_path)
        is_production = filename == PRODUCTION_WORKBOOK_NAME

        if not is_production:
            return None

        if self._session_backup_done:
            return None

        result = self.backup.create_session_backup()
        if not result["success"]:
            return {
                "success": False,
                "error": f"Session safety backup failed — production writes blocked: {result['error']}",
            }

        self._session_backup_done = True
        self._session_backup_path = result["backupPath"]
        return None

    def _check_write_safety(self) -> dict | None:
        """Run all safety gate checks. Returns error dict if any check fails, None if safe.

        Checks:
        0. force_read_only flag (runtime-selected workbooks)
        1. JOBTRACKER_WORKBOOK_PATH env var is explicitly set
        2. Workbook filename contains _DEMO, _TEST, _STAGING, or is the production workbook
        3. If _STAGING: JOBTRACKER_ENABLE_STAGING_WRITES=1 must be explicitly set
        4. If production workbook: JOBTRACKER_ENABLE_PRODUCTION_WRITES=1 must be explicitly set
        5. Workbook file exists
        6. Applications sheet exists with required headers
        """
        # Check 0: Runtime-selected workbooks are forced read-only
        if self._force_read_only:
            return {
                "success": False,
                "error": "Runtime-selected workbooks open in read-only mode. Restart JobTracker PRO with an explicit write-mode configuration to enable changes.",
            }

        # Check 1: JOBTRACKER_WORKBOOK_PATH must be explicitly set
        env_path = os.environ.get("JOBTRACKER_WORKBOOK_PATH")
        if not env_path:
            return {
                "success": False,
                "error": "Write actions require JOBTRACKER_WORKBOOK_PATH to be explicitly set.",
            }

        # Check 2: Determine workbook type
        filename = os.path.basename(self.workbook_path)
        upper_name = filename.upper()
        is_demo = "_DEMO" in upper_name or "_TEST" in upper_name
        is_staging = "_STAGING" in upper_name
        is_production = filename == PRODUCTION_WORKBOOK_NAME

        if not is_demo and not is_staging and not is_production:
            return {
                "success": False,
                "error": "Write actions are only enabled for demo/test/staging/production workbooks.",
            }

        # Check 3: Staging writes require explicit JOBTRACKER_ENABLE_STAGING_WRITES=1
        if is_staging and not is_demo:
            staging_enabled = os.environ.get("JOBTRACKER_ENABLE_STAGING_WRITES", "")
            if staging_enabled != "1":
                return {
                    "success": False,
                    "error": "Staging writes require JOBTRACKER_ENABLE_STAGING_WRITES=1 environment variable.",
                }

        # Check 4: Production writes require explicit JOBTRACKER_ENABLE_PRODUCTION_WRITES=1
        if is_production:
            prod_enabled = os.environ.get("JOBTRACKER_ENABLE_PRODUCTION_WRITES", "")
            if prod_enabled != "1":
                return {
                    "success": False,
                    "error": "Production writes require JOBTRACKER_ENABLE_PRODUCTION_WRITES=1 environment variable.",
                }

        # Check 4: Workbook must exist
        if not os.path.exists(self.workbook_path):
            return {
                "success": False,
                "error": f"Workbook not found: {self.workbook_path}",
            }

        # Check 5: Applications sheet must exist with required headers
        try:
            wb = openpyxl.load_workbook(self.workbook_path, read_only=True, data_only=True)
            if "Applications" not in wb.sheetnames:
                wb.close()
                return {
                    "success": False,
                    "error": "Applications sheet not found in workbook",
                }
            ws = wb["Applications"]
            headers = []
            for row in ws.iter_rows(min_row=1, max_row=1, values_only=True):
                headers = [str(v).strip() if v is not None else "" for v in row]
            wb.close()

            header_set = set(headers)
            missing = REQUIRED_HEADERS - header_set
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required headers: {', '.join(sorted(missing))}",
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to read workbook headers: {e}",
            }

        return None  # All checks passed

    def _atomic_save(self, wb: openpyxl.Workbook) -> dict:
        """Save workbook atomically via temp file + os.replace.

        Args:
            wb: The openpyxl Workbook object to save.

        Returns:
            dict with success/error.
        """
        tmp_fd, tmp_path = tempfile.mkstemp(
            suffix=".xlsx", dir=os.path.dirname(self.workbook_path)
        )
        os.close(tmp_fd)

        try:
            wb.save(tmp_path)
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return {"success": False, "error": f"Failed to save temp file: {e}"}

        # Validate temp file can be opened
        try:
            test_wb = openpyxl.load_workbook(tmp_path, read_only=True)
            test_wb.close()
        except Exception as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return {"success": False, "error": f"Temp file validation failed: {e}"}

        # Atomic replace
        try:
            os.replace(tmp_path, self.workbook_path)
        except OSError as e:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return {"success": False, "error": f"Atomic replace failed: {e}"}

        return {"success": True, "error": None}

    def get_write_mode(self) -> dict:
        """Check if write mode is active. Read-only — never writes anything.

        Returns:
            {
                enabled: bool,
                mode: str,  # "demo", "staging", "production", or "disabled"
                reason: str,
                workbookPath: str | None,
                workbookName: str | None,
            }
        """
        filename = os.path.basename(self.workbook_path)
        upper_name = filename.upper()
        is_staging = "_STAGING" in upper_name
        is_production = filename == PRODUCTION_WORKBOOK_NAME

        if self._force_read_only:
            return {
                "enabled": False,
                "mode": "read-only",
                "reason": "Runtime-selected workbook — read-only mode. Restart with explicit write-mode configuration to enable changes.",
                "workbookPath": self.workbook_path,
                "workbookName": filename,
                "sessionBackupPath": None,
            }

        gate_error = self._check_write_safety()
        if gate_error is None:
            if is_production:
                mode = "production"
                mode_label = "Production write mode"
            elif is_staging:
                mode = "staging"
                mode_label = "Staging write mode"
            else:
                mode = "demo"
                mode_label = "Demo write mode"
            return {
                "enabled": True,
                "mode": mode,
                "reason": f"{mode_label} active: {filename}",
                "workbookPath": self.workbook_path,
                "workbookName": filename,
                "sessionBackupPath": self._session_backup_path if is_production else None,
            }
        return {
            "enabled": False,
            "mode": "disabled",
            "reason": gate_error["error"],
            "workbookPath": self.workbook_path,
            "workbookName": filename,
        }

    def add_application(self, data: dict) -> dict:
        """Add a new application row to the Applications sheet.

        Args:
            data: dict with keys matching Applications sheet columns.
                  Required: company, role. Optional: status, location, salary, etc.

        Returns:
            { success, data, backupPath, error }
        """
        # Safety gate
        gate_error = self._check_write_safety()
        if gate_error:
            return gate_error

        # Session safety backup (production only, first write of session)
        session_error = self._ensure_session_backup()
        if session_error:
            return session_error

        # Validate required fields
        company = str(data.get("company", "")).strip()
        role = str(data.get("role", "")).strip()
        if not company or not role:
            return {
                "success": False,
                "error": "company and role are required fields",
            }

        # Create backup before write
        backup_result = self.backup.create_backup()
        if not backup_result["success"]:
            return {
                "success": False,
                "error": f"Backup failed — write aborted: {backup_result['error']}",
            }
        backup_path = backup_result["backupPath"]

        # Open workbook for writing
        try:
            wb = openpyxl.load_workbook(self.workbook_path)
        except Exception as e:
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Failed to open workbook: {e}",
            }

        try:
            ws = wb["Applications"]

            # Read headers from row 1
            headers = []
            for cell in ws[1]:
                headers.append(str(cell.value).strip() if cell.value is not None else "")

            # Generate Application ID
            app_id = f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # Build row data in header order
            row_values = []
            for h in headers:
                if h == "Application ID":
                    row_values.append(app_id)
                elif h == "Company":
                    row_values.append(company)
                elif h == "Role":
                    row_values.append(role)
                elif h == "Status":
                    status = str(data.get("status", "Saved")).strip()
                    row_values.append(_normalize_status(status))
                elif h == "Location":
                    row_values.append(str(data.get("location", "")))
                elif h == "Remote":
                    row_values.append(str(data.get("remote", data.get("workType", ""))))
                elif h == "Salary":
                    row_values.append(str(data.get("salary", "")))
                elif h == "Source":
                    row_values.append(str(data.get("source", "")))
                elif h == "Date Applied":
                    date_applied = str(data.get("appliedDate", data.get("dateApplied", "")))
                    row_values.append(date_applied if date_applied else datetime.now().strftime("%Y-%m-%d"))
                elif h == "Priority":
                    row_values.append(str(data.get("priority", "Medium")))
                elif h == "Fit Score":
                    try:
                        row_values.append(int(data.get("fitScore", 0)))
                    except (ValueError, TypeError):
                        row_values.append(0)
                elif h == "Follow-up Date":
                    row_values.append(str(data.get("followUpDate", "")))
                elif h == "Notes":
                    row_values.append(str(data.get("notes", "")))
                elif h == "Source":
                    row_values.append(str(data.get("source", "")))
                else:
                    # Leave unknown columns empty
                    row_values.append("")

            # Find the next empty row
            next_row = ws.max_row + 1
            # If max_row is 1 (only headers), next_row is 2
            # Check if row 2 is truly empty
            if next_row == 2:
                row2_empty = all(
                    ws.cell(row=2, column=c).value is None
                    for c in range(1, len(headers) + 1)
                )
                if not row2_empty:
                    # Find actual next empty row
                    for r in range(2, ws.max_row + 2):
                        is_empty = all(
                            ws.cell(row=r, column=c).value is None
                            for c in range(1, len(headers) + 1)
                        )
                        if is_empty:
                            next_row = r
                            break

            # Write the row
            for col_idx, value in enumerate(row_values, start=1):
                ws.cell(row=next_row, column=col_idx, value=value)

            # Atomic save
            save_result = self._atomic_save(wb)
            if not save_result["success"]:
                # Rollback from backup
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Write failed, rolled back from backup: {save_result['error']}",
                }

        except Exception as e:
            wb.close()
            # Rollback from backup
            self.backup.restore_from_backup(backup_path)
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Write failed, rolled back from backup: {e}",
            }
        finally:
            try:
                wb.close()
            except Exception:
                pass

        # Post-write validation: verify the row was added
        try:
            verify_wb = openpyxl.load_workbook(self.workbook_path, read_only=True, data_only=True)
            verify_ws = verify_wb["Applications"]
            found = False
            for row in verify_ws.iter_rows(min_row=2, values_only=True):
                if row and str(row[0]).strip() == app_id:
                    found = True
                    break
            verify_wb.close()
            if not found:
                # Rollback
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": "Post-write validation failed — application not found after save, rolled back",
                }
        except Exception as e:
            return {
                "success": True,
                "data": {"applicationId": app_id},
                "backupPath": backup_path,
                "error": f"Write succeeded but post-write validation error: {e}",
            }

        return {
            "success": True,
            "data": {"applicationId": app_id},
            "backupPath": backup_path,
            "error": None,
        }

    def update_application_status(self, application_id: str, status: str) -> dict:
        """Update the Status column for a specific application.

        Args:
            application_id: The Application ID value to find.
            status: New status value (will be normalized).

        Returns:
            { success, data, backupPath, error }
        """
        # Safety gate
        gate_error = self._check_write_safety()
        if gate_error:
            return gate_error

        # Session safety backup (production only, first write of session)
        session_error = self._ensure_session_backup()
        if session_error:
            return session_error

        if not application_id or not status:
            return {
                "success": False,
                "error": "application_id and status are required",
            }

        # Normalize status
        normalized_status = _normalize_status(status)

        # Create backup before write
        backup_result = self.backup.create_backup()
        if not backup_result["success"]:
            return {
                "success": False,
                "error": f"Backup failed — write aborted: {backup_result['error']}",
            }
        backup_path = backup_result["backupPath"]

        # Open workbook for writing
        try:
            wb = openpyxl.load_workbook(self.workbook_path)
        except Exception as e:
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Failed to open workbook: {e}",
            }

        try:
            ws = wb["Applications"]

            # Find header indices
            headers = []
            for cell in ws[1]:
                headers.append(str(cell.value).strip() if cell.value is not None else "")

            try:
                id_col = headers.index("Application ID") + 1
                status_col = headers.index("Status") + 1
            except ValueError:
                wb.close()
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": "Required columns (Application ID, Status) not found",
                }

            # Find the row with matching Application ID
            found_row = None
            old_status = None
            for row_idx in range(2, ws.max_row + 1):
                cell_val = ws.cell(row=row_idx, column=id_col).value
                if cell_val is not None and str(cell_val).strip() == str(application_id).strip():
                    found_row = row_idx
                    old_status = ws.cell(row=row_idx, column=status_col).value
                    break

            if found_row is None:
                wb.close()
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Application ID not found: {application_id}",
                }

            # Update the status cell
            ws.cell(row=found_row, column=status_col, value=normalized_status)

            # Atomic save
            save_result = self._atomic_save(wb)
            if not save_result["success"]:
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Write failed, rolled back from backup: {save_result['error']}",
                }

        except Exception as e:
            try:
                wb.close()
            except Exception:
                pass
            self.backup.restore_from_backup(backup_path)
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Write failed, rolled back from backup: {e}",
            }
        finally:
            try:
                wb.close()
            except Exception:
                pass

        # Post-write validation
        try:
            verify_wb = openpyxl.load_workbook(self.workbook_path, read_only=True, data_only=True)
            verify_ws = verify_wb["Applications"]
            verified = False
            for row in verify_ws.iter_rows(min_row=2, values_only=True):
                if row and str(row[0]).strip() == str(application_id).strip():
                    if str(row[status_col - 1]).strip() == normalized_status:
                        verified = True
                    break
            verify_wb.close()
            if not verified:
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": "Post-write validation failed — status not updated, rolled back",
                }
        except Exception as e:
            return {
                "success": True,
                "data": {
                    "applicationId": application_id,
                    "oldStatus": str(old_status) if old_status else "",
                    "newStatus": normalized_status,
                },
                "backupPath": backup_path,
                "error": f"Write succeeded but post-write validation error: {e}",
            }

        return {
            "success": True,
            "data": {
                "applicationId": application_id,
                "oldStatus": str(old_status) if old_status else "",
                "newStatus": normalized_status,
            },
            "backupPath": backup_path,
            "error": None,
        }

    # ── Editable field → column header mapping ──────────────────────────────
    EDITABLE_FIELDS = {
        "company": "Company",
        "role": "Role",
        "location": "Location",
        "source": "Source",
        "salary": "Salary",
        "fitScore": "Fit Score",
        "notes": "Notes",
    }

    def edit_application(self, application_id: str, data: dict) -> dict:
        """Edit specified fields for an existing application identified by stable ID.

        Only these fields can be edited: company, role, location, source, salary, fitScore, notes.
        All other columns, formulas, formatting, and sheets are preserved.

        Args:
            application_id: The stable Application ID to find and update.
            data: dict with fields to update (only editable fields are processed).

        Returns:
            { success, data, backupPath, error }
        """
        # Safety gate
        gate_error = self._check_write_safety()
        if gate_error:
            return gate_error

        # Session safety backup (production only, first write of session)
        session_error = self._ensure_session_backup()
        if session_error:
            return session_error

        # Validate application_id
        if not application_id or not str(application_id).strip():
            return {
                "success": False,
                "error": "Application ID is required to edit an application.",
            }

        # Filter data to only editable fields
        updates = {}
        for key, col_name in self.EDITABLE_FIELDS.items():
            if key in data and data[key] is not None:
                updates[col_name] = data[key]

        if not updates:
            return {
                "success": False,
                "error": "No editable fields provided. Editable: company, role, location, source, salary, fitScore, notes.",
            }

        # Create backup before write
        backup_result = self.backup.create_backup()
        if not backup_result["success"]:
            return {
                "success": False,
                "error": f"Backup failed — write aborted: {backup_result['error']}",
            }
        backup_path = backup_result["backupPath"]

        # Open workbook for writing
        try:
            wb = openpyxl.load_workbook(self.workbook_path)
        except Exception as e:
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Failed to open workbook: {e}",
            }

        old_values = {}
        try:
            ws = wb["Applications"]

            # Read headers from row 1
            headers = []
            for cell in ws[1]:
                headers.append(str(cell.value).strip() if cell.value is not None else "")

            try:
                id_col = headers.index("Application ID") + 1
            except ValueError:
                wb.close()
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": "Application ID column not found in workbook.",
                }

            # Find ALL matching rows — reject if 0 or >1 (duplicate IDs)
            matching_rows = []
            for row_idx in range(2, ws.max_row + 1):
                cell_val = ws.cell(row=row_idx, column=id_col).value
                if cell_val is not None and str(cell_val).strip() == str(application_id).strip():
                    matching_rows.append(row_idx)

            if len(matching_rows) == 0:
                wb.close()
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Application ID not found: {application_id}",
                }

            if len(matching_rows) > 1:
                wb.close()
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Duplicate Application ID found: {application_id} — operation aborted for safety.",
                }

            found_row = matching_rows[0]

            # Update only the specified editable fields
            for col_name, value in updates.items():
                try:
                    col_idx = headers.index(col_name) + 1
                except ValueError:
                    continue  # Column doesn't exist in this workbook, skip

                # Special handling for Fit Score (int)
                if col_name == "Fit Score":
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        value = 0

                old_val = ws.cell(row=found_row, column=col_idx).value
                old_values[col_name] = str(old_val) if old_val is not None else ""
                ws.cell(row=found_row, column=col_idx, value=value)

            # Atomic save
            save_result = self._atomic_save(wb)
            if not save_result["success"]:
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": f"Write failed, rolled back from backup: {save_result['error']}",
                }

        except Exception as e:
            try:
                wb.close()
            except Exception:
                pass
            self.backup.restore_from_backup(backup_path)
            return {
                "success": False,
                "backupPath": backup_path,
                "error": f"Write failed, rolled back from backup: {e}",
            }
        finally:
            try:
                wb.close()
            except Exception:
                pass

        # Post-write validation: verify at least one edited field
        try:
            verify_wb = openpyxl.load_workbook(self.workbook_path, read_only=True, data_only=True)
            verify_ws = verify_wb["Applications"]
            verified = False
            for row in verify_ws.iter_rows(min_row=2, values_only=True):
                if row and str(row[id_col - 1]).strip() == str(application_id).strip():
                    for col_name, expected_value in updates.items():
                        try:
                            col_idx = headers.index(col_name) + 1
                            actual = str(row[col_idx - 1]).strip() if row[col_idx - 1] is not None else ""
                            expected = str(expected_value).strip()
                            if col_name == "Fit Score":
                                try:
                                    expected = str(int(expected_value))
                                except (ValueError, TypeError):
                                    expected = "0"
                            if actual == expected:
                                verified = True
                                break
                        except (ValueError, IndexError):
                            continue
                    break
            verify_wb.close()
            if not verified:
                self.backup.restore_from_backup(backup_path)
                return {
                    "success": False,
                    "backupPath": backup_path,
                    "error": "Post-write validation failed — edited values not confirmed, rolled back.",
                }
        except Exception as e:
            return {
                "success": True,
                "data": {"applicationId": application_id, "updatedFields": list(updates.keys())},
                "backupPath": backup_path,
                "error": f"Write succeeded but post-write validation error: {e}",
            }

        return {
            "success": True,
            "data": {"applicationId": application_id, "updatedFields": list(updates.keys())},
            "backupPath": backup_path,
            "error": None,
        }
