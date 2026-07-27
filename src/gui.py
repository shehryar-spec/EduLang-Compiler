# ============================================================
# EduLang Compiler  —  Professional GUI
# Run: python gui.py   (inside src/ folder)
# ============================================================

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import re

# ── make sure our own modules are importable ─────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Try customtkinter; fall back to plain tkinter ─────────────
try:
    import customtkinter as ctk
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    USE_CTK = True
except ImportError:
    USE_CTK = False

from compiler import compile_source, format_output

# ── Colours ───────────────────────────────────────────────────
BG        = "#1e1e2e"
PANEL     = "#252535"
ACCENT    = "#7c3aed"
ACCENT2   = "#06b6d4"
SUCCESS   = "#10b981"
ERROR     = "#ef4444"
WARNING   = "#f59e0b"
TEXT      = "#e2e8f0"
SUBTEXT   = "#94a3b8"
BORDER    = "#3f3f5f"
EDIT_BG   = "#11111b"
LINE_BG   = "#181825"
KW_COL    = "#c084fc"
STR_COL   = "#86efac"
NUM_COL   = "#fbbf24"
CMT_COL   = "#6b7280"
OP_COL    = "#67e8f9"

KEYWORDS_HL = {'int','float','string','if','else',
               'while','for','return','main','void'}

FONT_CODE  = ("Courier New", 13)
FONT_UI    = ("Segoe UI", 12)
FONT_HDR   = ("Segoe UI", 13, "bold")

# ── Helpers ───────────────────────────────────────────────────

def make_btn(parent, text, cmd, bg=ACCENT, fg="white",
             width=None, font=FONT_UI):
    cfg = dict(text=text, command=cmd, bg=bg, fg=fg,
               font=font, relief="flat", cursor="hand2",
               activebackground=BORDER, activeforeground="white",
               bd=0, padx=14, pady=7)
    if width:
        cfg["width"] = width
    return tk.Button(parent, **cfg)


def make_label(parent, text, fg=TEXT, font=FONT_UI, bg=None):
    return tk.Label(parent, text=text, fg=fg,
                    font=font, bg=bg or PANEL)


# ── Line-number widget ────────────────────────────────────────

class LineNumbers(tk.Canvas):
    def __init__(self, master, text_widget, **kw):
        super().__init__(master, width=46, bg=LINE_BG,
                         highlightthickness=0, **kw)
        self.tw = text_widget
        self.tw.bind("<KeyRelease>",  self.redraw)
        self.tw.bind("<MouseWheel>",  self.redraw)
        self.tw.bind("<ButtonPress>", self.redraw)
        self.tw.bind("<Configure>",   self.redraw)

    def redraw(self, *_):
        self.delete("all")
        i = self.tw.index("@0,0")
        while True:
            dline = self.tw.dlineinfo(i)
            if dline is None:
                break
            y   = dline[1]
            num = i.split(".")[0]
            self.create_text(38, y, anchor="ne", text=num,
                             fill=SUBTEXT, font=("Courier New", 11))
            next_i = self.tw.index(f"{i}+1line")
            if next_i == i:
                break
            i = next_i


# ── Syntax highlighter ────────────────────────────────────────

class SyntaxHighlighter:
    PATTERNS = [
        ("comment", r"//[^\n]*"),
        ("string",  r'"[^"\n]*"?'),
        ("keyword", r'\b(?:' + '|'.join(KEYWORDS_HL) + r')\b'),
        ("number",  r'\b\d+(?:\.\d+)?\b'),
        ("op",      r'[+\-*/=<>!]+'),
    ]
    COLOURS = {
        "comment": CMT_COL,
        "string":  STR_COL,
        "keyword": KW_COL,
        "number":  NUM_COL,
        "op":      OP_COL,
    }

    def __init__(self, text_widget):
        self.tw = text_widget
        for tag, colour in self.COLOURS.items():
            bold = "bold" if tag == "keyword" else ""
            self.tw.tag_configure(tag, foreground=colour,
                                  font=("Courier New", 13, bold) if bold
                                  else FONT_CODE)

    def highlight(self, *_):
        for tag in self.COLOURS:
            self.tw.tag_remove(tag, "1.0", "end")
        content = self.tw.get("1.0", "end")
        for tag, pattern in self.PATTERNS:
            for m in re.finditer(pattern, content):
                s = f"1.0+{m.start()}c"
                e = f"1.0+{m.end()}c"
                self.tw.tag_add(tag, s, e)


# ── Main Application Window ───────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EduLang Compiler  —  Professional Edition")
        self.geometry("1420x880")
        self.minsize(1000, 650)
        self.configure(bg=BG)

        self._input_file  = None
        self._last_result = None
        self._last_report = ""

        self._build_titlebar()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

        self._load_sample_code(SAMPLE_VALID)

    # ── Title bar ─────────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg=ACCENT, height=50)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar,
                 text="  🚀  EduLang Compiler  —  Professional IDE",
                 bg=ACCENT, fg="white",
                 font=("Segoe UI", 16, "bold")
                 ).pack(side="left", padx=18, pady=10)

        tk.Label(bar, text="v1.0  |  Compiler Construction Lab",
                 bg=ACCENT, fg="#c4b5fd",
                 font=("Segoe UI", 10)
                 ).pack(side="right", padx=18)

    # ── Toolbar ───────────────────────────────────────────────
    def _build_toolbar(self):
        tb = tk.Frame(self, bg=PANEL, height=56)
        tb.pack(fill="x")
        tb.pack_propagate(False)

        btns = [
            ("📂  Open",    self._open,    ACCENT),
            ("💾  Save",    self._save,    "#374151"),
            ("▶  COMPILE",  self._compile, SUCCESS),
            ("📤  Save Output", self._save_output, ACCENT2),
            ("🗑  Clear",   self._clear,   "#4b5563"),
        ]
        for txt, cmd, col in btns:
            make_btn(tb, txt, cmd, bg=col,
                     font=("Segoe UI", 12, "bold")
                     ).pack(side="left", padx=6, pady=10)

        # separator
        tk.Frame(tb, bg=BORDER, width=2).pack(
            side="left", fill="y", padx=8, pady=8)

        tk.Label(tb, text="Load Sample:", bg=PANEL,
                 fg=SUBTEXT, font=FONT_UI
                 ).pack(side="left", padx=(4, 2))

        self._sample_var = tk.StringVar(value="-- select --")
        samples = ["Valid Program", "Lexical Errors",
                   "Syntax Errors", "Semantic Errors", "For Loop"]
        om = tk.OptionMenu(tb, self._sample_var, *samples,
                           command=self._load_sample_cb)
        om.configure(bg=PANEL, fg=TEXT, font=FONT_UI,
                     relief="flat", bd=0,
                     activebackground=BORDER,
                     highlightthickness=0)
        om["menu"].configure(bg=PANEL, fg=TEXT, font=FONT_UI,
                             activebackground=ACCENT)
        om.pack(side="left", padx=4)

    # ── Body (editor + output) ────────────────────────────────
    def _build_body(self):
        pane = tk.PanedWindow(self, orient="horizontal",
                              bg=BG, sashwidth=6,
                              sashrelief="flat")
        pane.pack(fill="both", expand=True, padx=4, pady=4)

        # ── Left: Code Editor ──────────────────────────────
        left = tk.Frame(pane, bg=BG)
        pane.add(left, minsize=480)
        pane.paneconfigure(left, width=680)

        # editor header
        eh = tk.Frame(left, bg=PANEL, height=34)
        eh.pack(fill="x")
        eh.pack_propagate(False)
        tk.Label(eh, text="  📝  Source Code Editor",
                 bg=PANEL, fg=TEXT, font=FONT_HDR
                 ).pack(side="left", padx=10, pady=6)

        # editor area
        editor_row = tk.Frame(left, bg=EDIT_BG)
        editor_row.pack(fill="both", expand=True)

        self.editor = tk.Text(
            editor_row,
            bg=EDIT_BG, fg=TEXT,
            insertbackground=ACCENT2,
            selectbackground=ACCENT,
            font=FONT_CODE,
            relief="flat", bd=0,
            wrap="none", undo=True,
            padx=10, pady=8,
        )

        vsb_e = ttk.Scrollbar(editor_row, orient="vertical",
                               command=self.editor.yview)
        vsb_e.pack(side="right", fill="y")
        self.editor.configure(yscrollcommand=vsb_e.set)

        self.ln = LineNumbers(editor_row, self.editor)
        self.ln.pack(side="left", fill="y")

        self.editor.pack(side="left", fill="both", expand=True)

        hsb_e = ttk.Scrollbar(left, orient="horizontal",
                               command=self.editor.xview)
        hsb_e.pack(fill="x")
        self.editor.configure(xscrollcommand=hsb_e.set)

        # syntax highlighter
        self.hl = SyntaxHighlighter(self.editor)
        self.editor.bind("<KeyRelease>", self._on_edit)

        # ── Right: Output Panel ────────────────────────────
        right = tk.Frame(pane, bg=BG)
        pane.add(right, minsize=380)
        pane.paneconfigure(right, width=700)

        # tab bar
        oh = tk.Frame(right, bg=PANEL, height=34)
        oh.pack(fill="x")
        oh.pack_propagate(False)
        tk.Label(oh, text="  📊  Compiler Output",
                 bg=PANEL, fg=TEXT, font=FONT_HDR
                 ).pack(side="left", padx=10, pady=6)

        tab_bar = tk.Frame(right, bg=PANEL)
        tab_bar.pack(fill="x")

        self._tabs = [
            "📋 Tokens", "🔴 Lex Errors",
            "🟡 Syntax",  "🔵 Semantic",
            "📦 Symbols", "⚡ TAC", "📄 Full Report"
        ]
        self._tab_content  = {t: "" for t in self._tabs}
        self._tab_btns     = {}
        self._active_tab   = self._tabs[0]

        for tab in self._tabs:
            btn = tk.Button(
                tab_bar, text=tab,
                bg=PANEL, fg=SUBTEXT,
                font=("Segoe UI", 10),
                relief="flat", bd=0, cursor="hand2",
                padx=8, pady=6,
                activebackground=BORDER,
                command=lambda t=tab: self._show_tab(t))
            btn.pack(side="left", padx=2, pady=4)
            self._tab_btns[tab] = btn

        # output text
        out_frame = tk.Frame(right, bg=EDIT_BG)
        out_frame.pack(fill="both", expand=True, padx=3, pady=3)

        self.out_text = tk.Text(
            out_frame,
            bg=EDIT_BG, fg=TEXT,
            font=FONT_CODE,
            relief="flat", bd=0,
            wrap="none", state="disabled",
            padx=10, pady=8,
        )
        vsb_o = ttk.Scrollbar(out_frame, orient="vertical",
                               command=self.out_text.yview)
        vsb_o.pack(side="right", fill="y")
        self.out_text.configure(yscrollcommand=vsb_o.set)
        self.out_text.pack(side="left", fill="both", expand=True)

        hsb_o = ttk.Scrollbar(right, orient="horizontal",
                               command=self.out_text.xview)
        hsb_o.pack(fill="x")
        self.out_text.configure(xscrollcommand=hsb_o.set)

        # output text tags
        self.out_text.tag_configure(
            "err",  foreground=ERROR,   font=("Courier New", 13, "bold"))
        self.out_text.tag_configure(
            "ok",   foreground=SUCCESS)
        self.out_text.tag_configure(
            "warn", foreground=WARNING)
        self.out_text.tag_configure(
            "hdr",  foreground=ACCENT2, font=("Courier New", 13, "bold"))
        self.out_text.tag_configure(
            "tac",  foreground="#a5f3fc")
        self.out_text.tag_configure(
            "sym",  foreground=STR_COL)

        self._show_tab(self._tabs[0])

    # ── Status bar ────────────────────────────────────────────
    def _build_statusbar(self):
        self.status_bar = tk.Frame(self, bg=PANEL, height=28)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        self._status_lbl = tk.Label(
            self.status_bar, text="  Ready",
            bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 11),
            anchor="w")
        self._status_lbl.pack(fill="x", padx=10)

    def _set_status(self, msg, colour=None):
        self._status_lbl.configure(
            text=f"  {msg}", fg=colour or SUBTEXT)

    # ── Tab logic ─────────────────────────────────────────────
    def _show_tab(self, name):
        self._active_tab = name
        for t, btn in self._tab_btns.items():
            if t == name:
                btn.configure(bg=ACCENT, fg="white")
            else:
                btn.configure(bg=PANEL, fg=SUBTEXT)
        self._render_output(self._tab_content[name])

    def _render_output(self, text):
        self.out_text.configure(state="normal")
        self.out_text.delete("1.0", "end")
        for line in text.split("\n"):
            lo = line.lower()
            if "error" in lo or line.strip().startswith("[error]"):
                tag = "err"
            elif ("passed" in lo or "successful" in lo or
                  "no lexical" in lo or "no syntax" in lo):
                tag = "ok"
            elif ("skipped" in lo or "halted" in lo or
                  "not generated" in lo):
                tag = "warn"
            elif (line.startswith("=") or
                  line.strip().startswith("[") or
                  line.strip().startswith("FUNC") or
                  line.strip().startswith("END")):
                tag = "hdr"
            elif "goto" in lo or line.strip().startswith("t") or \
                    "return" in lo:
                tag = "tac"
            else:
                tag = None
            self.out_text.insert(
                "end", line + "\n", tag if tag else ())
        self.out_text.configure(state="disabled")
        self.out_text.see("1.0")

    # ── Editor events ─────────────────────────────────────────
    def _on_edit(self, *_):
        self.hl.highlight()
        self.ln.redraw()

    # ── File actions ──────────────────────────────────────────
    def _open(self):
        path = filedialog.askopenfilename(
            title="Open EduLang Source",
            filetypes=[("Text / EduLang", "*.txt *.edu"),
                       ("All files", "*.*")])
        if not path:
            return
        self._input_file = path
        with open(path, "r", encoding="utf-8") as f:
            self._load_sample_code(f.read())
        self._set_status(f"Opened: {os.path.basename(path)}", ACCENT2)

    def _save(self):
        if not self._input_file:
            path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All", "*.*")])
            if not path:
                return
            self._input_file = path
        with open(self._input_file, "w", encoding="utf-8") as f:
            f.write(self._get_code())
        self._set_status(f"Saved: {os.path.basename(self._input_file)}", SUCCESS)

    def _save_output(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            initialfile="output.txt",
            filetypes=[("Text files", "*.txt"), ("All", "*.*")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(self._last_report)
        self._set_status(f"Output saved: {os.path.basename(path)}", SUCCESS)

    def _clear(self):
        self.editor.delete("1.0", "end")
        for k in self._tab_content:
            self._tab_content[k] = ""
        self._render_output("")
        self.ln.redraw()
        self._set_status("Cleared.", SUBTEXT)

    # ── Compile ───────────────────────────────────────────────
    def _compile(self):
        src = self._get_code().strip()
        if not src:
            messagebox.showwarning("Empty", "Please enter source code first.")
            return
        self._set_status("⏳  Compiling…", WARNING)
        self.update()

        def _run():
            result = compile_source(src)
            report = format_output(src, result)
            # also write output.txt next to this script
            out_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "output.txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(report)
            self.after(0, lambda: self._on_done(result, report))

        threading.Thread(target=_run, daemon=True).start()

    def _on_done(self, result, report):
        self._last_result = result
        self._last_report = report

        # ── Tokens tab
        lines = [f"  {'Line':<6} {'Type':<15} Value",
                 "  " + "-" * 44]
        for t in result.tokens:
            lines.append(f"  {t.line:<6} {t.type:<15} {t.value}")
        self._tab_content["📋 Tokens"] = "\n".join(lines)

        # ── Lex Errors tab
        if result.lexical_errors:
            self._tab_content["🔴 Lex Errors"] = "\n".join(
                f"  [ERROR] {repr(e)}" for e in result.lexical_errors)
        else:
            self._tab_content["🔴 Lex Errors"] = \
                "  No lexical errors found."

        # ── Syntax tab
        if result.lexical_errors:
            self._tab_content["🟡 Syntax"] = \
                "  Skipped (lexical errors present)."
        elif result.parse_errors:
            self._tab_content["🟡 Syntax"] = "\n".join(
                f"  [ERROR] {repr(e)}" for e in result.parse_errors)
        else:
            self._tab_content["🟡 Syntax"] = \
                "  Syntax analysis passed successfully."

        # ── Semantic tab
        if result.lexical_errors or result.parse_errors:
            self._tab_content["🔵 Semantic"] = \
                "  Skipped (earlier errors present)."
        elif result.semantic_errors:
            self._tab_content["🔵 Semantic"] = "\n".join(
                f"  [ERROR] {repr(e)}" for e in result.semantic_errors)
        else:
            self._tab_content["🔵 Semantic"] = \
                "  Semantic analysis passed successfully."

        # ── Symbol Table tab
        if result.symbol_table:
            rows = [f"  {'Name':<20} {'Type':<12} Declared at Line",
                    "  " + "-" * 46]
            for name, info in result.symbol_table.items():
                rows.append(
                    f"  {name:<20} {info['type']:<12} {info['line']}")
            self._tab_content["📦 Symbols"] = "\n".join(rows)
        else:
            self._tab_content["📦 Symbols"] = "  Empty."

        # ── TAC tab
        if result.tac:
            self._tab_content["⚡ TAC"] = "\n".join(
                f"  {i}" for i in result.tac)
        else:
            self._tab_content["⚡ TAC"] = \
                "  Not generated (errors present)."

        # ── Full report tab
        self._tab_content["📄 Full Report"] = report

        # refresh
        self._show_tab(self._active_tab)

        # status bar
        total_err = (len(result.lexical_errors) +
                     len(result.parse_errors) +
                     len(result.semantic_errors))
        if result.success:
            self._set_status("✔  Compilation successful!", SUCCESS)
        else:
            self._set_status(
                f"✖  Compilation failed  —  {total_err} error(s).", ERROR)

    # ── Helpers ───────────────────────────────────────────────
    def _get_code(self):
        return self.editor.get("1.0", "end-1c")

    def _load_sample_code(self, code):
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", code)
        self.hl.highlight()
        self.ln.redraw()

    def _load_sample_cb(self, name):
        mapping = {
            "Valid Program":   SAMPLE_VALID,
            "Lexical Errors":  SAMPLE_LEXICAL,
            "Syntax Errors":   SAMPLE_SYNTAX,
            "Semantic Errors": SAMPLE_SEMANTIC,
            "For Loop":        SAMPLE_FOR,
        }
        self._load_sample_code(mapping.get(name, ""))
        self._set_status(f"Sample loaded: {name}", ACCENT2)


# ── Sample programs ───────────────────────────────────────────

SAMPLE_VALID = """\
int main() {
    int x = 10;
    int y = 20;
    int z;
    z = x + y * 2;
    if (z > 30) {
        z = z - 5;
    }
    else {
        z = z + 5;
    }
    while (z > 0) {
        z = z - 1;
    }
    return z;
}
"""

SAMPLE_LEXICAL = """\
int main()
{
    int 2x = 10;
    float rate = 5.5;
    string name = "Ali;
    total = 2x + rate;
    if (name > 5) {
        return name;
    }
}
"""

SAMPLE_SYNTAX = """\
int main() {
    int x = 10
    int y = 20;
    if (x > 5 {
        return x;
    }
}
"""

SAMPLE_SEMANTIC = """\
int main() {
    int x = 10;
    float rate = 5.5;
    string name = "Alice";
    total = x + rate;
    if (name > 5) {
        return name;
    }
    return x;
}
"""

SAMPLE_FOR = """\
int main() {
    int x = 0;
    for (int i = 0; i < 3; i = i + 1) {
        x = x + i;
    }
    return x;
}
"""

# ── Entry point ───────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()