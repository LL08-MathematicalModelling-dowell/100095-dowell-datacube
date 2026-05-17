import { useMutation } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { btnPrimaryCn } from "../lib/uiClasses.ts";
import { cn } from "../lib/cn.ts";
import api from "../services/api.ts";
import useAuthStore from "../store/authStore.ts";
import {
  clearPkceSession,
  getOAuthRedirectUri,
  readPkceSession,
} from "../lib/oauthPkce.ts";
import { getApiErrorMessage } from "../lib/apiErrors.ts";

export default function OAuthCallbackPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [searchParams] = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);
  const started = useRef(false);

  const exchangeMutation = useMutation({
    mutationFn: async (payload: {
      provider: "google" | "github";
      code: string;
      verifier: string;
    }) => {
      const path =
        payload.provider === "google"
          ? "/core/auth/oauth/google/"
          : "/core/auth/oauth/github/";
      return api.post(path, {
        code: payload.code,
        code_verifier: payload.verifier,
        redirect_uri: getOAuthRedirectUri(),
      }) as Promise<{
        access: string;
        refresh: string;
        firstName: string;
      }>;
    },
  });

  useEffect(() => {
    if (started.current) return;
    started.current = true;

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

    exchangeMutation.mutate(
      { provider: session.provider, code, verifier: session.verifier },
      {
        onSuccess: (data) => {
          clearPkceSession();
          setAuth(data.access, data.refresh, data.firstName);
          toast.success("Signed in");
          navigate("/dashboard/overview", { replace: true });
        },
        onError: (err) => {
          clearPkceSession();
          setBusy(false);
          setError(getApiErrorMessage(err));
        },
      }
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
