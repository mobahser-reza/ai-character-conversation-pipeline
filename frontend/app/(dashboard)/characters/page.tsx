"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type VoiceProfile = {
  id: string;
  provider: string;
  provider_voice_id: string;
  language: string;
};

type Character = {
  id: string;
  name: string;
  description: string;
  appearance_ref_image_url: string | null;
  personality_profile: Record<string, unknown>;
  voices: VoiceProfile[];
};

export default function CharactersPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");

  function refresh() {
    apiFetch("/api/characters").then(setCharacters).catch(() => {});
  }

  useEffect(refresh, []);

  async function createCharacter(e: React.FormEvent) {
    e.preventDefault();
    await apiFetch("/api/characters", {
      method: "POST",
      body: JSON.stringify({ name, description, appearance_ref_image_url: imageUrl || null }),
    });
    setName("");
    setDescription("");
    setImageUrl("");
    refresh();
  }

  async function addVoice(characterId: string, provider: string, providerVoiceId: string, language: string) {
    await apiFetch(`/api/characters/${characterId}/voices`, {
      method: "POST",
      body: JSON.stringify({ provider, provider_voice_id: providerVoiceId, language }),
    });
    refresh();
  }

  async function deleteCharacter(id: string) {
    await apiFetch(`/api/characters/${id}`, { method: "DELETE" });
    refresh();
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Characters</h1>

      <form onSubmit={createCharacter} className="max-w-lg space-y-3 rounded-lg border border-slate-800 p-4">
        <h2 className="font-medium">Add character</h2>
        <input
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          placeholder="Name (e.g. Aryan)"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <textarea
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          placeholder="Personality / description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <input
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          placeholder="Reference image URL"
          value={imageUrl}
          onChange={(e) => setImageUrl(e.target.value)}
        />
        <button className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500">
          Create
        </button>
      </form>

      <div className="grid grid-cols-2 gap-4">
        {characters.map((c) => (
          <div key={c.id} className="rounded-lg border border-slate-800 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">{c.name}</h3>
              <button onClick={() => deleteCharacter(c.id)} className="text-xs text-red-400 hover:underline">
                Delete
              </button>
            </div>
            <p className="text-sm text-slate-400">{c.description || "No description"}</p>
            <div>
              <p className="text-xs uppercase text-slate-500 mb-1">Voices</p>
              {c.voices.map((v) => (
                <div key={v.id} className="text-sm text-slate-300">
                  {v.provider} / {v.provider_voice_id} ({v.language})
                </div>
              ))}
              <AddVoiceForm characterId={c.id} onAdd={addVoice} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AddVoiceForm({
  characterId,
  onAdd,
}: {
  characterId: string;
  onAdd: (characterId: string, provider: string, providerVoiceId: string, language: string) => void;
}) {
  const [provider, setProvider] = useState("elevenlabs");
  const [voiceId, setVoiceId] = useState("");
  const [language, setLanguage] = useState("en");

  return (
    <div className="mt-2 flex gap-2">
      <select
        className="rounded bg-slate-900 border border-slate-700 px-2 py-1 text-xs"
        value={provider}
        onChange={(e) => setProvider(e.target.value)}
      >
        <option value="elevenlabs">ElevenLabs</option>
        <option value="local_stub">Local Stub</option>
      </select>
      <input
        className="flex-1 rounded bg-slate-900 border border-slate-700 px-2 py-1 text-xs"
        placeholder="Provider voice id"
        value={voiceId}
        onChange={(e) => setVoiceId(e.target.value)}
      />
      <select
        className="rounded bg-slate-900 border border-slate-700 px-2 py-1 text-xs"
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
      >
        <option value="en">English</option>
        <option value="hi">Hindi</option>
        <option value="hinglish">Hinglish</option>
      </select>
      <button
        onClick={() => voiceId && onAdd(characterId, provider, voiceId, language)}
        className="rounded bg-slate-700 px-2 py-1 text-xs hover:bg-slate-600"
      >
        Add
      </button>
    </div>
  );
}
