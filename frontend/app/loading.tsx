// app/loading.tsx
'use client';

import { FaSpinner } from 'react-icons/fa';

export default function Loading() {
    return (
        <div className="fixed inset-0 flex flex-col items-center justify-center bg-gray-900 text-white">
            {/* App Logo/Name */}
            <h1 className="text-2xl sm:text-4xl font-bold mb-6">DataCube</h1>

            {/* Spinner */}
            <FaSpinner className="animate-spin text-4xl sm:text-6xl" />

            {/* Optional “Loading…” text */}
            <p className="mt-4 text-sm sm:text-base text-gray-400">Loading… please wait</p>

            {/* Skeleton / placeholder blocks */}
            <div className="mt-8 w-11/12 sm:w-3/4 lg:w-1/2 space-y-4 animate-pulse">
                <div className="h-6 bg-gray-800 rounded w-1/3 mx-auto" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="h-40 bg-gray-800 rounded" />
                    <div className="h-40 bg-gray-800 rounded" />
                    <div className="h-40 bg-gray-800 rounded" />
                </div>
            </div>
        </div>
    );
}