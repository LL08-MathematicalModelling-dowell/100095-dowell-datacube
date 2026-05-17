import {
  CreditCard,
  Database,
  FileText,
  Home,
  KeyRound,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type NavItem = {
  to: string;
  label: string;
  icon: LucideIcon;
  requireAuth?: boolean;
};

export const dashboardNavGroups: { label: string; items: NavItem[] }[] = [
  {
    label: "Workspace",
    items: [
      { to: "/dashboard/overview", label: "Databases", icon: Home, requireAuth: true },
      { to: "/dashboard/api-keys", label: "API Keys", icon: KeyRound, requireAuth: true },
      { to: "/dashboard/billing", label: "Billing", icon: CreditCard, requireAuth: true },
    ],
  },
  {
    label: "Resources",
    items: [{ to: "/api-docs", label: "API reference", icon: FileText }],
  },
];

export const mobileNavItems: NavItem[] = [
  { to: "/dashboard/overview", label: "Home", icon: Database, requireAuth: true },
  { to: "/dashboard/api-keys", label: "Keys", icon: KeyRound, requireAuth: true },
  { to: "/dashboard/billing", label: "Billing", icon: CreditCard, requireAuth: true },
  { to: "/api-docs", label: "Docs", icon: FileText },
];
