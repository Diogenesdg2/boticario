import tkinter as tk
from tkinter import ttk, messagebox
from database.db import get_conn
from utils.exportar import exportar_treeview
from config import NOTAS_FILTROS, NOTAS_COLS



class TelaConsultaNotas(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._filtros_vars  = {}
        self._empresas_map  = {}
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Consulta: Notas Fiscais",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        # ── Filtros ──────────────────────────────────────────────
        frm_filtros = ttk.LabelFrame(self, text="Filtros", padding=10)
        frm_filtros.pack(fill="x", pady=(0, 8))

        cols_por_linha = 3

        for i, (col_sql, label) in enumerate(NOTAS_FILTROS):
            row = i // cols_por_linha
            col = (i % cols_por_linha) * 2

            ttk.Label(frm_filtros, text=f"{label}:").grid(
                row=row, column=col, sticky="w", padx=(10, 2), pady=3
            )

            var = tk.StringVar()
            self._filtros_vars[col_sql] = var

            if col_sql == "empresa_codigo":
                self.cbo_empresa = ttk.Combobox(
                    frm_filtros,
                    textvariable=var,
                    state="readonly",
                    width=20
                )
                self.cbo_empresa.grid(row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3)
            else:
                ttk.Entry(
                    frm_filtros,
                    textvariable=var,
                    width=22
                ).grid(row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3)

        # ── Botões ──────────────────────────────────────────────
        btn_frame = ttk.Frame(frm_filtros)
        btn_frame.grid(
            row=(len(NOTAS_FILTROS) // cols_por_linha) + 1,
            column=0,
            columnspan=6,
            sticky="w",
            pady=(8, 0),
            padx=10
        )

        ttk.Button(
            btn_frame,
            text="🔄 Atualizar empresas",
            command=self._load_empresas
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="🔍 Filtrar",
            command=self._consultar
        ).pack(side="left", padx=(0, 8))

        ttk.Button(
            btn_frame,
            text="🧹 Limpar filtros",
            command=self._limpar
        ).pack(side="left")

        ttk.Button(
            btn_frame,
            text="📤 Exportar Excel",
            command=self._exportar
            ).pack(side="left", padx=(8, 0))

        self.lbl_total = ttk.Label(btn_frame, text="")
        self.lbl_total.pack(side="left", padx=16)

        # ── Tabela ──────────────────────────────────────────────
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        col_ids    = [c[0] for c in NOTAS_COLS]
        col_labels = [c[1] for c in NOTAS_COLS]

        self.tree = ttk.Treeview(frame, columns=col_ids, show="headings")

        for cid, lbl in zip(col_ids, col_labels):
            self.tree.heading(cid, text=lbl, anchor="w")
            self.tree.column(cid, width=120, minwidth=60, stretch=False)

        sb_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)

        self.tree.configure(
            yscrollcommand=sb_y.set,
            xscrollcommand=sb_x.set
        )

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._load_empresas()

    # ─────────────────────────────────────────────────────────────

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT codigo, nome FROM empresa ORDER BY codigo"
            ).fetchall()

        self._empresas_map = {f"{c} - {n}": c for c, n in rows}
        valores = ["(Todas)"] + list(self._empresas_map.keys())

        self.cbo_empresa["values"] = valores
        self.cbo_empresa.current(0)

    def _limpar(self):
        for var in self._filtros_vars.values():
            var.set("")
        self.cbo_empresa.current(0)

    def _consultar(self):
        col_ids  = [c[0] for c in NOTAS_COLS]
        cols_sql = ", ".join([f'"{c}"' for c in col_ids])

        where_parts = []
        params = []

        for col_sql, var in self._filtros_vars.items():
            val = var.get().strip()

            if not val or val == "(Todas)":
                continue

            if col_sql == "empresa_codigo":
                codigo = self._empresas_map.get(val)
                if codigo:
                    where_parts.append(f'"{col_sql}" = ?')
                    params.append(codigo)
            else:
                where_parts.append(f'"{col_sql}" LIKE ?')
                params.append(f"%{val}%")

        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""

        try:
            with get_conn() as conn:
                rows = conn.execute(
                    f'SELECT {cols_sql} FROM "notas" {where}',
                    params
                ).fetchall()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na consulta.\n\n{e}")
            return

        self.tree.delete(*self.tree.get_children())

        for r in rows:
            self.tree.insert("", "end", values=r)

        self.lbl_total.config(text=f"{len(rows)} registros encontrados")

    def _exportar(self):
        exportar_treeview(self.tree, "Notas")