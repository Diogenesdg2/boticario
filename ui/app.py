import tkinter as tk  
from tkinter import ttk, filedialog, messagebox  
from services.gerar import gerar_excel_notas  
from database.db import get_conn  
from importers.db_importer import import_planilha  
from services.ncm import inserir_ncm, listar_ncm
from ui.ncm_view import NCMView
from ui.empresas import TelaEmpresas
from ui.consulta_ncm import TelaConsultaNCM
from ui.consulta_estoque import TelaConsultaEstoque
from ui.consulta_notas import TelaConsultaNotas
from config import PLANILHAS




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

        ttk.Label(self, text="Empresa:").grid(row=1, column=0, sticky="w")
        self.cbo = ttk.Combobox(self, textvariable=self.empresa_var, state="readonly", width=45)
        self.cbo.grid(row=1, column=1, sticky="w", padx=(8, 0))
        ttk.Button(self, text="🔄", command=self._load_empresas, width=3).grid(row=1, column=2, padx=6)

        ttk.Separator(self, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky="ew", pady=14
        )

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

        self.lbl_log = ttk.Label(self, text="", foreground="green")
        self.lbl_log.grid(row=8, column=0, columnspan=3, sticky="w", pady=8)

        self._load_empresas()

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute("SELECT codigo, nome FROM empresa ORDER BY codigo").fetchall()
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
        if not messagebox.askyesno(
            "Confirmação",
            "Isso vai substituir os dados da empresa.\nDeseja continuar?"
        ):
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
            ("🧩  Cadastro NCM",     self._show_cad_ncm),  # ✅ NOVO
            ("📦  Consulta NCM",     self._show_ncm),
            ("🗂️  Consulta Estoque", self._show_estoque),
            ("🧾  Consulta Notas",   self._show_notas),
            ("📤  Gerar Excel",      self._gerar_excel),
        ]

        for label, cmd in menus:
            btn = tk.Button(
                sidebar, text=label, command=cmd,
                bg="#1e3a5f", fg="white", activebackground="#2e5f9f",
                activeforeground="white", relief="flat", anchor="w",
                padx=18, pady=10, font=("Segoe UI", 10), cursor="hand2"
            )
            btn.pack(fill="x")

        self.content = tk.Frame(self, bg="#f4f6f8")
        self.content.pack(side="left", fill="both", expand=True)

        self._telas = {
            "cadastro":   TelaEmpresas(self.content),
            "importacao": TelaImportacao(self.content),
            "cad_ncm":    NCMView(self.content),
            "ncm":        TelaConsultaNCM(self.content),
            "estoque":    TelaConsultaEstoque(self.content),
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
    def _show_cad_ncm(self):    self._show("cad_ncm")  # ✅ NOVO

    def _gerar_excel(self):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT codigo, nome FROM empresa ORDER BY codigo"
            ).fetchall()

        if not rows:
            messagebox.showwarning("Atenção", "Nenhuma empresa cadastrada.")
            return

        opcoes = [f"{c} - {n}" for c, n in rows]

        win = tk.Toplevel(self)
        win.title("Selecionar Empresa")
        win.geometry("350x120")

        ttk.Label(win, text="Escolha a empresa:").pack(pady=10)

        empresa_var = tk.StringVar()
        cbo = ttk.Combobox(win, textvariable=empresa_var, values=opcoes, state="readonly", width=40)
        cbo.pack()
        cbo.current(0)

        def confirmar():
            selecao = empresa_var.get()
            if not selecao:
                return

            codigo = selecao.split(" - ")[0]

            caminho = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                title="Salvar arquivo"
            )

            if not caminho:
                return

            try:
                gerar_excel_notas(codigo, caminho)
                messagebox.showinfo("Sucesso", f"Arquivo gerado:\n{caminho}")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Erro", str(e))

        ttk.Button(win, text="Gerar", command=confirmar).pack(pady=10)