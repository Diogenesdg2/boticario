import pandas as pd
from tkinter import filedialog, messagebox


def exportar_treeview(tree, titulo="dados"):
    """Exporta os dados visíveis de qualquer Treeview para Excel"""

    colunas = tree["columns"]
    dados = []

    for item in tree.get_children():
        dados.append(tree.item(item, "values"))

    if not dados:
        messagebox.showwarning("Atenção", "Nenhum dado para exportar.")
        return

    caminho = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")],
        title=f"Exportar {titulo}",
        initialfile=f"{titulo}.xlsx"
    )

    if not caminho:
        return

    try:
        df = pd.DataFrame(dados, columns=colunas)
        df.to_excel(caminho, index=False, sheet_name=titulo[:31])
        messagebox.showinfo("Sucesso", f"Exportado!\n{caminho}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))