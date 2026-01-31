# semantic_retriever.py
import pickle
import numpy as np
import faiss
import ollama

class SemanticRetriever:
    def __init__(self, embed_file: str, embed_model="qwen3-embedding:0.6b"):
        """
        Inicializa o recuperador semântico carregando embeddings e textos.
        
        embed_file: caminho para o pickle contendo {"texts": [...], "embeddings": [...]}
        embed_model: nome do modelo de embeddings Ollama
        """
        self.embed_model = embed_model
        self.texts, self.embeddings = self._load_embeddings(embed_file)
        self.dim = self.embeddings.shape[1]
        self.index = self._build_index(self.embeddings)
        
    def _load_embeddings(self, embed_file: str):
        with open(embed_file, "rb") as f:
            data = pickle.load(f)
        texts = data["texts"]
        embeddings = np.array(data["embeddings"], dtype="float32")
        # Normaliza embeddings
        faiss.normalize_L2(embeddings)
        return texts, embeddings

    def _build_index(self, embeddings: np.ndarray):
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        return index

    def embed_query(self, query: str) -> np.ndarray:
        """Gera embedding para a query."""
        response = ollama.embed(model=self.embed_model, input=[query])
        q_emb = np.array(response["embeddings"])
        q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)  # normaliza
        return q_emb

    def retrieve(self, query: str, threshold: float = 0.2):
        """
        Recupera todos os textos cujo embedding seja semanticamente próximo da query,
        acima do threshold.
        """
        q_emb = self.embed_query(query)
        lims, D, I = self.index.range_search(q_emb, threshold)
        return [self.texts[i] for i in I]


