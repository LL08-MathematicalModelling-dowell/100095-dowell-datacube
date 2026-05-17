/* eslint-disable @typescript-eslint/no-explicit-any */
import { ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "../../lib/cn";

function JsonKey({ name }: { name: string }) {
  return (
    <span className="text-[var(--info)] font-medium">{JSON.stringify(name)}:</span>
  );
}

function JsonScalar({ value }: { value: unknown }) {
  if (value === null)
    return <span className="text-[var(--text-subtle)] italic">null</span>;
  if (typeof value === "boolean")
    return <span className="text-[var(--chart-3)]">{String(value)}</span>;
  if (typeof value === "number")
    return <span className="text-[var(--chart-5)]">{value}</span>;
  if (typeof value === "string") {
    const isOid = /^[a-fA-F0-9]{24}$/.test(value);
    return (
      <span
        className={cn(
          "break-all",
          isOid ? "text-[var(--accent-bright)]" : "text-[var(--chart-2)]"
        )}
      >
        {JSON.stringify(value)}
      </span>
    );
  }
  return <span className="text-[var(--text-muted)]">{String(value)}</span>;
}

export function JsonTreeView({
  data,
  maxDepth = 8,
  className,
}: {
  data: unknown;
  maxDepth?: number;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-3 font-[var(--font-mono)] text-[13px] leading-relaxed overflow-auto max-h-[480px]",
        className
      )}
    >
      <TreeNode path="$" value={data} depth={0} maxDepth={maxDepth} />
    </div>
  );
}

function TreeNode({
  path: _path,
  value,
  depth,
  maxDepth,
}: {
  path: string;
  value: unknown;
  depth: number;
  maxDepth: number;
}) {
  const [open, setOpen] = useState(depth < 2);

  if (value === null || typeof value !== "object") {
    return <JsonScalar value={value} />;
  }

  if (Array.isArray(value)) {
    if (depth >= maxDepth) {
      return (
        <span className="text-[var(--text-muted)]">
          [ … {value.length} items ]
        </span>
      );
    }
    return (
      <div>
        <button
          type="button"
          onClick={() => setOpen(!open)}
          className="inline-flex items-center gap-0.5 text-left text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        >
          <ChevronRight
            className={cn(
              "h-4 w-4 shrink-0 transition-transform duration-200",
              open && "rotate-90"
            )}
          />
          <span className="text-[var(--text-subtle)] text-xs uppercase tracking-wide">
            array[{value.length}]
          </span>
        </button>
        {open && (
          <ul className="mt-1 ml-4 border-l border-[var(--border-subtle)] pl-3 space-y-1">
            {value.map((item, i) => (
              <li key={i} className="flex gap-2">
                <span className="text-[var(--text-subtle)] select-none w-6 text-right shrink-0 font-medium">
                  {i}
                </span>
                <div className="min-w-0 flex-1">
                  <TreeNode
                    path={`${_path}[${i}]`}
                    value={item}
                    depth={depth + 1}
                    maxDepth={maxDepth}
                  />
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }

  const entries = Object.entries(value as Record<string, unknown>);
  if (depth >= maxDepth) {
    return (
      <span className="text-[var(--text-muted)]">
        {"{ "}
        {entries.length} keys … {"}"}
      </span>
    );
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-0.5 text-left text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
      >
        <ChevronRight
          className={cn(
            "h-4 w-4 shrink-0 transition-transform duration-200",
            open && "rotate-90"
          )}
        />
        <span className="text-[var(--text-subtle)] text-xs uppercase tracking-wide">
          object ({entries.length})
        </span>
      </button>
      {open && (
        <ul className="mt-1 ml-4 border-l border-[var(--border-subtle)] pl-3 space-y-1">
          {entries.map(([k, v]) => (
            <li key={k} className="min-w-0">
              <div className="flex flex-wrap gap-x-2 gap-y-0.5 items-start">
                <JsonKey name={k} />
                <div className="min-w-0 flex-1">
                  <TreeNode
                    path={`${_path}.${k}`}
                    value={v}
                    depth={depth + 1}
                    maxDepth={maxDepth}
                  />
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
