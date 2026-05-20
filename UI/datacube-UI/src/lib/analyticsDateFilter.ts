/** Shared date-range query params for analytics API calls. */

export type AnalyticsDatePreset = 7 | 14 | 30 | "custom";

export type AnalyticsDateFilter = {
  preset: AnalyticsDatePreset;
  days: number;
  startDate: string;
  endDate: string;
};

export const DEFAULT_ANALYTICS_FILTER: AnalyticsDateFilter = {
  preset: 14,
  days: 14,
  startDate: "",
  endDate: "",
};

export function analyticsQueryString(filter: AnalyticsDateFilter): string {
  if (filter.preset === "custom" && filter.startDate && filter.endDate) {
    const p = new URLSearchParams({
      start_date: filter.startDate,
      end_date: filter.endDate,
    });
    return `?${p.toString()}`;
  }
  const p = new URLSearchParams({ days: String(filter.days) });
  return `?${p.toString()}`;
}

export function periodLabel(filter: AnalyticsDateFilter): string {
  if (filter.preset === "custom" && filter.startDate && filter.endDate) {
    return `${filter.startDate} → ${filter.endDate}`;
  }
  return `Last ${filter.days} days`;
}
