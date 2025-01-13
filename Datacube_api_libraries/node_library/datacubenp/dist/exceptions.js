"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ValidationError = exports.APIError = void 0;
class APIError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
        this.message = message;
        this.name = 'APIError';
    }
}
exports.APIError = APIError;
class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}
exports.ValidationError = ValidationError;
