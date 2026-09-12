import os
import shutil
from datetime import datetime
import openpyxl

# Auto Backup Script for Developer Job Application Tracker
# Creates timestamped backups and syncs to cloud storage

def create_backup(source_file, backup_dir):
    """Create a timestamped backup of the Excel file"""
    if not os.path.exists(source_file):
        raise FileNotFoundError(f"Source file not found: {source_file}")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.basename(source_file)
    backup_name = f"{filename.rsplit('.', 1)[0]}_backup_{timestamp}.xlsx"
    backup_path = os.path.join(backup_dir, backup_name)
    
    # Copy file
    shutil.copy2(source_file, backup_path)
    print(f"Backup created: {backup_name}")
    return backup_path

def sync_to_cloud(backup_path, cloud_dirs):
    """Sync backup to cloud storage directories"""
    for cloud_dir in cloud_dirs:
        if os.path.exists(cloud_dir):
            dest = os.path.join(cloud_dir, os.path.basename(backup_path))
            shutil.copy2(backup_path, dest)
            print(f"Synced to: {cloud_dir}")
        else:
            print(f"Cloud directory not found: {cloud_dir}")

def cleanup_old_backups(backup_dir, max_backups=10):
    """Keep only the most recent backups"""
    if not os.path.isdir(backup_dir):
        return
    backups = [
        f for f in os.listdir(backup_dir)
        if f.endswith('.xlsx') and os.path.isfile(os.path.join(backup_dir, f))
    ]
    backups.sort(reverse=True)
    
    for old_backup in backups[max_backups:]:
        os.remove(os.path.join(backup_dir, old_backup))
        print(f"Removed old backup: {old_backup}")

def main():
    _base = os.path.dirname(os.path.abspath(__file__))
    source_file = os.path.join(_base, 'Developer_Job_Application_Tracker_PRO.xlsx')
    backup_dir = os.path.join(_base, 'backups')

    max_backups = 10
    cloud_dirs = []
    try:
        import settings as _cfg
        cfg = _cfg.load()
        files_cfg = cfg.get("files", {})
        max_backups = int(files_cfg.get("max_backups", 10) or 10)
        custom_backup = files_cfg.get("backup_folder", "")
        if custom_backup:
            backup_dir = custom_backup
        cloud_dirs = files_cfg.get("cloud_sync_dirs", []) or []
    except Exception:
        pass

    os.makedirs(backup_dir, exist_ok=True)

    try:
        backup_path = create_backup(source_file, backup_dir)
    except FileNotFoundError as exc:
        print(str(exc))
        return

    if cloud_dirs:
        sync_to_cloud(backup_path, cloud_dirs)

    cleanup_old_backups(backup_dir, max_backups=max_backups)

    print("\nBackup completed successfully!")

if __name__ == "__main__":
    main()
