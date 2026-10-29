
from pathlib import Path

from app.pdf_reader import PDFReader
from app.semantic_search import SemanticSearchEngine


class EvidenceEngine:
    def __init__(self, chunk_size=180, overlap=40):
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be between 0 and chunk_size - 1.")

        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks = []
        self.search_engine = SemanticSearchEngine()
        self.pdf_reader = PDFReader()

    def _split_text(self, text):
        words = text.split()
        chunks = []
        step = self.chunk_size - self.overlap

        for start in range(0, len(words), step):
            chunk_text = " ".join(words[start:start + self.chunk_size])

            if chunk_text.strip():
                chunks.append(chunk_text)

            if start + self.chunk_size >= len(words):
                break

        return chunks

    def index_pdf(self, pdf_path):
        path = Path(pdf_path).expanduser()

        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")

        pages = self.pdf_reader.read_pdf(str(path))
        new_chunks = []

        for page_data in pages:
            text = page_data.get("text", "").strip()

            if not text:
                continue

            for chunk_text in self._split_text(text):
                new_chunks.append({
                    "source": path.name,
                    "page": page_data.get("page"),
                    "text": chunk_text,
                })

        if not new_chunks:
            raise ValueError(
                f"No extractable text found in {path.name}. "
                "The PDF may be scanned or empty."
            )

        # Avoid modifying the existing index until extraction succeeds.
        updated_chunks = self.chunks + new_chunks
        self.search_engine.index_documents(updated_chunks)
        self.chunks = updated_chunks

        return len(new_chunks)

    def search(self, query, top_k=5, source=None):
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if source is not None:
            available_sources = {
                chunk["source"] for chunk in self.chunks
            }

            if source not in available_sources:
                raise ValueError(f"Document not found: {source}")

            candidates = [
                chunk for chunk in self.chunks
                if chunk["source"] == source
            ]
        else:
            candidates = self.chunks

        if not candidates:
            return []

        # Search within the chosen document only, when specified.
        temporary_engine = SemanticSearchEngine()
        temporary_engine.index_documents(candidates)

        return temporary_engine.search(query, top_k=top_k)
