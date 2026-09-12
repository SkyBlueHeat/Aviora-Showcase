"""Excel backup helper for JobTracker PRO.

Creates timestamped backup copies of the workbook before any future write operation.
This module only copies files — it never opens, modifies, or saves the workbook itself.

Safety guarantees:
- Source workbook is never opened or modified
- Backup is a byte-level copy via shutil.copy2
- Backup filename includes timestamp with microseconds for uniqueness
- Collision check with incrementing suffix ensures no backup is ever overwritten
- Result is JSON-safe for PyWebView API consumption
"""
import os
import shutil
from datetime import datetime
from typing import Optional


class ExcelBackup:
    """Safe backup helper — copies workbook files without modifying them."""

    def __init__(self, workbook_path: str, backup_dir: str = "backups"):
        """
        Args:
            workbook_path: Absolute or relative path to the workbook file.
            backup_dir: Directory for backup files. Created if it doesn't exist.
                        Defaults to 'backups' relative to the workbook's parent dir.
        """
        self.workbook_path = workbook_path
        # Resolve backup_dir relative to workbook's parent if not absolute
        if os.path.isabs(backup_dir):
            self.backup_dir = backup_dir
        else:
            workbook_parent = os.path.dirname(os.path.abspath(workbook_path))
            self.backup_dir = os.path.join(workbook_parent, backup_dir)

    def create_backup(self) -> dict:
        """Create a timestamped backup copy of the workbook.

        Returns:
            dict with keys:
                success (bool): Whether the backup was created.
                backupPath (str|None): Path to the backup file if successful.
                error (str|None): Error message if failed.
        """
        # Check source workbook exists
        if not os.path.exists(self.workbook_path):
            return {
                "success": False,
                "backupPath": None,
                "error": f"Workbook not found: {self.workbook_path}",
            }

        # Create backup directory if it doesn't exist
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except OSError as e:
            return {
                "success": False,
                "backupPath": None,
                "error": f"Cannot create backup directory: {e}",
            }

        # Generate timestamped filename with microseconds for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        workbook_name = os.path.basename(self.workbook_path)
        name_without_ext = os.path.splitext(workbook_name)[0]
        backup_filename = f"{name_without_ext}_backup_{timestamp}.xlsx"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        # Collision check: if file already exists (extremely unlikely with microseconds),
        # append incrementing suffix until we find a unique filename
        if os.path.exists(backup_path):
            counter = 1
            while os.path.exists(backup_path):
                backup_filename = f"{name_without_ext}_backup_{timestamp}_{counter:03d}.xlsx"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                counter += 1

        # Copy the file (byte-level, preserves metadata via shutil.copy2)
        try:
            shutil.copy2(self.workbook_path, backup_path)
        except (OSError, shutil.Error) as e:
            return {
                "success": False,
                "backupPath": None,
                "error": f"Backup copy failed: {e}",
            }

        # Verify backup file exists and has non-zero size
        if not os.path.exists(backup_path):
            return {
                "success": False,
                "backupPath": None,
                "error": "Backup file not found after copy",
            }

        source_size = os.path.getsize(self.workbook_path)
        backup_size = os.path.getsize(backup_path)
        if backup_size == 0:
            return {
                "success": False,
                "backupPath": None,
                "error": "Backup file is empty (0 bytes)",
            }

        return {
            "success": True,
            "backupPath": backup_path,
            "error": None,
        }

    def create_session_backup(self) -> dict:
        """Create a session safety backup with a distinct _session_backup_ suffix.

        This is an additional full backup created before the first production write
        of a session. It is separate from the normal per-write backup.

        Returns:
            dict with keys: success, backupPath, error
        """
        if not os.path.exists(self.workbook_path):
            return {
                "success": False,
                "backupPath": None,
                "error": f"Workbook not found: {self.workbook_path}",
            }

        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except OSError as e:
            return {
                "success": False,
                "backupPath": None,
                "error": f"Cannot create backup directory: {e}",
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        workbook_name = os.path.basename(self.workbook_path)
        name_without_ext = os.path.splitext(workbook_name)[0]
        backup_filename = f"{name_without_ext}_session_backup_{timestamp}.xlsx"
        backup_path = os.path.join(self.backup_dir, backup_filename)

        if os.path.exists(backup_path):
            counter = 1
            while os.path.exists(backup_path):
                backup_filename = f"{name_without_ext}_session_backup_{timestamp}_{counter:03d}.xlsx"
                backup_path = os.path.join(self.backup_dir, backup_filename)
                counter += 1

        try:
            shutil.copy2(self.workbook_path, backup_path)
        except (OSError, shutil.Error) as e:
            return {
                "success": False,
                "backupPath": None,
                "error": f"Session backup copy failed: {e}",
            }

        if not os.path.exists(backup_path) or os.path.getsize(backup_path) == 0:
            return {
                "success": False,
                "backupPath": None,
                "error": "Session backup file missing or empty after copy",
            }

        return {
            "success": True,
            "backupPath": backup_path,
            "error": None,
        }

    def list_backups(self) -> dict:
        """List existing backup files in the backup directory.

        Returns:
            dict with keys:
                success (bool): Whether listing succeeded.
                backups (list[dict]): List of {filename, path, sizeBytes, modified}.
                count (int): Number of backups found.
                error (str|None): Error message if failed.
        """
        if not os.path.exists(self.backup_dir):
            return {
                "success": True,
                "backups": [],
                "count": 0,
                "error": None,
            }

        try:
            entries = os.listdir(self.backup_dir)
        except OSError as e:
            return {
                "success": False,
                "backups": [],
                "count": 0,
                "error": f"Cannot read backup directory: {e}",
            }

        workbook_name = os.path.basename(self.workbook_path)
        name_without_ext = os.path.splitext(workbook_name)[0]
        prefix = f"{name_without_ext}_backup_"

        backups = []
        for filename in sorted(entries, reverse=True):
            if filename.startswith(prefix) and filename.endswith(".xlsx"):
                filepath = os.path.join(self.backup_dir, filename)
                try:
                    size = os.path.getsize(filepath)
                    mtime = os.path.getmtime(filepath)
                    backups.append({
                        "filename": filename,
                        "path": filepath,
                        "sizeBytes": size,
                        "modified": datetime.fromtimestamp(mtime).isoformat(),
                    })
                except OSError:
                    continue

        return {
            "success": True,
            "backups": backups,
            "count": len(backups),
            "error": None,
        }

    def restore_from_backup(self, backup_path: str) -> dict:
        """Restore the workbook from a backup file.

        WARNING: This overwrites the current workbook with the backup copy.
        A backup of the current workbook is created before restore.

        Args:
            backup_path: Path to the backup file to restore from.

        Returns:
            dict with keys:
                success (bool): Whether the restore succeeded.
                preRestoreBackupPath (str|None): Path to pre-restore backup.
                error (str|None): Error message if failed.
        """
        if not os.path.exists(backup_path):
            return {
                "success": False,
                "preRestoreBackupPath": None,
                "error": f"Backup file not found: {backup_path}",
            }

        # Create a safety backup of current workbook before overwriting
        # Use a distinct _prerestore_ suffix with microseconds to avoid collision
        pre_restore = None
        if os.path.exists(self.workbook_path):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            workbook_name = os.path.basename(self.workbook_path)
            name_without_ext = os.path.splitext(workbook_name)[0]
            pre_filename = f"{name_without_ext}_prerestore_{timestamp}.xlsx"
            pre_path = os.path.join(self.backup_dir, pre_filename)
            # Collision check
            if os.path.exists(pre_path):
                counter = 1
                while os.path.exists(pre_path):
                    pre_filename = f"{name_without_ext}_prerestore_{timestamp}_{counter:03d}.xlsx"
                    pre_path = os.path.join(self.backup_dir, pre_filename)
                    counter += 1
            try:
                os.makedirs(self.backup_dir, exist_ok=True)
                shutil.copy2(self.workbook_path, pre_path)
                if os.path.exists(pre_path) and os.path.getsize(pre_path) > 0:
                    pre_restore = pre_path
            except (OSError, shutil.Error):
                pass

        try:
            shutil.copy2(backup_path, self.workbook_path)
        except (OSError, shutil.Error) as e:
            return {
                "success": False,
                "preRestoreBackupPath": pre_restore,
                "error": f"Restore copy failed: {e}",
            }

        if not os.path.exists(self.workbook_path):
            return {
                "success": False,
                "preRestoreBackupPath": pre_restore,
                "error": "Workbook not found after restore",
            }

        return {
            "success": True,
            "preRestoreBackupPath": pre_restore,
            "error": None,
        }
