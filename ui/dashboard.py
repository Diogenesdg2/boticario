import tkinter as tk
from tkinter import ttk
from database.db import get_conn


class Dashboard(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self._empresas_map = {}
        self._build()

    def _build(self):
        ttk.Label(
            self,
            text="Dashboard",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # ── seleção de empresa ─────────────────────
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Empresa:").pack(side="left")

        self.cbo_empresa = ttk.Combobox(
            top,
            state="readonly",
            width=40
        )
        self.cbo_empresa.pack(side="left", padx=8)

        self.cbo_empresa.bind("<<ComboboxSelected>>", self._on_empresa_change)

        ttk.Button(
            top,
            text="🔄 Atualizar",
            command=self._load_empresas
        ).pack(side="left", padx=5)

        # ── área do dashboard ─────────────────────
        self.frame_cards = ttk.Frame(self)
        self.frame_cards.pack(fill="both", expand=True)

        # cards (labels por enquanto)
        self.lbl_total_produtos = ttk.Label(self.frame_cards, text="Produtos: -", font=("Segoe UI", 12))
        self.lbl_total_notas = ttk.Label(self.frame_cards, text="Notas: -", font=("Segoe UI", 12))
        self.lbl_total_estoque = ttk.Label(self.frame_cards, text="Itens em estoque: -", font=("Segoe UI", 12))

        self.lbl_total_produtos.pack(anchor="w", pady=5)
        self.lbl_total_notas.pack(anchor="w", pady=5)
        self.lbl_total_estoque.pack(anchor="w", pady=5)

        self._bloquear_dashboard()
        self._load_empresas()

    # ─────────────────────────────────────────────

    def _load_empresas(self):
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT codigo, nome FROM empresa ORDER BY codigo"
            ).fetchall()

        self._empresas_map = {f"{c} - {n}": c for c, n in rows}

        self.cbo_empresa["values"] = list(self._empresas_map.keys())
        self.cbo_empresa.set("")

        self._bloquear_dashboard()

    def _on_empresa_change(self, event=None):
        empresa = self.cbo_empresa.get().strip()

        if not empresa:
            self._bloquear_dashboard()
            return

        self._carregar_dados()

    def _bloquear_dashboard(self):
        self.lbl_total_produtos.config(text="Produtos: -")
        self.lbl_total_notas.config(text="Notas: -")
        self.lbl_total_estoque.config(text="Itens em estoque: -")

    # ─────────────────────────────────────────────

    def _carregar_dados(self):
        empresa_sel = self.cbo_empresa.get().strip()
        empresa_codigo = self._empresas_map.get(empresa_sel)

        if not empresa_codigo:
            return

        with get_conn() as conn:

            total_produtos = conn.execute(
                'SELECT COUNT(*) FROM "estoque" WHERE "empresa_codigo" = ?',
                (empresa_codigo,)
            ).fetchone()[0]

            total_notas = conn.execute(
                'SELECT COUNT(*) FROM "notas" WHERE "empresa_codigo" = ?',
                (empresa_codigo,)
            ).fetchone()[0]

            total_estoque = conn.execute(
                'SELECT COUNT(*) FROM "estoque" WHERE "empresa_codigo" = ?',
                (empresa_codigo,)
            ).fetchone()[0]

        self.lbl_total_produtos.config(text=f"Produtos: {total_produtos}")
        self.lbl_total_notas.config(text=f"Notas: {total_notas}")
        self.lbl_total_estoque.config(text=f"Itens em estoque: {total_estoque}")