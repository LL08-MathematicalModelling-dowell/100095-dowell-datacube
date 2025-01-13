// validators.ts

import { ValidationError } from "./exceptions";

/**
 * Validates if a string is a valid MongoDB ObjectId.
 * @param id - The string to validate.
 */
export function validateDatabaseId(id: string): void {
  if (!id || typeof id !== "string" || !/^[a-fA-F0-9]{24}$/.test(id)) {
    throw new ValidationError(
      "Invalid database ID. Must be a 24-character hexadecimal string.",
    );
  }
}

/**
 * Validates if a collection name is a non-empty string.
 * @param name - The collection name to validate.
 */
export function validateCollectionName(name: string): void {
  if (!name || typeof name !== "string" || !/^[\w-]+$/.test(name)) {
    throw new ValidationError(
      "Collection name must be a non-empty string containing only alphanumeric characters, underscores, or hyphens.",
    );
  }
}

/**
 * Validates the structure of collections.
 * @param collections - The collections to validate.
 */
export function validateCollections(
  collections: Array<{
    name: string;
    fields: Array<{ name: string; type?: string }>;
  }>,
): void {
  if (!Array.isArray(collections)) {
    throw new ValidationError("Collections must be an array.");
  }

  collections.forEach((collection) => {
    if (!collection.name || typeof collection.name !== "string") {
      throw new ValidationError(
        'Each collection must have a "name" property as a non-empty string.',
      );
    }

    if (!Array.isArray(collection.fields)) {
      throw new ValidationError(
        `The "fields" property in collection "${collection.name}" must be an array.`,
      );
    }

    collection.fields.forEach((field) => {
      if (!field.name || typeof field.name !== "string") {
        throw new ValidationError(
          `Each field in collection "${collection.name}" must have a "name" property as a non-empty string.`,
        );
      }

      if (field.type && typeof field.type !== "string") {
        throw new ValidationError(
          `Field "${field.name}" in collection "${collection.name}" must have a "type" property as a string.`,
        );
      }
    });
  });
}

/**
 * Validates the structure of a document.
 * @param document - The document to validate.
 */
export function validateDocument(document: object): void {
  if (!document || typeof document !== "object" || Array.isArray(document)) {
    throw new ValidationError("Document must be a non-array object.");
  }
}
