/**
 * Validates if a string is a valid MongoDB ObjectId.
 * @param id - The string to validate.
 */
export declare function validateDatabaseId(id: string): void;
/**
 * Validates if a collection name is a non-empty string.
 * @param name - The collection name to validate.
 */
export declare function validateCollectionName(name: string): void;
/**
 * Validates the structure of collections.
 * @param collections - The collections to validate.
 */
export declare function validateCollections(collections: Array<{
    name: string;
    fields: Array<{
        name: string;
        type?: string;
    }>;
}>): void;
/**
 * Validates the structure of a document.
 * @param document - The document to validate.
 */
export declare function validateDocument(document: object): void;
