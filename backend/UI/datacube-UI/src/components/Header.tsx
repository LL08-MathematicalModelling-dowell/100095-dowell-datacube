import { Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import useUser from '../store/useUser';

const Header = () => {
  const { isAuthenticated, logout } = useAuthStore();
  const { user, isLoading } = useUser();

  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-300 p-4 sm:px-6 flex items-center justify-between shadow-lg relative z-10">
      {/* Logo/App Name - Clickable to Dashboard/Home */}
      <Link to={"/"} className="flex items-center group">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400 group-hover:text-cyan-300 transition-colors mr-2">
          <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
        </svg>
        <h1 className="text-2xl font-bold text-white tracking-tight group-hover:text-slate-100 transition-colors">
          DataCube
        </h1>
      </Link>

      {/* Conditional Rendering based on isAuthenticated */}
      <div className="flex items-center gap-4">
        {isAuthenticated ? (
          <>{isLoading ? (
            <span className="text-slate-400 text-sm hidden sm:block">Loading...</span>
          ) : (
            <>
              {user?.firstName && (
                <span className="text-slate-400 text-sm hidden sm:block">
                  Welcome, <span className="font-semibold text-slate-200">{user?.firstName}</span>
                </span>
              )}
              <span className="text-slate-400 text-sm hidden sm:block">|</span>
            </>
          )}

            <nav className="hidden sm:block">
              <ul className="flex items-center space-x-4">
                <li>
                  <Link to="/api-keys" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm font-medium">
                    API Keys
                  </Link>
                </li>
                <li>
                  <Link to="/billing" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm font-medium">
                    Billing
                  </Link>
                </li>
                <li>
                  <Link to="/overview" className="text-slate-400 hover:text-cyan-400 transition-colors text-sm font-medium">
                    Databases
                  </Link>
                </li>
              </ul>
            </nav>

            <button
              onClick={logout}
              className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 shadow-md"
            >
              Log Out
            </button>
          </>
        ) : (
          <Link
            to="/login"
            className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2 px-4 rounded-md text-sm transition-colors duration-200 shadow-md"
          >
            Log In
          </Link>
        )}
      </div>
    </header>
  );
};

export default Header;