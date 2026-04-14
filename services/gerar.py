from database.db import get_conn
import pandas as pd


def gerar_excel_notas(empresa_codigo, caminho_saida):
    with get_conn() as conn:
        df = pd.read_sql_query(
            'SELECT * FROM "notas" WHERE empresa_codigo = ?',
            conn,
            params=(empresa_codigo,)
        )

    df.to_excel(caminho_saida, index=False)

    return caminho_saida