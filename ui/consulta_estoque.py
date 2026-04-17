import tkinter as tk
from tkinter import ttk, messagebox
from database.db import get_conn
from utils.exportar import exportar_treeview
from config import ESTOQUE_FILTROS


class TelaConsultaEstoque(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._filtros_vars = {}
        self._filtros_widgets = {}
        self._empresas_map = {}
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Consulta: Estoque",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        frm_filtros = ttk.LabelFrame(self, text="Filtros", padding=10)
        frm_filtros.pack(fill="x", pady=(0, 8))

        cols_por_linha = 3

        for i, (col_sql, label) in enumerate(ESTOQUE_FILTROS):
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
                    width=25
                )
                self.cbo_empresa.grid(row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3)
                self.cbo_empresa.bind("<<ComboboxSelected>>", self._on_empresa_change)
            else:
                entry = ttk.Entry(
                    frm_filtros,
                    textvariable=var,
                    width=22,
                    state="disabled"
                )
                entry.grid(row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3)
                self._filtros_widgets[col_sql] = entry

        btn_frame = ttk.Frame(frm_filtros)
        btn_frame.grid(
            row=(len(ESTOQUE_FILTROS) // cols_por_linha) + 1,
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

        self.btn_filtrar = ttk.Button(
            btn_frame,
            text="🔍 Filtrar",
            command=self._consultar,
            state="disabled"
        )
        self.btn_filtrar.pack(side="left", padx=(0, 8))

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

        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, show="headings")

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

    # ─────────────────────────────────────────────

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT codigo, nome FROM empresa ORDER BY codigo"
            ).fetchall()

        self._empresas_map = {f"{c} - {n}": c for c, n in rows}
        valores = list(self._empresas_map.keys())

        self.cbo_empresa["values"] = valores

        if valores:
            self.cbo_empresa.set("")

        self._bloquear_campos()

    def _on_empresa_change(self, event=None):
        empresa = self.cbo_empresa.get().strip()

        if empresa:
            self._liberar_campos()
        else:
            self._bloquear_campos()

    def _bloquear_campos(self):
        for widget in self._filtros_widgets.values():
            widget.config(state="disabled")

        self.btn_filtrar.config(state="disabled")

    def _liberar_campos(self):
        for widget in self._filtros_widgets.values():
            widget.config(state="normal")

        self.btn_filtrar.config(state="normal")

    def _limpar(self):
        for col, var in self._filtros_vars.items():
            if col != "empresa_codigo":
                var.set("")

    def _consultar(self):

        empresa_sel = self._filtros_vars["empresa_codigo"].get().strip()

        if not empresa_sel:
            messagebox.showwarning("Atenção", "Selecione uma empresa.")
            return

        empresa_codigo = self._empresas_map.get(empresa_sel)

        where_parts = ['"empresa_codigo" = ?']
        params = [empresa_codigo]

        for col_sql, var in self._filtros_vars.items():
            if col_sql == "empresa_codigo":
                continue

            val = var.get().strip()

            if not val:
                continue

            where_parts.append(f'"{col_sql}" LIKE ?')
            params.append(f"%{val}%")

        where = "WHERE " + " AND ".join(where_parts)

        with get_conn() as conn:
            cursor = conn.execute(
                f'SELECT * FROM "estoque" {where}',
                params
            )
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = colunas

        for c in colunas:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)

        for r in rows:
            self.tree.insert("", "end", values=r)

        self.lbl_total.config(text=f"{len(rows)} registros")

    def _exportar(self):
        exportar_treeview(self.tree, "Estoque")