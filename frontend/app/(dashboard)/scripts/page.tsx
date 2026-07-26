"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Script = { id: string; title: string; language_mode: string; created_at: string };
type ParsedPreview = {
  scenes: { order: number; description: string; camera_notes: string }[];
  lines: { speaker_name: string | null; text: string; detected_language: string; expression_tag: string | null }[];
  unmatched_speakers: string[];
};

const SAMPLE_SCRIPT = `SCENE: A cozy modern living room, warm lighting, medium shot
[Aryan] (smiling, leaning forward): Hey, kaise ho aap?
[Meera] (curious, arms crossed): I'm good yaar, just thinking about our next trip.
CAMERA: slow zoom in
[Aryan] (laughing): Trip? Let's plan it right now!
`;

export default function ScriptsPage() {
  const [scripts, setScripts] = useState<Script[]>([]);
  const [title, setTitle] = useState("");
  const [rawText, setRawText] = useState(SAMPLE_SCRIPT);
  const [preview, setPreview] = useState<ParsedPreview | null>(null);

  function refresh() {
    apiFetch("/api/scripts").then(setScripts).catch(() => {});
  }

  useEffect(refresh, []);

  async function runPreview() {
    const result = await apiFetch("/api/scripts/parse-preview", {
      method: "POST",
      body: JSON.stringify({ title, raw_text: rawText }),
    });
    setPreview(result);
  }

  async function saveScript(e: React.FormEvent) {
    e.preventDefault();
    await apiFetch("/api/scripts", {
      method: "POST",
      body: JSON.stringify({ title, raw_text: rawText }),
    });
    setTitle("");
    setRawText("");
    setPreview(null);
    refresh();
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Scripts</h1>

      <form onSubmit={saveScript} className="space-y-3 rounded-lg border border-slate-800 p-4">
        <input
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          placeholder="Script title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
        <textarea
          className="h-56 w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 font-mono text-sm"
          value={rawText}
          onChange={(e) => setRawText(e.target.value)}
        />
        <div className="flex gap-2">
          <button
            type="button"
            onClick={runPreview}
            className="rounded bg-slate-700 px-4 py-2 text-sm hover:bg-slate-600"
          >
            Preview speakers/languages
          </button>
          <button className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500">
            Save script
          </button>
        </div>
      </form>

      {preview && (
        <div className="rounded-lg border border-slate-800 p-4">
          <h2 className="mb-2 font-medium">Parse preview</h2>
          {preview.unmatched_speakers.length > 0 && (
            <p className="mb-2 text-sm text-amber-400">
              Unmatched speakers (create these characters first): {preview.unmatched_speakers.join(", ")}
            </p>
          )}
          <div className="space-y-1 text-sm">
            {preview.lines.map((l, i) => (
              <div key={i} className="flex gap-3">
                <span className="w-24 text-slate-400">{l.speaker_name || "narration"}</span>
                <span className="w-20 text-xs text-slate-500">{l.detected_language}</span>
                <span>{l.text}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <h2 className="mb-2 font-medium">Saved scripts</h2>
        <div className="space-y-2">
          {scripts.map((s) => (
            <div key={s.id} className="flex items-center justify-between rounded border border-slate-800 px-4 py-2">
              <span>{s.title}</span>
              <Link href={`/scripts/${s.id}/generate`} className="text-sm text-indigo-400 hover:underline">
                Generate video →
              </Link>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
