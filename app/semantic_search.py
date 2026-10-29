
from sentence_transformers import SentenceTransformer
import numpy as np


class SemanticSearchEngine:
    """Semantic search that preserves passage identity and metadata."""

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        print("Loading semantic embedding model...")
        self.model = SentenceTransformer(model_name, device="cpu")
        self.passages = []
        self.embeddings = None
        print("Model loaded successfully!")

    def index(self, passages):
        if not passages:
            raise ValueError("At least one passage is required.")

        self.passages = list(passages)

        self.embeddings = self.model.encode(
            [item["text"] if isinstance(item, dict) else item
             for item in self.passages],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        return len(self.passages)

    def search(self, query, top_k=3):
        if not query.strip():
            raise ValueError("Query cannot be empty.")

        if self.embeddings is None:
            raise RuntimeError("Index passages before searching.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True
        )[0]

        scores = self.embeddings @ query_embedding
        ranked_indices = np.argsort(scores)[::-1][:top_k]

        results = []

        for idx in ranked_indices:
            passage = self.passages[int(idx)]

            if isinstance(passage, dict):
                result = passage.copy()
                result["similarity"] = round(float(scores[idx]), 4)
            else:
                result = {
                    "passage": passage,
                    "similarity": round(float(scores[idx]), 4)
                }

            results.append(result)

        return results
