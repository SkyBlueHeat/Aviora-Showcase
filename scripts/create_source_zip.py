"""Create a source checkpoint ZIP for the Core MVP release.

Excludes build artifacts, runtime data, and user-generated outputs.
Includes source code, tests, documentation, and config files only.
"""
import os
import zipfile
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EXCLUDE_DIRS = {
    "node_modules", "__pycache__", "build", "dist", ".git",
    "backups", "exports", "reports", "cover_letters", "linkedin_messages",
    "charts", "etsy_images", "etsy_png_images", "notion_templates",
    "_checkpoint_staging", "_dev", ".vite",
}

EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".zip", ".log"}

EXCLUDE_FILES = {
    "interview_scores.json", "streak_data.json", "settings.json",
    "Developer_Job_Application_Tracker_PRO.xlsx",
    "Developer_Job_Application_Tracker_PRO_v3.xlsx",
    "package-lock.json",
    "tsconfig.tsbuildinfo",
}

KEEP_XLSX_PATTERNS = ["_DEMO", "_STAGING", "test_fixture"]


def should_exclude(path: str, name: str) -> bool:
    full = os.path.join(path, name)
    if name in EXCLUDE_DIRS:
        return True
    if name in EXCLUDE_FILES:
        return True
    _, ext = os.path.splitext(name)
    if ext.lower() in EXCLUDE_EXTENSIONS:
        return True
    if ext.lower() == ".xlsx":
        if not any(p in name for p in KEEP_XLSX_PATTERNS):
            return True
    return False


def main():
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"JobTrackerPRO_CoreMVP_Source_{ts}.zip"
    zip_path = os.path.join(PROJECT_ROOT, "releases", zip_name)

    os.makedirs(os.path.dirname(zip_path), exist_ok=True)

    file_count = 0
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Filter dirs in-place to prevent descent
            dirs[:] = [d for d in dirs if not should_exclude(root, d)]
            for f in files:
                if should_exclude(root, f):
                    continue
                full = os.path.join(root, f)
                arc = os.path.relpath(full, PROJECT_ROOT)
                zf.write(full, arc)
                file_count += 1

    size = os.path.getsize(zip_path)
    print(f"Source ZIP created: releases/{zip_name}")
    print(f"  Files: {file_count}")
    print(f"  Size:  {size:,} bytes ({size / 1024 / 1024:.1f} MB)")


if __name__ == "__main__":
    main()
