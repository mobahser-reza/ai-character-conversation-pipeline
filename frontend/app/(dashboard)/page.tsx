"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Job = {
  id: string;
  status: string;
  progress_percent: number;
  created_at: string;
  output_video_url: string | null;
};

export default function DashboardPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [characterCount, setCharacterCount] = useState(0);
  const [scriptCount, setScriptCount] = useState(0);

  useEffect(() => {
    apiFetch("/api/jobs").then(setJobs).catch(() => {});
    apiFetch("/api/characters").then((c) => setCharacterCount(c.length)).catch(() => {});
    apiFetch("/api/scripts").then((s) => setScriptCount(s.length)).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg border border-slate-800 p-4">
          <p className="text-sm text-slate-400">Characters</p>
          <p className="text-3xl font-bold">{characterCount}</p>
        </div>
        <div className="rounded-lg border border-slate-800 p-4">
          <p className="text-sm text-slate-400">Scripts</p>
          <p className="text-3xl font-bold">{scriptCount}</p>
        </div>
        <div className="rounded-lg border border-slate-800 p-4">
          <p className="text-sm text-slate-400">Video Jobs</p>
          <p className="text-3xl font-bold">{jobs.length}</p>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-medium">Recent Jobs</h2>
        <div className="space-y-2">
          {jobs.slice(0, 8).map((job) => (
            <Link
              key={job.id}
              href={`/jobs/${job.id}`}
              className="flex items-center justify-between rounded border border-slate-800 px-4 py-2 hover:border-slate-600"
            >
              <span className="text-sm text-slate-300">{job.id.slice(0, 8)}</span>
              <span className="text-sm">{job.status}</span>
              <span className="text-sm text-slate-400">{job.progress_percent.toFixed(0)}%</span>
            </Link>
          ))}
          {jobs.length === 0 && <p className="text-sm text-slate-500">No jobs yet.</p>}
        </div>
      </div>
    </div>
  );
}
