import Modal from 'react-modal';
import React, { useEffect, useRef } from 'react';

interface ErrorModalProps {
    isOpen: boolean;
    onRequestClose: () => void;
    errorMessage: string;
}

const customStyles = {
    overlay: {
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        zIndex: 1000, // Ensure the modal is above other content
    },
    content: {
        backgroundColor: '#333',
        color: '#fff',
        border: 'none',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        maxWidth: '400px',
        width: '90%',
        height: '180px',
        margin: 'auto',
        position: 'fixed',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        transition: 'transform 0.3s ease-out',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)', // Optional shadow for depth
    },
};

// const customStyles = {

//     content: {
//         backgroundColor: '#333',
//         color: '#fff',
//         border: 'none',
//         borderRadius: '0.5rem',
//         padding: '1.5rem',
//         maxWidth: '400px',
//         margin: 'auto',
//         position: 'relative',
//         top: '50%',
//         left: '50%',
//         transform: 'translate(-50%, -50%)',
//         transition: 'transform 0.3s ease-out',
//     },
// };

const ErrorModal: React.FC<ErrorModalProps> = ({ isOpen, onRequestClose, errorMessage }) => {
    const modalRef = useRef<HTMLDivElement>(null);

    // Focus management: Trap focus inside the modal
    useEffect(() => {
        if (isOpen && modalRef.current) {
            const focusableElements = modalRef.current.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            ) as NodeListOf<HTMLElement>;
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            }
        }
    }, [isOpen]);

    return (
        <Modal
            isOpen={isOpen}
            onRequestClose={onRequestClose}
            style={customStyles}
            ariaHideApp={false}
            contentLabel="Error Modal"
        >
            <div ref={modalRef}>
                <h2 id="modal-title" className="text-lg font-semibold text-orange-400">
                    Error
                </h2>
                <p id="modal-description" className="text-red-500">
                    {errorMessage}
                </p>
                <button
                    onClick={onRequestClose}
                    className="bg-red-500 text-white p-2 mt-4 rounded hover:bg-red-400 focus:outline-none focus:ring-2 focus:ring-red-500"
                >
                    Close
                </button>
            </div>
        </Modal>
    );
};

export default ErrorModal;