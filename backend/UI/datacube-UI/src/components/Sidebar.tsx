import { Link, useLocation } from 'react-router-dom';
import useAuthStore from '../store/authStore'; // Assuming you have isAuthenticated in your auth store

const Sidebar = () => {
  const { isAuthenticated } = useAuthStore();
  const location = useLocation(); // To get the current path for active link styling

  return (
    <aside className="hidden lg:block w-64 flex-shrink-0 sticky top-0 h-screen overflow-y-auto py-10 pr-8 pl-4 border-r border-slate-800 bg-slate-900">
      <h2 className="text-white font-semibold mb-4 text-sm tracking-wide uppercase">DataCube</h2>

      <nav>
        <ul className="space-y-2">
          {/* Always visible: API Reference */}
          <li>
            <Link
              to="/api-docs"
              className={`block text-sm px-3 py-1.5 rounded-md transition-colors ${location.pathname === '/api-docs'
                ? 'bg-cyan-500/10 text-cyan-400 font-semibold'
                : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                }`}
            >
              API Reference
            </Link>
          </li>

          {/* Conditional links for authenticated users */}
          {isAuthenticated && (
            <>
              <li>
                <Link
                  to="/api-keys"
                  className={`block text-sm px-3 py-1.5 rounded-md transition-colors ${location.pathname === '/api-keys'
                    ? 'bg-cyan-500/10 text-cyan-400 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                    }`}
                >
                  API Keys
                </Link>
              </li>
              <li>
                <Link
                  to="/billing"
                  className={`block text-sm px-3 py-1.5 rounded-md transition-colors ${location.pathname === '/billing'
                    ? 'bg-cyan-500/10 text-cyan-400 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                    }`}
                >
                  Billing
                </Link>
              </li>
              <li>
                <Link
                  to="/overview"
                  className={`block text-sm px-3 py-1.5 rounded-md transition-colors ${location.pathname === '/overview'
                    ? 'bg-cyan-500/10 text-cyan-400 font-semibold'
                    : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
                    }`}
                >
                  Databases
                </Link>
              </li>
            </>
          )}
        </ul>
      </nav>

      <footer className="mt-auto pt-8 text-center text-slate-500 text-xs">
        &copy; {new Date().getFullYear()} DataCube
      </footer>
    </aside>
  );
};

export default Sidebar;