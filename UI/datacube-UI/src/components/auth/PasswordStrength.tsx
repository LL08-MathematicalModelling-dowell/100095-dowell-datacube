import { cn } from "../../lib/cn";

export type PasswordRuleId =
  | "len"
  | "upper"
  | "lower"
  | "number"
  | "special";

export const PASSWORD_RULES: { id: PasswordRuleId; label: string }[] = [
  { id: "len", label: "At least 12 characters" },
  { id: "upper", label: "One uppercase letter" },
  { id: "lower", label: "One lowercase letter" },
  { id: "number", label: "One number" },
  { id: "special", label: "One special character (!@#$%…)" },
];

export function evaluatePasswordRules(password: string): Record<PasswordRuleId, boolean> {
  return {
    len: password.length >= 12,
    upper: /[A-Z]/.test(password),
    lower: /[a-z]/.test(password),
    number: /\d/.test(password),
    special: /[^A-Za-z0-9]/.test(password),
  };
}

export function passwordStrengthScore(password: string): number {
  const r = evaluatePasswordRules(password);
  return Object.values(r).filter(Boolean).length;
}

/** Live checklist + meter — backend still accepts min 8; UI enforces stricter rules. */
export function PasswordStrength({ password }: { password: string }) {
  const rules = evaluatePasswordRules(password);
  const score = Object.values(rules).filter(Boolean).length;
  const pct = (score / PASSWORD_RULES.length) * 100;

  let label = "Enter a password";
  let barClass = "bg-[var(--surface-2)]";
  if (password.length > 0) {
    if (score < 3) {
      label = "Weak";
      barClass = "bg-[var(--danger)]";
    } else if (score < 5) {
      label = "Medium";
      barClass = "bg-[var(--warning)]";
    } else {
      label = "Strong";
      barClass = "bg-[var(--accent-bright)]";
    }
  }

  return (
    <div className="mt-3 space-y-3">
      <div>
        <div className="mb-1 flex justify-between text-xs text-[var(--text-muted)]">
          <span>Strength</span>
          <span className="font-medium text-[var(--text-primary)]">{label}</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-[var(--surface-2)]">
          <div
            className={cn("h-full rounded-full transition-all duration-300", barClass)}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
      <ul className="space-y-1.5 text-xs" aria-live="polite">
        {PASSWORD_RULES.map(({ id, label: text }) => (
          <li
            key={id}
            className={cn(
              "flex items-center gap-2",
              rules[id] ? "text-[var(--accent-bright)]" : "text-[var(--text-subtle)]"
            )}
          >
            <span
              className={cn(
                "inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full border text-[10px] font-bold",
                rules[id]
                  ? "border-[var(--accent-bright)] bg-[var(--accent-soft)]"
                  : "border-[var(--border-subtle)]"
              )}
              aria-hidden
            >
              {rules[id] ? "✓" : ""}
            </span>
            {text}
          </li>
        ))}
      </ul>
    </div>
  );
}
