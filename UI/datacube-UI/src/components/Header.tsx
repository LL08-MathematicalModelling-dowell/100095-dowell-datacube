import { Link, useLocation } from "react-router-dom";
import { useThemeStore } from "../store/themeStore";
import useAuthStore from "../store/authStore";
import useUser from "../store/useUser";
import { useState } from "react";
import { cn } from "../lib/cn";
import { mobileNavItems } from "../lib/navConfig";
import { AnimatePresence, motion } from "framer-motion";
import {
  Database,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Sun,
  X,
} from "lucide-react";

type HeaderProps = {
  onMenuClick?: () => void;
};

const Header = ({ onMenuClick }: HeaderProps) => {
  const { isAuthenticated, logout } = useAuthStore();
  const { user, isLoading } = useUser();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { mode, toggle } = useThemeStore();

  const isDashboard = location.pathname.startsWith("/dashboard");

  const filteredMobile = mobileNavItems.filter(
    (i) => !i.requireAuth || isAuthenticated
  );

  const NavLinkRow = ({
    to,
    label,
    icon: Icon,
  }: {
    to: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
  }) => {
    const active = location.pathname === to;
    return (
      <Link
        to={to}
        onClick={() => setMobileOpen(false)}
        className={cn(
          "flex items-center gap-3 rounded-[var(--radius-md)] px-3 py-3 text-sm font-medium transition-colors",
          active
            ? "bg-[var(--accent-soft)] text-[var(--accent-bright)]"
            : "text-[var(--text-muted)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]"
        )}
      >
        <Icon className="h-5 w-5 shrink-0" />
        {label}
      </Link>
    );
  };

  return (
    <header className="relative z-30 flex items-center justify-between gap-4 border-b border-[var(--border-subtle)] bg-[var(--surface-1)]/95 px-4 py-3 backdrop-blur-md sm:px-6">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        {isAuthenticated && isDashboard && (
          <button
            type="button"
            className="inline-flex rounded-[var(--radius-md)] p-2 text-[var(--text-muted)] transition-colors hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] lg:hidden"
            aria-label="Open navigation"
            onClick={onMenuClick}
          >
            <Menu className="h-6 w-6" />
          </button>
        )}
        <Link to="/" className="flex min-w-0 items-center gap-2 sm:gap-3 group">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[var(--radius-md)] bg-[var(--accent-soft)] border border-[var(--accent)]/25 transition-transform duration-200 group-hover:scale-[1.02]">
            <Database className="h-5 w-5 text-[var(--accent-bright)]" />
          </div>
          <span className="truncate text-lg font-bold tracking-tight text-[var(--accent-bright)] sm:text-xl">
            DataCube
          </span>
        </Link>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        <button
          type="button"
          onClick={toggle}
          className="inline-flex rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] p-2.5 text-[var(--text-muted)] transition-all hover:border-[var(--accent)]/30 hover:text-[var(--text-primary)]"
          aria-label={mode === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {mode === "dark" ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>

        {isAuthenticated && (
          <div className="hidden items-center gap-2 sm:flex text-sm text-[var(--text-muted)]">
            {isLoading ? (
              <span>…</span>
            ) : user?.firstName ? (
              <span>
                Hi,{" "}
                <span className="font-semibold text-[var(--accent-bright)]">
                  {user.firstName}
                </span>
              </span>
            ) : null}
          </div>
        )}

        {!isAuthenticated ? (
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="rounded-[var(--radius-md)] border border-[var(--border-subtle)] bg-[var(--surface-0)] px-3 py-2 text-sm font-semibold text-[var(--text-primary)] transition-colors hover:border-[var(--accent)]/40 hover:bg-[var(--surface-2)] sm:px-4"
            >
              Sign in
            </Link>
            <Link
              to="/register"
              className="rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:brightness-110 active:scale-[0.98]"
            >
              Register
            </Link>
          </div>
        ) : (
          <>
            {!isDashboard && (
              <Link
                to="/dashboard/overview"
                className="hidden items-center gap-2 rounded-[var(--radius-md)] bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:brightness-110 active:scale-[0.98] sm:inline-flex"
              >
                <LayoutDashboard className="h-4 w-4" />
                Dashboard
              </Link>
            )}
            <button
              type="button"
              onClick={() => setMobileOpen((o) => !o)}
              className="inline-flex rounded-[var(--radius-md)] border border-[var(--border-subtle)] p-2.5 text-[var(--text-muted)] hover:bg-[var(--surface-2)] lg:hidden"
              aria-label="Account menu"
            >
              {mobileOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </button>
            <button
              type="button"
              onClick={logout}
              className="hidden items-center gap-2 rounded-[var(--radius-md)] border border-transparent px-3 py-2 text-sm font-medium text-[var(--danger)] transition-colors hover:bg-[var(--danger-soft)] lg:inline-flex"
            >
              <LogOut className="h-4 w-4" />
              <span className="hidden xl:inline">Logout</span>
            </button>
          </>
        )}
      </div>

      <AnimatePresence>
        {mobileOpen && isAuthenticated && (
          <>
            <motion.div
              className="fixed inset-0 z-40 bg-[var(--overlay)] lg:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
            />
            <motion.div
              className="fixed right-3 top-14 z-50 w-[min(92vw,280px)] overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-subtle)] bg-[var(--surface-1)] shadow-[var(--shadow-md)] lg:hidden"
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.18 }}
            >
              <div className="max-h-[70vh] space-y-1 overflow-y-auto p-2">
                {!isDashboard && (
                  <NavLinkRow
                    to="/dashboard/overview"
                    label="Dashboard"
                    icon={LayoutDashboard}
                  />
                )}
                {filteredMobile.map((item) => (
                  <NavLinkRow
                    key={item.to}
                    to={item.to}
                    label={item.label}
                    icon={item.icon}
                  />
                ))}
                <button
                  type="button"
                  onClick={() => {
                    logout();
                    setMobileOpen(false);
                  }}
                  className="flex w-full items-center gap-3 rounded-[var(--radius-md)] px-3 py-3 text-left text-sm font-medium text-[var(--danger)] hover:bg-[var(--danger-soft)]"
                >
                  <LogOut className="h-5 w-5" />
                  Logout
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </header>
  );
};

export default Header;
