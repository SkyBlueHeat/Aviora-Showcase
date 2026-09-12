"""Streak computation service — extracted from api.py.

Computes daily/weekly counts and streaks from Excel application dates.
Falls back to streak_data.json when Excel is unavailable.
"""
import os
import json
from datetime import datetime, date, timedelta


def compute_streak_data(
    app_dates: list,
    daily_goal: int = 5,
    weekly_goal: int = 20,
    streak_json_path: str = None,
) -> dict:
    """Compute streak data from a list of application dates.

    Args:
        app_dates: List of date objects (from Excel Date Applied column).
        daily_goal: Daily application goal.
        weekly_goal: Weekly application goal.
        streak_json_path: Path to streak_data.json for fallback.

    Returns:
        { todayCount, weekCount, dailyGoal, weeklyGoal, currentStreak,
          longestStreak, lastActiveDate }
    """
    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Monday

    if app_dates:
        today_count = sum(1 for d in app_dates if d == today)
        week_count = sum(1 for d in app_dates if week_start <= d <= today)
        last_active = max((d for d in app_dates if d <= today), default=None)

        # Compute streak from app_dates
        date_counts = {}
        for d in app_dates:
            if d <= today:
                date_counts[d] = date_counts.get(d, 0) + 1

        # Current streak: count consecutive days (ending today or yesterday) meeting daily_goal
        current_streak = 0
        cursor = today
        # Allow today to not yet have applications (streak continues from yesterday)
        if today not in date_counts or date_counts[today] < daily_goal:
            cursor = today - timedelta(days=1)
        while cursor in date_counts and date_counts[cursor] >= daily_goal:
            current_streak += 1
            cursor -= timedelta(days=1)

        # Longest streak
        sorted_dates = sorted(date_counts.keys())
        longest = 0
        run = 0
        prev = None
        for d in sorted_dates:
            if date_counts[d] >= daily_goal:
                if prev and (d - prev).days == 1:
                    run += 1
                else:
                    run = 1
                longest = max(longest, run)
                prev = d
            else:
                run = 0
                prev = None
    else:
        # Fall back to streak_data.json
        if streak_json_path and os.path.exists(streak_json_path):
            try:
                with open(streak_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries = data.get("entries", {})
                today_str = today.isoformat()
                today_count = entries.get(today_str, {}).get("count", 0)
                week_count = sum(
                    entries.get((week_start + timedelta(days=i)).isoformat(), {}).get("count", 0)
                    for i in range(7)
                )
                current_streak = data.get("streak", 0)
                longest = data.get("best_streak", 0)
                last_active_str = data.get("last_date")
                last_active = datetime.strptime(last_active_str, "%Y-%m-%d").date() if last_active_str else None
            except Exception:
                today_count = 0
                week_count = 0
                current_streak = 0
                longest = 0
                last_active = None
        else:
            today_count = 0
            week_count = 0
            current_streak = 0
            longest = 0
            last_active = None

    last_active_str = last_active.isoformat() if last_active else None

    return {
        "todayCount": today_count,
        "weekCount": week_count,
        "dailyGoal": daily_goal,
        "weeklyGoal": weekly_goal,
        "currentStreak": current_streak,
        "longestStreak": longest,
        "lastActiveDate": last_active_str,
    }


def extract_app_dates(headers: list, rows: list) -> list:
    """Extract date objects from the Date Applied column of Excel data.

    Handles datetime, date, and string formats.
    """
    app_dates = []
    try:
        idx = headers.index("Date Applied")
    except ValueError:
        return app_dates

    for row in rows:
        val = row[idx] if idx < len(row) else None
        if val is None:
            continue
        if isinstance(val, (datetime, date)):
            app_dates.append(val.date() if isinstance(val, datetime) else val)
        else:
            s = str(val).strip()
            if not s:
                continue
            for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%Y/%m/%d"):
                try:
                    app_dates.append(datetime.strptime(s, fmt).date())
                    break
                except ValueError:
                    continue

    return app_dates
