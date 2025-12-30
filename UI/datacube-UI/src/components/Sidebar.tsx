import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import useAuthStore from "../store/authStore";
import {
  Home,
  Key,
  CreditCard,
  FileText,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "../components/ui/tooltip";

const Sidebar = () => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  const navItems = [
    ...(isAuthenticated
      ? [
          { to: "/dashboard/overview", label: "Databases", icon: Home },
          { to: "/dashboard/api-keys", label: "API Keys", icon: Key },
          { to: "/dashboard/billing", label: "Billing", icon: CreditCard },
        ]
      : []),
    { to: "/api-docs", label: "API Reference", icon: FileText },
  ];

  const NavLink = ({ to, label, icon: Icon }: { to: string; label: string; icon: any }) => {
    const isActive = location.pathname === to;

    const linkContent = (
      <div
        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium group ${
          isActive
            ? "bg-[var(--green-dark)]/20 text-[var(--green-dark)] border border-[var(--green-dark)]/30"
            : "text-[var(--text-muted)] hover:bg-[var(--bg-dark-3)] hover:text-[var(--text-light)]"
        }`}
      >
        <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? "text-[var(--green-dark)]" : ""}`} />
        {!collapsed && <span>{label}</span>}
      </div>
    );

    return collapsed ? (
      <TooltipProvider>
        <Tooltip >
          <TooltipTrigger>
            <Link to={to}>{linkContent}</Link>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-[var(--bg-dark-3)] border-[var(--border-color)] text-[var(--text-light)]">
            {label}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    ) : (
      <Link to={to}>{linkContent}</Link>
    );
  };

  return (
    <TooltipProvider>
      {/* Desktop Only Sidebar */}
      <aside
        className={`hidden lg:flex flex-col bg-[var(--bg-dark-2)] border-r border-[var(--border-color)] h-screen transition-all duration-300 ${
          collapsed ? "w-20" : "w-72"
        }`}
      >
        {/* Header */}
        <div className="p-6 border-b border-[var(--border-color)] flex items-center justify-between">
          <h2
            className={`font-bold text-[var(--green-dark)] transition-all duration-300 ${
              collapsed ? "text-xl opacity-0 w-0" : "text-2xl"
            }`}
          >
            DataCube
          </h2>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="p-2 rounded-lg hover:bg-[var(--bg-dark-3)] transition-all text-[var(--text-muted)] hover:text-[var(--green-dark)]"
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navItems.map((item) => (
              <li key={item.to}>
                <NavLink to={item.to} label={item.label} icon={item.icon} />
              </li>
            ))}
          </ul>
        </nav>

        {/* Footer */}
        <footer
          className={`p-6 border-t border-[var(--border-color)] text-center text-xs text-[var(--text-muted)] transition-opacity duration-300 ${
            collapsed ? "opacity-0" : "opacity-100"
          }`}
        >
          © {new Date().getFullYear()} DataCube
        </footer>
      </aside>
    </TooltipProvider>
  );
};

export default Sidebar;