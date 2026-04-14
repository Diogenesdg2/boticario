from database.db import get_conn
from .planilha_importer import read_planilha, normalize_columns


def import_planilha(table_name: str, empresa_codigo: str, file_path: str) -> int:
    """
    Substitui dados da empresa na tabela e insere os registros do arquivo.
    Retorna quantidade de linhas inseridas.
    """
    df = read_planilha(table_name, file_path)
    df = normalize_columns(df)

    df.insert(0, "empresa_codigo", empresa_codigo)

    # Aspas duplas para identificadores com espaço (ex: "NCM E CEST")
    table_sql = '"' + table_name.replace('"', '""') + '"'

    with get_conn() as conn:
        conn.execute(
            f'DELETE FROM {table_sql} WHERE "empresa_codigo" = ?',
            (empresa_codigo,)
        )

        if df.empty:
            return 0

        cols = list(df.columns)
        placeholders = ", ".join(["?"] * len(cols))
        cols_sql = ", ".join(['"' + c.replace('"', '""') + '"' for c in cols])

        sql = f"INSERT INTO {table_sql} ({cols_sql}) VALUES ({placeholders})"
        conn.executemany(sql, df.itertuples(index=False, name=None))
        return len(df)