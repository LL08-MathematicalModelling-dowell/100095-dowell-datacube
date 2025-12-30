import Header from '../components/Header.tsx';
import { Outlet } from 'react-router-dom';

const Layout = () => (
  <div className="flex-1">
    <Header />
    <main className="p-4 bg-[var(--white)] text-black">
      <Outlet />
    </main>
  </div>
);

export default Layout;