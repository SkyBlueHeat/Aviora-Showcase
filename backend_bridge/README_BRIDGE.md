# Backend Bridge — Excel Data Bridge with Read/Write Support

Core MVP implementation. Provides a safe data bridge from
the Excel workbook to the React UI with read-only access and safety-gated write operations
(add, update status, edit application) using an adapter-based architecture.

---

## Architecture

```
React Components
    ↓
dataService.ts (auto-selects adapter)
    ↓
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│DesktopAdapter│  │  WebAdapter  │  │ MockAdapter  │
│ (pywebview)  │  │  (future)    │  │ (mockData.ts)│
└──────┬───────┘  └──────────────┘  └──────────────┘
       ↓
┌──────────────┐
│ ExcelBridgeAPI│
│  (api.py)     │
└──────┬───────┘
       ↓
┌──────────────┐     ┌──────────────┐
│ ExcelReader   │────→│ DataMapper   │
│(read_only=True)│    │(row→typed dict)│
└──────────────┘     └──────────────┘
       ↓
Developer_Job_Application_Tracker_PRO.xlsx
```

## Files

### Python Backend

| File | Purpose |
|---|---|
| `__init__.py` | Package init |
| `excel_reader.py` | Read-only openpyxl wrapper (never writes) |
| `data_mapper.py` | Transforms Excel rows → typed dicts, computes KPIs/charts |
| `api.py` | PyWebView API class — read methods + Core MVP write methods (add, update status, edit) + workbook validation/status |
| `excel_writer.py` | Safety-gated write helper — add_application, update_application_status, edit_application |
| `excel_backup.py` | Timestamped backup helper (copies only, never modifies source) |
| `EXCEL_MAPPING.md` | Full Excel → React field mapping document |
| `WRITE_SAFETY.md` | Write safety architecture: backup rules, atomic save, rollback |
| `tests/create_fixture.py` | Generates test fixture workbook with sample data |
| `tests/test_bridge.py` | 148 tests: read-only safety, mapping, API, JSON-safe |
| `tests/test_backup.py` | 40 tests: backup creation, restore, source integrity |
| `tests/test_writer.py` | 114 tests: write safety gate, add/update/edit, backup-before-write, rollback, staging, production |
| `tests/test_fixture_workbook.xlsx` | Test fixture (NOT the real workbook) |

### React Adapters

| File | Purpose |
|---|---|
| `webui/src/lib/dataService.ts` | Interface + adapter factory + exported `dataService` |
| `webui/src/lib/adapters/MockAdapter.ts` | Wraps existing `mockData.ts` |
| `webui/src/lib/adapters/DesktopAdapter.ts` | Calls `window.pywebview.api`, falls back to mock |

### UI Changes

| File | Change |
|---|---|
| `webui/src/App.tsx` | Added data source indicator badge in header |

---

## Read-Only Safety Guarantees

1. `excel_reader.py` opens with `read_only=True` — openpyxl prevents writes
2. No `wb.save()` call exists anywhere in `backend_bridge/`
3. `data_mapper.py` only transforms data — no file operations
4. `api.py` only reads — no write/save/update/delete methods exposed
5. Workbook is closed after each read operation
6. Tests verify no write methods exist on any class

---

## API Methods

| Method | Returns | Description |
|---|---|---|
| `health()` | `{ status, workbook_exists, sheets, error }` | Health check |
| `get_applications()` | `{ data: Application[], error, count }` | All applications |
| `get_dashboard()` | `{ data: { kpis, monthlyChart, sourceChart, pipeline } }` | Dashboard summary |
| `get_kpis()` | `{ data: KPICard[], error }` | Computed KPIs |
| `get_pipeline()` | `{ data: PipelineCount[], error }` | Pipeline column counts |
| `get_salary_data()` | `{ data: SalaryEntry[], error, count }` | Salary comparison |
| `get_interview_history()` | `{ data: InterviewHistory[], error, count }` | Interview log |
| `get_cover_letter_history()` | `{ data: CoverLetterHistory[], error, count }` | Cover letter log |
| `add_application(data)` | `{ success, data, backupPath, error }` | Add new application (safety-gated) |
| `update_application_status(id, status)` | `{ success, data, backupPath, error }` | Update application status (safety-gated) |
| `edit_application(id, data)` | `{ success, data, backupPath, error }` | Edit application fields (safety-gated) |
| `get_write_mode()` | `{ enabled, mode, reason, workbookPath, workbookName }` | Check write mode status (read-only) |
| `validate_workbook(path)` | `{ valid, workbookName, sheets, missingHeaders, error }` | Validate workbook compatibility (read-only) |
| `get_workbook_status()` | `{ workbookName, mode, available, schemaValid, writeEnabled, writeMode, lastBackupFilename, error }` | Full workbook status (read-only) |
| `select_workbook()` | `{ selected, workbookName, reason, validation }` | Open native file dialog, validate, reinitialize reader/writer (does NOT enable writes) |

---

## Running Tests

```bash
# All checks (Python tests + React build)
python scripts/run_all_checks.py

# Backend bridge tests
python -m backend_bridge.tests.test_bridge

# Writer tests (safety gate, add/update/edit, backup, rollback)
python backend_bridge/tests/test_writer.py

# Backup tests
python backend_bridge/tests/test_backup.py

# Regenerate fixture (only if schema changes)
python backend_bridge/tests/create_fixture.py
```

---

## Adapter Selection Logic

```
window.pywebview.api exists?
  ├─ YES → DesktopAdapter
  │         ├─ API call succeeds → source: "excel-readonly"
  │         └─ API call fails    → source: "fallback" (MockAdapter)
  └─ NO  → MockAdapter
            └─ source: "mock"
```

The data source indicator in the UI header shows which adapter is active:
- **Mock** (gray) — Running without desktop shell
- **Excel Read-Only** (green) — Desktop shell with working Excel bridge
- **Fallback** (amber) — Desktop shell detected but Excel read failed

---

## Current Limitations

1. **Applications sheet is empty** — Real workbook has 0 data rows. DesktopAdapter returns empty data; UI shows empty state. Demo workbook (`_DEMO.xlsx`) has 6 sample rows for validation.
2. **Pages integrated** — Dashboard and Application Kit now consume `dataService`. Other pages still use mock data.
3. **Formula fields recomputed** — Total Comp, Net Salary, etc. are computed in Python since Excel formulas aren't cached in `data_only` mode.
4. **Demo + staging + production writes** — Phase 2B.3B enables production writes with explicit opt-in (`JOBTRACKER_ENABLE_PRODUCTION_WRITES=1`). Demo and staging modes remain available. Production writes are disabled by default.
5. **Interview questions, JD analysis, LinkedIn messages** — Always mock (not stored in Excel).
6. **Streak data** — Always mock (stored in `streak_data.json`, not Excel).
7. **New Application / Export Report buttons** — New Application is enabled in demo/staging/production write mode. Export Report remains disabled.

---

## Core MVP — Write Integration (current)

Write methods added to `ExcelBridgeAPI` — safety-gated for demo/staging/production workbooks.

Implemented methods:

| Method | Description |
|---|---|
| `add_application(data)` | Add a new row to Applications sheet |
| `update_application_status(id, status)` | Update status of an application |
| `edit_application(id, data)` | Edit specified fields of an application by stable ID |
| `validate_workbook(path)` | Validate a workbook file for compatibility (read-only) |
| `get_workbook_status()` | Return current workbook status for UI display (read-only) |
| `select_workbook()` | Open native file dialog (.xlsx only), validate, reinitialize reader/writer — does NOT enable writes |

### Dashboard Refresh After Writes

- `dataService.invalidate()` triggers all subscribed components to reload data
- `ApplicationKit` and `Dashboard` both subscribe via `onDataInvalidate()`
- No full page reload required after write operations

### User-Friendly Error Handling

- `DesktopAdapter.sanitizeError()` strips file paths, env var names, and tracebacks
- Error messages truncated to 200 characters
- No sensitive information exposed to users

### Empty-Workbook Experience

- Context-aware empty state in ApplicationKit when no applications found
- Different messages for: no workbook, schema invalid, empty workbook
- "Add Your First Application" CTA when write mode is enabled

### Production write testing plan

```powershell
# 1. Build React
cd webui
npm run build

# 2. Launch with production workbook (explicit opt-in)
cd ..
$env:JOBTRACKER_WORKBOOK_PATH = "$PWD\Developer_Job_Application_Tracker_PRO.xlsx"
$env:JOBTRACKER_ENABLE_PRODUCTION_WRITES = "1"
python desktop_shell/app_shell.py

# 3. Test write actions (Phase 2B.3B)
#    - Add application → verify row appears in Applications sheet
#    - Update status → verify status changes in kanban
#    - Check backups/ folder for unique timestamped backup files
#    - Close app, verify production workbook has new data
#    - Relaunch to confirm data persists
#    - Test restore from latest backup if needed

# 4. Return to read-only mode
Remove-Item Env:\JOBTRACKER_WORKBOOK_PATH
Remove-Item Env:\JOBTRACKER_ENABLE_PRODUCTION_WRITES
python desktop_shell/app_shell.py
```
