import tkinter as tk
from tkinter import ttk, messagebox
from database.db import get_conn


class TelaEmpresas(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=20)
        self._build()

    def _build(self):
        ttk.Label(self, text="Cadastro de Empresas", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 16)
        )

        ttk.Label(self, text="Código:").grid(row=1, column=0, sticky="w")
        self.ent_codigo = ttk.Entry(self, width=20)
        self.ent_codigo.grid(row=1, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(self, text="Nome:").grid(row=2, column=0, sticky="w")
        self.ent_nome = ttk.Entry(self, width=45)
        self.ent_nome.grid(row=2, column=1, sticky="w", padx=8, pady=4)

        # ✅ Simples
        ttk.Label(self, text="Simples Nacional:").grid(row=3, column=0, sticky="w")
        self.simples_var = tk.StringVar(value="Não")
        ttk.Combobox(self, textvariable=self.simples_var,
                     values=["Sim", "Não"], state="readonly").grid(row=3, column=1, sticky="w", padx=8, pady=4)

        # ✅ Tipo operação
        ttk.Label(self, text="Tipo da operação:").grid(row=4, column=0, sticky="w")
        self.tipo_operacao_var = tk.StringVar(value="Interna")
        ttk.Combobox(self, textvariable=self.tipo_operacao_var,
                     values=["Interna", "Interestadual"], state="readonly").grid(row=4, column=1, sticky="w", padx=8, pady=4)

        # ✅ Redução base
        ttk.Label(self, text="Redução de base:").grid(row=5, column=0, sticky="w")
        self.reducao_base_var = tk.StringVar(value="Não")
        ttk.Combobox(self, textvariable=self.reducao_base_var,
                     values=["Sim", "Não"], state="readonly").grid(row=5, column=1, sticky="w", padx=8, pady=4)

        # Botões
        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=1, column=2, rowspan=5, padx=12, sticky="ns")

        self.btn_salvar = ttk.Button(btn_frame, text="💾 Salvar", command=self._salvar)
        self.btn_salvar.pack(fill="x", pady=4)

        self.btn_editar = ttk.Button(btn_frame, text="✏️ Salvar edição", command=self._editar, state="disabled")
        self.btn_editar.pack(fill="x", pady=4)

        ttk.Button(btn_frame, text="🆕 Novo", command=self._limpar).pack(fill="x", pady=4)

        # Tabela
        self.tree = ttk.Treeview(
            self,
            columns=("codigo", "nome", "simples", "tipo", "reducao"),
            show="headings"
        )

        self.tree.heading("codigo", text="Código")
        self.tree.heading("nome", text="Nome")
        self.tree.heading("simples", text="Simples")
        self.tree.heading("tipo", text="Operação")
        self.tree.heading("reducao", text="Redução")

        self.tree.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._carregar()

    def _carregar(self):
        self.tree.delete(*self.tree.get_children())

        with get_conn() as conn:
            rows = conn.execute("""
                SELECT codigo, nome, simples_nacional, tipo_operacao, reducao_base
                FROM empresa
                ORDER BY codigo
            """).fetchall()

        for r in rows:
            self.tree.insert("", "end", values=r)

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return

        vals = self.tree.item(sel[0], "values")

        self.ent_codigo.delete(0, "end")
        self.ent_codigo.insert(0, vals[0])

        self.ent_nome.delete(0, "end")
        self.ent_nome.insert(0, vals[1])

        self.simples_var.set(vals[2])
        self.tipo_operacao_var.set(vals[3])
        self.reducao_base_var.set(vals[4])

        self.btn_salvar.config(state="disabled")
        self.btn_editar.config(state="normal")

    def _salvar(self):
        codigo = self.ent_codigo.get().strip()
        nome = self.ent_nome.get().strip()

        if not codigo or not nome:
            messagebox.showwarning("Atenção", "Informe código e nome")
            return

        with get_conn() as conn:
            conn.execute("""
                INSERT INTO empresa (codigo, nome, simples_nacional, tipo_operacao, reducao_base)
                VALUES (?, ?, ?, ?, ?)
            """, (
                codigo,
                nome,
                self.simples_var.get(),
                self.tipo_operacao_var.get(),
                self.reducao_base_var.get()
            ))

        self._carregar()
        self._reset_form()

    def _editar(self):
        codigo = self.ent_codigo.get().strip()

        with get_conn() as conn:
            conn.execute("""
                UPDATE empresa
                SET nome = ?, simples_nacional = ?, tipo_operacao = ?, reducao_base = ?
                WHERE codigo = ?
            """, (
                self.ent_nome.get(),
                self.simples_var.get(),
                self.tipo_operacao_var.get(),
                self.reducao_base_var.get(),
                codigo
            ))

        self._carregar()
        self._reset_form()

    def _reset_form(self):
        self.ent_codigo.delete(0, "end")
        self.ent_nome.delete(0, "end")

        self.simples_var.set("Não")
        self.tipo_operacao_var.set("Interna")
        self.reducao_base_var.set("Não")

        self.btn_salvar.config(state="normal")
        self.btn_editar.config(state="disabled")

    def _limpar(self):  
        self.ent_codigo.delete(0, "end")
        self.ent_nome.delete(0, "end")

        self.simples_var.set("Não")
        self.tipo_operacao_var.set("Interna")
        self.reducao_base_var.set("Não")

        self.tree.selection_remove(self.tree.selection())