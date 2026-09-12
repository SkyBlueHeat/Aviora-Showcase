"""
Job Search Goals & Streak Tracker
Developer Job Application Tracker PRO - CreatorDockStudio

Tracks daily/weekly application goals, maintains streaks,
and provides motivational feedback. Data saved to JSON.
"""

import json
import os
import threading
from datetime import datetime, date, timedelta

DATA_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(DATA_DIR, "streak_data.json")
# KNOWN LIMITATION: threading.Lock only protects single-process concurrent writes.
# Two application instances writing to the same JSON file can still cause data loss.
# This risk will be addressed in Checkpoint 4 with process-level file locking or
# single-instance enforcement. For now, "concurrent writes solved" means
# "single-process concurrent writes solved" only.
_save_lock = threading.Lock()

MOTIVATIONAL_MESSAGES = {
    "new":        "Every expert was once a beginner. Start today!",
    "day_1":      "First step taken! The hardest part is starting.",
    "day_3":      "3 days strong! You're building momentum.",
    "day_7":      "One week streak! You're in the top 10% of job seekers.",
    "day_14":     "Two weeks! Consistency is your superpower.",
    "day_21":     "21 days — habits are forming. Keep going!",
    "day_30":     "30-day streak! You're unstoppable.",
    "day_60":     "60 days! You're a job search machine.",
    "day_100":    "100 DAYS! Legendary dedication.",
    "goal_hit":   "Goal reached today! Outstanding work.",
    "goal_miss":  "Missed today's goal — tomorrow is a fresh start!",
    "streak_broken": "Streak broken, but your progress is still real. Reset and go!",
}

WEEKLY_TIPS = [
    "Apply on Tuesday–Thursday — response rates are highest mid-week.",
    "Personalize each cover letter. Generic ones get deleted first.",
    "Follow up 5-7 days after applying with a LinkedIn message.",
    "Quality > quantity. 5 tailored apps beat 20 generic ones.",
    "Update your LinkedIn 'Open to Work' settings — recruiters search daily.",
    "Ask for referrals before applying — it multiplies your chances 9x.",
    "Prep 3 STAR stories this week for behavioral interviews.",
]


def _load() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "daily_goal":   5,
        "weekly_goal":  20,
        "entries":      {},
        "streak":       0,
        "best_streak":  0,
        "last_date":    None,
        "total_apps":   0,
    }


def _save(data: dict):
    with _save_lock:
        import tempfile
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=os.path.dirname(DATA_FILE), suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, DATA_FILE)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise


def _parse_iso_day(text: str):
    try:
        return date.fromisoformat(text)
    except Exception:
        return None


def _calculate_current_streak(entries: dict, daily_goal: int, today: date | None = None) -> int:
    if daily_goal <= 0:
        return 0
    today = today or date.today()
    streak = 0
    cursor = today
    while True:
        day_key = cursor.isoformat()
        count = entries.get(day_key, {}).get("count", 0)
        if count >= daily_goal:
            streak += 1
            cursor -= timedelta(days=1)
            continue
        break
    return streak


def _calculate_best_streak(entries: dict, daily_goal: int) -> int:
    if daily_goal <= 0 or not entries:
        return 0
    valid_days = sorted(d for d in (_parse_iso_day(k) for k in entries.keys()) if d is not None)
    best = 0
    current = 0
    prev_day = None
    for day_obj in valid_days:
        count = entries.get(day_obj.isoformat(), {}).get("count", 0)
        if count >= daily_goal:
            if prev_day and (day_obj - prev_day).days == 1:
                current += 1
            else:
                current = 1
            best = max(best, current)
            prev_day = day_obj
        else:
            current = 0
            prev_day = None
    return best


def _refresh_streak_stats(data: dict):
    entries = data.get("entries", {})
    daily_goal = int(data.get("daily_goal", 5) or 5)
    data["total_apps"] = sum((entry or {}).get("count", 0) for entry in entries.values())
    data["streak"] = _calculate_current_streak(entries, daily_goal)
    data["best_streak"] = _calculate_best_streak(entries, daily_goal)
    data["last_date"] = max(entries.keys(), default=None)


def get_data() -> dict:
    return _load()


def set_goals(daily: int, weekly: int):
    data = _load()
    data["daily_goal"]  = daily
    data["weekly_goal"] = weekly
    _refresh_streak_stats(data)
    _save(data)


def log_applications(count: int, note: str = "") -> dict:
    data  = _load()
    today = date.today().isoformat()

    if count <= 0:
        raise ValueError("Application count must be greater than zero.")

    prev  = data["entries"].get(today, {})
    new_total = prev.get("count", 0) + count
    data["entries"][today] = {
        "count": new_total,
        "note":  note or prev.get("note", ""),
        "ts":    datetime.now().isoformat(),
    }
    _refresh_streak_stats(data)
    _save(data)

    goal_hit = new_total >= data["daily_goal"]
    return {
        "today_count": new_total,
        "goal_hit":    goal_hit,
        "streak":      data["streak"],
        "best_streak": data["best_streak"],
        "total_apps":  data["total_apps"],
        "message":     _get_message(data["streak"], goal_hit),
    }


def _get_message(streak: int, goal_hit: bool) -> str:
    if goal_hit:
        for days in [100, 60, 30, 21, 14, 7, 3, 1]:
            if streak >= days:
                key = f"day_{days}"
                if key in MOTIVATIONAL_MESSAGES:
                    return MOTIVATIONAL_MESSAGES[key]
        return MOTIVATIONAL_MESSAGES["goal_hit"]
    return MOTIVATIONAL_MESSAGES["goal_miss"]


def get_weekly_summary() -> dict:
    data  = _load()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_days  = [(week_start + timedelta(days=i)).isoformat() for i in range(7)]
    week_entries = {d: data["entries"].get(d, {"count": 0}) for d in week_days}
    week_total = sum(e["count"] for e in week_entries.values())
    daily_goal = data.get("daily_goal", 5)
    weekly_goal = data.get("weekly_goal", 20)
    days_with_apps = sum(1 for e in week_entries.values() if e["count"] > 0)
    days_hit_goal  = sum(1 for e in week_entries.values() if e["count"] >= daily_goal)
    tip_idx = today.weekday() % len(WEEKLY_TIPS)
    return {
        "week_total":    week_total,
        "weekly_goal":   weekly_goal,
        "daily_goal":    daily_goal,
        "pct":           min(int(week_total / weekly_goal * 100), 100) if weekly_goal else 0,
        "days_active":   days_with_apps,
        "days_hit_goal": days_hit_goal,
        "entries":       week_entries,
        "week_days":     week_days,
        "streak":        data.get("streak", 0),
        "best_streak":   data.get("best_streak", 0),
        "total_apps":    data.get("total_apps", 0),
        "tip":           WEEKLY_TIPS[tip_idx],
    }


def get_all_time_stats() -> dict:
    data = _load()
    entries = data.get("entries", {})
    if not entries:
        return {"total_apps": 0, "active_days": 0, "best_day": 0, "avg_per_day": 0.0}
    counts = [e["count"] for e in entries.values()]
    return {
        "total_apps":  data.get("total_apps", 0),
        "active_days": len(entries),
        "best_day":    max(counts),
        "avg_per_day": round(sum(counts) / len(counts), 1),
        "streak":      data.get("streak", 0),
        "best_streak": data.get("best_streak", 0),
    }
