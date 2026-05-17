import axios from "axios";

/** Flatten DRF / Django error payloads into a single user-facing string. */
export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (data && typeof data === "object") {
      const o = data as Record<string, unknown>;
      if (typeof o.error === "string") return o.error;
      if (typeof o.detail === "string") return o.detail;
      if (typeof o.message === "string") return o.message;
      const firstKey = Object.keys(o)[0];
      const firstVal = firstKey ? o[firstKey] : undefined;
      if (Array.isArray(firstVal) && typeof firstVal[0] === "string") {
        return `${firstKey}: ${firstVal[0]}`;
      }
      if (typeof firstVal === "string") return `${firstKey}: ${firstVal}`;
    }
    if (err.message) return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

export function isEmailUnverifiedResponse(err: unknown): boolean {
  if (!axios.isAxiosError(err)) return false;
  if (err.response?.status !== 403) return false;
  const data = err.response.data as { code?: string } | undefined;
  return data?.code === "email_unverified";
}
