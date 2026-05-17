import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import toast from "react-hot-toast";
import { z } from "zod";
import { AuthShell } from "../components/auth/AuthShell.tsx";
import {
  evaluatePasswordRules,
  PASSWORD_RULES,
  PasswordStrength,
} from "../components/auth/PasswordStrength.tsx";
import { cn } from "../lib/cn.ts";
import { btnPrimaryCn, inputCn } from "../lib/uiClasses.ts";
import api from "../services/api.ts";
import { getApiErrorMessage } from "../lib/apiErrors.ts";

const passwordField = z
  .string()
  .min(12, "Use at least 12 characters")
  .refine((p) => evaluatePasswordRules(p).upper, "Add an uppercase letter")
  .refine((p) => evaluatePasswordRules(p).lower, "Add a lowercase letter")
  .refine((p) => evaluatePasswordRules(p).number, "Add a number")
  .refine((p) => evaluatePasswordRules(p).special, "Add a special character");

const schema = z
  .object({
    email: z.string().email("Invalid email"),
    code: z.string().min(4, "Code required").max(12),
    password: passwordField,
    passwordConfirm: z.string(),
  })
  .refine((d) => d.password === d.passwordConfirm, {
    path: ["passwordConfirm"],
    message: "Passwords must match",
  });

type Form = z.infer<typeof schema>;

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const emailParam = searchParams.get("email")?.trim() || "";

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<Form>({
    resolver: zodResolver(schema),
    defaultValues: { email: emailParam, code: "", password: "", passwordConfirm: "" },
  });

  const password = watch("password");

  useEffect(() => {
    if (emailParam) setValue("email", emailParam);
  }, [emailParam, setValue]);

  const mutation = useMutation({
    mutationFn: (data: Form) =>
      api.post("/core/password-reset/confirm/", {
        email: data.email.trim(),
        code: data.code.trim(),
        password: data.password,
      }),
    onSuccess: () => {
      toast.success("Password updated. Sign in with your new password.");
      navigate("/login", { replace: true });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  return (
    <AuthShell
      title="Set a new password"
      subtitle="Use the code from your email. The same strength rules apply as for registration."
      footer={
        <p className="text-center text-sm text-[var(--text-muted)]">
          <Link to="/login" className="font-medium text-[var(--accent-bright)] hover:underline">
            Sign in
          </Link>
        </p>
      }
    >
      <ul className="mb-6 text-xs text-[var(--text-subtle)]">
        {PASSWORD_RULES.map((r) => (
          <li key={r.id}>• {r.label}</li>
        ))}
      </ul>
      <form
        onSubmit={handleSubmit((data) => mutation.mutate(data))}
        className="space-y-4"
      >
        <div>
          <input
            type="email"
            autoComplete="email"
            placeholder="Email"
            className={inputCn()}
            {...register("email")}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-[var(--danger)]">{errors.email.message}</p>
          )}
        </div>
        <div>
          <input
            inputMode="numeric"
            autoComplete="one-time-code"
            placeholder="Reset code from email"
            className={cn(inputCn(), "font-mono")}
            {...register("code")}
          />
          {errors.code && (
            <p className="mt-1 text-sm text-[var(--danger)]">{errors.code.message}</p>
          )}
        </div>
        <div>
          <input
            type="password"
            autoComplete="new-password"
            placeholder="New password"
            className={inputCn()}
            {...register("password")}
          />
          <PasswordStrength password={password} />
          {errors.password && (
            <p className="mt-1 text-sm text-[var(--danger)]">{errors.password.message}</p>
          )}
        </div>
        <div>
          <input
            type="password"
            autoComplete="new-password"
            placeholder="Confirm new password"
            className={inputCn()}
            {...register("passwordConfirm")}
          />
          {errors.passwordConfirm && (
            <p className="mt-1 text-sm text-[var(--danger)]">
              {errors.passwordConfirm.message}
            </p>
          )}
        </div>
        <button type="submit" disabled={mutation.isPending} className={btnPrimaryCn("w-full")}>
          {mutation.isPending ? "Saving…" : "Update password"}
        </button>
      </form>
    </AuthShell>
  );
}
