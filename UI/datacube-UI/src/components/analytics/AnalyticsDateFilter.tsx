import { cn } from "../../lib/cn";
import {
  type AnalyticsDateFilter,
  type AnalyticsDatePreset,
  periodLabel,
} from "../../lib/analyticsDateFilter";
import { inputCn } from "../../lib/uiClasses";

type Props = {
  value: AnalyticsDateFilter;
  onChange: (next: AnalyticsDateFilter) => void;
  className?: string;
};

const PRESETS: { id: AnalyticsDatePreset; label: string }[] = [
  { id: 7, label: "7d" },
  { id: 14, label: "14d" },
  { id: 30, label: "30d" },
  { id: "custom", label: "Custom" },
];

export function AnalyticsDateFilterBar({ value, onChange, className }: Props) {
  const setPreset = (preset: AnalyticsDatePreset) => {
    if (preset === "custom") {
      onChange({ ...value, preset: "custom" });
      return;
    }
    onChange({
      preset,
      days: preset,
      startDate: "",
      endDate: "",
    });
  };

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)]/80 p-3 sm:flex-row sm:flex-wrap sm:items-end sm:justify-between",
        className
      )}
    >
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-[var(--text-subtle)]">
          Date range
        </p>
        <p className="mt-0.5 text-sm text-[var(--text-muted)]">{periodLabel(value)}</p>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        {PRESETS.map((p) => (
          <button
            key={String(p.id)}
            type="button"
            onClick={() => setPreset(p.id)}
            className={cn(
              "rounded-[var(--radius-sm)] px-3 py-1.5 text-xs font-semibold transition-colors",
              value.preset === p.id
                ? "bg-[var(--accent-soft)] text-[var(--accent-bright)]"
                : "bg-[var(--surface-2)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            )}
          >
            {p.label}
          </button>
        ))}
        {value.preset === "custom" && (
          <>
            <input
              type="date"
              className={cn(inputCn(), "w-auto py-1.5 text-xs")}
              value={value.startDate}
              onChange={(e) => onChange({ ...value, startDate: e.target.value })}
            />
            <span className="text-[var(--text-subtle)]">→</span>
            <input
              type="date"
              className={cn(inputCn(), "w-auto py-1.5 text-xs")}
              value={value.endDate}
              onChange={(e) => onChange({ ...value, endDate: e.target.value })}
            />
          </>
        )}
      </div>
    </div>
  );
}
