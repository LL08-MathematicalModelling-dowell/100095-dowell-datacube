import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import { btnPrimaryCn, inputCn } from "../lib/uiClasses.ts";
import api from "../services/api.ts";
import { getApiErrorMessage } from "../lib/apiErrors.ts";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);

  const mutation = useMutation({
    mutationFn: () => api.post("/core/password-reset/request/", { email: email.trim() }),
    onSuccess: () => {
      toast.success("If an account exists, a reset code was emailed.");
      setDone(true);
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <AuthShell
      title="Forgot password"
      subtitle="We’ll email a one-time code if your account exists."
      footer={
        <p className="text-center text-sm text-[var(--text-muted)]">
          <Link to="/login" className="font-medium text-[var(--accent-bright)] hover:underline">
            ← Back to sign in
          </Link>
        </p>
      }
    >
      {done ? (
        <div className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] p-6 text-sm text-[var(--text-muted)]">
          Check your inbox for the code, then continue to{" "}
          <Link
            to={`/reset-password?email=${encodeURIComponent(email.trim())}`}
            className="font-semibold text-[var(--accent-bright)] hover:underline"
          >
            reset password
          </Link>
          .
        </div>
      ) : (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <input
            type="email"
            required
            autoComplete="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={inputCn()}
          />
          <button
            type="submit"
            disabled={mutation.isPending}
            className={btnPrimaryCn("w-full")}
          >
            {mutation.isPending ? "Sending…" : "Send reset code"}
          </button>
        </form>
      )}
    </AuthShell>
  );
}
