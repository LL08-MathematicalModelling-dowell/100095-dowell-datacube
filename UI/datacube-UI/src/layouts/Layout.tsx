import Header from "../components/Header.tsx";
import { Outlet } from "react-router-dom";

/** Public shell: full-width pages (home, API docs) control their own max-width. */
const Layout = () => (
  <div className="min-h-screen bg-[var(--surface-0)] text-[var(--text-primary)] font-[var(--font-sans)]">
    <Header />
    <main className="w-full">
      <Outlet />
    </main>
  </div>
);

export default Layout;
