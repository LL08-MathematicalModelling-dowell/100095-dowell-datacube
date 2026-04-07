'use client';

import { Toaster } from "@/components/ui/toaster";
import { signOut, useSession } from "next-auth/react";
import Link from "next/link";
import { redirect, usePathname } from "next/navigation";
import { ReactNode, useState } from "react";
import { FaBars, FaCog, FaDatabase, FaHome, FaKey, FaSignOutAlt } from "react-icons/fa";

interface HeaderProps {
  user: {
    name: string;
    email: string;
    image: string;
  };
  onMenuClick: () => void;
}

const Header = ({ user, onMenuClick }: HeaderProps) => {
  const splitName = user?.name.split(" ");
  const initials =
    splitName && splitName.length > 1
      ? splitName[0].charAt(0) + splitName[1].charAt(0)
      : "U";

  return (
    <header className="flex justify-between items-center px-4 py-3 bg-gray-800 text-white shadow-md">
      <div className="flex items-center">
        {/* Hamburger menu visible only on mobile */}
        <button
          onClick={onMenuClick}
          className="sm:hidden mr-3 focus:outline-none focus:ring-2 focus:ring-orange-500"
        >
          <FaBars className="w-6 h-6" />
        </button>
        <Link href="/" className="text-2xl font-bold text-orange-500">
          <h1 className="text-xl font-bold text-orange-500">Datacube Dashboard</h1>
        </Link>
      </div>
      <div className="flex items-center">
        {user && (
          <>
            <span className="bg-gray-700 w-8 h-8 flex items-center justify-center rounded-full text-base font-bold uppercase shadow-md mr-2">
              {initials}
            </span>
            <span className="text-sm">{user.name}</span>
          </>
        )}
      </div>
    </header>
  );
};

const DashboardLayout = ({ children }: { children: ReactNode }) => {
  const { data: session, status } = useSession();
  const path = usePathname();
  const currentPath = path.split("?")[0];

  // Manage sidebar visibility on mobile
  const [sidebarOpen, setSidebarOpen] = useState(false);

  if (status === "loading") return null;

  if (status === "unauthenticated") {
    // Redirect to login page if user is not authenticated
    redirect("/auth/login")
    return null; // Prevent rendering the layout while redirecting
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header
        user={session?.user as { name: string; email: string; image: string }}
        onMenuClick={() => setSidebarOpen((prev) => !prev)}
      />
      <div className="flex flex-1 relative">
        {/* Desktop Sidebar */}
        <nav className="hidden sm:block sm:w-56 md:w-64 bg-gray-800 p-4">
          <ul className="space-y-3">
            <li
              className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath === "/dashboard" ? "bg-gray-700" : "hover:bg-gray-700"
                }`}
            >
              <Link href="/dashboard" className="flex items-center text-sm text-white hover:text-orange-500">
                <FaHome className="mr-2 w-4 h-4" /> Home
              </Link>
            </li>
            <li
              className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/databases") ? "bg-gray-700" : "hover:bg-gray-700"
                }`}
            >
              <Link href="/dashboard/databases" className="flex items-center text-sm text-white hover:text-orange-500">
                <FaDatabase className="mr-2 w-4 h-4" /> Databases
              </Link>
            </li>
            <li
              className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/apikeys") ? "bg-gray-700" : "hover:bg-gray-700"
                }`}
            >
              <Link href="/dashboard/apikeys" className="flex items-center text-sm text-white hover:text-orange-500">
                <FaKey className="mr-2 w-4 h-4" /> API Keys Management
              </Link>
            </li>
            <li
              className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/settings") ? "bg-gray-700" : "hover:bg-gray-700"
                }`}
            >
              <Link href="/dashboard/settings" className="flex items-center text-sm text-white hover:text-orange-500">
                <FaCog className="mr-2 w-4 h-4" /> Settings
              </Link>
            </li>
            <li
              className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/reports") ? "bg-gray-700" : "hover:bg-gray-700"
                }`}
            >
              <Link href="/dashboard/reports" className="flex items-center text-sm text-white hover:text-orange-500">
                <FaCog className="mr-2 w-4 h-4" /> Reports
              </Link>
            </li>
          </ul>
          <button
            onClick={() => signOut()}
            className="flex items-center justify-center bg-red-600 text-white p-2 mt-6 rounded transition-colors hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-600 w-full"
          >
            <FaSignOutAlt className="mr-2 w-4 h-4" />
            <span className="text-sm font-medium">Sign Out</span>
          </button>
        </nav>

        {/* Mobile Sidebar (Drawer) */}
        {sidebarOpen && (
          <nav className="absolute top-0 left-0 z-50 w-56 md:w-64 bg-gray-800 p-4 sm:hidden">
            <ul className="space-y-3">
              <li
                className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath === "/dashboard" ? "bg-gray-700" : "hover:bg-gray-700"
                  }`}
              >
                <Link href="/dashboard"
                  className="flex items-center text-sm text-white hover:text-orange-500"
                  onClick={() => setSidebarOpen(false)}
                >
                  <FaHome className="mr-2 w-4 h-4" /> Home
                </Link>
              </li>
              <li
                className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/databases") ? "bg-gray-700" : "hover:bg-gray-700"
                  }`}
              >
                <Link href="/dashboard/databases"
                  className="flex items-center text-sm text-white hover:text-orange-500"
                  onClick={() => setSidebarOpen(false)}
                >
                  <FaDatabase className="mr-2 w-4 h-4" /> Databases
                </Link>
              </li>
              <li
                className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/apikeys") ? "bg-gray-700" : "hover:bg-gray-700"
                  }`}
              >
                <Link href="/dashboard/apikeys"
                  className="flex items-center text-sm text-white hover:text-orange-500"
                  onClick={() => setSidebarOpen(false)}
                >
                  <FaKey className="mr-2 w-4 h-4" /> API Keys Management
                </Link>
              </li>
              <li
                className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/settings") ? "bg-gray-700" : "hover:bg-gray-700"
                  }`}
              >
                <Link href="/dashboard/settings"
                  className="flex items-center text-sm text-white hover:text-orange-500"
                  onClick={() => setSidebarOpen(false)}
                >
                  <FaCog className="mr-2 w-4 h-4" /> Settings
                </Link>
              </li>
              <li
                className={`flex items-center px-2 py-1 rounded transition-colors ${currentPath.includes("/dashboard/reports") ? "bg-gray-700" : "hover:bg-gray-700"
                  }`}
              >
                <Link href="/dashboard/reports"
                  className="flex items-center text-sm text-white hover:text-orange-500"
                  onClick={() => setSidebarOpen(false)}
                >
                  <FaCog className="mr-2 w-4 h-4" /> Reports
                </Link>
              </li>
            </ul>
            <button
              onClick={() => {
                setSidebarOpen(false);
                signOut();
              }}
              className="flex items-center justify-center bg-red-600 text-white p-2 mt-6 rounded transition-colors hover:bg-red-500 focus:outline-none focus:ring-2 focus:ring-red-600 w-full"
            >
              <FaSignOutAlt className="mr-2 w-4 h-4" />
              <span className="text-sm font-medium">Sign Out</span>
            </button>
          </nav>
        )}

        <main className="flex-1 p-4 bg-gray-900 text-white">
          <div className="mb-4 text-xs text-gray-400">
            {currentPath.split("/").map((segment, index, array) => {
              if (!segment) return null;
              const href = `/${array.slice(1, index + 1).join("/")}`;
              return (
                <span key={index}>
                  <Link
                    href={href}
                    className={`text-orange-500 hover:underline ${index === array.length - 2 ? "font-bold" : ""
                      }`}
                  >
                    {" "}
                    / {segment.toUpperCase()}
                  </Link>
                  {index < array.length - 2 && <span className="text-gray-500"> </span>}
                </span>
              );
            })}
          </div>
          {children}
        </main>
      </div>
      <Toaster />
    </div>
  );
};

export default DashboardLayout;
