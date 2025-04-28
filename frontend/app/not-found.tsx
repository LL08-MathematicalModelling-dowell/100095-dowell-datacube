// app/not-found.tsx
'use client';
import Link from 'next/link';
import { FaExclamationTriangle } from 'react-icons/fa';

export default function NotFound() {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-900 text-white p-4">
            <FaExclamationTriangle className="text-6xl text-yellow-400 mb-6 animate-pulse" />
            <h1 className="text-3xl sm:text-5xl font-bold mb-4">404 — Page Not Found</h1>
            <p className="text-gray-400 mb-6 text-center">
                Sorry, we couldn’t find the page you’re looking for.
            </p>
            <Link href="/" className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white transition">
                Go Home
            </Link>
        </div>
    );
}