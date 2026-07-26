export default function DocsPage() {
  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-2xl font-semibold">Documentation</h1>
      <p className="text-sm text-slate-400">
        Full docs live in the repo under <code>/docs</code>: architecture.md, api-reference.md, and
        training-guide.md. Open them in your editor or a markdown viewer — this page is a pointer,
        not a renderer, so the docs stay easy to diff and version alongside the code.
      </p>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
        <li>docs/architecture.md — system design, provider swap mechanism, DB schema</li>
        <li>docs/api-reference.md — every endpoint, request/response shape</li>
        <li>docs/training-guide.md — step-by-step: character → voice → script → generate</li>
        <li>docs/video-production-log/ — one write-up per produced sample video</li>
      </ul>
    </div>
  );
}
