import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Database } from "lucide-react";
import { cn } from "../../lib/cn";

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[var(--surface-0)] font-[var(--font-sans)] text-[var(--text-primary)]">
      <div className="mx-auto grid min-h-screen lg:grid-cols-2">
        {/* Brand column — desktop */}
        <aside
          className={cn(
            "relative hidden flex-col justify-between overflow-hidden border-r border-[var(--border-subtle)] bg-[var(--surface-1)] p-12 xl:p-16",
            "lg:flex"
          )}
        >
          <div
            className="pointer-events-none absolute inset-0 opacity-[0.35]"
            style={{
              background:
                "radial-gradient(ellipse 70% 50% at 20% 20%, var(--accent-soft), transparent), radial-gradient(ellipse 50% 40% at 80% 60%, rgba(56, 189, 248, 0.08), transparent)",
            }}
          />
          <div className="relative">
            <Link to="/" className="inline-flex items-center gap-3 font-semibold text-[var(--text-primary)]">
              <span className="flex h-11 w-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--accent)]/25 bg-[var(--accent-soft)]">
                <Database className="h-6 w-6 text-[var(--accent-bright)]" />
              </span>
              Datacube
            </Link>
            <h2 className="mt-14 max-w-md text-3xl font-bold leading-tight tracking-tight xl:text-4xl">
              Secure access to your data API
            </h2>
            <p className="mt-4 max-w-sm text-[var(--text-muted)]">
              Email & password with OTP verification, or single sign-on with
              Google and GitHub using PKCE — matching the production Django
              backend.
            </p>
          </div>
          <ul className="relative mt-12 space-y-3 text-sm text-[var(--text-muted)]">
            {[
              "JWT sessions with refresh",
              "API keys after verification",
              "Role-aware developer & analyst flows",
            ].map((line) => (
              <li key={line} className="flex gap-2">
                <span className="text-[var(--accent-bright)]">✓</span>
                {line}
              </li>
            ))}
          </ul>
        </aside>

        {/* Form column */}
        <div className="flex flex-col justify-center px-4 py-10 sm:px-8 lg:px-12 xl:px-20">
          {/* Mobile brand */}
          <div className="mb-8 flex items-center justify-between gap-4 lg:hidden">
            <Link to="/" className="inline-flex items-center gap-2 font-semibold">
              <span className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)]">
                <Database className="h-5 w-5 text-[var(--accent-bright)]" />
              </span>
              Datacube
            </Link>
            <Link
              to="/api-docs"
              className="text-xs font-medium text-[var(--accent-bright)] hover:underline"
            >
              API docs
            </Link>
          </div>

          <div className="mx-auto w-full max-w-md">
            <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
            {subtitle ? (
              <div className="mt-2 text-sm text-[var(--text-muted)]">{subtitle}</div>
            ) : null}
            <div className="mt-8">{children}</div>
            {footer ? <div className="mt-8">{footer}</div> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
