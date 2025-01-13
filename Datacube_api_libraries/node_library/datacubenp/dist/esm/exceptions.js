export class APIError extends Error {
    constructor(status, message) {
        super(message);
        this.status = status;
        this.message = message;
        this.name = 'APIError';
    }
}
export class ValidationError extends Error {
    constructor(message) {
        super(message);
        this.name = 'ValidationError';
    }
}
