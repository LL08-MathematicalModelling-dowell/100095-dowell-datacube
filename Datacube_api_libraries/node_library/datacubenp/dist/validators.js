"use strict";
// validators.ts
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateDatabaseId = validateDatabaseId;
exports.validateCollectionName = validateCollectionName;
exports.validateCollections = validateCollections;
exports.validateDocument = validateDocument;
const exceptions_1 = require("./exceptions");
/**
 * Validates if a string is a valid MongoDB ObjectId.
 * @param id - The string to validate.
 */
function validateDatabaseId(id) {
    if (!id || typeof id !== "string" || !/^[a-fA-F0-9]{24}$/.test(id)) {
        throw new exceptions_1.ValidationError("Invalid database ID. Must be a 24-character hexadecimal string.");
    }
}
/**
 * Validates if a collection name is a non-empty string.
 * @param name - The collection name to validate.
 */
function validateCollectionName(name) {
    if (!name || typeof name !== "string" || !/^[\w-]+$/.test(name)) {
        throw new exceptions_1.ValidationError("Collection name must be a non-empty string containing only alphanumeric characters, underscores, or hyphens.");
    }
}
/**
 * Validates the structure of collections.
 * @param collections - The collections to validate.
 */
function validateCollections(collections) {
    if (!Array.isArray(collections)) {
        throw new exceptions_1.ValidationError("Collections must be an array.");
    }
    collections.forEach((collection) => {
        if (!collection.name || typeof collection.name !== "string") {
            throw new exceptions_1.ValidationError('Each collection must have a "name" property as a non-empty string.');
        }
        if (!Array.isArray(collection.fields)) {
            throw new exceptions_1.ValidationError(`The "fields" property in collection "${collection.name}" must be an array.`);
        }
        collection.fields.forEach((field) => {
            if (!field.name || typeof field.name !== "string") {
                throw new exceptions_1.ValidationError(`Each field in collection "${collection.name}" must have a "name" property as a non-empty string.`);
            }
            if (field.type && typeof field.type !== "string") {
                throw new exceptions_1.ValidationError(`Field "${field.name}" in collection "${collection.name}" must have a "type" property as a string.`);
            }
        });
    });
}
/**
 * Validates the structure of a document.
 * @param document - The document to validate.
 */
function validateDocument(document) {
    if (!document || typeof document !== "object" || Array.isArray(document)) {
        throw new exceptions_1.ValidationError("Document must be a non-array object.");
    }
}
