// hooks/useDatabase.ts
import client from "@/lib/axiosClient";
import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";

// --- Types (camelCase) ---
export interface Database {
  id: string;
  name: string;
  numCollections: number;
  description: string;
  createdAt: string;
}

interface Pagination {
  page: number;
  pageSize: number;
  total: number;
}

interface DatabaseResponse {
  success: boolean;
  data: Database[];
  pagination: Pagination;
}

// --- Infinite list hook ---
export const useDatabases = ({
  pageSize = 10,
  filter = "",
  path = "/database/",
} = {}) => {
  return useInfiniteQuery<DatabaseResponse, Error>({
    queryKey: ["databases", { pageSize, filter }],
    queryFn: ({ pageParam = 1 }) =>
      client
        .get<DatabaseResponse>(path, {
          params: { page: pageParam, pageSize, filter },
        })
        .then((res) => res.data),
    getNextPageParam: (lastPage) => {
      const { page, total } = lastPage.pagination;
      const fetched = lastPage.pagination.page * lastPage.data.length;
      return fetched < total ? page + 1 : undefined;
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
    initialPageParam: 1, // Added initialPageParam
  });
};

// --- Create database mutation ---
export interface CreateDatabaseInput {
  dbName: string; // matches server schema
  description?: string;
  collections: {
    name: string;
    fields?: string[]; // strings only
  }[];
}

interface CreateDatabaseResponse {
  success: boolean;
  message: string;
  database: { id: string; name: string };
  collections: { name: string; fields: string[] }[];
}

export const useCreateDatabase = () => {
  const queryClient = useQueryClient();
  return useMutation<CreateDatabaseResponse, Error, CreateDatabaseInput>({
    mutationFn: (newDatabase) =>
      client
        .post<CreateDatabaseResponse>("/database", newDatabase)
        .then((res) => res.data),
    onSuccess: () => {
      // Invalidate query to refetch the updated list of databases
      queryClient.invalidateQueries({ queryKey: ["databases"] });
    },
    onError: (error) => {
      console.error("Error creating database:", error);
    },
  });
};
