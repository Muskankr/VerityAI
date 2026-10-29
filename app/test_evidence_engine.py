
import pytest

from app.evidence_engine import EvidenceEngine
from app.semantic_search import SemanticSearchEngine


def test_chunking_preserves_all_words():
    text = " ".join(f"word{i}" for i in range(250))

    chunks = EvidenceEngine.split_text(
        text, chunk_size=100, overlap=20
    )

    assert len(chunks) > 1
    assert chunks[0].startswith("word0")
    assert chunks[-1].endswith("word249")


def test_chunking_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        EvidenceEngine.split_text(
            "some text", chunk_size=10, overlap=10
        )


def test_search_preserves_duplicate_passage_metadata():
    engine = SemanticSearchEngine()

    engine.search = lambda query, top_k=3: [
        {
            "source": "policy.pdf",
            "page": 7,
            "text": "Scholarship applications require documents.",
            "similarity": 0.9
        },
        {
            "source": "guide.pdf",
            "page": 2,
            "text": "Scholarship applications require documents.",
            "similarity": 0.8
        }
    ]

    evidence = EvidenceEngine.__new__(EvidenceEngine)
    evidence.search_engine = engine
    evidence.chunks = [
        {
            "source": "policy.pdf",
            "page": 7,
            "text": "Scholarship applications require documents."
        },
        {
            "source": "guide.pdf",
            "page": 2,
            "text": "Scholarship applications require documents."
        }
    ]

    results = evidence.search("scholarship documents", top_k=2)

    assert results[0]["page"] == 7
    assert results[1]["page"] == 2


def test_search_requires_indexed_documents():
    evidence = EvidenceEngine.__new__(EvidenceEngine)
    evidence.chunks = []
    evidence.search_engine = SemanticSearchEngine.__new__(
        SemanticSearchEngine
    )

    with pytest.raises(RuntimeError):
        evidence.search("scholarship")
