#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

from pycells_mds.core import PyCells
from pycells_mds.session import init_db, _expand_range

COLUMNS = ["A", "B", "C", "D", "E"]
ROWS = list(range(1, 11))


class MiniExcel:
    def __init__(self, root):
        self.root = root
        root.title("PyCells Mini Excel Demo")

        init_db({"engine": "sqlite", "path": "tk_demo.db"})
        self.pc = PyCells()

        user_id, tbl, sheet = self.pc.quick_start()
        self.user_id = user_id
        self.table = tbl.model.name
        self.sheet = sheet.model.name

        self.active_cell = None

        self.formula_var = tk.StringVar()
        self.cell_id_var = tk.StringVar()
        self.cursor_var = tk.StringVar()

        self.create_ui()
        self.refresh_grid()

    # ----------------------------------------------------------------------------
    # UI
    # ----------------------------------------------------------------------------
    def create_ui(self):
        frm = ttk.Frame(self.root)
        frm.pack(fill="both", expand=True, padx=10, pady=10)

        # Formula input
        ttk.Label(frm, text="Formula:").grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(frm, textvariable=self.formula_var, width=50)
        entry.grid(row=0, column=1, columnspan=10, sticky="we")
        entry.bind("<Return>", self.on_formula_enter)

        # Cell ID input
        ttk.Label(frm, text="Cell ID:").grid(row=1, column=0, sticky="w")
        cellid_entry = ttk.Entry(frm, textvariable=self.cell_id_var, width=30)
        cellid_entry.grid(row=1, column=1, sticky="we")
        cellid_entry.bind("<Return>", self.on_cell_id_enter)

        # Cursor input
        ttk.Label(frm, text="Cursor:").grid(row=2, column=0, sticky="w")
        cursor_entry = ttk.Entry(frm, textvariable=self.cursor_var, width=30)
        cursor_entry.grid(row=2, column=1, sticky="we")
        cursor_entry.bind("<Return>", self.on_cursor_enter)

        # Grid area
        self.grid_frame = ttk.Frame(frm)
        self.grid_frame.grid(row=3, column=0, columnspan=20, pady=10)

        ttk.Label(self.grid_frame, text="", width=4).grid(row=0, column=0)
        for j, c in enumerate(COLUMNS):
            ttk.Label(self.grid_frame, text=c, width=8, anchor="center").grid(row=0, column=j + 1)

        self.vars = {f"{c}{r}": tk.StringVar() for c in COLUMNS for r in ROWS}
        self.buttons = {}

        for r in ROWS:
            ttk.Label(self.grid_frame, text=str(r), width=4).grid(row=r, column=0)

            for j, c in enumerate(COLUMNS):
                name = f"{c}{r}"
                var = self.vars[name]
                btn = ttk.Button(
                    self.grid_frame, textvariable=var, width=8,
                    command=lambda n=name: self.select_cell(n)
                )
                btn.grid(row=r, column=j + 1)
                self.buttons[name] = btn

        # Recalc button
        ttk.Button(frm, text="Recalc", command=self.recalc).grid(row=4, column=0, pady=5, sticky="w")

        # ----------------------------
        # Export panel
        # ----------------------------
        export_frame = ttk.Frame(frm)
        export_frame.grid(row=5, column=0, columnspan=20, pady=10, sticky="w")

        ttk.Label(export_frame, text="Export mode:").grid(row=0, column=0, padx=5)

        self.export_mode = tk.StringVar(value="json")
        mode_select = ttk.Combobox(
            export_frame,
            textvariable=self.export_mode,
            values=["json", "flat", "tree"],
            width=10,
            state="readonly"
        )
        mode_select.grid(row=0, column=1)

        ttk.Button(export_frame, text="Export", command=self.on_export).grid(row=0, column=2, padx=10)

    # ----------------------------------------------------------------------------
    # Handlers
    # ----------------------------------------------------------------------------
    def select_cell(self, name):
        self.active_cell = name
        info = self.pc.read(self.table, self.sheet, name, self.user_id)

        self.formula_var.set(info.get("data") or "")
        self.cell_id_var.set(info.get("cell_id") or "")

        self.pc.set_active_cursor(self.table, self.sheet, [name], self.user_id)

    def on_formula_enter(self, event=None):
        if not self.active_cell:
            return
        raw = self.formula_var.get().strip()
        self.pc.write(self.table, self.sheet, self.active_cell,
                      self.cell_id_var.get().strip() or None,
                      raw, self.user_id)
        self.refresh_grid()

    def on_cell_id_enter(self, event=None):
        if not self.active_cell:
            return
        cid = self.cell_id_var.get().strip()
        data = self.pc.read(self.table, self.sheet, self.active_cell, self.user_id).get("data", "")
        try:
            self.pc.write(self.table, self.sheet, self.active_cell, cid, data, self.user_id)
        except Exception as e:
            self.show_popup(f"Cell ID update failed:\n{e}")
        self.refresh_grid()

    def on_cursor_enter(self, event=None):
        expr = self.cursor_var.get().strip()
        if not expr:
            return
        try:
            parts = [p.strip() for p in expr.split(",") if p.strip()]
            cells = []
            for p in parts:
                if ":" in p:
                    cells.extend(_expand_range(p))
                else:
                    cells.append(p.upper())
            self.pc.set_active_cursor(self.table, self.sheet, cells, self.user_id)
            self.show_popup(f"Cursor updated:\n{cells}")
        except Exception as e:
            self.show_popup(f"Cursor update failed:\n{e}")

    def recalc(self):
        self.pc.recalc(self.table, self.sheet, self.user_id)
        self.refresh_grid()

    # ----------------------------------------------------------------------------
    # Export
    # ----------------------------------------------------------------------------
    def on_export(self):
        mode = self.export_mode.get()

        try:
            data = self.pc.export(self.table, self.sheet, mode, self.user_id)
        except Exception as e:
            self.show_popup(f"Export failed:\n{e}")
            return

        import json
        text = json.dumps(data, indent=4, ensure_ascii=False)

        win = tk.Toplevel(self.root)
        win.title(f"Export: {mode}")

        txt = tk.Text(win, wrap="none", width=100, height=40)
        txt.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
        scroll_y.pack(side="right", fill="y")
        txt.configure(yscrollcommand=scroll_y.set)

        scroll_x = ttk.Scrollbar(win, orient="horizontal", command=txt.xview)
        scroll_x.pack(side="bottom", fill="x")
        txt.configure(xscrollcommand=scroll_x.set)

        txt.insert("1.0", text)
        txt.config(state="disabled")

    # ----------------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------------
    def show_popup(self, msg):
        win = tk.Toplevel(self.root)
        win.title("Info")
        ttk.Label(win, text=msg, justify="left").pack(padx=20, pady=20)
        ttk.Button(win, text="OK", command=win.destroy).pack(pady=5)

    def refresh_grid(self):
        for c in COLUMNS:
            for r in ROWS:
                name = f"{c}{r}"
                info = self.pc.read(self.table, self.sheet, name, self.user_id)
                val = info.get("value") or ""
                self.vars[name].set(val)

        for nm, btn in self.buttons.items():
            if nm == self.active_cell:
                btn.configure(style="Selected.TButton")
            else:
                btn.configure(style="TButton")


def main():
    root = tk.Tk()

    style = ttk.Style()
    style.configure("Selected.TButton", background="#88c", foreground="white")

    MiniExcel(root)
    root.mainloop()


if __name__ == "__main__":
    main()
