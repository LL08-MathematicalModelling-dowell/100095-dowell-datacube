// app/docs/page.tsx
'use client'
import React from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import {
    FaKey,
    FaLayerGroup,
    FaFileAlt,
    FaChartBar,
} from 'react-icons/fa'
import { Footer } from '@/components/Footer'
import { Navbar } from '@/components/NavBar'

const endpoints = [
    {
        title: 'List Databases',
        method: 'GET',
        path: '/api/database',
        desc: 'Returns all databases you have access to.',
        example: `fetch('/api/database', {
  headers: { 'datacube-key': YOUR_API_KEY }
})`,
    },
    {
        title: 'List Collections',
        method: 'GET',
        path: '/api/database/{dbId}/collections',
        desc: 'Returns paginated collections in a database.',
        example: `fetch(\`/api/database/\${dbId}/?page=1&pageSize=10\`, {
  headers: { 'datacube-key': YOUR_API_KEY }
})`,
    },
    {
        title: 'Create Document(s)',
        method: 'POST',
        path: '/api/database/{dbId}/{collName}',
        desc: 'Insert one or more JSON documents.',
        example: `fetch(\`/api/database/\${dbId}/\${collName}/users\`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'datacube-key': YOUR_API_KEY
  },
  body: JSON.stringify({ email: 'jane@example.com' })
})`,
    },
    {
        title: 'Update Document',
        method: 'PUT',
        path: '/api/database/{dbId}/{collName}',
        desc: 'Update a single document by `_id`.',
        example: `fetch(\`/api/database/\${dbId}/{collName}/users\`, {
  method: 'PUT',
  headers: {
    'Content-Type': 'application/json',
    'datacube-key': YOUR_API_KEY
  },
  body: JSON.stringify({ _id: 'abc123', role: 'admin' })
})`,
    },
    {
        title: 'Delete Document',
        method: 'DELETE',
        path: '/api/database/{dbId}/{collName}',
        desc: 'Delete a single document by `_id`.',
        example: `fetch(\`/api/database/\${dbId}/{collName}/users\`, {
  method: 'DELETE',
  headers: {
    'Content-Type': 'application/json',
    'datacube-key': YOUR_API_KEY
  },
  body: JSON.stringify({ documentId: 'abc123' })
})`,
    },
    {
        title: 'Get Reports',
        method: 'GET',
        path: '/api/reports',
        desc: 'Returns weekly & daily report data: `totalRecords`, `recordsAddedPerWeek`, `history`.',
        example: `fetch('/api/reports', {
  headers: { 'datacube-key': YOUR_API_KEY }
})`,
    },
    {
        title: 'Get Stats',
        method: 'GET',
        path: '/api/stats',
        desc: 'Returns aggregated counts: databases, collections, documents, reads/writes by day/month.',
        example: `fetch('/api/stats', {
  headers: { 'datacube-key': YOUR_API_KEY }
})`,
    },
]

const sections = [
    { id: 'authentication', title: 'Authentication', icon: <FaKey size={20} /> },
    { id: 'quickstart', title: 'Quickstart', icon: <FaLayerGroup size={20} /> },
    { id: 'endpoints', title: 'Endpoints', icon: <FaFileAlt size={20} /> },
    { id: 'response-formats', title: 'Response Formats', icon: <FaChartBar size={20} /> },
]

export default function DocsPage() {
    return (
        <div className="font-sans text-gray-100 bg-gray-900">
            <Navbar />

            {/* Hero */}
            <section className="relative pt-32 pb-16 text-center bg-gradient-to-br from-pink-600 to-purple-700">
                <motion.h1
                    className="text-5xl md:text-6xl font-extrabold mb-4"
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                >
                    DataCube API Documentation
                </motion.h1>
                <motion.p
                    className="max-w-2xl mx-auto text-lg text-gray-200"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                >
                    Everything you need to integrate, manage, and report on your data.
                </motion.p>
            </section>

            <div className="flex">
                {/* Sidebar nav for md+ */}
                <nav className="hidden md:block w-60 py-8 px-4 sticky top-0 self-start h-screen bg-gray-800">
                    <ul className="space-y-4">
                        {sections.map(({ id, title, icon }) => (
                            <li key={id}>
                                <a
                                    href={`#${id}`}
                                    className="flex items-center text-gray-300 hover:text-white transition"
                                >
                                    <span className="mr-2">{icon}</span>
                                    {title}
                                </a>
                            </li>
                        ))}
                    </ul>
                </nav>

                <div className="flex-1 px-4 md:px-8 py-16 max-w-4xl mx-auto">
                    {/* mobile top nav */}
                    <div className="md:hidden mb-6 overflow-x-auto">
                        <div className="flex space-x-4 text-sm">
                            {sections.map(({ id, title }) => (
                                <a
                                    key={id}
                                    href={`#${id}`}
                                    className="px-3 py-1 bg-gray-800 rounded-full whitespace-nowrap text-gray-300 hover:bg-gray-700"
                                >
                                    {title}
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Sections */}
                    <motion.section
                        id="authentication"
                        className="mb-20"
                        initial={{ x: -30, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="flex items-center mb-4 text-3xl font-bold">
                            <FaKey size={28} className="text-yellow-400 mr-3" />
                            Authentication
                        </h2>
                        <p className="text-gray-300 mb-4">
                            You can authenticate either via NextAuth session cookies or your
                            API key. To use an API key, include:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`fetch('/api/your-endpoint', {
  headers: {
    'datacube-key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
  }
})`}
                        </pre>
                        <p className="text-gray-300 mt-4">
                            The server uses this helper to resolve your user:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`// lib/getUserId.ts
export const getUserId = async () => {
  // tries NextAuth
  const session = await auth();
  if (session?.user?.email) {
    const u = await prisma.user.findUnique({ where: { email: session.user.email } });
    return u?.id;
  }
  // else check API key header
  const hdrs = await headers();
  const apiKey = hdrs.get('datacube-key');
  if (apiKey) {
    const hash = crypto.createHash('sha256').update(apiKey).digest('hex');
    const rec = await prisma.apiKey.findUnique({ where: { key: hash } });
    return rec?.userId || null;
  }
  return null;
}`}
                        </pre>
                    </motion.section>

                    <motion.section
                        id="quickstart"
                        className="mb-20"
                        initial={{ x: 30, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="flex items-center mb-4 text-3xl font-bold">
                            <FaLayerGroup size={28} className="text-green-400 mr-3" />
                            Quickstart
                        </h2>
                        <p className="text-gray-300 mb-4">
                            Install our NPM package and get going in a few lines:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto mb-6">
                            {`npm install dowell-datacube

import DataCube from 'dowell-datacube'

const api = new DataCube({ apiKey: 'YOUR_API_KEY' })

async function main() {
  const dbs = await api.get('/database')
  console.log(dbs)
}

main()`}
                        </pre>
                        <Link
                            href="/api-docs"
                            className="inline-block px-6 py-3 bg-green-400 text-gray-900 font-semibold rounded-lg hover:bg-green-300 transition"
                        >
                            Full API Client Docs →
                        </Link>
                    </motion.section>

                    <motion.section
                        id="endpoints"
                        className="mb-20"
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="flex items-center mb-6 text-3xl font-bold">
                            <FaFileAlt size={28} className="text-blue-400 mr-3" />
                            Endpoints
                        </h2>
                        <div className="space-y-8">
                            {endpoints.map((ep, i) => (
                                <motion.div
                                    key={i}
                                    className="bg-gray-800 p-6 rounded-lg shadow-lg"
                                    initial={{ y: 20, opacity: 0 }}
                                    whileInView={{ y: 0, opacity: 1 }}
                                    transition={{ delay: i * 0.1 }}
                                >
                                    <div className="flex items-baseline justify-between mb-2">
                                        <span className="text-sm font-mono text-green-300">
                                            {ep.method}
                                        </span>
                                        <code className="font-mono text-gray-300">{ep.path}</code>
                                    </div>
                                    <h3 className="text-xl font-semibold text-white mb-2">
                                        {ep.title}
                                    </h3>
                                    <p className="text-gray-400 mb-3">{ep.desc}</p>
                                    <pre className="bg-gray-900 p-4 rounded text-sm overflow-x-auto">
                                        {ep.example}
                                    </pre>
                                </motion.div>
                            ))}
                        </div>
                    </motion.section>

                    <motion.section
                        id="response-formats"
                        className="mb-20"
                        initial={{ x: -30, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="flex items-center mb-6 text-3xl font-bold">
                            <FaChartBar size={28} className="text-yellow-400 mr-3" />
                            Response Formats
                        </h2>
                        <p className="text-gray-300 mb-4">
                            All endpoints return JSON with this shape:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`{
  success: boolean,
  data: any | { ... },
  error?: string,
  pagination?: { page: number, pageSize: number, total: number }
}`}
                        </pre>
                        <p className="text-gray-300 mt-4">
                            Example: listing collections:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`{
  success: true,
  data: [
    { id: "coll1", name: "users", createdAt: "...", metadata: {...} },
    ...
  ],
  pagination: { page: 1, pageSize: 10, total: 42 }
}`}
                        </pre>
                    </motion.section>

                    <Footer />
                </div>
            </div>
        </div>
    )
}