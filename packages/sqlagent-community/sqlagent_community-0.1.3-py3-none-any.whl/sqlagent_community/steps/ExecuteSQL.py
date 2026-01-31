import sqlite3
from typing import Tuple, Any


class SQLiteExecutor:
    """Executa comandos SQL em um banco SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute(self, sql: str) -> Tuple[Any, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            try:
                cur.execute(sql)

                if sql.strip().lower().startswith("select"):
                    columns = [desc[0] for desc in cur.description]
                    results = cur.fetchall()
                    return columns, results

                conn.commit()
                return None, f"{cur.rowcount} linhas afetadas"

            except Exception as e:
                return None, f"Erro: {e}"
