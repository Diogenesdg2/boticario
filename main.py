# main.py
from database.db import get_conn
from database.schema import ensure_schema
from ui.app import App

def main():
    conn = get_conn()
    ensure_schema(conn)
    conn.close()

    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()