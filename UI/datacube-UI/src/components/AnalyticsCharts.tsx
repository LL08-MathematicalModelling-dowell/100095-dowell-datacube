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
import { cn } from "../lib/cn";
import { useThemeStore } from "../store/themeStore";

const TAB_QUERY_KEYS: Record<string, string[][]> = {
  overview: [["analytics", "dashboard"]],
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
  { id: "performance", label: "Performance", icon: Activity },
  { id: "errors", label: "Errors", icon: PieIcon },
  { id: "collections", label: "Collections", icon: Database },
  { id: "endpoints", label: "Endpoints", icon: BarChart3 },
  { id: "operations", label: "Operations", icon: PieIcon },
  { id: "storage", label: "Storage", icon: HardDrive },
  { id: "slow", label: "Slow queries", icon: Clock },
] as const;

type TabId = (typeof tabConfig)[number]["id"];

const AnalyticsCharts = () => {
  const [activeTab, setActiveTab] = useState<TabId>("overview");
  const themeMode = useThemeStore((s) => s.mode);
  const queryClient = useQueryClient();
  const analyticsFetching = useIsFetching({ queryKey: ["analytics"] });

  const axisProps = useMemo(
    () => ({
      stroke: "var(--chart-axis)",
      tick: { fill: "var(--text-muted)", fontSize: 11 },
    }),
    []
  );

  const { data: dashboardRaw, isLoading: dashboardLoading, error: dashboardError } = useQuery({
    queryKey: ["analytics", "dashboard"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/dashboard/");
      return unwrapData(res) || { overview: null, daily_requests: null };
    },
    retry: 1,
  });

  const { data: performanceRaw, isLoading: perfLoading, error: perfError } = useQuery({
    queryKey: ["analytics", "performance"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/performance/");
      return unwrapData(res) || { percentiles_ms: {}, throughput_last_24h: [] };
    },
    retry: 1,
  });

  const { data: errorsRaw, isLoading: errorsLoading, error: errorsErr } = useQuery({
    queryKey: ["analytics", "errors"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/errors/");
      return unwrapData(res) || {
        errors_by_status_code: {},
        top_error_endpoints: [],
        error_types: {},
      };
    },
    retry: 1,
  });

  const { data: endpointsRaw } = useQuery({
    queryKey: ["analytics", "endpoint-volume"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/endpoint-volume/");
      return unwrapData(res) || { endpoint_volume: [] };
    },
    retry: 1,
  });

  const { data: operationsRaw } = useQuery({
    queryKey: ["analytics", "operation-breakdown"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/operation-breakdown/");
      return unwrapData(res) || { operation_breakdown: {} };
    },
    retry: 1,
  });

  const { data: storageRaw } = useQuery({
    queryKey: ["analytics", "storage-trend"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/storage-trend/");
      return unwrapData(res) || { storage_trend_mb: [] };
    },
    retry: 1,
  });

  const { data: slowRaw } = useQuery({
    queryKey: ["analytics", "slow-queries"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/slow-queries/?limit=15");
      return unwrapData(res) || { data: [] };
    },
    retry: 1,
  });

  const { data: topCollectionsRaw, isLoading: topLoading, error: topErr } = useQuery({
    queryKey: ["analytics", "top-collections"],
    queryFn: async () => {
      const res = await api.get("/analytics/api/v2/top-collections/");
      const u = unwrapData(res);
      if (Array.isArray(u)) return { top_collections: u };
      if (u?.top_collections) return u;
      return { top_collections: [] };
    },
    retry: 1,
  });

  const dashboard = dashboardRaw || {};
  const performance = performanceRaw || {};
  const errors = errorsRaw || {};
  const topCollections = topCollectionsRaw?.top_collections || [];
  const endpointVolume = (endpointsRaw as any)?.endpoint_volume || [];
  const operationBreakdown = (operationsRaw as any)?.operation_breakdown || {};
  const storageTrend = (storageRaw as any)?.storage_trend_mb || [];
  const slowQueries = (slowRaw as any)?.data || [];
  const methods7d = (dashboard as any)?.methods_7d || {};

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
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              {
                k: "Requests (7d)",
                v: (dashboard as any)?.overview?.total_requests ?? 0,
                suf: "",
                tone: "text-[var(--chart-2)]",
              },
              {
                k: "Avg latency",
                v: (dashboard as any)?.overview?.avg_response_time_ms ?? 0,
                suf: " ms",
                tone: "text-[var(--chart-1)]",
              },
              {
                k: "Error rate",
                v: (dashboard as any)?.overview?.error_rate_percent ?? 0,
                suf: "%",
                tone: "text-[var(--danger)]",
              },
              {
                k: "Storage",
                v: (dashboard as any)?.overview?.total_storage_mb ?? 0,
                suf: " MB",
                tone: "text-[var(--chart-3)]",
              },
            ].map((card) => (
              <div
                key={card.k}
                className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-4 py-4 transition-transform duration-200 hover:shadow-[var(--shadow-sm)]"
              >
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-subtle)]">
                  {card.k}
                </p>
                <p className={cn("mt-2 text-2xl font-bold tabular-nums", card.tone)}>
                  {typeof card.v === "number" ? card.v.toLocaleString() : card.v}
                  {card.suf}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {[
              { k: "Databases", v: (dashboard as any)?.overview?.database_count ?? 0, tone: "text-[var(--accent-bright)]" },
              { k: "Collections", v: (dashboard as any)?.overview?.collection_count ?? 0, tone: "text-[var(--accent-bright)]" },
              { k: "Files", v: (dashboard as any)?.overview?.file_count ?? 0, tone: "text-[var(--chart-4)]" },
              { k: "API calls (month)", v: (dashboard as any)?.overview?.api_calls_current_month ?? 0, tone: "text-[var(--text-primary)]" },
              { k: "Slow queries (7d)", v: (dashboard as any)?.overview?.slow_queries_7d ?? 0, tone: "text-[var(--warning)]" },
            ].map((card) => (
              <div key={card.k} className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-4 py-4">
                <p className="text-xs font-medium uppercase tracking-wide text-[var(--text-subtle)]">{card.k}</p>
                <p className={cn("mt-2 text-2xl font-bold tabular-nums", card.tone)}>
                  {typeof card.v === "number" ? card.v.toLocaleString() : card.v}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-4 sm:p-5">
            <h3 className="mb-1 text-base font-semibold text-[var(--text-primary)]">
              Traffic & latency trend
            </h3>
            <p className="mb-4 text-sm text-[var(--text-muted)]">
              Daily request volume vs average response time (last 7 days)
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
            MongoDB operations logged per collection (7-day window)
          </p>
          {topCollections.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={topCollections}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" {...axisProps} tickLine={false} axisLine={false} />
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
            <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">HTTP methods (7d)</h3>
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
          <h3 className="mb-4 text-base font-semibold text-[var(--text-primary)]">File storage trend (30d)</h3>
          {storageTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={storageTrend}>
                <CartesianGrid stroke="var(--chart-grid)" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="date" {...axisProps} tickFormatter={formatTickDate} tickLine={false} axisLine={false} />
                <YAxis {...axisProps} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="storage_mb" name="MB" stroke="var(--chart-3)" fill="var(--chart-3)" fillOpacity={0.2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="py-12 text-center text-[var(--text-muted)]">Upload files to see storage growth.</p>
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
