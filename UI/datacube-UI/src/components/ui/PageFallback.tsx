export function PageFallback() {
  return (
    <div
      className="flex min-h-[50vh] w-full items-center justify-center bg-[var(--surface-0)]"
      role="status"
      aria-label="Loading page"
    >
      <div className="h-9 w-9 animate-spin rounded-full border-2 border-[var(--border-subtle)] border-t-[var(--accent)]" />
    </div>
  );
}
