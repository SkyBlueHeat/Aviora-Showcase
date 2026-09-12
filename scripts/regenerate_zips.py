"""Regenerate Source and EXE ZIP packages with privacy and integrity checks.

Root cause of previous hang:
  - releases/ directory was NOT excluded from os.walk, so the script tried to
    include its own output ZIP and all old release ZIPs, causing infinite growth.
  - force_zip64=True is not a valid ZipFile constructor parameter in Python 3.13.
  - .zip extension was not excluded, so old release packages were being added.

Fixes:
  - releases/ is now in exclude_dirs
  - .zip extension is now in exclude_exts
  - Output ZIP path is checked with os.path.abspath and skipped if it matches
  - allowZip64=True is used instead of force_zip64
  - Pre-compute file list before creating ZIP
  - Log each file addition
  - Delete incomplete ZIP on error
"""
import os
import sys
import zipfile
import hashlib

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories completely excluded from os.walk
EXCLUDE_DIRS = {
    'node_modules', '__pycache__', '.git', 'build', 'dist', 'backups',
    'exports', 'charts', 'cover_letters', 'linkedin_messages', 'reports',
    'etsy_images', 'etsy_png_images', '_checkpoint_staging', '_dev',
    '.venv', 'venv', 'Product_Delivery_Package', 'releases',
    '.pytest_cache', '.mypy_cache', '.idea', '.vscode',
    'release_packages',
}

# Individual files excluded by name
EXCLUDE_FILES = {
    '.env', 'settings.json', 'interview_scores.json', 'streak_data.json',
}

# Extensions excluded
EXCLUDE_EXTS = {
    '.pyc', '.pyo', '.zip', '.log', '.tmp', '.cache',
    '.egg-info', '.bak',
}

# Max file size to include (500 MB)
MAX_FILE_SIZE = 500 * 1024 * 1024


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _fmt_size(n):
    if n >= 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    elif n >= 1024:
        return f"{n / 1024:.1f} KB"
    return f"{n} B"


# Exact filenames that are forbidden (not substring match)
FORBIDDEN_EXACT_FILES = {
    '.env', 'settings.json', 'interview_scores.json', 'streak_data.json',
}

# .env.example is safe — only block exact .env


def _is_symlink_outside_root(full_path, root_real):
    """Check if file is a symlink pointing outside project root."""
    if not os.path.islink(full_path):
        return False
    try:
        target = os.path.realpath(full_path)
        target_norm = os.path.normcase(target)
        if not target_norm.startswith(root_real):
            return True
    except OSError:
        return True
    return False


def _collect_source_files(out_abspath):
    """Walk the tree and collect files to include, excluding everything unwanted."""
    files = []
    root_real = os.path.normcase(os.path.realpath(root))
    out_real = os.path.normcase(os.path.realpath(out_abspath))

    for dirpath, dirnames, filenames in os.walk(root):
        # Filter directories in-place so os.walk doesn't descend into them
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and not d.lower().endswith('.egg-info')
        ]
        for f in filenames:
            # Exact filename check for forbidden files
            if f in FORBIDDEN_EXACT_FILES:
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in EXCLUDE_EXTS:
                continue
            # Exclude production workbook, keep DEMO/STAGING/TEMPLATE
            if f.endswith('.xlsx'):
                upper = f.upper()
                if '_DEMO' not in upper and '_STAGING' not in upper and '_TEMPLATE' not in upper:
                    continue
            full = os.path.join(dirpath, f)
            full_real = os.path.normcase(os.path.realpath(full))
            # Skip the output ZIP itself (realpath comparison)
            if full_real == out_real:
                continue
            # Skip symlinks pointing outside project root
            if _is_symlink_outside_root(full, root_real):
                print(f"  [WARN] Skipping symlink outside root: {os.path.relpath(full, root)}")
                continue
            # Verify resolved path is still under root
            if not full_real.startswith(root_real):
                print(f"  [WARN] Skipping file outside root: {os.path.relpath(full, root)}")
                continue
            # Skip files larger than MAX_FILE_SIZE
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size > MAX_FILE_SIZE:
                print(f"  [WARN] Skipping large file: {os.path.relpath(full, root)} — {_fmt_size(size)}")
                continue
            arc = os.path.relpath(full, root)
            files.append((full, arc, size))

    # Sort for deterministic ZIP contents
    files.sort(key=lambda item: item[1].lower())
    return files


def make_source_zip():
    out = os.path.join(root, 'releases', 'JobTracker_PRO_Core_MVP_Complete_Source_v2.zip')
    out_abs = os.path.abspath(out)

    # Ensure releases directory exists
    os.makedirs(os.path.join(root, 'releases'), exist_ok=True)

    # Delete existing output ZIP if present
    if os.path.exists(out):
        os.remove(out)
        print(f"  Deleted existing: {os.path.basename(out)}")

    # Collect files first
    print("  Scanning files...")
    files = _collect_source_files(out_abs)

    total_uncompressed = sum(s for _, _, s in files)
    print(f"  Found {len(files)} files, total uncompressed: {_fmt_size(total_uncompressed)}")
    print(f"  Creating ZIP: {os.path.basename(out)}")

    try:
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            for full, arc, size in files:
                print(f"  [ADD] {arc} — {_fmt_size(size)}")
                zf.write(full, arc)
    except Exception as e:
        # Delete incomplete ZIP on error
        if os.path.exists(out):
            os.remove(out)
        print(f"  ERROR during ZIP creation: {e}")
        raise

    return out


def make_exe_zip():
    out = os.path.join(root, 'releases', 'JobTracker_PRO_Core_MVP_Complete_EXE_v2.zip')
    exe = os.path.join(root, 'dist', 'JobTrackerPRO.exe')

    # Ensure releases directory exists
    os.makedirs(os.path.join(root, 'releases'), exist_ok=True)

    # Delete existing output ZIP if present
    if os.path.exists(out):
        os.remove(out)
        print(f"  Deleted existing: {os.path.basename(out)}")

    if not os.path.exists(exe):
        print(f"  ERROR: EXE not found at {exe}")
        print(f"  Run: pyinstaller desktop_shell/app_shell.spec --noconfirm")
        print(f"  Source ZIP is still valid — only EXE ZIP is skipped.")
        return None

    exe_size = os.path.getsize(exe)
    print(f"  [ADD] JobTrackerPRO.exe — {_fmt_size(exe_size)}")

    try:
        with zipfile.ZipFile(out, 'w', compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
            zf.write(exe, 'JobTrackerPRO.exe')
    except Exception as e:
        if os.path.exists(out):
            os.remove(out)
        print(f"  ERROR during ZIP creation: {e}")
        raise

    return out


def verify_zip(zip_path, label):
    """Open ZIP, run testzip(), print stats."""
    print(f"\n  --- Verifying {label} ---")
    if not os.path.exists(zip_path):
        print(f"  {label}: FILE NOT FOUND")
        return False
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Integrity check
            bad = zf.testzip()
            if bad is not None:
                print(f"  {label}: CORRUPT — first bad file: {bad}")
                return False

            names = zf.namelist()
            zip_size = os.path.getsize(zip_path)
            uncompressed = sum(zi.file_size for zi in zf.infolist())

            print(f"  {label}: testzip() OK — no corruption")
            print(f"  {label}: file count: {len(names)}")
            print(f"  {label}: ZIP size: {_fmt_size(zip_size)}")
            print(f"  {label}: uncompressed total: {_fmt_size(uncompressed)}")
            return True
    except Exception as e:
        print(f"  {label}: Error — {e}")
        return False


def check_privacy(zip_path, label):
    with zipfile.ZipFile(zip_path, 'r') as zf:
        names = zf.namelist()
        found = []

        # Check exact filename matches (not substring)
        forbidden_exact = {'.env', 'settings.json', 'interview_scores.json', 'streak_data.json'}
        for n in names:
            basename = n.replace('\\', '/').split('/')[-1]
            if basename in forbidden_exact:
                found.append(f"forbidden file: {n}")
            # .env.example is safe — not blocked

        # Check for .zip extension (should never be in source ZIP)
        zip_files = [n for n in names if n.lower().endswith('.zip')]
        if zip_files:
            found.append(f".zip files: {zip_files[:3]}")

        # Check for .pyc extension
        pyc_files = [n for n in names if n.lower().endswith('.pyc')]
        if pyc_files:
            found.append(f".pyc files: {pyc_files[:3]}")

        # Check for node_modules
        nm = [n for n in names if 'node_modules' in n]
        if nm:
            found.append(f"node_modules: {nm[:3]}")

        # Check for production workbook (not DEMO/STAGING/TEMPLATE)
        prod = [n for n in names
                if 'Developer_Job_Application_Tracker_PRO.xlsx' in n
                and '_DEMO' not in n.upper()
                and '_STAGING' not in n.upper()
                and '_TEMPLATE' not in n.upper()]
        if prod:
            found.append(f"production workbook: {prod[:3]}")

        print(f"  {label}: {len(names)} entries")
        if found:
            print(f"  FORBIDDEN: {found}")
            return False
        else:
            print(f"  Privacy: CLEAN")
            return True


def main():
    print("=== Regenerating ZIP Packages ===\n")

    print("--- Source ZIP ---")
    src_zip = make_source_zip()

    print("\n--- EXE ZIP ---")
    exe_zip = make_exe_zip()

    # SHA256
    print("\n=== SHA256 ===")
    src_hash = sha256(src_zip)
    print(f"  Source ZIP SHA256: {src_hash}")
    if exe_zip:
        exe_hash = sha256(exe_zip)
        print(f"  EXE ZIP SHA256: {exe_hash}")

    # Privacy
    print("\n=== Privacy Check ===")
    src_ok = check_privacy(src_zip, "Source ZIP")
    exe_ok = check_privacy(exe_zip, "EXE ZIP") if exe_zip else False

    # Integrity + stats
    print("\n=== Integrity & Stats ===")
    src_integrity = verify_zip(src_zip, "Source ZIP")
    exe_integrity = verify_zip(exe_zip, "EXE ZIP") if exe_zip else False

    # Final result
    print(f"\n{'=' * 60}")
    # EXE ZIP is optional — if EXE wasn't built, only Source ZIP matters
    if exe_zip is None:
        all_ok = src_ok and src_integrity
        if all_ok:
            print("RESULT: SOURCE ZIP PASSED (EXE ZIP skipped — no EXE built)")
            sys.exit(0)
        else:
            print("RESULT: SOURCE ZIP FAILED — SEE ABOVE")
            sys.exit(1)
    else:
        all_ok = src_ok and exe_ok and src_integrity and exe_integrity
        if all_ok:
            print("RESULT: ALL CHECKS PASSED")
            sys.exit(0)
        else:
            print("RESULT: SOME CHECKS FAILED — SEE ABOVE")
            sys.exit(1)


if __name__ == "__main__":
    main()
