// components/CreateCollectionModal.tsx
'use client'
import React, { useState, useEffect } from 'react'
import Modal from 'react-modal'
import { motion, AnimatePresence } from 'framer-motion'
import { FaTimes } from 'react-icons/fa'

// Modal.setAppElement('#__next')

interface CreateCollectionModalProps {
    isOpen: boolean
    /**
     * onRequestClose will be called with:
     * - { name, fields } when user submits a valid collection
     * - null when the modal is closed without creating
     */
    onRequestClose: (
        newCollection: { name: string; fields: string[] } | null
    ) => void
}

const isValidMongoName = (name: string) => {
    const regex = /^(?!\.)(?!\$)(?!.*[\.\$])[A-Za-z0-9_]{1,120}$/
    return regex.test(name)
}

export default function CreateCollectionModal({
    isOpen,
    onRequestClose,
}: CreateCollectionModalProps) {
    const [collectionName, setCollectionName] = useState('')
    const [fieldInput, setFieldInput] = useState('')
    const [error, setError] = useState('')

    // reset form on open
    useEffect(() => {
        if (isOpen) {
            setCollectionName('')
            setFieldInput('')
            setError('')
        }
    }, [isOpen])

    const handleSubmit = () => {
        const name = collectionName.trim()
        if (!isValidMongoName(name)) {
            setError('Invalid name – use 1–120 alphanumeric or underscores, no “.” or “$”.')
            return
        }
        const fields = fieldInput
            .split(',')
            .map((f) => f.trim())
            .filter((f) => f && isValidMongoName(f))
        if (fields.length === 0) {
            setError('Enter at least one valid field name, comma‑separated.')
            return
        }
        onRequestClose({ name, fields })
    }

    const handleClose = () => onRequestClose(null)

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={handleClose}
            closeTimeoutMS={200}
            overlayClassName="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50"
            className="outline-none"
            bodyOpenClassName="overflow-hidden"
        >
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.2 }}
                        className="relative bg-gray-800 rounded-xl w-11/12 max-w-lg mx-auto p-6 shadow-2xl"
                    >
                        {/* Close */}
                        <button
                            onClick={handleClose}
                            className="absolute top-4 right-4 text-gray-400 hover:text-gray-200"
                            aria-label="Close modal"
                        >
                            <FaTimes size={18} />
                        </button>

                        <h2 className="text-2xl font-semibold text-white mb-4">
                            Create New Collection
                        </h2>
                        <p className="text-gray-300 mb-4 text-sm">
                            <strong>Naming rules:</strong>
                            <ul className="list-disc pl-5 mt-1 space-y-1">
                                <li>No <code className="bg-gray-700 px-1 rounded">.</code> or <code className="bg-gray-700 px-1 rounded">$</code></li>
                                <li>1–120 characters, letters, numbers, or underscore only</li>
                            </ul>
                        </p>

                        {error && (
                            <div className="bg-red-600 text-white px-4 py-2 rounded mb-4">
                                {error}
                            </div>
                        )}

                        <div className="space-y-4">
                            <input
                                type="text"
                                placeholder="Collection name"
                                value={collectionName}
                                onChange={(e) => {
                                    setCollectionName(e.target.value)
                                    if (error) setError('')
                                }}
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                            />
                            <textarea
                                placeholder="Field names (comma separated)"
                                rows={3}
                                value={fieldInput}
                                onChange={(e) => {
                                    setFieldInput(e.target.value)
                                    if (error) setError('')
                                }}
                                className="w-full px-4 py-2 bg-gray-700 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-pink-500"
                            />
                        </div>

                        <button
                            onClick={handleSubmit}
                            className="mt-6 w-full bg-pink-500 hover:bg-pink-400 text-white py-3 rounded-lg font-medium transition"
                        >
                            Create Collection
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </Modal>
    )
}

// // components/CreateCollectionModal.tsx
// 'use client';
// import React, { useState } from 'react';
// import Modal from 'react-modal';

// interface CreateCollectionModalProps {
//     isOpen: boolean;
//     /**
//      * onRequestClose will be called with:
//      * - { name, fields } when user submits a valid collection
//      * - null when the modal is closed without creating
//      */
//     onRequestClose: (newCollection: { name: string; fields: string[] } | null) => void;
// }

// const isValidMongoName = (name: string) => {
//     const regex = /^(?!\.)(?!\$)(?!.*[\.\$])[A-Za-z0-9_]{1,120}$/;
//     return regex.test(name);
// };

// const CreateCollectionModal: React.FC<CreateCollectionModalProps> = ({
//     isOpen,
//     onRequestClose,
// }) => {
//     const [collectionName, setCollectionName] = useState('');
//     const [fieldInput, setFieldInput] = useState('');
//     const [error, setError] = useState('');

//     const resetForm = () => {
//         setCollectionName('');
//         setFieldInput('');
//         setError('');
//     };

//     const handleSubmit = () => {
//         const name = collectionName.trim();
//         if (!isValidMongoName(name)) {
//             setError('Invalid collection name.');
//             return;
//         }

//         // parse comma‑separated fields
//         const fields = fieldInput
//             .split(',')
//             .map((f) => f.trim())
//             .filter((f) => f && isValidMongoName(f));

//         if (fields.length === 0) {
//             setError('Please enter at least one valid field name.');
//             return;
//         }

//         onRequestClose({ name, fields });
//         resetForm();
//     };

//     const handleClose = () => {
//         onRequestClose(null);
//         resetForm();
//     };

//     return (
//         <Modal
//             isOpen={isOpen}
//             onRequestClose={handleClose}
//             className="bg-gray-800 p-6 rounded-lg w-11/12 max-w-md mx-auto relative"
//             overlayClassName="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
//         >
//             {/* Close button */}
//             <button
//                 onClick={handleClose}
//                 className="absolute top-3 right-3 text-gray-400 hover:text-white"
//             >
//                 ×
//             </button>

//             <h2 className="text-xl font-semibold text-white mb-4">Create Collection</h2>

//             <div className="text-gray-300 mb-4 text-sm">
//                 <p>Naming rules:</p>
//                 <ul className="list-disc list-inside">
//                     <li>No <code>.</code> or <code>$</code> in names.</li>
//                     <li>1–120 chars, alphanumeric & underscore only.</li>
//                 </ul>
//             </div>

//             {error && <div className="mb-3 text-red-400">{error}</div>}

//             <input
//                 type="text"
//                 placeholder="Collection Name"
//                 value={collectionName}
//                 onChange={(e) => {
//                     setCollectionName(e.target.value);
//                     if (error) setError('');
//                 }}
//                 className="w-full px-3 py-2 mb-3 bg-gray-700 text-white rounded"
//             />

//             <textarea
//                 placeholder="Field Names (comma separated)"
//                 value={fieldInput}
//                 onChange={(e) => {
//                     setFieldInput(e.target.value);
//                     if (error) setError('');
//                 }}
//                 rows={4}
//                 className="w-full px-3 py-2 mb-4 bg-gray-700 text-white rounded"
//             />

//             <button
//                 onClick={handleSubmit}
//                 className="w-full bg-blue-600 hover:bg-blue-500 text-white py-2 rounded"
//             >
//                 Create Collection
//             </button>
//         </Modal>
//     );
// };

// export default CreateCollectionModal;

