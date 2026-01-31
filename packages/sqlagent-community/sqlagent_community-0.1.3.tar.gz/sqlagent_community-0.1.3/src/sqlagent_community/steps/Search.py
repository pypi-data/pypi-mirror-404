from sqlagent_community.utils.Rag import SemanticRetriever


class SemanticSearch:
    """Realiza busca semântica usando embeddings previamente gerados."""

    def __init__(self, embed_file: str, model: str, threshold: float = 0.1):
        self.embed_file = embed_file
        self.model = model
        self.threshold = threshold
        self.retriever = SemanticRetriever(embed_file, model)

    def search(self, query: str):
        return self.retriever.retrieve(
            query.lower(),
            threshold=self.threshold
        )
