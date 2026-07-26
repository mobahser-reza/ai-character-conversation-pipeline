"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";

type ApiKey = { id: string; provider_name: string; is_active: boolean };
type ProviderConfig = { id: string; capability: string; provider_name: string; is_default: boolean };

const CAPABILITIES = ["tts", "avatar", "video_gen", "subtitles"];
const KNOWN_PROVIDERS = ["elevenlabs", "heygen", "runway", "kling", "veo", "hedra", "local_stub"];

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>([]);
  const [providers, setProviders] = useState<ProviderConfig[]>([]);
  const [providerName, setProviderName] = useState("elevenlabs");
  const [apiKeyValue, setApiKeyValue] = useState("");

  function refresh() {
    apiFetch("/api/api-keys").then(setKeys).catch(() => {});
    apiFetch("/api/providers").then(setProviders).catch(() => {});
  }

  useEffect(refresh, []);

  async function saveKey(e: React.FormEvent) {
    e.preventDefault();
    await apiFetch("/api/api-keys", {
      method: "POST",
      body: JSON.stringify({ provider_name: providerName, api_key: apiKeyValue }),
    });
    setApiKeyValue("");
    refresh();
  }

  async function setActiveProvider(capability: string, provider_name: string) {
    await apiFetch("/api/providers", {
      method: "POST",
      body: JSON.stringify({ capability, provider_name, is_default: true }),
    });
    refresh();
  }

  function activeProviderFor(capability: string) {
    return providers.find((p) => p.capability === capability && p.is_default)?.provider_name || "local_stub";
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">API Keys & Providers</h1>

      <form onSubmit={saveKey} className="max-w-md space-y-3 rounded-lg border border-slate-800 p-4">
        <h2 className="font-medium">Add / update API key</h2>
        <select
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          value={providerName}
          onChange={(e) => setProviderName(e.target.value)}
        >
          {KNOWN_PROVIDERS.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
        <input
          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-2 text-sm"
          placeholder="API key"
          type="password"
          value={apiKeyValue}
          onChange={(e) => setApiKeyValue(e.target.value)}
          required
        />
        <button className="rounded bg-indigo-600 px-4 py-2 text-sm font-medium hover:bg-indigo-500">
          Save key
        </button>
      </form>

      <div>
        <h2 className="mb-2 font-medium">Stored keys</h2>
        <ul className="space-y-1 text-sm">
          {keys.map((k) => (
            <li key={k.id} className="text-slate-300">
              {k.provider_name} — {k.is_active ? "active" : "inactive"}
            </li>
          ))}
        </ul>
      </div>

      <div>
        <h2 className="mb-2 font-medium">Active provider per capability</h2>
        <p className="mb-3 text-xs text-slate-500">
          This is the swap mechanism — pick which provider runs each pipeline stage. Defaults to local_stub (no key needed) until you choose a real provider here.
        </p>
        <table className="w-full text-sm">
          <tbody>
            {CAPABILITIES.map((cap) => (
              <tr key={cap} className="border-t border-slate-800">
                <td className="py-2 pr-4 capitalize">{cap.replace("_", " ")}</td>
                <td className="py-2">
                  <select
                    className="rounded bg-slate-900 border border-slate-700 px-2 py-1 text-xs"
                    value={activeProviderFor(cap)}
                    onChange={(e) => setActiveProvider(cap, e.target.value)}
                  >
                    <option value="local_stub">local_stub (dev/dry-run)</option>
                    {KNOWN_PROVIDERS.filter((p) => p !== "local_stub").map((p) => (
                      <option key={p} value={p}>
                        {p}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
