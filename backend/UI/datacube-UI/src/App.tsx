import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import ApiDocs from './pages/ApiDocs';
import ApiKeys from './pages/ApiKeys';
import Billing from './pages/Billing';
import MainLayout from './layouts/MainLayout';
import useAuthStore from './store/authStore';
import NotFound from './pages/NotFound';
import DatabaseDetail from './pages/DatabaseDetail';
import Overview from './pages/Overview';
import Layout from './layouts/Layout';

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" />;
  return <Outlet />
};

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/api-docs" element={<ApiDocs />} />
        <Route path="/" element={<Navigate to="/api-docs" />} /> {/* Default redirect */}
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<MainLayout />}>
          <Route path="/api-keys" element={<ApiKeys />} />
          <Route path="/billing" element={<Billing />} />
          <Route path="/overview" element={<Overview />} />
          <Route path="/database/:id" element={<DatabaseDetail />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />

    </Routes>
  );
}

export default App;