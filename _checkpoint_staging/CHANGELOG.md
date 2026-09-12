# Changelog — Developer Job Application Tracker PRO v2.0

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/) conventions.

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
