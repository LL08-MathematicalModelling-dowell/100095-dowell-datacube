'use client';
import React, { useEffect, useState } from 'react';
import Modal from 'react-modal';
import {
    FaKey,
    FaEdit,
    FaTrashAlt,
    FaRegClipboard,
    FaPlus,
    FaTimes,
} from 'react-icons/fa';
import { toaster, Toaster } from '@/components/ui/toaster';
import { Spinner } from '@chakra-ui/react';
import {
    useGetApiKeys,
    useCreateApiKey,
    useUpdateApiKey,
    useDeleteApiKey,
} from '@/hooks/useAPIKey';
import { useSession } from 'next-auth/react';
import Loading from '@/components/Loading';
import { redirect } from 'next/navigation';

// Bind modal to #__next for a11y
// Modal.setAppElement('#__next');

export interface ApiKey {
    id: string;
    key: string;
    plainKey?: string;
    description: string;
    createdAt: string;
    expiresAt: string;
    lastUsed?: string;
}

const ApiKeyManagement: React.FC = () => {
    const { data: session, status } = useSession();
    const userId = session?.user?.email;

    useEffect(() => {
        if (status === 'unauthenticated') {
            redirect('/auth/login');
        }
    }, [status]);



    // Fetch & mutations
    const { data: apiKeys = [], isLoading } = useGetApiKeys(userId || '');
    const createMutation = useCreateApiKey();
    const updateMutation = useUpdateApiKey();
    const deleteMutation = useDeleteApiKey();

    // Form/edit state
    const [description, setDescription] = useState('');
    const [expirationDate, setExpirationDate] = useState('');
    const [editingKeyId, setEditingKeyId] = useState<string | null>(null);
    const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

    // New key modal
    const [newPlainKey, setNewPlainKey] = useState('');
    const [keyModalOpen, setKeyModalOpen] = useState(false);

    // Delete confirmation modal
    const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

    if (!userId) redirect("/auth/login");

    const getDefaultExpirationDate = () => {
        const d = new Date();
        d.setDate(d.getDate() + 30);
        return d.toISOString().split('T')[0];
    };

    // ----- Handlers -----
    const handleCopy = (key: string) => {
        navigator.clipboard.writeText(key);
        setCopyFeedback('Copied to clipboard!');
        setTimeout(() => setCopyFeedback(null), 2000);
    };

    const handleCreate = () => {
        if (!description.trim()) return toaster.create({ description: 'Enter a description', type: 'error' });
        const expiresAt = expirationDate || new Date(Date.now() + 30 * 86400000).toISOString();

        createMutation.mutate(
            { userId, description, expiresAt },
            {
                onSuccess: ({ apiKey }) => {
                    setNewPlainKey(apiKey.plainKey || '');
                    setKeyModalOpen(true);
                    toaster.create({ description: 'API key created!', type: 'success' });
                },
                onError: () => toaster.create({ description: 'Create failed', type: 'error' }),
            }
        );

        setDescription('');
        setExpirationDate('');
    };

    const handleUpdate = () => {
        if (!editingKeyId) return;
        updateMutation.mutate(
            { userId, apiKeyId: editingKeyId, description, expiresAt: expirationDate },
            {
                onSuccess: () => toaster.create({ description: 'Updated!', type: 'success' }),
                onError: () => toaster.create({ description: 'Update failed', type: 'error' }),
            }
        );
        setEditingKeyId(null);
        setDescription('');
        setExpirationDate('');
    };

    const requestDelete = (id: string) => {
        setConfirmDeleteId(id);
    };

    const confirmDelete = () => {
        if (!confirmDeleteId) return;
        deleteMutation.mutate(
            { userId, apiKeyId: confirmDeleteId },
            {
                onSuccess: () => toaster.create({ description: 'Deleted!', type: 'success' }),
                onError: () => toaster.create({ description: 'Delete failed', type: 'error' }),
            }
        );
        setConfirmDeleteId(null);
    };

    const cancelDelete = () => setConfirmDeleteId(null);

    const handleEdit = (key: ApiKey) => {
        setEditingKeyId(key.id);
        setDescription(key.description);
        setExpirationDate(key.expiresAt.split('T')[0]);
    };

    if (status === 'loading') {
        return <Loading />;
    }

    // ----- Render -----
    return (
        <div className="bg-gray-900 min-h-screen p-4 sm:p-6 text-white">
            <h2 className="text-xl sm:text-3xl font-bold mb-4 flex justify-center items-center">
                <FaKey className="mr-2 text-blue-400" /> API Key Management
            </h2>

            {/* Create / Update Form */}
            <div className="flex flex-col sm:flex-row gap-2 mb-4">
                <input
                    type="text"
                    placeholder="Description"
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    className="flex-1 p-2 bg-gray-800 border border-gray-700 rounded text-xs sm:text-base"
                />
                <input
                    type="date"
                    value={expirationDate || getDefaultExpirationDate()}
                    onChange={e => setExpirationDate(e.target.value)}
                    min={getDefaultExpirationDate()}
                    max={new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0]}
                    className="w-full sm:w-1/4 p-2 bg-gray-800 border border-gray-700 rounded text-xs sm:text-base"
                />
                {editingKeyId ? (
                    <button
                        onClick={handleUpdate}
                        className="flex items-center bg-green-600 hover:bg-green-500 px-2 py-2 rounded text-xs sm:text-base"
                    >
                        <FaEdit className="mr-1" /><span className="hidden sm:inline">Update</span>
                    </button>
                ) : (
                    <button
                        onClick={handleCreate}
                        className="flex items-center bg-blue-600 hover:bg-blue-500 px-2 py-2 rounded text-xs sm:text-base"
                    >
                        <FaPlus className="mr-1" /><span className="hidden sm:inline">Generate</span>
                    </button>
                )}
            </div>

            {copyFeedback && (
                <div className="mb-4 text-green-400 text-xs sm:text-base">{copyFeedback}</div>
            )}

            {/* List or Spinner */}
            {isLoading ? (
                <div className="flex justify-center items-center h-32">
                    <Spinner color="white" size="xl" />
                </div>
            ) : (
                <div className="space-y-4">
                    {apiKeys.length === 0 ? (
                        <div className="text-gray-400 text-center">No API keys found.</div>
                    ) : (
                        apiKeys.map((key: ApiKey) => (
                            <div
                                key={key.id}
                                className="p-4 bg-gray-800 rounded flex flex-col sm:flex-row justify-between items-start sm:items-center"
                            >
                                <div>
                                    <h3 className="text-sm sm:text-xl font-semibold">{key.description}</h3>
                                    <p className="text-gray-400 text-xs sm:text-base break-all">
                                        Key: {key.plainKey ?? '••••••••••'}
                                    </p>
                                    <p className="text-gray-500 text-xs">
                                        Created: {new Date(key.createdAt).toLocaleString()}
                                    </p>
                                    <p className="text-gray-500 text-xs">
                                        Expires: {new Date(key.expiresAt).toLocaleString()}
                                    </p>
                                    <p className="text-gray-500 text-xs">
                                        Last used: {key.lastUsed ? new Date(key.lastUsed).toLocaleString() : 'Never'}
                                    </p>
                                    {key.plainKey && (
                                        <p className="text-yellow-400 text-xs">
                                            Copy this now! It won&apos;t be shown again.
                                        </p>
                                    )}
                                </div>
                                <div className="mt-2 sm:mt-0 flex flex-col space-y-1">
                                    <button
                                        onClick={() => handleCopy(key.plainKey ?? '')}
                                        disabled={!key.plainKey}
                                        className={`flex items-center text-xs sm:text-base ${key.plainKey ? 'text-blue-400 hover:text-blue-300' : 'text-gray-600'
                                            }`}
                                    >
                                        <FaRegClipboard className="mr-1" />
                                        <span className="hidden sm:inline">Copy</span>
                                    </button>
                                    <button
                                        onClick={() => handleEdit(key)}
                                        className="flex items-center text-yellow-400 hover:text-yellow-300 text-xs sm:text-base"
                                    >
                                        <FaEdit className="mr-1" />
                                        <span className="hidden sm:inline">Edit</span>
                                    </button>
                                    <button
                                        onClick={() => requestDelete(key.id)}
                                        className="flex items-center text-red-400 hover:text-red-300 text-xs sm:text-base"
                                    >
                                        <FaTrashAlt className="mr-1" />
                                        <span className="hidden sm:inline">Delete</span>
                                    </button>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* New Plain‑Key Modal */}
            <Modal
                isOpen={keyModalOpen}
                onRequestClose={() => setKeyModalOpen(false)}
                overlayClassName="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center"
                className="bg-gray-800 p-4 rounded-lg w-11/12 sm:w-1/2 lg:w-1/3"
            >
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">Copy Your API Key</h3>
                    <button onClick={() => setKeyModalOpen(false)} className="text-gray-400 hover:text-white">
                        <FaTimes />
                    </button>
                </div>
                <p className="text-gray-200 mb-2 text-sm">
                    This is your only chance to copy the key. Keep it safe!
                </p>
                <div className="bg-gray-700 text-white p-3 rounded mb-4 break-all">
                    {newPlainKey}
                </div>
                <div className="flex justify-end">
                    <button
                        onClick={() => {
                            navigator.clipboard.writeText(newPlainKey);
                            toaster.create({ description: 'Copied!', type: 'success' });
                            setKeyModalOpen(false);
                        }}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded text-sm"
                    >
                        Copy & Close
                    </button>
                </div>
            </Modal>

            {/* Delete Confirmation Modal */}
            <Modal
                isOpen={!!confirmDeleteId}
                onRequestClose={cancelDelete}
                overlayClassName="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center"
                className="bg-gray-800 p-4 rounded-lg w-11/12 sm:w-1/3"
            >
                <h3 className="text-lg font-semibold text-white mb-4">Confirm Delete</h3>
                <p className="text-gray-200 mb-6">
                    Are you sure you want to delete this API key?
                </p>
                <div className="flex justify-end gap-2">
                    <button
                        onClick={cancelDelete}
                        className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded text-sm"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={confirmDelete}
                        className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded text-sm"
                    >
                        Delete
                    </button>
                </div>
            </Modal>

            <Toaster />
        </div>
    );
};

export default ApiKeyManagement;
