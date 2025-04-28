import client from "@/lib/axiosClient";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// --- Types ---
export interface Collection {
  id: string;
  name: string;
  fields: string[];
  numDocuments: number;
}

interface CollectionsResponse {
  success: boolean;
  collections: Collection[];
}

// --- Fetch collections for a given database ---
export const useCollections = (databaseId: string) => {
  return useQuery<CollectionsResponse, Error>({
    queryKey: ["collections", databaseId],
    queryFn: () =>
      client
        .get<CollectionsResponse>(`/database/${databaseId}/`)
        .then((res) => res.data),
    staleTime: 1000 * 60 * 60, // 1 hour
    retry: false,
  });
};

// --- Create a new collection ---
export interface CreateCollectionInput {
  name: string;
  fields: string[];
}

interface CreateCollectionResponse {
  success: boolean;
  message: string;
}

export const useCreateCollection = (databaseId: string) => {
  const queryClient = useQueryClient();
  return useMutation<CreateCollectionResponse, Error, CreateCollectionInput>({
    mutationFn: (data) =>
      client
        .post<CreateCollectionResponse>(`/api/database/${databaseId}/`, data)
        .then((res) => res.data),
    onSuccess: () => {
      // Invalidate the collections query to refetch
      queryClient.invalidateQueries({
        queryKey: ["collections", databaseId],
      });
    },
  });
};

// import client from "@/lib/axiosClient";
// import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";

// export interface Collection {
//   name: string;
//   num_documents: number;
// }

// interface CollectionResponse {
//   success: boolean;
//   message: string;
//   collections: Collection[];
// }

// interface CollectionQueryParams {
//   database_id: string;
// }

// const useCollections = ({ database_id }: CollectionQueryParams) => {
//   return useQuery<CollectionResponse, Error>({
//     queryKey: ["collections", { database_id }],
//     queryFn: () =>
//       client
//         .get(`/database/${database_id}`)
//         .then((res) => res.data)
//         .catch((err) => err.response.data),
//     staleTime: 1000 * 60 * 60, // 1 hour
//   });
// };

// export default useCollections;

// interface CreateCollectionRequest {
//   name: string;
//   fields: Array<{
//     name: string;
//     type?: string;
//   }>;
// }

// const useCreateCollection = (databaseId: string) => {
//   const queryClient = useQueryClient();
//   return useMutation({
//     mutationFn: (data: CreateCollectionRequest) =>
//       client
//         .post(`/database/${databaseId}`, data)
//         .then((res) => res.data)
//         .catch((err) => err.response.data),
//     onSuccess: () => {
//       // Invalidate the collections query to refetch
//       queryClient.invalidateQueries({
//         queryKey: ["collections", { database_id: databaseId }],
//       });
//     },
//   });
// };

// export { useCreateCollection };
