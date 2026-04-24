import pandas as pd
from database.db import get_conn
from reportlab.lib.pagesizes import A4, landscape  
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors  
from reportlab.lib.styles import getSampleStyleSheet  
from math import ceil 

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

    estoque_df["produto_norm"] = estoque_df["produto"].apply(norm_codigo)
    notas_df["produto_norm"] = notas_df["codigo_do_produto"].apply(norm_codigo)
    ncm_rel_df["produto_norm"] = ncm_rel_df["codigo_do_item"].apply(norm_codigo)

    ncm_rel_df["ncm_limpo"] = ncm_rel_df["ncm"].apply(limpar_ncm)
    ncm_tab_df["ncm_limpo"] = ncm_tab_df["ncm"].apply(limpar_ncm)

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

            if empresa_sn_flag:
                base_diff = bc_st_total - bc_icms
                valor_prop = (base_diff / qtd) * qtd_utilizada if qtd > 0 else 0
                if aliquota > 0 and valor_prop > 0:
                    credito = valor_prop * (aliquota / 100)
            else:
                bc_prop = (bc_st_total / qtd) * qtd_utilizada if qtd > 0 else 0
                if aliquota > 0 and bc_prop > 0:
                    credito = bc_prop * (aliquota / 100)

            # ✅ OBS ST (igual gerar.py)
            obs_st = ""
            if bc_st_total == 0:
                obs_st = "ITEM SEM BASE ST"
            elif bc_st_total == bc_icms:
                obs_st = ""

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
                "VALOR DO CREDITO": round(credito, 2),
                "OBS ST": obs_st
            })

    df = pd.DataFrame(resultado)

    if df.empty:
        df.to_excel(caminho_saida, index=False, engine="openpyxl")
        return caminho_saida

    colunas_numericas = [
        "QTD NOTA", "QTD UTILIZADA",
        "VALOR UNITARIO", "VALOR TOTAL",
        "ALIQ INTERNA", "VALOR DO CREDITO"
    ]

    for col in colunas_numericas:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df = df.fillna("")
    df = df.sort_values(by=["NCM", "CODIGO", "NF"])

    df.to_excel(caminho_saida, index=False, engine="openpyxl")

    return caminho_saida


def gerar_inventario_pdf(empresa_codigo, caminho_saida):

    with get_conn() as conn:
        empresa = conn.execute(
            "SELECT codigo, razao_social, cnpj FROM empresa WHERE codigo = ?",
            (empresa_codigo,)
        ).fetchone()

    empresa_razao = empresa[1] if empresa else ""
    empresa_cnpj = empresa[2] if empresa else ""

    caminho_temp = caminho_saida.replace(".pdf", "_temp.xlsx")
    gerar_inventario(empresa_codigo, caminho_temp)

    df = pd.read_excel(caminho_temp, engine="openpyxl")

    if df.empty:
        return None

    # ✅ REMOVE ITENS SEM ST DO PDF
    df = df[df["OBS ST"] != "ITEM SEM BASE ST"]

    df["NCM"] = (
        pd.to_numeric(df["NCM"], errors="coerce")
        .fillna(0)
        .astype(int)
        .astype(str)
    )

    df = df.sort_values(by=["NCM", "CODIGO", "NF"])

    styles = getSampleStyleSheet()

    doc = SimpleDocTemplate(
        caminho_saida,
        pagesize=landscape(A4),
        leftMargin=10,
        rightMargin=10,
        topMargin=40,
        bottomMargin=10
    )

    elements = []

    def header(canvas, doc):
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(10, 570, "RELATÓRIO DE INVENTÁRIO")

        canvas.setFont("Helvetica", 8)
        canvas.drawString(10, 555, f"{empresa_razao} | CNPJ: {empresa_cnpj}")

        canvas.drawRightString(820, 570, f"Página {canvas.getPageNumber()}")

    colunas = [c for c in df.columns if c != "OBS ST"]
    df = df[colunas]

    col_widths = [50, 300, 65, 35, 45, 45, 45, 60, 65, 40, 60, 80]

    total_geral = 0
    credito_geral = 0

    resumo_ncm = []

    col_aliq = None
    for c in df.columns:
        if "aliq" in c.lower():
            col_aliq = c
            break

    for ncm, grupo in df.groupby("NCM"):

        elements.append(Paragraph(f"<b>NCM: {ncm}</b>", styles["Normal"]))
        elements.append(Spacer(1, 4))

        data = [colunas]

        total_ncm = 0
        credito_ncm = 0

        aliquota = grupo[col_aliq].dropna().iloc[0] if col_aliq else ""

        for _, row in grupo.iterrows():

            linha = []
            for col in colunas:
                val = row[col]
                if isinstance(val, float):
                    val = f"{val:.2f}"
                linha.append(str(val))

            data.append(linha)

            total_ncm += row["VALOR TOTAL"]
            credito_ncm += row["VALOR DO CREDITO"]

        total_geral += total_ncm
        credito_geral += credito_ncm

        resumo_ncm.append((ncm, aliquota, total_ncm, credito_ncm))

        tabela = Table(data, colWidths=col_widths, repeatRows=1)

        tabela.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 4.2),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        elements.append(tabela)

        elements.append(Paragraph(
            f"<font size=7><b>TOTAL NCM {ncm} | VALOR: {total_ncm:.2f} | CRÉDITO: {credito_ncm:.2f}</b></font>",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 8))

    elements.append(PageBreak())
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>RESUMO GERAL POR NCM</b>", styles["Normal"]))
    elements.append(Spacer(1, 5))

    def to_float_local(valor):
        try:
            return float(valor)
        except:
            return 0.0

    dados = [
        (ncm, aliq, to_float_local(total), to_float_local(credito))
        for ncm, aliq, total, credito in resumo_ncm
    ]

    metade = ceil(len(dados) / 2)

    coluna1 = dados[:metade]
    coluna2 = dados[metade:]

    while len(coluna2) < len(coluna1):
        coluna2.append(("", "", 0.0, 0.0))

    resumo_data = [[
        "NCM", "ALÍQUOTA", "VALOR TOTAL", "CRÉDITO",
        "",
        "NCM", "ALÍQUOTA", "VALOR TOTAL", "CRÉDITO"
    ]]

    for i in range(len(coluna1)):
        ncm1, aliq1, tot1, cred1 = coluna1[i]
        ncm2, aliq2, tot2, cred2 = coluna2[i]

        resumo_data.append([
            ncm1 or "", aliq1 or "", f"{tot1:.2f}", f"{cred1:.2f}",
            "",
            ncm2 or "", aliq2 or "", f"{tot2:.2f}", f"{cred2:.2f}"
        ])

    tabela_resumo = Table(
        resumo_data,
        colWidths=[55, 55, 85, 85, 20, 55, 55, 85, 85]
    )

    tabela_resumo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.black),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.5),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("GRID", (4, 0), (4, -1), 0, colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    elements.append(tabela_resumo)

    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"<font size=8><b>TOTAL GERAL | VALOR: {total_geral:.2f} | CRÉDITO: {credito_geral:.2f}</b></font>",
        styles["Normal"]
    ))

    doc.build(elements, onFirstPage=header, onLaterPages=header)

    return caminho_saida