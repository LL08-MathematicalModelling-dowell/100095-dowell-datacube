import { motion } from "framer-motion";
import {
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Database,
  FileJson2,
  KeyRound,
  LayoutDashboard,
  Lock,
  Server,
  Shield,
} from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { btnPrimaryCn } from "../lib/uiClasses";
import useAuthStore from "../store/authStore";

const API_ORIGIN =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

const prefixRows = [
  {
    prefix: `${API_ORIGIN}/api/v2/`,
    title: "Data API",
    body: "Health, databases, collections, CRUD, GridFS files, imports.",
    icon: Database,
  },
  {
    prefix: `${API_ORIGIN}/core/`,
    title: "Auth & account",
    body: "Register, login, JWT refresh, profile, API keys, OAuth, OTP.",
    icon: KeyRound,
  },
  {
    prefix: `${API_ORIGIN}/analytics/api/v2/`,
    title: "Analytics",
    body: "Dashboard metrics, latency, errors — JWT only.",
    icon: LayoutDashboard,
  },
];

const roleRows = [
  {
    role: "developer",
    desc: "Full CRUD, files, and database management (default for most users).",
  },
  {
    role: "analyst",
    desc: "Read-only on CRUD, files, and list routes — no destructive writes.",
  },
  {
    role: "admin",
    desc: "Developer capabilities plus admin routes (e.g. prune fields, set roles).",
  },
];

const checklist = [
  "Store access + refresh tokens securely; refresh on expiry.",
  "Send Authorization: Bearer on data, analytics, and profile calls.",
  "Gate features on is_email_verified from login or profile.",
  "Hide write actions for analyst role in the UI.",
  "Use documents (not data) in CRUD POST bodies.",
];

export default function LandingPage() {
  const { isAuthenticated } = useAuthStore();

  return (
    <div className="overflow-x-hidden">
      {/* Hero */}
      <section className="relative border-b border-[var(--border-subtle)]">
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% -20%, var(--accent-soft), transparent), radial-gradient(ellipse 60% 40% at 100% 50%, rgba(56, 189, 248, 0.06), transparent)",
          }}
        />
        <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-28 text-center sm:px-6 sm:pb-24 sm:pt-32">
          <motion.p
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--accent-bright)]"
          >
            Mongo-backed REST API
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="mx-auto max-w-4xl text-4xl font-bold leading-tight tracking-tight text-[var(--text-primary)] sm:text-6xl md:text-7xl"
          >
            Ship data products with{" "}
            <span className="bg-gradient-to-r from-[var(--accent-bright)] to-[var(--info)] bg-clip-text text-transparent">
              one API
            </span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mx-auto mt-6 max-w-2xl text-lg text-[var(--text-muted)] sm:text-xl"
          >
            Logical databases, JSON documents, GridFS files, and analytics —
            authenticated with JWT or API keys, aligned with the Datacube
            backend you run in production.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="mt-10 flex flex-col items-stretch justify-center gap-3 sm:flex-row sm:items-center"
          >
            {isAuthenticated ? (
              <Link
                to="/dashboard/overview"
                className={cn(
                  btnPrimaryCn("w-full px-8 py-4 text-base sm:w-auto"),
                  "inline-flex items-center justify-center gap-2 shadow-[var(--shadow-glow-teal)]"
                )}
              >
                <LayoutDashboard className="h-5 w-5" />
                Go to dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/try"
                  className={cn(
                    btnPrimaryCn("w-full px-8 py-4 text-base sm:w-auto"),
                    "shadow-[var(--shadow-glow-teal)]"
                  )}
                >
                  Try playground
                </Link>
                <Link
                  to="/register"
                  className="inline-flex w-full items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-8 py-4 text-base font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--surface-2)] sm:w-auto"
                >
                  Create account
                </Link>
                <Link
                  to="/login"
                  className="inline-flex w-full items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-8 py-4 text-base font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--surface-2)] sm:w-auto"
                >
                  Sign in
                </Link>
              </>
            )}
            <Link
              to="/api-docs"
              className="inline-flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-8 py-4 text-base font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--surface-2)] sm:w-auto"
            >
              <BookOpen className="h-5 w-5 text-[var(--accent-bright)]" />
              API reference
            </Link>
          </motion.div>
          <p className="mt-8 font-mono text-xs text-[var(--text-subtle)] sm:text-sm">
            Base URL ·{" "}
            <span className="text-[var(--accent-bright)]">{API_ORIGIN}</span>
          </p>
        </div>
      </section>

      {/* API surface */}
      <section className="border-b border-[var(--border-subtle)] bg-[var(--surface-1)]/30 py-16 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-2xl font-bold text-[var(--text-primary)] sm:text-3xl">
              Three URL namespaces
            </h2>
            <p className="mt-3 text-[var(--text-muted)]">
              Matches the Django routes in production: data, auth, and
              analytics are versioned and documented together.
            </p>
          </div>
          <div className="mt-12 grid gap-4 md:grid-cols-3">
            {prefixRows.map((row, i) => (
              <motion.article
                key={row.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.06 }}
                className="flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 shadow-[var(--shadow-sm)]"
              >
                <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)] text-[var(--accent-bright)]">
                  <row.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--text-primary)]">
                  {row.title}
                </h3>
                <p className="mt-2 flex-1 text-sm text-[var(--text-muted)]">
                  {row.body}
                </p>
                <p className="mt-4 break-all font-mono text-[11px] leading-snug text-[var(--text-subtle)] sm:text-xs">
                  {row.prefix}
                </p>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      {/* Pillars */}
      <section className="py-16 sm:py-20">
        <div className="mx-auto grid max-w-6xl gap-10 px-4 sm:px-6 md:grid-cols-3 md:gap-8">
          {[
            {
              icon: Shield,
              title: "Verified access",
              text: "JWT and API keys resolve to Mongo users. Email verification is required before data and analytics calls succeed.",
            },
            {
              icon: Server,
              title: "Role-aware UI",
              text: "Developers manage schemas and writes; analysts stay read-only; admins get operational tools — mirror that in your product.",
            },
            {
              icon: FileJson2,
              title: "Documents & files",
              text: "CRUD uses a single /api/v2/crud/ contract with `documents` on insert. GridFS uploads share the same auth layer.",
            },
          ].map((item, i) => (
            <motion.div
              key={item.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
              className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)]/60 p-6"
            >
              <item.icon className="h-8 w-8 text-[var(--accent-bright)]" />
              <h3 className="mt-4 text-lg font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm text-[var(--text-muted)]">{item.text}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Roles + checklist */}
      <section className="border-y border-[var(--border-subtle)] bg-[var(--surface-1)]/25 py-16 sm:py-20">
        <div className="mx-auto grid max-w-6xl gap-12 px-4 sm:px-6 lg:grid-cols-2 lg:gap-16">
          <div>
            <div className="flex items-center gap-2 text-[var(--accent-bright)]">
              <Lock className="h-5 w-5" />
              <h2 className="text-xl font-bold sm:text-2xl">Roles</h2>
            </div>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              Returned on login and profile; use them to show or hide controls.
            </p>
            <ul className="mt-6 space-y-4">
              {roleRows.map((r) => (
                <li
                  key={r.role}
                  className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)]/80 p-4"
                >
                  <span className="font-mono text-sm font-semibold text-[var(--accent-bright)]">
                    {r.role}
                  </span>
                  <p className="mt-1 text-sm text-[var(--text-muted)]">{r.desc}</p>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <div className="flex items-center gap-2 text-[var(--accent-bright)]">
              <CheckCircle2 className="h-5 w-5" />
              <h2 className="text-xl font-bold sm:text-2xl">
                Integration checklist
              </h2>
            </div>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              Pulled from the backend frontend guide — safe defaults for SPAs.
            </p>
            <ul className="mt-6 space-y-3">
              {checklist.map((line) => (
                <li
                  key={line}
                  className="flex gap-3 text-sm text-[var(--text-primary)]"
                >
                  <span className="mt-0.5 text-[var(--accent-bright)]">✓</span>
                  <span className="text-[var(--text-muted)]">{line}</span>
                </li>
              ))}
            </ul>
            <Link
              to="/api-docs"
              className="mt-8 inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent-bright)] hover:underline"
            >
              Full endpoint list
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto max-w-3xl px-4 text-center sm:px-6">
          <h2 className="text-2xl font-bold sm:text-4xl">
            Ready to wire your UI to the API?
          </h2>
          <p className="mt-4 text-[var(--text-muted)]">
            The in-app reference is generated from the same routes as this
            deployment. Point <code className="rounded bg-[var(--surface-2)] px-1.5 py-0.5 font-mono text-xs">VITE_API_BASE</code>{" "}
            at your backend and start building.
          </p>
          <motion.div className="mt-10 flex flex-col gap-3 sm:flex-row sm:justify-center">
            {isAuthenticated ? (
              <Link
                to="/dashboard/overview"
                className={cn(
                  btnPrimaryCn(
                    "inline-flex items-center justify-center gap-2 px-10 py-4 sm:w-auto"
                  )
                )}
              >
                <LayoutDashboard className="h-5 w-5" />
                Open dashboard
              </Link>
            ) : (
              <Link to="/register" className={btnPrimaryCn("px-10 py-4 sm:w-auto")}>
                Get started
              </Link>
            )}
            <Link
              to="/api-docs"
              className="inline-flex items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-subtle)] px-10 py-4 font-semibold text-[var(--text-primary)] hover:bg-[var(--surface-1)]"
            >
              Browse docs
            </Link>
          </motion.div>
        </div>
      </section>

      <footer className="border-t border-[var(--border-subtle)] py-10 text-center text-sm text-[var(--text-muted)]">
        <p>© 2026 Datacube · API-first data platform</p>
        <motion.div className="mt-4 flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <Link to="/api-docs" className="hover:text-[var(--accent-bright)]">
            Documentation
          </Link>
          {isAuthenticated ? (
            <Link
              to="/dashboard/overview"
              className="hover:text-[var(--accent-bright)]"
            >
              Dashboard
            </Link>
          ) : (
            <>
              <Link to="/login" className="hover:text-[var(--accent-bright)]">
                Sign in
              </Link>
              <Link to="/register" className="hover:text-[var(--accent-bright)]">
                Register
              </Link>
            </>
          )}
        </motion.div>
      </footer>
    </div>
  );
}
