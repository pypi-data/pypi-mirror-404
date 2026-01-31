import re
import unicodedata
import numpy as np
import pandas as pd


class DataFrameCleaner:
    """Responsável por normalizar textos, nomes de colunas e limpar DataFrames."""

    @staticmethod
    def normalize_text(text: str) -> str | None:
        if not isinstance(text, str):
            return text

        text = text.lower()
        text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("utf-8")
        text = re.sub(r"[^a-z0-9 ]", "", text)
        text = re.sub(r"\s+", " ", text).strip()

        if text in {"", "null", "nan"}:
            return None

        return text

    @staticmethod
    def normalize_column_name(name: str) -> str:
        name = name.lower()
        name = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
        name = name.replace(" ", "_")
        name = re.sub(r"[^a-z0-9_]", "", name)
        return name

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # Normaliza nomes das colunas
        df.columns = [self.normalize_column_name(col) for col in df.columns]

        # Trata strings vazias e valores nulos textuais
        df.replace(r"^\s*$", np.nan, regex=True, inplace=True)
        df.replace({"null": np.nan, "nan": np.nan}, inplace=True)

        # Normaliza valores de texto
        for col in df.select_dtypes(include="object"):
            df[col] = df[col].apply(self.normalize_text)

        # Remove linhas e colunas totalmente nulas
        df.dropna(axis=0, how="all", inplace=True)
        df.dropna(axis=1, how="all", inplace=True)

        return df
