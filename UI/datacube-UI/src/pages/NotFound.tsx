import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { cn } from "../lib/cn.ts";

const NotFound = () => {
  const [isMounted, setIsMounted] = useState(false);
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    const timer = setTimeout(() => setIsMounted(true), 100);
    return () => clearTimeout(timer);
  }, []);

  const IconLink = ({
    to,
    icon,
    title,
    subtitle,
  }: {
    to: string;
    icon: React.ReactNode;
    title: string;
    subtitle: string;
  }) => (
    <Link
      to={to}
      className={cn(
        "group flex items-center rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 transition-all duration-300",
        "hover:-translate-y-0.5 hover:border-[var(--accent)]/35 hover:shadow-[var(--shadow-sm)]"
      )}
    >
      <div
        className={cn(
          "mr-4 flex h-12 w-12 shrink-0 items-center justify-center rounded-[var(--radius-sm)]",
          "bg-[var(--surface-0)] text-[var(--accent-bright)] transition-colors",
          "group-hover:bg-[var(--accent)] group-hover:text-white"
        )}
      >
        {icon}
      </div>
      <div>
        <p className="font-semibold text-[var(--text-primary)]">{title}</p>
        <p className="text-sm text-[var(--text-muted)]">{subtitle}</p>
      </div>
    </Link>
  );

  return (
    <>
      <main className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-[var(--surface-0)] font-[var(--font-sans)] text-[var(--text-primary)]">
        <div className="pointer-events-none absolute left-0 top-0 h-72 w-72 animate-pulse rounded-full bg-[var(--accent-soft)] blur-3xl" />
        <div
          className="pointer-events-none absolute bottom-0 right-0 h-96 w-96 rounded-full bg-[var(--info)]/10 blur-3xl"
          style={{ animation: "pulse 6s cubic-bezier(0.4, 0, 0.6, 1) infinite" }}
        />

        <div
          className={cn(
            "relative z-10 mx-4 w-full max-w-2xl rounded-2xl border border-[var(--border-subtle)] bg-[var(--surface-1)]/95 p-8 shadow-[var(--shadow-md)] backdrop-blur-lg transition-all duration-700 ease-out sm:p-10",
            isMounted ? "translate-y-0 opacity-100" : "translate-y-8 opacity-0"
          )}
        >
          <div className="mb-6 flex justify-center">
            <svg
              className="h-24 w-24 text-[var(--accent-bright)]"
              style={{ animation: "float 4s ease-in-out infinite" }}
              viewBox="0 0 64 64"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              aria-hidden
            >
              <path
                d="M48.752 34.331C53.31 35.533 56 36.69 56 38.002C56 39.313 53.31 40.47 48.752 41.671L37.333 44.5L32 56L26.667 44.5L15.248 41.671C10.69 40.47 8 39.313 8 38.002C8 36.69 10.69 35.533 15.248 34.331L26.667 31.5L32 20L37.333 31.5L48.752 34.331Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M32 8V20"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M22.05 22.05L26.667 26.667"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M8 32H20"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <circle cx="48" cy="16" r="4" fill="currentColor" fillOpacity="0.3" />
              <circle cx="12" cy="52" r="2" fill="currentColor" fillOpacity="0.3" />
            </svg>
          </div>

          <h1 className="mb-4 bg-gradient-to-r from-[var(--accent-bright)] to-[var(--info)] bg-clip-text text-center text-4xl font-bold tracking-tight text-transparent sm:text-5xl">
            404 — Page not found
          </h1>

          <p className="mx-auto mb-8 max-w-md text-center text-base leading-relaxed text-[var(--text-muted)] sm:text-lg">
            This URL doesn&apos;t match any route. Check the address or use the
            links below.
          </p>

          <div className="mb-10 flex flex-col items-stretch justify-center gap-4 sm:flex-row">
            <button
              type="button"
              onClick={() => window.history.back()}
              className={cn(
                "w-full rounded-[var(--radius-md)] bg-[var(--accent)] px-6 py-3 font-semibold text-white transition-transform hover:opacity-95 sm:w-auto",
                "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent-ring)]"
              )}
            >
              Go back
            </button>
            <Link
              to="/"
              className={cn(
                "w-full rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-6 py-3 text-center font-semibold text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-2)] sm:w-auto"
              )}
            >
              Home
            </Link>
          </div>

          <div className="space-y-4">
            <IconLink
              to="/api-docs"
              title="API reference"
              subtitle="Endpoint shapes and examples"
              icon={
                <svg
                  className="h-6 w-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  aria-hidden
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6.253v11.494m-9-5.747h18"
                  />
                </svg>
              }
            />
            {isAuthenticated ? (
              <>
                <IconLink
                  to="/dashboard/api-keys"
                  title="API keys"
                  subtitle="Tokens for automation"
                  icon={
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 7h3a5 5 0 015 5 5 5 0 01-5 5h-3m-6 0H6a5 5 0 01-5-5 5 5 0 015-5h3"
                      />
                    </svg>
                  }
                />
                <IconLink
                  to="/dashboard/billing"
                  title="Billing"
                  subtitle="Plan and invoices"
                  icon={
                    <svg
                      className="h-6 w-6"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                      />
                    </svg>
                  }
                />
              </>
            ) : null}
          </div>
        </div>
      </main>

      <style>
        {`
          @keyframes float {
            0% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
            100% { transform: translateY(0px); }
          }
          @keyframes pulse {
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </>
  );
};

export default NotFound;
