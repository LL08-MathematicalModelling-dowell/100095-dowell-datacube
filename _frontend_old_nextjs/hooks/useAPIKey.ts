// File: /hooks/useAPIKey.ts
import client from "@/lib/axiosClient";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface createApiKeyProps {
  userId: string;
  description: string;
  expiresAt: string;
}

export interface updateApiKeyProps {
  userId: string;
  apiKeyId: string;
  description: string;
  expiresAt: string;
}

export interface deleteApiKeyProps {
  userId: string;
  apiKeyId: string;
}

// Hook to get API keys.
export const useGetApiKeys = (userId: string) => {
  return useQuery({
    queryKey: ["apiKeys", userId],
    queryFn: async () => {
      const response = await client.get(`/apikey?userId=${userId}`);
      return response.data.apiKeys;
    },
  });
};

// Hook to create an API key.
export const useCreateApiKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: createApiKeyProps) => {
      const response = await client.post(`/apikey`, data);
      return response.data;
    },
    onSuccess: (newKey, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["apiKeys", variables.userId],
      });
    },
  });
};

// Hook to update an API key.
export const useUpdateApiKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: updateApiKeyProps) => {
      const response = await client.put("/apikey", data);
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["apiKeys", variables.userId],
      });
    },
  });
};

// Hook to delete an API key.
export const useDeleteApiKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: deleteApiKeyProps) => {
      const response = await client.delete("/apikey", { data });
      return response.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["apiKeys", variables.userId],
      });
    },
  });
};
