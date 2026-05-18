import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  AlertTriangle,
  Camera,
  CheckCircle2,
  KeyRound,
  Mail,
  Shield,
  Trash2,
  XCircle,
} from "lucide-react";
import { UserAvatar } from "../components/profile/UserAvatar.tsx";
import { Card, PageHeader } from "../components/ui/Card.tsx";
import { QueryErrorBlock, RefreshButton } from "../components/ui/QueryRefresh.tsx";
import { getApiErrorMessage } from "../lib/apiErrors.ts";
import { cn } from "../lib/cn.ts";
import { btnPrimaryCn, btnSecondaryCn, inputCn } from "../lib/uiClasses.ts";
import {
  AVATAR_QUERY_KEY,
  deleteAccount,
  deleteAvatar,
  fetchProfile,
  patchProfile,
  PROFILE_QUERY_KEY,
  resendVerificationEmail,
  uploadAvatar,
  type UserProfile,
} from "../services/profile.ts";
import useAuthStore from "../store/authStore.ts";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrator",
  analyst: "Analyst",
  developer: "Developer",
};

const AUTH_LABELS: Record<string, string> = {
  password: "Email & password",
  google: "Google",
  github: "GitHub",
  otp: "Email OTP",
};

const ALLOWED_AVATAR = ["image/jpeg", "image/png", "image/webp", "image/gif"];
const MAX_AVATAR_MB = 3;

export default function ProfilePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { logout, setFirstName } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [firstName, setFirstNameLocal] = useState("");
  const [lastName, setLastNameLocal] = useState("");
  const [deleteEmail, setDeleteEmail] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [formInitialized, setFormInitialized] = useState(false);

  const profileQuery = useQuery({
    queryKey: PROFILE_QUERY_KEY,
    queryFn: fetchProfile,
  });

  const profile = profileQuery.data;

  useEffect(() => {
    if (profile && !formInitialized) {
      setFirstNameLocal(profile.firstName ?? "");
      setLastNameLocal(profile.lastName ?? "");
      setFormInitialized(true);
    }
  }, [profile, formInitialized]);

  const saveProfileMutation = useMutation({
    mutationFn: () =>
      patchProfile({
        firstName: firstName.trim(),
        lastName: lastName.trim(),
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(PROFILE_QUERY_KEY, data);
      setFirstName(data.firstName);
      toast.success("Profile updated");
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const avatarUploadMutation = useMutation({
    mutationFn: (file: File) => uploadAvatar(file),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: PROFILE_QUERY_KEY });
      await queryClient.invalidateQueries({ queryKey: AVATAR_QUERY_KEY });
      toast.success("Profile photo updated");
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const avatarRemoveMutation = useMutation({
    mutationFn: deleteAvatar,
    onSuccess: async () => {
      queryClient.setQueryData<UserProfile | undefined>(PROFILE_QUERY_KEY, (old) =>
        old ? { ...old, has_avatar: false } : old
      );
      queryClient.removeQueries({ queryKey: AVATAR_QUERY_KEY });
      toast.success("Profile photo removed");
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const resendMutation = useMutation({
    mutationFn: resendVerificationEmail,
    onSuccess: () => toast.success("Verification email sent"),
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: () => {
      toast.success("Account deactivated");
      logout();
      navigate("/", { replace: true });
    },
    onError: (err) => toast.error(getApiErrorMessage(err)),
  });

  const handleAvatarPick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    if (!ALLOWED_AVATAR.includes(file.type)) {
      toast.error("Use JPEG, PNG, WebP, or GIF");
      return;
    }
    if (file.size > MAX_AVATAR_MB * 1024 * 1024) {
      toast.error(`Image must be under ${MAX_AVATAR_MB} MB`);
      return;
    }
    avatarUploadMutation.mutate(file);
  };

  const dirty =
    profile &&
    (firstName.trim() !== (profile.firstName ?? "") ||
      lastName.trim() !== (profile.lastName ?? ""));

  const canDelete =
    profile && deleteEmail.trim().toLowerCase() === profile.email.toLowerCase();

  return (
    <div>
      <PageHeader
        title="Profile & account"
        description="Manage your identity, security settings, and account lifecycle."
        action={
          <RefreshButton
            onClick={() => profileQuery.refetch()}
            isRefreshing={profileQuery.isFetching}
          />
        }
      />

      {profileQuery.isError && (
        <QueryErrorBlock
          message={getApiErrorMessage(profileQuery.error)}
          onRetry={() => profileQuery.refetch()}
        />
      )}

      {profileQuery.isLoading && (
        <p className="text-sm text-[var(--text-muted)]">Loading profile…</p>
      )}

      {profile && (
        <div className="space-y-6">
          <Card title="Profile photo" subtitle="JPEG, PNG, WebP, or GIF — max 3 MB">
            <div className="flex flex-col items-start gap-6 sm:flex-row sm:items-center">
              <UserAvatar profile={profile} size="xl" />
              <div className="flex flex-wrap gap-3">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept={ALLOWED_AVATAR.join(",")}
                  className="hidden"
                  onChange={handleAvatarPick}
                />
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={avatarUploadMutation.isPending}
                  className={btnPrimaryCn("w-auto px-5")}
                >
                  <Camera className="h-4 w-4" />
                  {avatarUploadMutation.isPending ? "Uploading…" : "Upload photo"}
                </button>
                {profile.has_avatar && (
                  <button
                    type="button"
                    onClick={() => avatarRemoveMutation.mutate()}
                    disabled={avatarRemoveMutation.isPending}
                    className={btnSecondaryCn("w-auto px-5")}
                  >
                    Remove photo
                  </button>
                )}
              </div>
            </div>
            <p className="mt-4 text-xs text-[var(--text-subtle)]">
              Without a photo, your initials are shown across the app.
            </p>
          </Card>

          <Card title="Personal information">
            <form
              className="grid gap-4 sm:grid-cols-2"
              onSubmit={(e) => {
                e.preventDefault();
                saveProfileMutation.mutate();
              }}
            >
              <label className="block sm:col-span-1">
                <span className="mb-1.5 block text-sm font-medium text-[var(--text-muted)]">
                  First name
                </span>
                <input
                  className={inputCn()}
                  value={firstName}
                  onChange={(e) => setFirstNameLocal(e.target.value)}
                  autoComplete="given-name"
                />
              </label>
              <label className="block sm:col-span-1">
                <span className="mb-1.5 block text-sm font-medium text-[var(--text-muted)]">
                  Last name
                </span>
                <input
                  className={inputCn()}
                  value={lastName}
                  onChange={(e) => setLastNameLocal(e.target.value)}
                  autoComplete="family-name"
                />
              </label>
              <div className="sm:col-span-2">
                <button
                  type="submit"
                  disabled={!dirty || saveProfileMutation.isPending}
                  className={btnPrimaryCn("w-auto px-6")}
                >
                  {saveProfileMutation.isPending ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          </Card>

          <Card title="Account" subtitle="Read-only fields managed by your organization or sign-in provider">
            <dl className="divide-y divide-[var(--border-subtle)]">
              <div className="flex flex-wrap items-center justify-between gap-2 py-3">
                <dt className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                  <Mail className="h-4 w-4" />
                  Email
                </dt>
                <dd className="font-medium text-[var(--text-primary)]">{profile.email}</dd>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 py-3">
                <dt className="text-sm text-[var(--text-muted)]">Verification</dt>
                <dd className="flex items-center gap-2">
                  {profile.is_email_verified ? (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--success-soft)] px-2.5 py-1 text-xs font-medium text-[var(--success)]">
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Verified
                    </span>
                  ) : (
                    <>
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-[var(--warning-soft)] px-2.5 py-1 text-xs font-medium text-[var(--warning)]">
                        <XCircle className="h-3.5 w-3.5" />
                        Not verified
                      </span>
                      <button
                        type="button"
                        onClick={() => resendMutation.mutate()}
                        disabled={resendMutation.isPending}
                        className="text-xs font-semibold text-[var(--accent-bright)] hover:underline"
                      >
                        Resend email
                      </button>
                    </>
                  )}
                </dd>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 py-3">
                <dt className="flex items-center gap-2 text-sm text-[var(--text-muted)]">
                  <Shield className="h-4 w-4" />
                  Role
                </dt>
                <dd>
                  <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--surface-2)] px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-[var(--text-primary)]">
                    {ROLE_LABELS[profile.role] ?? profile.role}
                  </span>
                </dd>
              </div>
              <div className="flex flex-wrap items-center justify-between gap-2 py-3">
                <dt className="text-sm text-[var(--text-muted)]">Sign-in method</dt>
                <dd className="text-sm font-medium text-[var(--text-primary)]">
                  {AUTH_LABELS[profile.auth_method] ?? profile.auth_method}
                </dd>
              </div>
            </dl>
          </Card>

          <Card title="Security">
            <ul className="space-y-3 text-sm">
              {profile.auth_method === "password" && (
                <li>
                  <Link
                    to={`/reset-password?email=${encodeURIComponent(profile.email)}`}
                    className="inline-flex items-center gap-2 font-medium text-[var(--accent-bright)] hover:underline"
                  >
                    <KeyRound className="h-4 w-4" />
                    Change password (email code)
                  </Link>
                </li>
              )}
              <li>
                <Link
                  to="/dashboard/api-keys"
                  className="inline-flex items-center gap-2 font-medium text-[var(--accent-bright)] hover:underline"
                >
                  <KeyRound className="h-4 w-4" />
                  Manage API keys
                </Link>
              </li>
            </ul>
          </Card>

          <Card
            title="Danger zone"
            subtitle="Deactivating your account signs you out and disables login. Contact support to recover access."
            className="border-[var(--danger)]/30"
          >
            {!showDeleteConfirm ? (
              <button
                type="button"
                onClick={() => setShowDeleteConfirm(true)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-[var(--radius-md)] border border-[var(--danger)]/40 px-4 py-2.5 text-sm font-semibold text-[var(--danger)] transition-colors hover:bg-[var(--danger-soft)]"
                )}
              >
                <Trash2 className="h-4 w-4" />
                Deactivate account
              </button>
            ) : (
              <div className="space-y-4 rounded-[var(--radius-md)] border border-[var(--danger)]/25 bg-[var(--danger-soft)]/30 p-4">
                <p className="flex items-start gap-2 text-sm text-[var(--text-primary)]">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--danger)]" />
                  Type <strong>{profile.email}</strong> to confirm deactivation.
                </p>
                <input
                  className={inputCn()}
                  value={deleteEmail}
                  onChange={(e) => setDeleteEmail(e.target.value)}
                  placeholder="your@email.com"
                  autoComplete="off"
                />
                <div className="flex flex-wrap gap-3">
                  <button
                    type="button"
                    disabled={!canDelete || deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate()}
                    className="inline-flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--danger)] px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50"
                  >
                    {deleteMutation.isPending ? "Deactivating…" : "Confirm deactivation"}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowDeleteConfirm(false);
                      setDeleteEmail("");
                    }}
                    className={btnSecondaryCn("w-auto px-4 py-2.5 text-sm")}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}
