// client.ts
import axios from "axios";
import { BASE_URL, CREATE_COLLECTION, CREATE_DATABASE, DATA_CRUD, DROP_COLLECTIONS, DROP_DATABASE, GET_METADATA, LIST_COLLECTIONS, } from "./endpoints";
import { APIError, ValidationError } from "./exceptions";
import { validateCollectionName, validateCollections, validateDatabaseId, } from "./validators";
export class APIClient {
    constructor(apiKey) {
        this.baseUrl = BASE_URL.replace(/\/$/, "");
        this.apiKey = apiKey;
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: { Authorization: `Bearer ${this.apiKey}` },
            timeout: 10000,
        });
    }
    async request({ method, endpoint, data, params, }) {
        try {
            const response = await this.client.request({
                method,
                url: endpoint,
                data,
                params: params,
            });
            return response.data;
        }
        catch (error) {
            if (error.response) {
                throw new APIError(error.response.status, error.response.data.message || "API Error");
            }
            throw new APIError(500, "An unexpected error occurred.");
        }
    }
    async createDatabase(payload) {
        validateCollections(payload.collections);
        return this.request({
            method: "POST",
            endpoint: CREATE_DATABASE,
            data: payload,
        });
    }
    async createCollection(payload) {
        validateDatabaseId(payload.databaseId);
        validateCollections(payload.collections);
        return this.request({
            method: "POST",
            endpoint: CREATE_COLLECTION,
            data: payload,
        });
    }
    async listCollections(databaseId) {
        validateDatabaseId(databaseId);
        const params = { database_id: databaseId };
        return this.request({
            method: "GET",
            endpoint: LIST_COLLECTIONS,
            params: params,
        });
    }
    async dropCollections(payload) {
        validateDatabaseId(payload.databaseId);
        if (!Array.isArray(payload.collectionNames) ||
            !payload.collectionNames.every((name) => typeof name === "string")) {
            throw new ValidationError("Collection names must be an array of strings.");
        }
        return this.request({
            method: "DELETE",
            endpoint: DROP_COLLECTIONS,
            data: payload,
        });
    }
    async dropDatabase(databaseId) {
        validateDatabaseId(databaseId);
        return this.request({
            method: "DELETE",
            endpoint: DROP_DATABASE,
            data: { databaseId },
        });
    }
    async create(payload) {
        validateDatabaseId(payload.databaseId);
        validateCollectionName(payload.collectionName);
        return this.request({ method: "POST", endpoint: DATA_CRUD, data: payload });
    }
    async read(payload) {
        validateDatabaseId(payload.databaseId);
        validateCollectionName(payload.collectionName);
        return this.request({
            method: "GET",
            endpoint: DATA_CRUD,
            params: payload,
        });
    }
    async update(payload) {
        validateDatabaseId(payload.databaseId);
        validateCollectionName(payload.collectionName);
        return this.request({ method: "PUT", endpoint: DATA_CRUD, data: payload });
    }
    async delete(payload) {
        validateDatabaseId(payload.databaseId);
        validateCollectionName(payload.collectionName);
        return this.request({
            method: "DELETE",
            endpoint: DATA_CRUD,
            data: payload,
        });
    }
    async get_metadata(payload) {
        return this.request({
            method: "GET",
            endpoint: GET_METADATA,
            params: payload,
        });
    }
}
