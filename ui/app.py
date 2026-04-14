import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from database.db import get_conn
from importers.db_importer import import_planilha

PLANILHAS = ["NCM E CEST", "Estoque", "notas"]

# Colunas originais das notas (para exibir cabeçalho legível)
NOTAS_COLS = [
    ("empresa_codigo",              "Empresa"),
    ("codigo_da_loja",              "Cód. Loja"),
    ("codigo_do_fornecedor",        "Cód. Fornecedor"),
    ("nome_do_fornecedor",          "Nome Fornecedor"),
    ("numero_do_documento",         "Nº Documento"),
    ("codigo_da_operacao",          "Cód. Operação"),
    ("operacao",                    "Operação"),
    ("situacao",                    "Situação"),
    ("data_de_emissao",             "Data Emissão"),
    ("data_de_entrada",             "Data Entrada"),
    ("frete",                       "Frete"),
    ("outros",                      "Outros"),
    ("seguro",                      "Seguro"),
    ("desconto",                    "Desconto"),
    ("ipi",                         "IPI"),
    ("dae",                         "DAE"),
    ("icms_desonerado",             "ICMS Desonerado"),
    ("fecop",                       "FECOP"),
    ("valor_fecopst",               "Valor FECOPST"),
    ("fecop_retido",                "FECOP Retido"),
    ("base_de_calculo_icms",        "BC ICMS"),
    ("valor_bc_do_icms",            "Valor BC ICMS"),
    ("base_de_calculo_icmsst",      "BC ICMSST"),
    ("valor_bc_icmsst",             "Valor BC ICMSST"),
    ("valor_total",                 "Valor Total"),
    ("codigo_do_produto",           "Cód. Produto"),
    ("descricao_produto",           "Descrição Produto"),
    ("unidade_de_medida",           "Unidade"),
    ("quantidade_de_itens_na_unidade", "Qtd Un."),
    ("quantidade_de_itens",         "Qtd Itens"),
    ("cfop",                        "CFOP"),
    ("frete_do_item",               "Frete Item"),
    ("seguro_do_item",              "Seguro Item"),
    ("desconto_do_item",            "Desconto Item"),
    ("ipi_do_item",                 "IPI Item"),
    ("base_de_calculo_do_icms_do_item", "BC ICMS Item"),
    ("icms_do_item",                "ICMS Item"),
    ("base_de_calculo_do_icms_st_do_item", "BC ICMSST Item"),
    ("icms_st_do_item",             "ICMSST Item"),
    ("dae_item",                    "DAE Item"),
    ("icms_desonerado_do_item",     "ICMS Desonerado Item"),
    ("icms_antecipado_do_item",     "ICMS Antecipado Item"),
    ("fecop_do_item",               "FECOP Item"),
    ("fecop_st_do_item",            "FECOP ST Item"),
    ("fecop_retido_do_item",        "FECOP Retido Item"),
    ("valor_unitario",              "Valor Unitário"),
    ("outras_despesas_do_item",     "Outras Despesas"),
    ("valor_total_do_item",         "Valor Total Item"),
    ("posicao_na_nf",               "Posição NF"),
    ("chave_nfe",                   "Chave NFe"),
]

# Filtros disponíveis na consulta de notas
NOTAS_FILTROS = [
    ("empresa_codigo",       "Empresa"),
    ("codigo_da_loja",       "Cód. Loja"),
    ("nome_do_fornecedor",   "Nome Fornecedor"),
    ("numero_do_documento",  "Nº Documento"),
    ("operacao",             "Operação"),
    ("situacao",             "Situação"),
    ("data_de_emissao",      "Data Emissão"),
    ("data_de_entrada",      "Data Entrada"),
    ("cfop",                 "CFOP"),
    ("codigo_do_produto",    "Cód. Produto"),
    ("descricao_produto",    "Descrição Produto"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Tela: Cadastro de Empresa
# ─────────────────────────────────────────────────────────────────────────────
class TelaCadastro(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        self._build()

    def _build(self):
        ttk.Label(self, text="Cadastro de Empresas", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 16)
        )

        ttk.Label(self, text="Código:").grid(row=1, column=0, sticky="w")
        self.ent_codigo = ttk.Entry(self, width=20)
        self.ent_codigo.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=4)

        ttk.Label(self, text="Nome:").grid(row=2, column=0, sticky="w")
        self.ent_nome = ttk.Entry(self, width=45)
        self.ent_nome.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=4)

        ttk.Button(self, text="💾  Salvar empresa", command=self._salvar).grid(
            row=3, column=1, sticky="w", padx=(8, 0), pady=12
        )

        ttk.Separator(self, orient="horizontal").grid(
            row=4, column=0, columnspan=3, sticky="ew", pady=10
        )

        ttk.Label(self, text="Empresas cadastradas:", font=("Segoe UI", 10, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w"
        )

        # Tabela de empresas
        frame_tree = ttk.Frame(self)
        frame_tree.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=8)
        self.grid_rowconfigure(6, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.tree = ttk.Treeview(frame_tree, columns=("codigo", "nome"), show="headings", height=12)
        self.tree.heading("codigo", text="Código")
        self.tree.heading("nome", text="Nome")
        self.tree.column("codigo", width=120)
        self.tree.column("nome", width=400)

        sb = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self._carregar()

    def _carregar(self):
        self.tree.delete(*self.tree.get_children())
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()
        for r in rows:
            self.tree.insert("", "end", values=(r[0], r[1]))

    def _salvar(self):
        codigo = self.ent_codigo.get().strip()
        nome = self.ent_nome.get().strip()
        if not codigo or not nome:
            messagebox.showwarning("Atenção", "Informe código e nome.")
            return
        try:
            with get_conn() as conn:
                conn.execute("INSERT INTO empresa(codigo, nome) VALUES(?,?)", (codigo, nome))
            self.ent_codigo.delete(0, "end")
            self.ent_nome.delete(0, "end")
            self._carregar()
            messagebox.showinfo("OK", "Empresa cadastrada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível cadastrar.\n\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# Tela: Importação
# ─────────────────────────────────────────────────────────────────────────────
class TelaImportacao(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        self.empresa_var = tk.StringVar()
        self.paths = {p: tk.StringVar() for p in PLANILHAS}
        self._build()

    def _build(self):
        ttk.Label(self, text="Importação de Planilhas", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 16)
        )

        # Seleção de empresa
        ttk.Label(self, text="Empresa:").grid(row=1, column=0, sticky="w")
        self.cbo = ttk.Combobox(self, textvariable=self.empresa_var, state="readonly", width=45)
        self.cbo.grid(row=1, column=1, sticky="w", padx=(8, 0))
        ttk.Button(self, text="🔄", command=self._load_empresas, width=3).grid(row=1, column=2, padx=6)

        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=14
        )

        # Seleção de arquivos
        for i, plan in enumerate(PLANILHAS):
            r = 3 + i
            ttk.Label(self, text=f"{plan}:").grid(row=r, column=0, sticky="w", pady=5)
            ttk.Entry(self, textvariable=self.paths[plan], width=50, state="readonly").grid(
                row=r, column=1, sticky="w", padx=(8, 0)
            )
            ttk.Button(self, text="📂 Buscar", command=lambda p=plan: self._pick(p)).grid(
                row=r, column=2, padx=8
            )

        ttk.Separator(self, orient="horizontal").grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=14
        )

        ttk.Button(
            self, text="⬆️  Importar (substitui dados da empresa)",
            command=self._importar
        ).grid(row=7, column=0, columnspan=3, sticky="ew", ipady=6)

        # Log
        self.lbl_log = ttk.Label(self, text="", foreground="green")
        self.lbl_log.grid(row=8, column=0, columnspan=3, sticky="w", pady=8)

        self._load_empresas()

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()
        self._empresas = rows
        self.cbo["values"] = [f"{c} - {n}" for c, n in rows]
        if self.cbo["values"] and not self.empresa_var.get():
            self.cbo.current(0)

    def _get_codigo(self):
        s = self.empresa_var.get().strip()
        return s.split(" - ", 1)[0].strip() if s else ""

    def _pick(self, planilha):
        ftypes = (
            [("Excel", "*.xlsx"), ("Todos", "*.*")]
            if planilha in ("NCM E CEST", "notas")
            else [("CSV", "*.csv"), ("Todos", "*.*")]
        )
        path = filedialog.askopenfilename(title=f"Selecione: {planilha}", filetypes=ftypes)
        if path:
            self.paths[planilha].set(path)

    def _importar(self):
        codigo = self._get_codigo()
        if not codigo:
            messagebox.showwarning("Atenção", "Selecione uma empresa.")
            return
        missing = [p for p in PLANILHAS if not self.paths[p].get().strip()]
        if missing:
            messagebox.showwarning("Atenção", "Selecione os arquivos:\n" + "\n".join(missing))
            return
        try:
            detalhes = []
            for p in PLANILHAS:
                n = import_planilha(p, codigo, self.paths[p].get().strip())
                detalhes.append(f"  ✔ {p}: {n} linhas")
            self.lbl_log.config(text="\n".join(detalhes))
            messagebox.showinfo("Concluído", "Importação realizada!\n\n" + "\n".join(detalhes))
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na importação.\n\n{e}")


# ─────────────────────────────────────────────────────────────────────────────
# Tela: Consulta genérica (NCM e Estoque)
# ─────────────────────────────────────────────────────────────────────────────
class TelaConsultaSimples(ttk.Frame):
    def __init__(self, master, table_name: str, cols: list[tuple]):
        """
        cols: lista de (col_sql, label)
        """
        super().__init__(master, padding=10)
        self.table_name = table_name
        self.cols = cols
        self._build()

    def _build(self):
        ttk.Label(self, text=f"Consulta: {self.table_name}", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 10)
        )

        top = ttk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="Empresa:").pack(side="left")
        self.empresa_var = tk.StringVar()
        self.cbo = ttk.Combobox(top, textvariable=self.empresa_var, state="readonly", width=35)
        self.cbo.pack(side="left", padx=6)
        ttk.Button(top, text="🔄", command=self._load_empresas, width=3).pack(side="left")
        ttk.Button(top, text="🔍 Consultar", command=self._consultar).pack(side="left", padx=10)
        self.lbl_total = ttk.Label(top, text="")
        self.lbl_total.pack(side="left", padx=10)

        # Treeview
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, pady=8)

        col_ids = [c[0] for c in self.cols]
        col_labels = [c[1] for c in self.cols]

        self.tree = ttk.Treeview(frame, columns=col_ids, show="headings")
        for cid, lbl in zip(col_ids, col_labels):
            self.tree.heading(cid, text=lbl)
            self.tree.column(cid, width=110, minwidth=60)

        sb_y = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right", fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        self._load_empresas()

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()
        self.cbo["values"] = [f"{c} - {n}" for c, n in rows]
        if self.cbo["values"]:
            self.cbo.current(0)

    def _consultar(self):
        empresa = self.empresa_var.get().strip()
        if not empresa:
            messagebox.showwarning("Atenção", "Selecione uma empresa.")
            return
        codigo = empresa.split(" - ", 1)[0].strip()
        col_ids = [c[0] for c in self.cols]
        cols_sql = ", ".join([f'"{c}"' for c in col_ids])
        tbl = '"' + self.table_name.replace('"', '""') + '"'

        with get_conn() as conn:
            rows = conn.execute(
                f'SELECT {cols_sql} FROM {tbl} WHERE "empresa_codigo" = ?', (codigo,)
            ).fetchall()

        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)
        self.lbl_total.config(text=f"{len(rows)} registros")


# ─────────────────────────────────────────────────────────────────────────────
# Tela: Consulta de Notas (com filtros)
# ─────────────────────────────────────────────────────────────────────────────
class TelaConsultaNotas(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._filtros_vars = {}
        self._build()

    def _build(self):
        ttk.Label(self, text="Consulta: Notas Fiscais", font=("Segoe UI", 14, "bold")).pack(
            anchor="w", pady=(0, 8)
        )

        # ── Painel de filtros ──────────────────────────────────────────────
        frm_filtros = ttk.LabelFrame(self, text="Filtros", padding=10)
        frm_filtros.pack(fill="x", pady=(0, 8))

        cols_por_linha = 3

        for i, (col_sql, label) in enumerate(NOTAS_FILTROS):
            row = i // cols_por_linha
            col = (i % cols_por_linha) * 2

            ttk.Label(frm_filtros, text=f"{label}:").grid(
                row=row, column=col, sticky="w", padx=(10, 2), pady=3
            )

            # Campo Empresa vira Combobox, os demais permanecem Entry
            if col_sql == "empresa_codigo":
                var = tk.StringVar()
                self._filtros_vars[col_sql] = var
                self.cbo_empresa = ttk.Combobox(
                    frm_filtros, textvariable=var, state="readonly", width=20
                )
                self.cbo_empresa.grid(row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3)
            else:
                var = tk.StringVar()
                self._filtros_vars[col_sql] = var
                ttk.Entry(frm_filtros, textvariable=var, width=22).grid(
                    row=row, column=col + 1, sticky="w", padx=(0, 14), pady=3
                )

        # Botões
        btn_frame = ttk.Frame(frm_filtros)
        btn_frame.grid(
            row=(len(NOTAS_FILTROS) // cols_por_linha) + 1,
            column=0, columnspan=6, sticky="w", pady=(8, 0), padx=10
        )
        ttk.Button(btn_frame, text="🔄 Atualizar empresas", command=self._load_empresas).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="🔍 Filtrar", command=self._consultar).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="🧹 Limpar filtros", command=self._limpar).pack(side="left")
        self.lbl_total = ttk.Label(btn_frame, text="")
        self.lbl_total.pack(side="left", padx=16)

        # ── Treeview ──────────────────────────────────────────────────────
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)

        col_ids    = [c[0] for c in NOTAS_COLS]
        col_labels = [c[1] for c in NOTAS_COLS]

        self.tree = ttk.Treeview(frame, columns=col_ids, show="headings")
        for cid, lbl in zip(col_ids, col_labels):
            self.tree.heading(cid, text=lbl, anchor="w")
            self.tree.column(cid, width=120, minwidth=60, stretch=False)

        sb_y = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        sb_x = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        sb_y.pack(side="right",  fill="y")
        sb_x.pack(side="bottom", fill="x")
        self.tree.pack(fill="both", expand=True)

        # Carrega empresas ao iniciar
        self._load_empresas()

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()
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
                # Pega o código real do mapa (ex: "001 - Nome" → "001")
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
                    f'SELECT {cols_sql} FROM "notas" {where}', params
                ).fetchall()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha na consulta.\n\n{e}")
            return

        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", values=r)
        self.lbl_total.config(text=f"{len(rows)} registros encontrados")


# ─────────────────────────────────────────────────────────────────────────────
# App principal com menu lateral
# ─────────────────────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Boticário — Gestão de Planilhas")
        self.geometry("1200x680")
        self.resizable(True, True)
        self._build()

    def _build(self):
        # ── Menu lateral ──────────────────────────────────────────────────
        sidebar = tk.Frame(self, bg="#1e3a5f", width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar, text="📊 Boticário", bg="#1e3a5f", fg="white",
            font=("Segoe UI", 13, "bold"), pady=20
        ).pack(fill="x")

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", padx=10)

        menus = [
            ("🏢  Cadastro",         self._show_cadastro),
            ("⬆️  Importação",       self._show_importacao),
            ("📦  Consulta NCM",     self._show_ncm),
            ("🗂️  Consulta Estoque", self._show_estoque),
            ("🧾  Consulta Notas",   self._show_notas),
        ]

        for label, cmd in menus:
            btn = tk.Button(
                sidebar, text=label, command=cmd,
                bg="#1e3a5f", fg="white", activebackground="#2e5f9f",
                activeforeground="white", relief="flat", anchor="w",
                padx=18, pady=10, font=("Segoe UI", 10), cursor="hand2"
            )
            btn.pack(fill="x")

        # ── Área de conteúdo ──────────────────────────────────────────────
        self.content = tk.Frame(self, bg="#f4f6f8")
        self.content.pack(side="left", fill="both", expand=True)

        # Instancia as telas
        self._telas = {
            "cadastro":   TelaCadastro(self.content),
            "importacao": TelaImportacao(self.content),
            "ncm":        TelaConsultaSimples(self.content, "NCM E CEST", [
                ("codigo_do_item", "Cód. Item"),
                ("ncm",            "NCM"),
                ("cest",           "CEST"),
            ]),
            "estoque":    TelaConsultaSimples(self.content, "Estoque", [
                ("quebra",         "Quebra"),
                ("produto",        "Produto"),
                ("descricao",      "Descrição"),
                ("unidade",        "Unidade"),
                ("saldo_inicial",  "Saldo Inicial"),
                ("entradas",       "Entradas"),
                ("saidas",         "Saídas"),
                ("saldo_atual",    "Saldo Atual"),
                ("custo",          "Custo"),
            ]),
            "notas":      TelaConsultaNotas(self.content),
        }

        self._show_cadastro()

    def _show(self, key: str):
        for tela in self._telas.values():
            tela.pack_forget()
        self._telas[key].pack(fill="both", expand=True)

    def _show_cadastro(self):   self._show("cadastro")
    def _show_importacao(self): self._show("importacao")
    def _show_ncm(self):        self._show("ncm")
    def _show_estoque(self):    self._show("estoque")
    def _show_notas(self):      self._show("notas")