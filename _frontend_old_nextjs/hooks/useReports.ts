import { useQuery } from "@tanstack/react-query";

export interface HistoryItem {
  date: string;
  totalRecords: number;
//   avgQueryTime: number;
  recordsAdded: number;
  recordsRemoved: number;
}

export interface ReportsPayload {
  totalRecords: number;
//   avgQueryTime: number;
  recordsAddedPerWeek: number[];
  recordsRemovedPerWeek: number[];
  history: HistoryItem[];
}

export function useReports() {
  return useQuery<ReportsPayload, Error>({
    queryKey: ["reports"],
    queryFn: async () => {
      const response = await fetch("/api/reports");
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      const json = await response.json();
      return json.data;
    },
    refetchInterval: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  });
}
