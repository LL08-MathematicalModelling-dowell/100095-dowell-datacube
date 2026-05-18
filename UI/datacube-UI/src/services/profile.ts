import api, { API_ORIGIN } from "./api";

export interface UserProfile {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  is_email_verified: boolean;
  auth_method: string;
  has_avatar: boolean;
}

export const PROFILE_QUERY_KEY = ["user", "profile"] as const;
export const AVATAR_QUERY_KEY = ["user", "avatar"] as const;

export const AVATAR_PATH = "/core/profile/avatar/";

/** Authenticated avatar URL (for img src with fetch — prefer blob helper). */
export function avatarAbsoluteUrl(): string {
  return `${API_ORIGIN}${AVATAR_PATH}`;
}

export async function fetchProfile(): Promise<UserProfile> {
  return api.get("/core/profile");
}

export async function patchProfile(body: {
  firstName?: string;
  lastName?: string;
}): Promise<UserProfile> {
  return api.patch("/core/profile/", body);
}

export async function uploadAvatar(file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  await api.raw.post(AVATAR_PATH, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export async function deleteAvatar(): Promise<void> {
  await api.raw.delete(AVATAR_PATH);
}

export async function fetchAvatarBlobUrl(): Promise<string | null> {
  try {
    const res = await api.raw.get(AVATAR_PATH, { responseType: "blob" });
    return URL.createObjectURL(res.data);
  } catch {
    return null;
  }
}

export async function deleteAccount(): Promise<void> {
  await api.delete("/core/account/");
}

export async function resendVerificationEmail(): Promise<void> {
  await api.post("/core/verify-email/resend/");
}
