// hooks/useSettings.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { signOut } from "next-auth/react";

/** Fetch current user settings */
async function fetchSettings() {
  const res = await fetch("/api/settings");
  if (!res.ok) throw new Error("Failed to fetch settings");
  const json = await res.json();
  return json.settings as {
    notifications: { email: boolean; push: boolean; inApp: boolean };
    theme: string;
    language: string;
  };
}

/** Patch settings on server */
async function patchSettings(
  updates: Partial<{
    notifications: { email: boolean; push: boolean; inApp: boolean };
    theme: string;
    language: string;
  }>
) {
  const res = await fetch("/api/settings", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Update failed");
  }
  const json = await res.json();
  return json.settings;
}

/** Call account‐deletion endpoint */
async function deleteAccount() {
  const res = await fetch("/api/user", { method: "DELETE" });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || "Delete failed");
  }
  return true;
}

/** Hook to read settings */
export function useSettingsQuery() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: fetchSettings,
    staleTime: 1000 * 60 * 60, // 5 minutes
  });
}

/** Hook to update settings */
export function useUpdateSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: patchSettings,
    onSuccess(data) {
      qc.setQueryData(["settings"], data); // update the cache
    },
    onError(error) {
      console.error("Update failed", error);
    },
  });
}

/** Hook to delete account */
export function useDeleteAccount() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteAccount,
    onSuccess() {
      qc.clear(); // clear all queries
      signOut({ redirect: true, callbackUrl: "/" });
    },
    onError(error) {
      console.error("Delete failed", error);
    },
  });
}
