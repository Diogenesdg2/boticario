import pandas as pd
from database.db import get_conn

from services.gerar import (
    to_float,
    norm_codigo,
    limpar_ncm,
    buscar_aliquota_float
)

OPERACAO_ENTRADA = "COMPRAS DE MERCADORIAS SEM FINANCEIRO"


def gerar_inventario(empresa_codigo, caminho_saida):

    with get_conn() as conn:

        empresa_sn = conn.execute(
            "SELECT simples_nacional FROM empresa WHERE codigo = ?",
            (empresa_codigo,)
        ).fetchone()

        empresa_sn = empresa_sn[0] if empresa_sn else "N"
        empresa_sn_flag = str(empresa_sn).strip().upper() in ["S", "SIM"]

        estoque_df = pd.read_sql_query(
            '''
            SELECT produto, descricao, saldo_atual
            FROM estoque
            WHERE empresa_codigo = ?
            AND saldo_atual > 0
            ''',
            conn,
            params=(empresa_codigo,)
        )

        notas_df = pd.read_sql_query(
            '''
            SELECT *
            FROM notas
            WHERE empresa_codigo = ?
              AND operacao = ?
            ''',
            conn,
            params=(empresa_codigo, OPERACAO_ENTRADA)
        )

        ncm_rel_df = pd.read_sql_query(
            '''
            SELECT codigo_do_item, ncm
            FROM "NCM E CEST"
            WHERE empresa_codigo = ?
            ''',
            conn,
            params=(empresa_codigo,)
        )

        ncm_tab_df = pd.read_sql_query(
            '''
            SELECT ncm, aliquota
            FROM ncm
            ''',
            conn
        )

    # ✅ normalizações
    estoque_df["produto_norm"] = estoque_df["produto"].apply(norm_codigo)
    notas_df["produto_norm"] = notas_df["codigo_do_produto"].apply(norm_codigo)
    ncm_rel_df["produto_norm"] = ncm_rel_df["codigo_do_item"].apply(norm_codigo)

    ncm_rel_df["ncm_limpo"] = ncm_rel_df["ncm"].apply(limpar_ncm)
    ncm_tab_df["ncm_limpo"] = ncm_tab_df["ncm"].apply(limpar_ncm)

    # ✅ ordenar posição
    if "posicao_na_nf" in notas_df.columns:
        notas_df["posicao_na_nf"] = pd.to_numeric(
            notas_df["posicao_na_nf"], errors="coerce"
        ).fillna(0).astype(int)
    else:
        notas_df["posicao_na_nf"] = 0

    grupos_notas = dict(tuple(notas_df.groupby("produto_norm")))

    resultado = []

    for _, est in estoque_df.iterrows():

        produto = est["produto"]
        descricao_estoque = est.get("descricao", "")
        produto_norm = est["produto_norm"]
        saldo = to_float(est["saldo_atual"])

        notas_prod = grupos_notas.get(produto_norm)

        if notas_prod is None or notas_prod.empty:
            continue

        # ✅ MESMA ORDEM DO GERAR.PY
        notas_prod = notas_prod.sort_values(
            by=["data_de_entrada", "numero_do_documento", "posicao_na_nf"],
            ascending=[False, False, True]
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

            valor_unit = to_float(nota.get("valor_unitario"))
            valor_total = valor_unit * qtd_utilizada

            unidade = (
                nota.get("unidade_de_medida")
                or nota.get("unidade")
                or ""
            )

            numero_nota = nota.get("numero_do_documento")

            bc_st_total = to_float(nota.get("base_de_calculo_do_icms_st_do_item"))
            bc_icms = to_float(nota.get("base_de_calculo_do_icms_do_item"))

            ncm_item = ncm_rel_df[ncm_rel_df["produto_norm"] == produto_norm]
            ncm_codigo = ncm_item.iloc[0]["ncm_limpo"] if not ncm_item.empty else ""

            aliquota = buscar_aliquota_float(ncm_codigo, ncm_tab_df)

            credito = 0.0

            # ✅ SIMPLES (igual gerar.py)
            if empresa_sn_flag:

                base_diff = bc_st_total - bc_icms

                valor_prop = (base_diff / qtd) * qtd_utilizada if qtd > 0 else 0

                if aliquota > 0 and valor_prop > 0:
                    credito = valor_prop * (aliquota / 100)

            # ✅ NORMAL (igual gerar.py)
            else:

                bc_prop = (bc_st_total / qtd) * qtd_utilizada if qtd > 0 else 0

                if aliquota > 0 and bc_prop > 0:
                    credito = bc_prop * (aliquota / 100)

            resultado.append({
                "CODIGO": produto,
                "DESCRICAO": nota.get("descricao_produto") or descricao_estoque,
                "NCM": ncm_codigo,
                "UNIDADE": unidade,
                "NF": numero_nota,

                "QTD NOTA": qtd,
                "QTD UTILIZADA": qtd_utilizada,

                "VALOR UNITARIO": round(valor_unit, 2),
                "VALOR TOTAL": round(valor_total, 2),

                "ALIQ INTERNA": aliquota,
                "VALOR DO CREDITO": round(credito, 2)
            })

    df = pd.DataFrame(resultado)

    if df.empty:
        df.to_excel(caminho_saida, index=False, engine="openpyxl")
        return caminho_saida

    # ✅ TIPAGEM (resolve erro do Excel)
    colunas_numericas = [
        "QTD NOTA", "QTD UTILIZADA",
        "VALOR UNITARIO", "VALOR TOTAL",
        "ALIQ INTERNA", "VALOR DO CREDITO"
    ]

    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.fillna("")

    # ✅ ORDENAÇÃO FINAL
    df = df.sort_values(by=["NCM", "CODIGO", "NF"])

    df.to_excel(caminho_saida, index=False, engine="openpyxl")

    return caminho_saida