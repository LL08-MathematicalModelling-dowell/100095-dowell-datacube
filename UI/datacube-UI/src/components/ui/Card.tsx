import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

export function Card({
  children,
  className,
  title,
  subtitle,
  action,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <section
      className={cn(
        "rounded-[var(--radius-lg)] border bg-[var(--surface-1)] shadow-[var(--shadow-sm)] transition-colors duration-200",
        "border-[var(--border-subtle)]",
        className
      )}
    >
      {(title || subtitle || action) && (
        <header className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between border-b border-[var(--border-subtle)] px-5 py-4">
          <div>
            {title && (
              <h2 className="text-lg font-semibold tracking-tight text-[var(--text-primary)]">
                {title}
              </h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-sm text-[var(--text-muted)]">{subtitle}</p>
            )}
          </div>
          {action && <div className="shrink-0">{action}</div>}
        </header>
      )}
      <div className={title || subtitle || action ? "p-5" : "p-5"}>{children}</div>
    </section>
  );
}

export function PageHeader({
  title,
  description,
  breadcrumbs,
  action,
}: {
  title: string;
  description?: string;
  breadcrumbs?: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {breadcrumbs && (
          <div className="mb-2 text-sm text-[var(--text-muted)]">{breadcrumbs}</div>
        )}
        <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)]">
          {title}
        </h1>
        {description && (
          <p className="mt-2 max-w-2xl text-[var(--text-muted)]">{description}</p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}
