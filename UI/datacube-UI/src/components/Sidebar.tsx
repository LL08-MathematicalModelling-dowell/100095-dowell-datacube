import { AnimatePresence, motion } from "framer-motion";
import { Link, useLocation } from "react-router-dom";
import {
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import useAuthStore from "../store/authStore";
import { cn } from "../lib/cn";
import { dashboardNavGroups } from "../lib/navConfig";
import { useState } from "react";

type SidebarProps = {
  mobileOpen: boolean;
  onMobileClose: () => void;
};

const Sidebar = ({ mobileOpen, onMobileClose }: SidebarProps) => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const filteredGroups = dashboardNavGroups
    .map((g) => ({
      ...g,
      items: g.items.filter((i) => !i.requireAuth || isAuthenticated),
    }))
    .filter((g) => g.items.length > 0);

  const NavLink = ({
    to,
    label,
    icon: Icon,
  }: {
    to: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }) => {
    const active =
      location.pathname === to ||
      (to !== "/dashboard/overview" && location.pathname.startsWith(to) && to !== "/api-docs");

    const inner = (
      <div
        className={cn(
          "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-all duration-200",
          active
            ? "bg-[var(--accent-soft)] text-[var(--accent-bright)] shadow-sm border border-[var(--accent)]/25"
            : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]/80 hover:text-[var(--text-primary)] border border-transparent"
        )}
      >
        <Icon
          className={cn(
            "h-5 w-5 shrink-0 transition-transform duration-200",
            active && "scale-[1.03]"
          )}
        />
        {!collapsed && <span className="truncate">{label}</span>}
      </div>
    );

    return collapsed ? (
      <Link to={to} onClick={onMobileClose} title={label}>
        {inner}
      </Link>
    ) : (
      <Link to={to} onClick={onMobileClose}>
        {inner}
      </Link>
    );
  };

  const asideInner = (
    <>
      <div className="flex items-center justify-between gap-2 border-b border-[var(--border-subtle)] px-4 py-4">
        <Link
          to="/dashboard/overview"
          onClick={onMobileClose}
          className={cn(
            "flex min-w-0 items-center gap-2 font-bold text-[var(--accent-bright)] tracking-tight transition-opacity",
            collapsed ? "opacity-0 w-0 overflow-hidden" : "text-xl"
          )}
        >
          <span className="flex h-9 w-9 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)] border border-[var(--accent)]/20">
            <PanelLeft className="h-5 w-5" />
          </span>
          {!collapsed && <span>DataCube</span>}
        </Link>
        <button
          type="button"
          onClick={() => setCollapsed((c) => !c)}
          className="hidden lg:inline-flex rounded-[var(--radius-md)] p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--accent-bright)]"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-5 w-5" />
          ) : (
            <ChevronLeft className="h-5 w-5" />
          )}
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto p-3">
        {filteredGroups.map((group) => (
          <div key={group.label} className="mb-6">
            {!collapsed && (
              <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-subtle)]">
                {group.label}
              </p>
            )}
            <ul className="space-y-1">
              {group.items.map((item) => (
                <li key={item.to}>
                  <NavLink to={item.to} label={item.label} icon={item.icon} />
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <footer
        className={cn(
          "border-t border-[var(--border-subtle)] p-4 text-center text-[11px] text-[var(--text-subtle)] transition-opacity duration-300",
          collapsed && "opacity-0 pointer-events-none h-0 p-0 overflow-hidden border-0"
        )}
      >
        © {new Date().getFullYear()} DataCube
      </footer>
    </>
  );

  return (
    <>
      {/* Desktop */}
      <aside
        className={cn(
          "relative z-20 hidden h-screen shrink-0 flex-col border-r border-[var(--border-subtle)] bg-[var(--surface-1)] transition-[width] duration-300 ease-out lg:flex",
          collapsed ? "w-[72px]" : "w-[var(--sidebar-width)]"
        )}
      >
        {asideInner}
      </aside>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.button
              type="button"
              aria-label="Close menu"
              className="fixed inset-0 z-40 bg-[var(--overlay)] lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={onMobileClose}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 z-50 flex w-[min(88vw,300px)] flex-col border-r border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-md)] lg:hidden"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
            >
              <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-3 py-3">
                <span className="font-semibold text-[var(--text-primary)]">Menu</span>
                <button
                  type="button"
                  onClick={onMobileClose}
                  className="rounded-[var(--radius-md)] p-2 text-[var(--text-muted)] hover:bg-[var(--surface-2)]"
                  aria-label="Close"
                >
                  <PanelLeftClose className="h-5 w-5" />
                </button>
              </div>
              <div className="flex flex-1 flex-col overflow-hidden">
                {/* re-use nav without collapsed for mobile */}
                <nav className="flex-1 overflow-y-auto p-3">
                  {filteredGroups.map((group) => (
                    <div key={group.label} className="mb-6">
                      <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-[var(--text-subtle)]">
                        {group.label}
                      </p>
                      <ul className="space-y-1">
                        {group.items.map((item) => {
                          const Icon = item.icon;
                          const active =
                            location.pathname === item.to ||
                            (item.to !== "/dashboard/overview" &&
                              location.pathname.startsWith(item.to) &&
                              item.to !== "/api-docs");
                          return (
                            <li key={item.to}>
                              <Link
                                to={item.to}
                                onClick={onMobileClose}
                                className={cn(
                                  "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-2.5 text-sm font-medium transition-all",
                                  active
                                    ? "bg-[var(--accent-soft)] text-[var(--accent-bright)] border border-[var(--accent)]/25"
                                    : "text-[var(--text-muted)] hover:bg-[var(--surface-2)]/80 hover:text-[var(--text-primary)] border border-transparent"
                                )}
                              >
                                <Icon className="h-5 w-5 shrink-0" />
                                {item.label}
                              </Link>
                            </li>
                          );
                        })}
                      </ul>
                    </div>
                  ))}
                </nav>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
};

export default Sidebar;
