'use client';
import React, { useState } from 'react';
import Modal from 'react-modal';
import { CreateDatabaseInput } from '@/hooks/useDatabase';


interface ModalProps {
    isOpen: boolean;
    onRequestClose: () => void;
    createDatabase: (data: CreateDatabaseInput) => void;
}

const isValidMongoName = (name: string) => {
    const regex = /^(?!\.)(?!\$)(?!.*[\.\$])[A-Za-z0-9_]{1,120}$/;
    return regex.test(name);
};

const CreateDatabaseModal: React.FC<ModalProps> = ({
    isOpen,
    onRequestClose,
    createDatabase,
}) => {
    const [step, setStep] = useState(1);
    const [dbName, setDbName] = useState('');
    const [description, setDescription] = useState('');
    const [collectionName, setCollectionName] = useState('');
    const [fieldNames, setFieldNames] = useState('');
    const [collections, setCollections] = useState<
        { name: string; fields: { name: string }[] }[]
    >([]);
    const [error, setError] = useState('');

    const handleAddCollection = () => {
        if (!collectionName.trim()) {
            setError('Collection name is required.');
            return;
        }
        if (!isValidMongoName(collectionName)) {
            setError('Invalid collection name.');
            return;
        }

        const fields = fieldNames
            .split(',')
            .map((f) => f.trim())
            .filter((f) => f && isValidMongoName(f))
            .map((f) => ({ name: f }));

        if (fields.length === 0) {
            setError('Please enter valid field names.');
            return;
        }

        setCollections([...collections, { name: collectionName, fields }]);
        setCollectionName('');
        setFieldNames('');
        setError('');
    };

    const handleCreate = () => {
        if (!dbName.trim()) {
            setError('Database name is required.');
            return;
        }
        if (!isValidMongoName(dbName)) {
            setError('Invalid database name.');
            return;
        }
        if (collections.length === 0) {
            setError('Add at least one collection.');
            return;
        }

        const payload = {
            dbName: dbName.toLowerCase(),
            description: description.trim() || undefined,
            collections: collections.map((col) => ({
                name: col.name.toLowerCase(),
                fields: col.fields.map((f) => f.name),
            })),
        };

        createDatabase(payload);
        // Reset form
        setStep(1);
        setDbName('');
        setDescription('');
        setCollections([]);
        setError('');
    };

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            className="bg-gray-800 p-6 rounded-lg w-11/12 max-w-md mx-auto"
            overlayClassName="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center"
        >
            <button
                onClick={onRequestClose}
                className="text-gray-400 hover:text-white absolute top-4 right-4"
            >
                ×
            </button>

            <div className="text-gray-200 mb-4">
                <h3 className="text-lg font-semibold">Naming Guidelines</h3>
                <ul className="list-disc list-inside text-sm">
                    <li>No <code>.</code> or <code>$</code></li>
                    <li>1–120 chars, alphanumeric & underscore</li>
                </ul>
            </div>

            {error && <div className="mb-4 text-red-400">{error}</div>}

            {step === 1 && (
                <div>
                    <h2 className="text-xl font-bold text-white mb-3">Step 1: Database</h2>
                    <input
                        type="text"
                        placeholder="Database Name"
                        value={dbName}
                        onChange={(e) => {
                            setDbName(e.target.value);
                            setError('');
                        }}
                        className="w-full px-3 py-2 mb-2 bg-gray-700 text-white rounded"
                    />
                    <input
                        type="text"
                        placeholder="Description (optional)"
                        value={description}
                        onChange={(e) => {
                            setDescription(e.target.value);
                            setError('');
                        }}
                        className="w-full px-3 py-2 mb-4 bg-gray-700 text-white rounded"
                    />
                    <button
                        onClick={() => setStep(2)}
                        className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded"
                    >
                        Next
                    </button>
                </div>
            )}

            {step === 2 && (
                <div>
                    <h2 className="text-xl font-bold text-white mb-3">Step 2: Collections</h2>
                    <input
                        type="text"
                        placeholder="Collection Name"
                        value={collectionName}
                        onChange={(e) => {
                            setCollectionName(e.target.value);
                            setError('');
                        }}
                        className="w-full px-3 py-2 mb-2 bg-gray-700 text-white rounded"
                    />
                    <input
                        type="text"
                        placeholder="Field names, comma separated"
                        value={fieldNames}
                        onChange={(e) => {
                            setFieldNames(e.target.value);
                            setError('');
                        }}
                        className="w-full px-3 py-2 mb-2 bg-gray-700 text-white rounded"
                    />
                    <button
                        onClick={handleAddCollection}
                        className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded"
                    >
                        Add Collection
                    </button>

                    <div className="mt-4 space-y-2">
                        {collections.map((col, idx) => (
                            <div key={idx} className="text-gray-300">
                                <strong>{col.name}: </strong>
                                {col.fields.map((f) => f.name).join(', ')}
                            </div>
                        ))}
                    </div>

                    <div className="mt-6 flex justify-between">
                        <button
                            onClick={() => setStep(1)}
                            className="bg-yellow-600 hover:bg-yellow-500 text-white px-4 py-2 rounded"
                        >
                            Back
                        </button>
                        <button
                            onClick={handleCreate}
                            className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded"
                        >
                            Create Database
                        </button>
                    </div>
                </div>
            )}
        </Modal>
    );
};

export default CreateDatabaseModal;



// import { useCreateDatabase } from '@/hooks/useDatabase';
// import { Spinner } from '@chakra-ui/react';
// import { useState } from 'react';
// import Modal from 'react-modal';

// interface ModalProps {
//     isOpen: boolean;
//     onRequestClose: () => void;
//     createDatabase: (data: {
//         db_name: string;
//         description: string;
//         collections: { name: string; fields: { name: string; type: string; }[] }[];
//     }) => void;
// }

// const isValidMongoName = (name: string) => {
//     const mongoNameRegex = /^(?!\.)(?!\$)(?!.*[\.\$])[a-zA-Z0-9_]+$/;
//     return mongoNameRegex.test(name) && name.length > 0 && name.length <= 120;
// };

// const CreateDatabaseModal = ({ isOpen, onRequestClose, createDatabase }: ModalProps) => {
//     const [step, setStep] = useState(1);
//     const [dbName, setDbName] = useState('');
//     const [description, setDescription] = useState('');
//     const [collectionName, setCollectionName] = useState('');
//     const [fieldNames, setFieldNames] = useState('');
//     const [collections, setCollections] = useState<{ name: string; fields: { name: string; type: string; }[] }[]>([]);
//     const [error, setError] = useState('');
//     const createDatabaseMutation = useCreateDatabase();

//     const handleAddCollection = () => {
//         if (collectionName && fieldNames) {
//             if (!isValidMongoName(collectionName)) {
//                 setError('Collection name is invalid. Follow MongoDB naming conventions.');
//                 return;
//             }

//             const fields = fieldNames.split(',').map(field => ({
//                 name: field.trim(),
//                 type: "string",
//             })).filter(field => field.name && isValidMongoName(field.name));

//             if (fields.length === 0) {
//                 setError('Invalid field names. Ensure they follow MongoDB naming conventions.');
//                 return;
//             }

//             setCollections([...collections, { name: collectionName, fields }]);
//             setCollectionName('');
//             setFieldNames('');
//             setError(''); // Clear the error message
//         }
//     };

//     const handleKeyDown = () => {
//         setError(''); // Clear error when user starts typing
//     };

//     return (
//         <Modal
//             isOpen={isOpen}
//             onRequestClose={onRequestClose}
//             className="bg-gray-800 p-5 rounded-lg w-4/5 sm:w-1/2 md:w-1/3 lg:w-1/4"
//             overlayClassName="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center"
//         >
//             {createDatabaseMutation.isPending && (
//                 <div className="flex justify-center mb-4">
//                     <Spinner size="lg" color="blue.500" />
//                 </div>
//             )}

//             {/* User Guidelines */}
//             <div className="mb-3 text-gray-300">
//                 <h3 className="text-lg">Guidelines for Naming:</h3>
//                 <ul className="list-disc list-inside">
//                     <li>Database and collection names must not contain <code>.</code> or <code>$</code>.</li>
//                     <li>Names should be between 1 and 120 characters long.</li>
//                     <li>Only alphanumeric characters and underscores <code>_</code> are allowed.</li>
//                 </ul>
//             </div>

//             {error && <div className="mb-2 text-red-500">{error}</div>}

//             {step === 1 && (
//                 <div>
//                     <h2 className="text-xl text-white mb-3">Create Database</h2>
//                     <input
//                         type="text"
//                         value={dbName}
//                         onChange={(e) => setDbName(e.target.value)}
//                         onKeyDown={handleKeyDown}
//                         placeholder="Database Name"
//                         className="w-full p-2 mb-2 rounded bg-gray-700 text-white"
//                     />
//                     <input
//                         type="text"
//                         value={description}
//                         onChange={(e) => setDescription(e.target.value)}
//                         onKeyDown={handleKeyDown}
//                         placeholder="Description"
//                         className="w-full p-2 mb-2 rounded bg-gray-700 text-white"
//                     />
//                     <button onClick={() => setStep(2)} className="bg-blue-500 text-white px-4 py-2 rounded mt-2">
//                         Next
//                     </button>
//                 </div>
//             )}

//             {step === 2 && (
//                 <div>
//                     <h2 className="text-xl text-white mb-3">Add Collections</h2>
//                     <input
//                         type="text"
//                         value={collectionName}
//                         onChange={(e) => setCollectionName(e.target.value)}
//                         onKeyDown={handleKeyDown}
//                         placeholder="Collection Name"
//                         className="w-full p-2 mb-2 rounded bg-gray-700 text-white"
//                     />
//                     <input
//                         type="text"
//                         value={fieldNames}
//                         onChange={(e) => setFieldNames(e.target.value)}
//                         onKeyDown={handleKeyDown}
//                         placeholder="Comma-separated Field Names (e.g., name, age)"
//                         className="w-full p-2 mb-2 rounded bg-gray-700 text-white"
//                     />
//                     <button onClick={handleAddCollection} className="bg-green-500 text-white px-4 py-2 rounded mt-2">
//                         Add Collection
//                     </button>
//                     <div className="mt-3 text-gray-300">
//                         {collections.map((collection, index) => (
//                             <div key={index} className="mb-1">
//                                 <strong>{collection.name}:</strong> {collection.fields.map(field => field.name).join(', ')}
//                             </div>
//                         ))}
//                     </div>
//                     <button onClick={() => createDatabase({ db_name: dbName, description, collections })}
//                         className="bg-red-500 text-white px-4 py-2 rounded mt-3">
//                         Create Database
//                     </button>
//                     <button onClick={() => setStep(1)} className="bg-yellow-500 text-white px-4 py-2 rounded mt-3">
//                         Back
//                     </button>
//                 </div>
//             )}
//         </Modal>
//     );
// };

// export default CreateDatabaseModal;
