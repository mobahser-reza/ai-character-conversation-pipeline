"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiFetch } from "@/lib/api";

const ASPECT_RATIOS = ["9:16", "1:1", "16:9"];

export default function GeneratePage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [aspectRatio, setAspectRatio] = useState("9:16");
  const [submitting, setSubmitting] = useState(false);

  async function generate() {
    setSubmitting(true);
    try {
      const job = await apiFetch("/api/jobs", {
        method: "POST",
        body: JSON.stringify({ script_id: params.id, target_aspect_ratio: aspectRatio }),
      });
      router.push(`/jobs/${job.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-md space-y-6">
      <h1 className="text-2xl font-semibold">Generate Video</h1>
      <div>
        <label className="mb-1 block text-sm text-slate-400">Target aspect ratio</label>
        <select
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          value={aspectRatio}
          onChange={(e) => setAspectRatio(e.target.value)}
        >
          {ASPECT_RATIOS.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>
      <button
        onClick={generate}
        disabled={submitting}
        className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500 disabled:opacity-50"
      >
        {submitting ? "Starting…" : "Start pipeline"}
      </button>
    </div>
  );
}
