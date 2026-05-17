import { useMutation } from "@tanstack/react-query";
import { Github } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { getApiErrorMessage, isEmailUnverifiedResponse } from "../lib/apiErrors.ts";
import { startOAuthRedirect } from "../lib/oauthPkce.ts";
import { btnPrimaryCn, btnSecondaryCn, inputCn } from "../lib/uiClasses.ts";
import { cn } from "../lib/cn.ts";
import api from "../services/api.ts";
import useAuthStore from "../store/authStore.ts";

interface FormData {
  email: string;
  password: string;
}

const googleIcon = (
  <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden>
    <path
      fill="currentColor"
      d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
    />
    <path
      fill="currentColor"
      d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
    />
    <path
      fill="currentColor"
      d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
    />
    <path
      fill="currentColor"
      d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
    />
  </svg>
);

const hasGoogle = Boolean(import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID);
const hasGithub = Boolean(import.meta.env.VITE_GITHUB_OAUTH_CLIENT_ID);

export default function LoginPage() {
  const navigate = useNavigate();
  const { register, handleSubmit, getValues } = useForm<FormData>();
  const { setAuth } = useAuthStore();
  const [errorMessage, setErrorMessage] = useState("");
  const [oauthBusy, setOauthBusy] = useState<"google" | "github" | null>(null);

  const mutation = useMutation({
    mutationFn: (data: FormData) => api.post("/core/login/", data),
    onSuccess: (response: {
      access: string;
      refresh: string;
      firstName: string;
    }) => {
      setAuth(response.access, response.refresh, response.firstName);
      navigate("/dashboard/overview");
    },
    onError: (error: unknown) => {
      const email = getValues("email");
      if (isEmailUnverifiedResponse(error) && email) {
        toast.error("Verify your email to continue.");
        navigate(`/verify-email?email=${encodeURIComponent(email.trim())}`, {
          replace: true,
        });
        return;
      }
      setErrorMessage(getApiErrorMessage(error));
    },
  });

  const oauthStart = async (provider: "google" | "github") => {
    setOauthBusy(provider);
    try {
      await startOAuthRedirect(provider);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Could not start sign-in");
      setOauthBusy(null);
    }
  };

  return (
    <AuthShell
      title="Sign in"
      subtitle="Use your email and password, or continue with Google or GitHub (PKCE)."
      footer={
        <p className="text-center text-sm text-[var(--text-muted)]">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="font-medium text-[var(--accent-bright)] hover:underline">
            Register
          </Link>
        </p>
      }
    >
      {(hasGoogle || hasGithub) && (
        <div className="mb-8 space-y-3">
          {hasGoogle && (
            <button
              type="button"
              disabled={oauthBusy !== null}
              onClick={() => void oauthStart("google")}
              className={cn(
                btnSecondaryCn("flex h-12 w-full items-center justify-center gap-3 font-medium"),
                "border-[var(--border-subtle)] bg-[var(--surface-1)]"
              )}
            >
              {oauthBusy === "google" ? (
                <span className="text-sm">Redirecting…</span>
              ) : (
                <>
                  <span className="text-[var(--text-muted)]">{googleIcon}</span>
                  Continue with Google
                </>
              )}
            </button>
          )}
          {hasGithub && (
            <button
              type="button"
              disabled={oauthBusy !== null}
              onClick={() => void oauthStart("github")}
              className={cn(
                btnSecondaryCn("flex h-12 w-full items-center justify-center gap-3 font-medium"),
                "border-[var(--border-subtle)] bg-[var(--surface-1)]"
              )}
            >
              {oauthBusy === "github" ? (
                <span className="text-sm">Redirecting…</span>
              ) : (
                <>
                  <Github className="h-5 w-5" />
                  Continue with GitHub
                </>
              )}
            </button>
          )}
          <div className="relative py-2 text-center text-xs text-[var(--text-subtle)]">
            <span className="bg-[var(--surface-0)] px-2">or use email</span>
            <div className="absolute left-0 right-0 top-1/2 -z-10 h-px bg-[var(--border-subtle)]" />
          </div>
        </div>
      )}

      <form
        onSubmit={handleSubmit((data) => {
          setErrorMessage("");
          mutation.mutate(data);
        })}
        className="space-y-4"
      >
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            Email
          </label>
          <input
            {...register("email", { required: true })}
            type="email"
            autoComplete="email"
            className={inputCn()}
          />
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            Password
          </label>
          <input
            {...register("password", { required: true })}
            type="password"
            autoComplete="current-password"
            className={inputCn()}
          />
        </div>

        {(mutation.isError || errorMessage) && (
          <div className="rounded-[var(--radius-md)] border border-[var(--danger)]/40 bg-[var(--danger-soft)] px-3 py-2 text-center text-sm text-[var(--danger)]">
            {errorMessage || "Sign-in failed."}
          </div>
        )}

        <button
          type="submit"
          disabled={mutation.isPending || oauthBusy !== null}
          className={btnPrimaryCn("w-full")}
        >
          {mutation.isPending ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="mt-6 flex flex-col gap-2 text-center text-sm text-[var(--text-muted)] sm:flex-row sm:justify-between">
        <Link to="/forgot-password" className="hover:text-[var(--accent-bright)] hover:underline">
          Forgot password?
        </Link>
        <Link to="/verify-email" className="hover:text-[var(--accent-bright)] hover:underline">
          Verify email / OTP
        </Link>
      </div>
    </AuthShell>
  );
}
