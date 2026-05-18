import { useState } from "react";
import toast from "react-hot-toast";
import {
  curlSample,
  javascriptSample,
  pythonSample,
  typescriptSample,
  type AuthMode,
  type RequestSampleInput,
} from "../../lib/apiSamples";
import { cn } from "../../lib/cn";

const TABS = [
  { id: "curl", label: "cURL" },
  { id: "python", label: "Python" },
  { id: "typescript", label: "TypeScript" },
  { id: "javascript", label: "JavaScript" },
] as const;

type TabId = (typeof TABS)[number]["id"];

function sampleForTab(tab: TabId, input: RequestSampleInput): string {
  switch (tab) {
    case "curl":
      return curlSample(input);
    case "python":
      return pythonSample(input);
    case "typescript":
      return typescriptSample(input);
    case "javascript":
      return javascriptSample(input);
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard.writeText(text).then(
          () => {
            setCopied(true);
            toast.success("Copied");
            setTimeout(() => setCopied(false), 1600);
          },
          () => toast.error("Copy failed")
        );
      }}
      className="absolute right-2 top-2 rounded-[var(--radius-sm)] bg-[var(--surface-2)] px-2 py-1 text-[10px] font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)]"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function CodeSampleTabs({
  baseUrl,
  method,
  path,
  authMode = "bearer",
  query,
  body,
  multipart,
}: {
  baseUrl: string;
  method: string;
  path: string;
  authMode?: AuthMode;
  query?: string;
  body?: string;
  multipart?: boolean;
}) {
  const [tab, setTab] = useState<TabId>("curl");
  const input: RequestSampleInput = {
    baseUrl,
    method,
    path,
    auth: authMode,
    query,
    body,
    multipart,
  };
  const code = sampleForTab(tab, input);

  return (
    <div className="mt-4">
      <h4 className="text-sm font-medium text-[var(--text-primary)]">Request examples</h4>
      <div
        className="mt-2 flex flex-wrap gap-1 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-1"
        role="tablist"
      >
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-medium transition-colors",
              tab === t.id
                ? "bg-[var(--accent-soft)] text-[var(--accent-bright)]"
                : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>
      <div className="relative mt-2">
        <pre className="max-h-[420px] overflow-auto rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 text-xs leading-relaxed text-[var(--text-primary)]">
          <code className="whitespace-pre">{code}</code>
        </pre>
        <CopyButton text={code} />
      </div>
    </div>
  );
}
