# Write Safety Architecture — JobTracker PRO

This document defines the safety rules and architecture for all future Excel write
operations in the JobTracker PRO desktop app.

**Current phase: Core MVP — Application editing, dashboard refresh, workbook status, error handling (2026-07-03)**

---

## Golden Rules

1. **Never write without a backup.** Every write operation must create a timestamped
   backup copy of the workbook before modifying it.
2. **Never write to the real workbook in demo mode.** When `JOBTRACKER_WORKBOOK_PATH`
   is set, writes target only the demo workbook.
3. **Never write while Excel has the file open.** File locks will corrupt the workbook.
4. **Always validate after write.** Re-read the workbook to confirm the change was
   applied correctly.
5. **Always rollback on failure.** If a write fails partway, restore from the
   pre-write backup.
6. **Never expose write methods to the UI until fully tested.** Stub methods return
   `{ success: false, error: "Write actions not enabled yet" }` until the current phase.

---

## Backup-Before-Write Rule

Before any write operation, the system must:

1. Call `ExcelBackup.create_backup()` to copy the current workbook
2. Verify the backup was created successfully (`success: true`)
3. If backup fails, **abort the write** and return the backup error
4. Proceed with the write only after a confirmed backup exists

```
User action (add/update/delete)
    ↓
ExcelBackup.create_backup()
    ↓
backup.success == true?
  ├─ NO  → abort, return error
  └─ YES → proceed with write
              ↓
           write succeeds?
              ├─ YES → validate, return success
              └─ NO  → restore from backup, return error
```

---

## Backup System

### Module: `backend_bridge/excel_backup.py`

| Method | Returns | Description |
|---|---|---|
| `create_backup()` | `{ success, backupPath, error }` | Timestamped copy of workbook |
| `list_backups()` | `{ success, backups[], count, error }` | List existing backups |
| `restore_from_backup(path)` | `{ success, preRestoreBackupPath, error }` | Restore from a backup |

### Backup file naming

```
Developer_Job_Application_Tracker_PRO_backup_YYYYMMDD_HHMMSS.xlsx
```

### Backup directory

Default: `backups/` relative to the workbook's parent directory.

Can be overridden by passing a custom `backup_dir` to `ExcelBackup.__init__()`.

### Backup verification

After copy, the system verifies:
- Backup file exists at the expected path
- Backup file size is non-zero
- Source workbook is not modified (copy is read-only operation)

---

## Real Workbook vs Demo Workbook vs Staging Workbook

| Workbook | Path | Write Status |
|---|---|---|
| **Real** | `Developer_Job_Application_Tracker_PRO.xlsx` | Write-enabled with explicit opt-in (Phase 2B.3B) |
| **Demo** | `Developer_Job_Application_Tracker_PRO_DEMO.xlsx` | Write target for demo/testing |
| **Staging** | `Developer_Job_Application_Tracker_PRO_STAGING.xlsx` | Write target for production-style validation (Phase 2B.3A) |

### How to switch between them

```powershell
# Real workbook (default — no env var needed, read-only)
python desktop_shell/app_shell.py

# Demo workbook (write-enabled)
$env:JOBTRACKER_WORKBOOK_PATH = "$PWD\Developer_Job_Application_Tracker_PRO_DEMO.xlsx"
python desktop_shell/app_shell.py

# Staging workbook (write-enabled — requires explicit enable)
$env:JOBTRACKER_WORKBOOK_PATH = "$PWD\Developer_Job_Application_Tracker_PRO_STAGING.xlsx"
$env:JOBTRACKER_ENABLE_STAGING_WRITES = "1"
python desktop_shell/app_shell.py

# Production workbook (write-enabled — requires explicit opt-in)
$env:JOBTRACKER_WORKBOOK_PATH = "$PWD\Developer_Job_Application_Tracker_PRO.xlsx"
$env:JOBTRACKER_ENABLE_PRODUCTION_WRITES = "1"
python desktop_shell/app_shell.py
```

The desktop shell reads `JOBTRACKER_WORKBOOK_PATH` and passes it to `ExcelBridgeAPI`.
Write operations use the same path. Staging writes require both env vars. Production writes require explicit opt-in.

### Write mode safety gate

| Mode | Filename contains | Env vars required | UI indicator |
|---|---|---|---|
| **Demo** | `_DEMO` or `_TEST` | `JOBTRACKER_WORKBOOK_PATH` | Green "Demo write mode" |
| **Staging** | `_STAGING` | `JOBTRACKER_WORKBOOK_PATH` + `JOBTRACKER_ENABLE_STAGING_WRITES=1` | Amber "Staging write mode" |
| **Production** | (real workbook) | `JOBTRACKER_WORKBOOK_PATH` + `JOBTRACKER_ENABLE_PRODUCTION_WRITES=1` | Red "Production write mode" |
| **Disabled** | (any) | (missing env vars) | Read-only (no writes) |

---

## Recovery from Backup

### Automatic recovery

If a write operation fails, the system automatically restores from the pre-write backup:

1. Write attempt fails (exception, validation error, etc.)
2. System calls `ExcelBackup.restore_from_backup(backup_path)`
3. Workbook is restored to its pre-write state
4. Error is returned to the UI

### Manual recovery

Users can manually restore from a backup:

1. Close the desktop app and Excel (if open)
2. Locate the backup in `backups/` folder
3. Copy the backup file over the workbook:
   ```powershell
   Copy-Item "backups\Developer_Job_Application_Tracker_PRO_backup_20260701_230000.xlsx" `
             "Developer_Job_Application_Tracker_PRO.xlsx" -Force
   ```
4. Relaunch the app

---

## File Lock Risks

### Problem

If the user has the workbook open in Microsoft Excel while the app tries to write:
- Windows file locking prevents `openpyxl` from saving
- `PermissionError` is raised
- The save may silently corrupt data if forced

### Mitigation

1. **Check for file lock before write:** Attempt to open the file in append mode. If
   it fails, return a user-friendly error: "Please close the workbook in Excel before
   saving."
2. **Never force a write:** If the file is locked, abort gracefully.
3. **Retry mechanism:** Offer the user a retry after they close Excel.

### Future: File lock detection

```python
def _is_workbook_locked(path: str) -> bool:
    try:
        with open(path, 'a'):
            pass
        return False
    except PermissionError:
        return True
```

---

## Atomic Save Strategy

### Problem

Direct `wb.save()` can fail partway, leaving a corrupted workbook.

### Strategy

1. Create a backup of the current workbook
2. Write to a **temporary file** (e.g., `workbook_tmp.xlsx`)
3. Verify the temp file is valid (re-read it)
4. **Atomically replace** the original with the temp file:
   - `os.replace(tmp_path, workbook_path)` — atomic on Windows
5. If any step fails, the original workbook is untouched

```
backup → write to temp → validate temp → atomic replace → done
                              ↓ fail
                    abort, original untouched
```

### Implementation plan (current phase)

```python
def safe_save(workbook_path, wb):
    # 1. Backup
    backup = ExcelBackup(workbook_path).create_backup()
    if not backup["success"]:
        return backup

    # 2. Write to temp
    tmp_path = workbook_path + ".tmp"
    wb.save(tmp_path)

    # 3. Validate temp
    try:
        test = openpyxl.load_workbook(tmp_path, read_only=True)
        test.close()
    except:
        os.remove(tmp_path)
        return {"success": False, "error": "Temp file validation failed"}

    # 4. Atomic replace
    os.replace(tmp_path, workbook_path)

    return {"success": True, "backupPath": backup["backupPath"]}
```

---

## Validation After Write

After every write operation, the system must:

1. Re-open the workbook in read-only mode
2. Verify the expected change is present (row count, field value, etc.)
3. If validation fails, restore from backup and return error
4. If validation passes, return success with backup path

---

## Rollback Strategy

If a write fails at any point:

| Failure Point | State | Action |
|---|---|---|
| Backup creation fails | Original untouched | Abort, return backup error |
| Temp write fails | Original untouched | Abort, remove temp, return error |
| Temp validation fails | Original untouched | Abort, remove temp, return error |
| Atomic replace fails | Original may be corrupted | Restore from backup, return error |
| Post-write validation fails | Original modified | Restore from backup, return error |

---

## Write API Methods

### Core MVP — Implemented

| Method | Description | Status |
|---|---|---|
| `add_application(data)` | Add a new row to Applications sheet | ✅ Implemented |
| `update_application_status(id, status)` | Update status of an application | ✅ Implemented |
| `edit_application(id, data)` | Edit specified fields of an application by stable ID | ✅ Implemented |
| `validate_workbook(path)` | Validate a workbook file for compatibility (read-only) | ✅ Implemented |
| `get_workbook_status()` | Return current workbook status for UI display (read-only) | ✅ Implemented |
| `select_workbook()` | Open native file dialog, validate, reinitialize reader/writer (does NOT enable writes) | ✅ Implemented |

### Editable Fields (edit_application only)

| Field Key | Excel Column | Type |
|---|---|---|
| `company` | Company | string |
| `role` | Role | string |
| `location` | Location | string |
| `source` | Source | string |
| `salary` | Salary | string |
| `fitScore` | Fit Score | int (0-100) |
| `notes` | Notes | string |

All other columns, formulas, formatting, and sheets are preserved during edits.

### Not Implemented (out of scope for Core MVP)

| Method | Description | Phase |
|---|---|---|
| `archive_application(id)` | Move application to archived | Future |
| `delete_application(id)` | Remove application row | Future |

### Core MVP Safety Gate

Before any write, `ExcelWriter._check_write_safety()` verifies ALL of these:

1. `JOBTRACKER_WORKBOOK_PATH` env var is explicitly set
2. Workbook filename contains `_DEMO`, `_TEST`, `_STAGING`, or is the production workbook
3. If `_STAGING`: `JOBTRACKER_ENABLE_STAGING_WRITES=1` must be explicitly set
4. If production workbook: `JOBTRACKER_ENABLE_PRODUCTION_WRITES=1` must be explicitly set
5. Workbook file exists
6. Applications sheet exists with required headers

For `edit_application`, additional safety checks:
7. Application ID must be non-empty
8. At least one editable field must be provided
9. Exactly one matching row must be found (rejects duplicates and missing IDs)

### Core MVP Write Flow

```
1. Safety gate (6+ checks)
   ↓ fail → return error
2. Session backup (production only, first write of session)
   ↓ fail → abort, return error
3. ExcelBackup.create_backup()
   ↓ fail → abort, return error
4. Open workbook (openpyxl, read-write mode)
5. Perform write (append row / update cell / edit fields)
   - edit_application: find row by Application ID, reject if 0 or >1 matches
6. Atomic save (temp file → validate → os.replace)
   ↓ fail → rollback from backup, return error
7. Post-write validation (re-read, verify change)
   ↓ fail → rollback from backup, return error
8. Return success with backupPath
9. Frontend calls dataService.invalidate() → all components refresh
```

### Core MVP — UI Write Integration (current)

New additions in Core MVP (on top of 2B.2/2B.3):

| Addition | Description |
|---|---|
| `get_write_mode()` | Read-only check method on `ExcelBridgeAPI` — returns `{ enabled, reason, workbookPath, workbookName }` |
| `get_workbook_status()` | Read-only method returning full workbook status (name, mode, availability, schema, write status, last backup) |
| `validate_workbook(path)` | Read-only method validating a workbook file for compatibility |
| `select_workbook()` | Opens native Windows file dialog (.xlsx only), validates, reinitializes reader/writer — does NOT enable writes |
| `editApplication()` in DataService | All adapters implement — dispatches to `edit_application` on the backend |
| `invalidate()` / `onDataInvalidate()` | Shared invalidation mechanism — `AutoAdapter` emits only on successful writes; UI handlers do not emit duplicate invalidation |
| Edit button (pencil icon) | On Kanban cards and list view rows — opens `EditApplicationModal` with pre-filled form |
| `EditApplicationModal` | Modal form for editing application fields (company, role, location, source, salary, fitScore, notes) |
| Workbook status bar | Shows workbook name, mode badge, availability, schema validity, write status, last backup |
| Empty state | Context-aware messaging when no applications found (no workbook, schema invalid, empty workbook) |
| `sanitizeError()` | Strips file paths, env var names, and tracebacks from error messages before showing to users |
| Feedback toasts | 4-second auto-dismissing success/error toasts after all write actions |
| Dashboard refresh | Dashboard subscribes to invalidation events and reloads data without full page reload |

### How to Launch Demo Write Mode

```powershell
# 1. Build React
cd webui
npm run build

# 2. Launch with demo workbook
cd ..
$env:JOBTRACKER_WORKBOOK_PATH = "$PWD\Developer_Job_Application_Tracker_PRO_DEMO.xlsx"
python desktop_shell/app_shell.py
```


# 3. Write actions are now enabled for the demo workbook
#    - add_application via API or UI (when enabled)
#    - update_application_status via API or UI (when enabled)

# 4. Check backups/ folder for timestamped backup files

# 5. Return to real workbook (writes blocked)
Remove-Item Env:\JOBTRACKER_WORKBOOK_PATH
python desktop_shell/app_shell.py
```

### How to Verify Backups Are Created

1. Before a write, check `backups/` folder is empty or note file count
2. Perform a write action (add application or update status)
3. Check `backups/` folder — a new `*_backup_YYYYMMDD_HHMMSS.xlsx` file should exist
4. The backup file should have the same size as the workbook before the write

### How to Confirm Real Workbook Is Protected

1. Launch without `JOBTRACKER_WORKBOOK_PATH` → all writes blocked
2. Set `JOBTRACKER_WORKBOOK_PATH` to the real workbook → writes still blocked (filename check)
3. Set `JOBTRACKER_WORKBOOK_PATH` to a file without `_DEMO` or `_TEST` → writes blocked
4. Only demo/test workbooks pass the safety gate

### How to Rollback from Backup

See the "Recovery from Backup" section above. Either:
- **Automatic:** Write failure triggers `ExcelBackup.restore_from_backup()`
- **Manual:** Copy backup file over workbook:
  ```powershell
  Copy-Item "backups\Tracker_DEMO_backup_20260702_010000.xlsx" `
            "Developer_Job_Application_Tracker_PRO_DEMO.xlsx" -Force
  ```
