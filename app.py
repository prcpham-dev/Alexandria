"""
app.py – Alexandria
====================
Transcript cleaner: removes line numbers & timestamps, merges/splits paragraphs.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import subprocess
import sys
import platform
import os

from filter import process_docx

BASE_DIR = Path(__file__).parent

# Save to Desktop when running as frozen bundle; ./output/ in dev mode.
if getattr(sys, "frozen", False):
    OUTPUT_DIR = Path.home() / "Desktop" / "Alexandria Output"
else:
    OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ─────────────────────────────────────────────────────────────
BG          = "#1e1e2e"
SURFACE     = "#2a2a3e"
ACCENT      = "#a78bfa"
ACCENT_DARK = "#7c3aed"
TEXT        = "#e2e8f0"
TEXT_DIM    = "#94a3b8"
SUCCESS     = "#34d399"
ERROR_CLR   = "#f87171"
BTN_BROWSE  = "#3d3d5c"   # distinct dark-slate for Browse button


# ── Reliable custom button (Frame + Label) ─────────────────────────────────────
# tk.Button on macOS ignores bg colour when relief="flat".
# Using a Frame+Label gives us full colour control on every platform.

class FlatButton(tk.Frame):
    """A Frame+Label that acts as a fully custom-coloured button."""

    def __init__(self, parent, text, command,
                 bg=ACCENT_DARK, fg=TEXT, font_size=11, big=False):
        super().__init__(parent, bg=bg, cursor="hand2")
        self._normal_bg = bg
        self._command   = command
        self._enabled   = True

        pady = 12 if big else 8
        self._lbl = tk.Label(
            self, text=text, bg=bg, fg=fg,
            font=("Helvetica", font_size, "bold"),
            padx=18, pady=pady,
        )
        self._lbl.pack(fill="both", expand=True)

        for w in (self, self._lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    # ── state helpers ──────────────────────────────────────────────────────────

    def set_state(self, enabled: bool, text: str | None = None):
        self._enabled = enabled
        if text:
            self._lbl.config(text=text)
        bg = self._normal_bg if enabled else SURFACE
        fg = TEXT if enabled else TEXT_DIM
        self.config(bg=bg)
        self._lbl.config(bg=bg, fg=fg)
        self.config(cursor="hand2" if enabled else "arrow")

    # ── event handlers ─────────────────────────────────────────────────────────

    def _on_click(self, _=None):
        if self._enabled:
            self._command()

    def _on_enter(self, _=None):
        if self._enabled:
            self._set_bg(ACCENT)

    def _on_leave(self, _=None):
        self._set_bg(self._normal_bg if self._enabled else SURFACE)

    def _set_bg(self, color):
        self.config(bg=color)
        self._lbl.config(bg=color)


# ── Main application ───────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Alexandria")
        self.resizable(False, False)
        self.configure(bg=BG)

        w, h = 540, 500
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._selected_file: Path | None = None
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=ACCENT_DARK, pady=18)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Alexandria",
                 font=("Helvetica", 22, "bold"),
                 bg=ACCENT_DARK, fg=TEXT).pack()
        tk.Label(hdr, text="Remove numbers & timestamps  ·  Fix paragraphs",
                 font=("Helvetica", 11),
                 bg=ACCENT_DARK, fg="#c4b5fd").pack(pady=(2, 0))

        body = tk.Frame(self, bg=BG, padx=34, pady=20)
        body.pack(fill="both", expand=True)

        # Step 1
        self._section(body, "Step 1  ·  Choose your Word document (.docx)")
        file_row = tk.Frame(body, bg=BG)
        file_row.pack(fill="x", pady=(6, 0))

        self._file_label = tk.Label(
            file_row, text="No file selected yet…",
            font=("Helvetica", 11),
            bg=SURFACE, fg=TEXT_DIM,
            anchor="w", padx=10,
            relief="flat", bd=0,
            width=32, wraplength=320,
        )
        self._file_label.pack(side="left", fill="x", expand=True,
                              ipady=8, padx=(0, 10))

        FlatButton(file_row, "Browse...", self._pick_file,
                   bg=BTN_BROWSE).pack(side="right")

        # Step 2
        self._section(body, "Step 2  ·  Output file name  (optional)")
        tk.Label(body, text="Leave blank to keep the original file name.",
                 font=("Helvetica", 10), bg=BG, fg=TEXT_DIM).pack(anchor="w")

        name_row = tk.Frame(body, bg=BG)
        name_row.pack(fill="x", pady=(6, 0))

        self._name_var = tk.StringVar()
        entry = tk.Entry(
            name_row, textvariable=self._name_var,
            font=("Helvetica", 12),
            bg=SURFACE, fg=TEXT, insertbackground=TEXT,
            relief="flat", bd=0,
            highlightthickness=2,
            highlightbackground=SURFACE,
            highlightcolor=ACCENT,
        )
        entry.pack(fill="x", ipady=8, padx=2)

        tk.Label(body, text="(.docx will be added automatically)",
                 font=("Helvetica", 10), bg=BG, fg=TEXT_DIM
                 ).pack(anchor="w", pady=(2, 0))

        # Step 3
        self._section(body, "Step 3  ·  Clean!")
        self._go_btn = FlatButton(body, "Clean Document", self._run,
                                  bg=ACCENT_DARK, font_size=13, big=True)
        self._go_btn.pack(fill="x", pady=(6, 0))

        # Status bar
        self._status_var = tk.StringVar(value="Ready – select a file to begin.")
        self._status_lbl = tk.Label(
            self, textvariable=self._status_var,
            font=("Helvetica", 11),
            bg=SURFACE, fg=TEXT_DIM,
            anchor="w", padx=16,
        )
        self._status_lbl.pack(fill="x", side="bottom", ipady=10)

    def _section(self, parent, text):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(18, 4))
        tk.Label(f, text=text,
                 font=("Helvetica", 12, "bold"),
                 bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Frame(f, bg=ACCENT, height=1).pack(fill="x", pady=(4, 0))

    # ── Actions ────────────────────────────────────────────────────────────────

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Select a Word document",
            filetypes=[("Word documents", "*.docx"), ("All files", "*.*")],
        )
        if not path:
            return
        self._selected_file = Path(path)
        short = self._selected_file.name
        if len(short) > 40:
            short = "…" + short[-38:]
        self._file_label.config(text=short, fg=TEXT)
        self._status(f"Selected: {self._selected_file.name}", TEXT_DIM)

    def _run(self):
        if not self._selected_file or not self._selected_file.exists():
            self._status("Please choose a .docx file first.", ERROR_CLR)
            messagebox.showwarning(
                "No file selected",
                "Please click 'Browse...' and select a Word document first.",
            )
            return

        custom = self._name_var.get().strip()
        if custom:
            out_name = custom if custom.lower().endswith(".docx") else custom + ".docx"
        else:
            # Default: Test.docx → Test_filtered.docx
            out_name = self._selected_file.stem + "_filtered" + self._selected_file.suffix
        dst = OUTPUT_DIR / out_name

        self._go_btn.set_state(False, "Processing...")
        self._status("Processing, please wait...", ACCENT)

        def worker():
            try:
                process_docx(self._selected_file, dst)
                self.after(0, self._on_success, dst)
            except Exception as exc:
                self.after(0, self._on_error, str(exc))

        threading.Thread(target=worker, daemon=True).start()

    @staticmethod
    def _open_output(dst: Path):
        """Open the output folder in the OS file manager, highlighting the file."""
        try:
            system = platform.system()
            if system == "Windows":
                subprocess.run(["explorer", "/select,",
                                str(dst).replace("/", "\\")])
            elif system == "Darwin":
                subprocess.run(["open", "-R", str(dst)])
            else:
                subprocess.run(["xdg-open", str(dst.parent)])
        except Exception:
            try:
                os.startfile(str(dst.parent))
            except Exception:
                pass

    def _on_success(self, dst: Path):
        self._go_btn.set_state(True, "Clean Document")
        self._status(f"Done!  Saved to: {dst.parent.name}/{dst.name}", SUCCESS)
        self._open_output(dst)

    def _on_error(self, msg: str):
        self._go_btn.set_state(True, "Clean Document")
        self._status(f"Error: {msg}", ERROR_CLR)
        messagebox.showerror("Something went wrong", f"Error:\n{msg}")

    def _status(self, text: str, color=TEXT_DIM):
        self._status_var.set(text)
        self._status_lbl.config(fg=color)


if __name__ == "__main__":
    app = App()
    app.mainloop()
