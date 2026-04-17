import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
from services.ncm import inserir_ncm, listar_ncm
from database.db import get_conn


class NCMView(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        self.id_selecionado = None

        self._build()
        self.carregar()

    def _build(self):
        ttk.Label(self, text="Cadastro de NCM", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(10, 15)
        )

        ttk.Label(self, text="NCM:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_ncm = ttk.Entry(self, width=20)
        self.entry_ncm.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        self.entry_ncm.bind("<KeyRelease>", self._on_ncm_digitando)

        ttk.Label(self, text="Descrição:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_desc = ttk.Entry(self, width=40)
        self.entry_desc.grid(row=2, column=1, columnspan=3, sticky="w", padx=5, pady=5)

        ttk.Label(self, text="Alíquota (%):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_aliq = ttk.Entry(self, width=15)
        self.entry_aliq.grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # ── Botões com controle de estado ──
        self.btn_salvar = ttk.Button(self, text="💾 Salvar", command=self.salvar)
        self.btn_salvar.grid(row=1, column=2, padx=5)

        self.btn_editar = ttk.Button(self, text="✏️ Salvar Edição", command=self.editar, state="disabled")
        self.btn_editar.grid(row=1, column=3, padx=5)

        self.btn_excluir = ttk.Button(self, text="🗑️ Excluir", command=self.excluir, state="disabled")
        self.btn_excluir.grid(row=1, column=4, padx=5)

        self.btn_cancelar = ttk.Button(self, text="❌ Cancelar", command=self.limpar, state="disabled")
        self.btn_cancelar.grid(row=2, column=4, padx=5)

        ttk.Button(self, text="📥 Importar Excel", command=self.importar_excel).grid(
            row=3, column=2, columnspan=2, padx=5, pady=5
        )

        self.tree = ttk.Treeview(
            self,
            columns=("id", "ncm", "desc", "aliq"),
            show="headings",
            height=12
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("ncm", text="NCM")
        self.tree.heading("desc", text="Descrição")
        self.tree.heading("aliq", text="Alíquota")

        self.tree.column("id", width=50)
        self.tree.column("ncm", width=120)
        self.tree.column("desc", width=300)
        self.tree.column("aliq", width=100)

        self.tree.grid(row=5, column=0, columnspan=5, sticky="nsew", pady=10)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=5, column=5, sticky="ns")

        self.grid_rowconfigure(5, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    # ── controle de estado dos botões ──
    def _modo_novo(self):
        """Estado padrão: pode salvar novo, não pode editar/excluir"""
        self.btn_salvar.config(state="normal")
        self.btn_editar.config(state="disabled")
        self.btn_excluir.config(state="disabled")
        self.btn_cancelar.config(state="disabled")

    def _modo_edicao(self):
        """Registro selecionado: pode editar/excluir, não pode salvar novo"""
        self.btn_salvar.config(state="disabled")
        self.btn_editar.config(state="normal")
        self.btn_excluir.config(state="normal")
        self.btn_cancelar.config(state="normal")

    # ── digitação + filtro ──
    def _on_ncm_digitando(self, event=None):
        self._formatar_ncm()
        self.filtrar()

    def filtrar(self):
        texto = ''.join(filter(str.isdigit, self.entry_ncm.get()))

        for i in self.tree.get_children():
            self.tree.delete(i)

        for row in listar_ncm():
            ncm = str(row[1])

            if texto and not ncm.startswith(texto):
                continue

            row_formatado = list(row)
            row_formatado[1] = self._formatar_ncm_display(row[1])
            row_formatado[3] = f"{float(row[3]):.2f}%"

            self.tree.insert("", "end", values=row_formatado)

    # ── alíquota ──
    def _parse_aliquota(self, valor):
        try:
            v = str(valor).replace("%", "").replace(",", ".").strip()
            return float(v) if v else 0.0
        except:
            return 0.0

    # ── importação ──
    def importar_excel(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )

        if not caminho:
            return

        try:
            df = pd.read_excel(caminho)

            with get_conn() as conn:
                for _, row in df.iterrows():
                    ncm = ''.join(filter(str.isdigit, str(row.iloc[0])))
                    if len(ncm) != 8:
                        continue

                    aliquota = self._parse_aliquota(row.iloc[1])

                    cur = conn.execute("SELECT id FROM ncm WHERE ncm=?", (ncm,))
                    if cur.fetchone():
                        conn.execute(
                            "UPDATE ncm SET aliquota=? WHERE ncm=?",
                            (aliquota, ncm)
                        )
                    else:
                        conn.execute(
                            "INSERT INTO ncm (ncm, descricao, aliquota) VALUES (?, ?, ?)",
                            (ncm, "", aliquota)
                        )

            messagebox.showinfo("Sucesso", "Importação concluída!")
            self.carregar()

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ── formatação ──
    def _formatar_ncm(self, event=None):
        valor = ''.join(filter(str.isdigit, self.entry_ncm.get()))[:8]

        formatado = valor
        if len(valor) >= 5:
            formatado = valor[:4] + "." + valor[4:6]
        if len(valor) >= 7:
            formatado = valor[:4] + "." + valor[4:6] + "." + valor[6:8]

        self.entry_ncm.delete(0, "end")
        self.entry_ncm.insert(0, formatado)

    def _formatar_ncm_display(self, ncm):
        ncm = ''.join(filter(str.isdigit, str(ncm)))
        if len(ncm) == 8:
            return f"{ncm[:4]}.{ncm[4:6]}.{ncm[6:]}"
        return ncm

    # ── salvar (novo) ──
    def salvar(self):
        try:
            ncm = self.entry_ncm.get().replace(".", "")

            if len(ncm) != 8:
                messagebox.showwarning("Atenção", "NCM deve ter 8 dígitos.")
                return

            inserir_ncm(
                ncm,
                self.entry_desc.get(),
                self._parse_aliquota(self.entry_aliq.get())
            )

            self.limpar()
            self.carregar()

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ── editar (salvar edição) ──
    def editar(self):
        if not self.id_selecionado:
            messagebox.showwarning("Atenção", "Selecione um registro.")
            return

        try:
            ncm = self.entry_ncm.get().replace(".", "")

            with get_conn() as conn:
                cur = conn.execute(
                    "SELECT id FROM ncm WHERE ncm=? AND id<>?",
                    (ncm, self.id_selecionado)
                )
                if cur.fetchone():
                    messagebox.showerror("Erro", "Este NCM já está cadastrado.")
                    return

                conn.execute(
                    "UPDATE ncm SET ncm=?, descricao=?, aliquota=? WHERE id=?",
                    (ncm, self.entry_desc.get(), self._parse_aliquota(self.entry_aliq.get()), self.id_selecionado)
                )

            messagebox.showinfo("Sucesso", "Atualizado!")
            self.limpar()
            self.carregar()

        except Exception as e:
            messagebox.showerror("Erro", str(e))

    # ── excluir ──
    def excluir(self):
        if not self.id_selecionado:
            return

        if not messagebox.askyesno("Confirmação", "Excluir?"):
            return

        with get_conn() as conn:
            conn.execute("DELETE FROM ncm WHERE id=?", (self.id_selecionado,))

        self.limpar()
        self.carregar()

    # ── carregar ──
    def carregar(self):
        self.filtrar()

    # ── seleção na tabela ──
    def on_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        valores = self.tree.item(sel[0], "values")

        self.id_selecionado = valores[0]

        self.entry_ncm.delete(0, "end")
        self.entry_ncm.insert(0, valores[1])

        self.entry_desc.delete(0, "end")
        self.entry_desc.insert(0, valores[2])

        self.entry_aliq.delete(0, "end")
        self.entry_aliq.insert(0, str(valores[3]).replace("%", ""))

        # ✅ ativa modo edição
        self._modo_edicao()

    # ── limpar ──
    def limpar(self):
        self.id_selecionado = None
        self.entry_ncm.delete(0, "end")
        self.entry_desc.delete(0, "end")
        self.entry_aliq.delete(0, "end")

        # ✅ volta pro modo novo
        self._modo_novo()