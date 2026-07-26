"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { apiFetch } from "@/lib/api";

type Job = {
  id: string;
  status: string;
  current_stage: string | null;
  progress_percent: number;
  output_video_url: string | null;
  error_message: string | null;
};

const STAGES = ["tts", "avatar", "background", "composite", "subtitles", "export"];

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<Job | null>(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const data = await apiFetch(`/api/jobs/${params.id}`);
        if (!active) return;
        setJob(data);
        if (!["completed", "failed", "cancelled"].includes(data.status)) {
          setTimeout(poll, 2000);
        }
      } catch {
        /* auth redirect already handled in apiFetch */
      }
    }
    poll();
    return () => {
      active = false;
    };
  }, [params.id]);

  if (!job) return <p className="text-sm text-slate-500">Loading…</p>;

  const currentIndex = job.current_stage ? STAGES.indexOf(job.current_stage) : -1;

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">Job {job.id.slice(0, 8)}</h1>

      <div className="flex gap-2">
        {STAGES.map((stage, i) => (
          <div
            key={stage}
            className={`flex-1 rounded px-2 py-2 text-center text-xs ${
              i < currentIndex || job.status === "completed"
                ? "bg-emerald-700"
                : i === currentIndex
                ? "bg-indigo-600"
                : "bg-slate-800 text-slate-500"
            }`}
          >
            {stage}
          </div>
        ))}
      </div>

      <div className="h-2 w-full rounded bg-slate-800">
        <div
          className="h-2 rounded bg-indigo-500 transition-all"
          style={{ width: `${job.progress_percent}%` }}
        />
      </div>

      <p className="text-sm text-slate-400">
        Status: <span className="text-slate-100">{job.status}</span>
      </p>

      {job.error_message && <p className="text-sm text-red-400">{job.error_message}</p>}

      {job.output_video_url && (
        <video className="w-full max-w-sm rounded-lg border border-slate-800" controls src={job.output_video_url} />
      )}
    </div>
  );
}
