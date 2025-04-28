// app/(your‐layout)/reports/page.tsx
'use client'
import React, { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js'
import { Bar, Line } from 'react-chartjs-2'
import {
    FaDatabase,
    FaFilter,
    FaFileDownload,
    FaEye,
    FaCalendarAlt,
} from 'react-icons/fa'
import { useReports, HistoryItem } from '@/hooks/useReports'
import Loading from '@/components/Loading'

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
)

export default function ReportsPage() {
    const router = useRouter()
    const { data, isLoading, isError, error } = useReports()
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [selectedMetric, setMetric] = useState('All Metrics')

    // guard
    const rawHistory: HistoryItem[] = data?.history ?? []

    // filtered history
    const history = useMemo(() => {
        return rawHistory.filter((h) => {
            if (startDate && h.date < startDate) return false
            if (endDate && h.date > endDate) return false
            if (selectedMetric === 'Records Added') return h.recordsAdded > 0
            if (selectedMetric === 'Records Removed') return h.recordsRemoved > 0
            return true
        })
    }, [rawHistory, startDate, endDate, selectedMetric])

    // bar chart
    const barData = useMemo(() => ({
        labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
        datasets: [
            {
                label: 'Added',
                data: data?.recordsAddedPerWeek ?? [],
                backgroundColor: 'rgba(75,192,192,0.6)',
            },
            {
                label: 'Removed',
                data: data?.recordsRemovedPerWeek ?? [],
                backgroundColor: 'rgba(255,99,132,0.6)',
            },
        ],
    }), [data])

    // line chart
    const lineData = useMemo(() => {
        const labels = history.map((h) => h.date)
        const values = history.map((h) =>
            selectedMetric === 'Records Added' ? h.recordsAdded :
                selectedMetric === 'Records Removed' ? h.recordsRemoved :
                    h.totalRecords
        )
        return {
            labels,
            datasets: [{
                label: selectedMetric,
                data: values,
                borderColor: 'rgba(54,162,235,0.8)',
                backgroundColor: 'rgba(54,162,235,0.4)',
                fill: true,
                tension: 0.3,
            }],
        }
    }, [history, selectedMetric])

    // summary: last day
    const latest = rawHistory[rawHistory.length - 1]
    const summaryRows = latest ? [
        { metric: 'Total Records', value: data!.totalRecords, date: latest.date },
        { metric: 'Records Added', value: latest.recordsAdded, date: latest.date },
        { metric: 'Records Removed', value: latest.recordsRemoved, date: latest.date },
    ] : []

    // handlers
    const handleView = (date: string) => {
        router.push(`/dashboard/details?date=${date}`)
    }
    const handleDownload = (date: string) => {
        window.open(`/api/reports/csv?date=${date}`, '_blank')
    }

    if (isLoading) {
        return (
            <Loading />
        )
    }
    if (isError) {
        return (
            <div className="flex h-screen items-center justify-center bg-gray-900 text-red-400">
                <p>Error loading reports: {error?.message}</p>
            </div>
        )
    }

    return (
        <div className="p-4 md:p-8 bg-gray-900 text-white min-h-screen">
            <div className="max-w-5xl mx-auto space-y-6">
                {/* header */}
                <header className="flex flex-col md:flex-row items-start md:items-center justify-between">
                    <h1 className="text-3xl font-bold flex items-center">
                        <FaDatabase className="mr-2 text-green-400" /> Database Reports
                    </h1>
                    <button
                        className="mt-4 md:mt-0 flex items-center bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
                        onClick={() => window.open('/api/reports/csv', '_blank')}
                    >
                        <FaFileDownload className="mr-2" /> Export All CSV
                    </button>
                </header>

                {/* filters */}
                <section className="bg-gray-800 p-4 rounded-lg shadow-inner">
                    <h2 className="text-xl font-semibold flex items-center mb-3">
                        <FaFilter className="mr-2 text-yellow-400" /> Filter Reports
                    </h2>
                    <form
                        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                        onSubmit={(e) => e.preventDefault()}
                    >
                        <div className="flex items-center bg-gray-700 rounded px-3">
                            <FaCalendarAlt className="mr-2 text-gray-300" />
                            <input
                                type="date"
                                className="bg-transparent w-full py-2 focus:outline-none"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                            />
                        </div>
                        <div className="flex items-center bg-gray-700 rounded px-3">
                            <FaCalendarAlt className="mr-2 text-gray-300" />
                            <input
                                type="date"
                                className="bg-transparent w-full py-2 focus:outline-none"
                                value={endDate}
                                onChange={(e) => setEndDate(e.target.value)}
                            />
                        </div>
                        <select
                            className="bg-gray-700 rounded px-3 py-2"
                            value={selectedMetric}
                            onChange={(e) => setMetric(e.target.value)}
                        >
                            <option>All Metrics</option>
                            <option>Total Records</option>
                            <option>Records Added</option>
                            <option>Records Removed</option>
                        </select>
                        <button
                            type="button"
                            className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded"
                        >
                            Apply Filters
                        </button>
                    </form>
                </section>

                {/* bar chart */}
                <section className="bg-gray-800 p-4 rounded-lg shadow">
                    <h2 className="text-lg font-semibold mb-3">Record Changes Overview</h2>
                    <Bar data={barData} options={{ responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } }} />
                </section>

                {/* summary table */}
                <section className="bg-gray-800 p-4 rounded-lg shadow overflow-x-auto">
                    <h2 className="text-lg font-semibold mb-4">Database Metrics</h2>
                    <table className="w-full table-auto">
                        <thead>
                            <tr className="text-left text-gray-400">
                                <th className="px-3 py-2">Metric</th>
                                <th className="px-3 py-2">Value</th>
                                <th className="px-3 py-2">Date</th>
                                <th className="px-3 py-2 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {summaryRows.map((r) => (
                                <tr key={r.metric} className="border-t border-gray-700 hover:bg-gray-700">
                                    <td className="px-3 py-2">{r.metric}</td>
                                    <td className="px-3 py-2">{r.value}</td>
                                    <td className="px-3 py-2">{r.date}</td>
                                    <td className="px-3 py-2 text-center space-x-2">
                                        <FaEye
                                            className="inline cursor-pointer text-blue-400 hover:text-blue-200"
                                            onClick={() => handleView(r.date)}
                                        />
                                        <FaFileDownload
                                            className="inline cursor-pointer text-yellow-400 hover:text-yellow-200"
                                            onClick={() => handleDownload(r.date)}
                                        />
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </section>

                {/* line chart */}
                <section className="bg-gray-800 p-4 rounded-lg shadow">
                    <h2 className="text-lg font-semibold mb-3">{selectedMetric} Over Time</h2>
                    {history.length ? (
                        <Line data={lineData} options={{ responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } }} />
                    ) : (
                        <p className="text-center text-gray-400">No data to display</p>
                    )}
                </section>
            </div>
        </div>
    )
}
