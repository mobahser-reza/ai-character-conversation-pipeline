"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiFetch } from "@/lib/api";

type Job = {
  id: string;
  status: string;
  progress_percent: number;
  target_aspect_ratio: string;
  created_at: string;
};

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    apiFetch("/api/jobs").then(setJobs).catch(() => {});
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Video Generation History</h1>
      <table className="w-full text-sm">
        <thead className="text-left text-slate-400">
          <tr>
            <th className="pb-2">Job</th>
            <th className="pb-2">Status</th>
            <th className="pb-2">Progress</th>
            <th className="pb-2">Aspect</th>
            <th className="pb-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((j) => (
            <tr key={j.id} className="border-t border-slate-800">
              <td className="py-2">
                <Link href={`/jobs/${j.id}`} className="text-indigo-400 hover:underline">
                  {j.id.slice(0, 8)}
                </Link>
              </td>
              <td className="py-2">{j.status}</td>
              <td className="py-2">{j.progress_percent.toFixed(0)}%</td>
              <td className="py-2">{j.target_aspect_ratio}</td>
              <td className="py-2 text-slate-400">{new Date(j.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
