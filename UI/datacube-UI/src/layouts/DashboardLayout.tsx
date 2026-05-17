import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
import Header from "../components/Header.tsx";
import Sidebar from "../components/Sidebar.tsx";
import api from "../services/api.ts";
import useAuthStore from "../store/authStore.ts";

const DashboardLayout = () => {
  const { accessToken, refreshToken, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (accessToken && !refreshToken) {
      logout();
      return;
    }

    if (accessToken && refreshToken) {
      api.get("/core/profile").catch(() => {
        /* refresh interceptor may redirect */
      });
    }
  }, [accessToken, refreshToken, logout]);

  return (
    <div className="flex h-screen bg-[var(--surface-0)] text-[var(--text-primary)] font-[var(--font-sans)]">
        <Sidebar
          mobileOpen={sidebarOpen}
          onMobileClose={() => setSidebarOpen(false)}
        />

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <Header onMenuClick={() => setSidebarOpen(true)} />

          <main className="flex-1 overflow-y-auto">
            <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
  );
};

export default DashboardLayout;
