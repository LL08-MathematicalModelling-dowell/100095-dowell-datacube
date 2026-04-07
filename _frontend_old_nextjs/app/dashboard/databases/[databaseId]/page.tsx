// app/dashboard/databases/[databaseId]/page.tsx
'use client'
import React, { useState, useEffect } from 'react'
import { use } from 'react'
import Link from 'next/link'
import { useSession } from 'next-auth/react'
import { redirect, useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { FaCopy, FaDatabase } from 'react-icons/fa'
import CollectionsList from '@/components/CollectionsList'
import CreateCollectionModal from '@/components/CreateCollectionModal'
import Loading from '@/components/Loading'
import { Toaster, toaster } from '@/components/ui/toaster'
import { Tooltip } from '@/components/ui/tooltip'
import {
    Collection,
    useCollections,
    useCreateCollection,
} from '@/hooks/useCollections'

interface DatabasePageProps {
    params: Promise<{ databaseId: string }>
}

export default function DatabasePage({ params }: DatabasePageProps) {
    const { status } = useSession()
    const router = useRouter()
    const { databaseId } = use(params)

    // require auth
    useEffect(() => {

        if (status === 'unauthenticated') redirect('/auth/login')
    }, [status, router])

    const { data, isLoading, isError, error } = useCollections(databaseId)
    const collections: Collection[] = data?.collections ?? []

    const createColl = useCreateCollection(databaseId)
    const [modalOpen, setModalOpen] = useState(false)

    if (status === 'loading') return null;
    if (isLoading) return <Loading />

    const handleAdd = () => setModalOpen(true)
    const handleClose = (newCol: { name: string; fields: string[] } | null) => {
        setModalOpen(false)
        if (newCol) {
            toaster.promise(
                createColl.mutateAsync(newCol),
                {
                    loading: { title: 'Creating...', description: newCol.name },
                    success: { title: 'Created!', description: newCol.name },
                    error: { title: 'Failed', description: newCol.name },
                }
            )
        }
    }

    const copyId = async () => {
        try {
            await navigator.clipboard.writeText(databaseId)
            toaster.success({ title: 'Copied!', description: 'Database ID' })
        } catch {
            toaster.error({ title: 'Copy failed' })
        }
    }

    return (
        <div className="relative min-h-screen bg-gray-900 text-white overflow-hidden">
            {/* Background blob */}
            <motion.div
                className="absolute top-0 right-0 w-[600px] h-[600px] bg-indigo-600 rounded-full mix-blend-screen opacity-20 filter blur-3xl"
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 50, ease: 'linear' }}
            />

            <div className="relative z-10 max-w-7xl mx-auto px-4 py-12">
                {/* Breadcrumb */}
                <motion.nav
                    className="text-gray-400 mb-4 flex items-center space-x-2 text-sm"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.5 }}
                >
                    <Link href="/dashboard" className="hover:underline">
                        Dashboard
                    </Link>
                    <span>/</span>
                    <span className="flex items-center">
                        <FaDatabase className="mr-1" /> {databaseId}
                    </span>
                </motion.nav>

                {/* Header with copy */}
                <motion.div
                    className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-8 gap-4"
                    initial={{ y: -20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                >
                    <h1 className="text-3xl font-bold">Database ID: {databaseId}</h1>
                    <div className="flex items-center space-x-3">
                        <Tooltip showArrow content="Copy Database ID">
                            <button
                                onClick={copyId}
                                className="flex items-center text-indigo-400 hover:text-indigo-300 transition"
                            >
                                <FaCopy className="mr-1" /> Copy ID
                            </button>
                        </Tooltip>
                        <button
                            onClick={handleAdd}
                            className="inline-flex items-center bg-pink-500 hover:bg-pink-400 px-4 py-2 rounded-full text-sm font-medium transition shadow"
                        >
                            + New Collection
                        </button>
                    </div>
                </motion.div>

                {/* Collections grid */}
                <CollectionsList
                    databaseId={databaseId}
                    collections={collections}
                    isLoading={isLoading}
                    error={isError ? (error as Error) : undefined}
                />

                {/* Modal */}
                <CreateCollectionModal
                    isOpen={modalOpen}
                    onRequestClose={handleClose}
                />
            </div>

            <Toaster />
        </div>
    )
}
