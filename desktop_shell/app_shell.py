"""
Aviora — Desktop Shell (Phase 1.6 Proof of Concept)

A minimal PyWebView wrapper that loads the React production build.
No backend, no Excel, no settings — just the UI shell.

Usage:
    python desktop_shell/app_shell.py

Requirements:
    pip install pywebview
"""
import os
import sys
import threading
import http.server
import socketserver
import functools

import webview

# Ensure project root is on sys.path so backend_bridge can be imported
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend_bridge.api import ExcelBridgeAPI


def _find_dist() -> str:
    """Locate the React production build directory."""
    # When packaged with PyInstaller, files are extracted to sys._MEIPASS
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    here = os.path.dirname(os.path.abspath(__file__))
    # In onedir mode, _MEIPASS points to _internal/ and exe is one level up
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else here
    candidates = [
        os.path.join(base, 'webui', 'dist'),              # PyInstaller bundled (onefile)
        os.path.join(base, '_internal', 'webui', 'dist'), # PyInstaller bundled (onedir)
        os.path.join(exe_dir, '_internal', 'webui', 'dist'),  # onedir: exe-relative
        os.path.join(here, '..', 'webui', 'dist'),        # dev / source layout
        os.path.join(here, 'dist'),                        # packaged layout
        os.path.join(here, 'webui', 'dist'),              # alt packaged layout
    ]
    for c in candidates:
        resolved = os.path.normpath(c)
        if os.path.isfile(os.path.join(resolved, 'index.html')):
            return resolved
    raise FileNotFoundError(
        "React production build not found. Run 'npm run build' in webui/ first."
    )


def _start_server(dist_dir: str) -> int:
    """Start a lightweight HTTP server serving the dist directory. Returns the port."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=dist_dir)
    # Try ports 8765..8770
    for port in range(8765, 8771):
        try:
            server = socketserver.TCPServer(('127.0.0.1', port), handler)
            server.daemon_threads = True
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            return port
        except OSError:
            continue
    raise RuntimeError("Could not find an available port for the local server.")


def main():
    dist_dir = _find_dist()
    port = _start_server(dist_dir)
    url = f'http://127.0.0.1:{port}/'

    # Locate the Excel workbook
    # Production default: Developer_Job_Application_Tracker_PRO.xlsx in project root
    # Override for demo/validation: set JOBTRACKER_WORKBOOK_PATH env var
    workbook_path = os.environ.get(
        'JOBTRACKER_WORKBOOK_PATH',
        os.path.join(_project_root, 'Developer_Job_Application_Tracker_PRO.xlsx'),
    )
    api = ExcelBridgeAPI(workbook_path)

    window = webview.create_window(
        title='Aviora',
        url=url,
        js_api=api,
        width=1280,
        height=800,
        min_size=(1024, 600),
    )
    api.attach_window(window)
    webview.start()


if __name__ == '__main__':
    main()
