
from transformers import pipeline


class ClaimVerifier:
    """Compare a claim with evidence using natural-language inference."""

    LABEL_MAP = {
        "entailment": "SUPPORTED",
        "contradiction": "CONTRADICTED",
        "neutral": "INSUFFICIENT EVIDENCE",
    }

    def __init__(
        self,
        model_name="cross-encoder/nli-deberta-v3-small"
    ):
        print("Loading claim verification model on CPU...")

        self.classifier = pipeline(
            task="text-classification",
            model=model_name,
            device=-1
        )

        print("Claim verification model loaded.")

    def verify(self, claim, evidence_items):
        if not claim.strip():
            raise ValueError("Claim cannot be empty.")

        if not evidence_items:
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "confidence": None,
                "evidence": [],
                "message": "No evidence was provided."
            }

        candidates = []

        for item in evidence_items:
            text = item["text"].strip()

            if not text:
                continue

            # NLI input order: premise first, hypothesis second.
            prediction = self.classifier({
                "text": text,
                "text_pair": claim
            })

            candidates.append({
                "source": item["source"],
                "page": item["page"],
                "text": text,
                "label": prediction["label"].lower(),
                "score": float(prediction["score"])
            })

        if not candidates:
            return {
                "verdict": "INSUFFICIENT EVIDENCE",
                "confidence": None,
                "evidence": [],
                "message": "No usable evidence was provided."
            }

        # Look for evidence of either entailment or contradiction.
        
        threshold = 0.65

        supported = [
            item for item in candidates
            if item["label"] == "entailment"
            and item["score"] >= threshold
        ]

        contradicted = [
            item for item in candidates
            if item["label"] == "contradiction"
            and item["score"] >= threshold
        ]

        if supported and contradicted:
            verdict = "CONFLICTING EVIDENCE"
            confidence = None

        elif supported:
            best = max(supported, key=lambda item: item["score"])
            verdict = "SUPPORTED"
            confidence = round(best["score"], 4)

        elif contradicted:
            best = max(contradicted, key=lambda item: item["score"])
            verdict = "CONTRADICTED"
            confidence = round(best["score"], 4)

        else:
            verdict = "INSUFFICIENT EVIDENCE"
            confidence = None


        if not decisive:
            verdict = "INSUFFICIENT EVIDENCE"
            confidence = None
        else:
            # Pick the strongest model prediction among the
            # decisive evidence passages.
            best = max(decisive, key=lambda item: item["score"])
            verdict = self.LABEL_MAP[best["label"]]
            confidence = round(best["score"], 4)

        return {
            "verdict": verdict,
            "confidence": confidence,
            "evidence": [
                {
                    "source": item["source"],
                    "page": item["page"],
                    "text": item["text"],
                    "nli_label": item["label"],
                    "nli_score": round(item["score"], 4)
                }
                for item in candidates
            ],
            "message": (
                "Model output is a prediction, not proof. "
                "Review the cited passages before relying on it."
            )
        }



if __name__ == "__main__":
    verifier = ClaimVerifier()

    evidence = [
        {
            "source": "sample_policy.pdf",
            "page": 2,
            "text": (
                "Applicants must submit their academic marksheets "
                "with the scholarship application."
            ),
        }
    ]

    test_claims = [
        (
            "SUPPORTED",
            "Applicants must submit academic marksheets "
            "with their scholarship application.",
        ),
        (
            "CONTRADICTED",
            "Applicants do not need to submit academic marksheets "
            "with their scholarship application.",
        ),
        (
            "INSUFFICIENT EVIDENCE",
            "Applicants must be under 25 years old to apply.",
        ),
    ]

    for expected, claim in test_claims:
        result = verifier.verify(claim, evidence)

        print("\n" + "=" * 60)
        print("Claim:", claim)
        print("Expected:", expected)
        print("Actual:", result["verdict"])
        print("Confidence:", result["confidence"])
        print("Evidence source:", result["evidence"][0]["source"])
        print("Evidence page:", result["evidence"][0]["page"])
