"""Data mapper — transforms raw Excel rows into clean typed dicts for React.
Handles None values, date normalization, status mapping, and formula recomputation.
"""
from datetime import datetime, date
from typing import Any


def _safe_str(val: Any) -> str:
    """Convert a value to string, handling None."""
    if val is None:
        return ""
    return str(val).strip()


def _safe_int(val: Any) -> int:
    """Convert a value to int, handling None/strings."""
    if val is None:
        return 0
    try:
        return int(val)
    except (ValueError, TypeError):
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return 0


def _safe_float(val: Any) -> float:
    """Convert a value to float, handling None/strings."""
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def _normalize_date(val: Any) -> str:
    """Normalize date values to ISO string (YYYY-MM-DD)."""
    if val is None:
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    # Try common date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return s


def _normalize_status(val: Any) -> str:
    """Normalize status values to known pipeline columns."""
    s = _safe_str(val)
    if not s:
        return "Saved"
    # Exact match check
    if s in {"Saved", "Applied", "Phone Screen", "Technical",
             "Onsite", "Offer", "Rejected", "Ghosted"}:
        return s
    # Case-insensitive fallback
    s_lower = s.lower()
    mapping = {
        "saved": "Saved",
        "applied": "Applied",
        "phone screen": "Phone Screen",
        "phone": "Phone Screen",
        "technical": "Technical",
        "tech": "Technical",
        "onsite": "Onsite",
        "on-site": "Onsite",
        "on site": "Onsite",
        "offer": "Offer",
        "rejected": "Rejected",
        "reject": "Rejected",
        "ghosted": "Ghosted",
        "ghost": "Ghosted",
    }
    return mapping.get(s_lower, "Applied")


def _normalize_remote(val: Any) -> str:
    """Map Remote column values to WorkType enum."""
    s = _safe_str(val).lower()
    if s in ("yes", "remote", "true", "1"):
        return "Remote"
    if s in ("hybrid",):
        return "Hybrid"
    if s in ("no", "on-site", "onsite", "false", "0", ""):
        return "On-site"
    return "On-site"


def _normalize_priority(val: Any) -> str:
    """Normalize priority values."""
    s = _safe_str(val)
    if s in ("Critical", "High", "Medium", "Low"):
        return s
    s_lower = s.lower()
    if "critical" in s_lower or "urgent" in s_lower:
        return "Critical"
    if "high" in s_lower:
        return "High"
    if "medium" in s_lower or "normal" in s_lower:
        return "Medium"
    return "Low"


def _compute_next_action(status: str, follow_up_date: str, priority: str) -> str:
    """Derive a next action from status + follow-up date + priority."""
    if status == "Offer":
        return "Negotiate and respond to offer"
    if status == "Rejected":
        return "Move on — practice areas for improvement"
    if status == "Ghosted":
        return "Follow up or move on"
    if follow_up_date:
        return f"Follow up on {follow_up_date}"
    if status == "Saved":
        return "Tailor resume and apply"
    if status == "Applied":
        return "Wait for response"
    if status in ("Phone Screen", "Technical", "Onsite"):
        return "Prepare for interview"
    return "Review application"


def _days_since(date_str: str) -> int | None:
    """Compute days since a date string. Returns None if invalid."""
    if not date_str:
        return None
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except (ValueError, TypeError):
        return None


def map_application(headers: list, row: list) -> dict:
    """Map an Applications sheet row to a React-compatible Application dict."""
    def get(col_name: str) -> Any:
        try:
            idx = headers.index(col_name)
            return row[idx] if idx < len(row) else None
        except ValueError:
            return None

    status = _normalize_status(get("Status"))
    applied_date = _normalize_date(get("Date Applied"))
    follow_up = _normalize_date(get("Follow-up Date"))
    priority = _normalize_priority(get("Priority"))

    return {
        "id": _safe_str(get("Application ID")) or f"row-{id(row)}",
        "company": _safe_str(get("Company")),
        "role": _safe_str(get("Role")),
        "status": status,
        "priority": priority,
        "workType": _normalize_remote(get("Remote")),
        "location": _safe_str(get("Location")),
        "appliedDate": applied_date,
        "salary": _safe_str(get("Salary")),
        "fitScore": _safe_int(get("Fit Score")),
        "qualityScore": 0,  # Not in Excel — mock/computed field
        "source": _safe_str(get("Source")),
        "techStack": [],  # Not in Applications sheet — mock fallback
        "notes": _safe_str(get("Notes")),
        "followUpDate": follow_up or None,
        "nextAction": _compute_next_action(status, follow_up, priority),
    }


def map_applications(headers: list, rows: list) -> list:
    """Map all application rows. Returns empty list if no data."""
    if not headers or not rows:
        return []
    return [map_application(headers, row) for row in rows]


def compute_kpis(applications: list) -> list:
    """Compute dashboard KPIs from applications list."""
    total = len(applications)
    active = sum(1 for a in applications if a["status"] not in ("Rejected", "Ghosted"))
    interviews = sum(1 for a in applications if a["status"] in ("Phone Screen", "Technical", "Onsite"))
    offers = sum(1 for a in applications if a["status"] == "Offer")
    ghosted = sum(1 for a in applications if a["status"] == "Ghosted")
    response_rate = 0
    if total > 0:
        responded = sum(1 for a in applications if a["status"] not in ("Saved", "Applied", "Ghosted"))
        response_rate = round((responded / total) * 100)

    return [
        {"label": "Total Applications", "value": total, "change": None, "trend": "neutral", "color": "indigo"},
        {"label": "Active", "value": active, "change": None, "trend": "neutral", "color": "cyan"},
        {"label": "Interviews", "value": interviews, "change": None, "trend": "neutral", "color": "violet"},
        {"label": "Offers", "value": offers, "change": None, "trend": "neutral", "color": "emerald"},
        {"label": "Response Rate", "value": f"{response_rate}%", "change": None, "trend": "neutral", "color": "amber"},
        {"label": "Ghosted", "value": ghosted, "change": None, "trend": "neutral", "color": "rose"},
    ]


def compute_pipeline(applications: list) -> list:
    """Compute pipeline column counts from applications."""
    columns = ["Saved", "Applied", "Phone Screen", "Technical", "Onsite", "Offer", "Rejected", "Ghosted"]
    return [
        {"status": col, "count": sum(1 for a in applications if a["status"] == col)}
        for col in columns
    ]


def compute_monthly_chart(applications: list) -> list:
    """Compute monthly activity chart data from applications."""
    months = {}
    for app in applications:
        d = app.get("appliedDate", "")
        if d and len(d) >= 7:
            month_key = d[:7]  # YYYY-MM
            if month_key not in months:
                months[month_key] = {"month": month_key, "applications": 0, "interviews": 0, "offers": 0}
            months[month_key]["applications"] += 1
            if app["status"] in ("Phone Screen", "Technical", "Onsite"):
                months[month_key]["interviews"] += 1
            if app["status"] == "Offer":
                months[month_key]["offers"] += 1
    return sorted(months.values(), key=lambda m: m["month"])


def compute_source_chart(applications: list) -> list:
    """Compute source distribution chart data from applications."""
    sources = {}
    for app in applications:
        src = app.get("source", "Unknown") or "Unknown"
        if src not in sources:
            sources[src] = {"source": src, "count": 0}
        sources[src]["count"] += 1
    return list(sources.values())


def map_salary_entry(headers: list, row: list) -> dict:
    """Map a Salary Comparison row to a salary dict."""
    def get(col_name: str) -> Any:
        try:
            idx = headers.index(col_name)
            return row[idx] if idx < len(row) else None
        except ValueError:
            return None

    base = _safe_int(get("Base Salary"))
    bonus = _safe_int(get("Bonus"))
    equity = _safe_int(get("Equity"))
    benefits = _safe_int(get("Benefits Value"))
    signing = _safe_int(get("Signing Bonus"))

    # Recompute formula fields (Excel formulas may not be cached)
    annual_comp = base + bonus + equity
    monthly_income = round(annual_comp / 12) if annual_comp else 0
    total_comp = annual_comp + benefits + signing
    estimated_tax = round(total_comp * 0.25) if total_comp else 0
    net_salary = total_comp - estimated_tax

    bonus_pct = round((bonus / base) * 100) if base else 0

    return {
        "company": _safe_str(get("Company")),
        "baseSalary": base,
        "bonusPct": bonus_pct,
        "bonusAbsolute": bonus,
        "equity": equity,
        "signingBonus": signing,
        "benefits": benefits,
        "benefitsDescription": _safe_str(get("Benefits Value")),
        "totalComp": total_comp,
        "netAnnual": net_salary,
        "netMonthly": round(net_salary / 12) if net_salary else 0,
        "taxBracket": "25%",
        "estimatedTax": estimated_tax,
    }


def map_salary_data(headers: list, rows: list) -> list:
    """Map all salary comparison rows."""
    if not headers or not rows:
        return []
    return [map_salary_entry(headers, row) for row in rows]


def map_interview_history(headers: list, rows: list) -> list:
    """Map Interview Tracker rows to interview history dicts."""
    if not headers or not rows:
        return []

    def get(row, col_name):
        try:
            idx = headers.index(col_name)
            return row[idx] if idx < len(row) else None
        except ValueError:
            return None

    result = []
    for row in rows:
        result.append({
            "company": _safe_str(get(row, "Company")),
            "role": _safe_str(get(row, "Role")),
            "stage": _safe_str(get(row, "Interview Stage")),
            "interviewer": _safe_str(get(row, "Interviewer")),
            "date": _normalize_date(get(row, "Interview Date")),
            "duration": _safe_int(get(row, "Duration (min)")),
            "preparationStatus": _safe_str(get(row, "Preparation Status")),
            "difficulty": _safe_str(get(row, "Difficulty")),
            "result": _safe_str(get(row, "Result")),
            "notes": _safe_str(get(row, "Notes")),
        })
    return result


def map_cover_letter_history(headers: list, rows: list) -> list:
    """Map Cover Letter Tracker rows to cover letter history dicts."""
    if not headers or not rows:
        return []

    def get(row, col_name):
        try:
            idx = headers.index(col_name)
            return row[idx] if idx < len(row) else None
        except ValueError:
            return None

    result = []
    for row in rows:
        result.append({
            "company": _safe_str(get(row, "Company")),
            "role": _safe_str(get(row, "Role")),
            "version": _safe_str(get(row, "Version")),
            "dateCreated": _normalize_date(get(row, "Date Created")),
            "dateSent": _normalize_date(get(row, "Date Sent")),
            "templateUsed": _safe_str(get(row, "Template Used")),
            "responseReceived": _safe_str(get(row, "Response Received")),
            "interviewScheduled": _safe_str(get(row, "Interview Scheduled")),
            "notes": _safe_str(get(row, "Notes")),
        })
    return result
