"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabaseClient";

export default function UploadPage() {
  const supabase = createClient();
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");
  const [result, setResult] = useState<any>(null);
  const [token, setToken] = useState<string>("");
  const [generating, setGenerating] = useState(false);

  const handleShowToken = async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();
    if (!session) {
      setToken("Not logged in.");
      return;
    }
    setToken(session.access_token);
  };

  const handleCopyToken = async () => {
    await navigator.clipboard.writeText(token);
    setStatus("Token copied to clipboard.");
  };

  const handleGenerateCourse = async () => {
    if (!result?.document_id) return;

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      setStatus("Not logged in.");
      return;
    }

    setGenerating(true);
    setStatus("Generating course... this can take 30-60s (chunking, embeddings, AI course design).");

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/courses/generate/${result.document_id}`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${session.access_token}`,
          },
        }
      );

      if (!res.ok) {
        const err = await res.json();
        setStatus(`Error: ${err.detail}`);
        setGenerating(false);
        return;
      }

      const data = await res.json();
      setStatus(`Course "${data.title}" generated!`);
      setGenerating(false);
      router.push(`/course/${data.course_id}`);
    } catch (e) {
      setStatus("Course generation failed. Is the backend running?");
      setGenerating(false);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      setStatus("Not logged in.");
      return;
    }

    setStatus("Uploading & extracting text...");
    setResult(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/documents/upload`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${session.access_token}`,
        },
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        setStatus(`Error: ${err.detail}`);
        return;
      }

      const data = await res.json();
      setResult(data);
      setStatus("Done. Text extracted successfully.");
    } catch (e) {
      setStatus("Upload failed. Is the backend running?");
    }
  };

  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="mb-4 text-xl font-semibold">Upload a PDF</h1>

      <input
        type="file"
        accept="application/pdf"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="mb-4 block"
      />

      <button
        onClick={handleUpload}
        disabled={!file}
        className="rounded-lg bg-black px-4 py-2 text-white disabled:opacity-40"
      >
        Upload & Extract
      </button>

      {status && <p className="mt-4 text-sm text-neutral-600">{status}</p>}

      {result && (
        <div className="mt-6 rounded-lg border p-4 text-sm">
          <p><strong>Document ID:</strong> {result.document_id}</p>
          <p><strong>Pages:</strong> {result.page_count}</p>
          <p><strong>Characters:</strong> {result.char_count}</p>
          <p className="mt-2 whitespace-pre-wrap text-neutral-500">{result.preview}...</p>

          <button
            onClick={handleGenerateCourse}
            disabled={generating}
            className="mt-4 rounded-lg bg-indigo-600 px-4 py-2 text-white disabled:opacity-40"
          >
            {generating ? "Generating course..." : "Generate Course from this PDF"}
          </button>
        </div>
      )}

      {/* Dev-only helper: grab your access token to test endpoints in /docs (Swagger) */}
      <div className="mt-10 rounded-lg border border-dashed p-4 text-sm">
        <p className="mb-2 font-medium text-neutral-500">Dev: get token for Swagger testing</p>
        <button
          onClick={handleShowToken}
          className="mr-2 rounded-lg border px-3 py-1.5 text-xs"
        >
          Show my access token
        </button>
        {token && (
          <>
            <button
              onClick={handleCopyToken}
              className="rounded-lg border px-3 py-1.5 text-xs"
            >
              Copy
            </button>
            <p className="mt-2 max-h-24 overflow-y-auto break-all rounded bg-neutral-100 p-2 text-xs">
              {token}
            </p>
          </>
        )}
      </div>
    </main>
  );
}
