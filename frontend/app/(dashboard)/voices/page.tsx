"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type Voice = {
  id: string;
  character_id: string;
  provider: string;
  provider_voice_id: string;
  language: string;
};

export default function VoicesPage() {
  const [voices, setVoices] = useState<Voice[]>([]);
  const [previewText, setPreviewText] = useState("Hello, this is a voice preview.");
  const [previewUrl, setPreviewUrl] = useState<Record<string, string>>({});

  useEffect(() => {
    apiFetch("/api/voices").then(setVoices).catch(() => {});
  }, []);

  async function preview(voiceId: string) {
    const result = await apiFetch(
      `/api/voices/${voiceId}/preview?text=${encodeURIComponent(previewText)}`,
      { method: "POST" }
    );
    setPreviewUrl((prev) => ({ ...prev, [voiceId]: result.audio_url }));
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Voice Library</h1>
      <input
        className="w-full max-w-md rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
        value={previewText}
        onChange={(e) => setPreviewText(e.target.value)}
        placeholder="Text to preview"
      />
      <table className="w-full text-sm">
        <thead className="text-slate-400 text-left">
          <tr>
            <th className="pb-2">Provider</th>
            <th className="pb-2">Voice ID</th>
            <th className="pb-2">Language</th>
            <th className="pb-2">Preview</th>
          </tr>
        </thead>
        <tbody>
          {voices.map((v) => (
            <tr key={v.id} className="border-t border-slate-800">
              <td className="py-2">{v.provider}</td>
              <td className="py-2">{v.provider_voice_id}</td>
              <td className="py-2">{v.language}</td>
              <td className="py-2">
                <button
                  onClick={() => preview(v.id)}
                  className="rounded bg-slate-700 px-3 py-1 text-xs hover:bg-slate-600"
                >
                  Play sample
                </button>
                {previewUrl[v.id] && (
                  <audio className="mt-1" controls src={previewUrl[v.id]} />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {voices.length === 0 && (
        <p className="text-sm text-slate-500">
          No voices yet — add one from a character&apos;s page.
        </p>
      )}
    </div>
  );
}
