import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "app.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS log_importacao (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa    TEXT    NOT NULL,
            tabela     TEXT    NOT NULL,
            linhas     INTEGER NOT NULL,
            arquivo    TEXT    NOT NULL,
            data_hora  TEXT    NOT NULL
        )
    """)
    return conn

