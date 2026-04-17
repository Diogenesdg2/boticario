from database.db import get_conn


TABELAS_LIMPAVEIS = [
    "notas",
    "estoque",
    "NCM E CEST"
]


def limpar_dados_empresa(empresa_codigo):
    """
    Remove todos os dados da empresa nas tabelas importadas.
    Retorna um relatório com quantidade de registros removidos por tabela.
    """

    relatorio = {}

    with get_conn() as conn:
        for tabela in TABELAS_LIMPAVEIS:

            tabela_sql = '"' + tabela.replace('"', '""') + '"'

            # ✅ conta antes
            count = conn.execute(
                f'SELECT COUNT(*) FROM {tabela_sql} WHERE empresa_codigo = ?',
                (empresa_codigo,)
            ).fetchone()[0]

            # ✅ deleta
            conn.execute(
                f'DELETE FROM {tabela_sql} WHERE empresa_codigo = ?',
                (empresa_codigo,)
            )

            relatorio[tabela] = count

    return relatorio