"""
Settings Manager
Developer Job Application Tracker PRO v3.0 — CreatorDockStudio

Handles persistent user configuration saved to settings.json.
All launcher tabs read from this on startup.
"""

import json
import os
import threading
from datetime import datetime

# KNOWN LIMITATION: threading.Lock only protects single-process concurrent writes.
# Two application instances writing to the same settings.json can still cause data loss.
# This risk will be addressed in Checkpoint 4 with process-level file locking or
# single-instance enforcement.
_save_lock = threading.Lock()

DATA_DIR     = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")

DEFAULTS = {
    # ── Profile ──────────────────────────────────────────────────────────────
    "profile": {
        "full_name":       "",
        "current_role":    "",
        "years_exp":       "3",
        "field":           "software development",
        "target_companies":"",
        "linkedin_url":    "",
        "job_status":      "Actively Looking",
    },

    # ── Job Search Goals ─────────────────────────────────────────────────────
    "goals": {
        "daily_apps":      5,
        "weekly_apps":     20,
        "target_salary":   "",
        "preferred_location": "Remote",
        "job_types":       "Full-time",
    },

    # ── Appearance ───────────────────────────────────────────────────────────
    "appearance": {
        "theme":           "dark_navy",
        "font_size":       "medium",
        "sidebar_width":   220,
        "accent_color":    "#7C83FD",
        "show_tips":       True,
    },

    # ── Interview Prep ────────────────────────────────────────────────────────
    "interview": {
        "default_category":    "Behavioral (STAR)",
        "auto_start_timer":    True,
        "min_word_warning":    50,
        "show_follow_ups":     True,
        "show_tips":           True,
        "save_history":        True,
    },

    # ── Files & Backup ───────────────────────────────────────────────────────
    "files": {
        "tracker_path":    "",
        "backup_enabled":  True,
        "backup_folder":   "",
        "backup_on_exit":  False,
        "max_backups":     10,
    },

    # ── Notifications ─────────────────────────────────────────────────────────
    "notifications": {
        "followup_days":       5,
        "streak_warning":      True,
        "email_reminder":      False,
        "reminder_time":       "09:00",
    },

    # ── Language & Tech Stack ─────────────────────────────────────────────────
    "language": {
        "app_language":       "English",
        "primary_language":   "Python",
        "secondary_languages": [],
        "frameworks":         [],
        "databases":          [],
        "cloud":              [],
    },

    # ── API & Integrations ────────────────────────────────────────────────────
    "api": {
        "openai_key":          "",
        "notion_token":        "",
        "notion_database_id":  "",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base recursively, keeping all base keys."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def load() -> dict:
    """Load settings, filling missing keys from DEFAULTS."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return _deep_merge(DEFAULTS, saved)
        except Exception:
            pass
    return _deep_merge(DEFAULTS, {})


def save(cfg: dict):
    """Persist settings to disk using atomic write (temp file + os.replace)."""
    with _save_lock:
        tmp_path = SETTINGS_FILE + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, SETTINGS_FILE)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise


def get(section: str, key: str, fallback=None):
    """Quick accessor: get a single value."""
    cfg = load()
    return cfg.get(section, {}).get(key, fallback)


def set_value(section: str, key: str, value):
    """Quick setter: update a single value and save atomically."""
    with _save_lock:
        cfg = load()
        if section not in cfg:
            cfg[section] = {}
        cfg[section][key] = value
        tmp_path = SETTINGS_FILE + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, SETTINGS_FILE)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            raise


def reset():
    """Reset all settings to defaults."""
    save(DEFAULTS)


# ── Convenience accessors used by other tabs ──────────────────────────────────

def get_profile_name() -> str:
    return get("profile", "full_name", "")

def get_profile_role() -> str:
    return get("profile", "current_role", "")

def get_profile_field() -> str:
    return get("profile", "field", "software development")

def get_profile_years() -> str:
    return get("profile", "years_exp", "3")

def get_daily_goal() -> int:
    return int(get("goals", "daily_apps", 5))

def get_weekly_goal() -> int:
    return int(get("goals", "weekly_apps", 20))

def get_openai_key() -> str:
    return get("api", "openai_key", "")

def get_notion_token() -> str:
    return get("api", "notion_token", "")

def get_notion_db() -> str:
    return get("api", "notion_database_id", "")

def get_tracker_path() -> str:
    stored = get("files", "tracker_path", "")
    if stored and os.path.exists(stored):
        return stored
    return ""

def get_interview_category() -> str:
    return get("interview", "default_category", "Behavioral (STAR)")

def get_auto_timer() -> bool:
    return bool(get("interview", "auto_start_timer", True))

def get_show_follow_ups() -> bool:
    return bool(get("interview", "show_follow_ups", True))

def get_primary_language() -> str:
    return get("language", "primary_language", "Python")

def get_app_language() -> str:
    return get("language", "app_language", "English")

# ── Language / Tech options ────────────────────────────────────────────────────

PROGRAMMING_LANGUAGES = [
    "Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "C",
    "Go", "Rust", "Kotlin", "Swift", "Ruby", "PHP", "Scala", "R",
    "Dart", "Elixir", "Haskell", "Lua", "Perl", "Shell / Bash",
    "SQL", "HTML/CSS", "MATLAB", "Julia",
]

FRAMEWORKS = [
    "React", "Next.js", "Vue.js", "Nuxt.js", "Angular", "Svelte",
    "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
    "ASP.NET Core", "Rails", "Laravel", "NestJS", "GraphQL",
    "React Native", "Flutter", "SwiftUI", "Jetpack Compose",
    "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy",
]

DATABASES = [
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch",
    "DynamoDB", "Cassandra", "Firebase", "Supabase", "MS SQL Server",
    "Oracle", "Neo4j", "ClickHouse", "CockroachDB",
]

CLOUD_PLATFORMS = [
    "AWS", "Google Cloud (GCP)", "Microsoft Azure", "Vercel", "Netlify",
    "Heroku", "DigitalOcean", "Cloudflare", "Docker", "Kubernetes",
    "Terraform", "GitHub Actions", "GitLab CI", "Jenkins", "CircleCI",
]

APP_LANGUAGES = [
    "English",
    "Turkish",
    "German",
    "French",
    "Spanish",
    "Portuguese",
    "Arabic",
    "Japanese",
    "Korean",
    "Chinese (Simplified)",
]
