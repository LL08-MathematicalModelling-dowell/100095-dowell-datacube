/* eslint-disable @typescript/no-explicit-any */
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Cell,
    Legend,
    Line,
    LineChart,
    Pie,
    PieChart,
    ResponsiveContainer,
    Tooltip,
    XAxis, YAxis
} from 'recharts';
import api from '../services/api';


const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const AnalyticsCharts = () => {
    const [activeTab, setActiveTab] = useState('overview');

    // Helper to safely unwrap API response
    const unwrapData = (response: any) => {
        // If the response has a 'data' property (axios interceptor)
        const inner = response.data ?? response;
        // If the inner object has a 'success' flag and 'data' property
        if (inner && typeof inner === 'object' && 'success' in inner && inner.success === true) {
            return inner.data ?? inner;
        }
        return inner;
    };

    // Dashboard query
    const { data: dashboardRaw, isLoading: dashboardLoading, error: dashboardError} = useQuery({
        queryKey: ['analytics', 'dashboard'],
        queryFn: async () => {
            const res = await api.get('/analytics/api/v2/dashboard/');
            const unwrapped = unwrapData(res);
            // Ensure we return at least an empty object
            return unwrapped || { overview: null, daily_requests: null };
        },
        retry: 1,
    });

    // Performance query
    const { data: performanceRaw, isLoading: perfLoading, error: perfError} = useQuery({
        queryKey: ['analytics', 'performance'],
        queryFn: async () => {
            const res = await api.get('/analytics/api/v2/performance/');
            const unwrapped = unwrapData(res);
            return unwrapped || { percentiles_ms: null, throughput_last_24h: [] };
        },
        retry: 1,
    });

    // Errors query
    const { data: errorsRaw, isLoading: errorsLoading, error: errorsError} = useQuery({
        queryKey: ['analytics', 'errors'],
        queryFn: async () => {
            const res = await api.get('/analytics/api/v2/errors/');
            const unwrapped = unwrapData(res);
            return unwrapped || { errors_by_status_code: {}, top_error_endpoints: [], error_types: {} };
        },
        retry: 1,
    });

    // Top collections query
    const { data: topCollectionsRaw, isLoading: topLoading, error: topError} = useQuery({
        queryKey: ['analytics', 'top-collections'],
        queryFn: async () => {
            const res = await api.get('/analytics/api/v2/top-collections/');
            const unwrapped = unwrapData(res);
            // Ensure we always return an object with top_collections array
            if (Array.isArray(unwrapped)) {
                return { top_collections: unwrapped };
            }
            if (unwrapped && unwrapped.top_collections) {
                return unwrapped;
            }
            return { top_collections: [] };
        },
        retry: 1,
    });
    const dashboard = dashboardRaw || { overview: null, daily_requests: null };
    const performance = performanceRaw || { percentiles_ms: null, throughput_last_24h: [] };
    const errors = errorsRaw || { errors_by_status_code: {}, top_error_endpoints: [], error_types: {} };
    const topCollections = topCollectionsRaw?.top_collections || [];

    const isLoading = dashboardLoading || perfLoading || errorsLoading || topLoading;
    const hasError = dashboardError || perfError || errorsError || topError;

    if (isLoading) {
        return <div className="text-slate-400">Loading analytics data...</div>;
    }

    if (hasError) {
        console.error('Analytics errors:', { dashboardError, perfError, errorsError, topError });
        return (
            <div className="text-red-400 p-4 bg-red-900/20 rounded-lg">
                Failed to load analytics. Please try again later.
                <button
                    onClick={() => window.location.reload()}
                    className="ml-4 underline hover:text-red-300"
                >
                    Retry
                </button>
            </div>
        );
    }

    // Prepare data (handle empty arrays)
    const dailyData = dashboard?.daily_requests.dates.map((date: any, idx: string | number) => ({
        date,
        requests: dashboard.daily_requests.counts[idx],
        avgDuration: dashboard.daily_requests.avg_durations_ms[idx],
    })) || [];

    const throughputData = performance?.throughput_last_24h || [];

    const errorStatusData = errors?.errors_by_status_code
        ? Object.entries(errors.errors_by_status_code).map(([code, count]) => ({ name: code, value: count }))
        : [];

    const topEndpoints = errors?.top_error_endpoints || [];

    const percentiles = performance?.percentiles_ms;

    return (
        <div>
            {/* Tabs */}
            <div className="border-b border-slate-700 mb-6">
                <nav className="flex space-x-4">
                    {['overview', 'performance', 'errors', 'collections'].map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-3 py-2 text-sm font-medium rounded-t-lg transition-colors ${activeTab === tab
                                    ? 'text-cyan-400 border-b-2 border-cyan-400 bg-slate-800/30'
                                    : 'text-slate-400 hover:text-slate-200'
                                }`}
                        >
                            {tab.charAt(0).toUpperCase() + tab.slice(1)}
                        </button>
                    ))}
                </nav>
            </div>

            {/* Tab content */}
            <div className="space-y-6">
                {/* Overview Tab */}
                {activeTab === 'overview' && (
                    <>
                        {/* KPI Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                <h3 className="text-sm font-medium text-slate-400">Total Requests (7d)</h3>
                                <p className="text-2xl font-bold text-cyan-400">
                                    {dashboard?.overview.total_requests?.toLocaleString() ?? 0}
                                </p>
                            </div>
                            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                <h3 className="text-sm font-medium text-slate-400">Avg Response Time</h3>
                                <p className="text-2xl font-bold text-emerald-400">
                                    {dashboard?.overview.avg_response_time_ms ?? 0} ms
                                </p>
                            </div>
                            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                <h3 className="text-sm font-medium text-slate-400">Error Rate</h3>
                                <p className="text-2xl font-bold text-rose-400">
                                    {dashboard?.overview.error_rate_percent ?? 0}%
                                </p>
                            </div>
                            <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                <h3 className="text-sm font-medium text-slate-400">Storage Used</h3>
                                <p className="text-2xl font-bold text-purple-400">
                                    {dashboard?.overview.total_storage_mb ?? 0} MB
                                </p>
                            </div>
                        </div>

                        {/* Daily Requests & Avg Duration */}
                        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                            <h2 className="text-xl font-semibold text-white mb-4">Daily API Requests & Response Time</h2>
                            {dailyData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={dailyData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="date" stroke="#94A3B8" />
                                        <YAxis yAxisId="left" stroke="#94A3B8" />
                                        <YAxis yAxisId="right" orientation="right" stroke="#94A3B8" />
                                        <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: 'none' }} />
                                        <Legend />
                                        <Line yAxisId="left" type="monotone" dataKey="requests" stroke="#38BDF8" name="Requests" strokeWidth={2} />
                                        <Line yAxisId="right" type="monotone" dataKey="avgDuration" stroke="#10B981" name="Avg Duration (ms)" strokeWidth={2} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-slate-400 text-center py-8">No request data available for the period.</div>
                            )}
                        </div>
                    </>
                )}

                {/* Performance Tab */}
                {activeTab === 'performance' && (
                    <>
                        {/* Percentiles */}
                        {percentiles && (
                            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                                <h2 className="text-xl font-semibold text-white mb-4">Response Time Percentiles (ms)</h2>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {Object.entries(percentiles).map(([key, value]) => (
                                        <div key={key} className="bg-slate-800 p-3 rounded text-center">
                                            <div className="text-xs text-slate-400 uppercase">{key}</div>
                                            <div className="text-xl font-bold text-cyan-400">{value as number} ms</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Throughput */}
                        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                            <h2 className="text-xl font-semibold text-white mb-4">Throughput (Requests per hour, last 24h)</h2>
                            {throughputData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={300}>
                                    <BarChart data={throughputData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="hour" stroke="#94A3B8" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                                        <YAxis stroke="#94A3B8" />
                                        <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: 'none' }} />
                                        <Bar dataKey="requests" fill="#38BDF8" />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-slate-400 text-center py-8">No throughput data available.</div>
                            )}
                        </div>
                    </>
                )}

                {/* Errors Tab */}
                {activeTab === 'errors' && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                            <h2 className="text-xl font-semibold text-white mb-4">Errors by Status Code</h2>
                            {errorStatusData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <PieChart>
                                        <Pie
                                            data={errorStatusData}
                                            cx="50%"
                                            cy="50%"
                                            labelLine={false}
                                            label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                                            outerRadius={80}
                                            fill="#8884d8"
                                            dataKey="value"
                                        >
                                            {errorStatusData.map((_entry, index) => (
                                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                            ))}
                                        </Pie>
                                        <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: 'none' }} />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-slate-400 text-center py-8">No errors recorded in the last 7 days.</div>
                            )}
                        </div>
                        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                            <h2 className="text-xl font-semibold text-white mb-4">Top Error‑Prone Endpoints</h2>
                            {topEndpoints.length > 0 ? (
                                <ResponsiveContainer width="100%" height={250}>
                                    <BarChart data={topEndpoints} layout="vertical">
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis type="number" stroke="#94A3B8" />
                                        <YAxis type="category" dataKey="path" stroke="#94A3B8" width={150} tick={{ fontSize: 11 }} />
                                        <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: 'none' }} />
                                        <Bar dataKey="errors" fill="#EF4444" />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="text-slate-400 text-center py-8">No error endpoints to display.</div>
                            )}
                        </div>
                    </div>
                )}

                {/* Collections Tab */}
                {activeTab === 'collections' && (
                    <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                        <h2 className="text-xl font-semibold text-white mb-4">Most Active Collections (by operations)</h2>
                        {topCollections && topCollections.length > 0 ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={topCollections}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="name" stroke="#94A3B8" />
                                    <YAxis stroke="#94A3B8" />
                                    <Tooltip contentStyle={{ backgroundColor: '#1E293B', border: 'none' }} />
                                    <Bar dataKey="operations" fill="#A855F7" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="text-slate-400 text-center py-8">No collection activity yet.</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalyticsCharts;