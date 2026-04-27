from database.db import get_conn
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

with get_conn() as conn:
    conn.execute("ALTER TABLE empresa ADD COLUMN razao_social TEXT")
    conn.execute("ALTER TABLE empresa ADD COLUMN cnpj TEXT")

print("✅ colunas adicionadas com sucesso")