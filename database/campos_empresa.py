from database.db import get_conn

with get_conn() as conn:
    conn.execute("ALTER TABLE empresa ADD COLUMN razao_social TEXT")
    conn.execute("ALTER TABLE empresa ADD COLUMN cnpj TEXT")

print("✅ colunas adicionadas com sucesso")