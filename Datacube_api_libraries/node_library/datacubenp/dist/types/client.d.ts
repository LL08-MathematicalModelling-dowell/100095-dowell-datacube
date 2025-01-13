import { CreateCollectionPayload, CreateDatabasePayload, CrudPayload, DeletePayload, ReadPayload, UpdatePayload } from "./types";
export declare class APIClient {
    private baseUrl;
    private apiKey;
    private client;
    constructor(apiKey: string);
    private request;
    createDatabase(payload: CreateDatabasePayload): Promise<any>;
    createCollection(payload: CreateCollectionPayload): Promise<any>;
    listCollections(databaseId: string): Promise<any>;
    dropCollections(payload: {
        databaseId: string;
        collectionNames: string[];
    }): Promise<any>;
    dropDatabase(databaseId: string): Promise<any>;
    create(payload: CrudPayload): Promise<any>;
    read(payload: ReadPayload): Promise<any>;
    update(payload: UpdatePayload): Promise<any>;
    delete(payload: DeletePayload): Promise<any>;
    get_metadata(payload: {
        database_id: string;
    }): Promise<any>;
}
