# Excel Workbook Mapping — Phase 2A.0

Complete mapping of `Developer_Job_Application_Tracker_PRO.xlsx` to the React UI.

**Inspection date:** 2026-07-01
**Mode:** `read_only=True`, `data_only=True` — no writes performed.
**Workbook:** 16 sheets, 1 sample row per data sheet (template workbook).

---

## 1. Workbook Structure Overview

| # | Sheet Name | Cols | Header Row | Data Rows | Relevance |
|---|---|---|---|---|---|
| 1 | Dashboard | 9 | 2 (layout) | 0 (labels only) | dashboard |
| 2 | Applications | 33 | 1 | 0 (headers only) | applications |
| 3 | Interview Tracker | 17 | 1 | 1 | interviews |
| 4 | Recruiter CRM | 15 | 1 | 1 | networking |
| 5 | Target Companies | 19 | 1 | 1 | company research |
| 6 | Salary Comparison | 19 | 1 | 1 | salary |
| 7 | Weekly Planner | 8 | 1 | 1 | planning |
| 8 | Statistics | 7 | 2 (layout) | 0 (labels only) | dashboard/stats |
| 9 | Notes | 7 | 2 (layout) | 0 | notes |
| 10 | Portfolio Projects | 15 | 1 | 1 | portfolio |
| 11 | Networking Tracker | 19 | 1 | 1 | networking |
| 12 | Skill Gap Analysis | 18 | 1 | 1 | skills |
| 13 | Cover Letter Tracker | 12 | 1 | 1 | cover letters |
| 14 | Job Search Calendar | 11 | 1 | 1 | calendar/interviews |
| 15 | Learning Resources | 14 | 1 | 1 | learning |
| 16 | Offer Decision Matrix | 20 | 1 | 1 | salary/offers |

**Key observations:**
- The workbook is a **template** — most sheets have 0 or 1 sample data rows.
- `Dashboard` and `Statistics` are **layout sheets** with merged cells and labels, not tabular data. They contain formulas that reference the `Applications` sheet.
- `Applications` has 33 columns but **no data rows** (headers only).
- Many formula columns return `None` in `data_only` mode because the workbook was not last saved by Excel (formulas not cached).

---

## 2. Sheet-by-Sheet Column Mapping

### 2.1 Applications → React Application Kit + Dashboard

**Excel sheet:** `Applications` (33 columns, header row 1)

| # | Excel Column | React Field | TS Type | Notes |
|---|---|---|---|---|
| 0 | Application ID | `id` | string | Direct map |
| 1 | Company | `company` | string | Direct map |
| 2 | Role | `role` | string | Direct map |
| 3 | Location | `location` | string | Direct map |
| 4 | Country | — | — | Not in TS type yet; could add |
| 5 | Remote | `workType` | WorkType | Map "Yes"→"Remote", "No"→"On-site", "Hybrid"→"Hybrid" |
| 6 | Salary | `salary` | string | Direct map (stored as string range) |
| 7 | Source | `source` | string | Direct map |
| 8 | Date Applied | `appliedDate` | string | Date format normalization needed |
| 9 | Status | `status` | ApplicationStatus | See status mapping table below |
| 10 | Priority | `priority` | Priority | Direct map (Critical/High/Medium/Low) |
| 11 | Fit Score | `fitScore` | number | Direct map (0-100) |
| 12 | Follow-up Date | `followUpDate` | string? | Direct map |
| 13 | Recruiter | — | — | Not in TS type; could add |
| 14 | LinkedIn Recruiter | — | — | Not in TS type |
| 15 | Interview Date | — | — | Could feed Interview Tracker |
| 16 | Offer | — | — | Boolean/amount; not in TS type |
| 17 | Application URL | — | — | Not in TS type; could add |
| 18 | Company Career Page | — | — | Not in TS type |
| 19 | Resume Version | — | — | Not in TS type |
| 20 | Cover Letter Version | — | — | Not in TS type |
| 21 | Visa Sponsorship | — | — | Not in TS type |
| 22 | Employment Type | — | — | Not in TS type |
| 23 | Work Authorization | — | — | Not in TS type |
| 24 | Referral | — | — | Not in TS type |
| 25 | Expected Salary | — | — | Not in TS type |
| 26 | Current Stage | — | — | May duplicate Status; needs clarification |
| 27 | Days Since Applied | — | — | Formula (computed); not cached |
| 28 | Days Until Follow-up | — | — | Formula (computed); not cached |
| 29 | Interview Count | — | — | Formula (computed); not cached |
| 30 | Favorite | — | — | Boolean flag; not in TS type |
| 31 | Archive | — | — | Boolean flag; not in TS type |
| 32 | Notes | `notes` | string | Direct map |

**Missing in Excel vs React:**
- `qualityScore` — not in Excel; React mock has it. **Mock fallback or compute from other fields.**
- `techStack` — not in Applications sheet; could come from Target Companies sheet or be mock-only.
- `nextAction` — not in Excel; could be computed from Status + Follow-up Date.

**Status value mapping (Excel → React pipeline columns):**

| Excel Status | React ApplicationStatus | Pipeline Column |
|---|---|---|
| Saved | `Saved` | Saved |
| Applied | `Applied` | Applied |
| Phone Screen | `Phone Screen` | Phone Screen |
| Technical | `Technical` | Technical |
| Onsite | `Onsite` | Onsite |
| Offer | `Offer` | Offer |
| Rejected | `Rejected` | Rejected |
| Ghosted | `Ghosted` | Ghosted |

**Assessment:** Status values appear to match 1:1. This is the cleanest mapping.

---

### 2.2 Interview Tracker → React Interview Prep

**Excel sheet:** `Interview Tracker` (17 columns, header row 1)

| # | Excel Column | React Field | Notes |
|---|---|---|---|
| 0 | Company | — | Link to Application by company name |
| 1 | Role | — | Link to Application |
| 2 | Interview Stage | — | Maps to question category (Technical/Behavioral) |
| 3 | Interviewer | — | Not in TS type; future field |
| 4 | Interview Date | — | Not in TS type; future field |
| 5 | Interview Number | — | Not in TS type |
| 6 | Duration (min) | — | Not in TS type |
| 7 | Preparation Status | — | Not in TS type |
| 8 | Confidence Score | — | Not in TS type; could map to ScoreCircle |
| 9 | Difficulty | `difficulty` | Maps to InterviewQuestion.difficulty |
| 10 | Result | — | Not in TS type |
| 11 | Technical Topics | — | Not in TS type; future field |
| 12 | Coding Questions | — | Could feed Interview Prep questions |
| 13 | Behavioral Questions | — | Could feed Interview Prep questions |
| 14 | Next Step | — | Not in TS type |
| 15 | Notes | — | Not in TS type |
| 16 | Lessons Learned | — | Not in TS type |

**Assessment:** Interview Tracker is a log of past interviews, while React Interview Prep is a practice tool with questions. **Weak direct mapping.** The Excel sheet could provide historical data (past interviews, results) but not the practice questions themselves. Questions should remain mock-only for now.

---

### 2.3 Salary Comparison → React Salary Calculator

**Excel sheet:** `Salary Comparison` (19 columns, header row 1)

| # | Excel Column | React Field | TS Type | Notes |
|---|---|---|---|---|
| 0 | Company | — | — | Context only |
| 1 | Base Salary | `baseSalary` | number | Direct map |
| 2 | Bonus | — | — | React uses `bonusPct` (percentage); Excel has absolute. Need conversion. |
| 3 | Equity | `equity` | number | Direct map |
| 4 | Benefits Value | `benefits` | number | Direct map (may need string→number parse) |
| 5 | PTO Days | — | — | Not in TS type |
| 6 | Remote | — | — | Not in TS type |
| 7 | Visa Sponsorship | — | — | Not in TS type |
| 8 | Signing Bonus | `signingBonus` | number | Direct map |
| 9 | Relocation Bonus | — | — | Not in TS type |
| 10 | Annual Compensation | — | — | Formula; not cached |
| 11 | Monthly Income | — | — | Formula; not cached |
| 12 | Hourly Rate | — | — | Formula; not cached |
| 13 | Total Compensation | `totalComp` | number | Formula; may need to compute in Python |
| 14 | Estimated Tax (25%) | — | — | Formula; not cached |
| 15 | Net Salary | `netAnnual` | number | Formula; may need to compute in Python |
| 16 | Decision Score | — | — | Not in TS type |
| 17 | Weighted Score | — | — | Formula; not cached |
| 18 | Offer Ranking | — | — | Formula; not cached |

**Assessment:** Base fields (salary, bonus, equity, benefits) map well. Formula columns (Total Comp, Net Salary, Monthly Income) are not cached in `data_only` mode — **Python bridge must recompute these.** React's `bonusPct` vs Excel's absolute `Bonus` is a mismatch — either change TS type or convert in adapter.

---

### 2.4 Cover Letter Tracker → React Cover Letter Studio

**Excel sheet:** `Cover Letter Tracker` (12 columns, header row 1)

| # | Excel Column | React Field | Notes |
|---|---|---|---|
| 0 | Company | `companyName` | Direct map |
| 1 | Role | `jobTitle` | Direct map |
| 2 | Version | — | Not in TS type |
| 3 | Date Created | — | Not in TS type |
| 4 | Date Sent | — | Not in TS type |
| 5 | Template Used | — | Not in TS type |
| 6 | Customization Level | — | Not in TS type |
| 7 | Response Received | — | Not in TS type |
| 8 | Interview Scheduled | — | Not in TS type |
| 9 | Success Rate | — | Formula; not cached |
| 10 | A/B Test Group | — | Not in TS type |
| 11 | Notes | — | Not in TS type |

**Assessment:** Cover Letter Tracker is a **tracking log** (which letters were sent, response rates). React Cover Letter Studio is a **generator** (creates new letters). These serve different purposes. The tracker data could show history/metrics, but the generator should remain mock/computed for now.

---

### 2.5 Dashboard → React Dashboard

**Excel sheet:** `Dashboard` (layout sheet, not tabular)

The Dashboard sheet contains:
- Title: "Developer Job Application Tracker PRO"
- KPI labels: Total Applications, Active Applications, Interviews, Offers
- These are **formula-driven** from the Applications sheet

**Mapping to React KPIs:**

| React KPI | Excel Source | Computation |
|---|---|---|
| Total Applications | Applications sheet | `COUNTA(Application ID column)` |
| Active | Applications sheet | `COUNTIF(Status, not in [Rejected, Ghosted, Offer])` |
| Interviews | Applications sheet | `COUNTIF(Status, in [Phone Screen, Technical, Onsite])` |
| Offers | Applications sheet | `COUNTIF(Status, "Offer")` |
| Response Rate | Applications sheet | `COUNTIF(Status, not in [Saved, Applied, Ghosted]) / total` |
| Ghosted | Applications sheet | `COUNTIF(Status, "Ghosted")` |

**Assessment:** Dashboard KPIs should be **computed in Python** from the Applications sheet, not read from the Dashboard sheet (which has uncached formulas). This is the correct approach for the bridge.

---

### 2.6 Statistics → React Dashboard Charts

**Excel sheet:** `Statistics` (layout sheet, not tabular)

Contains labels for:
- Application Metrics: Applications Submitted, Applications per Week
- Conversion Rates: Response Rate, Interview Rate

**Mapping to React chart data:**

| React Chart | Excel Source | Computation |
|---|---|---|
| Monthly activity chart | Applications sheet | Group by `Date Applied` month, count per status |
| Source pie chart | Applications sheet | Group by `Source`, count |

**Assessment:** Chart data must be **computed in Python** by aggregating Applications. The Statistics sheet itself is not usable (layout/formula sheet).

---

### 2.7 Job Search Calendar → Future Interview Company Brief

**Excel sheet:** `Job Search Calendar` (11 columns, header row 1)

| # | Excel Column | Future Company Brief Field | Notes |
|---|---|---|---|
| 0 | Date | `interview_datetime` | Direct map |
| 1 | Event Type | — | Context (Technical Assessment, Interview, etc.) |
| 2 | Company | `company_name` | Direct map |
| 3 | Role | — | Context |
| 4 | Time | — | Part of datetime |
| 5 | Location/Link | — | Not in Company Brief fields |
| 6 | Preparation Needed | — | Could map to `notes` |
| 7 | Status | — | Context |
| 8 | Priority | — | Context |
| 9 | Follow-up Required | — | Context |
| 10 | Notes | `notes` | Direct map |

**Assessment:** This sheet has **partial overlap** with the future Interview Company Brief feature (Phase 3). The Company Brief will need additional fields not in this sheet: `domain_industry`, `team_size`, `tech_stack`, `sprint_length`, `deployment_frequency`, `benefits`, `company_problems`, `suggested_questions`. These would need new Excel columns or a new sheet.

---

### 2.8 Other Sheets — No Direct React Mapping (Yet)

| Sheet | Cols | Assessment |
|---|---|---|
| Recruiter CRM | 15 | No React page. Future: networking/CRM page. |
| Target Companies | 19 | No React page. Future: company research page. Contains `Tech Stack`, `Industry`, `Size` — useful for Company Brief. |
| Weekly Planner | 8 | No React page. Future: planning page. |
| Notes | 7 | Layout sheet. No React page. |
| Portfolio Projects | 15 | No React page. Future: portfolio showcase. |
| Networking Tracker | 19 | No React page. Future: networking page. |
| Skill Gap Analysis | 18 | No React page. Future: skills page. |
| Learning Resources | 14 | No React page. Future: learning page. |
| Offer Decision Matrix | 20 | No React page. Could enrich Salary Calculator with offer comparison. |

---

## 3. Excel Status Values → Application Kit Pipeline

| Excel Status | React Pipeline Column | Color |
|---|---|---|
| Saved | Saved | #64748B |
| Applied | Applied | #6366F1 |
| Phone Screen | Phone Screen | #22D3EE |
| Technical | Technical | #A78BFA |
| Onsite | Onsite | #FBBF24 |
| Offer | Offer | #34D399 |
| Rejected | Rejected | #F43F5E |
| Ghosted | Ghosted | #64748B |

**Status mapping is 1:1.** No transformation needed. This is the cleanest part of the bridge.

---

## 4. Excel Values → Dashboard KPIs

All KPIs must be **computed in Python** from the Applications sheet:

| KPI | Formula (pseudo) |
|---|---|
| Total Applications | `len(applications)` |
| Active | `count where status not in [Rejected, Ghosted]` |
| Interviews | `count where status in [Phone Screen, Technical, Onsite]` |
| Offers | `count where status == Offer` |
| Response Rate | `count where status not in [Saved, Applied, Ghosted] / total * 100` |
| Ghosted | `count where status == Ghosted` |

---

## 5. Excel Values → Charts

All chart data must be **computed in Python** from the Applications sheet:

| Chart | Computation |
|---|---|
| Monthly activity | Group by `Date Applied` month → count per status category |
| Source distribution | Group by `Source` column → count |

---

## 6. Missing Excel Fields → Mock Fallback or Computed

| React Field | Excel Source | Strategy |
|---|---|---|
| `qualityScore` | Not in Excel | **Mock fallback** — no Excel equivalent. Could compute from interview results in future. |
| `techStack` | Not in Applications sheet | **Mock fallback** — could pull from Target Companies sheet by company name match, or leave mock. |
| `nextAction` | Not in Excel | **Computed** — derive from Status + Follow-up Date + Priority. |
| `bonusPct` | Excel has absolute Bonus | **Convert** — `bonusPct = (Bonus / Base Salary) * 100` in adapter. |
| `netMonthly` | Formula in Excel (not cached) | **Compute in Python** — `netAnnual / 12`. |
| `taxBracket` | Not in Excel | **Mock/default** — use "25%" as default. |

---

## 7. Fields That Should Remain Mock-Only (For Now)

| Field | Reason |
|---|---|
| Interview questions (all categories) | Excel has no question bank; questions are a practice tool feature |
| STAR framework examples | Not in Excel; generated/coached content |
| Cover letter generated text | Excel tracks sent letters, not generated content |
| LinkedIn message generated text | Excel has no LinkedIn message content |
| JD analysis results | Computed by Python script, not stored in Excel |
| ATS score results | Computed by Python script, not stored in Excel |
| Saved interview answers | Not in Excel; UI-only feature |
| Streak data | Stored in `streak_data.json`, not in Excel workbook |

---

## 8. Data Quality Issues

| Issue | Sheet | Details |
|---|---|---|
| **Uncached formulas** | All formula columns | `data_only=True` returns `None` for formulas not last saved by Excel. Python bridge must recompute. |
| **Empty Applications sheet** | Applications | 33 headers but 0 data rows. Bridge must handle empty gracefully (return empty array, not error). |
| **Date format inconsistency** | Multiple sheets | Some dates are strings ("2026-06-29"), some may be Excel date objects. Bridge must normalize to ISO format. |
| **Status vs Current Stage** | Applications | Both columns exist; unclear if they duplicate. Need to clarify which is authoritative. |
| **Salary as string** | Applications | Salary stored as string range ("$180k - $220k"), not numeric. Salary Comparison sheet has numeric values. |
| **Remote field mapping** | Applications | "Remote" column likely has "Yes"/"No"/"Hybrid" — needs mapping to `WorkType` enum. |
| **Dashboard/Statistics layout** | Dashboard, Statistics | These are layout sheets with merged cells, not tabular data. Must not try to parse as tables. |
| **Benefits Value type** | Salary Comparison | "Full Health" (string) vs 15000 (number) — inconsistent. Needs normalization. |

---

## 9. Future Fields for Interview Company Brief (Phase 3)

The following fields from the ROADMAP are **not in the current workbook** and would need either:
- New columns in an existing sheet
- A new "Company Brief" sheet
- A separate JSON file

| Company Brief Field | Closest Excel Source | Gap |
|---|---|---|
| `company_name` | Applications.Company / Target Companies.Company | Available |
| `domain_industry` | Target Companies.Industry | Available |
| `team_size` | Target Companies.Size | Available (but format may differ) |
| `tech_stack` | Target Companies.Tech Stack | Available |
| `sprint_length` | — | **Not in workbook** — new field needed |
| `deployment_frequency` | — | **Not in workbook** — new field needed |
| `benefits` | Salary Comparison.Benefits Value / Offer Decision Matrix | Partial — needs structured format |
| `company_problems` | — | **Not in workbook** — new field needed |
| `suggested_questions` | — | **Not in workbook** — new field needed |
| `notes` | Job Search Calendar.Notes / Applications.Notes | Available |
| `interview_datetime` | Job Search Calendar.Date + Time | Available |
| `calendar_link` | — | **Not in workbook** — future Google Calendar integration |

**Recommendation:** Create a new "Company Brief" sheet in Phase 3 rather than overloading existing sheets.

---

## 10. Summary: Sheet → React Page Mapping

| React Page | Primary Excel Sheet | Secondary Sheets | Computed? |
|---|---|---|---|
| Dashboard | Applications | Statistics (labels only) | KPIs computed in Python |
| Application Kit | Applications | — | Direct read |
| Job Analysis | — | — | Mock-only (Python script computes, not stored) |
| Cover Letter Studio | Cover Letter Tracker | — | Generator is mock; tracker is history |
| LinkedIn Composer | — | — | Mock-only (no Excel data) |
| Interview Prep | Interview Tracker | Job Search Calendar | Questions mock-only; history from Excel |
| Salary Calculator | Salary Comparison | Offer Decision Matrix | Formula fields recomputed in Python |

---

## 11. Recommended Phase 2A.1 Read-Only Bridge Architecture

### Folder Structure

```
backend_bridge/
  __init__.py
  excel_reader.py          ← Read-only openpyxl wrapper (never writes)
  data_mapper.py           ← Excel rows → typed Python dicts
  api.py                   ← PyWebView API class (methods exposed to React)
  EXCEL_MAPPING.md         ← This document
  workbook_inspection_report.json  ← Raw inspection data
```

### Python Modules

**`excel_reader.py`** — Safe read-only wrapper:
- Opens workbook with `read_only=True, data_only=True`
- Closes workbook after each read batch
- Never calls `wb.save()` — no write methods exposed
- Returns raw row data as lists

**`data_mapper.py`** — Transform raw rows to typed dicts:
- `map_application(row)` → `dict` matching `Application` TS type
- `map_salary(row)` → `dict` matching `SalaryBreakdown` TS type
- `map_interview(row)` → `dict` for interview history
- `compute_kpis(applications)` → `dict` matching `KPICard[]`
- `compute_charts(applications)` → monthly + source data
- Handles None values, date normalization, status mapping
- Computes formula fields (Total Comp, Net Salary, Days Since Applied)

**`api.py`** — PyWebView API bridge:
- Class with methods: `get_applications()`, `get_kpis()`, `get_salary_data()`, etc.
- Returns JSON-serializable dicts
- Each method calls `excel_reader` → `data_mapper` → returns result
- Error handling: returns `{ error: "...", data: null }` on failure

### TypeScript Types (update `types.ts` in Phase 2A.2)

The existing types are mostly sufficient. Suggested additions:
- `Application.recruiter?: string`
- `Application.applicationUrl?: string`
- `Application.visaSponsorship?: boolean`
- `Application.employmentType?: string`
- Remove or make optional: `qualityScore` (not in Excel)
- Add: `DataServiceResult<T> = { data?: T; error?: string }`

### JSON Response Shapes

```json
// get_applications()
{
  "data": [
    {
      "id": "1",
      "company": "Tech Corp",
      "role": "Senior Frontend Developer",
      "status": "Applied",
      "priority": "High",
      "workType": "Remote",
      "location": "San Francisco, CA",
      "appliedDate": "2026-06-29",
      "salary": "$150k - $180k",
      "fitScore": 85,
      "source": "LinkedIn",
      "notes": "",
      "followUpDate": null,
      "nextAction": "Wait for response"
    }
  ],
  "error": null
}

// get_kpis()
{
  "data": [
    { "label": "Total Applications", "value": 0, "change": null, "trend": "neutral", "color": "indigo" },
    { "label": "Active", "value": 0, "change": null, "trend": "neutral", "color": "cyan" },
    { "label": "Interviews", "value": 0, "change": null, "trend": "neutral", "color": "violet" },
    { "label": "Offers", "value": 0, "change": null, "trend": "neutral", "color": "emerald" },
    { "label": "Response Rate", "value": "0%", "change": null, "trend": "neutral", "color": "amber" },
    { "label": "Ghosted", "value": 0, "change": null, "trend": "neutral", "color": "rose" }
  ],
  "error": null
}
```

### DesktopAdapter: pywebview.api vs Local JSON API

**Recommendation: Use `pywebview.api` first (not a local HTTP API).**

Reasons:
1. PyWebView is already the desktop shell — `.api` is the native bridge
2. No need for a second HTTP server (the app already runs one for React assets)
3. `pywebview.api` provides automatic JS↔Python serialization
4. Lower latency than HTTP round-trip
5. Simpler error handling

The `api.py` class would be registered with PyWebView:
```python
import webview
from backend_bridge.api import ExcelBridgeAPI

api = ExcelBridgeAPI(workbook_path)
webview.create_window('JobTracker PRO', url, js_api=api)
```

React calls:
```typescript
// DesktopAdapter.ts
window.pywebview.api.get_applications().then(result => {
  if (result.error) { /* fallback to mock */ }
  else { /* use result.data */ }
})
```

### MockAdapter Fallback Strategy

1. `dataService.ts` tries `DesktopAdapter` first (if `window.pywebview` exists)
2. If `DesktopAdapter` returns an error (file not found, parse error, empty data) → **fall back to MockAdapter**
3. If `window.pywebview` doesn't exist (dev mode without desktop shell) → use `MockAdapter`
4. MockAdapter wraps existing `mockData.ts` — no changes to mock data needed
5. The UI shows a subtle "Demo Data" badge when MockAdapter is active

### Read-Only Safety Guarantees

1. `excel_reader.py` opens with `read_only=True` — openpyxl prevents writes in this mode
2. No `wb.save()` call exists anywhere in `backend_bridge/`
3. `data_mapper.py` only transforms data — no file operations
4. `api.py` only reads — no write methods exposed to React
5. The workbook is closed after each read operation (no persistent handle)
6. A unit test should verify: "attempting to access write methods raises AttributeError"

---

## 12. Known Risks Before Implementation

| Risk | Severity | Mitigation |
|---|---|---|
| **Empty Applications sheet** | Medium | Bridge returns empty array; UI shows empty state; MockAdapter fallback kicks in |
| **Uncached formulas** | High | Python bridge must recompute all formula fields (Total Comp, Net Salary, Days Since Applied, etc.) |
| **Date format inconsistency** | Medium | Normalize all dates to ISO 8601 (`YYYY-MM-DD`) in data_mapper |
| **Status vs Current Stage ambiguity** | Low | Use `Status` column as authoritative; ignore `Current Stage` until clarified |
| **Salary string vs numeric** | Low | Keep as string in Application type; use numeric from Salary Comparison sheet |
| **Benefits Value type mix** | Low | Parse as string in adapter; don't assume numeric |
| **Large workbook performance** | Low | Template has ~1 row per sheet; even 1000 rows would be < 1s with read_only mode |
| **File lock conflict** | Medium | If user has workbook open in Excel, openpyxl read_only should still work. Test this. |
| **PyWebView API async timing** | Medium | `window.pywebview.api` calls are async; React must handle loading states |
