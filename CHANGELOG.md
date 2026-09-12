# Changelog — Developer Job Application Tracker PRO v2.0

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [Core MVP] — 2026-07-03 — Fast-Track Core MVP Sprint

### Application Editing
- Added `edit_application(application_id, data)` method to `ExcelWriter` — updates specific fields of an existing application by stable Application ID
- Editable fields: company, role, location, source, salary, fitScore, notes (defined in `EDITABLE_FIELDS` mapping)
- Safety guarantees: backup before write, atomic save, post-write validation, rollback on failure
- Duplicate Application ID detection — rejects if 0 or >1 matching rows found
- Added `edit_application` endpoint to `ExcelBridgeAPI` for frontend access
- Added `editApplication` method to `DataService` interface, `AutoAdapter`, `DesktopAdapter`, and `MockAdapter`
- Added `EditApplicationModal` component in `ApplicationKit.tsx` with pre-filled form and validation
- Edit button (pencil icon) on Kanban cards and list view rows (visible only in write mode)
- Production confirmation dialog support for edit operations

### Dashboard Refresh After Writes
- Added shared data invalidation mechanism to `AutoAdapter`: `invalidate()` and `onDataInvalidate(cb)`
- **Single-emit ownership**: `AutoAdapter` emits invalidation only after a fully successful and validated write — UI handlers do not emit a second invalidation
- No invalidation on cancelled or failed writes
- React effects return unsubscribe cleanup functions (no duplicate subscriptions, no constant polling)
- `ApplicationKit` subscribes to invalidation events and reloads applications + workbook status
- `Dashboard` subscribes to invalidation events via `refreshKey` counter, triggering full data reload
- No full page reload required — all components stay in sync after writes

### Workbook Selection and Status UI
- Added `select_workbook()` method to `ExcelBridgeAPI` — opens native Windows file dialog (.xlsx only), validates selected workbook (Applications sheet + required headers), reinitializes reader/writer
- Selecting a workbook does NOT enable writes — existing safety gates still apply based on filename and env vars
- Clears cached session backup state and production confirmation on workbook switch
- Added `validate_workbook(file_path)` method to `ExcelBridgeAPI` — validates .xlsx files for compatibility (Applications sheet, required headers)
- Added `get_workbook_status()` method to `ExcelBridgeAPI` — returns workbook name, mode, availability, schema validity, write status, and last backup filename
- Added `WorkbookStatusResult` TypeScript interface to `dataService.ts`
- Added workbook status bar in `ApplicationKit.tsx` showing: workbook name, mode badge (Mock/Read-only/Demo/Staging/Production), availability, schema validity, write status, last backup
- Added "Select Workbook" button in status bar — opens native file dialog, validates, and refreshes all components
- Status bar updates on mount, on data source change, and after write operations

### First-Run and Empty-Workbook Experience
- Added empty state in `ApplicationKit.tsx` when no applications found
- Context-aware messaging: no workbook found, schema invalid, or empty workbook
- "Add Your First Application" CTA button shown when write mode is enabled
- No confusing empty Kanban columns — single clear call-to-action

### User-Friendly Error Handling
- Added `sanitizeError()` method to `DesktopAdapter` — strips file paths, environment variable names, and tracebacks from error messages
- Error messages truncated to 200 characters max
- No raw stack traces, full file paths, or sensitive env var names exposed to users
- Applied to all write methods: `addApplication`, `updateApplicationStatus`, `editApplication`

### Unified Verification Script
- Created `scripts/run_all_checks.py` — runs all required regression tests and React build with pass/fail summary
- 7 required checks: Backup tests, Bridge tests, Writer tests, Python compile (launcher.py), Settings tests, UI smoke tests, React production build
- Continue-on-failure: all checks run regardless of earlier results
- Clean environment for subprocess tests (strips `JOBTRACKER_` env vars, sets UTF-8 encoding)
- Exit code 0 only when ALL checks pass
- Created `scripts/manual_validation.py` — staging validation, disposable production-copy validation, real production read-only SHA256 verification

### Files Created
- `scripts/run_all_checks.py` — unified verification script (7 required checks)
- `scripts/manual_validation.py` — manual validation script (staging + production-copy + read-only SHA256)
- `scripts/create_source_zip.py` — source ZIP packaging script

### Files Changed
- `backend_bridge/excel_writer.py` — added `edit_application` method + `EDITABLE_FIELDS` mapping
- `backend_bridge/api.py` — added `edit_application`, `validate_workbook`, `get_workbook_status`, `select_workbook` endpoints
- `webui/src/lib/dataService.ts` — added `editApplication`, `getWorkbookStatus`, `selectWorkbook`, `invalidate`, `onDataInvalidate` to interface + `AutoAdapter`; invalidation emitted on success only
- `webui/src/lib/adapters/DesktopAdapter.ts` — added `editApplication`, `getWorkbookStatus`, `selectWorkbook`, `sanitizeError`, `invalidate`, `onDataInvalidate`
- `webui/src/lib/adapters/MockAdapter.ts` — added `editApplication`, `getWorkbookStatus`, `selectWorkbook`, `invalidate`, `onDataInvalidate`
- `webui/src/pages/ApplicationKit.tsx` — added `EditApplicationModal`, edit buttons, workbook status bar with Select Workbook button, empty state, invalidation subscription
- `webui/src/pages/Dashboard.tsx` — added invalidation subscription with `refreshKey` counter
- `desktop_shell/app_shell.spec` — added hidden imports for `backend_bridge` and `openpyxl`
- `backend_bridge/tests/test_writer.py` — added 16 comprehensive edit safety tests (51 new assertions)

### Verification
- `python scripts/run_all_checks.py` — 7/7 checks PASS
- Writer tests: 166 passes (114 original + 52 edit safety)
- Backup tests: 54 passes
- Bridge tests: PASS
- Python compile: PASS
- Settings tests: 11 passes
- UI smoke tests: 206 passes
- React production build: 2337 modules, 0 TypeScript errors
- Manual validation: 46/46 passes (staging + production-copy + read-only SHA256)

---

## [Phase 1.7] — 2026-07-01 — Desktop Distribution Polish

### App Icon
- Created `desktop_shell/generate_icon.py` — generates a placeholder `.ico` file (indigo background, white "J")
- Generated `desktop_shell/icon.ico` (32×32, 4.2 KB)
- Updated `app_shell.spec` and `app_shell_onedir.spec` to embed the icon in the .exe

### Favicon Cleanup
- Added inline SVG favicon to `webui/index.html` (data URI, no external file needed)
- Eliminated the harmless `/favicon.ico` 404 from the HTTP server logs
- Fully offline-safe — no external requests

### Offline-Safe Fonts
- Removed Google Fonts CDN links (`fonts.googleapis.com`, `fonts.gstatic.com`) from `webui/index.html`
- Updated `webui/tailwind.config.ts` to use system fonts: `Segoe UI` (sans), `Consolas` (mono)
- UI now renders correctly without any internet connection

### Packaging Comparison
- Built and tested both `--onefile` (13.2 MB, 1 file) and `--onedir` (25.5 MB, 159 files)
- Documented comparison: size, startup speed, UX, antivirus risk, distribution suitability
- Recommendation: `--onefile` for Etsy/direct download, `--onedir` for future installer

### Documentation
- Rewrote `desktop_shell/README_RUN_EXE.txt` for non-technical users with troubleshooting section
- Updated `DESKTOP_POC.md` with Phase 1.7 changes, packaging comparison table, and updated limitations

### Files Created
- `desktop_shell/generate_icon.py` — icon generator script
- `desktop_shell/icon.ico` — placeholder app icon
- `desktop_shell/app_shell_onedir.spec` — PyInstaller onedir spec

### Files Changed
- `webui/index.html` — removed Google Fonts, added inline SVG favicon
- `webui/tailwind.config.ts` — system fonts instead of web fonts
- `desktop_shell/app_shell.spec` — added icon.ico reference
- `desktop_shell/README_RUN_EXE.txt` — rewritten for non-technical users
- `DESKTOP_POC.md` — updated with Phase 1.7 changes + packaging comparison

### Verification
- `python -m py_compile launcher.py` — passed
- `python tests/test_settings_save.py` — 11/11 passes
- `python tests/full_ui_smoke_test.py` — 205/205 passes
- `npm run build` — 2334 modules, 12.19s
- `JobTrackerPRO.exe` (onefile) — confirmed running with icon
- `JobTrackerPRO_Onedir/JobTrackerPRO.exe` (onedir) — confirmed running

---

## [Phase 1.6] — 2026-07-01 — Desktop Shell Proof of Concept

### Desktop Shell
- Created `desktop_shell/app_shell.py` — PyWebView wrapper that loads the React production build via a local HTTP server (127.0.0.1:8765)
- Window title: "JobTracker PRO", size: 1280×800, min: 1024×600
- No backend, no Excel, no settings access — pure UI shell with mock data
- Supports both development mode (from source) and packaged mode (PyInstaller _MEIPASS)

### PyInstaller Packaging
- Created `desktop_shell/app_shell.spec` — single-file exe spec bundling Python runtime, PyWebView, pythonnet, and webui/dist/
- Successfully packaged as `dist/JobTrackerPRO.exe` (13.2 MB)
- Console hidden, WebView2 renderer confirmed working

### Build Configuration
- Updated `webui/vite.config.ts` with `base: './'` for relative asset paths (required for local HTTP server)

### Documentation
- Created `DESKTOP_POC.md` — full documentation for building React, running the desktop shell, packaging the .exe, current limitations, and next steps
- Created `desktop_shell/README_RUN_EXE.txt` — end-user instructions for the packaged exe

### Files Created
- `desktop_shell/app_shell.py` — PyWebView wrapper + HTTP server
- `desktop_shell/app_shell.spec` — PyInstaller spec
- `desktop_shell/README_RUN_EXE.txt` — end-user readme for exe
- `DESKTOP_POC.md` — developer documentation

### Files Changed
- `webui/vite.config.ts` — added `base: './'`

### Verification
- `python -m py_compile launcher.py` — passed
- `python tests/test_settings_save.py` — 11/11 passes
- `python tests/full_ui_smoke_test.py` — 205/205 passes
- `npm run build` — 2334 modules, 13.89s
- `JobTrackerPRO.exe` — confirmed running (2 processes)

---

## [Phase 1.5] — 2026-07-01 — Visual Polish + Desktop App Readiness

### Visual Polish
- Enhanced `index.css` with premium card shadows, button hover glow, wider scrollbars (8px), scrollbar corner styling
- Improved nav active state with indigo accent background and left border
- Added hover shadow transition to `KPICard` component
- Removed duplicate `.btn-secondary` CSS rule
- Added `.kanban-scroll` class for polished horizontal scrollbar in Kanban board

### Application Kit Kanban Layout
- Narrower columns (260px fixed width) with `shrink-0` to prevent compression
- Per-column max-height with independent vertical scroll (`max-h-[calc(100vh-280px)]`)
- Polished horizontal scroll container with custom thin scrollbar
- Better card text truncation (`min-w-0`, `truncate` on company/role/salary)
- List view wrapped in `overflow-x-auto` with `min-w-[700px]` for small screens
- Toolbar uses `flex-wrap` for responsive button layout

### Mock Identity Cleanup
- Added `mockProfile` to `mockData.ts` with neutral demo identity "Jordan Avery"
- Replaced all hardcoded "Alex Chen" references across `App.tsx`, `Dashboard.tsx`, `CoverLetterStudio.tsx`, `LinkedInComposer.tsx`, and `mockData.ts` cover letter
- All LinkedIn mock message sign-offs updated from "Alex" to "Jordan"

### Mock Prototype Badge
- Added `SHOW_MOCK_BADGE = true` config flag in `mockData.ts`
- `App.tsx` conditionally renders the "Mock Prototype" badge based on this flag
- Set to `false` for final builds to hide the badge

### Interview Prep Improvements
- Redesigned to 3-column layout (3/6/3 grid) for better space utilization
- Added STAR checklist sidebar with letter badges and descriptions
- Added AI feedback placeholder with `ScoreCircle` and mock feedback items
- Added answer score calculation based on word count
- Added saved answer history with 2 mock entries and bookmark metadata
- Added practice stats card (questions practiced, avg score, avg time, best category)
- Reduced empty state height from 400px to 300px

### Responsive Polish
- Header padding adapts: `px-4 lg:px-6`
- Search bar hidden on xs screens (`hidden sm:block`), width responsive (`w-32 lg:w-48`)
- Main content padding responsive: `p-4 lg:p-6`
- Dashboard KPI grid uses `xl:grid-cols-6`, main grid uses `xl:grid-cols-3`
- Hero/Application Kit headers use `flex-wrap gap-4` for small screens

### Desktop App Readiness
- Created `webui/DESKTOP_ARCHITECTURE.md` with architecture recommendation
- Evaluated PyWebView+PyInstaller, Electron+React+Python, Tauri+React+Python
- Recommended PyWebView+PyInstaller as safest option (smallest bundle, single-process, native Python backend)
- No desktop packaging implemented — UI prepared for future packaging only

### Smoke Test Fix
- Fixed pre-existing bug in `tests/full_ui_smoke_test.py` where "linkedin live preview debounce" test targeted wrong tab index (3=Tools instead of 8=LinkedIn)
- Tab index now resolved dynamically from `app._nav_keys` instead of hardcoded
- Added fail-on-empty guard: test records clear FAIL if no Entry widgets found, instead of silently skipping
- Restored test count from 204 to 205 passes

### Files Changed
- `webui/src/index.css` — scrollbar, card, button, nav, kanban-scroll styles
- `webui/src/lib/mockData.ts` — `SHOW_MOCK_BADGE`, `mockProfile`, `mockSavedAnswers`, `mockStarChecklist`, cover letter name
- `webui/src/App.tsx` — mockProfile, conditional badge, responsive header/main
- `webui/src/components/KPICard.tsx` — hover shadow transition
- `webui/src/pages/Dashboard.tsx` — mockProfile greeting, responsive grids, flex-wrap hero
- `webui/src/pages/ApplicationKit.tsx` — Kanban layout, list overflow, flex-wrap header
- `webui/src/pages/InterviewPrep.tsx` — full rewrite with STAR, AI feedback, saved answers, stats
- `webui/src/pages/CoverLetterStudio.tsx` — mockProfile name
- `webui/src/pages/LinkedInComposer.tsx` — mockProfile name/role, message sign-offs
- `webui/DESKTOP_ARCHITECTURE.md` — new architecture note
- `tests/full_ui_smoke_test.py` — LinkedIn tab index fix with dynamic resolution

---

## [Phase 1] — 2026-06-30 — React UI Mock Prototype

### Web UI Foundation
- Created `webui/` directory with Vite + React + TypeScript + Tailwind CSS + Zustand + Recharts + Lucide-react
- Defined TypeScript types for all data structures in `lib/types.ts`
- Centralized all mock data in `lib/mockData.ts`
- Created shared components: `Sidebar`, `Card`, `StatusPill`, `ScoreCircle`, `KPICard`, `NextActionCard`, `ProgressBar`, `EmptyState`
- Created `useAppStore` Zustand store for page navigation and sidebar state

### Pages Implemented
- **Dashboard** — KPIs, weekly activity chart, application source pie chart, next best actions, top applications
- **Job Analysis** — JD paste area, AI analysis results with fit score, keyword matches, red/green flags
- **Application Kit** — Kanban board with 6 pipeline columns, list view toggle, search/filter
- **Cover Letter Studio** — Input form with company/role/tone, generated letter preview, copy/save actions
- **LinkedIn Composer** — Message type selector, input fields, generated message with character count
- **Interview Prep** — Question categories, timer, answer textarea, STAR framework guide for behavioral questions
- **Salary Calculator** — Base/bonus/equity/tax inputs, total compensation display, breakdown chart

### Design System
- Dark SaaS dashboard aesthetic with custom Tailwind color palette
- Custom font sizes including `2xs` for micro-text
- Fade-in and slide-up animations
- Custom scrollbar styling
- Responsive grid layouts

---

## Legacy Python Application (Pre-Phase 1)

### Excel Tracker
- 16 integrated sheets: Dashboard, Applications, Tracker, Salary, Interview Prep, Cover Letters, LinkedIn, Streak, Settings, JD Analysis, ATS Scores, Notion Sync, Email Templates, Reports, Backup Log, Validation

### Python Scripts (12)
- `auto_backup.py` — Scheduled Excel backup
- `email_reminder.py` — Application follow-up email reminders
- `data_export.py` — Export data to CSV/JSON
- `chart_generator.py` — Generate charts from tracker data
- `report_generator.py` — HTML/PDF report generation
- `sync_notion.py` — Two-way Notion database sync
- `test_formulas.py` — Excel formula validation
- `validate_data.py` — Data integrity validation
- `package_builder.py` — Release ZIP packaging
- `create_tracker.py` — Excel tracker creation from template
- `ats_resume_checker.py` — ATS resume score against job description
- `job_description_analyzer.py` — JD analysis with seniority, salary estimate, red/green flags

### Tkinter Desktop App
- `launcher.py` — Main application with 12 tabs, status bar, settings management
- `settings.py` — Settings persistence and validation
- `i18n.py` — Turkish/English internationalization
- `tests/test_settings_save.py` — Settings save/load test (11 passes)
- `tests/full_ui_smoke_test.py` — Full UI smoke test (205 passes)
