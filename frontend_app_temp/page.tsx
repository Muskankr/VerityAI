
"use client";

import { useEffect, useState } from "react";

type Evidence = {
  source: string;
  page: number;
  text: string;
  nli_label?: string;
  nli_score?: number;
};

type VerificationResult = {
  claim: string;
  verdict: string;
  confidence: number | null;
  evidence: Evidence[];
  message: string;
};

type DocumentItem = {
  filename: string;
  display_name: string;
  chunks: number;
};

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [claim, setClaim] = useState("");
  const [result, setResult] = useState<VerificationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [libraryError, setLibraryError] = useState("");
  const [notice, setNotice] = useState("");

  useEffect(() => {
    let active = true;

    async function loadDocuments() {
      try {
        const response = await fetch(`${API_URL}/documents`);

        if (!response.ok) {
          throw new Error("Could not load the document library.");
        }

        const data = await response.json();

        if (active) {
          setDocuments(data.documents ?? []);
          setLibraryError("");
        }
      } catch {
        if (active) {
          setLibraryError(
            "Unable to load documents. Check that the backend is running."
          );
        }
      } finally {
        if (active) {
          setLoadingDocuments(false);
        }
      }
    }

    loadDocuments();

    return () => {
      active = false;
    };
  }, []);

  async function refreshDocuments() {
    const response = await fetch(`${API_URL}/documents`);

    if (!response.ok) {
      throw new Error("Could not refresh the document library.");
    }

    const data = await response.json();
    setDocuments(data.documents ?? []);
    setLibraryError("");
  }

  async function uploadDocument() {
    if (!file) {
      setError("Choose a PDF document first.");
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError("The PDF must be 15 MB or smaller.");
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    setResult(null);

    try {
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(`${API_URL}/documents`, {
        method: "POST",
        body,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Document upload failed.");
      }

      setNotice(
        `${data.filename} indexed successfully. ${data.chunks_added} text chunks added.`
      );

      setFile(null);

      const input = document.getElementById(
        "pdf"
      ) as HTMLInputElement | null;

      if (input) {
        input.value = "";
      }

      try {
        await refreshDocuments();
      } catch {
        setLibraryError(
          "Upload succeeded, but the document library could not refresh."
        );
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Cannot connect to VerityAI. Check that the API is running."
      );
    } finally {
      setBusy(false);
    }
  }

  async function verifyClaim() {
    if (documents.length === 0) {
      setError("Upload and index a PDF before verifying a claim.");
      return;
    }

    if (!claim.trim()) {
      setError("Enter a claim to verify.");
      return;
    }

    setBusy(true);
    setError("");
    setNotice("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          claim: claim.trim(),
          top_k: 5,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail ?? "Claim verification failed.");
      }

      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not verify this claim."
      );
    } finally {
      setBusy(false);
    }
  }

  const verdictStyle =
    result?.verdict === "SUPPORTED"
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : result?.verdict === "CONTRADICTED"
        ? "border-rose-500/30 bg-rose-500/10 text-rose-300"
        : result?.verdict === "CONFLICTING EVIDENCE"
          ? "border-orange-500/30 bg-orange-500/10 text-orange-200"
          : "border-amber-500/30 bg-amber-500/10 text-amber-200";

  return (
    <main className="min-h-screen bg-[#080c16] text-slate-100">
      <header className="border-b border-white/10">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
          <a href="/" className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-cyan-400 font-black text-slate-950">
              V
            </div>

            <div>
              <h1 className="text-lg font-bold tracking-tight">
                VerityAI
              </h1>
              <p className="text-xs text-slate-400">
                Evidence-first document intelligence
              </p>
            </div>
          </a>

          <span className="rounded-full border border-cyan-400/20 px-3 py-1.5 text-xs text-cyan-300">
            CPU inference
          </span>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-5 py-12 sm:py-16">
        <div className="max-w-3xl">
          <p className="mb-4 text-xs font-semibold uppercase tracking-[0.25em] text-cyan-300">
            DOCUMENT INTELLIGENCE / 01
          </p>

          <h2 className="text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Don&apos;t just read documents.
            <span className="block text-cyan-300">
              Verify the evidence.
            </span>
          </h2>

          <p className="mt-5 max-w-2xl text-base leading-7 text-slate-400">
            Upload a PDF, enter a factual claim, and retrieve relevant
            passages with source and page references to help assess it.
          </p>
        </div>

        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-6">
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <p className="text-sm text-cyan-300">01 / SOURCE</p>
                <h3 className="mt-2 text-xl font-semibold">
                  Add a document
                </h3>
              </div>

              <span className="rounded-lg bg-white/5 px-3 py-2 text-xs text-slate-400">
                PDF · 15 MB max
              </span>
            </div>

            <label
              htmlFor="pdf"
              className="flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-slate-600 bg-black/20 p-5 text-center transition hover:border-cyan-400"
            >
              <span className="text-3xl">↥</span>

              <span className="mt-3 break-all text-sm font-medium">
                {file ? file.name : "Choose your PDF"}
              </span>

              <span className="mt-2 text-xs text-slate-500">
                Select a text-based PDF from your device
              </span>

              <input
                id="pdf"
                type="file"
                accept=".pdf,application/pdf"
                className="sr-only"
                onChange={(event) => {
                  const selected = event.target.files?.[0] ?? null;

                  setFile(selected);
                  setResult(null);
                  setError("");
                  setNotice("");
                }}
              />
            </label>

            <button
              onClick={uploadDocument}
              disabled={busy || !file}
              className="mt-5 w-full rounded-xl bg-cyan-300 px-5 py-3.5 font-semibold text-slate-950 transition hover:bg-cyan-200 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Processing..." : "Upload & index document"}
            </button>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              Documents are processed by your local backend.
              Scanned PDFs may require OCR.
            </p>
          </section>

          <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-6">
            <p className="text-sm text-cyan-300">02 / CLAIM</p>

            <h3 className="mt-2 text-xl font-semibold">
              Verify a statement
            </h3>

            <p className="mt-3 text-sm leading-6 text-slate-400">
              Enter one factual statement to compare against the
              indexed documents.
            </p>

            <label
              htmlFor="claim"
              className="mt-6 block text-sm font-medium text-slate-300"
            >
              Your claim
            </label>

            <textarea
              id="claim"
              value={claim}
              onChange={(event) => setClaim(event.target.value)}
              placeholder="Example: Applicants must submit academic marksheets."
              rows={5}
              maxLength={2000}
              className="mt-2 w-full resize-y rounded-xl border border-white/10 bg-black/20 p-4 text-sm leading-6 outline-none transition placeholder:text-slate-600 focus:border-cyan-400"
            />

            <div className="mt-2 text-right text-xs text-slate-500">
              {claim.length}/2000
            </div>

            <button
              onClick={verifyClaim}
              disabled={busy || documents.length === 0 || !claim.trim()}
              className="mt-3 w-full rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-5 py-3.5 font-semibold text-cyan-200 transition hover:bg-cyan-400/20 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "Analyzing..." : "Verify claim →"}
            </button>

            {documents.length === 0 && (
              <p className="mt-3 text-xs text-slate-500">
                Upload a PDF first to enable verification.
              </p>
            )}
          </section>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-xl border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-200"
          >
            {error}
          </div>
        )}

        {notice && (
          <div
            role="status"
            className="mt-6 rounded-xl border border-emerald-400/20 bg-emerald-400/5 p-4 text-sm text-emerald-200"
          >
            {notice}
          </div>
        )}

        <section className="mt-10 rounded-2xl border border-white/10 bg-white/[0.035] p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm text-cyan-300">YOUR WORKSPACE</p>
              <h3 className="mt-2 text-xl font-semibold">
                Document Library
              </h3>
            </div>

            <span className="rounded-full border border-white/10 px-3 py-1.5 text-xs text-slate-300">
              {documents.length} indexed
            </span>
          </div>

          {loadingDocuments ? (
            <p className="mt-5 text-sm text-slate-400">
              Loading documents...
            </p>
          ) : documents.length === 0 ? (
            <p className="mt-5 text-sm text-slate-400">
              No indexed documents found. Upload a PDF to get started.
            </p>
          ) : (
            <div className="mt-5 space-y-3">
              {documents.map((doc) => (
                <div
                  key={doc.filename}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 p-4"
                >
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="text-2xl">📄</span>

                    <div className="min-w-0">
                      <p className="break-all text-sm font-medium">
                        {doc.display_name}
                      </p>
                      <p className="mt-1 text-xs text-slate-500">
                        PDF document
                      </p>
                    </div>
                  </div>

                  <span className="text-xs text-cyan-300">
                    {doc.chunks} chunks
                  </span>
                </div>
              ))}
            </div>
          )}

          {libraryError && (
            <p role="status" className="mt-4 text-sm text-amber-200">
              {libraryError}
            </p>
          )}

          <button
            type="button"
            onClick={async () => {
              setLibraryError("");

              try {
                await refreshDocuments();
              } catch {
                setLibraryError("Could not refresh the document library.");
              }
            }}
            disabled={busy || loadingDocuments}
            className="mt-5 rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 disabled:opacity-40"
          >
            Refresh library
          </button>
        </section>

        {result && (
          <section className="mt-10">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm text-cyan-300">03 / ANALYSIS</p>
                <h3 className="mt-2 text-2xl font-bold">
                  Verification results
                </h3>
              </div>

              <span className="text-xs text-slate-500">
                Model prediction · Not a factual guarantee
              </span>
            </div>

            <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.035] p-6">
              <p className="text-xs uppercase tracking-widest text-slate-500">
                Claim submitted
              </p>

              <p className="mt-2 leading-7">{result.claim}</p>

              <div className="mt-6 flex flex-wrap items-center gap-3">
                <span
                  className={`rounded-full border px-4 py-2 text-sm font-semibold ${verdictStyle}`}
                >
                  {result.verdict}
                </span>

                {result.confidence !== null && (
                  <span className="text-sm text-slate-400">
                    Model score:{" "}
                    {(result.confidence * 100).toFixed(2)}%
                  </span>
                )}
              </div>

              <p className="mt-4 text-sm leading-6 text-slate-400">
                {result.message}
              </p>
            </div>

            <div className="mt-8">
              <h4 className="text-xl font-semibold">
                Retrieved evidence
              </h4>

              <p className="mt-2 text-sm text-slate-400">
                Review these passages and citations before relying
                on the prediction.
              </p>

              {result.evidence.length === 0 ? (
                <p className="mt-4 rounded-xl border border-white/10 p-5 text-sm text-slate-400">
                  No evidence passages were returned.
                </p>
              ) : (
                <div className="mt-5 space-y-4">
                  {result.evidence.map((item, index) => (
                    <article
                      key={`${item.source}-${item.page}-${index}`}
                      className="rounded-2xl border border-white/10 bg-white/[0.025] p-5"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <p className="break-all text-sm font-semibold text-cyan-200">
                          {item.source}
                        </p>

                        <span className="rounded-lg bg-white/5 px-3 py-1.5 text-xs text-slate-300">
                          Page {item.page}
                        </span>
                      </div>

                      <blockquote className="mt-4 border-l-2 border-cyan-400/60 pl-4 text-sm leading-7 text-slate-300">
                        {item.text}
                      </blockquote>

                      <div className="mt-4 flex flex-wrap gap-3 text-xs text-slate-500">
                        {item.nli_label && (
                          <span>NLI: {item.nli_label}</span>
                        )}

                        {item.nli_score !== undefined && (
                          <span>
                            NLI score:{" "}
                            {(item.nli_score * 100).toFixed(2)}%
                          </span>
                        )}
                      </div>
                    </article>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        <footer className="mt-16 border-t border-white/10 py-7 text-xs leading-6 text-slate-500">
          VerityAI · Evidence-first document intelligence
          <span className="block">
            Experimental AI predictions can be wrong. Always check
            the original document.
          </span>
        </footer>
      </section>
    </main>
  );
}
