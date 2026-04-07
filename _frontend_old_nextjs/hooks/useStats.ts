// hooks/useStats.ts
import { useQuery } from "@tanstack/react-query";
import client from "@/lib/axiosClient";

export interface Stats {
  databases: number;
  collections: number;
  documents: number;
  mostFrequentDb: string | null;
  mostFrequentCollection: string | null;
  readsPerDay: number[];
  writesPerDay: number[];
  readsPerMonth: number[];
  writesPerMonth: number[];
}

export function useStats() {
  return useQuery<Stats, Error>({
    queryKey: ["stats"],
    queryFn: () =>
      client.get("/stats").then((res) => {
        if (res.status !== 200) {
          throw new Error("Error fetching stats");
        }
        return res.data.data;
      }),
    refetchInterval: 60000, // 1 minute
    refetchOnWindowFocus: false,
    staleTime: 60000, // 1 minute
  });
}
