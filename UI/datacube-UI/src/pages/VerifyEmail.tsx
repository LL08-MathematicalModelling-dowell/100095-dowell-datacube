import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { Mail } from "lucide-react";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { btnPrimaryCn, btnSecondaryCn, inputCn } from "../lib/uiClasses.ts";
import { cn } from "../lib/cn.ts";
import api from "../services/api.ts";
import useAuthStore from "../store/authStore.ts";
import { getApiErrorMessage } from "../lib/apiErrors.ts";

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const emailParam = searchParams.get("email")?.trim() || "";
  const [email, setEmail] = useState(emailParam);
  const [code, setCode] = useState("");
  const [cooldown, setCooldown] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (emailParam) setEmail(emailParam);
  }, [emailParam]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setInterval(() => setCooldown((c) => c - 1), 1000);
    return () => clearInterval(t);
  }, [cooldown]);

  const verifyMutation = useMutation({
    mutationFn: () =>
      api.post("/core/auth/otp/verify/", {
        email: email.trim(),
        code: code.trim(),
        purpose: "register",
      }) as Promise<{
        access: string;
        refresh: string;
        firstName: string;
      }>,
    onSuccess: (data) => {
      setError(null);
      setAuth(data.access, data.refresh, data.firstName);
      toast.success("Email verified — welcome!");
      navigate("/dashboard/overview", { replace: true });
    },
    onError: (err) => {
      setError(getApiErrorMessage(err));
    },
  });

  const resendMutation = useMutation({
    mutationFn: () =>
      api.post("/core/verify-email/resend/", { email: email.trim() }),
    onSuccess: () => {
      toast.success("If an account exists, a new code was sent.");
      setCooldown(60);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err));
    },
  });

  const requestAltMutation = useMutation({
    mutationFn: () =>
      api.post("/core/auth/otp/request/", {
        email: email.trim(),
        purpose: "register",
      }),
    onSuccess: () => {
      toast.success("If an account matches, check your inbox.");
      setCooldown(60);
    },
    onError: (err) => {
      toast.error(getApiErrorMessage(err));
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!email.trim()) {
      setError("Enter the email you registered with.");
      return;
    }
    if (!code.trim() || code.trim().length < 4) {
      setError("Enter the verification code from your email.");
      return;
    }
    verifyMutation.mutate();
  };

  return (
    <AuthShell
      title="Verify your email"
      subtitle={
        <>
          Enter the code we sent after registration. Codes expire after a short
          time — you can resend or request a new OTP.
        </>
      }
      footer={
        <p className="text-center text-sm text-[var(--text-muted)]">
          Wrong address?{" "}
          <Link to="/register" className="font-medium text-[var(--accent-bright)] hover:underline">
            Register again
          </Link>
        </p>
      }
    >
      <div className="mb-6 flex justify-center lg:hidden">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--accent-soft)] text-[var(--accent-bright)]">
          <Mail className="h-6 w-6" />
        </span>
      </div>

      {error ? (
        <div className="mb-6 rounded-[var(--radius-md)] border border-[var(--danger)]/40 bg-[var(--danger-soft)] px-3 py-2 text-sm text-[var(--danger)]">
          {error}
        </div>
      ) : null}

      <form onSubmit={onSubmit} className="space-y-4">
        <div>
          <label htmlFor="ve-email" className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            Email
          </label>
          <input
            id="ve-email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCn()}
            required
          />
        </div>
        <div>
          <label htmlFor="ve-code" className="mb-1 block text-xs font-medium text-[var(--text-muted)]">
            Verification code
          </label>
          <input
            id="ve-code"
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="6-digit code"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 12))}
            className={cn(inputCn(), "font-mono text-lg tracking-widest")}
            maxLength={12}
          />
        </div>
        <button
          type="submit"
          disabled={verifyMutation.isPending}
          className={btnPrimaryCn("w-full")}
        >
          {verifyMutation.isPending ? "Verifying…" : "Verify & continue"}
        </button>
      </form>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row">
        <button
          type="button"
          disabled={resendMutation.isPending || cooldown > 0}
          onClick={() => resendMutation.mutate()}
          className={cn(btnSecondaryCn("flex-1"), "text-sm")}
        >
          {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend verification email"}
        </button>
        <button
          type="button"
          disabled={requestAltMutation.isPending || cooldown > 0}
          onClick={() => requestAltMutation.mutate()}
          className={cn(btnSecondaryCn("flex-1"), "text-sm")}
        >
          Request OTP (register)
        </button>
      </div>

      <p className="mt-6 text-center text-sm text-[var(--text-muted)]">
        Already verified?{" "}
        <Link to="/login" className="font-medium text-[var(--accent-bright)] hover:underline">
          Sign in
        </Link>
      </p>
    </AuthShell>
  );
}
