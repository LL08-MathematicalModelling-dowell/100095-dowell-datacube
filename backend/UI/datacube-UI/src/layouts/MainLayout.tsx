import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import Header from '../components/Header.tsx';
import Sidebar from '../components/Sidebar.tsx';
import api from '../services/api.ts';
import useAuthStore from '../store/authStore.ts';

const MainLayout = () => {
  const { accessToken, refreshToken, logout } = useAuthStore();

  useEffect(() => {
    if (accessToken && !refreshToken) {
      console.warn(
        'Authentication token mismatch: Access token present without Refresh token. Clearing session.'
      );
      logout();
      return;
    }

    // If both tokens exist, silently validate the session
    if (accessToken && refreshToken) {
      api.get('/core/profile')
        .then(() => {
          console.log('Session validated successfully.');
        })
        .catch((error) => {
          console.error('Initial profile validation failed. Session is expired.', error);

          // The interceptor *should* handle logout/redirect, but this ensures a clean slate
          // in case of other unhandled network errors or non-401 failures.
          // logout();
        });
    }
  }, [accessToken, refreshToken]);
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