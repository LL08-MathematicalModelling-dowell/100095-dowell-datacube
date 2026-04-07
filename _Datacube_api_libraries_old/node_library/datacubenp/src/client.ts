// client.ts
import axios, { AxiosInstance } from "axios";
import {
  BASE_URL,
  CREATE_COLLECTION,
  CREATE_DATABASE,
  DATA_CRUD,
  DROP_COLLECTIONS,
  DROP_DATABASE,
  GET_METADATA,
  LIST_COLLECTIONS,
} from "./endpoints";
import { APIError, ValidationError } from "./exceptions";
import {
  CreateCollectionPayload,
  CreateDatabasePayload,
  CrudPayload,
  DeletePayload,
  ReadPayload,
  RequestInterface,
  UpdatePayload,
} from "./types";
import {
  validateCollectionName,
  validateCollections,
  validateDatabaseId,
} from "./validators";

export class APIClient {
  private baseUrl: string;
  private apiKey: string;
  private client: AxiosInstance;

  constructor(apiKey: string) {
    this.baseUrl = BASE_URL.replace(/\/$/, "");
    this.apiKey = apiKey;
    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: { Authorization: `Bearer ${this.apiKey}` },
      timeout: 10000,
    });
  }

  private async request<T>({
    method,
    endpoint,
    data,
    params,
  }: RequestInterface): Promise<T> {
    try {
      const response = await this.client.request<T>({
        method,
        url: endpoint,
        data,
        params: params,
      });
      return response.data;
    } catch (error: any) {
      if (error.response) {
        throw new APIError(
          error.response.status,
          error.response.data.message || "API Error",
        );
      }
      throw new APIError(500, "An unexpected error occurred.");
    }
  }

  async createDatabase(payload: CreateDatabasePayload): Promise<any> {
    validateCollections(payload.collections);
    return this.request({
      method: "POST",
      endpoint: CREATE_DATABASE,
      data: payload,
    });
  }

  async createCollection(payload: CreateCollectionPayload): Promise<any> {
    validateDatabaseId(payload.databaseId);
    validateCollections(payload.collections);
    return this.request({
      method: "POST",
      endpoint: CREATE_COLLECTION,
      data: payload,
    });
  }

  async listCollections(databaseId: string): Promise<any> {
    validateDatabaseId(databaseId);
    const params = { database_id: databaseId };
    return this.request({
      method: "GET",
      endpoint: LIST_COLLECTIONS,
      params: params,
    });
  }

  async dropCollections(payload: {
    databaseId: string;
    collectionNames: string[];
  }): Promise<any> {
    validateDatabaseId(payload.databaseId);
    if (
      !Array.isArray(payload.collectionNames) ||
      !payload.collectionNames.every((name) => typeof name === "string")
    ) {
      throw new ValidationError(
        "Collection names must be an array of strings.",
      );
    }
    return this.request({
      method: "DELETE",
      endpoint: DROP_COLLECTIONS,
      data: payload,
    });
  }

  async dropDatabase(databaseId: string): Promise<any> {
    validateDatabaseId(databaseId);
    return this.request({
      method: "DELETE",
      endpoint: DROP_DATABASE,
      data: { databaseId },
    });
  }

  async create(payload: CrudPayload): Promise<any> {
    validateDatabaseId(payload.databaseId);
    validateCollectionName(payload.collectionName);
    return this.request({ method: "POST", endpoint: DATA_CRUD, data: payload });
  }

  async read(payload: ReadPayload): Promise<any> {
    validateDatabaseId(payload.databaseId);
    validateCollectionName(payload.collectionName);
    return this.request({
      method: "GET",
      endpoint: DATA_CRUD,
      params: payload,
    });
  }

  async update(payload: UpdatePayload): Promise<any> {
    validateDatabaseId(payload.databaseId);
    validateCollectionName(payload.collectionName);
    return this.request({ method: "PUT", endpoint: DATA_CRUD, data: payload });
  }

  async delete(payload: DeletePayload): Promise<any> {
    validateDatabaseId(payload.databaseId);
    validateCollectionName(payload.collectionName);
    return this.request({
      method: "DELETE",
      endpoint: DATA_CRUD,
      data: payload,
    });
  }

  async get_metadata(payload: { database_id: string }): Promise<any> {
    return this.request({
      method: "GET",
      endpoint: GET_METADATA,
      params: payload,
    });
  }
}
