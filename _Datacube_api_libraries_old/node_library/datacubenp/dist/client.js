"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.APIClient = void 0;
// client.ts
const axios_1 = __importDefault(require("axios"));
const endpoints_1 = require("./endpoints");
const exceptions_1 = require("./exceptions");
const validators_1 = require("./validators");
class APIClient {
    constructor(apiKey) {
        this.baseUrl = endpoints_1.BASE_URL.replace(/\/$/, "");
        this.apiKey = apiKey;
        this.client = axios_1.default.create({
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
                throw new exceptions_1.APIError(error.response.status, error.response.data.message || "API Error");
            }
            throw new exceptions_1.APIError(500, "An unexpected error occurred.");
        }
    }
    async createDatabase(payload) {
        (0, validators_1.validateCollections)(payload.collections);
        return this.request({
            method: "POST",
            endpoint: endpoints_1.CREATE_DATABASE,
            data: payload,
        });
    }
    async createCollection(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        (0, validators_1.validateCollections)(payload.collections);
        return this.request({
            method: "POST",
            endpoint: endpoints_1.CREATE_COLLECTION,
            data: payload,
        });
    }
    async listCollections(databaseId) {
        (0, validators_1.validateDatabaseId)(databaseId);
        const params = { database_id: databaseId };
        return this.request({
            method: "GET",
            endpoint: endpoints_1.LIST_COLLECTIONS,
            params: params,
        });
    }
    async dropCollections(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        if (!Array.isArray(payload.collectionNames) ||
            !payload.collectionNames.every((name) => typeof name === "string")) {
            throw new exceptions_1.ValidationError("Collection names must be an array of strings.");
        }
        return this.request({
            method: "DELETE",
            endpoint: endpoints_1.DROP_COLLECTIONS,
            data: payload,
        });
    }
    async dropDatabase(databaseId) {
        (0, validators_1.validateDatabaseId)(databaseId);
        return this.request({
            method: "DELETE",
            endpoint: endpoints_1.DROP_DATABASE,
            data: { databaseId },
        });
    }
    async create(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        (0, validators_1.validateCollectionName)(payload.collectionName);
        return this.request({ method: "POST", endpoint: endpoints_1.DATA_CRUD, data: payload });
    }
    async read(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        (0, validators_1.validateCollectionName)(payload.collectionName);
        return this.request({
            method: "GET",
            endpoint: endpoints_1.DATA_CRUD,
            params: payload,
        });
    }
    async update(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        (0, validators_1.validateCollectionName)(payload.collectionName);
        return this.request({ method: "PUT", endpoint: endpoints_1.DATA_CRUD, data: payload });
    }
    async delete(payload) {
        (0, validators_1.validateDatabaseId)(payload.databaseId);
        (0, validators_1.validateCollectionName)(payload.collectionName);
        return this.request({
            method: "DELETE",
            endpoint: endpoints_1.DATA_CRUD,
            data: payload,
        });
    }
    async get_metadata(payload) {
        return this.request({
            method: "GET",
            endpoint: endpoints_1.GET_METADATA,
            params: payload,
        });
    }
}
exports.APIClient = APIClient;
