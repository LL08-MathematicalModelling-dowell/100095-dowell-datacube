/** Display initials from name parts or email local-part. */
export function userInitials(
  firstName?: string | null,
  lastName?: string | null,
  email?: string | null
): string {
  const f = (firstName ?? "").trim();
  const l = (lastName ?? "").trim();
  if (f && l) return `${f[0]}${l[0]}`.toUpperCase();
  if (f.length >= 2) return f.slice(0, 2).toUpperCase();
  if (f) return f[0].toUpperCase();
  const local = (email ?? "").split("@")[0]?.trim() ?? "";
  if (local.length >= 2) return local.slice(0, 2).toUpperCase();
  if (local) return local[0].toUpperCase();
  return "?";
}
