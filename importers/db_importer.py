from database.db import get_conn
from .planilha_importer import read_planilha, normalize_columns


# ✅ mapeamento mais completo (baseado no seu layout real)
MAPEAMENTO_NOTAS = {
    # nota
    "numero nota": "numero_do_documento",
    "nº nota": "numero_do_documento",
    "nota": "numero_do_documento",

    # datas
    "data emissao": "data_de_emissao",
    "data emissão": "data_de_emissao",
    "data entrada": "data_de_entrada",

    # fornecedor
    "codigo fornecedor": "codigo_do_fornecedor",
    "fornecedor": "nome_do_fornecedor",

    # produto
    "codigo produto": "codigo_do_produto",
    "produto": "codigo_do_produto",
    "descricao": "descricao_produto",
    "descrição": "descricao_produto",

    # quantidades
    "quantidade": "quantidade_de_itens",
    "qtd": "quantidade_de_itens",

    # valores
    "valor unitario": "valor_unitario",
    "valor unitário": "valor_unitario",
    "valor total": "valor_total_do_item",

    # impostos
    "base icms": "base_de_calculo_do_icms_do_item",
    "valor icms": "icms_do_item",
    "icms": "icms_do_item",

    # adicionais comuns
    "cfop": "cfop",
    "frete": "frete",
    "seguro": "seguro",
    "desconto": "desconto",
}


def aplicar_mapeamento(df, mapa):
    novas_cols = {}

    for col in df.columns:
        col_norm = col.strip().lower()
        if col_norm in mapa:
            novas_cols[col] = mapa[col_norm]

    return df.rename(columns=novas_cols)


def import_planilha(table_name: str, empresa_codigo: str, file_path: str) -> int:
    """
    Substitui dados da empresa na tabela e insere os registros do arquivo.
    Retorna quantidade de linhas inseridas.
    """

    df = read_planilha(table_name, file_path)
    df = normalize_columns(df)

    # ✅ aplica mapeamento automático para NOTAS
    if table_name.lower() == "notas":
        df = aplicar_mapeamento(df, MAPEAMENTO_NOTAS)

    # ✅ garante empresa_codigo
    if "empresa_codigo" not in df.columns:
        df.insert(0, "empresa_codigo", empresa_codigo)
    else:
        df["empresa_codigo"] = empresa_codigo

    # ✅ nome seguro da tabela
    table_sql = '"' + table_name.replace('"', '""') + '"'

    with get_conn() as conn:
        # ✅ remove dados antigos da empresa
        conn.execute(
            f'DELETE FROM {table_sql} WHERE "empresa_codigo" = ?',
            (empresa_codigo,)
        )

        if df.empty:
            return 0

        # ✅ substitui NaN por None (SQLite precisa disso)
        df = df.where(df.notna(), None)

        cols = list(df.columns)

        placeholders = ", ".join(["?"] * len(cols))
        cols_sql = ", ".join([f'"{c}"' for c in cols])

        sql = f"INSERT INTO {table_sql} ({cols_sql}) VALUES ({placeholders})"

        data = [tuple(row) for row in df.to_numpy()]

        conn.executemany(sql, data)

        return len(df)