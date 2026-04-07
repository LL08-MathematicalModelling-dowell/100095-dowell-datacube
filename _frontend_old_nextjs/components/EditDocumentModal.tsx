/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import Modal from 'react-modal';

// Interface for Document
export interface DocumentData {
    [key: string]: any; // Flexible fields
}

interface EditDocumentModalProps {
    document: DocumentData;
    onSave: (updatedDoc: DocumentData) => void;
    onClose: () => void;
}

const EditDocumentModal: React.FC<EditDocumentModalProps> = ({ document, onSave, onClose }) => {
    const [updatedDoc, setUpdatedDoc] = useState<DocumentData>(document);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setUpdatedDoc({ ...updatedDoc, [e.target.name]: e.target.value });
    };

    const handleSubmit = (e: React.SyntheticEvent) => {
        e.preventDefault();
        onSave(updatedDoc);
    };

    return (
        <Modal isOpen={true} onRequestClose={onClose} style={customStyles}>
            <h2 className="text-xl font-semibold text-orange-400">Edit Document</h2>
            <form onSubmit={handleSubmit}>
                {Object.entries(updatedDoc).map(([key, value]) => {
                    if (key === "_id") {
                        return (
                            <div className="mb-4" key={key}>
                                <label className="block mb-2">{key}:</label>
                                <input
                                    type="text"
                                    name={key}
                                    value={value}
                                    readOnly // Make the _id field read-only
                                    className="border p-2 rounded w-full bg-gray-900 text-white"
                                />
                            </div>
                        );
                    }

                    // Exclude _id from editability
                    if (key !== "id") {
                        return (
                            <div className="mb-4" key={key}>
                                <label className="block mb-2">{key}:</label>
                                <input
                                    type="text"
                                    name={key}
                                    value={value}
                                    onChange={handleChange}
                                    className="border p-2 rounded w-full bg-gray-900 text-white"
                                />
                            </div>
                        );
                    }
                    return null; // Exclude other keys as necessary
                })}
                <div className="flex justify-end">
                    <button type="button" onClick={onClose} className="bg-gray-600 text-white p-2 rounded mr-2 hover:bg-gray-500">Cancel</button>
                    <button type="submit" className="bg-orange-500 text-white p-2 rounded hover:bg-orange-400">Save</button>
                </div>
            </form>
        </Modal>
    );
};

// Updated customStyles
const customStyles = {
    overlay: {
        backgroundColor: 'rgba(0, 0, 0, 0.75)', // Increased opacity for the overlay
    },
    content: {
        backgroundColor: '#1f2937',
        color: 'white',
        borderRadius: '10px',
        padding: '20px',
        maxWidth: '400px', // Set maximum width
        margin: 'auto', // Center the modal horizontally
        top: '50%', // Center vertically
        left: '50%', // Center horizontally
        right: 'auto', // Reset right
        bottom: 'auto', // Reset bottom
        transform: 'translate(-50%, -50%)', // Offset to center modal
    }
};

export default EditDocumentModal;
