from database.db import get_conn
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill


OPERACAO_ENTRADA = "COMPRAS DE MERCADORIAS SEM FINANCEIRO"


def to_float(valor):
    try:
        if valor is None:
            return 0.0
        if isinstance(valor, str):
            v = valor.strip().replace(".", "").replace(",", ".")
            if v == "":
                return 0.0
            return float(v)
        return float(valor)
    except:
        return 0.0


def norm_codigo(x):
    if x is None:
        return ""
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s.lstrip("0")


def gerar_excel_notas(empresa_codigo, caminho_saida):

    with get_conn() as conn:
        estoque_df = pd.read_sql_query(
            '''
            SELECT produto, saldo_atual
            FROM "Estoque"
            WHERE empresa_codigo = ?
            ''',
            conn,
            params=(empresa_codigo,)
        )

        notas_df = pd.read_sql_query(
            '''
            SELECT *
            FROM "notas"
            WHERE empresa_codigo = ?
              AND operacao = ?
            ''',
            conn,
            params=(empresa_codigo, OPERACAO_ENTRADA)
        )

        ncm_df = pd.read_sql_query(
            '''
            SELECT codigo_do_item, ncm, cest
            FROM "NCM E CEST"
            ''',
            conn
        )

    estoque_df["produto_norm"] = estoque_df["produto"].apply(norm_codigo)
    notas_df["produto_norm"] = notas_df["codigo_do_produto"].apply(norm_codigo)
    ncm_df["produto_norm"] = ncm_df["codigo_do_item"].apply(norm_codigo)

    grupos_notas = dict(tuple(notas_df.groupby("produto_norm")))

    resultado = []

    for _, est in estoque_df.iterrows():
        produto = est["produto"]
        produto_norm = est["produto_norm"]
        saldo = to_float(est["saldo_atual"])

        if saldo <= 0:
            continue

        notas_prod = grupos_notas.get(produto_norm)

        if notas_prod is None or notas_prod.empty:
            continue

        notas_prod = notas_prod.sort_values(
            by=["data_de_entrada", "numero_do_documento"],
            ascending=[False, False]
        )

        acumulado = 0.0

        for _, nota in notas_prod.iterrows():

            if acumulado >= saldo:
                break

            qtd = to_float(
                nota.get("quantidade_de_itens")
                or nota.get("quantidade")
                or nota.get("qtd")
                or 0
            )

            if qtd <= 0:
                continue

            restante = saldo - acumulado
            qtd_utilizada = min(qtd, restante)

            acumulado += qtd_utilizada

            numero_nota = (
                nota.get("numero_do_documento")
                or nota.get("numero")
                or nota.get("num_doc")
                or ""
            )

            unidade = (
                nota.get("unidade_de_medida")
                or nota.get("unidade")
                or nota.get("ucom")
                or ""
            )

            resultado.append({
                "produto": produto,
                "descricao": nota.get("descricao_produto"),
                "emitente": nota.get("nome_do_fornecedor"),
                "numero": numero_nota,
                "serie": nota.get("serie"),
                "subserie": nota.get("subserie"),
                "data_emissao": nota.get("data_de_emissao"),
                "data_entrada": nota.get("data_de_entrada"),
                "chave_acesso": nota.get("chave_nfe"),
                "quantidade_nota": qtd,
                "quantidade_utilizada": qtd_utilizada,
                "acumulado": acumulado,
                "estoque": saldo,
                "cobriu_estoque": acumulado >= saldo,
                "unidade_medida": unidade
            })

    df_final = pd.DataFrame(resultado)

    if df_final.empty:
        df_final.to_excel(caminho_saida, index=False, engine="openpyxl")
        return caminho_saida

    # ✅ AQUI ESTÁ A CORREÇÃO PRINCIPAL
    df_final["unidade_medida"] = df_final.apply(
        lambda x: x["unidade_medida"] if x["cobriu_estoque"] else "",
        axis=1
    )

    df_final["produto_norm"] = df_final["produto"].apply(norm_codigo)

    df_final = df_final.merge(
        ncm_df[["produto_norm", "ncm", "cest"]],
        on="produto_norm",
        how="left"
    )

    df_final["Cod. Mercadoria estoque"] = df_final["produto"]
    df_final["NCM"] = df_final["ncm"]
    df_final["CEST"] = df_final["cest"]

    colunas = [
        "produto",
        "descricao",
        "emitente",
        "numero",
        "serie",
        "subserie",
        "data_emissao",
        "data_entrada",
        "chave_acesso",
        "quantidade_nota",
        "quantidade_utilizada",
        "acumulado",
        "estoque",
        "cobriu_estoque",
        "Cod. Mercadoria estoque",
        "NCM",
        "CEST",
        "unidade_medida"
    ]

    df_final = df_final[[c for c in colunas if c in df_final.columns]]

    df_final = df_final.sort_values(
        by=["produto", "data_entrada"],
        ascending=[True, False]
    )

    df_final.to_excel(caminho_saida, index=False, engine="openpyxl")

    # 🎨 só pintar (não mexe mais nos valores)
    wb = load_workbook(caminho_saida)
    ws = wb.active

    fill_verde = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

    headers = [cell.value for cell in ws[1]]
    idx_flag = headers.index("cobriu_estoque") + 1

    for row in ws.iter_rows(min_row=2):
        if row[idx_flag - 1].value:
            for cell in row:
                cell.fill = fill_verde

    wb.save(caminho_saida)

    return caminho_saida