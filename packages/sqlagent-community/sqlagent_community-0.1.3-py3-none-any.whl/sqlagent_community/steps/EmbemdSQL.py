from sqlagent_community.utils.Schema import (
    SchemaEmbedding,
    SchemaExtractor,
    SchemaSerializer,
    OllamaEmbeddingModel,
    EmbeddingStore,
)


class Embedding:
    """Gera embeddings do schema do banco e salva em um arquivo."""

    def __init__(
        self,
        db_path: str,
        embed_file: str,
        embed_model: str,
    ):
        self.db_path = db_path
        self.embed_file = embed_file
        self.embed_model = embed_model

        self.embedding = SchemaEmbedding(
            extractor=SchemaExtractor(db_path),
            serializer=SchemaSerializer(),
            embedding_model=OllamaEmbeddingModel(embed_model),
            store=EmbeddingStore(),
        )

    def run(self) -> None:
        self.embedding.run(self.embed_file)
