import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).resolve().parent.parent / "app.db"

def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn