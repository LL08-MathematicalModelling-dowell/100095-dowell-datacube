// components/Header.tsx
import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import useAuthStore from "../store/authStore";
import useUser from "../store/useUser";
import { Menu, X, LogOut, Home, Key, CreditCard, FileText } from "lucide-react";

const Header = () => {
  const { isAuthenticated, logout } = useAuthStore();
  const { user, isLoading } = useUser();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isDashboardPath = location.pathname.startsWith("/dashboard");

  const navItems = [
    { to: "/dashboard/overview", label: "Databases", icon: Home },
    { to: "/dashboard/api-keys", label: "API Keys", icon: Key },
    { to: "/dashboard/billing", label: "Billing", icon: CreditCard },
    { to: "/api-docs", label: "API Reference", icon: FileText },
  ];

  const NavLink = ({ to, label, icon: Icon }: { to: string; label: string; icon: any }) => {
    const isActive = location.pathname === to;
    return (
      <Link
        to={to}
        onClick={() => setMobileMenuOpen(false)}
        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 font-medium ${isActive
          ? "bg-[var(--green-dark)]/20 text-[var(--green-dark)] border border-[var(--green-dark)]/30"
          : "text-[var(--text-muted)] hover:bg-[var(--bg-dark-3)] hover:text-[var(--text-light)]"
          }`}
      >
        <Icon className="w-5 h-5" />
        {label}
      </Link>
    );
  };

  return (
    <header className="bg-[var(--bg-dark-2)] border-b border-[var(--border-color)] px-6 py-4 flex items-center justify-between relative z-10 shadow-lg">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-3 group">
        <div className="p-2 bg-[var(--green-dark)]/20 rounded-lg group-hover:bg-[var(--green-dark)]/30 transition-all">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--green-dark)]">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
        <h1 className="text-2xl sm:text-md font-bold text-[var(--green-dark)] tracking-tight">DataCube</h1>
      </Link>

      <div className="flex items-center gap-6">
        {/* Auth Status (Right Side) */}
        <div className="flex items-center gap-4">
          {isAuthenticated && (
            <div className="hidden sm:flex items-center gap-3 text-sm">
              {isLoading ? (
                <span className="text-[var(--text-muted)]">Loading...</span>
              ) : (
                user?.firstName && (
                  <span className="text-[var(--text-light)]">
                    Hi, <span className="font-semibold text-[var(--green-dark)]">{user.firstName}</span>
                  </span>
                )
              )}
            </div>
          )}
        </div>
        <nav className="hidden sm:block">
          <ul className="flex items-center space-x-4">
            {/* button to /dashboard */}
            {!isDashboardPath && (
              <li>
                <Link to="/dashboard" className="text-slate-200 hover:text-cyan-400 transition-colors text-sm font-medium bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-md shadow-md">
                  Dashboard
                </Link>
              </li>
            )}
          </ul>
        </nav>


        {/* Desktop Navigation */}
        <nav className="hidden lg:flex items-center gap-2">
          {isAuthenticated && (
            <>
              {/* {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} label={item.label} icon={item.icon} />
            ))} */}
              <button
                onClick={logout}
                className="flex items-center gap-2 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all ml-4"
              >
                <LogOut className="w-5 h-5" />
                Logout
              </button>
            </>
          )}
        </nav>

        {/* Mobile Menu Button */}
        {isAuthenticated ? (
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-3 rounded-lg bg-[var(--bg-dark-3)] border border-[var(--border-color)] hover:border-[var(--green-dark)] transition-all"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        ) : (
          <Link
            to="/login"
            className="bg-[var(--green-dark)] hover:bg-[var(--green-dark)]/90 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-all shadow-md"
          >
            Log In
          </Link>
        )}

        {/* Mobile Dropdown Menu */}
        {mobileMenuOpen && isAuthenticated && (
          <>
            <div
              className="fixed inset-0 bg-black/70 z-40 lg:hidden"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="fixed top-16 left-4 right-4 bg-[var(--bg-dark-2)] border border-[var(--border-color)] rounded-xl shadow-2xl z-50 p-4">
              <div className="space-y-1">
                {navItems.map((item) => (
                  <NavLink key={item.to} to={item.to} label={item.label} icon={item.icon} />
                ))}
                <button
                  onClick={() => {
                    logout();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-4 py-3 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all text-left"
                >
                  <LogOut className="w-5 h-5" />
                  Logout
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </header>
  );
};

export default Header;




// import { Link } from 'react-router-dom';
// import useAuthStore from '../store/authStore';
// import useUser from '../store/useUser';

// const Header = () => {
//   const { isAuthenticated, logout } = useAuthStore();
//   const { user, isLoading } = useUser();

//   //  check the current url path
//   const currentPath = window.location.pathname;
//   // if dashboard in the path, do not show "dashboard" link
//   const isDashboardPath = currentPath.includes('/dashboard');

//   return (
//     <header className="bg-slate-900 border-b border-slate-800 text-slate-300 p-4 sm:px-6 flex items-center justify-between shadow-lg relative z-10">
//       {/* Logo/App Name - Clickable to Dashboard/Home */}
//       <Link to={"/"} className="flex items-center group">
//         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-cyan-400 group-hover:text-cyan-300 transition-colors mr-2">
//           <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
//         </svg>
//         <h1 className="text-2xl font-bold text-white tracking-tight group-hover:text-slate-100 transition-colors">
//           DataCube
//         </h1>
//       </Link>

//       {/* Conditional Rendering based on isAuthenticated */}
//       <div className="flex items-center gap-4">
//         {isAuthenticated ? (
//           <>{isLoading ? (
//             <span className="text-slate-400 text-sm hidden sm:block">Loading...</span>
//           ) : (
//             <>
//               {user?.firstName && (
//                 <span className="text-slate-400 text-sm hidden sm:block">
//                   Welcome, <span className="font-semibold text-slate-200">{user?.firstName}</span>
//                 </span>
//               )}
//               <span className="text-slate-400 text-sm hidden sm:block">|</span>
//             </>
//           )}

// <nav className="hidden sm:block">
//   <ul className="flex items-center space-x-4">
//     {/* button to /dashboard */}
//     {!isDashboardPath && (
//     <li>
//       <Link to="/dashboard" className="text-slate-200 hover:text-cyan-400 transition-colors text-sm font-medium bg-slate-700 hover:bg-slate-600 px-3 py-2 rounded-md shadow-md">
//         Dashboard
//       </Link>
//     </li>
//     )}
//   </ul>
// </nav>

//             <button
//               onClick={logout}
//               className="bg-slate-700 hover:bg-slate-600 text-slate-300 hover:text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-200 shadow-md"
//             >
//               Log Out
//             </button>
//           </>
//         ) : (
//           <Link
//             to="/login"
//             className="bg-cyan-600 hover:bg-cyan-700 text-white font-semibold py-2 px-4 rounded-md text-sm transition-colors duration-200 shadow-md"
//           >
//             Log In
//           </Link>
//         )}
//       </div>
//     </header>
//   );
// };

// export default Header;