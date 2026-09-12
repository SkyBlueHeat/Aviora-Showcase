# Roadmap — Developer Job Application Tracker PRO

Product planning document. Updated based on external feedback from a
Senior Front-End Developer review (2026-07-01) and dual distribution
architecture planning (2026-07-01).

---

## Current State

- **Phase 1.6** — Desktop Shell POC (PyWebView + PyInstaller) ✅
- **Phase 1.7** — Desktop Distribution Polish (icon, offline fonts, favicon, packaging) ✅
- **Core MVP** — Fast-Track Core MVP Sprint (edit, refresh, workbook selection + status UI, empty state, error handling, verification, manual validation) ✅
- Legacy Python/Excel application remains fully functional and untouched.
- React UI runs as a native Windows desktop app with full Excel read/write integration.

---

## 1. Dual Distribution Strategy

**Long-term product vision:** Two versions available from the website.

| Version | Delivery | Data Storage | Offline | Price Model |
|---|---|---|---|---|
| **Desktop App** | Windows .exe download | Local files (Excel) | ✅ Full | One-time payment |
| **Web App** (future) | Browser, no download | Cloud sync | ❌ Requires internet | Subscription or freemium |

### Website Positioning

```
┌─────────────────────────────────────────────────────┐
│              JobTracker PRO Website                  │
│                                                      │
│  ┌─────────────────┐    ┌─────────────────────────┐ │
│  │  Desktop App     │    │  Web App (Coming Soon)  │ │
│  │                  │    │                         │ │
│  │  • Local-first   │    │  • No download          │ │
│  │  • Private       │    │  • Cloud sync           │ │
│  │  • Offline       │    │  • Access anywhere      │ │
│  │  • One-time $    │    │  • Subscription         │ │
│  │  • Windows .exe  │    │  • Browser-based        │ │
│  └─────────────────┘    └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Why Desktop Remains the MVP

1. **Already built** — Phase 1.7 desktop shell is complete and working.
2. **No infrastructure cost** — No servers, databases, auth, or cloud bills.
3. **Privacy selling point** — Local-first is a genuine differentiator vs. cloud tools.
4. **One-time payment** — Simpler business model for Etsy/direct sale.
5. **Faster to market** — No auth, no hosting, no compliance, no GDPR concerns.
6. **Proves product value** — Real Excel integration validates the core use case.

### Why Web App Comes Later

1. **Infrastructure** — Requires hosting, database, auth, and cloud storage.
2. **Compliance** — GDPR, data protection, user accounts, password security.
3. **Cost** — Monthly server + database + auth provider costs.
4. **Complexity** — Cloud sync conflict resolution, offline queue, multi-device.
5. **Business model** — Subscription pricing needs recurring billing infrastructure.

### Risks of Maintaining Both Versions

| Risk | Mitigation |
|---|---|
| **Code duplication** | Adapter pattern — React UI is shared, only data layer differs |
| **Feature divergence** | Desktop features must work through the adapter interface; no direct Excel calls from React |
| **Testing burden** | Mock adapter tests cover the shared UI; each adapter has its own integration tests |
| **Release coordination** | Desktop ships first; web follows when infrastructure is ready |
| **Support complexity** | Clear version labeling; web app is a separate product, not a free add-on |
| **Data migration** | If users switch from desktop to web, need an import/export path (Excel → cloud) |

---

## 2. Product Positioning Validation

**Current MVP direction:** Local-first, private Windows desktop workspace.

**Must validate:**
- User trust — are users comfortable downloading and running a .exe?
- Download friction — does the download + SmartScreen warning drop conversion?
- Security perception — users may feel safer with browser-based tools

**Architecture principle:**
- The React UI must **not** be tightly coupled to pywebview, Excel, or desktop-only APIs.
- An adapter-based data layer keeps both delivery paths possible.
- See Section 7 for the full adapter architecture specification.

**Future delivery options to keep open:**
- Web app version (browser-based, no download)
- Browser extension version
- Hybrid: desktop app with optional web companion

---

## 3. Differentiation

| Pillar | Description |
|---|---|
| **Local-first privacy** | All data stays on the user's machine. No cloud, no tracking. |
| **One-time payment** | Alternative to subscription-heavy web tools ($9.99–$24.99). |
| **Serious command center** | Not a simple tracker — interview prep, JD analysis, ATS scoring, salary calc. |
| **Offline capable** | Works without internet. No CDN dependencies. System fonts only. |

**Messaging must address:**
- Why downloading is safe (no telemetry, no network calls, open architecture)
- What data stays local (everything — no cloud sync)
- SmartScreen warning explanation (no code signing certificate yet)
- Future web version possibility (not locked to desktop only)
- Desktop vs Web comparison on the website so users can choose

---

## 4. Future Feature: Interview Company Brief

A rich company profile attached to each interview calendar slot,
giving the candidate a quick briefing before the interview.

### Fields

| Field | Type | Description |
|---|---|---|
| `company_name` | string | Company name |
| `domain_industry` | string | e.g. "Fintech", "Healthcare SaaS" |
| `team_size` | string | e.g. "5 engineers", "20+ team" |
| `tech_stack` | string[] | e.g. ["React", "Python", "AWS", "PostgreSQL"] |
| `sprint_length` | string | e.g. "2 weeks" |
| `deployment_frequency` | string | e.g. "Daily", "Weekly", "CI/CD on merge" |
| `benefits` | string[] | e.g. ["Remote-first", "401k match", "Learning budget"] |
| `company_problems` | string | Known challenges or problems the team is solving |
| `suggested_questions` | string[] | Questions the candidate should consider asking |
| `notes` | string | Free-form notes |
| `interview_datetime` | datetime | Scheduled interview date and time |
| `calendar_link` | string (optional) | Future: Google Calendar event link |

### Concept

When a user has an interview scheduled, they can open the Interview Prep
page and see a structured company brief — a quick-reference card with
all the key info they need before walking into the interview.

This feature is **planned for Phase 3** — after Excel data integration
is complete and the app has real data flowing.

---

## 5. Future Integration: Google Calendar

**Status:** Roadmap only. Do not implement.

- Sync interview dates to Google Calendar
- Generate calendar event links from Interview Company Brief entries
- Optional reminders/notifications via calendar
- Would require OAuth2 flow or calendar link generation (ICS export as simpler alternative)

**Planned for Phase 4** — after Interview Company Brief is built.

---

## 6. Phase Order

### Completed

| Phase | Name | Status |
|---|---|---|
| 1.0–1.5 | React UI + mock data + page implementations | ✅ Done |
| 1.6 | Desktop Shell POC (PyWebView + PyInstaller) | ✅ Done |
| 1.7 | Desktop Distribution Polish (icon, offline, packaging) | ✅ Done |
| 2A.0–2A.3 | Excel read-only bridge + React integration + demo workbook | ✅ Done |
| 2B.0 | Backup system + write safety docs | ✅ Done |
| 2B.1 | Demo workbook write actions (backend) | ✅ Done |
| 2B.2 | Demo UI write integration (React modal + status dropdown) | ✅ Done |
| 2B.3A | Staging write validation | ✅ Done |
| 2B.3B | Production write enablement | ✅ Done |
| **Core MVP** | Fast-Track Core MVP Sprint | ✅ Done |

### Next Phases

| Phase | Name | Goal | Key Deliverable |
|---|---|---|---|
| **2B.3B** | Production Write Enablement | Enable controlled writes to the real production workbook with explicit opt-in safety gate | Production write mode with JOBTRACKER_ENABLE_PRODUCTION_WRITES=1 | ✅ Done |
| **Core MVP** | Fast-Track Core MVP Sprint | Application editing, dashboard refresh, workbook selection + status UI, empty state, error handling, verification script, manual validation | All Core MVP features implemented and verified | ✅ Done |
| **3** | Interview Company Brief | New page/section with company profile fields, linked to interview prep | Company Brief feature complete |
| **4** | Calendar Integration | Google Calendar sync or ICS export for interview dates | Calendar events from app |
| **5** | Web App MVP Exploration | Evaluate delivering the same UI as a browser-based web app using the WebAdapter; prototype cloud backend | Feasibility report + WebAdapter prototype |
| **6** | Browser Extension Exploration | Evaluate browser extension for JD analysis / ATS scoring on job sites | Feasibility report + prototype decision |

### Phase Dependency Graph

```
1.7 (done) → 2A.0 → 2A.1 → 2A.2 → 2B.0 → 2B.1 → 2B.2 → 2B.3A → 2B.3B → 3 → 4 → 5 → 6
                                                              ↗
                          (adapter layer from 2A.0 keeps both paths open)
```

### Why This Order

1. **Excel first (2A)** — The product's core value is real data. Without real Excel data, the desktop app is a UI demo. This is the highest priority.
2. **Write actions second (2B)** — Read-only proves the bridge works. Write actions add risk (data corruption), so they come after the read path is solid.
3. **Interview Company Brief third (3)** — A new feature that builds on real data. Users will have real interviews to track.
4. **Calendar fourth (4)** — Depends on Interview Company Brief having dates to sync.
5. **Web App MVP exploration (5)** — Only meaningful after the core product works end-to-end with real data. The adapter layer from 2A.0 makes this possible without rewriting the UI.
6. **Browser extension (6)** — JD analysis and ATS scoring could work as a browser extension on job sites. Evaluated after the web app proves the cloud backend.

---

## 7. Adapter-Based Data Layer Architecture

**Core principle:** React components never call `pywebview.api`, `openpyxl`,
`fetch()`, or any backend directly. They consume typed data through
a single `dataService.ts` interface. The adapter is selected at startup.

### Architecture Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    React UI (shared)                      │
│                                                           │
│  Components call: dataService.getApplications(), etc.    │
│  Components receive: typed TS objects (Application[],     │
│    JobStats, InterviewQuestion[], etc.)                  │
│  Components never know which adapter is active.           │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│                  dataService.ts                           │
│                                                           │
│  • Detects environment (pywebview? window.api?)          │
│  • Selects adapter at startup                            │
│  • Exposes typed methods: getApplications, getStats,     │
│    saveApplication, getSettings, saveSettings, etc.      │
│  • Falls back to MockAdapter if no backend detected      │
└────────────────────────┬─────────────────────────────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│DesktopAdapter│ │  WebAdapter  │ │ MockAdapter  │
│              │ │  (future)    │ │              │
│ Uses:        │ │ Uses:        │ │ Uses:        │
│ pywebview    │ │ fetch() to   │ │ Hardcoded    │
│ .api calls   │ │ REST API     │ │ mock data    │
│ to local     │ │ (Flask/      │ │ (mockData.ts)│
│ Python       │ │  FastAPI)    │ │              │
│ backend      │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
     │                  │               │
     ▼                  ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Python local │ │ Cloud backend│ │  In-memory   │
│ openpyxl     │ │ (PostgreSQL/ │ │  (demo/fallb.)│
│ Excel r/w    │ │  Supabase)   │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

### Data Layer Rules

1. **No direct backend calls from components** — React components import `dataService`, never `pywebview` or `fetch`.
2. **Typed interface** — `dataService.ts` defines a TypeScript interface (`DataService`) that all adapters implement.
3. **Adapter selection at startup** — `dataService.ts` detects the environment and picks the right adapter:
   - `window.pywebview` exists → `DesktopAdapter`
   - `window.__WEB_API_BASE__` exists → `WebAdapter` (future)
   - Neither → `MockAdapter` (fallback/demo)
4. **Mock always available** — `MockAdapter` is always importable for tests, demos, and fallback.
5. **Identical return types** — All adapters return the same TypeScript types. The UI doesn't know or care which adapter is active.
6. **No Excel types in React** — Adapters translate backend-specific structures (Excel rows, API JSON) into shared TS types.
7. **Write methods return results** — `saveApplication()` returns `{ success: boolean, error?: string }`, not Excel-specific data.
8. **Error handling is adapter-specific** — Each adapter handles its own errors (file not found, network error, etc.) and returns a normalized error to the UI.

### DataService Interface (conceptual)

```typescript
interface DataService {
  // Read
  getApplications(): Promise<Application[]>
  getApplication(id: string): Promise<Application | null>
  getStats(): Promise<JobStats>
  getSettings(): Promise<Settings>
  getInterviewQuestions(category: string): Promise<InterviewQuestion[]>
  getStreakData(): Promise<StreakData>

  // Write
  saveApplication(app: Application): Promise<SaveResult>
  updateApplicationStatus(id: string, status: string): Promise<SaveResult>
  saveSettings(settings: Settings): Promise<SaveResult>

  // Analysis
  analyzeJobDescription(text: string): Promise<JDAnalysis>
  scoreResume(resume: string, jobDescription: string): Promise<ATSScore>
}
```

### File Structure (planned for Phase 2A.0)

```
webui/src/
  lib/
    dataService.ts          ← exports active adapter, typed interface
    adapters/
      DesktopAdapter.ts     ← pywebview.api bridge (Phase 2A.1)
      WebAdapter.ts         ← fetch() to REST API (Phase 5, stub only)
      MockAdapter.ts        ← current mockData.ts logic
    types.ts                ← shared TS types (already exists)
    mockData.ts             ← mock data (already exists, used by MockAdapter)
```

### Migration Path from Current Code

- **Now (Phase 1.7):** React imports `mockData.ts` directly in components.
- **Phase 2A.0:** Create `dataService.ts` + `MockAdapter.ts` wrapping existing mock data. Components switch to `dataService`.
- **Phase 2A.1:** Add `DesktopAdapter.ts` calling `pywebview.api`. `dataService.ts` auto-selects it when running in desktop shell.
- **Phase 5:** Add `WebAdapter.ts` calling REST API. `dataService.ts` auto-selects it when running in browser with API config.

---

## 8. Architecture Principles for Upcoming Phases

1. **Adapter-first** — React components consume typed data through `dataService.ts`. No direct pywebview, Excel, or fetch calls in components.
2. **Mock fallback** — `MockAdapter` is always available so the UI never breaks if no backend is detected.
3. **Backup before write** — Any Excel write action must create a timestamped backup copy before modifying the workbook.
4. **No tight coupling** — React components consume typed data, not Excel-specific or API-specific structures. Adapters translate backend → typed objects.
5. **Legacy safety** — The existing `launcher.py` / `settings.py` / `i18n.py` / scripts / tests must continue to work independently.
6. **Shared UI, separate backends** — The React component tree is identical for desktop and web. Only the adapter differs.

---

## 9. Release & Backup Strategy

There are two distinct package types for checkpoints and backups:

### 9.1 Source Checkpoint Package

Used for phase milestones, version tagging, and clean handoff.

**Includes:**
- Source code (Python + React/TypeScript)
- Tests and test fixtures
- Documentation (ROADMAP, CHANGELOG, guides, mapping docs)
- Config templates (requirements.txt, package.json, tsconfig, etc.)
- Excel workbook template (empty or schema-only)

**Excludes:**
- Runtime/user data (settings.json, interview_scores.json, streak_data.json)
- Build artifacts (node_modules, dist, build, __pycache__)
- User-generated outputs (backups, charts, exports, reports, cover letters, linkedin messages)
- Old release zips

**Examples:** `JobTracker_PRO_Phase_2A_1_ReadOnly_Bridge_Adapter_Source.zip`

### 9.2 Full Restore Backup Package

Used for disaster recovery or migrating the app to a new machine.

**Includes everything from Source Checkpoint, plus:**
- Runtime data files:
  - `settings.json` — user profile, preferences, API keys
  - `interview_scores.json` — interview practice history
  - `streak_data.json` — daily streak tracking state
- Current workbook with user data (`Developer_Job_Application_Tracker_PRO.xlsx`)
- User-generated outputs if needed (exports, reports, cover letters, linkedin messages)
- Anything required to fully restore the local app state

**Excludes:**
- Build artifacts (node_modules, dist, build, __pycache__)
- Old release zips

**Naming convention:** `JobTracker_PRO_Full_Restore_YYYYMMDD_HHMMSS.zip`

---

## External Feedback Log

| Date | Source | Feedback | Action Taken |
|---|---|---|---|
| 2026-07-01 | Senior Front-End Developer | Desktop direction may conflict with user behavior (download reluctance) | Added positioning validation section; architecture must stay web-capable |
| 2026-07-01 | Senior Front-End Developer | Liked interview prep, JD analysis, fit score, keyword matching | Confirmed as core differentiators; continue investing |
| 2026-07-01 | Senior Front-End Developer | Suggested Interview Company Brief with company profile fields | Added as Phase 3 feature concept |
| 2026-07-01 | Senior Front-End Developer | Suggested Google Calendar integration | Added as Phase 4 roadmap item |
| 2026-07-01 | Product planning | Dual distribution strategy (desktop + future web) | Added Section 1 (dual distribution), Section 7 (adapter architecture), updated phase order |
