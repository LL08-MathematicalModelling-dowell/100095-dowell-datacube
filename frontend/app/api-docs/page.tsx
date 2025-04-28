'use client'
import { Footer } from '@/components/Footer'
import { Navbar } from '@/components/NavBar'
import { motion } from 'framer-motion'
import {
    FaChartBar,
    FaDatabase,
    FaFileAlt,
    FaFolder,
    FaKey,
    FaLayerGroup,
} from 'react-icons/fa'


const endpoints = [
    {
        group: 'Databases',
        items: [
            {
                title: 'List Databases',
                method: 'GET',
                path: '/api/database',
                description: 'Return all databases you own.',
                request: `curl -H "datacube-key: YOUR_API_KEY" \
  https://your-domain.com/api/database`,
                response: `{
  "success": true,
  "data": [
    { "id": "db1", "name": "customers", ... },
    { "id": "db2", "name": "orders", ... }
  ]
}`,
            },
            {
                title: 'Create Database',
                method: 'POST',
                path: '/api/database',
                description: 'Create a new database under your account.',
                request: `curl -X POST -H "Content-Type: application/json" \\
     -H "datacube-key: YOUR_API_KEY" \\
     -d '{"name":"my_new_db"}' \\
     https://your-domain.com/api/database`,
                response: `{
  "success": true,
  "data": { "id": "db3", "name": "my_new_db", ... }
}`,
            },
        ],
    },
    {
        group: 'Collections',
        items: [
            {
                title: 'List Collections',
                method: 'GET',
                path: '/api/database/{dbId}/collections',
                description: 'Page and filter collections in a database.',
                request: `curl -H "datacube-key: YOUR_API_KEY" \\
  "https://your-domain.com/api/database/db1/collections?page=1&pageSize=10"`,
                response: `{
  "success": true,
  "data": [
    { "id":"col1","name":"users","createdAt":"..."},
    ...
  ],
  "pagination": { "page":1,"pageSize":10,"total":4 }
}`,
            },
            {
                title: 'Create Collection',
                method: 'POST',
                path: '/api/database/{dbId}/collections',
                description: 'Create a new collection in the database.',
                request: `curl -X POST -H "Content-Type: application/json" \\
  -H "datacube-key: YOUR_API_KEY" \\
  -d '{"name":"products"}' \\
  https://your-domain.com/api/database/db1/collections`,
                response: `{
  "success": true,
  "data": { "id":"col5","name":"products","createdAt":"..." }
}`,
            },
        ],
    },
    {
        group: 'Documents',
        items: [
            {
                title: 'List Documents',
                method: 'GET',
                path: '/api/database/{dbId}/collections/{collName}',
                description: 'Page & filter JSON documents.',
                request: `curl -H "datacube-key: YOUR_API_KEY" \\
  "https://your-domain.com/api/database/db1/collections/users?page=2&pageSize=5&filters={\"active\":true}"`,
                response: `{
  "success": true,
  "data": [
    { "_id":"60a...", "email":"jane@…", "active":true },
    …
  ],
  "pagination": { "page":2,"pageSize":5,"total":23 }
}`,
            },
            {
                title: 'Create Document(s)',
                method: 'POST',
                path: '/api/database/{dbId}/collections/{collName}',
                description: 'Insert one or more JSON documents.',
                request: `curl -X POST -H "Content-Type: application/json" \\
  -H "datacube-key: YOUR_API_KEY" \\
  -d '[{"name":"Alice"},{"name":"Bob"}]' \\
  https://your-domain.com/api/database/db1/collections/customers`,
                response: `{
  "success": true,
  "message": "Bulk insert OK",
  "insertedCount": 2
}`,
            },
            {
                title: 'Update Document',
                method: 'PUT',
                path: '/api/database/{dbId}/collections/{collName}',
                description: 'Update a single document by its `_id`.',
                request: `curl -X PUT -H "Content-Type: application/json" \\
  -H "datacube-key: YOUR_API_KEY" \\
  -d '{"_id":"60a...","role":"admin"}' \\
  https://your-domain.com/api/database/db1/collections/users`,
                response: `{
  "success": true,
  "message": "Document updated successfully."
}`,
            },
            {
                title: 'Delete Document',
                method: 'DELETE',
                path: '/api/database/{dbId}/collections/{collName}',
                description: 'Delete a document by its `_id`.',
                request: `curl -X DELETE -H "Content-Type: application/json" \\
  -H "datacube-key: YOUR_API_KEY" \\
  -d '{"documentId":"60a..."}' \\
  https://your-domain.com/api/database/db1/collections/users`,
                response: `{
  "success": true,
  "message": "Document deleted successfully."
}`,
            },
        ],
    },
    {
        group: 'Reporting',
        items: [
            {
                title: 'Get Reports',
                method: 'GET',
                path: '/api/reports',
                description:
                    'Weekly & daily metrics: totalRecords, recordsAddedPerWeek, history.',
                request: `curl -H "datacube-key: YOUR_API_KEY" \\
  https://your-domain.com/api/reports`,
                response: `{
  "success": true,
  "data": {
    "totalRecords": 5234,
    "recordsAddedPerWeek": [10,23,15,7],
    "recordsRemovedPerWeek":[2,5,1,0],
    "history": [
      { "date":"2024-01-01","recordsAdded":3,"recordsRemoved":0,"totalRecords":5234 },
      …
    ]
  }
}`,
            },
            {
                title: 'Get Stats',
                method: 'GET',
                path: '/api/stats',
                description:
                    'Summary counts: databases, collections, documents, reads/writes per day/month.',
                request: `curl -H "datacube-key: YOUR_API_KEY" \\
  https://your-domain.com/api/stats`,
                response: `{
  "success": true,
  "data": {
    "databases":3,
    "collections":12,
    "documents":10428,
    "readsPerDay":[15,23,19,22,14,18,21],
    "writesPerDay":[3,2,5,1,0,4,2],
    "readsPerMonth":[420,380,455,500,470,430,395],
    "writesPerMonth":[45,38,52,60,48,39,27]
  }
}`,
            },
        ],
    },
]


// Define your sidebar sections with icons
const sections = [
    { id: 'authentication', label: 'Authentication', icon: <FaKey /> },
    { id: 'quickstart', label: 'Quickstart', icon: <FaLayerGroup /> },
    { id: 'databases', label: 'Databases', icon: <FaDatabase /> },
    { id: 'collections', label: 'Collections', icon: <FaFolder /> },
    { id: 'documents', label: 'Documents', icon: <FaFileAlt /> },
    { id: 'reporting', label: 'Reporting', icon: <FaChartBar /> },
]

export default function ApiDocsPage() {
    return (
        <div className="min-h-screen bg-gray-900 text-gray-100 font-sans">
            <Navbar />

            {/* Hero */}
            <section className="relative text-center py-24 bg-gradient-to-br from-purple-800 to-indigo-900">
                <motion.h1
                    className="text-5xl md:text-6xl font-extrabold mb-4"
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                >
                    DataCube REST API Docs
                </motion.h1>
                <motion.p
                    className="text-lg text-gray-300 max-w-2xl mx-auto"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                >
                    Authenticate with an API key or NextAuth session. All endpoints return
                    a JSON envelope with `success`, `data`, optional `error` and pagination.
                </motion.p>
            </section>

            <div className="flex">
                {/* Sidebar (md+) */}
                <nav className="hidden md:block w-60 bg-gray-800 sticky top-0 h-screen p-4 overflow-y-auto">
                    <ul className="space-y-2">
                        {sections.map(({ id, label, icon }) => (
                            <li key={id}>
                                <a
                                    href={`#${id}`}
                                    className="flex items-center px-3 py-2 rounded-lg transition-colors hover:bg-gray-700"
                                >
                                    <span className="text-pink-400 mr-3">{icon}</span>
                                    <span className="text-gray-300 hover:text-white">{label}</span>
                                </a>
                            </li>
                        ))}
                    </ul>
                </nav>

                <div className="flex-1 px-4 md:px-8 py-16 max-w-5xl mx-auto">
                    {/* Mobile pill nav */}
                    <div className="md:hidden mb-8 overflow-x-auto">
                        <div className="flex space-x-3 text-sm">
                            {sections.map(({ id, label }) => (
                                <a
                                    key={id}
                                    href={`#${id}`}
                                    className="px-3 py-1 bg-gray-800 rounded-full whitespace-nowrap text-gray-300 hover:bg-gray-700"
                                >
                                    {label}
                                </a>
                            ))}
                        </div>
                    </div>

                    {/* Authentication */}
                    <motion.section
                        id="authentication"
                        className="mb-16"
                        initial={{ x: -30, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        viewport={{ once: true }}
                    >
                        <h2 className="flex items-center mb-4 text-2xl font-bold">
                            <FaKey size={24} className="text-yellow-400 mr-2" />
                            Authentication
                        </h2>
                        <p className="text-gray-300 mb-4">
                            Provide your API key in the `datacube-key` header:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`fetch('/api/database', {
  headers: {
    'datacube-key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
  }
})`}
                        </pre>
                        <p className="text-gray-300 mt-4">
                            Internally, we resolve the user via:
                        </p>
                        <pre className="bg-gray-800 p-4 rounded text-sm overflow-x-auto">
                            {`// lib/getUserId.ts
export const getUserId = async () => {
  const session = await auth()
  if (session?.user?.email) {
    const u = await prisma.user.findUnique({ where: { email: session.user.email } })
    return u?.id
  }
  const hdrs = await headers()
  const key = hdrs.get('datacube-key')
  if (key) {
    const hash = crypto.createHash('sha256').update(key).digest('hex')
    const rec = await prisma.apiKey.findUnique({ where: { key: hash } })
    return rec?.userId ?? null
  }
  return null
}`}
                        </pre>
                    </motion.section>

                    {/* Databases, Collections, Documents, Reporting */}
                    {endpoints.map((grp, gi) => {
                        // match sections[gi+1] → skip authentication & quickstart
                        const sec = sections[gi + 2]
                        return (
                            <motion.section
                                key={grp.group}
                                id={sec?.id}
                                className="mb-16"
                                initial={{ opacity: 0 }}
                                whileInView={{ opacity: 1 }}
                                viewport={{ once: true }}
                            >
                                <h2 className="text-3xl font-bold mb-6">{grp.group}</h2>
                                <div className="space-y-8">
                                    {grp.items.map((ep, i) => (
                                        <div
                                            key={i}
                                            className="bg-gray-800 p-6 rounded-2xl shadow-lg"
                                        >
                                            <div className="flex justify-between items-center mb-2">
                                                <span
                                                    className={`text-sm font-mono px-2 py-1 rounded ${ep.method === 'GET'
                                                        ? 'bg-green-600'
                                                        : ep.method === 'POST'
                                                            ? 'bg-blue-600'
                                                            : ep.method === 'PUT'
                                                                ? 'bg-yellow-600'
                                                                : ep.method === 'DELETE'
                                                                    ? 'bg-red-600'
                                                                    : 'bg-gray-600'
                                                        }`}
                                                >
                                                    {ep.method}
                                                </span>
                                                <code className="font-mono text-gray-300">
                                                    {ep.path}
                                                </code>
                                            </div>
                                            <h3 className="text-xl font-semibold text-white mb-2">
                                                {ep.title}
                                            </h3>
                                            <p className="text-gray-400 mb-4">{ep.description}</p>
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div>
                                                    <h4 className="font-semibold mb-1">Request</h4>
                                                    <pre className="bg-gray-900 p-3 rounded text-sm overflow-x-auto">
                                                        {ep.request}
                                                    </pre>
                                                </div>
                                                <div>
                                                    <h4 className="font-semibold mb-1">Response</h4>
                                                    <pre className="bg-gray-900 p-3 rounded text-sm overflow-x-auto">
                                                        {ep.response}
                                                    </pre>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </motion.section>
                        )
                    })}

                    <Footer />
                </div>
            </div>
        </div>
    )
}