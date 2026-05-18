import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { cn } from "../../lib/cn";
import { userInitials } from "../../lib/initials";
import {
  AVATAR_QUERY_KEY,
  fetchAvatarBlobUrl,
  type UserProfile,
} from "../../services/profile";

const sizeMap = {
  sm: "h-9 w-9 text-xs",
  md: "h-14 w-14 text-base",
  lg: "h-24 w-24 text-2xl",
  xl: "h-32 w-32 text-3xl",
} as const;

type UserAvatarProps = {
  profile?: Pick<UserProfile, "firstName" | "lastName" | "email" | "has_avatar"> | null;
  size?: keyof typeof sizeMap;
  className?: string;
  /** When false, skip avatar fetch even if has_avatar (e.g. after remove). */
  showImage?: boolean;
};

export function UserAvatar({
  profile,
  size = "md",
  className,
  showImage = true,
}: UserAvatarProps) {
  const hasAvatar = showImage && Boolean(profile?.has_avatar);
  const initials = userInitials(
    profile?.firstName,
    profile?.lastName,
    profile?.email
  );

  const { data: src } = useQuery({
    queryKey: AVATAR_QUERY_KEY,
    queryFn: fetchAvatarBlobUrl,
    enabled: hasAvatar,
    staleTime: 1000 * 60 * 5,
    gcTime: 1000 * 60 * 10,
  });

  useEffect(() => {
    return () => {
      if (src) URL.revokeObjectURL(src);
    };
  }, [src]);

  return (
    <div
      className={cn(
        "relative shrink-0 overflow-hidden rounded-full border-2 border-[var(--border-subtle)] bg-[var(--accent-soft)] font-semibold text-[var(--accent-bright)] shadow-[var(--shadow-sm)]",
        sizeMap[size],
        className
      )}
      aria-hidden={!initials}
    >
      {src ? (
        <img
          src={src}
          alt=""
          className="h-full w-full object-cover"
        />
      ) : (
        <span className="flex h-full w-full items-center justify-center">
          {initials}
        </span>
      )}
    </div>
  );
}
