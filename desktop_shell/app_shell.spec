# PyInstaller spec for JobTracker PRO Desktop Shell
# Build: pyinstaller desktop_shell/app_shell.spec --noconfirm

import os
import sys

block_cipher = None

# Paths
here = os.path.dirname(os.path.abspath(SPEC))
project_root = os.path.dirname(here)
dist_dir = os.path.join(project_root, 'webui', 'dist')

a = Analysis(
    [os.path.join(here, 'app_shell.py')],
    pathex=[here, project_root],
    binaries=[],
    datas=[
        (dist_dir, 'webui/dist'),
    ],
    hiddenimports=[
        'webview',
        'webview.platforms.edgechromium',
        'http.server',
        'socketserver',
        'openpyxl',
        'backend_bridge',
        'backend_bridge.api',
        'backend_bridge.excel_reader',
        'backend_bridge.excel_writer',
        'backend_bridge.excel_backup',
        'backend_bridge.data_mapper',
        'backend_bridge.services',
        'backend_bridge.services.streak_service',
        'backend_bridge.services.action_service',
        'job_description_analyzer',
        'cover_letter_generator',
        'linkedin_message_generator',
        'interview_prep',
        'streak_tracker',
        'settings',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'pytest'],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='JobTrackerPRO',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(here, 'icon.ico'),
)
