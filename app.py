"""
app.py – Doc Number Filter (GUI)
=================================
A friendly window where mom can:
  1. Click "Browse..." to pick any .docx from anywhere on the computer
  2. Optionally type a custom name for the output file
  3. Click "Clean Document" to process it
  4. The cleaned file is saved to the "output" folder on the Desktop
     (or next to this script when running in developer mode)
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import subprocess
import sys
import platform
import os

from filter import process_docx   # reuse the existing logic

BASE_DIR = Path(__file__).parent

# When frozen as a .app bundle, save to ~/Desktop/output/ so it's easy to find.
# When running as a plain script (dev), save to ./output/ next to the script.
if getattr(sys, 'frozen', False):
    OUTPUT_DIR = Path.home() / "Desktop" / "Doc Filter Output"
else:
    OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour palette ────────────────────────────────────────────────────────────
BG          = "#1e1e2e"
SURFACE     = "#2a2a3e"
ACCENT      = "#a78bfa"
ACCENT_DARK = "#7c3aed"
TEXT        = "#e2e8f0"
TEXT_DIM    = "#94a3b8"
SUCCESS     = "#34d399"
ERROR_CLR   = "#f87171"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Doc Number Filter")
        self.resizable(False, False)
        self.configure(bg=BG)

        # Centre the window on screen
        w, h = 540, 500
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._selected_file: Path | None = None
        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=ACCENT_DARK, pady=18)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="Doc Number Filter",
            font=("Helvetica", 20, "bold"),
            bg=ACCENT_DARK, fg=TEXT,
        ).pack()
        tk.Label(
            hdr,
            text="Remove numbers & timestamps  ·  Fix paragraphs",
            font=("Helvetica", 11),
            bg=ACCENT_DARK, fg="#c4b5fd",
        ).pack(pady=(2, 0))

        body = tk.Frame(self, bg=BG, padx=34, pady=24)
        body.pack(fill="both", expand=True)

        # ── Step 1: Pick file ─────────────────────────────────────────────────
        self._section(body, "Step 1 · Choose your Word document (.docx)")

        file_row = tk.Frame(body, bg=BG)
        file_row.pack(fill="x", pady=(6, 0))

        self._file_label = tk.Label(
            file_row,
            text="No file selected yet…",
            font=("Helvetica", 11),
            bg=SURFACE, fg=TEXT_DIM,
            anchor="w", padx=10,
            relief="flat", bd=0,
            width=32, wraplength=320,
        )
        self._file_label.pack(side="left", fill="x", expand=True,
                              ipady=8, padx=(0, 10))

        self._btn(file_row, "Browse...", self._pick_file,
                  color="#333350").pack(side="right")

        # ── Step 2: Output name ───────────────────────────────────────────────
        self._section(body, "Step 2 · Output file name  (optional)")
        tk.Label(
            body,
            text="Leave blank to keep the original file name.",
            font=("Helvetica", 10), bg=BG, fg=TEXT_DIM,
        ).pack(anchor="w")

        name_row = tk.Frame(body, bg=BG)
        name_row.pack(fill="x", pady=(6, 0))

        self._name_var = tk.StringVar()
        entry = tk.Entry(
            name_row,
            textvariable=self._name_var,
            font=("Helvetica", 12),
            bg=SURFACE, fg=TEXT,
            insertbackground=TEXT,
            relief="flat", bd=0,
        )
        entry.pack(fill="x", ipady=8, padx=2)
        self._style_entry(entry)

        ext_note = tk.Label(
            body, text="(.docx will be added automatically)",
            font=("Helvetica", 10), bg=BG, fg=TEXT_DIM,
        )
        ext_note.pack(anchor="w", pady=(2, 0))

        # ── Step 3: Go! ───────────────────────────────────────────────────────
        self._section(body, "Step 3 · Clean!")

        self._go_btn = self._btn(
            body, "Clean Document", self._run,
            big=True, color=ACCENT_DARK,
        )
        self._go_btn.pack(fill="x", pady=(6, 0))

        # ── Status bar ────────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Ready – waiting for a file…")
        self._status_lbl = tk.Label(
            self,
            textvariable=self._status_var,
            font=("Helvetica", 11),
            bg=SURFACE, fg=TEXT_DIM,
            anchor="w", padx=16,
        )
        self._status_lbl.pack(fill="x", side="bottom", ipady=10)

    def _section(self, parent, text):
        """Render a subtle section header."""
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", pady=(18, 4))
        tk.Label(
            f, text=text,
            font=("Helvetica", 12, "bold"),
            bg=BG, fg=ACCENT,
        ).pack(anchor="w")
        tk.Frame(f, bg=ACCENT, height=1).pack(fill="x", pady=(4, 0))

    def _btn(self, parent, text, cmd, big=False, color=ACCENT_DARK):
        size = 13 if big else 11
        btn = tk.Button(
            parent,
            text=text,
            command=cmd,
            font=("Helvetica", size, "bold"),
            bg=color, fg=TEXT,
            activebackground=ACCENT,
            activeforeground=TEXT,
            relief="flat", bd=0,
            # highlightbackground forces macOS to render the actual bg colour
            # instead of overriding it with the system button appearance.
            highlightbackground=color,
            highlightthickness=2,
            highlightcolor=ACCENT,
            cursor="hand2",
            padx=18, pady=10 if big else 7,
        )
        self._bind_hover(btn, color)
        return btn

    def _bind_hover(self, widget, normal_color):
        widget.bind("<Enter>", lambda _: widget.config(bg=ACCENT, highlightbackground=ACCENT))
        widget.bind("<Leave>", lambda _: widget.config(bg=normal_color, highlightbackground=normal_color))

    def _style_entry(self, entry):
        """Give the entry a bottom-border feel."""
        entry.config(highlightthickness=2,
                     highlightbackground=SURFACE,
                     highlightcolor=ACCENT)

    # ── Actions ───────────────────────────────────────────────────────────────

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

        # Determine output file name
        custom = self._name_var.get().strip()
        if custom:
            out_name = custom if custom.lower().endswith(".docx") else custom + ".docx"
        else:
            out_name = self._selected_file.name

        dst = OUTPUT_DIR / out_name

        # Disable button while running
        self._go_btn.config(state="disabled", text="Processing...")
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
        """Open the output folder in the system file manager, selecting the file."""
        system = platform.system()
        try:
            if system == "Windows":
                # Open Explorer with the file selected
                subprocess.run(["explorer", "/select,", str(dst).replace("/", "\\")])
            elif system == "Darwin":  # macOS
                subprocess.run(["open", "-R", str(dst)])
            else:  # Linux
                subprocess.run(["xdg-open", str(dst.parent)])
        except Exception:
            # Fallback: just open the folder
            try:
                os.startfile(str(dst.parent))
            except Exception:
                pass

    def _on_success(self, dst: Path):
        self._go_btn.config(state="normal", text="Clean Document")
        self._status(f"Done!  Saved to:  {dst.parent.name}/{dst.name}", SUCCESS)
        self._open_output(dst)

    def _on_error(self, msg: str):
        self._go_btn.config(state="normal", text="Clean Document")
        self._status(f"Error: {msg}", ERROR_CLR)
        messagebox.showerror("Something went wrong", f"Error:\n{msg}")

    def _status(self, text: str, color=TEXT_DIM):
        self._status_var.set(text)
        self._status_lbl.config(fg=color)


if __name__ == "__main__":
    app = App()
    app.mainloop()
