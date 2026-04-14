# database/schema.py
import re
import unicodedata


def normalize_col_name(name: str) -> str:
    """
    Converte nomes de colunas vindos da planilha em nomes seguros para SQL.
    Ex:
      'Código do Item' -> 'codigo_do_item'
      'Saldo Atual' -> 'saldo_atual'
    """
    if name is None:
        return "coluna"

    s = str(name).strip()

    # Remove acentos
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    # Lower + troca separadores por underscore
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")

    if not s:
        s = "coluna"

    # Não deixar começar com número
    if s[0].isdigit():
        s = f"c_{s}"

    return s


def quote_ident(ident: str) -> str:
    """
    Coloca aspas duplas em identificadores SQL, escapando aspas internas.
    """
    ident = str(ident)
    return '"' + ident.replace('"', '""') + '"'


def ensure_schema(conn):
    """
    Cria as tabelas necessárias caso não existam.
    As tabelas de planilha seguem o nome definido pelo projeto:
      - "NCM E CEST"
      - "Estoque"
      - "notas"
    """
    cur = conn.cursor()

    # Empresa
    cur.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            codigo TEXT PRIMARY KEY,
            nome   TEXT NOT NULL
        )
    """)

    # Definição das tabelas e colunas (baseado nas planilhas)
    table_specs = {
        "NCM E CEST": [
            "Código do Item",
            "NCM",
            "CEST",
        ],
        "Estoque": [
            "Quebra",
            "Produto",
            "Descrição",
            "Unidade",
            "Saldo inicial",
            "Entradas",
            "Saidas",
            "Saldo Atual",
            "Custo",
        ],
        "notas": [
            "Código da Loja",
            "Código do Fornecedor",
            "Nome do Fornecedor",
            "Número do Documento",
            "codigo da operacao",
            "Operação",
            "Situação",
            "Data De Emissão",
            "Data de entrada",
            "Frete",
            "Outros",
            "Seguro",
            "Desconto",
            "IPI",
            "DAE",
            "ICMS Desonerado",
            "FECOP",
            "Valor FECOPST",
            "FECOP Retido",
            "Base de Cálculo ICMS",
            "Valor BC do ICMS",
            "Base de Cálculo ICMSST",
            "Valor BC ICMSST",
            "Valor Total",
            "Código do produto",
            "Descrição Produto",
            "Unidade de medida",
            "Quantidade de itens na unidade",
            "Quantidade de itens",
            "CFOP",
            "Frete do item",
            "Seguro do item",
            "Desconto do item",
            "IPI do item",
            "Base de cálculo do ICMS do item",
            "ICMS do item",
            "Base de calculo do ICMS ST do item",
            "ICMS ST do item",
            "DAE Item",
            "ICMS desonerado do item",
            "ICMS antecipado do item",
            "FECOP do item",
            "FECOP ST do item",
            "FECOP retido do item",
            "Valor unitário",
            "Outras despesas do item",
            "Valor total do item",
            "Posição na NF",
            "Chave Nfe",
        ],
    }

    for table_name, columns in table_specs.items():
        # Coluna de vínculo com a empresa + id interno opcional
        col_defs = [
            f'{quote_ident("id")} INTEGER PRIMARY KEY AUTOINCREMENT',
            f'{quote_ident("empresa_codigo")} TEXT NOT NULL',
        ]

        # Aqui está a parte que estava quebrando: SEM \" e com aspas corretas
        for col in columns:
            col_sql = normalize_col_name(col)
            col_defs.append(f'{quote_ident(col_sql)} TEXT')

        sql = f"CREATE TABLE IF NOT EXISTS {quote_ident(table_name)} ({', '.join(col_defs)})"
        cur.execute(sql)

        # Índice para acelerar DELETE/SELECT por empresa
        idx_name = f"idx_{normalize_col_name(table_name)}_empresa"
        cur.execute(
            f"CREATE INDEX IF NOT EXISTS {quote_ident(idx_name)} "
            f"ON {quote_ident(table_name)} ({quote_ident('empresa_codigo')})"
        )

    conn.commit()