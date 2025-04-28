'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */
import AddDocument from '@/components/AddDocument';
import DeleteConfirmModal from '@/components/DeleteConfirmModal';
import Document from '@/components/Document';
import { toaster, Toaster } from '@/components/ui/toaster';
import { useCreateDocument, useDeleteDocument, useDocuments, useUpdateDocument } from '@/hooks/useDocuments';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useSession } from 'next-auth/react';
import { redirect, useParams } from 'next/navigation';
import React, { useEffect, useMemo, useState } from 'react';
import { FaCloudUploadAlt, FaPlus, FaSearch, FaSyncAlt, FaTimes, FaTrashAlt } from 'react-icons/fa';
import Modal from 'react-modal';

// JSON viewer for previewing uploaded JSON
import JSONViewer from '@uiw/react-json-view';
import { githubDarkTheme } from '@uiw/react-json-view/githubDark';

// Assume you have an API client (e.g. an Axios instance)
import Loading from '@/components/Loading';
import client from '@/lib/axiosClient';

export interface DocumentData {
    [key: string]: any; // Flexible fields
}

const DocumentsPage = () => {
    const { status } = useSession();
    const { collection, databaseId } = useParams<{ collection: string; databaseId: string }>();
    const { data, isLoading, refetch } = useDocuments({ databaseId, collectionName: collection });

    // Main state for documents and error messages.
    const [documents, setDocuments] = useState<DocumentData[]>([]);
    const [error, setError] = useState<string | null>(null);

    // Modal visibility states.
    const [isDeleting, setIsDeleting] = useState(false);
    const [deletingId, setDeletingId] = useState<string | null>(null);
    const [isAdding, setIsAdding] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [isDeletingAll, setIsDeletingAll] = useState(false);

    // Uploaded JSON file content.
    const [uploadContent, setUploadContent] = useState("");

    // Search and pagination states.
    const [searchQuery, setSearchQuery] = useState('');
    const [parsedQuery, setParsedQuery] = useState<{ [key: string]: any }>({});
    const [currentPage, setCurrentPage] = useState(1);
    const documentsPerPage = 5;

    const queryClient = useQueryClient();

    const createDocumentMutation = useCreateDocument(databaseId, collection);
    const updateDocumentMutation = useUpdateDocument(databaseId, collection);
    const deleteDocumentMutation = useDeleteDocument(databaseId, collection);

    // Mutation for deleting all documents.
    const deleteAllMutation = useMutation({
        mutationFn: () =>
            client.delete(`/database/${databaseId}/${collection}/all`, { data: {} }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["documents", { databaseId, collection }] });
            setDocuments([]);
        }
    });

    // Parse uploaded JSON safely.
    const parsedUploadData = useMemo(() => {
        try {
            return JSON.parse(uploadContent);
        } catch {
            return null;
        }
    }, [uploadContent]);

    useEffect(() => {
        if (data) {
            setDocuments(data.pages.flatMap((page) => page.data) as DocumentData[]);
        }
    }, [data]);

    // Instant search with 300ms debounce.
    useEffect(() => {
        if (searchQuery.trim() === "") {
            setParsedQuery({});
            return;
        }
        // const handler = setTimeout(() => {
        //     try {
        //         const parsed = JSON.parse(searchQuery);
        //         setParsedQuery(parsed);
        //         setCurrentPage(1);
        //     } catch {
        //         setParsedQuery({});
        //     }
        // }, 300);
        // return () => clearTimeout(handler);
    }, [searchQuery]);

    const filteredDocuments = useMemo(() => {
        if (!parsedQuery || Object.keys(parsedQuery).length === 0) return documents;
        return documents.filter((doc) =>
            Object.entries(parsedQuery).every(
                ([key, value]) => key in doc && String(doc[key]) === String(value)
            )
        );
    }, [documents, parsedQuery]);

    const currentDocuments = useMemo(() => {
        const indexOfLast = currentPage * documentsPerPage;
        const indexOfFirst = indexOfLast - documentsPerPage;
        return filteredDocuments.slice(indexOfFirst, indexOfLast);
    }, [filteredDocuments, currentPage]);

    if (status === 'loading') return;
    if (status === 'unauthenticated') redirect('/auth/login');
    if (isLoading) return <Loading />

    const totalPages = Math.ceil(filteredDocuments.length / documentsPerPage);

    // *****************
    // Document Mutation Handlers
    // *****************
    const handleSaveEdit = async (data: { [key: string]: any }) => {
        toaster.promise(
            updateDocumentMutation.mutateAsync(data)
                .then(() => {
                    setDocuments((prev) =>
                        prev.map((doc) => (doc._id === data._id ? { ...doc, ...data } : doc))
                    );
                })
                .catch((err) => {
                    console.error("Error updating document:", err);
                    setError("Error updating document");
                    throw err;
                }),
            {
                loading: { title: "Updating document...", description: "Please wait." },
                success: { title: "Success", description: "Document updated successfully." },
                error: { title: "Failed", description: "Failed to update document." }
            }
        );
    };

    const handleAddDocument = async (newDocument: DocumentData) => {
        setIsAdding(false);
        toaster.promise(
            createDocumentMutation.mutateAsync({ data: newDocument })
                .then(() => {
                    setDocuments((prev) => [...prev, newDocument]);
                })
                .catch((err) => {
                    console.error("Error creating document:", err);
                    setError("Error creating document");
                    throw err;
                }),
            {
                loading: { title: "Creating document...", description: "Please wait." },
                success: { title: "Success", description: "Document created successfully." },
                error: { title: "Failed", description: "Error creating document." }
            }
        );
    };

    const deleteDocument = async (documentId: string) => {
        setIsDeleting(false);
        toaster.promise(
            deleteDocumentMutation.mutateAsync(documentId)
                .then(() => {
                    setDocuments((prev) => prev.filter((doc) => doc._id !== documentId));
                })
                .catch((err) => {
                    console.error("Error deleting document:", err);
                    setError("Error deleting document");
                    throw err;
                }),
            {
                loading: { title: "Deleting document...", description: "Please wait." },
                success: { title: "Success", description: "Document deleted successfully." },
                error: { title: "Failed", description: "Failed to delete document." }
            }
        );
    };

    const handleRefresh = async () => {
        try {
            toaster.promise(
                refetch()
                    .then(() => console.log("Data refreshed successfully"))
                    .catch((err) => {
                        console.error("Error refreshing data:", err);
                        setError("Error refreshing data");
                        throw err;
                    }),
                {
                    loading: { title: "Refreshing data...", description: "Please wait." },
                    success: { title: "Success", description: "Data refreshed successfully." },
                    error: { title: "Failed", description: "Failed to refresh data." }
                }
            );
        } catch (err) {
            console.error("Error refreshing data:", err);
            setError("Error refreshing data");
            toaster.create({ description: "Error refreshing data", type: "error" });
        }
    };

    const handleDeleteAll = async () => {
        setIsDeletingAll(false);
        toaster.promise(
            deleteAllMutation.mutateAsync()
                .then(() => {
                    setDocuments([]);
                })
                .catch((err: any) => {
                    console.error("Error deleting all documents:", err);
                    setError("Error deleting all documents");
                    throw err;
                }),
            {
                loading: { title: "Deleting all documents...", description: "Please wait." },
                success: { title: "Success", description: "All documents deleted." },
                error: { title: "Failed", description: "Failed to delete all documents." }
            }
        );
    };

    // *****************
    // File Upload Handlers
    // *****************
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const text = event.target?.result;
                if (typeof text === "string") {
                    setUploadContent(text);
                }
            };
            reader.onerror = () => setError("Error reading file.");
            reader.readAsText(file);
        }
    };

    const handleUploadJson = async () => {
        try {
            if (!parsedUploadData) {
                throw new Error("Invalid JSON file.");
            }
            let docs: DocumentData[] = [];
            if (Array.isArray(parsedUploadData)) {
                docs = parsedUploadData;
            } else if (typeof parsedUploadData === "object" && parsedUploadData !== null) {
                docs = [parsedUploadData];
            } else {
                throw new Error("Uploaded JSON must be an object or array of objects");
            }
            const uploadPromises = docs.map((doc) =>
                createDocumentMutation.mutateAsync({ data: doc })
            );
            toaster.promise(
                Promise.all(uploadPromises)
                    .then(() => {
                        setDocuments((prev) => [...prev, ...docs]);
                        setUploadContent("");
                    })
                    .catch((err) => {
                        console.error("Error uploading JSON:", err);
                        setError("Error uploading JSON: " + err.message);
                        throw err;
                    }),
                {
                    loading: { title: "Uploading JSON...", description: "Please wait." },
                    success: { title: "Success", description: "JSON uploaded successfully." },
                    error: { title: "Failed", description: "Failed to upload JSON." }
                }
            );
            setIsUploading(false);
        } catch (err: any) {
            console.error("Error uploading JSON:", err);
            setError("Error uploading JSON: " + err.message);
        }
    };

    return (
        <div className="container mx-auto p-4 bg-gray-900 text-white min-h-screen">
            <h1 className="text-xl sm:text-3xl font-semibold mb-4 text-orange-400 text-center">
                {`"${collection}" `} Documents
            </h1>

            {/* Action Toolbar */}
            <div className="flex flex-col sm:flex-row justify-between items-center mb-4 gap-4">
                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={() => setIsAdding(true)}
                        className="flex items-center bg-green-600 hover:bg-green-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded shadow transition text-xs sm:text-base"
                    >
                        <FaPlus className="mr-0 sm:mr-1" />
                        <span className="hidden sm:inline">Add New Document</span>
                    </button>
                    <button
                        onClick={handleRefresh}
                        className="flex items-center bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded shadow transition text-xs sm:text-base"
                    >
                        <FaSyncAlt className="mr-0 sm:mr-1" />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                    <button
                        onClick={() => setIsUploading(true)}
                        className="flex items-center bg-purple-600 hover:bg-purple-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded shadow transition text-xs sm:text-base"
                    >
                        <FaCloudUploadAlt className="mr-0 sm:mr-1" />
                        <span className="hidden sm:inline">Upload JSON</span>
                    </button>
                    <button
                        onClick={() => setIsDeletingAll(true)}
                        className="flex items-center bg-red-600 hover:bg-red-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded shadow transition text-xs sm:text-base"
                    >
                        <FaTrashAlt className="mr-0 sm:mr-1" />
                        <span className="hidden sm:inline">Delete All</span>
                    </button>
                </div>
                <div className="flex items-center gap-2">
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            if (!e.target.value.trim()) setParsedQuery({});
                            setError(null);
                        }}
                        placeholder='Search: { "name": "john" }'
                        className="border p-2 rounded bg-gray-800 text-white w-full sm:w-64 text-xs sm:text-sm"
                        aria-label="Search documents"
                    />
                    {searchQuery && (
                        <button onClick={() => { setSearchQuery(''); setParsedQuery({}); }} className="text-gray-400 hover:text-white">
                            <FaTimes />
                        </button>
                    )}
                    <button
                        onClick={() => { }}
                        className="flex items-center bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 sm:px-3 sm:py-2 rounded shadow transition text-xs sm:text-base"
                    >
                        <FaSearch className="mr-0 sm:mr-1" />
                        <span className="hidden sm:inline">Search</span>
                    </button>
                </div>
            </div>

            {/* Documents Grid */}

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {currentDocuments.map((doc, index) => (
                    <Document
                        key={doc._id || index}
                        document={doc}
                        onSave={handleSaveEdit}
                        onDelete={(documentId: string) => {
                            setDeletingId(documentId);
                            setIsDeleting(true);
                        }}
                    />
                ))}
            </div>

            {/* Pagination Controls */}
            <div className="flex justify-between items-center mt-4 text-xs sm:text-sm">
                <button onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))} disabled={currentPage === 1} className="bg-gray-700 text-white p-1 sm:p-2 rounded hover:bg-gray-600 transition">
                    Previous
                </button>
                <span className="text-white">
                    Page {currentPage} of {totalPages}
                </span>
                <button onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))} disabled={currentPage === totalPages} className="bg-gray-700 text-white p-1 sm:p-2 rounded hover:bg-gray-600 transition">
                    Next
                </button>
            </div>

            {/* Add Document Modal */}
            <Modal
                isOpen={isAdding}
                onRequestClose={() => setIsAdding(false)}
                className="bg-gray-800 p-4 rounded-lg w-11/12 sm:w-1/2 md:w-1/3 lg:w-1/4"
                overlayClassName="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center"
            >
                <AddDocument onAdd={handleAddDocument} />
            </Modal>

            {/* Upload JSON Modal */}
            <Modal
                isOpen={isUploading}
                onRequestClose={() => setIsUploading(false)}
                className="bg-gray-800 p-4 rounded-lg w-11/12 sm:w-1/2 md:w-1/3 lg:w-1/4 overflow-auto"
                overlayClassName="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center"
            >
                <h2 className="text-lg sm:text-xl font-semibold mb-4 text-orange-400 flex items-center">
                    <FaCloudUploadAlt className="mr-2" /> Upload JSON Data
                </h2>
                <input type="file" accept=".json" onChange={handleFileChange} className="mb-3 text-white" />
                {uploadContent && parsedUploadData ? (
                    <div className="h-48 overflow-auto mb-3">
                        <JSONViewer
                            value={parsedUploadData}
                            style={githubDarkTheme}
                            className="h-full"
                            enableClipboard={false}
                            displayDataTypes={false}
                        />
                    </div>
                ) : uploadContent && !parsedUploadData ? (
                    <p className="text-red-500 mb-3">Invalid JSON file.</p>
                ) : (
                    <p className="mb-3">No file selected.</p>
                )}
                {error && <p className="text-red-500 text-xs mt-2">{error}</p>}
                <div className="flex justify-end mt-4 gap-2">
                    <button onClick={() => setIsUploading(false)} className="bg-gray-600 text-white px-2 py-1 rounded hover:bg-gray-500 transition text-xs sm:text-base">
                        Cancel
                    </button>
                    <button onClick={handleUploadJson} className="bg-purple-600 text-white px-2 py-1 rounded hover:bg-purple-500 transition text-xs sm:text-base">
                        Upload
                    </button>
                </div>
            </Modal>

            {/* Delete Confirm Modals */}
            {isDeleting && (
                <DeleteConfirmModal
                    onConfirm={() => deletingId && deleteDocument(deletingId)}
                    onClose={() => setIsDeleting(false)}
                    title="Delete Document"
                    message="Are you sure you want to delete this document?"
                />
            )}
            {isDeletingAll && (
                <DeleteConfirmModal
                    onConfirm={handleDeleteAll}
                    onClose={() => setIsDeletingAll(false)}
                    title="Delete All Documents"
                    message="Are you sure you want to delete ALL documents in this collection?"
                />
            )}

            <Toaster />
        </div>
    );
};

export default DocumentsPage;
