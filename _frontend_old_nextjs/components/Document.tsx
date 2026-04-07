'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import JSONViewer from '@uiw/react-json-view';
import { githubDarkTheme } from '@uiw/react-json-view/githubDark';
import { FaEdit, FaSave, FaTimes, FaTrashAlt } from 'react-icons/fa';

export interface DocumentData {
    id: string;
    [key: string]: any;
}

interface DocumentProps {
    document: { [key: string]: any };
    onSave: (doc: { [key: string]: any }) => void;
    onDelete: (documentId: string) => void;
}

// Validate that the field name complies with MongoDB constraints.
const isValidMongoName = (name: string) => {
    const mongoNameRegex = /^(?!\.)(?!\$)(?!.*[\.\$])[a-zA-Z0-9_]+$/;
    return mongoNameRegex.test(name) && name.length > 0 && name.length <= 120;
};

const Document = ({ document, onSave, onDelete }: DocumentProps) => {
    // Helper function: returns a copy of the document excluding _id.
    const withoutId = (doc: any) => {
        const newDoc = { ...doc };
        delete newDoc._id;
        return newDoc;
    };

    // Component state.
    const [isEditing, setIsEditing] = useState(false);
    const [jsonContent, setJsonContent] = useState<string>(
        JSON.stringify(withoutId(document), null, 2)
    );
    const [error, setError] = useState<string | null>(null);

    const handleEdit = () => {
        try {
            const updatedDoc = JSON.parse(jsonContent);
            // Validate each editable field's name.
            for (const key in updatedDoc) {
                if (!isValidMongoName(key)) {
                    throw new Error(`Invalid field name: ${key}`);
                }
            }
            // Re-attach the original _id.
            const finalDoc = { ...updatedDoc, _id: document._id };
            onSave(finalDoc);
            setIsEditing(false);
            setError(null);
        } catch (error: any) {
            setError("Invalid JSON format. Please correct it. " + error?.message);
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg p-3 sm:p-4 shadow-lg hover:shadow-xl transition duration-300 w-full max-w-4xl mx-auto my-4">
            {/* Document Header */}
            <div className="flex justify-between items-center mb-2">
                <div className="flex space-x-2">
                    {isEditing ? (
                        <>
                            <button
                                onClick={handleEdit}
                                className="bg-green-500 text-white px-2 py-1 sm:px-4 sm:py-1 rounded hover:bg-green-400 text-xs sm:text-sm"
                            >
                                <span className="sm:hidden"><FaSave /></span>
                                <span className="hidden sm:inline">Save</span>
                            </button>
                            <button
                                onClick={() => {
                                    setIsEditing(false);
                                    setJsonContent(JSON.stringify(withoutId(document), null, 2));
                                }}
                                className="bg-red-500 text-white px-2 py-1 sm:px-4 sm:py-1 rounded hover:bg-red-400 text-xs sm:text-sm"
                            >
                                <span className="sm:hidden"><FaTimes /></span>
                                <span className="hidden sm:inline">Cancel</span>
                            </button>
                        </>
                    ) : (
                        <button
                            onClick={() => {
                                setJsonContent(JSON.stringify(withoutId(document), null, 2));
                                setIsEditing(true);
                            }}
                            className="bg-orange-500 text-white px-2 py-1 sm:px-4 sm:py-1 rounded hover:bg-orange-400 text-xs sm:text-sm"
                        >
                            <span className="sm:hidden"><FaEdit /></span>
                            <span className="hidden sm:inline">Edit</span>
                        </button>
                    )}
                    <button
                        onClick={() => onDelete(document._id)}
                        className="bg-red-500 text-white px-2 py-1 sm:px-4 sm:py-1 rounded hover:bg-red-400 text-xs sm:text-sm"
                    >
                        <span className="sm:hidden"><FaTrashAlt /></span>
                        <span className="hidden sm:inline">Delete</span>
                    </button>
                </div>
            </div>

            {/* Document Content */}
            <div className="mt-2 max-h-80 overflow-y-auto">
                {isEditing ? (
                    <>
                        <textarea
                            className="w-full h-40 sm:h-80 p-2 bg-gray-900 text-white border border-gray-700 rounded text-xs sm:text-sm"
                            value={jsonContent}
                            onChange={(e) => {
                                setJsonContent(e.target.value);
                                setError(null);
                            }}
                            title="Edit JSON content"
                            placeholder="Enter JSON content here"
                        />
                        {error && <p className="text-red-500 text-xs sm:text-sm">{error}</p>}
                    </>
                ) : (
                    <div className="text-gray-400 text-xs sm:text-sm h-40 sm:h-80 overflow-y-auto">
                        <JSONViewer value={document} style={githubDarkTheme} className="h-full" />
                    </div>
                )}
            </div>
        </div>
    );
};

export default Document;

