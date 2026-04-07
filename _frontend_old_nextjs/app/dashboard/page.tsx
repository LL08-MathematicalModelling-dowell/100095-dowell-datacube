'use client';
import Loading from '@/components/Loading';
import { useStats } from '@/hooks/useStats';
import { Chart, registerables } from 'chart.js';
import { useSession } from "next-auth/react";
import { redirect } from 'next/navigation';
import React from 'react';
import { Bar } from 'react-chartjs-2';
import {
  FaChartBar,
  FaDatabase,
  FaFileAlt,
  FaFolder,
  FaTasks,
} from 'react-icons/fa';

Chart.register(...registerables);

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

/**
 * Generate the last `count` month‐abbreviations,
 * ending with the current month.
 */
function getLastMonthsLabels(count: number): string[] {
  const labels: string[] = [];
  const now = new Date();
  for (let i = count - 1; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    labels.push(
      d.toLocaleString('default', {
        month: 'short',
      })
    );
  }
  return labels;
}

export default function StatsDashboard() {
  const { status } = useSession();
  const { data, isError, isLoading, error } = useStats();

  if (status === "loading") return null;

  if (status === "unauthenticated") redirect("/auth/login");

  if (isLoading) {
    return (
      <Loading />
    );
  }
  if (isError || !data) {
    return (
      <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-red-400">
        <p className="text-xl">Error loading stats</p>
        <p>{error?.message}</p>
      </div>
    );
  }

  // Always expect 7 days from your API
  const readsPerDay = data.readsPerDay.length === 7
    ? data.readsPerDay
    : Array(7).fill(0);
  const writesPerDay = data.writesPerDay.length === 7
    ? data.writesPerDay
    : Array(7).fill(0);

  // Use whatever length the API returned
  const readsPerMonth = data.readsPerMonth.length > 0
    ? data.readsPerMonth
    : Array(7).fill(0);
  const writesPerMonth = data.writesPerMonth.length > 0
    ? data.writesPerMonth
    : Array(7).fill(0);

  // Now generate exactly N month‐labels
  const monthLabels = getLastMonthsLabels(readsPerMonth.length);

  return (
    <div className="p-6 bg-gray-900 text-white min-h-screen space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {/* Top stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {[
          {
            label: 'Databases',
            value: data.databases,
            icon: <FaDatabase className="text-green-400" />,
          },
          {
            label: 'Collections',
            value: data.collections,
            icon: <FaFolder className="text-blue-400" />,
          },
          {
            label: 'Documents',
            value: data.documents,
            icon: <FaFileAlt className="text-purple-400" />,
          },
          {
            label: 'Popular DB',
            value: data.mostFrequentDb ?? '-',
            icon: <FaDatabase className="text-orange-400" />,
          },
          {
            label: 'Popular Coll',
            value: data.mostFrequentCollection ?? '-',
            icon: <FaFolder className="text-red-400" />,
          },
        ].map((stat, i) => (
          <div
            key={i}
            className="bg-gray-800 rounded-lg p-5 flex items-center hover:shadow-lg transition"
          >
            <div className="text-3xl mr-4">{stat.icon}</div>
            <div>
              <div className="text-sm text-gray-300">{stat.label}</div>
              <div className="text-2xl font-semibold">{stat.value}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Operation summaries */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <SummaryCard
          icon={<FaTasks className="text-blue-400 text-3xl mr-4" />}
          label="Reads (Last 7 days)"
          total={readsPerDay.reduce((a, b) => a + b, 0)}
        />
        <SummaryCard
          icon={<FaTasks className="text-purple-400 text-3xl mr-4" />}
          label="Writes (Last 7 days)"
          total={writesPerDay.length}
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <ChartCard
          title="Reads / Day"
          labels={WEEK_DAYS}
          dataset={readsPerDay}
          color="rgba(75,192,192,0.6)"
        />
        <ChartCard
          title="Writes / Day"
          labels={WEEK_DAYS}
          dataset={writesPerDay}
          color="rgba(153,102,255,0.6)"
        />
        <ChartCard
          title="Reads / Month"
          labels={monthLabels}
          dataset={readsPerMonth}
          color="rgba(75,192,192,0.6)"
        />
        <ChartCard
          title="Writes / Month"
          labels={monthLabels}
          dataset={writesPerMonth}
          color="rgba(153,102,255,0.6)"
        />
      </div>
    </div>
  );
}

type SummaryCardProps = {
  icon: React.ReactNode;
  label: string;
  total: number;
};
function SummaryCard({ icon, label, total }: SummaryCardProps) {
  return (
    <div className="bg-gray-800 p-5 rounded-lg flex items-center">
      {icon}
      <div>
        <div className="text-sm text-gray-300">{label}</div>
        <div className="text-xl font-semibold">{total}</div>
      </div>
    </div>
  );
}

type ChartCardProps = {
  title: string;
  labels: string[];
  dataset: number[];
  color: string;
};
function ChartCard({ title, labels, dataset, color }: ChartCardProps) {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md">
      <h2 className="flex items-center text-lg font-semibold mb-3">
        <FaChartBar className="mr-2" /> {title}
      </h2>
      <Bar
        data={{
          labels,
          datasets: [
            {
              label: title,
              data: dataset,
              backgroundColor: color,
              borderColor: color.replace(/0\.6/, '1'),
              borderWidth: 1,
            },
          ],
        }}
        options={{
          responsive: true,
          scales: { y: { beginAtZero: true } },
        }}
      />
    </div>
  );
}

