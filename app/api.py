
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.pipeline import VerityAI


app = FastAPI(
    title="VerityAI API",
    description="Evidence-based PDF claim verification",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_SIZE = 15 * 1024 * 1024
verity = None


def get_engine():
    global verity

    if verity is None:
        verity = VerityAI()

    return verity


def display_filename(stored_name: str) -> str:
    """Recover the original display name from our stored filename."""
    if len(stored_name) > 33 and stored_name[32] == "_":
        return stored_name[33:]

    return stored_name


@app.on_event("startup")
def restore_saved_documents():
    """Rebuild the in-memory search index from saved PDFs."""
    saved_pdfs = sorted(UPLOAD_DIR.glob("*.pdf"))

    # Avoid loading the AI models when there are no saved documents.
    if not saved_pdfs:
        return

    engine = get_engine()

    for pdf_path in saved_pdfs:
        try:
            result = engine.add_document(pdf_path)
            print(
                f"Restored {pdf_path.name}: "
                f"{result['chunks_added']} chunks"
            )
        except Exception as error:
            print(
                f"Could not restore {pdf_path.name}: {error}"
            )


class ClaimRequest(BaseModel):
    claim: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=10)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "project": "VerityAI",
        "version": "0.1.0",
    }


@app.get("/documents")
def list_documents():
    """List successfully indexed documents."""
    if verity is None:
        return {"count": 0, "documents": []}

    documents = []

    for stored_name in verity.indexed_files:
        matching_chunks = [
            chunk
            for chunk in verity.evidence_engine.chunks
            if chunk["source"] == stored_name
        ]

        documents.append({
            "filename": stored_name,
            "display_name": display_filename(stored_name),
            "chunks": len(matching_chunks),
        })

    return {
        "count": len(documents),
        "documents": documents,
    }


@app.post("/documents")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Please select a PDF file.",
        )

    # Handle both Windows-style and Unix-style filename separators.
    original_name = Path(
        file.filename.replace("\\", "/")
    ).name

    if Path(original_name).suffix.lower() != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported.",
        )

    try:
        content = await file.read(MAX_FILE_SIZE + 1)

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="PDF exceeds the 15 MB upload limit.",
            )

        if not content.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="The uploaded file does not appear to be a PDF.",
            )

        # Unique storage names prevent accidental overwrites.
        stored_name = f"{uuid4().hex}_{original_name}"
        saved_path = UPLOAD_DIR / stored_name

        try:
            saved_path.write_bytes(content)

            result = get_engine().add_document(saved_path)

            return {
                "message": "Document indexed successfully.",
                "filename": original_name,
                "stored_filename": stored_name,
                "chunks_added": result["chunks_added"],
            }

        except HTTPException:
            saved_path.unlink(missing_ok=True)
            raise

        except Exception as error:
            saved_path.unlink(missing_ok=True)
            raise HTTPException(
                status_code=500,
                detail="Document processing failed.",
            ) from error

    finally:
        await file.close()


@app.post("/verify")
def verify_claim(request: ClaimRequest):
    if not request.claim.strip():
        raise HTTPException(
            status_code=400,
            detail="Claim cannot be empty.",
        )

    if verity is None or not verity.indexed_files:
        raise HTTPException(
            status_code=400,
            detail="Upload and index a PDF before verifying claims.",
        )

    try:
        return verity.verify_claim(
            request.claim.strip(),
            top_k=request.top_k,
        )

    except (ValueError, RuntimeError) as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error
