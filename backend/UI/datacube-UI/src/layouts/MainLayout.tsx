import Header from '../components/Header.tsx';
import Sidebar from '../components/Sidebar.tsx';
import { Outlet } from 'react-router-dom';

const MainLayout = () => (
  <div className="flex-1">
    <Header />

    <div className="flex">
      <Sidebar />
      <main className="p-4 bg-[var(--white)] text-black">
        <Outlet />
      </main>
    </div>
  </div>
);

export default MainLayout;