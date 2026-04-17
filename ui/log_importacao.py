import tkinter as tk
from tkinter import ttk
from database.db import get_conn


class TelaLogImportacao(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._build()

    def _build(self):
        ttk.Label(self, text="📋 Histórico de Importações", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))

        ttk.Button(top, text="🔄 Atualizar", command=self._carregar).pack(side="left")
        ttk.Button(top, text="🧹 Limpar Histórico", command=self._limpar).pack(side="left", padx=10)

        self.lbl_total = ttk.Label(top, text="")
        self.lbl_total.pack(side="left", padx=10)

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        colunas = ("id", "empresa", "tabela", "linhas", "arquivo", "data_hora")

        self.tree = ttk.Treeview(frame, columns=colunas, show="headings")

        larguras = {"id": 50, "empresa": 100, "tabela": 120, "linhas": 80, "arquivo": 350, "data_hora": 150}

        for c in colunas:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=larguras.get(c, 120))

        sb_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._carregar()

    def _carregar(self):
        self.tree.delete(*self.tree.get_children())

        with get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM log_importacao ORDER BY id DESC"
            ).fetchall()

        for r in rows:
            self.tree.insert("", "end", values=r)

        self.lbl_total.config(text=f"{len(rows)} registros")

    def _limpar(self):
        from tkinter import messagebox

        if not messagebox.askyesno("Confirmação", "Limpar todo o histórico?"):
            return

        with get_conn() as conn:
            conn.execute("DELETE FROM log_importacao")

        self._carregar()