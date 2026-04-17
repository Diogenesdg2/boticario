import tkinter as tk
import textwrap
from tkinter import ttk
from database.db import get_conn

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


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

        # ── empresa ─────────────────────────────
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 10))

        ttk.Label(top, text="Empresa:").pack(side="left")

        self.cbo_empresa = ttk.Combobox(top, state="readonly", width=40)
        self.cbo_empresa.pack(side="left", padx=8)

        self.cbo_empresa.bind("<<ComboboxSelected>>", self._on_empresa_change)

        ttk.Button(top, text="🔄 Atualizar", command=self._load_empresas).pack(side="left")

        # ── área dos gráficos ───────────────────
        self.frame = ttk.Frame(self)
        self.frame.pack(fill="both", expand=True)

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

        self._limpar()

    def _on_empresa_change(self, event=None):
        if not self.cbo_empresa.get().strip():
            self._limpar()
            return

        self._carregar()

    def _limpar(self):
        for w in self.frame.winfo_children():
            w.destroy()

    # ─────────────────────────────────────────────

    def _carregar(self):
        self._limpar()

        empresa = self.cbo_empresa.get().strip()
        empresa_codigo = self._empresas_map.get(empresa)

        if not empresa_codigo:
            return

        with get_conn() as conn:

            # ✅ TOP PRODUTOS
            produtos = conn.execute("""
                SELECT produto, SUM(CAST(saldo_atual AS REAL))
                FROM estoque
                WHERE empresa_codigo = ?
                GROUP BY produto
                ORDER BY SUM(CAST(saldo_atual AS REAL)) DESC
                LIMIT 10
            """, (empresa_codigo,)).fetchall()

            # ✅ TOP FORNECEDORES
            fornecedores = conn.execute("""
                SELECT nome_do_fornecedor, COUNT(*)
                FROM notas
                WHERE empresa_codigo = ?
                AND nome_do_fornecedor IS NOT NULL
                AND nome_do_fornecedor <> ''
                GROUP BY nome_do_fornecedor
                ORDER BY COUNT(*) DESC
                LIMIT 10
            """, (empresa_codigo,)).fetchall()

            # ✅ NOTAS POR MÊS (últimos 5 meses)
            notas_mes = conn.execute("""
                SELECT substr(data_de_entrada, 1, 7) AS mes, COUNT(*)
                FROM notas
                WHERE empresa_codigo = ?
                    AND situacao = 'EFETIVADA'
                GROUP BY mes
                ORDER BY mes DESC
                LIMIT 5
            """, (empresa_codigo,)).fetchall()

        # inverter ordem (mais antigo → mais novo)
        notas_mes = list(reversed(notas_mes))

        # ── layout ─────────────────────────────
        linha1 = ttk.Frame(self.frame)
        linha1.pack(fill="both", expand=True)

        linha2 = ttk.Frame(self.frame)
        linha2.pack(fill="both", expand=True)

        # ── gráfico 1: produtos ────────────────
        if produtos:
            nomes = [str(p[0]) for p in produtos]
            valores = [p[1] for p in produtos]

            fig = Figure(figsize=(5, 4))
            ax = fig.add_subplot(111)

            ax.barh(nomes, valores)
            ax.set_title("Top 10 Produtos (Estoque)")
            ax.invert_yaxis()

            canvas = FigureCanvasTkAgg(fig, linha1)
            canvas.draw()
            canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        # ── gráfico 2: fornecedores ───────────
        if fornecedores:
            nomes = [textwrap.fill(str(f[0]), 20) for f in fornecedores]
            valores = [f[1] for f in fornecedores]

            fig = Figure(figsize=(5, 4))
            ax = fig.add_subplot(111)

            ax.barh(nomes, valores)
            ax.set_title("Top Fornecedores")
            ax.invert_yaxis()

            ax.tick_params(axis='y', labelsize=8)

            fig.subplots_adjust(left=0.35)

            canvas = FigureCanvasTkAgg(fig, linha1)
            canvas.draw()
            canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        # ── gráfico 3: notas por mês ──────────
        if notas_mes:
            meses = [m[0] for m in notas_mes]
            valores = [m[1] for m in notas_mes]

            fig = Figure(figsize=(10, 3))
            ax = fig.add_subplot(111)

            ax.plot(meses, valores, marker="o")
            ax.set_title("Notas por mês (últimos 5 meses)")
            ax.grid(True)

            canvas = FigureCanvasTkAgg(fig, linha2)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)