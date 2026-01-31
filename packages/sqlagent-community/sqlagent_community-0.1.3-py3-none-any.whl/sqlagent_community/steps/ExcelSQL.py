import sqlite3
import pandas as pd
from sqlagent_community.utils.CleanData import DataFrameCleaner


class ExcelToSQLiteImporter:
    """Importa todas as abas de um Excel para um banco SQLite, com limpeza e normalização."""

    def __init__(self, excel_file: str, db_file: str):
        self.excel_file = excel_file
        self.db_file = db_file
        self.cleaner = DataFrameCleaner()

    def run(self) -> None:
        all_sheets = pd.read_excel(self.excel_file, sheet_name=None)

        with sqlite3.connect(self.db_file) as conn:
            for sheet_name, df in all_sheets.items():
                table_name = self.cleaner.normalize_column_name(sheet_name)
                df_clean = self.cleaner.clean(df)
                df_clean.to_sql(
                    table_name,
                    conn,
                    if_exists="replace",
                    index=False
                )

        print("Banco criado com tabelas e valores totalmente normalizados e limpos!")
