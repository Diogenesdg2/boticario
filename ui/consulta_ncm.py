import tkinter as tk
from tkinter import ttk, messagebox
from database.db import get_conn
from utils.exportar import exportar_treeview


NCM_FILTROS = [
    ("empresa_codigo", "Empresa"),
    ("codigo_do_item", "Cód. Item"),
    ("ncm",            "NCM"),
    ("cest",           "CEST"),
]


class TelaConsultaNCM(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._filtros_vars = {}
        self._empresas_map = {}
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Consulta: NCM E CEST",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # ── Filtros ─────────────────────────────────────
        frm = ttk.LabelFrame(self, text="Filtros", padding=10)
        frm.pack(fill="x", pady=(0, 8))

        for i, (col_sql, label) in enumerate(NCM_FILTROS):
            ttk.Label(frm, text=label).grid(row=0, column=i*2, sticky="w")

            var = tk.StringVar()
            self._filtros_vars[col_sql] = var

            if col_sql == "empresa_codigo":
                self.cbo = ttk.Combobox(frm, textvariable=var, state="readonly", width=25)
                self.cbo.grid(row=0, column=i*2 + 1, padx=5)
            else:
                ttk.Entry(frm, textvariable=var, width=20).grid(row=0, column=i*2 + 1, padx=5)

        # Botões
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=1, column=0, columnspan=8, pady=8, sticky="w")

        ttk.Button(btn_frame, text="🔄 Empresas", command=self._load_empresas).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔍 Filtrar", command=self._consultar).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🧹 Limpar", command=self._limpar).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="📤 Exportar Excel", command=self._exportar).pack(side="left", padx=(8, 0))

        self.lbl_total = ttk.Label(btn_frame, text="")
        self.lbl_total.pack(side="left", padx=10)

        # ── Tabela ─────────────────────────────────────
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        colunas = ["empresa_codigo", "codigo_do_item", "ncm", "cest"]

        self.tree = ttk.Treeview(frame, columns=colunas, show="headings")

        for c in colunas:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)

        sb_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._load_empresas()

    # ─────────────────────────────────────────

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()

        self._empresas_map = {f"{c} - {n}": c for c, n in rows}
        valores = ["(Todas)"] + list(self._empresas_map.keys())

        self.cbo["values"] = valores
        self.cbo.current(0)

    def _limpar(self):
        for var in self._filtros_vars.values():
            var.set("")
        self.cbo.current(0)

    def _consultar(self):
        where = []
        params = []

        for col, var in self._filtros_vars.items():
            val = var.get().strip()

            if not val or val == "(Todas)":
                continue

            if col == "empresa_codigo":
                codigo = self._empresas_map.get(val)
                if codigo:
                    where.append(f'"{col}" = ?')
                    params.append(codigo)
            else:
                where.append(f'"{col}" LIKE ?')
                params.append(f"%{val}%")

        where_sql = "WHERE " + " AND ".join(where) if where else ""

        with get_conn() as conn:
            rows = conn.execute(
                f'SELECT "empresa_codigo","codigo_do_item","ncm","cest" FROM "NCM E CEST" {where_sql}',
                params
            ).fetchall()

        self.tree.delete(*self.tree.get_children())

        for r in rows:
            self.tree.insert("", "end", values=r)

        self.lbl_total.config(text=f"{len(rows)} registros")

    def _exportar(self):
        exportar_treeview(self.tree, "NCM_CEST")