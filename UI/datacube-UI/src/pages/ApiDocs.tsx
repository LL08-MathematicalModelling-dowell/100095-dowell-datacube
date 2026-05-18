import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { Link } from "react-router-dom";
import { CodeSampleTabs } from "../components/docs/CodeSampleTabs.tsx";
import { apiDocs, type ApiGroup } from "../data/apiReference";
import type { AuthMode } from "../lib/apiSamples";
import { cn } from "../lib/cn";
import useAuthStore from "../store/authStore";

const API_ORIGIN =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

function generateId(text: string): string {
  return text
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  const onCopy = useCallback(() => {
    void navigator.clipboard.writeText(text).then(
      () => {
        setCopied(true);
        toast.success("Copied");
        setTimeout(() => setCopied(false), 1800);
      },
      () => toast.error("Copy failed")
    );
  }, [text]);

  return (
    <button
      type="button"
      onClick={onCopy}
      className="absolute right-2 top-2 rounded-[var(--radius-sm)] bg-[var(--surface-2)] p-1.5 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-elevated)] hover:text-[var(--text-primary)]"
      aria-label="Copy"
    >
      {copied ? (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          className="text-[var(--accent-bright)]"
        >
          <path d="M20 6 9 17l-5-5" />
        </svg>
      ) : (
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        >
          <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
          <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
        </svg>
      )}
    </button>
  );
}

function MethodBadge({ method }: { method: string }) {
  type Verb = "GET" | "POST" | "PUT" | "DELETE" | "PATCH";
  const verb = method.split(" ")[0].toUpperCase() as Verb;
  const map: Record<string, string> = {
    GET: "bg-[var(--verb-get)] text-[var(--verb-get-text)]",
    POST: "bg-[var(--verb-post)] text-[var(--verb-post-text)]",
    PUT: "bg-[var(--verb-put)] text-[var(--verb-put-text)]",
    DELETE: "bg-[var(--verb-delete)] text-[var(--verb-delete-text)]",
    PATCH: "bg-[var(--verb-patch)] text-[var(--verb-patch-text)]",
  };
  const cls = map[verb] || "bg-[var(--surface-2)] text-[var(--text-muted)]";
  return (
    <span
      className={cn(
        "shrink-0 rounded-[var(--radius-sm)] px-2 py-1 text-xs font-bold",
        cls
      )}
    >
      {verb}
    </span>
  );
}

function CodeBlock({ code }: { code: string | undefined | null }) {
  if (!code) return null;
  return (
    <div className="relative mt-2">
      <pre className="max-h-[360px] overflow-auto rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 text-xs leading-relaxed text-[var(--text-primary)] sm:text-sm">
        <code className="break-words">{code}</code>
      </pre>
      <CopyButton text={code} />
    </div>
  );
}

function AuthBlock({ group }: { group: ApiGroup }) {
  if (!group.auth_header && !group.how_to_get_key) return null;
  return (
    <div className="mt-6 rounded-[var(--radius-md)] border border-[var(--info)]/25 bg-[var(--surface-0)]/90 p-4 sm:p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide text-[var(--info)]">
        Authentication
      </h3>
      {group.auth_header ? (
        <div className="mt-3">
          <p className="text-xs font-medium text-[var(--text-muted)]">
            Header example
          </p>
          <CodeBlock code={group.auth_header} />
        </div>
      ) : null}
      {group.how_to_get_key ? (
        <p className="mt-4 text-sm leading-relaxed text-[var(--text-muted)]">
          {group.how_to_get_key}
        </p>
      ) : null}
    </div>
  );
}

export default function ApiDocsPage() {
  const { isAuthenticated } = useAuthStore();
  const initialId =
    apiDocs.length > 0 ? generateId(apiDocs[0].group) : "";
  const [activeId, setActiveId] = useState(initialId);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const groupRefs = useRef<Record<string, HTMLElement | null>>({});

  const navIds = useMemo(
    () => apiDocs.map((g) => ({ id: generateId(g.group), label: g.group })),
    []
  );

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (
            entry.isIntersecting &&
            entry.boundingClientRect.top < window.innerHeight * 0.45
          ) {
            setActiveId(entry.target.id);
          }
        });
      },
      { rootMargin: "-40% 0px -45% 0px", threshold: 0 }
    );

    navIds.forEach(({ id }) => {
      const el = groupRefs.current[id];
      if (el) obs.observe(el);
    });

    return () => obs.disconnect();
  }, [navIds]);

  const scrollToSection = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setMobileNavOpen(false);
  };

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-[var(--surface-0)]">
      <style>{`html { scroll-behavior: smooth; }`}</style>

      {/* Mobile section picker */}
      <div className="sticky top-0 z-20 border-b border-[var(--border-subtle)] bg-[var(--surface-1)]/95 px-4 py-3 backdrop-blur-md lg:hidden">
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-4 py-3 text-left text-sm font-medium text-[var(--text-primary)]"
          onClick={() => setMobileNavOpen((o) => !o)}
          aria-expanded={mobileNavOpen}
        >
          <span className="line-clamp-2 pr-2">
            {navIds.find((n) => n.id === activeId)?.label ?? "Jump to section"}
          </span>
          <span className="text-[var(--accent-bright)]" aria-hidden>
            {mobileNavOpen ? "▲" : "▼"}
          </span>
        </button>
        {mobileNavOpen ? (
          <ul className="mt-2 max-h-[50vh] overflow-y-auto rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] py-2 shadow-[var(--shadow-md)]">
            {navIds.map(({ id, label }) => (
              <li key={id}>
                <button
                  type="button"
                  className={cn(
                    "w-full px-4 py-3 text-left text-sm transition-colors",
                    id === activeId
                      ? "bg-[var(--accent-soft)] font-semibold text-[var(--accent-bright)]"
                      : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]"
                  )}
                  onClick={() => scrollToSection(id)}
                >
                  {label}
                </button>
              </li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="mx-auto flex max-w-[1400px]">
        {/* Desktop sidebar */}
        <aside className="sticky top-[3.5rem] hidden h-[calc(100vh-3.5rem)] w-72 shrink-0 self-start overflow-y-auto border-r border-[var(--border-subtle)] py-8 pl-6 pr-4 lg:block xl:w-80">
          <p className="text-xs font-semibold uppercase tracking-widest text-[var(--text-subtle)]">
            Contents
          </p>
          <nav className="mt-4 space-y-1">
            {navIds.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => scrollToSection(id)}
                className={cn(
                  "w-full rounded-[var(--radius-md)] px-3 py-2.5 text-left text-sm transition-colors",
                  id === activeId
                    ? "bg-[var(--accent-soft)] font-medium text-[var(--accent-bright)]"
                    : "text-[var(--text-muted)] hover:bg-[var(--surface-1)] hover:text-[var(--text-primary)]"
                )}
              >
                {label.replace(/ \(`[^`]+`\)/, "")}
              </button>
            ))}
          </nav>
          <div className="mt-8 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 text-xs text-[var(--text-muted)]">
            <p className="font-semibold text-[var(--text-primary)]">
              Official guide
            </p>
            <p className="mt-2">
              Integration endpoints only. Full platform reference (auth UI flows, analytics, admin):{" "}
              <code className="text-[var(--accent-bright)]">datacube_documentation.md</code> in the repo root.
            </p>
            <Link
              to={isAuthenticated ? "/dashboard/overview" : "/register"}
              className="mt-3 inline-block font-medium text-[var(--accent-bright)] hover:underline"
            >
              {isAuthenticated ? "Go to dashboard →" : "Create account →"}
            </Link>
          </div>
        </aside>

        <div className="min-w-0 flex-1 px-4 py-8 sm:px-8 lg:py-10 lg:pl-10 lg:pr-12">
          <header className="max-w-3xl border-b border-[var(--border-subtle)] pb-10">
            <h1 className="text-3xl font-bold tracking-tight text-[var(--text-primary)] sm:text-4xl">
              API reference
            </h1>
            <p className="mt-4 text-base text-[var(--text-muted)] sm:text-lg">
              REST reference for <strong className="font-medium text-[var(--text-primary)]">developers</strong>{" "}
              integrating with Datacube: authentication, data CRUD, and files. Each operation includes
              copy-paste samples in cURL, Python, TypeScript, and JavaScript. Mongo ObjectIds are
              24-character hex strings; trailing slashes are optional on paths.
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4">
                <p className="text-xs font-semibold text-[var(--text-subtle)]">
                  Your app uses
                </p>
                <p className="mt-2 break-all font-mono text-sm text-[var(--accent-bright)]">
                  {API_ORIGIN}
                </p>
              </div>
              <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-4 text-sm text-[var(--text-muted)]">
                <p>
                  <strong className="text-[var(--text-primary)]">Data:</strong>{" "}
                  <code className="font-mono text-xs">/api/v2/</code>
                </p>
                <p className="mt-2">
                  <strong className="text-[var(--text-primary)]">Auth:</strong>{" "}
                  <code className="font-mono text-xs">/core/</code>
                </p>
                <p className="mt-2 text-[var(--text-subtle)]">
                  Dashboard analytics (<code className="font-mono text-xs">/analytics/api/v2/</code>) are
                  internal to the SPA — see full docs.
                </p>
              </div>
            </div>
          </header>

          <div className="max-w-3xl space-y-16 pt-12">
            {apiDocs.map((group) => {
              const id = generateId(group.group);
              return (
                <section
                  key={group.group}
                  id={id}
                  ref={(el) => {
                    groupRefs.current[id] = el;
                  }}
                  className="scroll-mt-24"
                >
                  <h2 className="text-2xl font-bold text-[var(--text-primary)]">
                    {group.group}
                  </h2>
                  <p className="mt-3 text-[var(--text-muted)]">
                    {group.description}
                  </p>
                  <AuthBlock group={group} />

                  <div className="mt-10 space-y-10">
                    {group.endpoints.map((endpoint) => (
                      <article
                        key={`${group.group}-${endpoint.name}`}
                        className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)]/80 p-5 shadow-[var(--shadow-sm)] sm:p-6"
                      >
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                          <div>
                            <h3 className="text-lg font-semibold text-[var(--accent-bright)]">
                              {endpoint.name}
                            </h3>
                            {endpoint.description ? (
                              <p className="mt-1 text-sm text-[var(--text-muted)]">
                                {endpoint.description}
                              </p>
                            ) : null}
                          </div>
                          {endpoint.auth_required ? (
                            <span className="shrink-0 rounded-full border border-[var(--border-subtle)] bg-[var(--surface-0)] px-3 py-1 text-xs font-medium text-[var(--text-muted)]">
                              {endpoint.auth_required}
                            </span>
                          ) : null}
                        </div>

                        <p className="mt-4 font-mono text-xs break-all text-[var(--text-primary)] sm:text-sm">
                          {endpoint.url}
                        </p>

                        <div className="mt-6 space-y-6">
                          {endpoint.methods.map((method, idx) => {
                            const authMode: AuthMode =
                              method.auth_mode ??
                              endpoint.auth_mode ??
                              group.default_auth_mode ??
                              "bearer";
                            return (
                            <div
                              key={`${method.method}-${idx}`}
                              className={
                                idx > 0
                                  ? "border-t border-[var(--border-subtle)] pt-6"
                                  : ""
                              }
                            >
                              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
                                <MethodBadge method={method.method} />
                                <div className="min-w-0 flex-1">
                                  <span className="font-mono text-xs text-[var(--text-muted)] sm:text-sm">
                                    {endpoint.url}
                                  </span>
                                  {method.method.includes("(") ? (
                                    <p className="mt-1 text-xs text-[var(--text-subtle)]">
                                      {(() => {
                                        const m = method.method.match(
                                          /\(([^)]+)\)/
                                        );
                                        return m ? m[1] : null;
                                      })()}
                                    </p>
                                  ) : null}
                                </div>
                              </div>
                              {method.params ? (
                                <div className="mt-4">
                                  <h4 className="text-sm font-medium text-[var(--text-primary)]">
                                    Query
                                  </h4>
                                  <CodeBlock code={method.params} />
                                </div>
                              ) : null}
                              {method.body ? (
                                <div className="mt-4">
                                  <h4 className="text-sm font-medium text-[var(--text-primary)]">
                                    Body
                                  </h4>
                                  <CodeBlock code={method.body} />
                                </div>
                              ) : null}
                              <CodeSampleTabs
                                baseUrl={API_ORIGIN}
                                method={method.method}
                                path={endpoint.url}
                                authMode={authMode}
                                query={method.params}
                                body={method.body}
                                multipart={method.multipart}
                              />
                              <div className="mt-4">
                                <h4 className="text-sm font-medium text-[var(--text-primary)]">
                                  Example response
                                </h4>
                                <CodeBlock code={method.response} />
                              </div>
                            </div>
                            );
                          })}
                        </div>

                        {endpoint.notes ? (
                          <div className="mt-6 rounded-[var(--radius-md)] border border-[var(--warning)]/35 bg-[var(--warning)]/8 p-4 text-sm text-[var(--text-muted)]">
                            <strong className="text-[var(--text-primary)]">
                              Note:{" "}
                            </strong>
                            {endpoint.notes}
                          </div>
                        ) : null}
                      </article>
                    ))}
                  </div>
                </section>
              );
            })}
          </div>

          <footer className="mt-20 max-w-3xl border-t border-[var(--border-subtle)] pt-10 text-sm text-[var(--text-muted)]">
            <p>
              Analyst role: safe HTTP methods only on CRUD/files. Developers
              and admins may write. Admin-only routes include field pruning and
              role assignment.
            </p>
            <Link
              to="/"
              className="mt-4 inline-block font-medium text-[var(--accent-bright)] hover:underline"
            >
              ← Back to home
            </Link>
          </footer>
        </div>
      </div>
    </div>
  );
}
