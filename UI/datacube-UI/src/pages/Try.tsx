import { useMutation } from "@tanstack/react-query";
import { Clock, Database, Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { getApiErrorMessage } from "../lib/apiErrors.ts";
import { btnPrimaryCn } from "../lib/uiClasses.ts";
import api from "../services/api.ts";
import useAuthStore from "../store/authStore.ts";

const PG_SESSION_KEY = "pg_session";

type PlaygroundStartResponse = {
  access: string;
  refresh: string;
  firstName: string;
  lastName?: string;
  is_playground?: boolean;
  playground_session_id?: string;
  playground_expires_at?: string | null;
  reused_session?: boolean;
};

const PERKS = [
  "A fresh, isolated sandbox — just for you",
  "Pre-seeded demo_store database with sample data",
  "Full CRUD: create collections, insert & query docs",
];

export default function TryPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [errorMessage, setErrorMessage] = useState("");

  const mutation = useMutation({
    mutationFn: async () => {
      const sessionId = localStorage.getItem(PG_SESSION_KEY);
      return api.post(
        "/core/api/v2/playground/start/",
        sessionId ? { session_id: sessionId } : {},
        { withCredentials: true }
      ) as Promise<PlaygroundStartResponse>;
    },
    onSuccess: (data) => {
      if (data.playground_session_id) {
        localStorage.setItem(PG_SESSION_KEY, data.playground_session_id);
      }
      if (data.playground_expires_at) {
        localStorage.setItem("pg_expires_at", data.playground_expires_at);
      }
      setAuth(data.access, data.refresh, data.firstName);
      toast.success(
        data.reused_session
          ? "Welcome back to your playground session."
          : "Playground ready — explore with sample data."
      );
      navigate("/dashboard/overview");
    },
    onError: (err) => {
      setErrorMessage(getApiErrorMessage(err));
    },
  });

  return (
    <AuthShell
      title="Try Datacube"
      subtitle={
        <span>
          Launch a free, temporary playground — no signup required. You get your
          own isolated sandbox seeded with sample data.
        </span>
      }
      footer={
        <p className="text-center text-sm text-[var(--text-muted)]">
          Want to keep your data?{" "}
          <Link
            to="/register"
            className="font-medium text-[var(--accent-bright)] hover:underline"
          >
            Create a free account
          </Link>
        </p>
      }
    >
      <div className="space-y-6">
        <ul className="space-y-3 text-sm text-[var(--text-muted)]">
          {PERKS.map((line) => (
            <li key={line} className="flex items-start gap-2">
              <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[var(--accent-bright)]" />
              {line}
            </li>
          ))}
        </ul>

        <div className="flex items-start gap-2 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-2)] px-4 py-3 text-xs text-[var(--text-muted)]">
          <Clock className="mt-0.5 h-4 w-4 shrink-0 text-[var(--accent-bright)]" />
          <span>
            Playground sessions expire after a few hours and are automatically
            deleted. Limits: 1 database, 3 collections, 100 documents. API keys
            and file uploads are disabled.
          </span>
        </div>

        {errorMessage ? (
          <div className="rounded-[var(--radius-md)] border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {errorMessage}
          </div>
        ) : null}

        <button
          type="button"
          onClick={() => {
            setErrorMessage("");
            mutation.mutate();
          }}
          disabled={mutation.isPending}
          className={btnPrimaryCn("text-base shadow-[var(--shadow-glow-teal)]")}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              Preparing your sandbox…
            </>
          ) : (
            <>
              <Database className="h-5 w-5" />
              Launch playground
            </>
          )}
        </button>
      </div>
    </AuthShell>
  );
}
