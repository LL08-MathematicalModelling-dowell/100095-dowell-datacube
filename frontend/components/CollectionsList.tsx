/* eslint-disable @typescript-eslint/no-explicit-any */
// components/CollectionsList.tsx
'use client'
import { Collection } from '@/hooks/useCollections'
import { Input, Spinner } from '@chakra-ui/react'
import { AnimatePresence, motion } from 'framer-motion'
import Link from 'next/link'
import { useMemo, useState } from 'react'
import { FaExclamationTriangle, FaFolder, FaSearch } from 'react-icons/fa'

interface CollectionsListProps {
    databaseId: string
    collections: Collection[]
    isLoading: boolean
    error: any
}

export default function CollectionsList({
    databaseId,
    collections,
    isLoading,
    error,
}: CollectionsListProps) {
    const [filter, setFilter] = useState('')

    // Filter & sort
    const visible = useMemo(() => {
        return collections
            .filter((c) =>
                c.name.toLowerCase().includes(filter.trim().toLowerCase())
            )
            .sort((a, b) => a.name.localeCompare(b.name))
    }, [collections, filter])

    return (
        <div className="relative min-h-screen bg-gray-900 text-gray-100 overflow-hidden">
            {/* Decorative rotating blob */}
            <motion.div
                className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-pink-600 rounded-full mix-blend-screen opacity-30 filter blur-3xl"
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 30, ease: 'linear' }}
            />

            <div className="relative z-10 max-w-7xl mx-auto px-4 py-10">
                {/* Header */}
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 gap-4">
                    <h1 className="text-3xl md:text-4xl font-extrabold text-white">
                        Collections
                    </h1>

                    <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
                        <div className="relative flex-1">
                            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                            <Input
                                placeholder="Search collections…"
                                value={filter}
                                onChange={(e) => setFilter(e.target.value)}
                                bg="gray.800"
                                color="white"
                                _placeholder={{ color: 'gray.500' }}
                                ps="10"
                            />
                        </div>
                        {/* <button
                            onClick={onAddCollection}
                            className="inline-flex items-center justify-center bg-pink-500 hover:bg-pink-400 text-white px-5 py-3 rounded-full shadow-lg transition"
                        >
                            <FaPlus className="mr-2" /> New Collection
                        </button> */}
                    </div>
                </div>

                {/* Error */}
                {error && (
                    <div className="flex items-center mb-6 p-4 bg-red-600 rounded-lg shadow">
                        <FaExclamationTriangle className="mr-3 text-xl" />
                        <span className="font-medium">
                            Error loading collections: {error.message}
                        </span>
                    </div>
                )}

                {/* Loading */}
                {isLoading && !error && (
                    <div className="flex justify-center py-20">
                        <Spinner size="xl" color="pink.400" />
                    </div>
                )}

                {/* No results */}
                {!isLoading && visible.length === 0 && (
                    <div className="py-20 text-center text-gray-500">
                        No collections found.
                    </div>
                )}

                {/* Grid */}
                <AnimatePresence>
                    {!isLoading && visible.length > 0 && (
                        <motion.div
                            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
                            initial="hidden"
                            animate="visible"
                            variants={{
                                hidden: {},
                                visible: { transition: { staggerChildren: 0.1 } },
                            }}
                        >
                            {visible.map((col) => (
                                <motion.div
                                    key={col.name}
                                    className="bg-gray-800 rounded-2xl p-6 shadow-xl flex flex-col h-full hover:scale-105 transition"
                                    variants={{
                                        hidden: { opacity: 0, y: 20 },
                                        visible: { opacity: 1, y: 0 },
                                    }}
                                >
                                    <Link
                                        href={`/dashboard/databases/${databaseId}/${col.name}`}
                                        className="flex-1 flex flex-col"
                                    >
                                        <div className="flex items-center mb-4">
                                            <FaFolder className="text-yellow-400 mr-3" size={28} />
                                            <h2 className="text-xl font-semibold text-white">
                                                {col.name}
                                            </h2>
                                        </div>
                                        <p className="text-gray-400 mb-6">
                                            Documents: <strong className="text-white">{col.numDocuments}</strong>
                                        </p>
                                    </Link>
                                    <Link
                                        href={`/dashboard/databases/${databaseId}/${col.name}`}
                                        className="mt-auto inline-block text-center py-2 bg-yellow-400 hover:bg-yellow-300 text-gray-900 rounded-full font-medium transition"
                                    >
                                        View
                                    </Link>
                                </motion.div>
                            ))}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}