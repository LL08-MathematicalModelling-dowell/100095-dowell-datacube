import { AlertCircle, RefreshCw } from "lucide-react";
import { cn } from "../../lib/cn";

export function RefreshButton({
  onClick,
  isRefreshing = false,
  label = "Refresh",
  size = "sm",
}: {
  onClick: () => void;
  isRefreshing?: boolean;
  label?: string;
  size?: "sm" | "md";
}) {
  const compact = size === "sm";
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={isRefreshing}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-[var(--radius-md)] border border-[var(--border-subtle)] font-medium text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] disabled:opacity-50",
        compact ? "px-2.5 py-1.5 text-xs" : "px-3 py-2 text-sm"
      )}
      aria-label={label}
    >
      <RefreshCw
        className={cn(compact ? "h-3.5 w-3.5" : "h-4 w-4", isRefreshing && "animate-spin")}
      />
      {label}
    </button>
  );
}

export function QueryErrorBlock({
  message = "Failed to load data.",
  onRetry,
  isRefreshing = false,
}: {
  message?: string;
  onRetry: () => void;
  isRefreshing?: boolean;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-8 text-center">
      <AlertCircle className="h-8 w-8 text-[var(--danger)]" />
      <p className="text-sm text-[var(--text-muted)]">{message}</p>
      <button
        type="button"
        onClick={onRetry}
        disabled={isRefreshing}
        className="inline-flex items-center gap-2 text-sm font-medium text-[var(--accent-bright)] hover:underline disabled:opacity-50"
      >
        <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
        Retry
      </button>
    </div>
  );
}
