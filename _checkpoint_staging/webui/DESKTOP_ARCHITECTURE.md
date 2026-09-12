# Desktop App Architecture — React UI → Windows .exe

## Goal

Package the React web UI + existing Python/Excel backend into a single
Windows desktop application distributed as an `.exe` installer.

---

## Option Comparison

### 1. PyWebView + PyInstaller

| Aspect | Details |
|---|---|
| **How it works** | Python process opens a webview window pointing at the Vite build output (static HTML/JS/CSS). Python backend runs in the same process. PyInstaller bundles everything into a single `.exe`. |
| **Pros** | Smallest bundle (~30-50 MB). No Node.js runtime needed at runtime. Python backend runs natively — direct access to openpyxl, scripts, file system. Existing `launcher.py` patterns can be reused. Single-process architecture = simpler debugging. |
| **Cons** | PyWebView uses Edge WebView2 (pre-installed on Win10+). Limited window customization vs Electron. No auto-update built-in. |
| **Effort** | Low. Build React → `dist/`, point PyWebView at it, wrap with PyInstaller. |

### 2. Electron + React + Python backend bridge

| Aspect | Details |
|---|---|
| **How it works** | Electron hosts the React UI in a Chromium window. Python backend runs as a subprocess (spawned by Electron). Communication via stdio JSON or local HTTP. |
| **Pros** | Mature ecosystem. Rich window APIs (tray, notifications, auto-update via electron-updater). Huge community. |
| **Cons** | Large bundle (~120-180 MB — ships Chromium + Node.js). Must manage Python subprocess lifecycle. Two runtimes = more complex debugging. Security surface larger. |
| **Effort** | Medium-High. Need electron main process, Python spawn logic, IPC bridge, packaging config. |

### 3. Tauri + React + Python backend bridge

| Aspect | Details |
|---|---|
| **How it works** | Tauri (Rust) hosts the React UI using the OS webview. Python backend runs as a sidecar subprocess. Communication via Tauri commands or local HTTP. |
| **Pros** | Smallest possible bundle (~10-20 MB — uses OS webview, no Chromium). Fast startup. Modern, secure. Good window customization. |
| **Cons** | Rust toolchain required for build. Python sidecar management still needed. Younger ecosystem — fewer examples. WebView2 dependency (same as PyWebView). |
| **Effort** | Medium-High. Need Rust toolchain, Tauri config, Python sidecar setup, IPC bridge. |

---

## Recommendation: PyWebView + PyInstaller

**This is the safest option for this project because:**

1. **Existing Python backend** — The project already has `launcher.py`, 12 Python scripts, openpyxl Excel integration, and a Tkinter UI. PyWebView keeps Python as the primary runtime, meaning all existing code runs natively without subprocess management.

2. **Minimal bundle size** — ~30-50 MB vs Electron's ~150 MB. Important for an Etsy digital download product. Customers don't want to download 150 MB.

3. **Single process** — No IPC bridge, no subprocess lifecycle management, no port conflicts. Python calls and Excel operations happen in the same process that renders the UI.

4. **Simple packaging** — PyInstaller is well-documented for Windows `.exe` creation. The existing `package_builder.py` script already handles ZIP packaging — extending it to PyInstaller is straightforward.

5. **WebView2 is standard** — Edge WebView2 is pre-installed on Windows 10/11. For older systems, a small bootstrapper can be included.

---

## Architecture (Future Implementation)

```
┌─────────────────────────────────────────────┐
│              JobTrackerPRO.exe               │
│                                              │
│  ┌─────────────┐    ┌─────────────────────┐ │
│  │  PyWebView   │    │  Python Backend     │ │
│  │  (WebView2)  │    │                     │ │
│  │              │    │  • openpyxl (Excel)  │ │
│  │  Renders:    │◄──►│  • 12 scripts       │ │
│  │  dist/       │    │  • settings.json    │ │
│  │  (React SPA) │    │  • AI API calls     │ │
│  │              │    │  • File I/O         │ │
│  └─────────────┘    └─────────────────────┘ │
│                                              │
│  JS ↔ Python bridge: window.pywebview.api   │
└─────────────────────────────────────────────┘
         Bundled by PyInstaller
```

## Implementation Steps (Future — Not Now)

1. **Build React** → `npm run build` → `webui/dist/`
2. **Create `desktop_app.py`** — PyWebView window loading `dist/index.html`
3. **Expose Python API** — `pywebview.api` methods for Excel read/write, script execution, settings
4. **Replace mock data calls** — React calls `window.pywebview.api.getApplications()` instead of importing `mockData.ts`
5. **PyInstaller spec** — Bundle Python + `dist/` + scripts + Excel template
6. **Test on clean Windows** — Verify no missing DLLs, WebView2 fallback
7. **Icon + metadata** — `.ico` file, app name, version info

## What We're Doing Now (Phase 1.5)

- Keeping the React UI as a static SPA (no backend calls)
- All data mocked from `mockData.ts`
- `SHOW_MOCK_BADGE` flag in `mockData.ts` controls the "Mock Prototype" badge
- UI is responsive and desktop-ready (fixed sidebar, no browser chrome needed)
- No changes to legacy Python files
