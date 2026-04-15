import re
import pandas as pd
from database.db import get_conn


# =========================
# VALIDAÇÃO
# =========================
def validar_ncm(ncm: str) -> bool:
    padrao = r"^\d{4}\.\d{2}\.\d{2}$"
    return bool(re.match(padrao, ncm))


# =========================
# CRIAR TABELA
# =========================
def criar_tabela_ncm(conn):
    conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS NCM (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ncm TEXT NOT NULL UNIQUE,
            descricao TEXT,
            aliquota REAL
        )
        '''
    )

    conn.commit()


# =========================
# INSERIR MANUAL
# =========================
def inserir_ncm(ncm, descricao, aliquota):
    if not validar_ncm(ncm):
        raise ValueError("NCM inválido. Use ####.##.##")

    with get_conn() as conn:
        conn.execute(
            '''
            INSERT OR IGNORE INTO NCM (ncm, descricao, aliquota)
            VALUES (?, ?, ?)
            ''',
            (ncm, descricao, aliquota)
        )
        conn.commit()


# =========================
# LISTAR
# =========================
def listar_ncm():
    with get_conn() as conn:
        cursor = conn.execute(
            '''
            SELECT id, ncm, descricao, aliquota
            FROM NCM
            ORDER BY ncm
            '''
        )
        return cursor.fetchall()


# =========================
# IMPORTAR EXCEL
# =========================
def importar_ncm_excel(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo)

    with get_conn() as conn:
        for _, row in df.iterrows():

            ncm = str(row.get("NCM", "")).strip()
            descricao = row.get("DESCRICAO", "")
            aliquota = row.get("ALIQUOTA", 0)

            if not validar_ncm(ncm):
                print(f"NCM inválido ignorado: {ncm}")
                continue

            conn.execute(
                '''
                INSERT OR IGNORE INTO NCM (ncm, descricao, aliquota)
                VALUES (?, ?, ?)
                ''',
                (ncm, descricao, aliquota)
            )

        conn.commit()