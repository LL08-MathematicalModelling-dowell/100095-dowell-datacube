'use client';
import { FaSpinner } from 'react-icons/fa';

export default function Loading() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 p-4">
            {/* <h2 className="text-2xl sm:text-4xl font-semibold text-white mb-6">Dashboard</h2> */}
            <FaSpinner className="text-5xl sm:text-7xl text-blue-500 animate-spin mb-6" />
            <div className="w-full max-w-4xl grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
                {[...Array(6)].map((_, idx) => (
                    <div key={idx} className="h-40 bg-gray-800 rounded-lg" />
                ))}
            </div>
        </div>
    );
}