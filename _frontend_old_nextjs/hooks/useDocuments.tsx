// hooks/useDocuments.ts
import client from '@/lib/axiosClient';
import {
    useInfiniteQuery,
    useMutation,
    useQueryClient,
} from '@tanstack/react-query';

// --- Types ---
export interface DocumentsResponse<T = unknown> {
    success: boolean;
    data: T[];
    pagination: {
        page: number;
        pageSize: number;
        total: number;
    };
}

// --- Fetch documents with infinite scroll ---
interface UseDocumentsOptions {
    databaseId: string;
    collectionName: string;
    pageSize?: number;
    filters?: Record<string, string | number | boolean>;
}

export const useDocuments = ({
    databaseId,
    collectionName,
    pageSize = 10,
    filters = {},
}: UseDocumentsOptions) => {
    if (!databaseId || !collectionName) {
        throw new Error('databaseId and collectionName are required');
    }

    const endpoint = `/database/${databaseId}/${collectionName}`;

    return useInfiniteQuery<DocumentsResponse, Error>(
        {
            queryKey: ['documents', databaseId, collectionName],
            queryFn: ({ pageParam = 1 }) =>
                client
                    .get<DocumentsResponse>(endpoint, {
                        params: {
                            filters: JSON.stringify(filters),
                            page: pageParam,
                            pageSize,
                        },
                    })
                    .then((res) => res.data),
            getNextPageParam: (lastPage) => {
                const { page, total } = lastPage.pagination;
                return page < Math.ceil(total / pageSize) ? page + 1 : undefined;
            },
            initialPageParam: 1, // Add this line
            staleTime: 1000 * 60 * 60, // 1 hour        
        }
    );
};

// --- Create a document ---
export const useCreateDocument = (
    databaseId: string,
    collectionName: string
) => {
    const queryClient = useQueryClient();
    const endpoint = `/database/${databaseId}/${collectionName}`;

    return useMutation<
        { success: boolean; id?: string },
        Error, { data: Record<string, unknown> }
    >(
        {
            mutationFn: (doc) =>
                client
                    .post(endpoint, doc)
                    .then((res) => res.data),
            onSuccess: () => {
                queryClient.invalidateQueries({
                    queryKey: ['documents', databaseId, collectionName],
                });
            },
        }
    );
};

// --- Update a document ---
export const useUpdateDocument = (
    databaseId: string,
    collectionName: string
) => {
    const queryClient = useQueryClient();
    const endpoint = `/database/${databaseId}/${collectionName}`;

    return useMutation<
        { success: boolean },
        Error,
        Record<string, unknown>
    >(
        {
            mutationFn: (doc) =>
                client
                    .put(endpoint, { data: doc })
                    .then((res) => res.data),
            onSuccess: () => {
                queryClient.invalidateQueries({
                    queryKey: ['documents', databaseId, collectionName],
                });
            },
        }
    );
};

// --- Delete a document ---
export const useDeleteDocument = (
    databaseId: string,
    collectionName: string
) => {
    const queryClient = useQueryClient();
    const endpoint = `/database/${databaseId}/${collectionName}`;

    return useMutation<
        { success: boolean },
        Error,
        string
    >(
        {
            mutationFn: (documentId) =>
                client
                    .delete(endpoint, { data: { documentId } })
                    .then((res) => res.data),
            onSuccess: () => {
                queryClient.invalidateQueries({
                    queryKey: ['documents', databaseId, collectionName],
                });
            },
        }
    );
};



// /* eslint-disable @typescript-eslint/no-explicit-any */
// import client from "@/lib/axiosClient";
// import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";

// interface Pagination {
//     page: number;
//     page_size: number;
//     total: number; // Total records

// }

// export interface DatabaseResponse {
//     data: object[];
//     pagination: Pagination;
// }

// interface DocumentsQueryParams {
//     page_size?: number;
//     filters?: object;
//     path?: string;
//     databaseId: string;
//     collectionName: string;
// }

// const useDocuments = ({
//     page_size = 10,
//     filters = {},
//     path = "/database/",
//     databaseId,
//     collectionName,
// }: DocumentsQueryParams) => {
//     if (!databaseId || !collectionName) {
//         throw new Error("Database ID and Collection Name are required.");
//     }

//     const fullPath = `${path}${databaseId}/${collectionName}/`;

//     return useInfiniteQuery<DatabaseResponse, Error>({
//         // Set up the query key
//         queryKey: ["documents", {
//             databaseId,
//             collectionName,
//             page_size,
//             filters,
//         }],
//         // Fetch function
//         queryFn: ({ pageParam = 1 }) =>
//             client
//                 .get(fullPath, {
//                     params: {
//                         filters: JSON.stringify(filters),
//                         page: pageParam,
//                         page_size,
//                     },
//                 })
//                 .then((res) => res.data).catch((err) => err.response.data),
//         // Handle pagination
//         getNextPageParam: (lastPage) => {
//             // Check if there's another page to load
//             return lastPage.pagination.page < Math.ceil(lastPage.pagination.total / page_size)
//                 ? lastPage.pagination.page + 1
//                 : undefined;
//         },
//         initialPageParam: 1,
//         staleTime: 1000 * 60 * 60, // 1 hour
//     });
// };

// export default useDocuments;


// export const useCreateDocument = (databaseId: string, collectionName: string) => {
//     const queryClient = useQueryClient();
//     const fullPath = `/database/${databaseId}/${collectionName}/`; // Ensure this path is correctly set up
//     return useMutation({
//         mutationFn: (data: object) =>
//             client.post(fullPath, { data }).catch((err) => err.response.data),
//         onSuccess: () => {
//             // Invalidate the documents query to refetch data after mutation
//             queryClient.invalidateQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//             // Optionally, you can also refetch the documents query to get the latest data
//             queryClient.refetchQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//         }
//     });
// };


// export const useUpdateDocument = (databaseId: string, collectionName: string) => {
//     const fullPath = `/database/${databaseId}/${collectionName}/`;
//     const queryClient = useQueryClient();

//     return useMutation({
//         mutationFn: (data: { [key: string]: any }) =>
//             client.put(`${fullPath}`, { data }).catch((err) => {
//                 throw new Error(JSON.stringify(err.response.data));
//             }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//             queryClient.refetchQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//         }
//     });
// };


// export const useDeleteDocument = (databaseId: string, collectionName: string) => {
//     const queryClient = useQueryClient();
//     const fullPath = `/database/${databaseId}/${collectionName}/`;

//     return useMutation({
//         mutationFn: (documentId: string) =>
//             client
//                 .delete(fullPath, { data: { documentId } })
//                 .catch((err) => {
//                     throw new Error(JSON.stringify(err.response.data));
//                 }),
//         onSuccess: () => {
//             queryClient.invalidateQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//             queryClient.refetchQueries({
//                 queryKey: ["documents", { databaseId, collectionName }],
//             });
//         },
//     });
// };

