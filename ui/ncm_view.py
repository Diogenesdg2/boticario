import tkinter as tk
from tkinter import ttk, messagebox
from services.ncm import inserir_ncm, listar_ncm


class NCMView(tk.Frame):
    def __init__(self, master):
        super().__init__(master)

        # Campos
        tk.Label(self, text="NCM").grid(row=0, column=0)
        self.entry_ncm = tk.Entry(self)
        self.entry_ncm.grid(row=0, column=1)

        tk.Label(self, text="Descrição").grid(row=1, column=0)
        self.entry_desc = tk.Entry(self)
        self.entry_desc.grid(row=1, column=1)

        tk.Label(self, text="Alíquota").grid(row=2, column=0)
        self.entry_aliq = tk.Entry(self)
        self.entry_aliq.grid(row=2, column=1)

        tk.Button(self, text="Salvar", command=self.salvar).grid(row=3, column=0, columnspan=2)

        # Tabela
        self.tree = ttk.Treeview(self, columns=("ncm", "desc", "aliq"), show="headings")
        self.tree.heading("ncm", text="NCM")
        self.tree.heading("desc", text="Descrição")
        self.tree.heading("aliq", text="Alíquota")
        self.tree.grid(row=4, column=0, columnspan=2)

        self.carregar()

    def salvar(self):
        try:
            inserir_ncm(
                self.entry_ncm.get(),
                self.entry_desc.get(),
                float(self.entry_aliq.get() or 0)
            )
            messagebox.showinfo("Sucesso", "NCM cadastrado!")
            self.carregar()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def carregar(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for row in listar_ncm():
            self.tree.insert("", "end", values=(row[1], row[2], row[3]))