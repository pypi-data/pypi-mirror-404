import sqlite3
import pickle
from dataclasses import dataclass
from typing import Dict, List, Protocol
import ollama


@dataclass
class TableSchemaDoc:
    table: str
    ddl: str
    examples: Dict[str, List[str]]



class SchemaExtractor:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def extract(self) -> List[TableSchemaDoc]:
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        cur.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table';"
        )
        tables = cur.fetchall()

        docs: List[TableSchemaDoc] = []

        for table_name, create_sql in tables:
            if not create_sql:
                continue

            cur.execute(f"PRAGMA table_info({table_name});")
            columns = cur.fetchall()

            examples = self._extract_examples(
                cur, table_name, columns
            )

            docs.append(
                TableSchemaDoc(
                    table=table_name,
                    ddl=create_sql,
                    examples=examples,
                )
            )

        con.close()
        return docs

    def _extract_examples(self, cur, table_name, columns):
        examples: Dict[str, List[str]] = {}

        for _, col_name, *_ in columns:
            try:
                cur.execute(
                    f"""
                    SELECT DISTINCT {col_name}
                    FROM {table_name}
                    WHERE {col_name} IS NOT NULL
                    LIMIT 3;
                    """
                )
                vals = [str(v[0]) for v in cur.fetchall()]
                if vals:
                    examples[col_name] = vals
            except sqlite3.Error:
                # Colunas incompatíveis (BLOB, JSON estranho, etc.)
                pass

        return examples



class SchemaSerializer:
    def serialize(self, table_doc: TableSchemaDoc) -> str:
        lines = [f"{table_doc.ddl};\n"]

        if table_doc.examples:
            lines.append("-- Column examples")
            for col, vals in table_doc.examples.items():
                lines.append(f"-- {col}: {', '.join(vals)}")

        return "\n".join(lines)

    def serialize_many(
        self, docs: List[TableSchemaDoc]
    ) -> List[str]:
        return [self.serialize(d) for d in docs]


class EmbeddingModel(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]:
        ...


class OllamaEmbeddingModel:
    def __init__(self, model_name: str):
        self.model_name = model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        response = ollama.embed(
            model=self.model_name,
            input=texts,
        )
        return response["embeddings"]


class EmbeddingStore:
    def save(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        path: str,
    ):
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "texts": texts,
                    "embeddings": embeddings,
                },
                f,
            )


class SchemaEmbedding:
    def __init__(
        self,
        extractor: SchemaExtractor,
        serializer: SchemaSerializer,
        embedding_model: EmbeddingModel,
        store: EmbeddingStore,
    ):
        self.extractor = extractor
        self.serializer = serializer
        self.embedding_model = embedding_model
        self.store = store

    def run(self, output_path: str):
        docs = self.extractor.extract()
        texts = self.serializer.serialize_many(docs)
        embeddings = self.embedding_model.embed(texts)
        self.store.save(texts, embeddings, output_path)


if __name__ == "__main__":
    EMBED_MODEL = "qwen3-embedding:0.6b"

    pipeline = SchemaEmbedding(
        extractor=SchemaExtractor("database.db"),
        serializer=SchemaSerializer(),
        embedding_model=OllamaEmbeddingModel(EMBED_MODEL),
        store=EmbeddingStore(),
    )

    pipeline.run("schema_embeddings.pkl")
