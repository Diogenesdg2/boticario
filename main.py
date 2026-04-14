# main.py
from database.db import get_conn
from database.schema import ensure_schema
from database.db import get_conn
from ui.app import App


def main():
    # ✅ Garante que o schema (incluindo migração) rode SEMPRE ao iniciar
    with get_conn() as conn:
        ensure_schema(conn)

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()