
from pathlib import Path

from app.evidence_engine import EvidenceEngine
from app.claim_verifier import ClaimVerifier


class VerityAI:
    """End-to-end evidence retrieval and claim verification."""

    def __init__(self):
        self.evidence_engine = EvidenceEngine()
        self.claim_verifier = ClaimVerifier()
        self.indexed_files = []

    def add_document(self, pdf_path):
        path = Path(pdf_path).expanduser()

        if not path.is_file():
            raise FileNotFoundError(f"PDF not found: {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError("Only PDF files are supported.")

        added_chunks = self.evidence_engine.index_pdf(path)
        self.indexed_files.append(path.name)

        return {
            "filename": path.name,
            "chunks_added": added_chunks,
            "total_documents": len(self.indexed_files),
        }

    def verify_claim(self, claim, top_k=5):
        if not isinstance(claim, str) or not claim.strip():
            raise ValueError("Please enter a non-empty claim.")

        evidence = self.evidence_engine.search(
            claim,
            top_k=top_k,
        )

        result = self.claim_verifier.verify(claim, evidence)

        return {
            "claim": claim,
            "verdict": result["verdict"],
            "confidence": result["confidence"],
            "evidence": result["evidence"],
            "message": result["message"],
        }


if __name__ == "__main__":
    app = VerityAI()

    print("\n=== VerityAI: Document Claim Verification ===")

    while True:
        pdf_path = input(
            "\nEnter PDF path (or 'done' to finish adding documents): "
        ).strip().strip('"')

        if pdf_path.lower() == "done":
            break

        if not pdf_path:
            print("Please enter a PDF path.")
            continue

        try:
            result = app.add_document(pdf_path)
            print(f"Indexed: {result['filename']}")
            print(f"Chunks added: {result['chunks_added']}")
        except (FileNotFoundError, ValueError, RuntimeError) as error:
            print(f"Could not add document: {error}")

    if not app.indexed_files:
        print("No documents indexed. Exiting.")
    else:
        while True:
            claim = input(
                "\nEnter a claim to verify (or 'exit' to quit): "
            ).strip()

            if claim.lower() == "exit":
                break

            try:
                result = app.verify_claim(claim)

                print("\n" + "=" * 55)
                print("CLAIM:", result["claim"])
                print("VERDICT:", result["verdict"])
                print("MODEL SCORE:", result["confidence"])
                print("\nRETRIEVED EVIDENCE:")

                for item in result["evidence"]:
                    print(
                        f"\nSource: {item['source']} | "
                        f"Page: {item['page']}"
                    )
                    print(f"Evidence: {item['text']}")
                    print(f"NLI label: {item['nli_label']}")
                    print(f"NLI score: {item['nli_score']}")

                print("\nNOTE:", result["message"])

            except (ValueError, RuntimeError) as error:
                print(f"Verification error: {error}")
