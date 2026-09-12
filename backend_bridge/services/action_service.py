"""Next actions generation service — extracted from api.py.

Generates deterministic, prioritized action items from real Excel application data.
"""
from datetime import datetime, date


def generate_next_actions(applications: list, rows: list, headers: list) -> list:
    """Generate prioritized next actions from application data.

    Args:
        applications: List of mapped application dicts (from data_mapper.map_applications).
        rows: Raw Excel rows (for accessing columns not in the mapped dict).
        headers: Excel column headers.

    Returns:
        List of action dicts: { id, type, priority, title, description,
        applicationId, company, role, dueDate }
    """
    today = date.today()
    actions = []
    seen_keys = set()

    active_statuses = {"Applied", "Phone Screen", "Technical", "Onsite"}

    def get_raw(col_name: str, row: list) -> str:
        try:
            idx = headers.index(col_name)
            val = row[idx] if idx < len(row) else None
            return str(val).strip() if val is not None else ""
        except (ValueError, IndexError):
            return ""

    def parse_date(s):
        if not s:
            return None
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def add_action(key, action):
        if key not in seen_keys:
            actions.append(action)
            seen_keys.add(key)

    for i, app in enumerate(applications):
        row = rows[i] if i < len(rows) else []
        app_id = app.get("id", "")
        company = app.get("company", "")
        role = app.get("role", "")
        status = app.get("status", "")
        follow_up = app.get("followUpDate", "")
        fit_score = app.get("fitScore", 0)
        applied_date = app.get("appliedDate", "")
        salary = app.get("salary", "")
        notes = app.get("notes", "")
        app_url = get_raw("Application URL", row)
        interview_date = get_raw("Interview Date", row)

        fu_date = parse_date(follow_up)
        iv_date = parse_date(interview_date)
        ap_date = parse_date(applied_date)

        # Rule 1: Overdue follow-up
        if status in active_statuses and fu_date and fu_date < today:
            add_action(f"{app_id}-overdue-fu", {
                "id": f"{app_id}-overdue-fu",
                "type": "follow-up",
                "priority": "high",
                "title": f"Follow up with {company}",
                "description": f"Follow-up date was {follow_up} and has passed. Send a polite follow-up message.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": follow_up,
            })

        # Rule 2: Follow-up due today
        elif status in active_statuses and fu_date and fu_date == today:
            add_action(f"{app_id}-today-fu", {
                "id": f"{app_id}-today-fu",
                "type": "follow-up",
                "priority": "high",
                "title": f"Follow up with {company} today",
                "description": f"Follow-up is scheduled for today. Reach out to {company} about the {role} position.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": follow_up,
            })

        # Rule 3: Upcoming interview (within 7 days)
        if iv_date and iv_date >= today and (iv_date - today).days <= 7:
            days_until = (iv_date - today).days
            priority = "high" if days_until <= 2 else "medium"
            add_action(f"{app_id}-upcoming-interview", {
                "id": f"{app_id}-upcoming-interview",
                "type": "prep",
                "priority": priority,
                "title": f"Prepare for {company} interview",
                "description": f"Interview scheduled for {interview_date} ({days_until} day{'s' if days_until != 1 else ''} away). Review technical and behavioral topics.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": interview_date,
            })

        # Rule 4: Interview status but no interview date
        if status in ("Phone Screen", "Technical", "Onsite") and not iv_date:
            add_action(f"{app_id}-missing-iv-date", {
                "id": f"{app_id}-missing-iv-date",
                "type": "follow-up",
                "priority": "medium",
                "title": f"Schedule interview with {company}",
                "description": f"Status is '{status}' but no interview date is set. Contact the recruiter to schedule.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": None,
            })

        # Rule 5: Offer but missing salary or notes
        if status == "Offer" and (not salary or not notes):
            missing = []
            if not salary:
                missing.append("salary")
            if not notes:
                missing.append("notes")
            add_action(f"{app_id}-offer-incomplete", {
                "id": f"{app_id}-offer-incomplete",
                "type": "negotiate",
                "priority": "high",
                "title": f"Update offer details for {company}",
                "description": f"Offer status but missing: {', '.join(missing)}. Record the offer details for negotiation.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": None,
            })

        # Rule 6: Stale active application (14+ days since applied, no response)
        if status == "Applied" and ap_date and (today - ap_date).days >= 14:
            days = (today - ap_date).days
            add_action(f"{app_id}-stale", {
                "id": f"{app_id}-stale",
                "type": "follow-up",
                "priority": "medium",
                "title": f"Check on {company} application",
                "description": f"Applied {days} days ago with no response. Consider sending a follow-up or moving on.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": None,
            })

        # Rule 7: High fit score but still Saved
        if status == "Saved" and fit_score >= 75:
            add_action(f"{app_id}-saved-high-fit", {
                "id": f"{app_id}-saved-high-fit",
                "type": "apply",
                "priority": "medium",
                "title": f"Apply to {company}",
                "description": f"Fit score is {fit_score}/100 but application is still in Saved status. Tailor your resume and apply.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": None,
            })

        # Rule 8: Active application missing URL
        if status in active_statuses and not app_url:
            add_action(f"{app_id}-missing-url", {
                "id": f"{app_id}-missing-url",
                "type": "follow-up",
                "priority": "low",
                "title": f"Add application URL for {company}",
                "description": f"Active application is missing the Application URL. Add it for easy reference.",
                "applicationId": app_id,
                "company": company,
                "role": role,
                "dueDate": None,
            })

    # Sort by priority (high → medium → low), then by dueDate
    priority_order = {"high": 0, "medium": 1, "low": 2}
    actions.sort(key=lambda a: (
        priority_order.get(a.get("priority", "low"), 2),
        a.get("dueDate") or "9999-12-31",
    ))

    # Limit to 10 actions
    return actions[:10]
