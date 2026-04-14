import re
import unicodedata
import pandas as pd


def _slug(name: str) -> str:
    s = name.strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if re.match(r"^\d", s):
        s = "c_" + s
    return s or "col"


def read_planilha(table_name: str, file_path: str) -> pd.DataFrame:
    """Lê o arquivo de acordo com a planilha esperada."""
    if table_name == "NCM E CEST":
        return pd.read_excel(file_path, sheet_name=0, dtype=str)
    if table_name == "notas":
        return pd.read_excel(file_path, sheet_name=0, dtype=str)
    if table_name == "Estoque":
        return pd.read_csv(file_path, sep=";", encoding="latin-1", dtype=str)

    raise ValueError(f"Tabela/planilha desconhecida: {table_name}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas do DataFrame para nomes compatíveis com SQLite."""
    mapping = {}
    used = set()

    for c in df.columns:
        col_sql = _slug(str(c))

        # Evita conflito com coluna reservada
        if col_sql == "empresa_codigo":
            col_sql = "empresa_codigo_planilha"

        # Garante unicidade
        base = col_sql
        i = 2
        while col_sql in used:
            col_sql = f"{base}_{i}"
            i += 1

        used.add(col_sql)
        mapping[c] = col_sql

    df2 = df.rename(columns=mapping).copy()

    # Substitui NaN por None (NULL no SQLite)
    df2 = df2.where(df2.notna(), other=None)

    return df2