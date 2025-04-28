/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import JSONViewer from '@uiw/react-json-view';
import { githubDarkTheme } from '@uiw/react-json-view/githubDark';

const isValidMongoName = (name: string) => {
    const mongoNameRegex = /^(?!\.)(?!\$)(?!.*[\.\$])[a-zA-Z0-9_]+$/;
    return mongoNameRegex.test(name) && name.length > 0 && name.length <= 120;
};

interface AddDocumentProps {
    onAdd: (document: Record<string, any>) => void;
}

const AddDocument: React.FC<AddDocumentProps> = ({ onAdd }) => {
    const [jsonContent, setJsonContent] = useState<string>('');
    const [error, setError] = useState<string | null>(null);
    const [parsedDocument, setParsedDocument] = useState<any>(null); // State for parsed JSON

    const handleAdd = () => {
        try {
            const newDocument = JSON.parse(jsonContent); // Parse the JSON
            for (const key in newDocument) {
                if (!isValidMongoName(key)) {
                    throw new Error(`Invalid field name: ${key}`);
                }
            }
            onAdd(newDocument);
            setJsonContent(''); // Reset input after adding
            setError(null); // Clear error
            setParsedDocument(null); // Clear parsed document
        } catch (error: any) {
            setError('Invalid JSON format or field names. Please correct it. ' + error?.message);
            setParsedDocument(null); // Reset parsed document on error
        }
    };

    // Update parsedDocument only if jsonContent is valid JSON
    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setJsonContent(e.target.value);
        setError(null); // Clear error on input change
        try {
            setParsedDocument(JSON.parse(e.target.value)); // Try parsing
        } catch {
            setParsedDocument(null); // Reset if parsing fails
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
            <h2 className="text-lg font-semibold text-white mb-2">Add New Document</h2>
            <textarea
                className="w-full h-40 p-2 bg-gray-900 text-white border border-gray-700 rounded"
                placeholder="Enter document in JSON format"
                value={jsonContent}
                onChange={handleChange} // Use the new handleChange
            />
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <button
                onClick={handleAdd}
                className="bg-green-500 text-white px-4 py-2 rounded mt-2 hover:bg-green-400"
            >
                Add Document
            </button>
            {/* JSON Viewer to show the formatted JSON */}
            {parsedDocument && (
                <div className="mt-4">
                    <h3 className="text-sm font-semibold text-white">Preview:</h3>
                    <div className="h-40 overflow-y-auto">
                        <JSONViewer value={parsedDocument} style={githubDarkTheme} />
                    </div>
                </div>
            )}
        </div>
    );
};

export default AddDocument;