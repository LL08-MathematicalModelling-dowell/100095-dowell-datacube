// layouts/MainLayout.tsx
import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import Header from '../components/Header.tsx';
import Sidebar from '../components/Sidebar.tsx';
import api from '../services/api.ts';
import useAuthStore from '../store/authStore.ts';

const MainLayout = () => {
  const navigate = useNavigate();
  const { accessToken, refreshToken, logout } = useAuthStore();

  useEffect(() => {
    // If we have tokens, validate them silently on app start
    if (accessToken && refreshToken) {
      api
        .get('/core/profile')
        .catch((err) => {
          console.warn('Token validation failed:', err.message);
          logout();
          navigate('/login', { replace: true });
        });
    } else if (accessToken && !refreshToken) {
      // Edge case: only access token exists → probably corrupted state
      logout();
      navigate('/login', { replace: true });
    }
  }, [accessToken, refreshToken, logout, navigate]);

  return (
    <div className="flex h-screen bg-[var(--bg-dark-1)] text-[var(--text-light)] font-[var(--font-sans)]">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-[var(--bg-dark-1)] p-6 sm:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default MainLayout;