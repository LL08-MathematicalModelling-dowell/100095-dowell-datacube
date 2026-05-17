import { cn } from "./cn";

/** Single-line text inputs + textareas */
export const inputClass =
  "w-full rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-3 py-3 text-[var(--text-primary)] placeholder:text-[var(--text-subtle)] shadow-[var(--shadow-sm)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--accent-ring)] focus:border-[var(--accent)]";

/** Primary call-to-action */
export const btnPrimaryClass =
  "inline-flex w-full items-center justify-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-3 font-semibold text-white shadow-[var(--shadow-sm)] transition-colors hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50";

/** Secondary / ghost actions */
export const btnSecondaryClass =
  "inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-1)] px-4 py-3 font-semibold text-[var(--text-primary)] transition-colors hover:bg-[var(--surface-2)] disabled:cursor-not-allowed disabled:opacity-50";

/** Auth / marketing card shell (pair with w-full max-w-sm | max-w-md) */
export const authCardShell =
  "rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)]/95 p-8 shadow-[var(--shadow-md)] backdrop-blur-sm";

export function inputCn(extra?: string) {
  return cn(inputClass, extra);
}

export function btnPrimaryCn(extra?: string) {
  return cn(btnPrimaryClass, extra);
}

export function btnSecondaryCn(extra?: string) {
  return cn(btnSecondaryClass, extra);
}
