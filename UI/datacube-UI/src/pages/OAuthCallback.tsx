import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { btnPrimaryCn } from "../lib/uiClasses.ts";
import { cn } from "../lib/cn.ts";
import useAuthStore from "../store/authStore.ts";
import {
  clearPkceSession,
  exchangeOAuthTokens,
  readPkceSession,
} from "../lib/oauthPkce.ts";
import { getApiErrorMessage } from "../lib/apiErrors.ts";

export default function OAuthCallbackPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let active = true;

    const providerErr = searchParams.get("error");
    const providerDesc = searchParams.get("error_description");
    if (providerErr) {
      setBusy(false);
      setError(
        providerDesc ||
          (providerErr === "access_denied"
            ? "Sign-in was cancelled."
            : `OAuth error: ${providerErr}`)
      );
      clearPkceSession();
      return;
    }

    const code = searchParams.get("code");
    const state = searchParams.get("state");
    if (!code || !state) {
      setBusy(false);
      setError("Missing authorization code. Return to login and try again.");
      clearPkceSession();
      return;
    }

    const session = readPkceSession();
    if (!session || session.state !== state) {
      setBusy(false);
      setError("Invalid or expired sign-in session. Please start again from login.");
      clearPkceSession();
      return;
    }

    void exchangeOAuthTokens(session.provider, code, session.verifier)
      .then((data) => {
        if (!active) return;
        clearPkceSession();
        setAuth(data.access, data.refresh, data.firstName);
        toast.success("Signed in");
        navigate("/dashboard/overview", { replace: true });
      })
      .catch((err) => {
        if (!active) return;
        clearPkceSession();
        setBusy(false);
        setError(getApiErrorMessage(err));
      });

    return () => {
      active = false;
    };
  }, [navigate, searchParams, setAuth]);

  return (
    <AuthShell
      title="Completing sign-in"
      subtitle="Securely exchanging the OAuth code with your Datacube backend."
    >
      {error ? (
        <div className="space-y-4">
          <div className="rounded-[var(--radius-md)] border border-[var(--danger)]/40 bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]">
            {error}
          </div>
          <Link
            to="/login"
            className={cn(btnPrimaryCn("inline-flex w-full justify-center"))}
          >
            Back to login
          </Link>
        </div>
      ) : busy ? (
        <div className="flex flex-col items-center gap-4 py-8">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-[var(--border-subtle)] border-t-[var(--accent)]" />
          <p className="text-center text-sm text-[var(--text-muted)]">
            Finishing OAuth sign-in…
          </p>
        </div>
      ) : null}
    </AuthShell>
  );
}
