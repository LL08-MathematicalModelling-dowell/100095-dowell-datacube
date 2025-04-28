'use client';
import CreateDatabaseModal from '@/components/CreateDatabaseModal';
import DatabaseDashboard from '@/components/DatabaseDashboard';
import Loading from '@/components/Loading';
import { Toaster, toaster } from '@/components/ui/toaster';
import {
    CreateDatabaseInput,
    useCreateDatabase,
    useDatabases,
} from '@/hooks/useDatabase';
import { useSession } from 'next-auth/react';
import { redirect } from 'next/navigation';
import React, { useMemo, useState } from 'react';

const Home: React.FC = () => {
    const { data: session, status: sessionStatus } = useSession();
    const [modalIsOpen, setModalIsOpen] = useState(false);

    // Fetch paginated databases
    const {
        data,
        isLoading,
        isError,
        error,
        fetchNextPage,
        hasNextPage,
        status,
    } = useDatabases({ pageSize: 10 });


    const databases = useMemo(
        () => data?.pages.flatMap((page) => page.data) ?? [],
        [data]
    );

    // Create mutation
    const createDatabaseMutation = useCreateDatabase();

    if (sessionStatus === 'loading') return null;
    if (sessionStatus === 'unauthenticated' || !session) {
        redirect('/auth/login');
    }

    if (isLoading) return <Loading />

    if (isError) {
        return (
            <p className="text-center text-red-500 mb-4">
                {error?.message || 'Something went wrong.'}
            </p>
        )
    }

    const handleCreateClick = () => setModalIsOpen(true);

    // Now accept CreateDatabaseInput directly
    const handleCreateSubmit = (payload: CreateDatabaseInput) => {
        setModalIsOpen(false);

        toaster.promise(
            createDatabaseMutation.mutateAsync(payload),
            {
                loading: {
                    title: 'Creating database...',
                    description: 'Please wait.',
                },
                success: { title: 'Database created!' },
                error: {
                    title: 'Failed to create database',
                    description: 'Please try again.',
                },
            }
        );
    };

    return (
        <>
            <DatabaseDashboard
                databases={databases}
                onCreateDatabase={handleCreateClick}
                isLoading={isLoading}
                fetchNextPage={fetchNextPage}
                hasNextPage={!!hasNextPage}
                status={status}
            />

            <CreateDatabaseModal
                isOpen={modalIsOpen}
                onRequestClose={() => setModalIsOpen(false)}
                // Now expects CreateDatabaseInput shape:
                createDatabase={handleCreateSubmit}
            />

            <Toaster />
        </>
    );
};

export default Home;
