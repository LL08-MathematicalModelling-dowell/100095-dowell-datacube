export interface RequestInterface {
  method: string;
  endpoint: string;
  data?: object;
  params?: object;
}

export interface Field {
  name: string;
  type?: string;
}

export interface Collection {
  name: string;
  fields: Field[];
}

export interface CreateDatabasePayload {
  dbName: string;
  collections: Collection[];
}

export interface CreateCollectionPayload {
  databaseId: string;
  collections: Collection[];
}

export interface CrudPayload {
  databaseId: string;
  collectionName: string;
  data: object | object[];
}

export interface ReadPayload {
  databaseId: string;
  collectionName: string;
  filters?: object;
  limit?: number;
  offset?: number;
}

export interface UpdatePayload {
  databaseId: string;
  collectionName: string;
  filters: object;
  updateData: object;
}

export interface DeletePayload {
  databaseId: string;
  collectionName: string;
  filters: object;
  softDelete?: boolean;
}

export interface DropCollectionsPayload {
  databaseId: string;
  collectionNames: string[];
}
