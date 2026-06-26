import { Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

function formatRemaining(expiresAt: string | null): string | null {
  if (!expiresAt) return null;
  const expires = new Date(expiresAt).getTime();
  if (Number.isNaN(expires)) return null;
  const diffMs = expires - Date.now();
  if (diffMs <= 0) return "expired";
  const mins = Math.floor(diffMs / 60000);
  const hours = Math.floor(mins / 60);
  const remMins = mins % 60;
  if (hours > 0) return `${hours}h ${remMins}m`;
  return `${remMins}m`;
}

export function PlaygroundBanner({
  expiresAt,
}: {
  expiresAt: string | null;
}) {
  const [remaining, setRemaining] = useState<string | null>(() =>
    formatRemaining(expiresAt)
  );
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setRemaining(formatRemaining(expiresAt));
    const id = window.setInterval(() => {
      setRemaining(formatRemaining(expiresAt));
    }, 60000);
    return () => window.clearInterval(id);
  }, [expiresAt]);

  if (dismissed) return null;

  return (
    <div className="flex items-center gap-3 border-b border-[var(--accent)]/25 bg-[var(--accent-soft)] px-4 py-2 text-sm text-[var(--text-primary)] sm:px-6">
      <Sparkles className="h-4 w-4 shrink-0 text-[var(--accent-bright)]" />
      <p className="min-w-0 flex-1">
        <span className="font-semibold">Playground session</span>
        {remaining ? (
          <span className="text-[var(--text-muted)]">
            {" "}
            — {remaining === "expired" ? "expired" : `expires in ${remaining}`}.
          </span>
        ) : (
          <span className="text-[var(--text-muted)]"> — temporary sandbox.</span>
        )}{" "}
        <Link
          to="/register"
          className="font-medium text-[var(--accent-bright)] hover:underline"
        >
          Sign up to keep your data
        </Link>
      </p>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        className="shrink-0 rounded p-1 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
