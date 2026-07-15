"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabaseClient";

export default function UploadPage() {
  const supabase = createClient();
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<string>("");
  const [result, setResult] = useState<any>(null);

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
        </div>
      )}
    </main>
  );
}
