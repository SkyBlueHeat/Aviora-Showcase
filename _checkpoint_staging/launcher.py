"""
Developer Job Application Tracker PRO
Launcher & Tools GUI
CreatorDockStudio

Double-click to run. No extra installation needed beyond Python.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, font as tkfont
import threading
import os
import sys
import io
import subprocess
from datetime import datetime, timedelta

# ── Resolve project directory ────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── i18n: load language from settings before building UI ─────────────────────
try:
    from i18n import t, set_language, get_language, load_from_settings
    load_from_settings()
except Exception:
    def t(key, lang=None): return key.split(".")[-1].replace("_", " ").title()
    def set_language(lang): pass
    def get_language(): return "English"
TRACKER_NAME = "Developer_Job_Application_Tracker_PRO.xlsx"

def _find_tracker() -> str:
    """Search for the Excel tracker in common locations relative to launcher."""
    candidates = [
        # Same folder as launcher
        os.path.join(BASE_DIR, TRACKER_NAME),
        # One level up (launcher is inside 07_Scripts/)
        os.path.join(BASE_DIR, "..", TRACKER_NAME),
        # Two levels up
        os.path.join(BASE_DIR, "..", "..", TRACKER_NAME),
        # Sibling 01_Main_Product folder (ZIP structure)
        os.path.join(BASE_DIR, "..", "01_Main_Product", TRACKER_NAME),
        os.path.join(BASE_DIR, "..", "..", "01_Main_Product", TRACKER_NAME),
    ]
    for p in candidates:
        p = os.path.normpath(p)
        if os.path.exists(p):
            return p
    # Fallback: deep search from two levels up
    root = os.path.normpath(os.path.join(BASE_DIR, "..", ".."))
    for dirpath, _, files in os.walk(root):
        if TRACKER_NAME in files:
            return os.path.join(dirpath, TRACKER_NAME)
    return os.path.join(BASE_DIR, TRACKER_NAME)  # default (will show error)

TRACKER_PATH = _find_tracker()


def _load_settings_cfg() -> dict:
    try:
        import settings as _settings
        return _settings.load()
    except Exception:
        return {}


def _get_tracker_path() -> str:
    cfg = _load_settings_cfg()
    stored = cfg.get("files", {}).get("tracker_path", "")
    if stored and os.path.exists(stored):
        return stored
    return TRACKER_PATH


def _get_saved_api_value(key: str, fallback: str = "") -> str:
    cfg = _load_settings_cfg()
    return str(cfg.get("api", {}).get(key, fallback) or fallback)

# Also add parent dirs to sys.path so sibling scripts are importable
for _p in [BASE_DIR,
           os.path.normpath(os.path.join(BASE_DIR, "..")),
           os.path.normpath(os.path.join(BASE_DIR, "..", "07_Scripts"))]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Color Palette: Deep Navy / Warm Slate ────────────────────────────────────
#   Background: deep slate-navy  →  göz yormaz, profesyonel
#   Cards: 1 ton daha açık slate →  kart hissi verirken aşırı kontrast yok
#   Accent: soft indigo + mint   →  canlı ama agresif değil
BG         = "#0B0F17"   # deeper midnight background
SIDEBAR_BG = "#0F1520"   # slightly elevated sidebar
SURFACE    = "#151B2B"   # card surface with subtle depth
SURFACE2   = "#1C2438"   # input / hover surface
BORDER     = "#2A3650"   # refined borders
BORDER2    = "#364560"   # stronger borders for focus

ACCENT     = "#6366F1"   # vivid indigo
ACCENT2    = "#22D3EE"   # electric cyan
ACCENT3    = "#FBBF24"   # warm amber
ACCENT4    = "#A78BFA"   # soft violet
DANGER     = "#F43F5E"   # rose red

TEXT       = "#F1F5F9"   # crisp off-white
TEXT2      = "#94A3B8"   # secondary text
TEXT3      = "#64748B"   # muted text
WHITE      = "#F1F5F9"
GRAY       = "#64748B"
LIGHT_GRAY = "#2A3650"
GREEN      = "#22D3EE"

# Legacy aliases
ORANGE     = ACCENT3
TEAL       = ACCENT2

# ── Scalable Typography System ───────────────────────────────────────────────
#   All font sizes are derived from _FONT_SCALE.  When the user changes the
#   font size preset, _FONT_SCALE is updated and every F_*() helper returns
#   a proportionally scaled tuple.  This ensures headings, body, buttons,
#   inputs and mono text all scale together consistently.
_FONT_SCALE = 1.0

def _fs(base: int) -> int:
    """Return a font size scaled by the current _FONT_SCALE (min 7)."""
    return max(7, round(base * _FONT_SCALE))

# Semantic font helpers — call these everywhere instead of hardcoding tuples
def F_HERO():     return ("Segoe UI", _fs(18), "bold")    # greeting / page hero
def F_TITLE():    return ("Segoe UI", _fs(16), "bold")    # section titles
def F_SECTION():  return ("Segoe UI", _fs(13), "bold")    # subsection titles
def F_SUB():      return ("Segoe UI", _fs(11))            # subtitles
def F_SUB_B():    return ("Segoe UI", _fs(11), "bold")    # bold subtitles
def F_LABEL():    return ("Segoe UI", _fs(10), "bold")    # labels / buttons
def F_BODY():     return ("Segoe UI", _fs(10))            # body text
def F_SMALL():    return ("Segoe UI", _fs(9))             # secondary text
def F_SMALL_B():  return ("Segoe UI", _fs(9), "bold")     # small bold
def F_TINY():     return ("Segoe UI", _fs(8))             # hints / captions
def F_TINY_B():   return ("Segoe UI", _fs(8), "bold")     # tiny bold
def F_MICRO():    return ("Segoe UI", _fs(7))             # micro labels
def F_STAT():     return ("Segoe UI", _fs(28), "bold")    # big stat numbers
def F_ICON_LG():  return ("Segoe UI", _fs(20))            # large icon text
def F_MONO():     return ("Consolas", _fs(9))             # monospace output
def F_MONO_S():   return ("Consolas", _fs(8))             # small monospace
def F_BODY_I():   return ("Segoe UI", _fs(10), "italic")  # italic body
def F_SMALL_I():  return ("Segoe UI", _fs(9), "italic")   # italic small
def F_TINY_I():   return ("Segoe UI", _fs(8), "italic")   # italic tiny
def F_NAV_LOGO(): return ("Segoe UI", _fs(17), "bold")    # sidebar logo

# Legacy module-level constants (kept for backward compat, now scale-aware)
FONT_TITLE  = F_TITLE()
FONT_SUB    = F_SUB()
FONT_LABEL  = F_LABEL()
FONT_BODY   = F_BODY()
FONT_MONO   = F_MONO()
FONT_BTN    = F_LABEL()

THEME_PRESETS = {
    "dark_navy": {
        "BG": "#151C2C",
        "SIDEBAR_BG": "#0F1520",
        "SURFACE": "#1E2840",
        "SURFACE2": "#253047",
        "BORDER": "#2E3D5C",
        "ACCENT": "#6C8EFF",
        "ACCENT2": "#4ECDC4",
        "ACCENT3": "#FFB347",
        "ACCENT4": "#C084FC",
        "DANGER": "#FF6B6B",
        "TEXT": "#E8EDF8",
        "TEXT2": "#A8B4CC",
        "TEXT3": "#6A7A9B",
        "WHITE": "#E8EDF8",
        "GRAY": "#6A7A9B",
        "LIGHT_GRAY": "#2E3D5C",
        "GREEN": "#4ECDC4",
    },
    "darker": {
        "BG": "#0F131C",
        "SIDEBAR_BG": "#0A0E15",
        "SURFACE": "#171C27",
        "SURFACE2": "#202737",
        "BORDER": "#2A3346",
        "ACCENT": "#7C83FD",
        "ACCENT2": "#47C9B5",
        "ACCENT3": "#FFB86C",
        "ACCENT4": "#BD93F9",
        "DANGER": "#FF6B81",
        "TEXT": "#EEF2FF",
        "TEXT2": "#B2BDD2",
        "TEXT3": "#74819B",
        "WHITE": "#EEF2FF",
        "GRAY": "#74819B",
        "LIGHT_GRAY": "#2A3346",
        "GREEN": "#47C9B5",
    },
    "midnight": {
        "BG": "#111827",
        "SIDEBAR_BG": "#0B1220",
        "SURFACE": "#1F2937",
        "SURFACE2": "#273449",
        "BORDER": "#344256",
        "ACCENT": "#60A5FA",
        "ACCENT2": "#34D399",
        "ACCENT3": "#FBBF24",
        "ACCENT4": "#A78BFA",
        "DANGER": "#F87171",
        "TEXT": "#F3F4F6",
        "TEXT2": "#CBD5E1",
        "TEXT3": "#94A3B8",
        "WHITE": "#F3F4F6",
        "GRAY": "#94A3B8",
        "LIGHT_GRAY": "#344256",
        "GREEN": "#34D399",
    },
    "slate": {
        "BG": "#18212F",
        "SIDEBAR_BG": "#121A26",
        "SURFACE": "#233043",
        "SURFACE2": "#2A3A4E",
        "BORDER": "#3A4A60",
        "ACCENT": "#7C83FD",
        "ACCENT2": "#53D8C9",
        "ACCENT3": "#FFBE76",
        "ACCENT4": "#C792EA",
        "DANGER": "#FF7675",
        "TEXT": "#EAF1FF",
        "TEXT2": "#B7C3D8",
        "TEXT3": "#7C8AA5",
        "WHITE": "#EAF1FF",
        "GRAY": "#7C8AA5",
        "LIGHT_GRAY": "#3A4A60",
        "GREEN": "#53D8C9",
    },
}

FONT_SIZE_PRESETS = {
    "small": {
        "scale": 0.88,
    },
    "medium": {
        "scale": 1.0,
    },
    "large": {
        "scale": 1.15,
    },
}


def _sanitize_hex_color(value: str, fallback: str) -> str:
    text = str(value or "").strip()
    if len(text) == 7 and text.startswith("#"):
        try:
            int(text[1:], 16)
            return text.upper()
        except ValueError:
            return fallback
    return fallback


def _get_backup_dir(cfg: dict | None = None) -> str:
    cfg = cfg or _load_settings_cfg()
    folder = str(cfg.get("files", {}).get("backup_folder", "") or "").strip()
    return folder or os.path.join(BASE_DIR, "backups")


def _parse_clock_time(text: str):
    value = str(text or "").strip()
    try:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.hour, parsed.minute
    except ValueError:
        return None


def _apply_runtime_settings(cfg: dict | None = None):
    global BG, SIDEBAR_BG, SURFACE, SURFACE2, BORDER, ACCENT, ACCENT2, ACCENT3, ACCENT4
    global DANGER, TEXT, TEXT2, TEXT3, WHITE, GRAY, LIGHT_GRAY, GREEN, ORANGE, TEAL
    global FONT_TITLE, FONT_SUB, FONT_LABEL, FONT_BODY, FONT_MONO, FONT_BTN
    global _FONT_SCALE

    cfg = cfg or _load_settings_cfg()
    appearance_cfg = cfg.get("appearance", {})
    theme_name = str(appearance_cfg.get("theme", "dark_navy") or "dark_navy")
    palette = dict(THEME_PRESETS.get(theme_name, THEME_PRESETS["dark_navy"]))
    palette["ACCENT"] = _sanitize_hex_color(appearance_cfg.get("accent_color", palette["ACCENT"]), palette["ACCENT"])

    BG = palette["BG"]
    SIDEBAR_BG = palette["SIDEBAR_BG"]
    SURFACE = palette["SURFACE"]
    SURFACE2 = palette["SURFACE2"]
    BORDER = palette["BORDER"]
    ACCENT = palette["ACCENT"]
    ACCENT2 = palette["ACCENT2"]
    ACCENT3 = palette["ACCENT3"]
    ACCENT4 = palette["ACCENT4"]
    DANGER = palette["DANGER"]
    TEXT = palette["TEXT"]
    TEXT2 = palette["TEXT2"]
    TEXT3 = palette["TEXT3"]
    WHITE = palette["WHITE"]
    GRAY = palette["GRAY"]
    LIGHT_GRAY = palette["LIGHT_GRAY"]
    GREEN = palette["GREEN"]
    ORANGE = ACCENT3
    TEAL = ACCENT2

    font_preset = FONT_SIZE_PRESETS.get(
        str(appearance_cfg.get("font_size", "medium") or "medium").lower(),
        FONT_SIZE_PRESETS["medium"])
    _FONT_SCALE = font_preset.get("scale", 1.0)
    # Refresh legacy constants so they pick up the new scale
    FONT_TITLE = F_TITLE()
    FONT_SUB   = F_SUB()
    FONT_LABEL = F_LABEL()
    FONT_BODY  = F_BODY()
    FONT_MONO  = F_MONO()
    FONT_BTN   = F_LABEL()


def _configure_ttk_style(style: ttk.Style):
    style.theme_use("clam")
    style.configure(
        "TProgressbar",
        troughcolor=SURFACE2,
        background=ACCENT,
        borderwidth=0,
        thickness=4,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )
    style.configure(
        "Vertical.TScrollbar",
        background=SURFACE2,
        troughcolor=SIDEBAR_BG,
        arrowcolor=TEXT3,
        borderwidth=0,
    )
    style.configure(
        "TScrollbar",
        background=SURFACE2,
        troughcolor=BG,
        arrowcolor=TEXT3,
        borderwidth=0,
    )
    style.configure(
        "TCombobox",
        fieldbackground=SURFACE2,
        background=SURFACE2,
        foreground=TEXT,
        selectbackground=ACCENT,
        selectforeground=BG,
        arrowcolor=TEXT2,
        borderwidth=1,
        relief="flat",
        padding=(6, 4),
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", SURFACE2)],
        foreground=[("readonly", TEXT)],
        selectbackground=[("readonly", ACCENT)],
        selectforeground=[("readonly", BG)],
        background=[("active", SURFACE2), ("!active", SURFACE2)],
    )


def _run_auto_backup(cfg: dict | None = None):
    cfg = cfg or _load_settings_cfg()
    files_cfg = cfg.get("files", {})
    if not files_cfg.get("backup_enabled", True):
        return None
    tracker_path = _get_tracker_path()
    if not os.path.exists(tracker_path):
        return None
    backup_dir = _get_backup_dir(cfg)
    os.makedirs(backup_dir, exist_ok=True)
    import auto_backup as _auto_backup
    backup_path = _auto_backup.create_backup(tracker_path, backup_dir)
    max_backups = files_cfg.get("max_backups", 10)
    try:
        max_backups = max(1, int(max_backups))
    except Exception:
        max_backups = 10
    _auto_backup.cleanup_old_backups(backup_dir, max_backups=max_backups)
    return backup_path


_apply_runtime_settings(_load_settings_cfg())


# ── Helper: run a function in thread, stream output to a Text widget ─────────

class OutputRedirector(io.TextIOBase):
    def __init__(self, text_widget: tk.Text):
        self.widget = text_widget

    def write(self, s: str) -> int:
        try:
            if self.widget and self.widget.winfo_exists():
                self.widget.after(0, self._insert, s)
        except (RuntimeError, tk.TclError):
            pass
        return len(s)

    def _insert(self, s: str):
        try:
            self.widget.config(state="normal")
            self.widget.insert("end", s)
            self.widget.see("end")
            self.widget.config(state="disabled")
        except (RuntimeError, tk.TclError):
            pass

    def flush(self):
        pass


def run_in_thread(fn, *args, name=None):
    """Run fn in a daemon thread. If name is given, use it for debugging."""
    t = threading.Thread(target=fn, args=args, daemon=True, name=name or "task")
    t.start()
    return t


# ── Styled helpers ───────────────────────────────────────────────────────────

def styled_frame(parent, bg=SURFACE, **kw):
    return tk.Frame(parent, bg=bg, **kw)


def styled_label(parent, text, font=None, fg=TEXT, bg=SURFACE, **kw):
    return tk.Label(parent, text=text, font=font or F_BODY(), fg=fg, bg=bg, **kw)


def styled_button(parent, text, command, color=ACCENT, width=22, **kw):
    fg_col = "#0F1520" if color in (ACCENT2, ACCENT3) else TEXT
    btn = tk.Button(
        parent, text=text, command=command,
        font=F_LABEL(), bg=color, fg=fg_col,
        activebackground=_lighten(color), activeforeground=fg_col,
        relief="flat", cursor="hand2", width=width,
        padx=14, pady=10, bd=0, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=_lighten(color)))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
    return btn


def ghost_button(parent, text, command, width=18, **kw):
    """Outline-style secondary button."""
    btn = tk.Button(
        parent, text=text, command=command,
        font=F_BODY(), bg=SURFACE2, fg=TEXT2,
        activebackground=BORDER, activeforeground=TEXT,
        relief="flat", cursor="hand2", width=width,
        padx=14, pady=10, bd=0,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=ACCENT, **kw
    )
    btn.bind("<Enter>", lambda e: btn.config(bg=BORDER, fg=TEXT, highlightbackground=ACCENT))
    btn.bind("<Leave>", lambda e: btn.config(bg=SURFACE2, fg=TEXT2, highlightbackground=BORDER))
    return btn


def _lighten(hex_color: str) -> str:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    r, g, b = min(r + 28, 255), min(g + 28, 255), min(b + 28, 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def card(parent, padx=20, pady=16, **kw):
    """Dark card with subtle border — 1px top accent line."""
    outer = tk.Frame(parent, bg=BORDER, **kw)
    top_line = tk.Frame(outer, bg=ACCENT, height=2)
    top_line.pack(fill="x")
    inner = tk.Frame(outer, bg=SURFACE, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True, padx=1, pady=(0, 1))
    return outer, inner


def plain_card(parent, padx=20, pady=16, **kw):
    """Dark card without the top accent line."""
    outer = tk.Frame(parent, bg=BORDER, **kw)
    inner = tk.Frame(outer, bg=SURFACE, padx=padx, pady=pady)
    inner.pack(fill="both", expand=True, padx=1, pady=1)
    return outer, inner


def field(parent, label_text, default="", show=None, height=1):
    """Label + modern dark input field, returns the Entry/Text widget."""
    tk.Label(parent, text=label_text, font=F_SMALL(),
             fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(12, 3))
    if height == 1:
        e = tk.Entry(parent, font=F_BODY(), bg=SURFACE2, fg=TEXT,
                     relief="flat", insertbackground=ACCENT,
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT, show=show or "",
                     disabledbackground=SURFACE2)
        e.insert(0, default)
        e.pack(fill="x", ipady=8)
    else:
        e = tk.Text(parent, font=F_BODY(), bg=SURFACE2, fg=TEXT,
                    relief="flat", insertbackground=ACCENT,
                    highlightthickness=1, highlightbackground=BORDER,
                    highlightcolor=ACCENT, height=height, wrap="word")
        e.insert("1.0", default)
        e.pack(fill="x")
    return e


def section_title(parent, text, color=TEXT, bg=BG):
    tk.Label(parent, text=text, font=F_TITLE(),
             fg=color, bg=bg).pack(anchor="w", pady=(0, 4))


def section_sub(parent, text, bg=BG):
    tk.Label(parent, text=text, font=F_BODY(),
             fg=TEXT3, bg=bg).pack(anchor="w", pady=(0, 12))


def output_box(parent, height=18, placeholder="Output will appear here..."):
    box = scrolledtext.ScrolledText(
        parent, font=F_MONO(), bg="#0D1117", fg="#79C0FF",
        insertbackground=ACCENT, relief="flat", height=height,
        state="disabled", wrap="word",
        highlightthickness=1, highlightbackground=BORDER,
        selectbackground=ACCENT, selectforeground="#0D1117"
    )
    # Insert placeholder text
    box.config(state="normal")
    box.insert("1.0", placeholder)
    box.tag_add("placeholder", "1.0", "end")
    box.tag_config("placeholder", foreground="#3D4D6B", font=("Consolas", _fs(8), "italic"))
    box.config(state="disabled")
    return box


def clear_output(box: scrolledtext.ScrolledText):
    box.config(state="normal")
    box.delete("1.0", "end")
    box.config(state="disabled")


# ── Toast notification system ────────────────────────────────────────────────

_toast_queue: list[tk.Toplevel] = []
_TOAST_COLORS = {
    "success": (ACCENT2, "#0D1B1A"),
    "error":   (DANGER,  "#1B0D0F"),
    "warning": (ACCENT3, "#1B160D"),
    "info":    (ACCENT,  "#0D101B"),
}
_TOAST_ICONS = {"success": "✓", "error": "✕", "warning": "!", "info": "i"}


def show_toast(parent, message, kind="info", duration=3000):
    """Show an elegant toast notification that auto-dismisses."""
    global _toast_queue
    accent_color, bg_color = _TOAST_COLORS.get(kind, _TOAST_COLORS["info"])
    icon = _TOAST_ICONS.get(kind, "i")

    toast = tk.Toplevel(parent)
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.configure(bg=bg_color)

    inner = tk.Frame(toast, bg=bg_color, padx=16, pady=10)
    inner.pack()

    icon_lbl = tk.Label(inner, text=f" {icon} ", font=F_SUB_B(),
                        fg=accent_color, bg=bg_color)
    icon_lbl.pack(side="left", padx=(0, 10))

    msg_lbl = tk.Label(inner, text=message, font=F_BODY(),
                       fg=TEXT, bg=bg_color, wraplength=320, justify="left")
    msg_lbl.pack(side="left")

    accent_strip = tk.Frame(toast, bg=accent_color, height=2)
    accent_strip.pack(fill="x", side="bottom")

    toast.update_idletasks()
    tw = toast.winfo_width()
    th = toast.winfo_height()

    parent.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_x()
    py = parent.winfo_y()

    x = px + pw - tw - 24
    y = py + ph - th - 24 - (len(_toast_queue) * (th + 8))
    toast.geometry(f"{tw}x{th}+{x}+{y}")

    _toast_queue.append(toast)

    def _fade_out(step=0):
        if step < 8:
            toast.attributes("-alpha", 1.0 - (step * 0.12))
            toast.after(20, lambda: _fade_out(step + 1))
        else:
            _dismiss()

    def _dismiss():
        if toast in _toast_queue:
            _toast_queue.remove(toast)
        try:
            toast.destroy()
        except Exception:
            pass

    toast.after(duration, _fade_out)

    def _on_enter(e):
        toast.attributes("-alpha", 1.0)

    def _on_click(e):
        _dismiss()

    toast.bind("<Enter>", _on_enter)
    toast.bind("<Button-1>", _on_click)


# ── Animated counter helper ──────────────────────────────────────────────────

def animate_counter(label, target_text, duration_ms=600, is_percent=False):
    """Animate a label's text from 0 to target value smoothly."""
    try:
        target = int(target_text.replace("%", "").replace(",", ""))
    except (ValueError, TypeError):
        label.config(text=target_text)
        return

    if target == 0:
        label.config(text="0%" if is_percent else "0")
        return

    steps = max(12, min(30, duration_ms // 20))
    delay = duration_ms // steps

    def _step(current=0):
        if current >= steps:
            label.config(text=target_text)
            return
        val = int(target * (current / steps))
        label.config(text=f"{val}%" if is_percent else str(val))
        if label.winfo_exists():
            label.after(delay, lambda: _step(current + 1))

    _step()


# ── Progress bar widget ──────────────────────────────────────────────────────

def mini_progress_bar(parent, value, maximum, color=ACCENT, width=200, height=6, bg=SURFACE2):
    """Create a slim progress bar showing value/maximum."""
    container = tk.Frame(parent, bg=bg, width=width, height=height)
    container.pack_propagate(False)
    fill_width = int((width - 2) * min(value / max(maximum, 1), 1.0))
    fill = tk.Frame(container, bg=color, width=max(fill_width, 0), height=height)
    fill.place(x=0, y=0)
    return container, fill


def update_progress_bar(container, fill, value, maximum, width=200):
    """Update an existing progress bar's fill width."""
    fill_width = int((width - 2) * min(value / max(maximum, 1), 1.0))
    fill.config(width=max(fill_width, 0))


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — HOME
# ════════════════════════════════════════════════════════════════════════════

def build_home_tab(frame):
    frame.config(bg=BG)

    # Scrollable content
    canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(-1*(e.delta//120), "units"))

    # ── Hero Header with Dynamic Greeting ────────────────────────────────
    hdr = tk.Frame(inner, bg=SURFACE, height=130)
    hdr.pack(fill="x")
    hdr.pack_propagate(False)
    # left accent strip
    tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
    hdr_txt = tk.Frame(hdr, bg=SURFACE)
    hdr_txt.pack(side="left", fill="both", expand=True, padx=28, pady=22)

    # Dynamic greeting based on time of day
    _hour = datetime.now().hour
    if _hour < 12:
        _greeting = "Good morning"
    elif _hour < 18:
        _greeting = "Good afternoon"
    else:
        _greeting = "Good evening"

    # Try to get user's name from settings
    _user_name = ""
    try:
        _profile_cfg = _load_settings_cfg().get("profile", {})
        _user_name = _profile_cfg.get("full_name", "").strip()
        if _user_name:
            _first = _user_name.split()[0]
            _greeting_text = f"{_greeting}, {_first}"
        else:
            _greeting_text = _greeting
    except Exception:
        _greeting_text = _greeting

    greeting_lbl = tk.Label(hdr_txt, text=_greeting_text,
             font=F_HERO(), fg=TEXT, bg=SURFACE)
    greeting_lbl.pack(anchor="w")

    # Current date subtitle
    _date_str = datetime.now().strftime("%A, %B %d")
    tk.Label(hdr_txt, text=_date_str,
             font=F_SUB(), fg=ACCENT, bg=SURFACE).pack(anchor="w")

    tk.Label(hdr_txt, text="JobTracker PRO  ·  CreatorDockStudio  ·  v3.0",
             font=F_TINY(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(6, 0))
    # right side: quick action
    hdr_right = tk.Frame(hdr, bg=SURFACE)
    hdr_right.pack(side="right", padx=28)

    def open_tracker():
        tracker_path = _get_tracker_path()
        if os.path.exists(tracker_path):
            os.startfile(tracker_path)
            show_toast(frame.winfo_toplevel(), "Excel tracker opened", "success", 2000)
        else:
            show_toast(frame.winfo_toplevel(), f"Tracker not found at:\n{tracker_path}", "error", 4000)

    styled_button(hdr_right, t("home.step_open"), open_tracker,
                  color=ACCENT, width=20).pack(pady=(28, 6))
    ghost_button(hdr_right, t("home.open_project"),
                 lambda: os.startfile(os.path.dirname(_get_tracker_path())
                         if os.path.exists(_get_tracker_path()) else BASE_DIR),
                 width=20).pack()

    # separator
    tk.Frame(inner, bg=BORDER, height=1).pack(fill="x")

    pad = tk.Frame(inner, bg=BG)
    pad.pack(fill="both", expand=True, padx=24, pady=(20, 0))

    # ── Live Stats KPI Cards ──────────────────────────────────────────────────
    row_lbl = tk.Frame(pad, bg=BG)
    row_lbl.pack(fill="x", pady=(0, 8))
    tk.Label(row_lbl, text=t("home.your_progress"), font=F_SECTION(),
             fg=TEXT, bg=BG).pack(side="left")
    refresh_btn_f = tk.Frame(row_lbl, bg=BG)
    refresh_btn_f.pack(side="right")

    stats_row = tk.Frame(pad, bg=BG)
    stats_row.pack(fill="x", pady=(0, 16))

    stat_labels = {}
    stat_defs = [
        ("apps",       "Total\nApplications", ACCENT),
        ("interviews", "Interviews",           ACCENT4),
        ("offers",     "Offers",               ACCENT2),
        ("rate",       "Response\nRate",        ACCENT3),
    ]
    for key, lbl_text, color in stat_defs:
        c_outer, c_inner = plain_card(stats_row, padx=16, pady=14)
        c_outer.pack(side="left", padx=(0, 10), fill="both", expand=True)
        # colored top line per card
        tk.Frame(c_outer, bg=color, height=3).place(x=1, y=0, relwidth=1)
        val_lbl = tk.Label(c_inner, text="--", font=F_STAT(),
                           fg=color, bg=SURFACE)
        val_lbl.pack(anchor="w")
        tk.Label(c_inner, text=lbl_text, font=F_SMALL(),
                 fg=TEXT3, bg=SURFACE, justify="left").pack(anchor="w")
        stat_labels[key] = val_lbl

    # ── Pipeline Visualization ────────────────────────────────────────────────
    pipeline_f = tk.Frame(pad, bg=BG)
    pipeline_f.pack(fill="x", pady=(0, 16))

    tk.Label(pipeline_f, text="Application Pipeline", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    pipeline_outer, pipeline_inner = plain_card(pad, padx=20, pady=16)
    pipeline_outer.pack(fill="x", pady=(0, 16))

    pipeline_bar_f = tk.Frame(pipeline_inner, bg=SURFACE, height=28)
    pipeline_bar_f.pack(fill="x", pady=(0, 8))
    pipeline_bar_f.pack_propagate(False)

    pipeline_labels_f = tk.Frame(pipeline_inner, bg=SURFACE)
    pipeline_labels_f.pack(fill="x")

    pipeline_segments = {}
    pipeline_seg_labels = {}
    PIPELINE_STAGES = [
        ("Applied",    ACCENT,   "#1E2438"),
        ("Screening",  ACCENT4,  "#231E38"),
        ("Interview",  ACCENT3,  "#2A2418"),
        ("Offer",      ACCENT2,  "#0D2222"),
        ("Rejected",   DANGER,   "#2A0F14"),
    ]

    for stage, color, dim_color in PIPELINE_STAGES:
        seg = tk.Frame(pipeline_bar_f, bg=dim_color)
        seg.pack(side="left", fill="y", padx=1, expand=True)
        pipeline_segments[stage] = seg
        lbl_f = tk.Frame(pipeline_labels_f, bg=SURFACE)
        lbl_f.pack(side="left", fill="x", expand=True, padx=1)
        tk.Label(lbl_f, text=stage, font=F_TINY_B(),
                 fg=color, bg=SURFACE).pack(anchor="center")
        cnt_lbl = tk.Label(lbl_f, text="0", font=F_LABEL(),
                           fg=TEXT, bg=SURFACE)
        cnt_lbl.pack(anchor="center")
        pipeline_seg_labels[stage] = cnt_lbl

    # ── Three-column: Weekly Chart | Today's Focus | Smart Insight ──────────
    insight_row = tk.Frame(pad, bg=BG)
    insight_row.pack(fill="x", pady=(0, 16))

    # Left: Weekly Activity Chart (wider)
    chart_col = tk.Frame(insight_row, bg=BG)
    chart_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(chart_col, text="Weekly Activity", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    chart_outer, chart_inner = plain_card(chart_col, padx=16, pady=14)
    chart_outer.pack(fill="both", expand=True)

    chart_canvas = tk.Canvas(chart_inner, bg=SURFACE, highlightthickness=0, height=130)
    chart_canvas.pack(fill="both", expand=True)

    # Middle: Today's Focus
    focus_col = tk.Frame(insight_row, bg=BG)
    focus_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(focus_col, text="Today's Focus", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    focus_outer, focus_inner = plain_card(focus_col, padx=16, pady=14)
    focus_outer.pack(fill="both", expand=True)

    focus_items_f = tk.Frame(focus_inner, bg=SURFACE)
    focus_items_f.pack(fill="x")

    # Right: Smart Insight
    insight_col = tk.Frame(insight_row, bg=BG)
    insight_col.pack(side="left", fill="both", expand=True)

    tk.Label(insight_col, text="Smart Insight", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    insight_outer, insight_inner = plain_card(insight_col, padx=16, pady=14)
    insight_outer.pack(fill="both", expand=True)

    insight_icon_lbl = tk.Label(insight_inner, text="💡", font=F_ICON_LG(),
                                fg=ACCENT3, bg=SURFACE)
    insight_icon_lbl.pack(anchor="w")
    insight_text_lbl = tk.Label(insight_inner, text="Add applications to get personalized insights.",
                                font=F_SMALL(), fg=TEXT2, bg=SURFACE,
                                wraplength=240, justify="left")
    insight_text_lbl.pack(anchor="w", pady=(6, 0))

    # ── Two-column: Recent Applications + Upcoming Follow-ups ────────────────
    dual_f = tk.Frame(pad, bg=BG)
    dual_f.pack(fill="x", pady=(0, 16))

    # Left: Recent Applications
    left_col = tk.Frame(dual_f, bg=BG)
    left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

    tk.Label(left_col, text="Recent Applications", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    recent_outer, recent_inner = plain_card(left_col, padx=16, pady=14)
    recent_outer.pack(fill="both", expand=True)

    recent_list_f = tk.Frame(recent_inner, bg=SURFACE)
    recent_list_f.pack(fill="both", expand=True)

    recent_empty = tk.Label(recent_list_f, text="No applications yet — open the Excel tracker to get started",
                            font=F_SMALL(), fg=TEXT3, bg=SURFACE,
                            wraplength=300, justify="left", pady=20)
    recent_empty.pack(fill="both", expand=True)

    # Right: Upcoming Follow-ups
    right_col = tk.Frame(dual_f, bg=BG)
    right_col.pack(side="right", fill="both", expand=True)

    tk.Label(right_col, text="Upcoming Follow-ups", font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    followup_outer, followup_inner = plain_card(right_col, padx=16, pady=14)
    followup_outer.pack(fill="both", expand=True)

    followup_list_f = tk.Frame(followup_inner, bg=SURFACE)
    followup_list_f.pack(fill="both", expand=True)

    followup_empty = tk.Label(followup_list_f, text="No upcoming follow-ups — you're all caught up!",
                              font=F_SMALL(), fg=TEXT3, bg=SURFACE,
                              wraplength=300, justify="left", pady=20)
    followup_empty.pack(fill="both", expand=True)

    # ── Quick Start card (2-column grid) ────────────────────────────────────
    tk.Label(pad, text=t("home.getting_started"), font=F_SECTION(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    step_colors = [ACCENT, ACCENT4, ACCENT2, ACCENT3, ACCENT2, ACCENT4]
    steps = [
        (t("home.step_open"),    t("home.step_open_desc")),
        (t("home.step_add"),     t("home.step_add_desc")),
        (t("home.step_dashboard"),t("home.step_dashboard_desc")),
        (t("home.step_ats"),     t("home.step_ats_desc")),
        (t("home.step_jd"),      t("home.step_jd_desc")),
        (t("home.step_cover"),   t("home.step_cover_desc")),
    ]
    qs_outer, qs_inner = plain_card(pad, padx=20, pady=16)
    qs_outer.pack(fill="x", pady=(0, 16))

    for i, (title, desc) in enumerate(steps):
        col = i % 2
        row = i // 2
        row_f = tk.Frame(qs_inner, bg=SURFACE)
        row_f.grid(row=row, column=col, padx=(0, 16 if col == 0 else 0), pady=4, sticky="ew")
        qs_inner.columnconfigure(col, weight=1)
        dot_color = step_colors[i]
        tk.Label(row_f, text="●", font=F_SECTION(),
                 fg=dot_color, bg=SURFACE).pack(side="left", padx=(0, 10))
        tk.Label(row_f, text=title, font=F_LABEL(),
                 fg=TEXT, bg=SURFACE, anchor="w").pack(side="left")
        tk.Label(row_f, text=desc, font=F_SMALL(),
                 fg=TEXT3, bg=SURFACE).pack(side="left", padx=(8, 0))

    # ── Data refresh logic ────────────────────────────────────────────────────
    _first_refresh = [True]

    def refresh_stats():
        try:
            import openpyxl
            tracker_path = _get_tracker_path()
            wb = openpyxl.load_workbook(tracker_path, data_only=True, read_only=True)
            ws = wb["Applications"]
            rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if any(c for c in r)]
            total = len(rows)
            # v3.0: Status is now column J (index 9)
            interviews = sum(1 for r in rows if len(r) > 9 and r[9] and "interview" in str(r[9]).lower())
            offers = sum(1 for r in rows if len(r) > 9 and r[9] and str(r[9]).lower() in ["offer", "accepted"])
            rate_val = f"{int(interviews/total*100)}%" if total else "0%"
            wb.close()

            # Animate counters only on first load
            if _first_refresh[0]:
                animate_counter(stat_labels["apps"], str(total))
                animate_counter(stat_labels["interviews"], str(interviews))
                animate_counter(stat_labels["offers"], str(offers))
                animate_counter(stat_labels["rate"], rate_val, is_percent=True)
                _first_refresh[0] = False
            else:
                stat_labels["apps"].config(text=str(total))
                stat_labels["interviews"].config(text=str(interviews))
                stat_labels["offers"].config(text=str(offers))
                stat_labels["rate"].config(text=rate_val)

            # Update pipeline
            status_counts = {"Applied": 0, "Screening": 0, "Interview": 0, "Offer": 0, "Rejected": 0}
            for r in rows:
                s = str(r[9] or "").strip() if len(r) > 9 else ""
                s_lower = s.lower()
                if s_lower == "applied": status_counts["Applied"] += 1
                elif s_lower == "screening": status_counts["Screening"] += 1
                elif "interview" in s_lower: status_counts["Interview"] += 1
                elif s_lower in ("offer", "accepted"): status_counts["Offer"] += 1
                elif s_lower in ("rejected", "ghosted", "withdrawn", "declined"): status_counts["Rejected"] += 1

            for stage, count in status_counts.items():
                pipeline_seg_labels[stage].config(text=str(count))

            # Update recent applications (Company=col B idx 1, Role=col C idx 2, Status=col J idx 9, Date=col I idx 8)
            for child in recent_list_f.winfo_children():
                child.destroy()
            recent_rows = sorted(rows, key=lambda r: str(r[8] or ""), reverse=True)[:5]
            if recent_rows:
                for r in recent_rows:
                    company = str(r[1] or "—")[:20]
                    role = str(r[2] or "—")[:22]
                    status = str(r[9] or "—")[:12]
                    row_f = tk.Frame(recent_list_f, bg=SURFACE)
                    row_f.pack(fill="x", pady=3)
                    tk.Label(row_f, text=company, font=F_SMALL_B(),
                             fg=TEXT, bg=SURFACE, width=18, anchor="w").pack(side="left")
                    tk.Label(row_f, text=role, font=F_SMALL(),
                             fg=TEXT2, bg=SURFACE, width=20, anchor="w").pack(side="left", padx=(4, 0))
                    tk.Label(row_f, text=status, font=F_TINY_B(),
                             fg=ACCENT, bg=SURFACE, anchor="e").pack(side="right")
            else:
                tk.Label(recent_list_f, text="No applications yet — open the Excel tracker to get started",
                         font=F_SMALL(), fg=TEXT3, bg=SURFACE,
                         wraplength=280, justify="left", pady=20).pack(fill="both", expand=True)

            # Update upcoming follow-ups (Follow-up Date=col M idx 12, Company=col B idx 1, Role=col C idx 2)
            for child in followup_list_f.winfo_children():
                child.destroy()
            today = datetime.now().date()
            followups = []
            for r in rows:
                fu_date_raw = r[12] if len(r) > 12 else None
                if fu_date_raw:
                    try:
                        if hasattr(fu_date_raw, 'date'):
                            fu_date = fu_date_raw.date()
                        else:
                            fu_date = datetime.strptime(str(fu_date_raw)[:10], "%Y-%m-%d").date()
                        if fu_date >= today:
                            followups.append((fu_date, str(r[1] or "—"), str(r[2] or "—")))
                    except Exception:
                        pass
            followups.sort(key=lambda x: x[0])
            followups = followups[:5]
            if followups:
                for fu_date, company, role in followups:
                    days_away = (fu_date - today).days
                    if days_away == 0:
                        badge_text = "Today"
                        badge_color = DANGER
                    elif days_away == 1:
                        badge_text = "1 day"
                        badge_color = ACCENT3
                    else:
                        badge_text = f"{days_away}d"
                        badge_color = ACCENT4
                    row_f = tk.Frame(followup_list_f, bg=SURFACE)
                    row_f.pack(fill="x", pady=3)
                    tk.Label(row_f, text=company[:18], font=F_SMALL_B(),
                             fg=TEXT, bg=SURFACE, width=16, anchor="w").pack(side="left")
                    tk.Label(row_f, text=role[:18], font=F_SMALL(),
                             fg=TEXT2, bg=SURFACE, width=16, anchor="w").pack(side="left", padx=(4, 0))
                    tk.Label(row_f, text=badge_text, font=F_TINY_B(),
                             fg=badge_color, bg=SURFACE, anchor="e").pack(side="right")
            else:
                tk.Label(followup_list_f, text="No upcoming follow-ups — you're all caught up!",
                         font=F_SMALL(), fg=TEXT3, bg=SURFACE,
                         wraplength=280, justify="left", pady=20).pack(fill="both", expand=True)

            # ── Update Weekly Activity Chart ─────────────────────────────────
            chart_canvas.delete("all")
            today_date = datetime.now().date()
            day_counts = []
            for i in range(6, -1, -1):
                d = today_date - timedelta(days=i)
                count = 0
                for r in rows:
                    date_raw = r[8] if len(r) > 8 else None
                    if date_raw:
                        try:
                            if hasattr(date_raw, 'date'):
                                r_date = date_raw.date()
                            else:
                                r_date = datetime.strptime(str(date_raw)[:10], "%Y-%m-%d").date()
                            if r_date == d:
                                count += 1
                        except Exception:
                            pass
                day_counts.append(count)

            cw = chart_canvas.winfo_width() or 300
            ch = chart_canvas.winfo_height() or 120
            if cw < 10: cw = 300
            if ch < 10: ch = 120
            bar_w = (cw - 40) / 7
            max_val = max(max(day_counts), 1)
            bar_h_max = ch - 30
            day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            today_dow = today_date.weekday()
            for i, count in enumerate(day_counts):
                x = 20 + i * bar_w
                bar_h = max((count / max_val) * bar_h_max, 2) if count > 0 else 2
                y_top = ch - 20 - bar_h
                dow = (today_dow - 6 + i) % 7
                color = ACCENT if count > 0 else SURFACE2
                chart_canvas.create_rectangle(x + 4, y_top, x + bar_w - 4, ch - 20,
                                              fill=color, outline="")
                if count > 0:
                    chart_canvas.create_text(x + bar_w / 2, y_top - 8,
                                             text=str(count), font=F_TINY_B(),
                                             fill=TEXT, anchor="s")
                chart_canvas.create_text(x + bar_w / 2, ch - 8,
                                         text=day_labels[dow], font=F_MICRO(),
                                         fill=TEXT3, anchor="s")

            # ── Update Today's Focus ─────────────────────────────────────────
            for child in focus_items_f.winfo_children():
                child.destroy()

            # Count follow-ups due today and this week
            fu_today = 0
            fu_this_week = 0
            for r in rows:
                fu_date_raw = r[12] if len(r) > 12 else None
                if fu_date_raw:
                    try:
                        if hasattr(fu_date_raw, 'date'):
                            fu_date = fu_date_raw.date()
                        else:
                            fu_date = datetime.strptime(str(fu_date_raw)[:10], "%Y-%m-%d").date()
                        if fu_date == today_date:
                            fu_today += 1
                        elif fu_date > today_date and (fu_date - today_date).days <= 7:
                            fu_this_week += 1
                    except Exception:
                        pass

            pending_interviews = sum(1 for r in rows if len(r) > 9 and r[9] and "interview" in str(r[9]).lower())

            focus_items = [
                (f"{fu_today} follow-up{'s' if fu_today != 1 else ''} due today", DANGER if fu_today > 0 else TEXT3),
                (f"{pending_interviews} active interview{'s' if pending_interviews != 1 else ''}", ACCENT4 if pending_interviews > 0 else TEXT3),
                (f"{fu_this_week} follow-up{'s' if fu_this_week != 1 else ''} this week", ACCENT3 if fu_this_week > 0 else TEXT3),
            ]
            for text, color in focus_items:
                r_f = tk.Frame(focus_items_f, bg=SURFACE)
                r_f.pack(fill="x", pady=3)
                tk.Label(r_f, text="●", font=F_TINY(),
                         fg=color, bg=SURFACE).pack(side="left", padx=(0, 8))
                tk.Label(r_f, text=text, font=F_SMALL(),
                         fg=TEXT2, bg=SURFACE).pack(side="left")

            if not any(fu_today or pending_interviews or fu_this_week):
                tk.Label(focus_items_f, text="Nothing urgent — great job staying on top of things!",
                         font=F_SMALL_I(), fg=ACCENT2, bg=SURFACE,
                         wraplength=280, justify="left").pack(anchor="w", pady=4)

            # ── Update Smart Insight ─────────────────────────────────────────
            if total == 0:
                insight_icon_lbl.config(text="🚀")
                insight_text_lbl.config(text="Welcome! Open the Excel tracker and add your first application to get started.")
            elif total < 5:
                insight_icon_lbl.config(text="🌱")
                insight_text_lbl.config(text=f"You've started with {total} application{'s' if total != 1 else ''}. Keep the momentum going — consistency is key!")
            elif rate_val != "0%":
                rate_num = int(rate_val.replace("%", ""))
                if rate_num >= 20:
                    insight_icon_lbl.config(text="🔥")
                    insight_text_lbl.config(text=f"Your response rate is {rate_val} — that's above the industry average of 10-15%. Excellent work!")
                elif rate_num >= 10:
                    insight_icon_lbl.config(text="📈")
                    insight_text_lbl.config(text=f"Your response rate is {rate_val}. Try tailoring your resume for each application to boost this further.")
                else:
                    insight_icon_lbl.config(text="💡")
                    insight_text_lbl.config(text=f"Your response rate is {rate_val}. Consider using the ATS Checker to optimize your resume before applying.")
            elif interviews > 0:
                insight_icon_lbl.config(text="🎯")
                insight_text_lbl.config(text=f"You have {interviews} active interview{'s' if interviews != 1 else ''}. Practice with the Interview Prep tab to ace them!")
            elif offers > 0:
                insight_icon_lbl.config(text="🎉")
                insight_text_lbl.config(text=f"Congratulations on {offers} offer{'s' if offers != 1 else ''}! Use the Salary Calculator to negotiate the best package.")
            else:
                insight_icon_lbl.config(text="📋")
                insight_text_lbl.config(text=f"You have {total} applications in progress. Follow up on older ones to increase your response rate.")

        except Exception:
            for v in stat_labels.values(): v.config(text="--")

    def poll_stats():
        refresh_stats()
        if frame.winfo_exists():
            frame.after(15000, poll_stats)

    ghost_button(refresh_btn_f, "Refresh", refresh_stats, width=10).pack()
    frame.after(600, poll_stats)
    frame._refresh_data = refresh_stats


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — ATS RESUME CHECKER
# ════════════════════════════════════════════════════════════════════════════

def build_ats_tab(frame):
    frame.config(bg=BG)

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("ats.title"), color=ACCENT, bg=BG)
    section_sub(hdr, t("ats.subtitle"), bg=BG)

    body = tk.Frame(frame, bg=BG)
    body.pack(fill="x", padx=24)

    c_outer, c_inner = card(body, padx=20, pady=16)
    c_outer.pack(fill="x", pady=(0, 12))

    resume_var = tk.StringVar()
    jd_var     = tk.StringVar()

    def pick(var, title, types):
        p = filedialog.askopenfilename(title=title, filetypes=types)
        if p: var.set(p)

    for lbl_txt, var, title, types in [
        (t("ats.resume_file"), resume_var, "Select Resume",
         [("Documents", "*.docx *.pdf *.txt"), ("All", "*.*")]),
        (t("ats.jd_optional"), jd_var, "Select Job Description",
         [("Text", "*.txt"), ("All", "*.*")]),
    ]:
        r = tk.Frame(c_inner, bg=SURFACE)
        r.pack(fill="x", pady=5)
        tk.Label(r, text=lbl_txt, font=F_SMALL(), fg=TEXT3, bg=SURFACE, width=24, anchor="w").pack(side="left")
        tk.Entry(r, textvariable=var, font=F_BODY(), bg=SURFACE2, fg=TEXT,
                 relief="flat", highlightthickness=1, highlightbackground=BORDER,
                 highlightcolor=ACCENT, width=46).pack(side="left", ipady=5, padx=(0, 8))
        styled_button(r, "Browse", lambda v=var, t=title, tp=types: pick(v, t, tp),
                      color=BORDER, width=7).pack(side="left")

    out = output_box(frame, height=20)

    def run_check():
        resume = resume_var.get().strip()
        if not resume or not os.path.exists(resume):
            show_toast(frame.winfo_toplevel(), "Please select a valid resume file", "warning", 3000)
            return
        jd = jd_var.get().strip() or None
        clear_output(out)
        sys.stdout = OutputRedirector(out)
        def task():
            try:
                import ats_resume_checker as a
                a.generate_report(resume, jd)
            except Exception as e:
                print(f"\n[!] Error: {e}")
            finally:
                sys.stdout = sys.__stdout__
        run_in_thread(task, name="ats_analyze")

    styled_button(body, t("ats.analyze"), run_check,
                  color=ACCENT, width=20).pack(anchor="w", pady=(0, 8))
    out.pack(fill="both", expand=True, padx=24, pady=(0, 16))


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — JOB DESCRIPTION ANALYZER
# ════════════════════════════════════════════════════════════════════════════

def build_jd_tab(frame):
    frame.config(bg=BG)

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("jd.title"), color=ACCENT4, bg=BG)
    section_sub(hdr, t("jd.subtitle"), bg=BG)

    body = tk.Frame(frame, bg=BG)
    body.pack(fill="both", expand=True, padx=24, pady=0)

    left = tk.Frame(body, bg=BG)
    left.pack(side="left", fill="both", expand=True, padx=(0, 10))
    right = tk.Frame(body, bg=BG)
    right.pack(side="left", fill="both", expand=True)

    tk.Label(left, text=t("jd.job_description"), font=F_SMALL(), fg=TEXT3, bg=BG).pack(anchor="w", pady=(0, 4))
    jd_input = scrolledtext.ScrolledText(
        left, font=F_BODY(), bg=SURFACE, fg=TEXT,
        insertbackground=TEXT, relief="flat", height=14, wrap="word",
        highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT
    )
    jd_input.pack(fill="both", expand=True, pady=(0, 8))

    tk.Label(left, text=t("jd.skills_hint"),
             font=F_SMALL(), fg=TEXT3, bg=BG).pack(anchor="w")
    skills_entry = tk.Entry(left, font=F_BODY(), bg=SURFACE, fg=TEXT,
                            relief="flat", insertbackground=TEXT,
                            highlightthickness=1, highlightbackground=BORDER,
                            highlightcolor=ACCENT)
    skills_entry.pack(fill="x", ipady=6, pady=(4, 4))
    tk.Label(left, text=t("jd.skills_example"),
             font=F_TINY(), fg=TEXT3, bg=BG).pack(anchor="w")

    styled_button(left, t("jd.analyze_btn"), lambda: run_analysis(),
                  color=ACCENT4, width=20).pack(anchor="w", pady=12)

    tk.Label(right, text=t("jd.output"), font=F_SMALL(), fg=TEXT3, bg=BG).pack(anchor="w", pady=(0, 4))
    out = output_box(right, height=24)
    out.pack(fill="both", expand=True)

    _jd_live_status = tk.Label(right, text="", font=F_TINY(), fg=TEXT3, bg=BG)
    _jd_live_status.pack(anchor="w", pady=(2, 0))

    _jd_debounce_id = [None]
    _jd_gen_id = [0]

    def _render_analysis_output(jd_text, skills, gen_id, tracker_path=""):
        if not frame.winfo_exists():
            return
        if gen_id != _jd_gen_id[0]:
            return
        clear_output(out)
        old_stdout = sys.stdout
        sys.stdout = OutputRedirector(out)
        def task():
            try:
                import job_description_analyzer as j
                j.analyze(jd_text, skills, tracker_path)
                if frame.winfo_exists() and gen_id == _jd_gen_id[0]:
                    try:
                        frame.after(0, lambda: _jd_live_status.config(text="Live analysis complete", fg=ACCENT2))
                    except Exception:
                        pass
            except Exception:
                if frame.winfo_exists() and gen_id == _jd_gen_id[0]:
                    try:
                        frame.after(0, lambda: _jd_live_status.config(text="Analysis error", fg=DANGER))
                    except Exception:
                        pass
            finally:
                sys.stdout = old_stdout
        run_in_thread(task, name="jd_analyze")
        jd_text = jd_input.get("1.0", "end").strip()
        if len(jd_text) < 50:
            _jd_live_status.config(text="Type 50+ characters for live analysis", fg=TEXT3)
            return
        skills = skills_entry.get().strip()
        _jd_gen_id[0] += 1
        gen_id = _jd_gen_id[0]
        _jd_live_status.config(text="Analyzing...", fg=ACCENT3)
        _render_analysis_output(jd_text, skills, gen_id, tracker_path="")

    def _jd_debounced_live():
        if _jd_debounce_id[0]:
            frame.after_cancel(_jd_debounce_id[0])
        _jd_debounce_id[0] = frame.after(1500, _jd_live_analysis)

    jd_input.bind("<KeyRelease>", lambda _: _jd_debounced_live(), add="+")
    skills_entry.bind("<KeyRelease>", lambda _: _jd_debounced_live(), add="+")

    def run_analysis():
        jd_text = jd_input.get("1.0", "end").strip()
        if len(jd_text) < 50:
            show_toast(frame.winfo_toplevel(), "Please paste a full job description (50+ characters)", "warning", 3000)
            return
        skills = skills_entry.get().strip()
        _jd_gen_id[0] += 1
        gen_id = _jd_gen_id[0]
        _jd_live_status.config(text="Manual analysis running...", fg=ACCENT3)
        _render_analysis_output(jd_text, skills, gen_id, tracker_path=_get_tracker_path())


# ════════════════════════════════════════════════════════════════════════════
# TAB 4 — TOOLS
# ════════════════════════════════════════════════════════════════════════════

def build_tools_tab(frame):
    frame.config(bg=BG)

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("tools.title"), color=TEXT, bg=BG)
    section_sub(hdr, t("tools.subtitle"), bg=BG)

    out = output_box(frame, height=14)

    # Map script names to their main callable
    SCRIPT_FUNCS = {
        "auto_backup.py":      ("auto_backup",      "main"),
        "chart_generator.py":  ("chart_generator",  "main"),
        "report_generator.py": ("report_generator", "main"),
        "data_export.py":      ("data_export",       "main"),
        "validate_data.py":    ("validate_data",     "main"),
    }

    def _find_script(name: str) -> str:
        for folder in [BASE_DIR,
                       os.path.normpath(os.path.join(BASE_DIR, "..", "07_Scripts")),
                       os.path.normpath(os.path.join(BASE_DIR, ".."))]:
            p = os.path.join(folder, name)
            if os.path.exists(p):
                return p
        return os.path.join(BASE_DIR, name)

    # Progress bar
    prog_var = tk.DoubleVar(value=0)
    prog_row = tk.Frame(frame, bg=BG)
    prog_row.pack(fill="x", padx=24, pady=(0, 4))
    prog = ttk.Progressbar(prog_row, variable=prog_var, maximum=100, mode="indeterminate", length=400)
    prog.pack(side="left")
    prog_lbl = tk.Label(prog_row, text="", font=F_SMALL(), fg=TEXT3, bg=BG)
    prog_lbl.pack(side="left", padx=10)

    def run_script(script_name: str):
        path = _find_script(script_name)
        if not os.path.exists(path):
            messagebox.showerror("Not Found", f"{script_name} not found.")
            return
        clear_output(out)

        def _safe_ui(fn):
            try:
                frame.after(0, fn)
            except (RuntimeError, tk.TclError):
                pass

        def task():
            old_stdout = sys.stdout
            sys.stdout = OutputRedirector(out)
            _safe_ui(lambda: prog.start(12))
            _safe_ui(lambda: prog_lbl.config(text=f"Running {script_name}..."))
            try:
                print(f">> Running {script_name}...\n")
                mod_name, func_name = SCRIPT_FUNCS.get(script_name, (None, None))
                if mod_name:
                    import importlib
                    mod = importlib.import_module(mod_name)
                    importlib.reload(mod)
                    fn = getattr(mod, func_name, None)
                    if fn:
                        fn()
                    else:
                        result = subprocess.run(
                            [sys.executable, path],
                            capture_output=True, text=True, cwd=BASE_DIR
                        )
                        print(result.stdout or "(no output)")
                        if result.stderr:
                            print("\n[!] Errors:\n" + result.stderr)
                else:
                    result = subprocess.run(
                        [sys.executable, path],
                        capture_output=True, text=True, cwd=BASE_DIR
                    )
                    print(result.stdout or "(no output)")
                    if result.stderr:
                        print("\n[!] Errors:\n" + result.stderr)
                print(f"\n[DONE] {script_name} finished.")
                _safe_ui(lambda: prog_lbl.config(text=f"Done: {script_name}"))
            except Exception as e:
                import traceback
                print(f"\n[!] Error: {e}\n")
                print(traceback.format_exc())
                _safe_ui(lambda: prog_lbl.config(text="Error — see output below"))
            finally:
                sys.stdout = old_stdout
                _safe_ui(lambda: (prog.stop(), prog_var.set(0)))

        run_in_thread(task, name="tools_run_script")
    tools = [
        (t("tools.backup_tracker"),  "auto_backup.py",     ACCENT2, t("tools.backup_desc")),
        (t("tools.generate_charts"), "chart_generator.py", ACCENT,  t("tools.charts_desc")),
        (t("tools.weekly_report"),   "report_generator.py",ACCENT4, t("tools.report_desc")),
        (t("tools.export_data"),     "data_export.py",     ACCENT3, t("tools.export_desc")),
        (t("tools.validate_data"),   "validate_data.py",   DANGER,  t("tools.validate_desc")),
    ]

    grid = tk.Frame(frame, bg=BG)
    grid.pack(fill="x", padx=24, pady=(0, 10))

    for i, (label, script, color, tooltip) in enumerate(tools):
        col = i % 3
        row_idx = i // 3
        c_outer, c_inner = card(grid, padx=14, pady=12)
        c_outer.grid(row=row_idx, column=col, padx=5, pady=5, sticky="nsew")
        grid.columnconfigure(col, weight=1)

        accent_strip = tk.Frame(c_inner, bg=color, width=3)
        accent_strip.pack(side="left", fill="y", padx=(0, 10))
        content = tk.Frame(c_inner, bg=SURFACE)
        content.pack(side="left", fill="both", expand=True)

        tk.Label(content, text=label, font=F_LABEL(),
                 fg=TEXT, bg=SURFACE).pack(anchor="w")
        tk.Label(content, text=tooltip, font=F_TINY(),
                 fg=TEXT3, bg=SURFACE, wraplength=200, justify="left").pack(anchor="w", pady=(2, 8))
        styled_button(content, t("tools.run"), lambda s=script: run_script(s),
                      color=color, width=10).pack(anchor="w")

    out.pack(fill="both", expand=True, padx=24, pady=(0, 16))


# ════════════════════════════════════════════════════════════════════════════
# TAB 5 - EMAIL REMINDER
# ════════════════════════════════════════════════════════════════════════════

def build_email_tab(frame):
    frame.config(bg=BG)
    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("email.title"), color=ACCENT3, bg=BG)
    section_sub(hdr, t("email.subtitle"), bg=BG)

    notifications_cfg = _load_settings_cfg().get("notifications", {})
    app = frame.winfo_toplevel()
    runtime_email = getattr(app, "_get_email_runtime_config", lambda: {})()

    c_outer, form = card(frame, padx=24, pady=20)
    c_outer.pack(fill="x", padx=24, pady=(0, 12))

    to_entry   = field(form, t("email.your_email"), runtime_email.get("to_email", "") or "you@example.com")
    from_entry = field(form, t("email.sender"), runtime_email.get("from_email", "") or "sender@gmail.com")
    pass_entry = field(form, t("email.password"), runtime_email.get("password", ""), show="*")
    days_entry = field(form, t("email.days"), str(notifications_cfg.get("followup_days", 7)))

    def _remember_email_fields(_event=None):
        remember_fn = getattr(app, "_remember_email_runtime_config", None)
        if remember_fn:
            remember_fn({
                "to_email": to_entry.get().strip(),
                "from_email": from_entry.get().strip(),
                "password": pass_entry.get().strip(),
            })

    for entry in (to_entry, from_entry, pass_entry):
        entry.bind("<KeyRelease>", _remember_email_fields, add="+")
        entry.bind("<FocusOut>", _remember_email_fields, add="+")

    tk.Label(form,
             text=t("email.tip"),
             font=F_TINY(), fg=TEXT3, bg=SURFACE, wraplength=480, justify="left"
             ).pack(anchor="w", pady=(6, 0))

    out = output_box(frame, height=10)

    def send_reminders():
        clear_output(out)
        old = sys.stdout; sys.stdout = OutputRedirector(out)
        _remember_email_fields()
        # Pre-read widget values on main thread before spawning background thread
        _from_val = from_entry.get().strip()
        _pass_val = pass_entry.get().strip()
        _to_val = to_entry.get().strip()
        _days_val = days_entry.get().strip()
        def task():
            try:
                import importlib
                if "email_reminder" in sys.modules: del sys.modules["email_reminder"]
                mod = importlib.import_module("email_reminder")
                runtime_cfg = getattr(app, "_get_email_runtime_config", lambda: {})()
                cfg = {
                    "from_email": runtime_cfg.get("from_email", _from_val),
                    "smtp_server": runtime_cfg.get("smtp_server", "smtp.gmail.com") or "smtp.gmail.com",
                    "smtp_port": int(runtime_cfg.get("smtp_port", 587) or 587),
                    "username": runtime_cfg.get("from_email", _from_val),
                    "password": runtime_cfg.get("password", _pass_val),
                }
                to_email = runtime_cfg.get("to_email", _to_val)
                if not to_email or not cfg["from_email"] or not cfg["password"]:
                    raise ValueError("Recipient email, sender email, and Gmail app password are required.")
                days = int(_days_val or 7)
                apps = mod.check_pending_applications(_get_tracker_path(), days)
                if not apps:
                    print(f"No applications pending for {days}+ days. All good!")
                else:
                    print(f"Found {len(apps)} pending applications. Sending reminders...")
                    mod.send_reminder_email(to_email, apps, cfg)
                    print(f"\n[DONE] {len(apps)} pending reminder(s) sent.")
            except Exception as e:
                import traceback
                print(f"[!] Error: {e}\n"); print(traceback.format_exc())
            finally:
                sys.stdout = old
        run_in_thread(task, name="email_send")

    styled_button(form, t("email.send_now"), send_reminders,
                  color=ACCENT3, width=24).pack(anchor="w", pady=12)
    out.pack(fill="both", expand=True, padx=24, pady=(0, 16))


# ════════════════════════════════════════════════════════════════════════════
# TAB 6 - NOTION SYNC
# ════════════════════════════════════════════════════════════════════════════

def build_notion_tab(frame):
    frame.config(bg=BG)
    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("notion.title"), color=ACCENT, bg=BG)
    section_sub(hdr, t("notion.subtitle"), bg=BG)

    api_cfg = _load_settings_cfg().get("api", {})

    c_outer, form = card(frame, padx=24, pady=20)
    c_outer.pack(fill="x", padx=24, pady=(0, 12))

    api_entry = field(form, "Notion API Key", api_cfg.get("notion_token", "secret_..."))
    db_entry  = field(form, "Notion Database ID", api_cfg.get("notion_database_id", "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"))

    tk.Label(form,
             text=t("notion.tip"),
             font=F_TINY(), fg=TEXT3, bg=SURFACE, wraplength=500, justify="left"
             ).pack(anchor="w", pady=(6, 0))

    out = output_box(frame, height=14)

    def do_sync():
        api = api_entry.get().strip() or _get_saved_api_value("notion_token", "")
        db  = db_entry.get().strip() or _get_saved_api_value("notion_database_id", "")
        if len(api) < 20 or len(db) < 20:
            show_toast(frame.winfo_toplevel(), "Please enter a valid Notion API Key and Database ID", "warning", 3500)
            return
        clear_output(out)
        old = sys.stdout; sys.stdout = OutputRedirector(out)
        def task():
            try:
                import importlib
                if "sync_notion" in sys.modules: del sys.modules["sync_notion"]
                mod = importlib.import_module("sync_notion")
                if hasattr(mod, "sync_to_notion"):
                    mod.sync_to_notion(_get_tracker_path(), api, db)
                else:
                    print("[!] sync_notion.py does not expose sync_to_notion().")
            except Exception as e:
                import traceback
                print(f"[!] Error: {e}\n"); print(traceback.format_exc())
            finally:
                sys.stdout = old
        run_in_thread(task, name="notion_sync")

    styled_button(form, t("notion.sync_now"), do_sync,
                  color=TEXT, width=24).pack(anchor="w", pady=12)
    out.pack(fill="both", expand=True, padx=24, pady=(0, 16))


# ════════════════════════════════════════════════════════════════════════════
# TAB 7 - COVER LETTER GENERATOR
# ════════════════════════════════════════════════════════════════════════════

def build_cover_letter_tab(frame):
    frame.config(bg=BG)
    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("cover.title"), color=ACCENT2, bg=BG)
    section_sub(hdr, t("cover.subtitle"), bg=BG)

    cfg = _load_settings_cfg()
    profile_cfg = cfg.get("profile", {})
    api_cfg = cfg.get("api", {})
    target_companies = [c.strip() for c in str(profile_cfg.get("target_companies", "") or "").split(",") if c.strip()]

    panes = tk.PanedWindow(frame, orient="horizontal", bg=BG, sashwidth=8,
                           sashrelief="flat", bd=0)
    panes.pack(fill="both", expand=True, padx=24, pady=(0, 8))

    lc_out, left  = card(panes, padx=20, pady=16)
    rc_out, right = card(panes, padx=20, pady=16)
    panes.add(lc_out, minsize=310)
    panes.add(rc_out, minsize=340)

    name_e    = field(left, t("cover.your_name"), profile_cfg.get("full_name", "") or "Your Name")
    company_e = field(left, t("cover.target_company"), target_companies[0] if target_companies else "Google")
    role_e    = field(left, t("cover.target_role"), profile_cfg.get("current_role", "") or "Senior Python Developer")
    years_e   = field(left, t("cover.years"), profile_cfg.get("years_exp", "") or "3")
    field_e   = field(left, t("cover.field"), profile_cfg.get("field", "") or "backend development")

    tk.Label(left, text=t("cover.tone"), font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(10, 4))
    tone_var = tk.StringVar(value="professional")
    tone_row = tk.Frame(left, bg=SURFACE)
    tone_row.pack(anchor="w")
    for tone in ["professional", "enthusiastic", "concise"]:
        tk.Radiobutton(tone_row, text=tone.title(), variable=tone_var, value=tone,
                       bg=SURFACE, fg=TEXT, selectcolor=SURFACE2, activebackground=SURFACE,
                       font=F_SMALL()).pack(side="left", padx=(0, 12))

    api_e = field(left, t("cover.api_key_hint"), api_cfg.get("openai_key", "") or _get_saved_api_value("openai_key", ""), show="*")
    tk.Label(left, text=t("cover.api_note"),
             font=F_TINY(), fg=ACCENT2, bg=SURFACE).pack(anchor="w", pady=(2, 0))

    notes_box = field(left, t("cover.notes"), height=3)

    # Right side
    tk.Label(right, text=t("cover.jd_label"), font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(0, 4))
    jd_box = tk.Text(right, height=9, font=F_SMALL(), bg=SURFACE2, fg=TEXT,
                     insertbackground=TEXT, relief="flat", wrap="word",
                     highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
    jd_box.pack(fill="x")

    tk.Label(right, text=t("cover.generated"), font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(12, 4))
    out_box = scrolledtext.ScrolledText(
        right, height=14, font=F_SMALL(),
        bg=SURFACE2, fg=TEXT, relief="flat", wrap="word",
        highlightthickness=1, highlightbackground=BORDER,
        state="disabled"
    )
    out_box.pack(fill="both", expand=True)

    live_lbl = tk.Label(right, text="Live Preview (Offline)", font=F_TINY(),
                        fg=ACCENT3, bg=SURFACE)
    live_lbl.pack(anchor="w", pady=(4, 0))

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", padx=24, pady=(8, 14))

    status_lbl = tk.Label(btn_row, text="", font=F_SMALL(), fg=TEXT3, bg=BG)
    _cl_debounce_id = [None]

    def set_out(text):
        out_box.config(state="normal")
        out_box.delete("1.0", "end")
        out_box.insert("end", text)
        out_box.config(state="disabled")

    def do_generate():
        if _cl_debounce_id[0]:
            frame.after_cancel(_cl_debounce_id[0])
            _cl_debounce_id[0] = None
        company = company_e.get().strip() or "the company"
        role    = role_e.get().strip()    or "the role"
        name    = name_e.get().strip()    or "Your Name"
        years   = years_e.get().strip()   or "3"
        field   = field_e.get().strip()   or "software development"
        tone    = tone_var.get()
        api_key = api_e.get().strip() or _get_saved_api_value("openai_key", "")
        jd_text = jd_box.get("1.0", "end").strip()
        notes   = notes_box.get("1.0", "end").strip()

        if not jd_text:
            show_toast(frame.winfo_toplevel(), "Please paste a job description first", "warning", 3000)
            return

        set_out("Generating...")
        status_lbl.config(text="Working...")

        def task():
            try:
                import importlib
                if "cover_letter_generator" in sys.modules:
                    del sys.modules["cover_letter_generator"]
                mod = importlib.import_module("cover_letter_generator")
                letter = mod.generate(
                    company=company, role=role, jd_text=jd_text,
                    your_name=name, years=years, field=field,
                    tone=tone, extra_notes=notes, api_key=api_key
                )
                set_out(letter)
                status_lbl.config(text="Done! Edit the letter above, then Save.")
            except Exception as e:
                import traceback
                set_out(f"Error: {e}\n\n{traceback.format_exc()}")
                status_lbl.config(text="Error - see output")

        run_in_thread(task, name="cover_letter_gen")

    def do_save():
        letter = out_box.get("1.0", "end").strip()
        if not letter or letter == "Generating...":
            show_toast(frame.winfo_toplevel(), "Generate a letter first", "warning", 2500)
            return
        _base = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(_base, "cover_letters")
        os.makedirs(out_dir, exist_ok=True)
        import re as _re
        safe = _re.sub(r'[^a-zA-Z0-9_-]', '_',
                       f"{company_e.get().strip()}_{role_e.get().strip()}")
        from datetime import datetime as _dt
        path = os.path.join(out_dir, f"CoverLetter_{safe}_{_dt.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(letter)
        show_toast(frame.winfo_toplevel(), f"Cover letter saved", "success", 2500)

    def do_copy():
        letter = out_box.get("1.0", "end").strip()
        if letter:
            frame.clipboard_clear()
            frame.clipboard_append(letter)
            status_lbl.config(text="Copied to clipboard!")

    styled_button(btn_row, "Generate Letter", do_generate, color=ACCENT2, width=18).pack(side="left", padx=(0, 8))
    styled_button(btn_row, "Save as .txt",    do_save,     color=ACCENT,  width=14).pack(side="left", padx=(0, 8))
    styled_button(btn_row, t("cover.copy_clipboard"),do_copy,    color=TEXT3,   width=18).pack(side="left", padx=(0, 12))
    status_lbl.pack(side="left")

    def _live_preview():
        api_key = api_e.get().strip() or _get_saved_api_value("openai_key", "")
        if api_key:
            live_lbl.config(text="AI Mode — click Generate Letter", fg=ACCENT2)
            return
        try:
            import cover_letter_generator as clg
            jd_text = jd_box.get("1.0", "end").strip()
            if not jd_text:
                return
            letter = clg.generate_offline(
                company=company_e.get().strip() or "the company",
                role=role_e.get().strip() or "the role",
                jd_text=jd_text,
                your_name=name_e.get().strip() or "Your Name",
                years=years_e.get().strip() or "3",
                field=field_e.get().strip() or "software development",
                tone=tone_var.get(),
                extra_notes=notes_box.get("1.0", "end").strip(),
            )
            set_out(letter)
            live_lbl.config(text="Live Preview (Offline)", fg=ACCENT3)
        except Exception:
            pass

    def _debounced_preview():
        if _cl_debounce_id[0]:
            frame.after_cancel(_cl_debounce_id[0])
        _cl_debounce_id[0] = frame.after(800, _live_preview)

    for e in (name_e, company_e, role_e, years_e, field_e):
        e.bind("<KeyRelease>", lambda _: _debounced_preview(), add="+")
    jd_box.bind("<KeyRelease>", lambda _: _debounced_preview(), add="+")
    notes_box.bind("<KeyRelease>", lambda _: _debounced_preview(), add="+")
    api_e.bind("<KeyRelease>", lambda _: _debounced_preview(), add="+")
    tone_var.trace_add("write", lambda *_: _debounced_preview())
    _live_preview()


# ════════════════════════════════════════════════════════════════════════════
# TAB 8 — INTERVIEW PREP TIMER & SCORECARD
# ════════════════════════════════════════════════════════════════════════════

def build_interview_tab(frame):
    frame.config(bg=BG)
    import time as _time
    import random

    try:
        import interview_prep as ip
        categories = ip.get_categories()
    except Exception:
        ip = None
        categories = ["Behavioral (STAR)", "Technical / Problem Solving",
                      "Motivation & Culture Fit", "Salary & Logistics"]

    CAT_COLORS = [ACCENT4, ACCENT, ACCENT2, ACCENT3]
    SCORE_COLORS_MAP = {1: DANGER, 2: ACCENT3, 3: ACCENT3, 4: ACCENT, 5: ACCENT2}

    # ── State ────────────────────────────────────────────────────────────────
    _state = {
        "cat":        categories[0],
        "question":   None,
        "q_count":    0,
        "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timer_on":   False,
        "t_start":    0.0,
        "elapsed":    0.0,
        "awaiting":   False,   # True = question shown, waiting for answer
    }

    def _load_interview_settings():
        cfg = {
            "default_category": categories[0],
            "auto_start_timer": True,
            "min_word_warning": 50,
            "show_follow_ups": True,
            "show_tips": True,
            "save_history": True,
        }
        cfg.update(_load_settings_cfg().get("interview", {}))
        if cfg.get("default_category") not in categories:
            cfg["default_category"] = categories[0]
        return cfg

    # ════════════════════════════════════════════════════════════════════════
    # TOP BAR: category + session stats
    # ════════════════════════════════════════════════════════════════════════
    top_bar = tk.Frame(frame, bg=SIDEBAR_BG)
    top_bar.pack(fill="x")

    # interviewer badge
    badge_f = tk.Frame(top_bar, bg=SIDEBAR_BG)
    badge_f.pack(side="left", padx=20, pady=12)
    tk.Label(badge_f, text="AI", font=F_SECTION(),
             fg=BG, bg=ACCENT4, width=3, pady=4).pack(side="left")
    info_f = tk.Frame(badge_f, bg=SIDEBAR_BG)
    info_f.pack(side="left", padx=10)
    tk.Label(info_f, text=t("interview.interviewer"),
             font=F_LABEL(), fg=TEXT, bg=SIDEBAR_BG).pack(anchor="w")
    tk.Label(info_f, text=t("interview.session_info"),
             font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG).pack(anchor="w")

    # session counter (right side)
    sess_f = tk.Frame(top_bar, bg=SIDEBAR_BG)
    sess_f.pack(side="right", padx=20)
    q_counter_lbl = tk.Label(sess_f, text="Q: 0  |  Avg: —",
                              font=F_SMALL(), fg=TEXT3, bg=SIDEBAR_BG)
    q_counter_lbl.pack(side="right")

    tk.Frame(frame, bg=BORDER, height=1).pack(fill="x")

    # ════════════════════════════════════════════════════════════════════════
    # CATEGORY SELECTOR
    # ════════════════════════════════════════════════════════════════════════
    cat_bar = tk.Frame(frame, bg=BG)
    cat_bar.pack(fill="x", padx=20, pady=(12, 4))
    tk.Label(cat_bar, text="CATEGORY:", font=F_TINY_B(),
             fg=TEXT3, bg=BG).pack(side="left", padx=(0, 10))

    _cat_btns = {}

    def _select_cat(cat):
        _state["cat"] = cat
        for c, b in _cat_btns.items():
            idx = categories.index(c)
            if c == cat:
                b.config(bg=CAT_COLORS[idx % len(CAT_COLORS)],
                         fg=BG, font=F_SMALL_B())
            else:
                b.config(bg=SURFACE2, fg=TEXT2, font=F_SMALL())

    for i, cat in enumerate(categories):
        col = CAT_COLORS[i % len(CAT_COLORS)]
        b = tk.Button(cat_bar, text=cat,
                      font=F_SMALL(), bg=SURFACE2, fg=TEXT2,
                      relief="flat", cursor="hand2", padx=12, pady=6, bd=0,
                      activebackground=col, activeforeground=BG,
                      command=lambda c=cat: _select_cat(c))
        b.pack(side="left", padx=(0, 6))
        _cat_btns[cat] = b

    _select_cat(_load_interview_settings().get("default_category", categories[0]))

    # ════════════════════════════════════════════════════════════════════════
    # MAIN LAYOUT: chat pane (left) | scoreboard (right)
    # ════════════════════════════════════════════════════════════════════════
    main_f = tk.Frame(frame, bg=BG)
    main_f.pack(fill="both", expand=True, padx=20, pady=(8, 12))

    chat_f = tk.Frame(main_f, bg=BG)
    chat_f.pack(side="left", fill="both", expand=True, padx=(0, 12))

    right_f = tk.Frame(main_f, bg=BG, width=230)
    right_f.pack(side="right", fill="y")
    right_f.pack_propagate(False)

    # ────────────────────────────────────────────────────────────────────────
    # CHAT LOG (read-only scrolled text with custom tags)
    # ────────────────────────────────────────────────────────────────────────
    chat_log = scrolledtext.ScrolledText(
        chat_f, font=F_BODY(), bg=SURFACE, fg=TEXT,
        relief="flat", wrap="word", state="disabled", height=14,
        highlightthickness=1, highlightbackground=BORDER,
        insertbackground=ACCENT, padx=14, pady=10,
        selectbackground=ACCENT, selectforeground=BG
    )
    chat_log.pack(fill="both", expand=True, pady=(0, 8))

    # configure tags
    chat_log.tag_config("interviewer_name", foreground=ACCENT4, font=F_SMALL_B())
    chat_log.tag_config("interviewer_msg",  foreground=TEXT,    font=F_BODY())
    chat_log.tag_config("question_text",    foreground=TEXT,    font=F_SUB_B())
    chat_log.tag_config("follow_up",        foreground=ACCENT3, font=F_BODY_I())
    chat_log.tag_config("you_name",         foreground=ACCENT2, font=F_SMALL_B())
    chat_log.tag_config("you_msg",          foreground=TEXT2,   font=F_BODY())
    chat_log.tag_config("score_good",       foreground=ACCENT2, font=F_LABEL())
    chat_log.tag_config("score_mid",        foreground=ACCENT3, font=F_LABEL())
    chat_log.tag_config("score_bad",        foreground=DANGER,  font=F_LABEL())
    chat_log.tag_config("feedback_line",    foreground=TEXT2,   font=F_SMALL())
    chat_log.tag_config("separator",        foreground=BORDER,  font=F_TINY())
    chat_log.tag_config("tip_text",         foreground=ACCENT3, font=F_SMALL_I())

    def _chat_append(text, tag="interviewer_msg", newline=True):
        chat_log.config(state="normal")
        chat_log.insert("end", (text + "\n") if newline else text, tag)
        chat_log.see("end")
        chat_log.config(state="disabled")

    def _chat_clear():
        chat_log.config(state="normal")
        chat_log.delete("1.0", "end")
        chat_log.config(state="disabled")

    # Welcome message
    _chat_append("Alex  (Senior Hiring Manager)", "interviewer_name")
    _chat_append("Welcome! I'll be conducting your mock interview today.", "interviewer_msg")
    _chat_append("Select a category above and click  \"Next Question\"  to begin.", "interviewer_msg")
    _chat_append("Type your answer in the box below and press  \"Submit Answer\".", "interviewer_msg")
    _chat_append("─" * 55, "separator")

    # ────────────────────────────────────────────────────────────────────────
    # TIMER strip
    # ────────────────────────────────────────────────────────────────────────
    timer_strip = tk.Frame(chat_f, bg=SURFACE, height=42)
    timer_strip.pack(fill="x", pady=(0, 6))
    timer_strip.pack_propagate(False)

    timer_var = tk.StringVar(value="0:00")
    timer_lbl = tk.Label(timer_strip, textvariable=timer_var,
                         font=F_HERO(), fg=ACCENT, bg=SURFACE)
    timer_lbl.pack(side="left", padx=14)
    timer_hint = tk.Label(timer_strip, text="Answer time",
                          font=F_TINY(), fg=TEXT3, bg=SURFACE)
    timer_hint.pack(side="left")

    def _tick():
        if _state["timer_on"]:
            _state["elapsed"] = _time.time() - _state["t_start"]
            s = int(_state["elapsed"])
            timer_var.set(f"{s//60}:{s%60:02d}")
            color = DANGER if s > 120 else ACCENT3 if s > 60 else ACCENT
            timer_lbl.config(fg=color)
            frame.after(250, _tick)

    def _start_timer():
        _state["t_start"] = _time.time() - _state["elapsed"]
        _state["timer_on"] = True
        _tick()

    def _stop_timer():
        _state["timer_on"] = False

    def _reset_timer():
        _state["timer_on"] = False
        _state["elapsed"]  = 0.0
        timer_var.set("0:00")
        timer_lbl.config(fg=ACCENT)

    tbtn_f = tk.Frame(timer_strip, bg=SURFACE)
    tbtn_f.pack(side="right", padx=10)
    tk.Button(tbtn_f, text="▶", font=F_BODY(), bg=ACCENT2, fg=BG,
              relief="flat", cursor="hand2", padx=8, pady=4, bd=0,
              command=_start_timer).pack(side="left", padx=2)
    tk.Button(tbtn_f, text="■", font=F_BODY(), bg=SURFACE2, fg=TEXT2,
              relief="flat", cursor="hand2", padx=8, pady=4, bd=0,
              command=_stop_timer).pack(side="left", padx=2)
    tk.Button(tbtn_f, text="↺", font=F_BODY(), bg=SURFACE2, fg=TEXT2,
              relief="flat", cursor="hand2", padx=8, pady=4, bd=0,
              command=_reset_timer).pack(side="left", padx=2)

    # ────────────────────────────────────────────────────────────────────────
    # ANSWER INPUT BOX
    # ────────────────────────────────────────────────────────────────────────
    answer_box = tk.Text(chat_f, font=F_BODY(), bg=SURFACE2, fg=TEXT,
                         insertbackground=ACCENT, relief="flat", height=5,
                         wrap="word", highlightthickness=1,
                         highlightbackground=BORDER, highlightcolor=ACCENT,
                         padx=10, pady=8)
    answer_box.pack(fill="x", pady=(0, 6))

    placeholder_text = "Type your answer here... (Ctrl+Enter to submit)"

    def _set_placeholder():
        answer_box.delete("1.0", "end")
        answer_box.insert("1.0", placeholder_text)
        answer_box.config(fg=TEXT3)

    def _clear_placeholder(event=None):
        if answer_box.get("1.0", "end").strip() == placeholder_text:
            answer_box.delete("1.0", "end")
            answer_box.config(fg=TEXT)

    _set_placeholder()
    answer_box.bind("<FocusIn>", _clear_placeholder)

    # ────────────────────────────────────────────────────────────────────────
    # BOTTOM BUTTON ROW
    # ────────────────────────────────────────────────────────────────────────
    btn_row = tk.Frame(chat_f, bg=BG)
    btn_row.pack(fill="x")

    # ── Core actions ────────────────────────────────────────────────────────
    def next_question():
        cat = _state["cat"]
        live_cfg = _load_interview_settings()
        try:
            import interview_prep as _ip
            qs  = _ip.get_questions(cat)
            tip = _ip.get_tip(cat)
        except Exception:
            qs  = ["Tell me about yourself."]
            tip = ""

        q = random.choice(qs)
        _state["question"] = q
        _state["q_count"] += 1
        _state["awaiting"] = True
        _reset_timer()
        _set_placeholder()
        answer_box.config(state="normal")

        # post to chat
        _chat_append(f"\nAlex  (Q{_state['q_count']}  •  {cat})", "interviewer_name")
        _chat_append(q, "question_text")
        if tip and live_cfg.get("show_tips", True):
            _chat_append(f"Tip: {tip}", "tip_text")
        _chat_append("", "interviewer_msg")

        if live_cfg.get("auto_start_timer", True):
            _start_timer()
        answer_box.focus_set()

    def submit_answer(event=None):
        answer = answer_box.get("1.0", "end").strip()
        if not answer or answer == placeholder_text:
            show_toast(frame.winfo_toplevel(), "Please type your answer first", "warning", 2500)
            return
        if not _state["question"]:
            show_toast(frame.winfo_toplevel(), "Click 'Next Question' first", "warning", 2500)
            return

        _stop_timer()
        elapsed = round(_state["elapsed"], 1)

        # Show user answer in chat
        _chat_append("You", "you_name")
        _chat_append(answer, "you_msg")
        _chat_append("", "you_msg")

        # Analyze
        try:
            import interview_prep as _ip
            result = _ip.analyze_answer(
                question=_state["question"],
                answer=answer,
                category=_state["cat"],
                elapsed_s=elapsed,
            )
        except Exception as ex:
            _chat_append(f"[Analysis error: {ex}]", "score_bad")
            return

        score  = result["score"]
        sc_tag = "score_good" if score >= 4 else "score_mid" if score >= 3 else "score_bad"
        live_cfg = _load_interview_settings()

        # Interviewer feedback
        _chat_append(f"Alex  (Feedback)", "interviewer_name")
        _chat_append(result["reaction"], "interviewer_msg")
        _chat_append(f"\nScore: {score}/5 — {result['label']}  |  Time: {elapsed}s  |  Words: {result['word_count']}",
                     sc_tag)
        _chat_append("", "feedback_line")
        for line in result["feedback"]:
            _chat_append(f"  {line}", "feedback_line")

        min_words = int(live_cfg.get("min_word_warning", 50) or 50)
        if result.get("word_count", 0) < min_words:
            _chat_append(f"\nShort answer warning: aim for at least {min_words} words for this practice mode.", "score_mid")

        if live_cfg.get("show_follow_ups", True) and result.get("follow_up"):
            _chat_append(f"\nFollow-up: {result['follow_up']}", "follow_up")

        _chat_append("\n" + "─" * 55, "separator")

        # Update counter
        _update_counter(score)

        # Save to file
        if live_cfg.get("save_history", True):
            try:
                import interview_prep as _ip
                _ip.save_score({
                    "question":   _state["question"],
                    "category":   _state["cat"],
                    "score":      score,
                    "elapsed_s":  elapsed,
                    "session_id": _state["session_id"],
                    "date":       datetime.now().isoformat(),
                    "word_count": result["word_count"],
                })
            except Exception:
                pass

        _state["question"] = None
        _state["awaiting"] = False
        _reset_timer()
        _set_placeholder()
        refresh_scoreboard()

    # Ctrl+Enter to submit
    answer_box.bind("<Control-Return>", submit_answer)

    styled_button(btn_row, t("interview.next_arrow"), next_question,
                  color=ACCENT4, width=18).pack(side="left", padx=(0, 8))
    styled_button(btn_row, t("interview.submit_check"), submit_answer,
                  color=ACCENT2, width=18).pack(side="left", padx=(0, 8))
    ghost_button(btn_row, t("interview.clear_chat"), _chat_clear, width=12).pack(side="left")

    # ════════════════════════════════════════════════════════════════════════
    # RIGHT: Scoreboard panel
    # ════════════════════════════════════════════════════════════════════════
    tk.Label(right_f, text="Session Stats", font=F_SUB_B(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 8))

    sb_out, sb_in = plain_card(right_f, padx=16, pady=14)
    sb_out.pack(fill="x", pady=(0, 10))

    _session_scores = []

    def _update_counter(score):
        _session_scores.append(score)
        avg = round(sum(_session_scores) / len(_session_scores), 1)
        color = ACCENT2 if avg >= 4 else ACCENT3 if avg >= 3 else DANGER
        q_counter_lbl.config(
            text=f"Q: {len(_session_scores)}  |  Avg: {avg}/5",
            fg=color
        )

    sb_vals = {}
    for key, label, color in [
        ("total",    "All-time questions", ACCENT),
        ("avg_all",  "All-time avg score", ACCENT2),
        ("sessions", "Sessions",           ACCENT4),
    ]:
        r = tk.Frame(sb_in, bg=SURFACE)
        r.pack(fill="x", pady=4)
        tk.Label(r, text=label, font=F_SMALL(), fg=TEXT3,
                 bg=SURFACE, anchor="w").pack(side="left")
        v = tk.Label(r, text="—", font=F_LABEL(),
                     fg=color, bg=SURFACE)
        v.pack(side="right")
        sb_vals[key] = v

    tk.Frame(sb_in, bg=BORDER, height=1).pack(fill="x", pady=(8, 8))

    # Per-category scores
    tk.Label(sb_in, text="BY CATEGORY", font=F_MICRO(),
             fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(0, 4))
    cat_lbls = {}
    for i, cat in enumerate(categories):
        r = tk.Frame(sb_in, bg=SURFACE)
        r.pack(fill="x", pady=2)
        short = cat.split("(")[0].strip()[:14]
        tk.Label(r, text=short, font=F_TINY(), fg=TEXT3,
                 bg=SURFACE, anchor="w").pack(side="left")
        v = tk.Label(r, text="—", font=F_SMALL_B(),
                     fg=CAT_COLORS[i % len(CAT_COLORS)], bg=SURFACE)
        v.pack(side="right")
        cat_lbls[cat] = v

    def refresh_scoreboard():
        try:
            import interview_prep as _ip
            s = _ip.get_summary()
            if not s:
                return
            sb_vals["total"].config(text=str(s.get("total_answers", 0)))
            sb_vals["avg_all"].config(text=f"{s.get('overall_avg', 0)}/5")
            sb_vals["sessions"].config(text=str(s.get("sessions", 0)))
            by_cat = s.get("by_category", {})
            for cat, lbl in cat_lbls.items():
                val = by_cat.get(cat)
                lbl.config(text=f"{val}/5" if val else "—")
        except Exception:
            pass

    def poll_scoreboard():
        refresh_scoreboard()
        if frame.winfo_exists():
            frame.after(5000, poll_scoreboard)

    ghost_button(right_f, "Refresh Stats", refresh_scoreboard, width=18).pack(anchor="w", pady=(4, 10))

    # Tips card
    tip_out, tip_in = plain_card(right_f, padx=14, pady=12)
    tip_out.pack(fill="x")
    tk.Label(tip_in, text="QUICK TIPS", font=F_TINY_B(),
             fg=ACCENT3, bg=SURFACE).pack(anchor="w", pady=(0, 6))
    tips_text = [
        "• STAR: Situation → Task → Action → Result",
        "• Aim for 90-120 seconds per answer",
        "• Use numbers/metrics whenever possible",
        "• Avoid vague phrases like 'I always...'",
        "• Ctrl+Enter to submit your answer",
    ]
    for tip in tips_text:
        tk.Label(tip_in, text=tip, font=F_TINY(), fg=TEXT2,
                 bg=SURFACE, anchor="w", justify="left", wraplength=200).pack(anchor="w", pady=1)

    frame.after(900, poll_scoreboard)
    frame._refresh_data = refresh_scoreboard


# ════════════════════════════════════════════════════════════════════════════
# TAB 9 — LINKEDIN MESSAGE GENERATOR
# ════════════════════════════════════════════════════════════════════════════

def build_linkedin_tab(frame):
    frame.config(bg=BG)

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("linkedin.title"), color=ACCENT, bg=BG)
    section_sub(hdr, t("linkedin.subtitle"), bg=BG)

    panes = tk.PanedWindow(frame, orient="horizontal", bg=BG, sashwidth=8,
                           sashrelief="flat", bd=0)
    panes.pack(fill="both", expand=True, padx=24, pady=(0, 8))

    lc_out, left  = card(panes, padx=20, pady=16)
    rc_out, right = card(panes, padx=20, pady=16)
    panes.add(lc_out, minsize=310)
    panes.add(rc_out, minsize=340)

    # ── Message type picker ─────────────────────────────────────────────────
    try:
        import linkedin_message_generator as lmg
        msg_types = lmg.get_message_types()
    except Exception:
        msg_types = ["Cold Connection", "Referral Request",
                     "Follow-Up After Applying", "Thank-You After Interview", "Reconnecting"]

    tk.Label(left, text="Message Type", font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(0, 3))
    type_var = tk.StringVar(value=msg_types[0])
    desc_lbl = tk.Label(left, text="", font=F_TINY_I(), fg=ACCENT3,
                        bg=SURFACE, wraplength=280, justify="left")

    def on_type_change(*_):
        try:
            import linkedin_message_generator as lmg
            desc_lbl.config(text=lmg.get_description(type_var.get()))
            lim = lmg.get_char_limit(type_var.get())
            char_lbl.config(text=f"LinkedIn limit: {lim} chars")
        except Exception:
            pass

    type_menu = ttk.Combobox(left, textvariable=type_var, values=msg_types,
                              state="readonly", font=F_BODY(), width=34)
    type_menu.pack(fill="x", ipady=4)
    type_menu.bind("<<ComboboxSelected>>", lambda _: on_type_change())
    desc_lbl.pack(anchor="w", pady=(4, 8))

    # ── Input fields ────────────────────────────────────────────────────────
    your_name_e  = field(left, t("cover.your_name"), "Alex Johnson")
    your_role_e  = field(left, t("cover.target_role"), "Senior Python Developer")
    your_field_e = field(left, t("cover.field"), "backend development")
    years_e      = field(left, t("cover.years"), "5")
    first_name_e = field(left, t("linkedin.recipient_name"), "Sarah")
    company_e    = field(left, t("linkedin.company"), "Google")
    target_role_e= field(left, t("linkedin.target_role_opt"), "Staff Engineer")
    highlight_e  = field(left, t("linkedin.highlight"), "building distributed systems")

    # ── Right: output ───────────────────────────────────────────────────────
    tk.Label(right, text="Generated Message", font=F_SMALL(),
             fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(0, 4))
    out_box = scrolledtext.ScrolledText(
        right, font=F_BODY(), bg=SURFACE2, fg=TEXT,
        relief="flat", wrap="word", height=16,
        highlightthickness=1, highlightbackground=BORDER,
        state="disabled"
    )
    out_box.pack(fill="both", expand=True)

    char_lbl = tk.Label(right, text="LinkedIn limit: 300 chars",
                        font=F_TINY(), fg=TEXT3, bg=SURFACE)
    char_lbl.pack(anchor="w", pady=(4, 0))
    count_lbl = tk.Label(right, text="0 characters",
                         font=F_TINY(), fg=ACCENT3, bg=SURFACE)
    count_lbl.pack(anchor="w")

    on_type_change()

    def set_out(text):
        out_box.config(state="normal")
        out_box.delete("1.0", "end")
        out_box.insert("end", text)
        out_box.config(state="disabled")
        count_lbl.config(text=f"{len(text)} characters",
                         fg=DANGER if len(text) > 500 else ACCENT2)

    def do_generate():
        try:
            import linkedin_message_generator as lmg
            raw_highlight = highlight_e.get().strip()
            msg = lmg.generate(
                message_type=type_var.get(),
                your_name=your_name_e.get().strip(),
                your_role=your_role_e.get().strip(),
                your_field=your_field_e.get().strip(),
                years=years_e.get().strip(),
                first_name=first_name_e.get().strip(),
                company=company_e.get().strip(),
                target_role=target_role_e.get().strip(),
                their_field=your_field_e.get().strip(),
                highlight=raw_highlight,
                reason=f"{company_e.get().strip()}'s innovative work" if company_e.get().strip() else "its innovative approach",
                shared_context=raw_highlight or "our previous workplace",
            )
            set_out(msg)
        except Exception as ex:
            set_out(f"Error: {ex}")

    def do_copy():
        txt = out_box.get("1.0", "end").strip()
        if txt:
            frame.clipboard_clear()
            frame.clipboard_append(txt)
            copy_lbl.config(text="Copied!")
            frame.after(2000, lambda: copy_lbl.config(text=""))

    def do_save():
        txt = out_box.get("1.0", "end").strip()
        if not txt:
            show_toast(frame.winfo_toplevel(), "Generate a message first", "warning", 2500)
            return
        try:
            import linkedin_message_generator as lmg
            out_dir = os.path.join(BASE_DIR, "linkedin_messages")
            path = lmg.save_message(type_var.get(), txt, out_dir)
            show_toast(frame.winfo_toplevel(), "Message saved", "success", 2500)
        except Exception as ex:
            show_toast(frame.winfo_toplevel(), str(ex), "error", 4000)

    btn_row = tk.Frame(frame, bg=BG)
    btn_row.pack(anchor="w", padx=24, pady=(8, 14))
    styled_button(btn_row, "Generate Message", do_generate, color=ACCENT,   width=18).pack(side="left", padx=(0, 8))
    styled_button(btn_row, "Copy",             do_copy,     color=ACCENT2,  width=10).pack(side="left", padx=(0, 8))
    ghost_button(btn_row,  "Save as .txt",     do_save,     width=14).pack(side="left", padx=(0, 12))
    copy_lbl = tk.Label(btn_row, text="", font=F_SMALL(), fg=ACCENT2, bg=BG)
    copy_lbl.pack(side="left")

    _li_debounce_id = [None]
    def _debounced_generate():
        if _li_debounce_id[0]:
            frame.after_cancel(_li_debounce_id[0])
        _li_debounce_id[0] = frame.after(600, do_generate)
    for e in (your_name_e, your_role_e, your_field_e, years_e,
              first_name_e, company_e, target_role_e, highlight_e):
        e.bind("<KeyRelease>", lambda _: _debounced_generate(), add="+")
    type_menu.bind("<<ComboboxSelected>>", lambda _: _debounced_generate(), add="+")
    do_generate()


# ════════════════════════════════════════════════════════════════════════════
# TAB 10 — SALARY NEGOTIATION CALCULATOR
# ════════════════════════════════════════════════════════════════════════════

def build_salary_tab(frame):
    frame.config(bg=BG)

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("salary.title"), color=ACCENT2, bg=BG)
    section_sub(hdr, t("salary.subtitle"), bg=BG)

    try:
        import salary_calculator as sc
        levels    = sc.get_levels()
        locations = sc.get_locations()
        tax_opts  = sc.get_tax_options()
    except Exception:
        levels    = ["Mid-Level (3-5 yrs)"]
        locations = ["Remote (US Average)"]
        tax_opts  = ["USA (Federal ~24%)"]

    # ── Notebook-style tabs inside the tab ──────────────────────────────────
    tab_bar = tk.Frame(frame, bg=BG)
    tab_bar.pack(fill="x", padx=24, pady=(0, 12))

    content_area = tk.Frame(frame, bg=BG)
    content_area.pack(fill="both", expand=True, padx=24)

    pages = {}
    tab_btns = {}

    def switch_page(name):
        for n, pg in pages.items():
            pg.pack_forget()
        pages[name].pack(fill="both", expand=True)
        for n, b in tab_btns.items():
            b.config(bg=ACCENT if n == name else SURFACE2,
                     fg=BG if n == name else TEXT2)

    for pg_name in ["Offer Breakdown", "Counter Strategy", "Compare Offers"]:
        pg = tk.Frame(content_area, bg=BG)
        pages[pg_name] = pg
        b = tk.Button(tab_bar, text=pg_name, font=F_LABEL(),
                      bg=SURFACE2, fg=TEXT2, relief="flat", cursor="hand2",
                      padx=16, pady=8, bd=0,
                      command=lambda n=pg_name: switch_page(n))
        b.pack(side="left", padx=(0, 4))
        tab_btns[pg_name] = b

    # ── PAGE 1: Offer Breakdown ──────────────────────────────────────────────
    p1 = pages["Offer Breakdown"]
    p1_left  = tk.Frame(p1, bg=BG)
    p1_left.pack(side="left", fill="both", expand=True, padx=(0, 12))
    p1_right = tk.Frame(p1, bg=BG)
    p1_right.pack(side="right", fill="both", expand=True)

    c1o, c1i = card(p1_left, padx=20, pady=16)
    c1o.pack(fill="x", pady=(0, 10))

    base_e    = field(c1i, t("salary.base_salary"), "120000")
    bonus_e   = field(c1i, t("salary.bonus_pct"), "10")
    equity_e  = field(c1i, t("salary.equity"), "20000")
    signing_e = field(c1i, t("salary.signing"), "10000")
    benefits_e= field(c1i, t("salary.benefits"), "12000")

    tk.Label(p1_left, text=t("salary.tax_bracket"), font=F_SMALL(), fg=TEXT3, bg=BG).pack(anchor="w", pady=(10, 3))
    tax_var = tk.StringVar(value=tax_opts[0])
    tax_menu = ttk.Combobox(p1_left, textvariable=tax_var, values=tax_opts,
                            state="readonly", font=F_BODY(), width=34)
    tax_menu.pack(fill="x", ipady=4)

    result_outer, result_inner = plain_card(p1_right, padx=20, pady=18)
    result_outer.pack(fill="x")

    result_rows = {}
    result_defs = [
        ("base",         "Base Salary"),
        ("bonus",        "Annual Bonus"),
        ("equity_annual","Annual Equity"),
        ("signing_annual","Signing (annualized)"),
        ("benefits",     "Benefits"),
        ("sep",          None),
        ("total_cash",   "Total Cash"),
        ("total_comp",   "Total Compensation"),
        ("sep2",         None),
        ("net_annual",   "Net Annual (after tax)"),
        ("net_monthly",  "Net Monthly"),
    ]
    for key, label in result_defs:
        if label is None:
            tk.Frame(result_inner, bg=BORDER, height=1).pack(fill="x", pady=8)
            continue
        r = tk.Frame(result_inner, bg=SURFACE)
        r.pack(fill="x", pady=3)
        is_total = key in ("total_comp", "net_monthly")
        tk.Label(r, text=label, font=F_LABEL() if is_total else F_BODY(),
                 fg=TEXT if is_total else TEXT2, bg=SURFACE).pack(side="left")
        v = tk.Label(r, text="—", font=F_LABEL(),
                     fg=ACCENT2 if is_total else TEXT, bg=SURFACE)
        v.pack(side="right")
        result_rows[key] = v

    def calc_breakdown(silent=False):
        try:
            import salary_calculator as sc
            base     = float(base_e.get().replace(",", "") or 0)
            bonus    = float(bonus_e.get() or 0)
            equity   = float(equity_e.get().replace(",", "") or 0)
            signing  = float(signing_e.get().replace(",", "") or 0)
            benefits = float(benefits_e.get().replace(",", "") or 0)
            tax_rate = sc.get_tax_rate(tax_var.get())
            comp = sc.calculate_total_comp(base, bonus, equity, signing, benefits)
            th   = sc.calculate_takehome(comp["total_cash"], tax_rate)
            merged = {**comp, **th}
            for key, widget in result_rows.items():
                val = merged.get(key)
                if val is not None:
                    widget.config(text=f"${val:,.0f}")
        except Exception as ex:
            if not silent:
                messagebox.showerror("Error", str(ex))

    styled_button(p1_left, t("salary.breakdown"), calc_breakdown,
                  color=ACCENT2, width=22).pack(anchor="w", pady=12)

    _bd_debounce_id = [None]
    def _debounced_breakdown():
        if _bd_debounce_id[0]:
            frame.after_cancel(_bd_debounce_id[0])
        _bd_debounce_id[0] = frame.after(500, lambda: calc_breakdown(silent=True))
    for e in (base_e, bonus_e, equity_e, signing_e, benefits_e):
        e.bind("<KeyRelease>", lambda _: _debounced_breakdown(), add="+")
    tax_menu.bind("<<ComboboxSelected>>", lambda _: calc_breakdown(silent=True), add="+")

    # ── PAGE 2: Counter Strategy ─────────────────────────────────────────────
    p2 = pages["Counter Strategy"]
    p2c_out, p2c = card(p2, padx=22, pady=18)
    p2c_out.pack(fill="x", pady=(0, 12))

    offer_e  = field(p2c, t("salary.offer_base"), "100000")
    target_e = field(p2c, t("salary.your_target"), "120000")
    walkaway_e = field(p2c, t("salary.walk_away"), "90000")

    tk.Label(p2c, text=t("salary.exp_level"), font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(12, 3))
    level_var = tk.StringVar(value=levels[1] if len(levels) > 1 else levels[0])
    lv_menu = ttk.Combobox(p2c, textvariable=level_var, values=levels,
                           state="readonly", font=F_BODY(), width=34)
    lv_menu.pack(fill="x", ipady=4)

    tk.Label(p2c, text="Location / Cost of Living", font=F_SMALL(), fg=TEXT3, bg=SURFACE).pack(anchor="w", pady=(12, 3))
    loc_var = tk.StringVar(value=locations[3] if len(locations) > 3 else locations[0])
    loc_menu = ttk.Combobox(p2c, textvariable=loc_var, values=locations,
                            state="readonly", font=F_BODY(), width=34)
    loc_menu.pack(fill="x", ipady=4)

    strat_outer, strat_inner = plain_card(p2, padx=22, pady=18)
    strat_outer.pack(fill="x")
    strat_verdict = tk.Label(strat_inner, text="Fill in the fields and click Calculate.",
                             font=F_SUB_B(), fg=ACCENT3, bg=SURFACE,
                             wraplength=600, justify="left")
    strat_verdict.pack(anchor="w")
    strat_action  = tk.Label(strat_inner, text="",
                             font=F_BODY(), fg=TEXT2, bg=SURFACE,
                             wraplength=600, justify="left")
    strat_action.pack(anchor="w", pady=(6, 0))
    strat_counter = tk.Label(strat_inner, text="",
                             font=F_SECTION(), fg=ACCENT2, bg=SURFACE)
    strat_counter.pack(anchor="w", pady=(8, 0))

    def calc_strategy(silent=False):
        try:
            import salary_calculator as sc
            r = sc.negotiation_strategy(
                offer_base=float(offer_e.get().replace(",", "") or 0),
                your_target=float(target_e.get().replace(",", "") or 0),
                walk_away=float(walkaway_e.get().replace(",", "") or 0),
                level=level_var.get(),
                location=loc_var.get(),
            )
            color = ACCENT2 if "GREAT" in r["verdict"] else ACCENT3 if "ACCEPT" in r["verdict"] else DANGER
            strat_verdict.config(text=r["verdict"], fg=color)
            strat_action.config(text=r["action"])
            strat_counter.config(text=f"Suggested Counter: ${r['counter_offer']:,.0f}"
                                      f"   |   Market Mid: ${r['market_mid']:,.0f}"
                                      f"   |   Market High: ${r['market_high']:,.0f}")
        except Exception as ex:
            if not silent:
                messagebox.showerror("Error", str(ex))

    styled_button(p2c, t("salary.strategy"), calc_strategy, color=ACCENT, width=22).pack(anchor="w", pady=12)

    _st_debounce_id = [None]
    def _debounced_strategy():
        if _st_debounce_id[0]:
            frame.after_cancel(_st_debounce_id[0])
        _st_debounce_id[0] = frame.after(500, lambda: calc_strategy(silent=True))
    for e in (offer_e, target_e, walkaway_e):
        e.bind("<KeyRelease>", lambda _: _debounced_strategy(), add="+")
    lv_menu.bind("<<ComboboxSelected>>", lambda _: calc_strategy(silent=True), add="+")
    loc_menu.bind("<<ComboboxSelected>>", lambda _: calc_strategy(silent=True), add="+")

    # ── PAGE 3: Compare Offers ───────────────────────────────────────────────
    p3 = pages["Compare Offers"]
    tk.Label(p3, text="Enter up to 3 offers to compare total compensation.",
             font=F_BODY(), fg=TEXT3, bg=BG).pack(anchor="w", pady=(0, 10))

    offers_frame = tk.Frame(p3, bg=BG)
    offers_frame.pack(fill="x")
    offer_entries = []
    for i in range(3):
        oc_out, oc = plain_card(offers_frame, padx=16, pady=14)
        oc_out.grid(row=0, column=i, padx=(0, 10), sticky="nsew")
        offers_frame.columnconfigure(i, weight=1)
        tk.Label(oc, text=f"Offer {i+1}", font=F_LABEL(),
                 fg=ACCENT, bg=SURFACE).pack(anchor="w", pady=(0, 4))
        co = field(oc, t("salary.company"), ["Startup A","Big Tech B","Scale-up C"][i])
        cb = field(oc, t("salary.base_dollar"), ["90000","130000","110000"][i])
        cx = field(oc, t("salary.bonus_pct_short"), "10")
        ce = field(oc, t("salary.equity_yr"), ["5000","30000","15000"][i])
        offer_entries.append((co, cb, cx, ce))

    result_outer3, result_inner3 = plain_card(p3, padx=20, pady=14)
    result_outer3.pack(fill="x", pady=(12, 0))
    compare_lbl = tk.Label(result_inner3, text="Click Compare to see results.",
                           font=F_BODY(), fg=TEXT3, bg=SURFACE,
                           justify="left", wraplength=700)
    compare_lbl.pack(anchor="w")

    def do_compare(silent=False):
        try:
            import salary_calculator as sc
            offers = []
            for co, cb, cx, ce in offer_entries:
                name = co.get().strip()
                base = float(cb.get().replace(",","") or 0)
                if base == 0: continue
                offers.append({"company": name, "base": base,
                                "bonus_pct": float(cx.get() or 0),
                                "equity_annual": float(ce.get().replace(",","") or 0),
                                "signing_bonus": 0, "benefits": 12000, "tax_rate": 0.24})
            if not offers:
                if not silent:
                    show_toast(frame.winfo_toplevel(), "Enter at least one offer", "warning", 2500)
                else:
                    compare_lbl.config(text="Enter at least one offer with a base salary to compare.", fg=TEXT3)
                return
            results = sc.compare_offers(offers)
            lines = []
            medals = ["🥇", "🥈", "🥉"]
            for r in results:
                m = medals[r["rank"]-1] if r["rank"] <= len(medals) else f"#{r['rank']}"
                lines.append(
                    f"{m}  {r['company']:<20}  "
                    f"Total Comp: ${r['total_comp']:>10,.0f}   "
                    f"Net/Month: ${r['net_monthly']:>8,.0f}"
                )
            compare_lbl.config(text="\n".join(lines), fg=TEXT)
        except Exception as ex:
            if not silent:
                messagebox.showerror("Error", str(ex))

    styled_button(p3, t("salary.compare"), do_compare, color=ACCENT, width=20).pack(anchor="w", pady=10)

    _cp_debounce_id = [None]
    def _debounced_compare():
        if _cp_debounce_id[0]:
            frame.after_cancel(_cp_debounce_id[0])
        _cp_debounce_id[0] = frame.after(500, lambda: do_compare(silent=True))
    for co, cb, cx, ce in offer_entries:
        for e in (co, cb, cx, ce):
            e.bind("<KeyRelease>", lambda _: _debounced_compare(), add="+")

    calc_breakdown(silent=True)
    calc_strategy(silent=True)
    do_compare(silent=True)

    switch_page("Offer Breakdown")


# ════════════════════════════════════════════════════════════════════════════
# TAB 11 — JOB SEARCH GOALS & STREAK TRACKER
# ════════════════════════════════════════════════════════════════════════════

def build_streak_tab(frame):
    frame.config(bg=BG)

    streak_cfg = {}
    try:
        import streak_tracker as _st
        streak_cfg = _st.get_data()
    except Exception:
        streak_cfg = {
            "daily_goal": _load_settings_cfg().get("goals", {}).get("daily_apps", 5),
            "weekly_goal": _load_settings_cfg().get("goals", {}).get("weekly_apps", 20),
        }

    hdr = tk.Frame(frame, bg=BG)
    hdr.pack(fill="x", padx=24, pady=(20, 0))
    section_title(hdr, t("streak.title"), color=ACCENT3, bg=BG)
    section_sub(hdr, t("streak.subtitle"), bg=BG)

    body = tk.Frame(frame, bg=BG)
    body.pack(fill="both", expand=True, padx=24, pady=(0, 16))

    left  = tk.Frame(body, bg=BG)
    left.pack(side="left", fill="both", expand=True, padx=(0, 12))
    right = tk.Frame(body, bg=BG)
    right.pack(side="right", fill="both", expand=True)

    # ── Left: Log applications ───────────────────────────────────────────────
    tk.Label(left, text="Log Today's Applications", font=F_SUB_B(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 10))

    c_out, c_in = card(left, padx=20, pady=18)
    c_out.pack(fill="x", pady=(0, 12))

    count_e = field(c_in, t("streak.count_today"), "1")
    note_e  = field(c_in, t("streak.notes_opt"), height=2)

    result_lbl = tk.Label(c_in, text="", font=F_SUB_B(),
                          fg=ACCENT2, bg=SURFACE, wraplength=340, justify="left")
    result_lbl.pack(anchor="w", pady=(10, 0))
    msg_lbl = tk.Label(c_in, text="", font=F_SMALL_I(),
                       fg=ACCENT3, bg=SURFACE, wraplength=340, justify="left")
    msg_lbl.pack(anchor="w", pady=(4, 0))

    def log_apps():
        try:
            import streak_tracker as st
            n = int(count_e.get().strip() or 1)
            note = note_e.get("1.0", "end").strip()
            res = st.log_applications(n, note)
            today = res["today_count"]
            streak = res["streak"]
            color  = ACCENT2 if res["goal_hit"] else ACCENT3
            result_lbl.config(
                text=f"{today} apps today  |  Streak: {streak} days  |  Best: {res['best_streak']}",
                fg=color
            )
            msg_lbl.config(text=res["message"])
            if _refresh_ref[0]:
                _refresh_ref[0]()
            count_e.delete(0, "end")
            count_e.insert(0, "1")
            note_e.delete("1.0", "end")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    styled_button(c_in, t("streak.log"), log_apps, color=ACCENT3, width=22).pack(anchor="w", pady=(12, 0))

    # ── Goals setup ──────────────────────────────────────────────────────────
    tk.Label(left, text="Set Goals", font=F_SUB_B(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(12, 6))

    g_out, g_in = plain_card(left, padx=20, pady=14)
    g_out.pack(fill="x")

    daily_goal_e  = field(g_in, "Daily Application Goal", str(streak_cfg.get("daily_goal", 5)))
    weekly_goal_e = field(g_in, "Weekly Application Goal", str(streak_cfg.get("weekly_goal", 20)))

    def save_goals():
        try:
            import streak_tracker as st
            d = int(daily_goal_e.get().strip() or 5)
            w = int(weekly_goal_e.get().strip() or 20)
            st.set_goals(d, w)
            try:
                import settings as _settings
                _settings.set_value("goals", "daily_apps", d)
                _settings.set_value("goals", "weekly_apps", w)
            except Exception:
                pass
            show_toast(frame.winfo_toplevel(), f"Goals updated: {d}/day, {w}/week", "success", 2500)
            if _refresh_ref[0]:
                _refresh_ref[0]()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    ghost_button(g_in, "Save Goals", save_goals, width=16).pack(anchor="w", pady=(10, 0))

    _refresh_ref = [None]  # forward reference to refresh_summary

    # ── Right: Weekly summary & stats ────────────────────────────────────────
    tk.Label(right, text="This Week", font=F_SUB_B(),
             fg=TEXT, bg=BG).pack(anchor="w", pady=(0, 10))

    # Progress bars for daily and weekly goals
    prog_outer, prog_inner = plain_card(right, padx=18, pady=14)
    prog_outer.pack(fill="x", pady=(0, 12))

    # Daily progress
    daily_prog_f = tk.Frame(prog_inner, bg=SURFACE)
    daily_prog_f.pack(fill="x", pady=(0, 10))
    daily_prog_header = tk.Frame(daily_prog_f, bg=SURFACE)
    daily_prog_header.pack(fill="x")
    tk.Label(daily_prog_header, text="Today", font=F_SMALL_B(),
             fg=TEXT, bg=SURFACE).pack(side="left")
    daily_prog_lbl = tk.Label(daily_prog_header, text="0 / 5", font=F_SMALL_B(),
             fg=ACCENT, bg=SURFACE)
    daily_prog_lbl.pack(side="right")
    daily_prog_bar_container, daily_prog_bar_fill = mini_progress_bar(
        daily_prog_f, 0, 5, color=ACCENT, width=260, height=8, bg=SURFACE2)
    daily_prog_bar_container.pack(fill="x", pady=(4, 0))

    # Weekly progress
    weekly_prog_f = tk.Frame(prog_inner, bg=SURFACE)
    weekly_prog_f.pack(fill="x")
    weekly_prog_header = tk.Frame(weekly_prog_f, bg=SURFACE)
    weekly_prog_header.pack(fill="x")
    tk.Label(weekly_prog_header, text="This Week", font=F_SMALL_B(),
             fg=TEXT, bg=SURFACE).pack(side="left")
    weekly_prog_lbl = tk.Label(weekly_prog_header, text="0 / 20", font=F_SMALL_B(),
             fg=ACCENT4, bg=SURFACE)
    weekly_prog_lbl.pack(side="right")
    weekly_prog_bar_container, weekly_prog_bar_fill = mini_progress_bar(
        weekly_prog_f, 0, 20, color=ACCENT4, width=260, height=8, bg=SURFACE2)
    weekly_prog_bar_container.pack(fill="x", pady=(4, 0))

    week_outer, week_inner = plain_card(right, padx=18, pady=16)
    week_outer.pack(fill="x", pady=(0, 12))

    week_labels = {}
    for key, label, color in [
        ("week_total",  "This week",    ACCENT),
        ("weekly_goal", "Weekly goal",  TEXT3),
        ("days_active", "Active days",  ACCENT4),
        ("days_hit_goal","Goal met",    ACCENT2),
        ("streak",      "Current streak",ACCENT3),
        ("best_streak", "Best streak",  ACCENT3),
        ("total_apps",  "All-time total",TEXT),
    ]:
        r = tk.Frame(week_inner, bg=SURFACE)
        r.pack(fill="x", pady=3)
        tk.Label(r, text=label, font=F_SMALL(), fg=TEXT3, bg=SURFACE,
                 width=15, anchor="w").pack(side="left")
        v = tk.Label(r, text="—", font=F_LABEL(), fg=color, bg=SURFACE)
        v.pack(side="right")
        week_labels[key] = v

    # Tip of the day
    tip_outer, tip_inner = plain_card(right, padx=18, pady=14)
    tip_outer.pack(fill="x", pady=(0, 8))
    tk.Label(tip_inner, text="Tip of the Day", font=F_SMALL_B(),
             fg=ACCENT3, bg=SURFACE).pack(anchor="w", pady=(0, 4))
    tip_text = tk.Label(tip_inner, text="", font=F_SMALL(), fg=TEXT2, bg=SURFACE,
                        wraplength=280, justify="left")
    tip_text.pack(anchor="w")

    def refresh_summary():
        try:
            import streak_tracker as st
            s = st.get_weekly_summary()
            for key, widget in week_labels.items():
                val = s.get(key, "—")
                widget.config(text=str(val) if isinstance(val, int) else str(val))
            tip_text.config(text=s.get("tip", ""))
            # Update progress bars
            today_count = s.get("today_count", 0)
            daily_goal = s.get("daily_goal", 5)
            week_total = s.get("week_total", 0)
            weekly_goal = s.get("weekly_goal", 20)
            daily_prog_lbl.config(text=f"{today_count} / {daily_goal}")
            weekly_prog_lbl.config(text=f"{week_total} / {weekly_goal}")
            update_progress_bar(daily_prog_bar_container, daily_prog_bar_fill, today_count, daily_goal, width=260)
            update_progress_bar(weekly_prog_bar_container, weekly_prog_bar_fill, week_total, weekly_goal, width=260)
        except Exception:
            pass

    def poll_summary():
        refresh_summary()
        if frame.winfo_exists():
            frame.after(5000, poll_summary)

    _refresh_ref[0] = refresh_summary

    ghost_button(right, "Refresh", refresh_summary, width=16).pack(anchor="w")
    frame.after(700, poll_summary)
    frame._refresh_data = refresh_summary


# ════════════════════════════════════════════════════════════════════════════
# TAB 12 — SETTINGS
# ════════════════════════════════════════════════════════════════════════════

def build_settings_tab(frame):  # noqa: C901
    frame.config(bg=BG)
    frame._is_settings_tab = True

    try:
        import settings as cfg_mod
        cfg = cfg_mod.load()
    except Exception:
        cfg_mod = None
        cfg = {}

    # ── i18n helpers ─────────────────────────────────────────────────────────
    _I18N_PREFIXES = ("field.", "salary.", "btn.", "settings.", "nav.", "misc.",
                      "streak.", "interview.", "linkedin.", "status.", "home.",
                      "ats.", "jd.", "tools.", "email.", "notion.", "cover.")
    def _tl(key):
        return t(key) if any(key.startswith(p) for p in _I18N_PREFIXES) else key

    all_vars      = {}
    _label_reg    = []  # [(widget, i18n_key)]

    def _reg(widget, key):
        _label_reg.append((widget, key))
        return widget

    # ─────────────────────────────────────────────────────────────────────────
    # WIDGET HELPERS
    # ─────────────────────────────────────────────────────────────────────────
    CARD_BG  = SURFACE
    CARD_BD  = BORDER

    def lbl(parent, text_key, font=F_SMALL(), fg=TEXT3, **kw):
        txt = _tl(text_key)
        w = tk.Label(parent, text=txt, font=font, fg=fg, bg=parent["bg"], **kw)
        if any(text_key.startswith(p) for p in _I18N_PREFIXES):
            _reg(w, text_key)
        return w

    def sep(parent):
        tk.Frame(parent, bg=CARD_BD, height=1).pack(fill="x", pady=(10, 8))

    def field_row(parent, label_key, var_key, default="", show=False, width=32):
        r = tk.Frame(parent, bg=CARD_BG)
        r.pack(fill="x", pady=3)
        lbl(r, label_key, fg=TEXT3).pack(anchor="w", pady=(0, 2))
        var = tk.StringVar(master=frame, value=str(default))
        e = tk.Entry(r, textvariable=var, font=F_BODY(),
                     bg=SURFACE2, fg=TEXT, relief="flat",
                     insertbackground=ACCENT, width=width,
                     highlightthickness=1, highlightbackground=CARD_BD,
                     highlightcolor=ACCENT, show="*" if show else "")
        e.pack(fill="x", ipady=7)
        all_vars[var_key] = var
        return var

    def check_row(parent, label_key, var_key, default=True):
        r = tk.Frame(parent, bg=CARD_BG)
        r.pack(fill="x", pady=2)
        var = tk.BooleanVar(master=frame, value=bool(default))
        txt = _tl(label_key)
        cb  = tk.Checkbutton(r, text=txt, variable=var,
                             font=F_BODY(), fg=TEXT, bg=CARD_BG,
                             selectcolor=SURFACE2, activebackground=CARD_BG,
                             activeforeground=TEXT, cursor="hand2",
                             anchor="w")
        cb.pack(fill="x")
        if any(label_key.startswith(p) for p in _I18N_PREFIXES):
            _reg(cb, label_key)
        all_vars[var_key] = var
        return var

    def drop_row(parent, label_key, var_key, options, default=""):
        r = tk.Frame(parent, bg=CARD_BG)
        r.pack(fill="x", pady=3)
        lbl(r, label_key, fg=TEXT3).pack(anchor="w", pady=(0, 2))
        var = tk.StringVar(master=frame, value=default or (options[0] if options else ""))
        cb  = ttk.Combobox(r, textvariable=var, values=options,
                           state="readonly", font=F_BODY(), width=30)
        cb.pack(fill="x", ipady=5)
        all_vars[var_key] = var
        return var

    def spin_row(parent, label_key, var_key, from_=1, to=100, default=5):
        r = tk.Frame(parent, bg=CARD_BG)
        r.pack(fill="x", pady=3)
        lbl(r, label_key, fg=TEXT3).pack(anchor="w", pady=(0, 2))
        var = tk.StringVar(master=frame, value=str(default))
        sb  = tk.Spinbox(r, from_=from_, to=to, textvariable=var,
                         font=F_BODY(), bg=SURFACE2, fg=TEXT,
                         relief="flat", buttonbackground=SURFACE2,
                         highlightthickness=1, highlightbackground=CARD_BD,
                         width=8)
        sb.pack(anchor="w", ipady=5)
        all_vars[var_key] = var
        return var

    def section_title_row(parent, text_key, color=ACCENT):
        f = tk.Frame(parent, bg=CARD_BG)
        f.pack(fill="x", pady=(0, 12))
        txt = _tl(text_key)
        lw  = tk.Label(f, text=txt, font=F_SECTION(), fg=color, bg=CARD_BG)
        lw.pack(side="left")
        if any(text_key.startswith(p) for p in _I18N_PREFIXES):
            _reg(lw, text_key)
        tk.Frame(f, bg=CARD_BD, height=2).pack(side="left", fill="x", expand=True, padx=(10, 0), pady=8)

    def group_lbl(parent, text_key):
        txt = _tl(text_key)
        w = tk.Label(parent, text=txt.upper(), font=F_TINY_B(),
                     fg=ACCENT, bg=CARD_BG)
        w.pack(anchor="w", pady=(14, 4))
        if any(text_key.startswith(p) for p in _I18N_PREFIXES):
            _reg(w, text_key)

    def card(parent, pady=(0,10)):
        f = tk.Frame(parent, bg=CARD_BG, padx=20, pady=14)
        f.pack(fill="x", pady=pady)
        return f

    # ─────────────────────────────────────────────────────────────────────────
    # LAYOUT  —  left sidebar | divider | right content
    # ─────────────────────────────────────────────────────────────────────────
    root = tk.Frame(frame, bg=BG)
    root.pack(fill="both", expand=True)

    # Left nav sidebar
    nav_panel = tk.Frame(root, bg=SIDEBAR_BG, width=190)
    nav_panel.pack(side="left", fill="y")
    nav_panel.pack_propagate(False)

    tk.Frame(root, bg=BORDER, width=1).pack(side="left", fill="y")

    # Right content area (plain Frame — NO canvas, NO scroll glitch)
    content_area = tk.Frame(root, bg=BG)
    content_area.pack(side="left", fill="both", expand=True)

    # ── Settings page header ─────────────────────────────────────────────────
    top_bar = tk.Frame(content_area, bg=BG)
    top_bar.pack(fill="x", padx=24, pady=(20, 0))

    _page_title_lbl = tk.Label(top_bar, text="", font=F_TITLE(),
                               fg=TEXT, bg=BG)
    _page_title_lbl.pack(side="left")

    # Save / Reset in top-right corner
    btn_area = tk.Frame(top_bar, bg=BG)
    btn_area.pack(side="right")
    status_lbl = tk.Label(btn_area, text="", font=F_SMALL(), fg=ACCENT2, bg=BG)
    status_lbl.pack(side="right", padx=(10, 0))
    app = frame.winfo_toplevel()
    flash_text = getattr(app, "_settings_flash_message", "")
    if flash_text:
        status_lbl.config(text=flash_text, fg=ACCENT2)
        app._settings_flash_message = ""
        frame.after(3000, lambda: status_lbl.config(text=""))

    # Divider under header
    tk.Frame(content_area, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(10, 0))

    # Scrollable content wrapper
    scroll_outer = tk.Frame(content_area, bg=BG)
    scroll_outer.pack(fill="both", expand=True, padx=(24, 0), pady=(0, 0))

    _sb = ttk.Scrollbar(scroll_outer, orient="vertical")
    _sb.pack(side="right", fill="y", padx=(0, 6), pady=6)

    _cv = tk.Canvas(scroll_outer, bg=BG, highlightthickness=0,
                    yscrollcommand=_sb.set)
    _cv.pack(side="left", fill="both", expand=True)
    _sb.config(command=_cv.yview)

    _inner = tk.Frame(_cv, bg=BG)
    _win   = _cv.create_window((0, 0), window=_inner, anchor="nw")

    _cv.bind("<Configure>", lambda e: _cv.itemconfig(_win, width=e.width))
    _inner.bind("<Configure>", lambda e: _cv.configure(scrollregion=_cv.bbox("all")))

    _mw_cb = lambda e: _cv.yview_scroll(int(-1*(e.delta/120)), "units")
    _cv.bind("<MouseWheel>", _mw_cb)

    def _bind_mw(w):
        w.bind("<MouseWheel>", _mw_cb, add="+")
        for c in w.winfo_children():
            _bind_mw(c)

    # Category pages — each is a Frame inside _inner
    _pages    = {}
    _nav_btns = {}
    _nav_rows = {}
    _nav_inds = {}
    _active   = [None]

    CATS = [
        ("profile",       "👤", "settings.profile"),
        ("goals",         "🎯", "settings.goals"),
        ("appearance",    "🎨", "settings.appearance"),
        ("interview",     "🤖", "settings.interview"),
        ("files",         "📁", "settings.files"),
        ("notifications", "🔔", "settings.notifications"),
        ("language",      "💻", "settings.language"),
        ("api",           "🔑", "settings.api"),
    ]

    def _show_cat(key):
        if _active[0] == key:
            return
        _active[0] = key

        # Update nav button styles
        for k, b in _nav_btns.items():
            row = _nav_rows[k]
            ind = _nav_inds[k]
            if k == key:
                row.config(bg=SURFACE2)
                b.config(bg=SURFACE2, fg=TEXT,
                         font=F_LABEL())
                ind.config(bg=ACCENT)
            else:
                row.config(bg=SIDEBAR_BG)
                b.config(bg=SIDEBAR_BG, fg=TEXT3,
                         font=F_BODY())
                ind.config(bg=SIDEBAR_BG)

        # Hide all pages, show selected
        for k, pg in _pages.items():
            pg.pack_forget()
        _pages[key].pack(fill="both", expand=True, pady=(14, 14))

        # Update header title
        cat_key = next((ik for cid, _, ik in CATS if cid == key), "")
        _page_title_lbl.config(text=_tl(cat_key))

        # Reset scroll to top
        _cv.yview_moveto(0)
        frame.after(100, lambda: _bind_mw(_inner))

    # ── Build nav sidebar buttons ─────────────────────────────────────────────
    settings_hdr_lbl = tk.Label(nav_panel, text=t("settings.title"), font=F_TINY_B(),
                                fg=TEXT3, bg=SIDEBAR_BG)
    settings_hdr_lbl.pack(anchor="w", padx=16, pady=(20, 8))
    _reg(settings_hdr_lbl, "settings.title")

    tk.Frame(nav_panel, bg=BORDER, height=1).pack(fill="x", padx=12, pady=(0, 8))

    for cat_id, icon, i18n_key in CATS:
        row = tk.Frame(nav_panel, bg=SIDEBAR_BG, cursor="hand2")
        row.pack(fill="x", pady=1)
        _nav_rows[cat_id] = row

        # Active indicator bar
        ind = tk.Frame(row, bg=SIDEBAR_BG, width=3)
        ind.pack(side="left", fill="y")
        _nav_inds[cat_id] = ind

        btn_txt = f"  {icon}  {_tl(i18n_key).replace(icon,'').strip()}"
        btn = tk.Button(row, text=btn_txt,
                        font=F_BODY(), fg=TEXT3, bg=SIDEBAR_BG,
                        relief="flat", anchor="w", padx=10, pady=8, bd=0,
                        cursor="hand2", activebackground=SURFACE2,
                        activeforeground=TEXT,
                        command=lambda k=cat_id: _show_cat(k))
        btn.pack(side="left", fill="x", expand=True)
        _nav_btns[cat_id] = btn
        _reg(btn, i18n_key)  # register for language updates

        def _make_hover(r, b, cat_key):
            def _enter(_e=None):
                if _active[0] != cat_key:
                    r.config(bg=SURFACE2)
                    b.config(bg=SURFACE2)

            def _leave(_e=None):
                if _active[0] != cat_key:
                    r.config(bg=SIDEBAR_BG)
                    b.config(bg=SIDEBAR_BG)

            r.bind("<Enter>", _enter)
            r.bind("<Leave>", _leave)
            b.bind("<Enter>", _enter)
            b.bind("<Leave>", _leave)
        _make_hover(row, btn, cat_id)

    # ── Build one Frame per category ─────────────────────────────────────────
    p  = cfg.get("profile", {})
    g  = cfg.get("goals", {})
    _app = frame.winfo_toplevel()
    _preview = getattr(_app, "_preview_cfg", None)
    if _preview and "appearance" in _preview:
        ap = _preview.get("appearance", {})
    else:
        ap = cfg.get("appearance", {})
    iv = cfg.get("interview", {})
    fi = cfg.get("files", {})
    no = cfg.get("notifications", {})
    lv = cfg.get("language", {})
    api= cfg.get("api", {})

    for cat_id, _, _ in CATS:
        pg = tk.Frame(_inner, bg=BG, padx=2, pady=2)
        _pages[cat_id] = pg

    # ── 1. PROFILE ────────────────────────────────────────────────────────────
    pg = _pages["profile"]
    c  = card(pg)
    section_title_row(c, "settings.profile", ACCENT4)
    field_row(c, "field.full_name",          "profile.full_name",       p.get("full_name",""))
    field_row(c, "field.current_role",       "profile.current_role",    p.get("current_role",""))
    field_row(c, "field.field",              "profile.field",           p.get("field","software development"))
    field_row(c, "field.years_exp",          "profile.years_exp",       p.get("years_exp","3"), width=10)
    field_row(c, "field.linkedin_url",       "profile.linkedin_url",    p.get("linkedin_url",""))
    sep(c)
    field_row(c, "field.target_companies",   "profile.target_companies",p.get("target_companies",""), width=42)
    lbl(c, "misc.comma_hint", font=F_TINY(), fg=TEXT3).pack(anchor="w", pady=(2, 6))
    drop_row(c, "field.job_status",          "profile.job_status",
             [t("status.actively_looking"), t("status.open_offers"),
              t("status.casually"),          t("status.not_looking")],
             p.get("job_status", t("status.actively_looking")))

    # ── 2. GOALS ─────────────────────────────────────────────────────────────
    pg = _pages["goals"]
    c  = card(pg)
    section_title_row(c, "settings.goals", ACCENT2)
    group_lbl(c, "misc.application_targets")
    spin_row(c, "field.daily_goal",          "goals.daily_apps",  1, 50,  g.get("daily_apps", 5))
    spin_row(c, "field.weekly_goal",         "goals.weekly_apps", 1, 200, g.get("weekly_apps", 20))
    sep(c)
    group_lbl(c, "misc.job_preferences")
    field_row(c, "field.target_salary",      "goals.target_salary",      g.get("target_salary",""), width=20)
    field_row(c, "field.preferred_location", "goals.preferred_location", g.get("preferred_location","Remote"), width=28)
    drop_row(c,  "field.job_type",           "goals.job_types",
             ["Full-time", "Part-time", "Contract", "Freelance", "Any"],
             g.get("job_types", "Full-time"))

    # ── 3. APPEARANCE ─────────────────────────────────────────────────────────
    pg = _pages["appearance"]
    c  = card(pg)
    section_title_row(c, "settings.appearance", ACCENT3)
    drop_row(c, "field.theme",     "appearance.theme",
             ["dark_navy", "darker", "midnight", "slate"], ap.get("theme", "dark_navy"))
    lbl(c, "misc.theme_note", font=F_TINY(), fg=TEXT3).pack(anchor="w", pady=(2, 8))
    drop_row(c, "field.font_size", "appearance.font_size",
             ["small", "medium", "large"], ap.get("font_size", "medium"))
    field_row(c, "Accent Color (#RRGGBB)", "appearance.accent_color",
             ap.get("accent_color", "#7C83FD"), width=16)
    sep(c)
    check_row(c, "misc.show_tips",
              "appearance.show_tips", ap.get("show_tips", True))

    _preview_lbl = tk.Label(c, text="", font=F_TINY(), fg=ACCENT3, bg=CARD_BG)
    _preview_lbl.pack(anchor="w", pady=(4, 0))
    if getattr(_app, "_preview_cfg", None):
        _preview_lbl.config(text="Preview active — Save to keep, Discard to revert")

    _accent_debounce_id = [None]
    _last_valid_accent = ap.get("accent_color", "#7C83FD")

    def _is_valid_hex(text):
        text = str(text or "").strip()
        return len(text) == 7 and text.startswith("#") and all(ch in "0123456789ABCDEFabcdef" for ch in text[1:])

    def _apply_preview():
        if not frame.winfo_exists():
            return
        accent_val = all_vars.get("appearance.accent_color")
        if accent_val:
            raw = accent_val.get().strip()
            if not _is_valid_hex(raw):
                _preview_lbl.config(text=f"Invalid hex color: {raw or '(empty)'} — using last valid: {_last_valid_accent}", fg=DANGER)
                return
        new_appearance = {}
        for key in ("appearance.theme", "appearance.font_size", "appearance.accent_color"):
            v = all_vars.get(key)
            if v:
                k = key.split(".", 1)[1]
                new_appearance[k] = v.get()
        base_cfg = cfg_mod.load() if cfg_mod else {}
        temp_cfg = dict(base_cfg)
        temp_cfg["appearance"] = new_appearance
        _app._preview_cfg = temp_cfg
        _app._settings_var_snapshot = {k: v.get() for k, v in all_vars.items()}
        _preview_lbl.config(text="Preview active — Save to keep, Discard to revert", fg=ACCENT3)
        _app.after(10, lambda: _app._apply_live_settings(temp_cfg, rebuild_ui=True, refresh_tabs=False))

    def _on_theme_change(*_):
        _apply_preview()

    def _on_font_change(*_):
        _apply_preview()

    def _on_accent_change(*_):
        accent_val = all_vars.get("appearance.accent_color")
        if accent_val:
            raw = accent_val.get().strip()
            if _is_valid_hex(raw):
                _last_valid_accent = raw
        if _accent_debounce_id[0]:
            frame.after_cancel(_accent_debounce_id[0])
        _accent_debounce_id[0] = frame.after(500, _apply_preview)

    _theme_var = all_vars.get("appearance.theme")
    _font_var = all_vars.get("appearance.font_size")
    _accent_var = all_vars.get("appearance.accent_color")
    if _theme_var:
        _theme_var.trace_add("write", _on_theme_change)
    if _font_var:
        _font_var.trace_add("write", _on_font_change)
    if _accent_var:
        _accent_var.trace_add("write", _on_accent_change)

    # ── 4. INTERVIEW PREP ─────────────────────────────────────────────────────
    pg = _pages["interview"]
    c  = card(pg)
    section_title_row(c, "settings.interview", ACCENT4)
    try:
        import interview_prep as _ip
        cat_opts = _ip.get_categories()
    except Exception:
        cat_opts = ["Behavioral (STAR)", "Technical / Problem Solving",
                    "Motivation & Culture Fit", "Salary & Logistics"]
    drop_row(c, "field.default_category", "interview.default_category",
             cat_opts, iv.get("default_category", cat_opts[0]))
    spin_row(c, "field.min_word_warning", "interview.min_word_warning",
             10, 200, iv.get("min_word_warning", 50))
    sep(c)
    check_row(c, "misc.auto_start_timer",
              "interview.auto_start_timer", iv.get("auto_start_timer", True))
    check_row(c, "misc.show_follow_ups",
              "interview.show_follow_ups",  iv.get("show_follow_ups", True))
    check_row(c, "misc.show_category_tips",
              "interview.show_tips",        iv.get("show_tips", True))
    check_row(c, "misc.save_answer_history",
              "interview.save_history",     iv.get("save_history", True))

    # ── 5. FILES & BACKUP ─────────────────────────────────────────────────────
    pg = _pages["files"]
    c  = card(pg)
    section_title_row(c, "settings.files", ACCENT)
    group_lbl(c, "misc.paths")
    tracker_var = tk.StringVar(master=frame, value=fi.get("tracker_path", ""))
    all_vars["files.tracker_path"] = tracker_var
    tr = tk.Frame(c, bg=CARD_BG); tr.pack(fill="x", pady=3)
    lbl(tr, "field.excel_tracker_path", fg=TEXT3).pack(anchor="w", pady=(0,2))
    tr2 = tk.Frame(tr, bg=CARD_BG); tr2.pack(fill="x")
    tk.Entry(tr2, textvariable=tracker_var, font=F_BODY(),
             bg=SURFACE2, fg=TEXT, relief="flat", width=36,
             highlightthickness=1, highlightbackground=CARD_BD,
             insertbackground=ACCENT).pack(side="left", fill="x", expand=True, ipady=7)
    def browse_tracker():
        p2 = filedialog.askopenfilename(title="Select Excel Tracker",
             filetypes=[("Excel files", "*.xlsx *.xls"), ("All","*.*")])
        if p2: tracker_var.set(p2)
    tracker_browse_btn = tk.Button(tr2, text=t("btn.browse"), font=F_SMALL(), bg=SURFACE2, fg=TEXT2,
                                   relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
                                   activebackground=BORDER, command=browse_tracker)
    tracker_browse_btn.pack(side="left", padx=(6,0))
    _reg(tracker_browse_btn, "btn.browse")

    backup_var = tk.StringVar(master=frame, value=fi.get("backup_folder", ""))
    all_vars["files.backup_folder"] = backup_var
    br = tk.Frame(c, bg=CARD_BG); br.pack(fill="x", pady=3)
    lbl(br, "field.backup_folder", fg=TEXT3).pack(anchor="w", pady=(0,2))
    br2 = tk.Frame(br, bg=CARD_BG); br2.pack(fill="x")
    tk.Entry(br2, textvariable=backup_var, font=F_BODY(),
             bg=SURFACE2, fg=TEXT, relief="flat", width=36,
             highlightthickness=1, highlightbackground=CARD_BD,
             insertbackground=ACCENT).pack(side="left", fill="x", expand=True, ipady=7)
    def browse_backup():
        p3 = filedialog.askdirectory(title="Select Backup Folder")
        if p3: backup_var.set(p3)
    backup_browse_btn = tk.Button(br2, text=t("btn.browse"), font=F_SMALL(), bg=SURFACE2, fg=TEXT2,
                                  relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
                                  activebackground=BORDER, command=browse_backup)
    backup_browse_btn.pack(side="left", padx=(6,0))
    _reg(backup_browse_btn, "btn.browse")
    sep(c)
    group_lbl(c, "misc.backup_options")
    check_row(c, "misc.enable_auto_backups",  "files.backup_enabled", fi.get("backup_enabled", True))
    check_row(c, "misc.backup_on_exit",       "files.backup_on_exit", fi.get("backup_on_exit", False))
    spin_row(c,  "field.max_backups",         "files.max_backups",    1, 50, fi.get("max_backups", 10))

    # ── 6. NOTIFICATIONS ─────────────────────────────────────────────────────
    pg = _pages["notifications"]
    c  = card(pg)
    section_title_row(c, "settings.notifications", ACCENT3)
    spin_row(c, "field.followup_days", "notifications.followup_days",
             1, 30, no.get("followup_days", 5))
    field_row(c, "field.reminder_time",      "notifications.reminder_time",
              no.get("reminder_time", "09:00"), width=10)
    sep(c)
    check_row(c, "misc.streak_warning",      "notifications.streak_warning",
              no.get("streak_warning", True))
    check_row(c, "misc.enable_email_reminders", "notifications.email_reminder",
              no.get("email_reminder", False))

    # ── 7. LANGUAGE & TECH STACK ─────────────────────────────────────────────
    pg = _pages["language"]
    c  = card(pg)
    section_title_row(c, "settings.language", ACCENT)

    try:
        import settings as _sm
        PROG_LANGS   = _sm.PROGRAMMING_LANGUAGES
        FRAMEWORKS_L = _sm.FRAMEWORKS
        DATABASES_L  = _sm.DATABASES
        CLOUD_L      = _sm.CLOUD_PLATFORMS
        APP_LANGS    = _sm.APP_LANGUAGES
    except Exception:
        PROG_LANGS   = ["Python","JavaScript","TypeScript","Java","C#","Go","Rust","Swift","Kotlin","PHP","Ruby","C++"]
        FRAMEWORKS_L = ["React","Django","FastAPI","Node.js","Spring Boot","Flutter","Vue.js","Angular"]
        DATABASES_L  = ["PostgreSQL","MySQL","MongoDB","Redis","SQLite","DynamoDB","Firebase"]
        CLOUD_L      = ["AWS","GCP","Azure","Docker","Kubernetes","Vercel","GitHub Actions"]
        APP_LANGS    = ["English","Turkish","German","French","Spanish","Portuguese","Arabic","Japanese","Korean","Chinese (Simplified)"]

    saved_app_lang   = lv.get("app_language", "English")
    saved_primary    = lv.get("primary_language", "Python")
    saved_secondary  = lv.get("secondary_languages", [])
    saved_frameworks = lv.get("frameworks", [])
    saved_databases  = lv.get("databases", [])
    saved_cloud      = lv.get("cloud", [])

    # App language (instant change)
    lang_lbl_w = lbl(c, "field.app_lang", fg=TEXT3)
    lang_lbl_w.pack(anchor="w", pady=(0, 2))
    lang_var = tk.StringVar(master=frame, value=saved_app_lang)
    lang_cb  = ttk.Combobox(c, textvariable=lang_var, values=APP_LANGS,
                            state="readonly", font=F_BODY(), width=30)
    lang_cb.pack(fill="x", ipady=5)
    all_vars["language.app_language"] = lang_var

    def _on_lang_select(event=None):
        try:
            set_language(lang_var.get())
            frame.winfo_toplevel()._apply_language()
        except Exception:
            pass
    lang_cb.bind("<<ComboboxSelected>>", _on_lang_select)

    sep(c)
    drop_row(c, "field.primary_lang", "language.primary_language", PROG_LANGS, saved_primary)
    lbl(c, "misc.tech_autofill_note", font=F_TINY_I(), fg=ACCENT3).pack(anchor="w", pady=(4, 8))

    def multi_grid(parent, label_key, items, saved_list, var_key, cols=5):
        lbl(parent, label_key, font=F_SMALL_B(), fg=TEXT2).pack(anchor="w", pady=(10, 4))
        grid = tk.Frame(parent, bg=CARD_BG)
        grid.pack(fill="x", pady=(0, 6))
        item_vars = {}
        for i, item in enumerate(items):
            v = tk.BooleanVar(master=frame, value=(item in saved_list))
            tk.Checkbutton(grid, text=item, variable=v,
                           font=F_SMALL(), fg=TEXT2, bg=CARD_BG,
                           selectcolor=SURFACE2, activebackground=CARD_BG,
                           activeforeground=TEXT, cursor="hand2",
                           anchor="w", width=16).grid(
                               row=i//cols, column=i%cols, sticky="w", padx=2, pady=1)
            item_vars[item] = v
        class _LP:
            def get(self):
                return [it for it, vv in item_vars.items() if vv.get()]
        all_vars[var_key] = _LP()

    sep(c)
    multi_grid(c, "field.add_langs",  PROG_LANGS,   saved_secondary,  "language.secondary_languages", cols=5)
    multi_grid(c, "field.frameworks", FRAMEWORKS_L, saved_frameworks, "language.frameworks", cols=4)
    multi_grid(c, "field.databases",  DATABASES_L,  saved_databases,  "language.databases",  cols=4)
    multi_grid(c, "field.cloud",      CLOUD_L,      saved_cloud,      "language.cloud",      cols=4)

    # ── 8. API & INTEGRATIONS ─────────────────────────────────────────────────
    pg = _pages["api"]
    c  = card(pg)
    section_title_row(c, "settings.api", ACCENT2)
    group_lbl(c, "misc.openai_group")
    lbl(c, "field.openai_key", fg=TEXT3).pack(anchor="w", pady=(0, 2))
    field_row(c, "field.openai_key", "api.openai_key",
              api.get("openai_key", ""), show=True, width=42)
    sep(c)
    group_lbl(c, "misc.notion_group")
    field_row(c, "field.notion_token", "api.notion_token",
              api.get("notion_token", ""), show=True, width=42)
    field_row(c, "field.notion_db",    "api.notion_database_id",
              api.get("notion_database_id", ""), width=42)

    # ── Restore snapshot from preview rebuild ─────────────────────────────────
    _autosave_paused = [False]
    _snapshot = getattr(_app, "_settings_var_snapshot", None)
    if _snapshot:
        _autosave_paused[0] = True
        for dotkey, val in _snapshot.items():
            v = all_vars.get(dotkey)
            if v:
                try:
                    v.set(val)
                except Exception:
                    pass
        _app._settings_var_snapshot = None
        _autosave_paused[0] = False

    # ── Auto-save for non-appearance, non-API fields ──────────────────────────
    _autosave_debounce_id = [None]
    _AUTOSAVE_EXCLUDED = {"appearance", "api"}

    def _do_autosave():
        if not frame.winfo_exists():
            return
        if _autosave_paused[0]:
            return
        try:
            saved_cfg = cfg_mod.load() if cfg_mod else {}
            for dotkey, var in all_vars.items():
                parts = dotkey.split(".", 1)
                if len(parts) != 2:
                    continue
                sect, key2 = parts
                if sect in _AUTOSAVE_EXCLUDED:
                    continue
                if sect not in saved_cfg:
                    saved_cfg[sect] = {}
                val = var.get()
                if isinstance(var, tk.BooleanVar):
                    val = bool(val)
                elif key2 in ("daily_apps", "weekly_apps", "min_word_warning",
                              "followup_days", "max_backups", "sidebar_width"):
                    try:
                        val = int(val)
                    except Exception:
                        pass
                saved_cfg[sect][key2] = val
            if cfg_mod:
                cfg_mod.save(saved_cfg)
        except Exception as e:
            try:
                _app.after(0, lambda: _app._status_validation_lbl.config(text="  ⚠ Settings save error", fg=DANGER))
            except Exception:
                pass

    def _schedule_autosave(*_):
        if _autosave_paused[0]:
            return
        if _autosave_debounce_id[0]:
            frame.after_cancel(_autosave_debounce_id[0])
        _autosave_debounce_id[0] = frame.after(1500, _do_autosave)

    for dotkey, var in all_vars.items():
        parts = dotkey.split(".", 1)
        if len(parts) == 2 and parts[0] not in _AUTOSAVE_EXCLUDED:
            if isinstance(var, tk.StringVar):
                var.trace_add("write", _schedule_autosave)
            elif isinstance(var, tk.BooleanVar):
                var.trace_add("write", _schedule_autosave)

    # ─────────────────────────────────────────────────────────────────────────
    # SAVE / RESET
    # ─────────────────────────────────────────────────────────────────────────
    def save_all():
        try:
            _app._preview_cfg = None
            _app._settings_var_snapshot = None
            new_cfg = cfg_mod.load() if cfg_mod else {}
            for dotkey, var in all_vars.items():
                parts = dotkey.split(".", 1)
                if len(parts) == 2:
                    sect, key2 = parts
                    if sect not in new_cfg:
                        new_cfg[sect] = {}
                    val = var.get()
                    if isinstance(val, list):
                        pass
                    elif isinstance(var, tk.BooleanVar):
                        val = bool(val)
                    elif key2 in ("daily_apps","weekly_apps","min_word_warning",
                                  "followup_days","max_backups","sidebar_width"):
                        try: val = int(val)
                        except: pass
                    new_cfg[sect][key2] = val
            if cfg_mod:
                cfg_mod.save(new_cfg)
            try:
                set_language(new_cfg.get("language", {}).get("app_language", get_language()))
            except Exception:
                pass
            try:
                import streak_tracker as st
                def _get_int_setting(dotkey, default):
                    var = all_vars.get(dotkey)
                    if var is None:
                        return default
                    try:
                        return int(var.get() or default)
                    except Exception:
                        return default
                st.set_goals(
                    _get_int_setting("goals.daily_apps", 5),
                    _get_int_setting("goals.weekly_apps", 20),
                )
            except Exception:
                pass
            app = frame.winfo_toplevel()
            app._settings_flash_message = t("settings.saved")
            apply_fn = getattr(app, "_apply_live_settings", None)
            if apply_fn:
                apply_fn(new_cfg, rebuild_ui=True, refresh_tabs=True)
            else:
                status_lbl.config(text=t("settings.saved"), fg=ACCENT2)
                frame.after(3000, lambda: status_lbl.config(text=""))
        except Exception as ex:
            messagebox.showerror("Save Error", str(ex))

    def discard_preview():
        _app._preview_cfg = None
        _app._settings_var_snapshot = None
        saved_cfg = cfg_mod.load() if cfg_mod else {}
        apply_fn = getattr(_app, "_apply_live_settings", None)
        if apply_fn:
            apply_fn(saved_cfg, rebuild_ui=True, refresh_tabs=False)

    def reset_all():
        if messagebox.askyesno("Reset to Defaults", t("settings.reset_confirm")):
            _app._preview_cfg = None
            _app._settings_var_snapshot = None
            if cfg_mod:
                cfg_mod.reset()
                try:
                    fresh_cfg = cfg_mod.load()
                    default_lang = fresh_cfg.get("language", {}).get("app_language", "English")
                    set_language(default_lang)
                    app = frame.winfo_toplevel()
                    app._settings_flash_message = t("settings.reset_done")
                    apply_fn = getattr(app, "_apply_live_settings", None)
                    if apply_fn:
                        apply_fn(fresh_cfg, rebuild_ui=True, refresh_tabs=True)
                except Exception:
                    pass

    save_btn  = styled_button(btn_area, t("btn.save_settings"), save_all, color=ACCENT2, width=16)
    save_btn.pack(side="left", padx=(0, 8))
    _reg(save_btn, "btn.save_settings")
    discard_btn = ghost_button(btn_area, "Discard Preview", discard_preview, width=16)
    discard_btn.pack(side="left", padx=(0, 8))
    reset_btn = ghost_button(btn_area, t("btn.reset_defaults"), reset_all, width=16)
    reset_btn.pack(side="left")
    _reg(reset_btn, "btn.reset_defaults")

    # Store registry for live language updates
    frame._label_registry = _label_reg

    # Store all_vars on app for trace cleanup during rebuild
    _app_ref = frame.winfo_toplevel()
    _app_ref._settings_all_vars = all_vars

    # Update nav button labels helper (called by _apply_language)
    def _refresh_nav_labels():
        for cat_id, icon, i18n_key in CATS:
            if cat_id in _nav_btns:
                clean = _tl(i18n_key).replace(icon, "").strip()
                _nav_btns[cat_id].config(text=f"  {icon}  {clean}")
        if _active[0]:
            cat_key = next((ik for cid, _, ik in CATS if cid == _active[0]), "")
            _page_title_lbl.config(text=_tl(cat_key))
    frame._refresh_nav_labels = _refresh_nav_labels

    # Show first category by default
    _show_cat("profile")


# ════════════════════════════════════════════════════════════════════════════
# MAIN APP
# ════════════════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Developer Job Application Tracker PRO")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self._current_cfg = _load_settings_cfg()
        self._email_runtime_config = self._load_initial_email_config()
        self._email_last_sent_key = ""
        self._tracker_signature = None
        self._tracker_watch_id = None
        self._email_watch_id = None
        self._status_bar_watch_id = None
        self._json_watch_id = None
        self._json_signatures = {}
        self._chart_debounce_id = None
        self._validation_debounce_id = None
        self._last_chart_gen_ts = 0.0
        self._chart_regen_running = False
        self._preview_cfg = None
        self._settings_var_snapshot = None
        self._settings_flash_message = ""
        self._closing = False
        self.current_tab_index = 0
        self.style = ttk.Style(self)
        self._apply_live_settings(self._current_cfg, rebuild_ui=False, refresh_tabs=False)

        try:
            self.iconbitmap(os.path.join(BASE_DIR, "icon.ico"))
        except Exception:
            pass

        self._build_sidebar()
        self._build_content()
        self._build_status_bar()
        self._show_tab(0)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._bind_keyboard_shortcuts()
        self.after(350, self._bootstrap_runtime_services)

    def _load_initial_email_config(self):
        return {
            "to_email": os.environ.get("EMAIL_REMINDER_TO", "").strip(),
            "from_email": os.environ.get("EMAIL_REMINDER_FROM", "").strip(),
            "password": os.environ.get("EMAIL_REMINDER_PASSWORD", "").strip(),
            "smtp_server": os.environ.get("EMAIL_REMINDER_SMTP_SERVER", "smtp.gmail.com").strip() or "smtp.gmail.com",
            "smtp_port": os.environ.get("EMAIL_REMINDER_SMTP_PORT", "587").strip() or "587",
        }

    def _get_email_runtime_config(self):
        merged = self._load_initial_email_config()
        merged.update({k: v for k, v in self._email_runtime_config.items() if v not in (None, "")})
        merged["smtp_server"] = merged.get("smtp_server") or "smtp.gmail.com"
        merged["smtp_port"] = str(merged.get("smtp_port") or "587")
        return merged

    def _remember_email_runtime_config(self, values: dict):
        for key, value in values.items():
            if value is None:
                continue
            self._email_runtime_config[key] = str(value).strip()

    def _get_sidebar_width(self, cfg: dict | None = None) -> int:
        cfg = cfg or self._current_cfg
        raw = cfg.get("appearance", {}).get("sidebar_width", 220)
        try:
            return max(180, min(320, int(raw)))
        except Exception:
            return 220

    def _apply_window_state(self, cfg: dict | None = None):
        cfg = cfg or _load_settings_cfg()
        self._current_cfg = cfg
        _apply_runtime_settings(cfg)
        try:
            self.tk.call("tk", "scaling", _FONT_SCALE)
        except Exception:
            pass
        try:
            tkfont.nametofont("TkDefaultFont").configure(family="Segoe UI", size=FONT_BODY[1])
            tkfont.nametofont("TkTextFont").configure(family="Segoe UI", size=FONT_BODY[1])
            tkfont.nametofont("TkHeadingFont").configure(family="Segoe UI", size=FONT_LABEL[1], weight="bold")
            tkfont.nametofont("TkMenuFont").configure(family="Segoe UI", size=FONT_SUB[1])
            tkfont.nametofont("TkFixedFont").configure(family="Consolas", size=FONT_MONO[1])
        except Exception:
            pass
        self.configure(bg=BG)
        try:
            _configure_ttk_style(self.style)
        except Exception:
            pass

    def _bootstrap_runtime_services(self):
        self._tracker_signature = self._get_tracker_signature()
        self._update_status_bar()
        self.after(600, self._refresh_live_tabs)
        run_in_thread(self._run_startup_backup, name="startup_backup")
        self._schedule_tracker_watch()
        self._schedule_email_scheduler()
        self._schedule_status_bar_refresh()
        self._schedule_json_watch()

    def _build_sidebar(self):
        self.sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=self._get_sidebar_width())
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Frame(self.sidebar, bg=BORDER, width=1).pack(side="right", fill="y")

        inner_sb = tk.Frame(self.sidebar, bg=SIDEBAR_BG)
        inner_sb.pack(fill="both", expand=True, side="left")

        logo = tk.Frame(inner_sb, bg=SIDEBAR_BG)
        logo.pack(fill="x", pady=(24, 0))
        tk.Label(logo, text="JobTracker", font=F_NAV_LOGO(),
                 fg=TEXT, bg=SIDEBAR_BG).pack(anchor="w", padx=22)
        badge_row = tk.Frame(logo, bg=SIDEBAR_BG)
        badge_row.pack(anchor="w", padx=22, pady=(2, 0))
        tk.Frame(badge_row, bg=ACCENT, width=6, height=6).pack(side="left", pady=5)
        tk.Label(badge_row, text=" PRO", font=F_TINY_B(),
                 fg=ACCENT, bg=SIDEBAR_BG).pack(side="left")

        tk.Frame(inner_sb, bg=BORDER, height=1).pack(fill="x", pady=(20, 12))

        # Nav items with dot indicators
        self.nav_buttons: list[tk.Button] = []
        nav_dot_colors = [ACCENT, ACCENT2, ACCENT4, ACCENT3, ACCENT3, ACCENT2, ACCENT2,
                             ACCENT4, ACCENT, ACCENT2, ACCENT3, TEXT3]
        self._nav_keys = [
            ("nav.home",      0),
            ("nav.ats",       1),
            ("nav.jd",        2),
            ("nav.tools",     3),
            ("nav.email",     4),
            ("nav.notion",    5),
            ("nav.cover",     6),
            ("nav.interview", 7),
            ("nav.linkedin",  8),
            ("nav.salary",    9),
            ("nav.streak",   10),
            ("nav.settings", 11),
        ]
        nav_items = [(t(k), idx) for k, idx in self._nav_keys]

        self._nav_frames: list[tk.Frame] = []
        for (label, idx), dot_col in zip(nav_items, nav_dot_colors):
            row_f = tk.Frame(inner_sb, bg=SIDEBAR_BG, cursor="hand2")
            row_f.pack(fill="x")
            self._nav_frames.append(row_f)

            # active indicator bar (left)
            ind = tk.Frame(row_f, bg=SIDEBAR_BG, width=3)
            ind.pack(side="left", fill="y")

            # dot
            tk.Label(row_f, text="●", font=F_TINY(),
                     fg=dot_col, bg=SIDEBAR_BG).pack(side="left", padx=(10, 8))

            btn = tk.Button(
                row_f, text=label, font=F_BODY(),
                bg=SIDEBAR_BG, fg=TEXT2, relief="flat",
                anchor="w", pady=11, cursor="hand2",
                activebackground=SIDEBAR_BG, activeforeground=TEXT,
                bd=0, highlightthickness=0,
                command=lambda i=idx: self._show_tab(i)
            )
            btn.pack(side="left", fill="x", expand=True)

            # Keyboard shortcut hint (Ctrl+1..9, Ctrl+0 for tab 10)
            if idx < 9:
                hint_text = f"Ctrl+{idx+1}"
            elif idx == 10:
                hint_text = "Ctrl+0"
            else:
                hint_text = ""
            if hint_text:
                tk.Label(row_f, text=hint_text, font=F_MICRO(),
                         fg=TEXT3, bg=SIDEBAR_BG).pack(side="right", padx=(0, 8))

            self.nav_buttons.append(btn)

            # hover
            for w in (row_f, btn):
                w.bind("<Enter>", lambda e, f=row_f: f.config(bg=SURFACE2) or
                       [c.config(bg=SURFACE2) for c in f.winfo_children()])
                w.bind("<Leave>", lambda e, f=row_f, i=idx: None if i == getattr(self, '_active_tab', 0)
                       else f.config(bg=SIDEBAR_BG) or
                       [c.config(bg=SIDEBAR_BG) for c in f.winfo_children()])

        # Version + quick gear button
        bottom_f = tk.Frame(inner_sb, bg=SIDEBAR_BG)
        bottom_f.pack(side="bottom", fill="x", pady=(0, 12), padx=16)
        self._ver_lbl = tk.Label(bottom_f, text=t("misc.version"),
                 font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG)
        self._ver_lbl.pack(anchor="w", pady=(0, 6))
        self._gear_btn = tk.Button(
            bottom_f, text=t("btn.quick_settings"),
            font=F_SMALL(), bg=SURFACE2, fg=TEXT2,
            relief="flat", cursor="hand2", padx=10, pady=6, bd=0,
            activebackground=BORDER, activeforeground=TEXT,
            command=self._open_settings_popup
        )
        self._gear_btn.pack(fill="x")

    def _build_content(self):
        content_wrapper = styled_frame(self, bg=BG)
        content_wrapper.pack(side="left", fill="both", expand=True)
        self.content = content_wrapper

        builders = [build_home_tab, build_ats_tab, build_jd_tab, build_tools_tab,
                    build_email_tab, build_notion_tab, build_cover_letter_tab,
                    build_interview_tab, build_linkedin_tab, build_salary_tab,
                    build_streak_tab, build_settings_tab]
        self.tabs: list[tk.Frame] = []
        for builder in builders:
            tab = styled_frame(content_wrapper, bg=BG)
            tab.place(x=0, y=0, relwidth=1, relheight=1)
            builder(tab)
            self.tabs.append(tab)

    def _build_status_bar(self):
        self._status_bar = tk.Frame(self, bg=SIDEBAR_BG, height=26)
        self._status_bar.pack(side="bottom", fill="x")
        self._status_bar.pack_propagate(False)
        tk.Frame(self._status_bar, bg=BORDER, height=1).pack(fill="x", side="top")

        self._status_tracker_lbl = tk.Label(
            self._status_bar, text="  ● Tracker: Loading...",
            font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG, anchor="w")
        self._status_tracker_lbl.pack(side="left", padx=(12, 0), pady=4)

        self._status_lang_lbl = tk.Label(
            self._status_bar, text=f"  {get_language()}",
            font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG)
        self._status_lang_lbl.pack(side="right", padx=(0, 12), pady=4)

        self._status_validation_lbl = tk.Label(
            self._status_bar, text="",
            font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG)
        self._status_validation_lbl.pack(side="right", padx=(0, 20), pady=4)

        self._status_backup_lbl = tk.Label(
            self._status_bar, text="",
            font=F_TINY(), fg=TEXT3, bg=SIDEBAR_BG)
        self._status_backup_lbl.pack(side="right", padx=(0, 20), pady=4)

    def _update_status_bar(self):
        tracker_path = _get_tracker_path()
        if os.path.exists(tracker_path):
            self._status_tracker_lbl.config(text="  ● Tracker: Connected", fg=ACCENT2)
        else:
            self._status_tracker_lbl.config(text="  ● Tracker: Not found", fg=DANGER)
        try:
            self._status_lang_lbl.config(text=f"  {get_language()}")
        except Exception:
            pass
        backup_dir = _get_backup_dir()
        try:
            backups = sorted([f for f in os.listdir(backup_dir) if f.endswith(".xlsx")], reverse=True)
            if backups:
                self._status_backup_lbl.config(text=f"Last backup: {backups[0][:19]}  ")
            else:
                self._status_backup_lbl.config(text="")
        except Exception:
            self._status_backup_lbl.config(text="")

    def _schedule_status_bar_refresh(self):
        if self._status_bar_watch_id:
            self.after_cancel(self._status_bar_watch_id)
        self._status_bar_watch_id = self.after(30000, self._poll_status_bar)

    def _poll_status_bar(self):
        if not self.winfo_exists():
            return
        self._update_status_bar()
        self._status_bar_watch_id = self.after(30000, self._poll_status_bar)

    def _get_json_signature(self, path):
        if not path or not os.path.exists(path):
            return None
        try:
            stat = os.stat(path)
            return (stat.st_mtime_ns, stat.st_size)
        except OSError:
            return None

    def _schedule_json_watch(self):
        if self._json_watch_id:
            self.after_cancel(self._json_watch_id)
        self._json_watch_id = self.after(5000, self._poll_json_watch)

    def _poll_json_watch(self):
        if not self.winfo_exists():
            return
        json_files = {
            "interview_scores": os.path.join(BASE_DIR, "interview_scores.json"),
            "streak_data": os.path.join(BASE_DIR, "streak_data.json"),
        }
        changed = False
        for name, path in json_files.items():
            current = self._get_json_signature(path)
            previous = self._json_signatures.get(name)
            self._json_signatures[name] = current
            if previous is not None and current is not None and current != previous:
                changed = True
        if changed:
            self._refresh_live_tabs((7, 10))
        self._json_watch_id = self.after(5000, self._poll_json_watch)

    def _bind_keyboard_shortcuts(self):
        for i in range(min(9, len(self._nav_keys))):
            self.bind(f"<Control-KeyPress-{i+1}>", lambda e, idx=i: self._show_tab(idx))
        self.bind("<Control-KeyPress-0>", lambda e: self._show_tab(10))
        self.bind("<Control-q>", lambda e: self._on_close())
        self.bind("<Control-Q>", lambda e: self._on_close())
        self.bind("<Control-comma>", lambda e: self._show_tab(11))

    def _cleanup_tk_variables(self):
        """Remove traces on tracked Tk variables before destroying widgets
        to prevent RuntimeError in Variable.__del__ during GC."""
        all_vars = getattr(self, "_settings_all_vars", None)
        if all_vars:
            for var in all_vars.values():
                try:
                    for info in var.trace_info():
                        var.trace_remove(info[0], info[1])
                except Exception:
                    pass
            all_vars.clear()

    def _rebuild_ui(self, active_idx: int | None = None):
        active = getattr(self, "_active_tab", 0) if active_idx is None else active_idx
        # Clean up ALL Tk variables before destroying widgets to prevent
        # RuntimeError in Variable.__del__ during GC (main thread not in main loop)
        self._cleanup_tk_variables()
        if hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            self.sidebar.destroy()
        if hasattr(self, "content") and self.content.winfo_exists():
            self.content.destroy()
        if hasattr(self, "_status_bar") and self._status_bar.winfo_exists():
            self._status_bar.destroy()
        self._build_sidebar()
        self._build_content()
        self._build_status_bar()
        self._show_tab(active if 0 <= active < len(self.tabs) else 0)
        self._apply_language()

    def _apply_live_settings(self, cfg: dict | None = None, rebuild_ui: bool = True, refresh_tabs: bool = True):
        cfg = cfg or _load_settings_cfg()
        try:
            set_language(cfg.get("language", {}).get("app_language", get_language()))
        except Exception:
            pass
        self._apply_window_state(cfg)
        if rebuild_ui and hasattr(self, "tabs"):
            self._rebuild_ui(getattr(self, "_active_tab", 0))
        elif hasattr(self, "sidebar") and self.sidebar.winfo_exists():
            self.sidebar.config(width=self._get_sidebar_width(cfg), bg=SIDEBAR_BG)
        self._tracker_signature = self._get_tracker_signature()
        if refresh_tabs:
            self.after(150, self._refresh_live_tabs)

    def _apply_language(self):
        for btn, (key, _) in zip(self.nav_buttons, self._nav_keys):
            btn.config(text=t(key))

        self._gear_btn.config(text=t("btn.quick_settings"))
        self.title(t("home.title"))

        for tab in self.tabs:
            registry = getattr(tab, "_label_registry", [])
            for widget, key in registry:
                try:
                    widget.config(text=t(key))
                except Exception:
                    pass
            # Refresh settings sub-nav labels if present
            refresh_fn = getattr(tab, "_refresh_nav_labels", None)
            if refresh_fn:
                try:
                    refresh_fn()
                except Exception:
                    pass

    def _rebuild_settings_tab(self):
        if not hasattr(self, "tabs") or len(self.tabs) <= 11:
            return
        settings_tab = self.tabs[11]
        for child in settings_tab.winfo_children():
            child.destroy()
        settings_tab._label_registry = []
        settings_tab._refresh_nav_labels = None
        build_settings_tab(settings_tab)
        if getattr(self, "_active_tab", None) == 11:
            settings_tab.lift()

    def _get_tracker_signature(self):
        tracker_path = _get_tracker_path()
        if not tracker_path or not os.path.exists(tracker_path):
            return (tracker_path, None, None)
        try:
            stat = os.stat(tracker_path)
            return (tracker_path, stat.st_mtime_ns, stat.st_size)
        except OSError:
            return (tracker_path, None, None)

    def _refresh_live_tabs(self, tab_indexes=None):
        indexes = tab_indexes or (0, 7, 10)
        if not hasattr(self, "tabs"):
            return
        for idx in indexes:
            if 0 <= idx < len(self.tabs):
                refresh_fn = getattr(self.tabs[idx], "_refresh_data", None)
                if callable(refresh_fn):
                    try:
                        refresh_fn()
                    except Exception:
                        pass

    def _schedule_tracker_watch(self):
        if self._tracker_watch_id:
            self.after_cancel(self._tracker_watch_id)
        self._tracker_watch_id = self.after(2500, self._poll_tracker_watch)

    def _schedule_email_scheduler(self):
        if self._email_watch_id:
            self._safe_after_cancel(self._email_watch_id)
        self._email_watch_id = self.after(30000, self._poll_email_scheduler)

    def _poll_tracker_watch(self):
        if not self.winfo_exists():
            return
        current = self._get_tracker_signature()
        previous = self._tracker_signature
        self._tracker_signature = current
        if previous and current != previous:
            self._refresh_live_tabs((0, 7, 10))
            self._update_status_bar()
            self._schedule_chart_regen()
            self._schedule_validation_summary()
        self._tracker_watch_id = self.after(2500, self._poll_tracker_watch)

    def _schedule_chart_regen(self):
        if self._chart_debounce_id:
            self.after_cancel(self._chart_debounce_id)
        self._chart_debounce_id = self.after(3000, self._maybe_run_chart_regen)

    def _maybe_run_chart_regen(self):
        if self._chart_regen_running:
            return
        import time as _time
        elapsed = _time.time() - self._last_chart_gen_ts
        if elapsed < 120:
            return
        tracker_path = _get_tracker_path()
        if not tracker_path or not os.path.exists(tracker_path):
            return
        self._chart_regen_running = True
        self._last_chart_gen_ts = _time.time()
        run_in_thread(self._run_chart_regen, tracker_path, name="chart_regen")

    def _run_chart_regen(self, tracker_path):
        try:
            import importlib
            if "chart_generator" in sys.modules:
                del sys.modules["chart_generator"]
            mod = importlib.import_module("chart_generator")
            charts_dir = os.path.join(BASE_DIR, "charts")
            os.makedirs(charts_dir, exist_ok=True)
            chart_specs = [
                ("pipeline.png",              mod.create_pipeline_chart),
                ("weekly_trend.png",          mod.create_weekly_trend_chart),
                ("salary_distribution.png",   mod.create_salary_distribution_chart),
                ("response_rate.png",         mod.create_response_rate_chart),
            ]
            for filename, fn in chart_specs:
                final_path = os.path.join(charts_dir, filename)
                tmp_path = os.path.join(charts_dir, f".tmp_{filename}")
                try:
                    fn(tracker_path, tmp_path)
                    if os.path.exists(tmp_path):
                        if os.path.exists(final_path):
                            os.remove(final_path)
                        os.rename(tmp_path, final_path)
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self._chart_regen_running = False

    def _schedule_validation_summary(self):
        if self._validation_debounce_id:
            self.after_cancel(self._validation_debounce_id)
        self._validation_debounce_id = self.after(3000, self._run_validation_summary)

    def _run_validation_summary(self):
        tracker_path = _get_tracker_path()
        if not tracker_path or not os.path.exists(tracker_path):
            return
        def task():
            total_errors = 0
            total_warnings = 0
            try:
                import importlib
                if "validate_data" in sys.modules:
                    del sys.modules["validate_data"]
                mod = importlib.import_module("validate_data")
                old_stdout = sys.stdout
                sys.stdout = open(os.devnull, "w")
                try:
                    errors, warnings = mod.validate_applications_sheet(tracker_path)
                    total_errors += len(errors)
                    total_warnings += len(warnings)
                    errors = mod.validate_interview_tracker(tracker_path)
                    total_errors += len(errors)
                    errors = mod.validate_salary_comparison(tracker_path)
                    total_errors += len(errors)
                    errors = mod.validate_email_format(tracker_path)
                    total_errors += len(errors)
                    errors = mod.validate_linkedin_urls(tracker_path)
                    total_errors += len(errors)
                finally:
                    sys.stdout.close()
                    sys.stdout = old_stdout
            except Exception:
                return
            if not self.winfo_exists():
                return
            if total_errors == 0 and total_warnings == 0:
                text = "  ✓ Data valid"
                color = ACCENT2
            else:
                text = f"  ⚠ {total_errors} error(s), {total_warnings} warning(s)"
                color = DANGER if total_errors > 0 else ACCENT3
            try:
                self.after(0, lambda: self._status_validation_lbl.config(text=text, fg=color))
            except Exception:
                pass
        run_in_thread(task, name="validation_summary")
        if self._email_watch_id:
            self.after_cancel(self._email_watch_id)
        self._email_watch_id = self.after(30000, self._poll_email_scheduler)

    def _poll_email_scheduler(self):
        if not self.winfo_exists():
            return
        cfg = _load_settings_cfg()
        notifications = cfg.get("notifications", {})
        when = _parse_clock_time(notifications.get("reminder_time", "09:00"))
        if notifications.get("email_reminder") and when:
            now = datetime.now()
            reminder_key = f"{now.date().isoformat()} {when[0]:02d}:{when[1]:02d}"
            runtime_cfg = self._get_email_runtime_config()
            ready = runtime_cfg.get("to_email") and runtime_cfg.get("from_email") and runtime_cfg.get("password")
            if ready and now.hour == when[0] and now.minute == when[1] and self._email_last_sent_key != reminder_key:
                self._email_last_sent_key = reminder_key
                run_in_thread(self._send_scheduled_email_reminders, name="scheduled_email")
        self._email_watch_id = self.after(30000, self._poll_email_scheduler)

    def _send_scheduled_email_reminders(self):
        try:
            tracker_path = _get_tracker_path()
            if not tracker_path or not os.path.exists(tracker_path):
                return
            import importlib
            if "email_reminder" in sys.modules:
                del sys.modules["email_reminder"]
            mod = importlib.import_module("email_reminder")
            runtime_cfg = self._get_email_runtime_config()
            smtp_config = {
                "from_email": runtime_cfg.get("from_email", ""),
                "smtp_server": runtime_cfg.get("smtp_server", "smtp.gmail.com") or "smtp.gmail.com",
                "smtp_port": int(runtime_cfg.get("smtp_port", 587) or 587),
                "username": runtime_cfg.get("from_email", ""),
                "password": runtime_cfg.get("password", ""),
            }
            days = int(_load_settings_cfg().get("notifications", {}).get("followup_days", 7) or 7)
            pending = mod.check_pending_applications(tracker_path, days)
            if pending:
                mod.send_reminder_email(runtime_cfg.get("to_email", ""), pending, smtp_config)
        except Exception:
            pass

    def _run_startup_backup(self):
        try:
            _run_auto_backup(_load_settings_cfg())
        except Exception:
            pass

    def _open_settings_popup(self):
        popup = tk.Toplevel(self)
        popup.title(t("btn.quick_settings"))
        popup.geometry("500x420")
        popup.configure(bg=BG)
        popup.resizable(False, False)
        popup.grab_set()

        tk.Label(popup, text=t("btn.quick_settings"), font=F_SECTION(),
                 fg=TEXT, bg=BG).pack(anchor="w", padx=24, pady=(20, 4))
        tk.Label(popup, text=t("misc.quick_settings_hint"),
                 font=F_TINY(), fg=TEXT3, bg=BG).pack(anchor="w", padx=24)
        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x", pady=(12, 0))

        body = tk.Frame(popup, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=16)

        try:
            import settings as cfg_mod
            cfg = cfg_mod.load()
        except Exception:
            cfg_mod = None
            cfg = {}

        popup_vars = {}

        def popup_row(label_key, sect, key, default="", show=False):
            r = tk.Frame(body, bg=BG)
            r.pack(fill="x", pady=5)
            tk.Label(r, text=t(label_key), font=F_SMALL(), fg=TEXT3, bg=BG,
                     width=22, anchor="w").pack(side="left")
            var = tk.StringVar(value=str(cfg.get(sect, {}).get(key, default)))
            tk.Entry(r, textvariable=var, font=F_BODY(),
                     bg=SURFACE2, fg=TEXT, relief="flat", width=28,
                     insertbackground=ACCENT, show="*" if show else "",
                     highlightthickness=1, highlightbackground=BORDER,
                     highlightcolor=ACCENT).pack(side="left", ipady=6)
            popup_vars[(sect, key)] = var

        popup_row("field.full_name",     "profile", "full_name")
        popup_row("field.current_role",  "profile", "current_role")
        popup_row("field.field",         "profile", "field", "software development")
        popup_row("field.years_exp",     "profile", "years_exp", "3")
        popup_row("field.daily_goal",    "goals",   "daily_apps", "5")
        popup_row("field.weekly_goal",   "goals",   "weekly_apps", "20")
        popup_row("field.openai_key",    "api",     "openai_key", show=True)

        tk.Frame(popup, bg=BORDER, height=1).pack(fill="x")
        btn_f = tk.Frame(popup, bg=BG)
        btn_f.pack(fill="x", padx=24, pady=12)
        saved_lbl = tk.Label(btn_f, text="", font=F_SMALL(), fg=ACCENT2, bg=BG)

        def popup_save():
            if not cfg_mod:
                return
            try:
                new_cfg = cfg_mod.load()
                for (sect, key), var in popup_vars.items():
                    val = var.get()
                    if key in ("daily_apps", "weekly_apps"):
                        try:
                            val = int(val)
                        except Exception:
                            pass
                    new_cfg.setdefault(sect, {})[key] = val
                cfg_mod.save(new_cfg)
                try:
                    import streak_tracker as st
                    st.set_goals(
                        int(new_cfg.get("goals", {}).get("daily_apps", 5) or 5),
                        int(new_cfg.get("goals", {}).get("weekly_apps", 20) or 20),
                    )
                except Exception:
                    pass
                self._settings_flash_message = t("settings.saved")
                self._apply_live_settings(new_cfg, rebuild_ui=True, refresh_tabs=True)
                saved_lbl.config(text=t("settings.saved"))
                popup.after(2000, lambda: saved_lbl.config(text=""))
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=popup)

        styled_button(btn_f, t("btn.save"), popup_save, color=ACCENT2, width=12).pack(side="left", padx=(0, 8))
        ghost_button(btn_f, t("btn.open_full_settings"),
                     lambda: [popup.destroy(), self._show_tab(11)],
                     width=18).pack(side="left", padx=(0, 8))
        ghost_button(btn_f, t("btn.close"), popup.destroy, width=10).pack(side="left")
        saved_lbl.pack(side="left", padx=(10, 0))

    def _show_tab(self, idx: int):
        self._active_tab = idx
        self.current_tab_index = idx
        for i, tab in enumerate(self.tabs):
            tab.lift() if i == idx else tab.lower()
        for i, (btn, row_f) in enumerate(zip(self.nav_buttons, self._nav_frames)):
            ind = row_f.winfo_children()[0]  # indicator bar
            if i == idx:
                row_f.config(bg=SURFACE)
                for c in row_f.winfo_children(): c.config(bg=SURFACE)
                ind.config(bg=ACCENT)
                btn.config(fg=TEXT, font=F_LABEL())
            else:
                row_f.config(bg=SIDEBAR_BG)
                for c in row_f.winfo_children(): c.config(bg=SIDEBAR_BG)
                ind.config(bg=SIDEBAR_BG)
                btn.config(fg=TEXT2, font=F_BODY())
        # Update window title with current tab name
        if 0 <= idx < len(self._nav_keys):
            tab_name = t(self._nav_keys[idx][0])
            self.title(f"{tab_name}  ·  JobTracker PRO")
        # Auto-refresh data when switching to a tab that supports it
        refresh_fn = getattr(self.tabs[idx], "_refresh_data", None)
        if callable(refresh_fn):
            try:
                refresh_fn()
            except Exception:
                pass
        # Update status bar on tab switch
        self._update_status_bar()

    def _safe_after_cancel(self, after_id):
        if not after_id:
            return
        try:
            self.after_cancel(after_id)
        except tk.TclError:
            pass

    def _on_close(self):
        if getattr(self, "_closing", False):
            return
        self._closing = True
        for after_id in (
            self._tracker_watch_id,
            self._email_watch_id,
            self._status_bar_watch_id,
            self._json_watch_id,
            self._chart_debounce_id,
            self._validation_debounce_id,
        ):
            self._safe_after_cancel(after_id)
        try:
            cfg = _load_settings_cfg()
            if cfg.get("files", {}).get("backup_enabled", True) and cfg.get("files", {}).get("backup_on_exit", False):
                _run_auto_backup(cfg)
        except Exception:
            pass
        # Clean up ALL Tk variables before destroy
        self._cleanup_tk_variables()
        try:
            self.destroy()
        except tk.TclError:
            pass


# ── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
