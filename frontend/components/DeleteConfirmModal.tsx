import React from 'react';
import Modal from 'react-modal';

// Set your app element for accessibility (replace '#root' with your actual root element ID if different)
// Modal.setAppElement('#root');

interface DeleteConfirmModalProps {
    title?: string;
    message?: string;
    onConfirm: () => void;
    onClose: () => void;
}

const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({ title, message, onConfirm, onClose }) => {
    return (
        <Modal isOpen={true} onRequestClose={onClose} style={customStyles}>
            <h2 className="text-xl font-semibold text-orange-400">Confirm Deletion</h2>
            {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
            <p className="mt-2 text-gray-300">{message || "Are you sure you want to delete this item?"}</p>
            <div className="flex justify-end mt-4">
                <button type="button" onClick={onClose} className="bg-gray-600 text-white p-2 rounded mr-2 hover:bg-gray-500">Cancel</button>
                <button onClick={onConfirm} className="bg-red-500 text-white p-2 rounded hover:bg-red-400">Delete</button>
            </div>
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

export default DeleteConfirmModal;