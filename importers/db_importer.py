from database.db import get_conn
from .planilha_importer import read_planilha, normalize_columns


def import_planilha(table_name: str, empresa_codigo: str, file_path: str) -> int:
    """
    Substitui dados da empresa na tabela e insere os registros do arquivo.
    Retorna quantidade de linhas inseridas.
    """

    df = read_planilha(table_name, file_path)
    df = normalize_columns(df)

    # ✅ garante que não duplica coluna se já existir
    if "empresa_codigo" not in df.columns:
        df.insert(0, "empresa_codigo", empresa_codigo)
    else:
        df["empresa_codigo"] = empresa_codigo

    # ✅ trata nome da tabela com segurança
    table_sql = '"' + table_name.replace('"', '""') + '"'

    with get_conn() as conn:
        # ✅ remove dados antigos da empresa
        conn.execute(
            f'DELETE FROM {table_sql} WHERE "empresa_codigo" = ?',
            (empresa_codigo,)
        )

        if df.empty:
            return 0

        # ✅ remove NaN (ESSENCIAL pro SQLite)
        df = df.where(df.notna(), None)

        cols = list(df.columns)

        placeholders = ", ".join(["?"] * len(cols))
        cols_sql = ", ".join([f'"{c}"' for c in cols])

        sql = f"INSERT INTO {table_sql} ({cols_sql}) VALUES ({placeholders})"

        # ✅ mais seguro que itertuples direto
        data = [tuple(row) for row in df.to_numpy()]

        conn.executemany(sql, data)

        return len(df)