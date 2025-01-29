export declare class APIError extends Error {
    status: number;
    message: string;
    constructor(status: number, message: string);
}
export declare class ValidationError extends Error {
    constructor(message: string);
}
