/* eslint-disable @typescript-eslint/no-explicit-any */
import { useIsFetching, useQuery, useQueryClient } from "@tanstack/react-query";
import { format, parseISO, isValid } from "date-fns";
import { useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  Activity,
  BarChart3,
  Clock,
  Database,
  HardDrive,
  LayoutDashboard,
  PieChart as PieIcon,
} from "lucide-react";
import api from "../services/api";
import { QueryErrorBlock, RefreshButton } from "./ui/QueryRefresh";
import { AnalyticsDateFilterBar } from "./analytics/AnalyticsDateFilter";
import {
  analyticsQueryString,
  DEFAULT_ANALYTICS_FILTER,
  periodLabel,
  type AnalyticsDateFilter,
} from "../lib/analyticsDateFilter";
import { cn } from "../lib/cn";
import { useThemeStore } from "../store/themeStore";

const TAB_QUERY_KEYS: Record<string, string[][]> = {
  overview: [["analytics", "dashboard"]],
  inventory: [["analytics", "inventory"]],
  performance: [["analytics", "performance"]],
  errors: [["analytics", "errors"]],
  collections: [["analytics", "top-collections"]],
  endpoints: [["analytics", "endpoint-volume"]],
  operations: [["analytics", "operation-breakdown"], ["analytics", "dashboard"]],
  storage: [["analytics", "storage-trend"]],
  slow: [["analytics", "slow-queries"]],
};

const COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)"];

const unwrapData = (response: any) => {
  const inner = response?.data ?? response;
  if (inner && typeof inner === "object" && "success" in inner && inner.success === true) {
    return inner;
  }
  return inner;
};

function formatTickDate(value: string) {
  try {
    const d = parseISO(value);
    if (!isValid(d)) return value;
    return format(d, "MMM d");
  } catch {
    return value;
  }
}

const tabConfig = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "inventory", label: "Data inventory", icon: Database },
  { id: "performance", label: "Performance", icon: Activity },
  { id: "errors", label: "Errors", icon: PieIcon },
  { id: "collections", label: "Collections", icon: Database },
  { id: "endpoints", label: "Endpoints", icon: BarChart3 },
  { id: "operations", label: "Operations", icon: PieIcon },
  { id: "storage", label: "Storage", icon: HardDrive },
  { id: "slow", label: "Slow queries", icon: Clock },
] as const;

type TabId = (typeof tabConfig)[number]["id"];

function dateFilterKey(f: AnalyticsDateFilter): string {
  return f.preset === "custom" && f.startDate && f.endDate
    ? `custom:${f.startDate}:${f.endDate}`
    : `days:${f.days}`;
}

const AnalyticsCharts = () => {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const [dateFilter, setDateFilter] = useState<AnalyticsDateFilter>(DEFAULT_ANALYTICS_FILTER);
  const themeMode = useThemeStore((s) => s.mode);
  const queryClient = useQueryClient();
  const analyticsFetching = useIsFetching({ queryKey: ["analytics"] });
  const qs = analyticsQueryString(dateFilter);
  const dk = dateFilterKey(dateFilter);
  const periodText = periodLabel(dateFilter);

  const axisProps = useMemo(
    () => ({
      stroke: "var(--chart-axis)",
      tick: { fill: "var(--text-muted)", fontSize: 11 },
    }),
    []
  );

  const { data: dashboardRaw, isLoading: dashboardLoading, error: dashboardError } = useQuery({
    queryKey: ["analytics", "dashboard", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/dashboard/${qs}`);
      return unwrapData(res) || { overview: null, daily_requests: null };
    },
    retry: 1,
  });

  const { data: inventoryRaw, isLoading: inventoryLoading } = useQuery({
    queryKey: ["analytics", "inventory", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/inventory/${qs}`);
      return unwrapData(res) || { databases: [], totals: {} };
    },
    retry: 1,
  });

  const { data: performanceRaw, isLoading: perfLoading, error: perfError } = useQuery({
    queryKey: ["analytics", "performance", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/performance/${qs}`);
      return unwrapData(res) || { percentiles_ms: {}, throughput_last_24h: [] };
    },
    retry: 1,
  });

  const { data: errorsRaw, isLoading: errorsLoading, error: errorsErr } = useQuery({
    queryKey: ["analytics", "errors", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/errors/${qs}`);
      return unwrapData(res) || {
        errors_by_status_code: {},
        top_error_endpoints: [],
        error_types: {},
      };
    },
    retry: 1,
  });

  const { data: endpointsRaw } = useQuery({
    queryKey: ["analytics", "endpoint-volume", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/endpoint-volume/${qs}`);
      return unwrapData(res) || { endpoint_volume: [] };
    },
    retry: 1,
  });

  const { data: operationsRaw } = useQuery({
    queryKey: ["analytics", "operation-breakdown", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/operation-breakdown/${qs}`);
      return unwrapData(res) || { operation_breakdown: {} };
    },
    retry: 1,
  });

  const { data: storageRaw } = useQuery({
    queryKey: ["analytics", "storage-trend", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/storage-trend/${qs}`);
      return unwrapData(res) || { storage_trend_mb: [] };
    },
    retry: 1,
  });

  const { data: slowRaw } = useQuery({
    queryKey: ["analytics", "slow-queries", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/slow-queries/${qs}${qs ? "&" : "?"}limit=15`);
      return unwrapData(res) || { data: [] };
    },
    retry: 1,
  });

  const { data: topCollectionsRaw, isLoading: topLoading, error: topErr } = useQuery({
    queryKey: ["analytics", "top-collections", dk],
    queryFn: async () => {
      const res = await api.get(`/analytics/api/v2/top-collections/${qs}`);
      const u = unwrapData(res);
      if (Array.isArray(u)) return { top_collections: u };
      if (u?.top_collections) return u;
      return { top_collections: [] };
    },
    retry: 1,
  });

  const dashboard = dashboardRaw || {};
  const inventory = inventoryRaw || {};
  const baseSummary = (dashboard as any)?.base_summary || (dashboard as any)?.overview || {};
  const technicalSummary =
    (dashboard as any)?.technical_summary || (dashboard as any)?.overview || {};
  const performance = performanceRaw || {};
  const errors = errorsRaw || {};
  const topCollections = topCollectionsRaw?.top_collections || [];
  const endpointVolume = (endpointsRaw as any)?.endpoint_volume || [];
  const operationBreakdown = (operationsRaw as any)?.operation_breakdown || {};
  const storageTrend = (storageRaw as any)?.storage_trend_mb || [];
  const slowQueries = (slowRaw as any)?.data || [];
  const methods7d = (dashboard as any)?.methods || (dashboard as any)?.methods_7d || {};
  const inventoryDbs = (inventory as any)?.databases || [];

  const isLoading = dashboardLoading || perfLoading || errorsLoading || topLoading;
  const hasError = dashboardError || perfError || errorsErr || topErr;
  const isRefreshing = analyticsFetching > 0 && !isLoading;

  const refreshTab = () => {
    (TAB_QUERY_KEYS[activeTab] ?? []).forEach((key) =>
      queryClient.invalidateQueries({ queryKey: key })
    );
  };

  const refreshAll = () => {
    queryClient.invalidateQueries({ queryKey: ["analytics"] });
  };

  const dailyData = useMemo(() => {
    const dr = (dashboard as any)?.daily_requests;
    if (!dr?.dates || !Array.isArray(dr.dates)) return [];
    return dr.dates.map((date: string, idx: number) => ({
      date,
      label: formatTickDate(date),
      requests: dr.counts?.[idx] ?? 0,
      avgDuration: Math.round(dr.avg_durations_ms?.[idx] ?? 0),
    }));
  }, [dashboard]);

  const throughputData = useMemo(() => {
    const raw = (performance as any)?.throughput_last_24h || [];
    return raw.map((row: any) => ({
      ...row,
      label: row.hour?.replace(" ", "\n") ?? row.hour,
    }));
  }, [performance]);

  const errorStatusData = errors?.errors_by_status_code
    ? Object.entries(errors.errors_by_status_code).map(([code, count]) => ({
        name: String(code),
        value: count as number,
      }))
    : [];

  const topEndpoints = errors?.top_error_endpoints || [];
  const percentiles = (performance as any)?.percentiles_ms;

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-elevated)] px-3 py-2 text-xs shadow-[var(--shadow-md)]">
        <p className="mb-1 font-semibold text-[var(--text-primary)]">{label}</p>
        {payload.map((p: any) => (
          <p key={p.dataKey} className="text-[var(--text-muted)]">
            <span style={{ color: p.color }}>{p.name}:</span>{" "}
            <span className="font-mono text-[var(--text-primary)]">{p.value}</span>
          </p>
        ))}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center text-[var(--text-muted)]">
        <div className="flex items-center gap-3">
          <BarChart3 className="h-6 w-6 animate-pulse text-[var(--accent-bright)]" />
          Loading analytics…
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <QueryErrorBlock
        message="Could not load analytics. Check your connection and try again."
        onRetry={refreshAll}
        isRefreshing={isRefreshing}
      />
    );
  }

  return (
    <div className={cn("space-y-6", isRefreshing && "opacity-90")} data-theme={themeMode}>
      <AnalyticsDateFilterBar value={dateFilter} onChange={setDateFilter} />
      <div className="flex flex-wrap items-center justify-end gap-2">
        <RefreshButton
          onClick={refreshTab}
          isRefreshing={isRefreshing}
          label="Reload tab"
        />
        <RefreshButton
          onClick={refreshAll}
          isRefreshing={isRefreshing}
          label="Reload all"
        />
      </div>
      <div className="flex flex-wrap gap-2 border-b border-[var(--border-subtle)] pb-1 rounded-t-[var(--radius-md)]">
        {tabConfig.map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "inline-flex items-center gap-2 rounded-t-[var(--radius-md)] px-4 py-2.5 text-sm font-medium transition-all duration-200",
                active
                  ? "bg-[var(--accent-soft)] text-[var(--accent-bright)] shadow-sm"
                  : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]/60 hover:text-[var(--text-primary)]"
              )}
            >
              <Icon className="h-4 w-4 opacity-80" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {activeTab === "overview" && (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <section className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
              <h3 className="text-base font-semibold text-[var(--text-primary)]">Base summary</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Data plane & account ({periodText})</p>
              <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                {[
                  { k: "Databases", v: baseSummary.database_count, tone: "text-[var(--accent-bright)]" },
                  { k: "Collections", v: baseSummary.collection_count, tone: "text-[var(--accent-bright)]" },
                  { k: "Documents", v: baseSummary.document_count, tone: "text-[var(--text-primary)]" },
                  { k: "Data storage", v: baseSummary.storage_data_mb, suf: " MB", tone: "text-[var(--chart-3)]" },
                  { k: "File storage", v: baseSummary.storage_files_mb, suf: " MB", tone: "text-[var(--chart-4)]" },
                  { k: "Files", v: baseSummary.file_count, tone: "text-[var(--chart-4)]" },
                  { k: "API calls (period)", v: baseSummary.api_calls_in_period, tone: "text-[var(--chart-2)]" },
                  { k: "API calls (month)", v: baseSummary.api_calls_current_month, tone: "text-[var(--text-muted)]" },
                ].map((card) => (
                  <div key={card.k} className="rounded-[var(--radius-md)] border border-[var(--border-subtle)]/80 px-3 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-subtle)]">{card.k}</p>
                    <p className={cn("mt-1 text-lg font-bold tabular-nums", card.tone)}>
                      {typeof card.v === "number" ? card.v.toLocaleString() : card.v ?? "—"}
                      {(card as { suf?: string }).suf ?? ""}
                    </p>
                  </div>
                ))}
              </div>
            </section>
            <section className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
              <h3 className="text-base font-semibold text-[var(--text-primary)]">Technical summary</h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">HTTP telemetry ({periodText})</p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                {[
                  { k: "Requests", v: technicalSummary.total_requests, tone: "text-[var(--chart-2)]" },
                  { k: "Avg latency", v: technicalSummary.avg_response_time_ms, suf: " ms", tone: "text-[var(--chart-1)]" },
                  { k: "Error rate", v: technicalSummary.error_rate_percent, suf: "%", tone: "text-[var(--danger)]" },
                  { k: "Slow queries", v: technicalSummary.slow_queries, tone: "text-[var(--warning)]" },
                ].map((card) => (
                  <div key={card.k} className="rounded-[var(--radius-md)] border border-[var(--border-subtle)]/80 px-3 py-3">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-[var(--text-subtle)]">{card.k}</p>
                    <p className={cn("mt-1 text-lg font-bold tabular-nums", card.tone)}>
                      {typeof card.v === "number" ? card.v.toLocaleString() : card.v ?? "—"}
                      {(card as { suf?: string }).suf ?? ""}
                    </p>
                  </div>
                ))}
              </div>
              <p className="mt-4 text-xs text-[var(--text-subtle)]">
                Plan: {baseSummary.subscription_plan ?? "—"} · Role: {baseSummary.role ?? "—"}
                {baseSummary.last_activity_at ? ` · Last activity: ${formatTickDate(baseSummary.last_activity_at.slice(0, 10))}` : ""}
              </p>
            </section>
          </div>

          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
            <h3 className="mb-1 text-base font-semibold text-[var(--text-primary)]">
              Traffic & latency trend
            </h3>
            <p className="mb-4 text-sm text-[var(--text-muted)]">
              Daily request volume vs average response time ({periodText})
            </p>
            {dailyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={320}>
                <ComposedChart data={dailyData} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="reqFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--chart-2)" stopOpacity={0.35} />
                      <stop offset="100%" stopColor="var(--chart-2)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" {...axisProps} tickLine={false} axisLine={false} />
                  <YAxis yAxisId="l" {...axisProps} tickLine={false} axisLine={false} />
                  <YAxis
                    yAxisId="r"
                    orientation="right"
                    {...axisProps}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Area
                    yAxisId="l"
                    type="monotone"
                    dataKey="requests"
                    name="Requests"
                    stroke="var(--chart-2)"
                    fill="url(#reqFill)"
                    strokeWidth={2}
                  />
                  <Line
                    yAxisId="r"
                    type="monotone"
                    dataKey="avgDuration"
                    name="Avg ms"
                    stroke="var(--chart-1)"
                    strokeWidth={2}
                    dot={false}
                  />
                  <ReferenceLine
                    yAxisId="r"
                    y={500}
                    stroke="var(--warning)"
                    strokeDasharray="4 4"
                  />
                </ComposedChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-12 text-center text-[var(--text-muted)]">
                No traffic data for this period yet. Make API calls to populate analytics.
              </p>
            )}
          </div>
        </>
      )}

      {activeTab === "inventory" && (
        <div className="space-y-4">
          {inventoryLoading ? (
            <p className="text-sm text-[var(--text-muted)]">Loading inventory…</p>
          ) : inventoryDbs.length === 0 ? (
            <p className="text-sm text-[var(--text-muted)]">No databases yet.</p>
          ) : (
            inventoryDbs.map((db: any) => (
              <div
                key={db.id}
                className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h3 className="text-lg font-semibold text-[var(--accent-bright)]">{db.display_name}</h3>
                    <p className="mt-1 font-mono text-xs text-[var(--text-subtle)]">{db.id}</p>
                  </div>
                  <div className="text-right text-sm text-[var(--text-muted)]">
                    <p>{db.document_count?.toLocaleString()} docs · {db.storage_mb} MB</p>
                    <p>{db.api_calls?.toLocaleString()} API ops ({periodText})</p>
                  </div>
                </div>
                <dl className="mt-4 grid gap-2 text-xs sm:grid-cols-2 lg:grid-cols-4">
                  <div><dt className="text-[var(--text-subtle)]">Created</dt><dd>{db.created_at ? formatTickDate(db.created_at.slice(0, 10)) : "—"}</dd></div>
                  <div><dt className="text-[var(--text-subtle)]">Last access</dt><dd>{db.last_access_at ? formatTickDate(db.last_access_at.slice(0, 10)) : "—"}</dd></div>
                  <div><dt className="text-[var(--text-subtle)]">Updated</dt><dd>{db.updated_at ? formatTickDate(db.updated_at.slice(0, 10)) : "—"}</dd></div>
                  <div><dt className="text-[var(--text-subtle)]">Stats refreshed</dt><dd>{db.stats_updated_at ? formatTickDate(db.stats_updated_at.slice(0, 10)) : "—"}</dd></div>
                </dl>
                {db.trend?.length > 0 && (
                  <div className="mt-4 h-[120px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={db.trend.map((t: any) => ({ ...t, label: formatTickDate(t.date) }))}>
                        <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                        <XAxis dataKey="label" {...axisProps} tick={{ fontSize: 9 }} />
                        <YAxis {...axisProps} hide />
                        <Tooltip />
                        <Area type="monotone" dataKey="api_calls" stroke="var(--chart-2)" fill="var(--chart-2)" fillOpacity={0.15} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}
                <div className="mt-4 overflow-x-auto">
                  <table className="w-full min-w-[520px] text-left text-sm">
                    <thead>
                      <tr className="border-b border-[var(--border-subtle)] text-xs uppercase text-[var(--text-subtle)]">
                        <th className="py-2 pr-4">Collection</th>
                        <th className="py-2 pr-4">Documents</th>
                        <th className="py-2 pr-4">Size (MB)</th>
                        <th className="py-2 pr-4">API calls</th>
                        <th className="py-2">Last access</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(db.collections || []).map((c: any) => (
                        <tr key={c.name} className="border-b border-[var(--border-subtle)]/60">
                          <td className="py-2 pr-4 font-medium">{c.name}</td>
                          <td className="py-2 pr-4 tabular-nums">{c.document_count?.toLocaleString()}</td>
                          <td className="py-2 pr-4 tabular-nums">{c.storage_mb}</td>
                          <td className="py-2 pr-4 tabular-nums">{c.api_calls?.toLocaleString()}</td>
                          <td className="py-2 text-[var(--text-muted)]">
                            {c.last_access_at ? formatTickDate(c.last_access_at.slice(0, 10)) : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {activeTab === "performance" && (
        <>
          {percentiles && Object.keys(percentiles).length > 0 && (
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(percentiles).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 text-center"
                >
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-subtle)]">
                    {key}
                  </div>
                  <div className="mt-1 text-xl font-bold tabular-nums text-[var(--chart-2)]">
                    {String(value)} ms
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
            <h3 className="mb-1 text-base font-semibold text-[var(--text-primary)]">
              Hourly throughput
            </h3>
            <p className="mb-4 text-sm text-[var(--text-muted)]">
              Request count by hour (last 24h)
            </p>
            {throughputData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={throughputData}>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                  <XAxis
                    dataKey="hour"
                    {...axisProps}
                    tick={{ ...axisProps.tick, fontSize: 9 }}
                    angle={-35}
                    textAnchor="end"
                    height={70}
                    interval={0}
                    tickFormatter={(v) => (typeof v === "string" && v.length > 13 ? v.slice(0, 13) + "…" : v)}
                  />
                  <YAxis {...axisProps} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="requests" name="Requests" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-12 text-center text-[var(--text-muted)]">
                No throughput samples yet.
              </p>
            )}
          </div>
        </>
      )}

      {activeTab === "errors" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4">
            <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">
              Errors by HTTP status
            </h3>
            {errorStatusData.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={errorStatusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={58}
                    outerRadius={88}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`
                    }
                  >
                    {errorStatusData.map((_e, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-10 text-center text-[var(--text-muted)]">No errors — great job.</p>
            )}
          </div>
          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4">
            <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">
              Noisiest endpoints
            </h3>
            {topEndpoints.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={topEndpoints} layout="vertical" margin={{ left: 8 }}>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" horizontal />
                  <XAxis type="number" {...axisProps} tickLine={false} />
                  <YAxis type="category" dataKey="path" width={120} tick={{ ...axisProps.tick, fontSize: 10 }} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="errors" name="Errors" fill="var(--danger)" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-10 text-center text-[var(--text-muted)]">No failing routes in range.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "collections" && (
        <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
          <h3 className="mb-1 text-base font-semibold text-[var(--text-primary)]">
            Hottest collections
          </h3>
          <p className="mb-4 text-sm text-[var(--text-muted)]">
            MongoDB operations logged per collection ({periodText})
          </p>
          {topCollections.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart
                data={topCollections.map((c: any) => ({
                  ...c,
                  label: c.db_id ? `${c.name}` : c.name,
                }))}
              >
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" {...axisProps} tickLine={false} axisLine={false} />
                <YAxis {...axisProps} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="operations" name="Ops" fill="var(--chart-3)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-[var(--text-muted)]">No collection ops recorded yet.</p>
          )}
        </div>
      )}

      {activeTab === "endpoints" && (
        <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
          <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">Request volume by endpoint</h3>
          {endpointVolume.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={endpointVolume} layout="vertical" margin={{ left: 8 }}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" horizontal />
                <XAxis type="number" {...axisProps} tickLine={false} />
                <YAxis type="category" dataKey="endpoint" width={140} tick={{ ...axisProps.tick, fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="requests" name="Requests" fill="var(--chart-2)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-[var(--text-muted)]">No endpoint data yet.</p>
          )}
        </div>
      )}

      {activeTab === "operations" && (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4">
            <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">DB operations by type</h3>
            {Object.keys(operationBreakdown).length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={Object.entries(operationBreakdown).map(([name, value]) => ({ name, value }))}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="50%"
                    outerRadius={90}
                    label={({ name, percent }) => `${name} (${((percent ?? 0) * 100).toFixed(0)}%)`}
                  >
                    {Object.keys(operationBreakdown).map((_k, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-10 text-center text-[var(--text-muted)]">No operations logged yet.</p>
            )}
          </div>
          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4">
            <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">HTTP methods ({periodText})</h3>
            {Object.keys(methods7d).length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={Object.entries(methods7d).map(([name, value]) => ({ name, value }))}>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" {...axisProps} tickLine={false} axisLine={false} />
                  <YAxis {...axisProps} tickLine={false} axisLine={false} />
                  <Tooltip content={<CustomTooltip />} />
                  <Bar dataKey="value" name="Requests" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="py-10 text-center text-[var(--text-muted)]">No method breakdown yet.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "storage" && (
        <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
          <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">
            Storage & activity ({periodText})
          </h3>
          {storageTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={storageTrend.map((r: any) => ({ ...r, label: formatTickDate(r.date) }))}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="label" {...axisProps} tickLine={false} axisLine={false} />
                <YAxis {...axisProps} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area type="monotone" dataKey="storage_mb" name="Files (MB)" stroke="var(--chart-3)" fill="var(--chart-3)" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-[var(--text-muted)]">Upload files to see storage growth.</p>
          )}
          {(storageRaw as any)?.data_activity_trend?.length > 0 && (
            <div className="mt-6">
              <h4 className="mb-2 text-sm font-medium text-[var(--text-muted)]">Data API activity (calls per day)</h4>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={(storageRaw as any).data_activity_trend.map((r: any) => ({ ...r, label: formatTickDate(r.date) }))}>
                  <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" {...axisProps} tick={{ fontSize: 10 }} />
                  <YAxis {...axisProps} tickLine={false} axisLine={false} />
                  <Tooltip />
                  <Bar dataKey="api_calls" name="API calls" fill="var(--chart-2)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {activeTab === "slow" && (
        <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
          <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">Recent slow queries</h3>
          {slowQueries.length > 0 ? (
            <ul className="divide-y divide-[var(--border-subtle)] text-sm">
              {slowQueries.map((row: any) => (
                <li key={row.id} className="flex flex-wrap items-center justify-between gap-2 py-3">
                  <span className="font-mono text-[var(--text-muted)]">{row.collection || "—"}</span>
                  <span className="tabular-nums text-[var(--warning)]">{row.duration_ms} ms</span>
                  <span className="w-full text-xs text-[var(--text-subtle)]">{row.timestamp}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="py-12 text-center text-[var(--text-muted)]">No slow queries recorded.</p>
          )}
        </div>
      )}
    </div>
  );
};

export default AnalyticsCharts;
