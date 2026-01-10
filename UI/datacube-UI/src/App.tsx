import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import ApiDocs from './pages/ApiDocs';
import ApiKeys from './pages/ApiKeys';
import Billing from './pages/Billing';
import DashboardLayout from './layouts/DashboardLayout';
import useAuthStore from './store/authStore';
import NotFound from './pages/NotFound';
import DatabaseDetail from './pages/DatabaseDetail';
import Overview from './pages/Overview';
import Layout from './layouts/Layout';
import LandingPage from './pages/LandingPage';
import CollectionDocuments from './pages/CollectionDocuments';

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <Outlet /> : <Navigate to="/" />;
};

const UnauthenticatedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? <Outlet /> : <Navigate to="/dashboard/overview" />;
}

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/api-docs" element={<ApiDocs />} />
      </Route>
      
      <Route element={<UnauthenticatedRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard/api-keys" element={<ApiKeys />} />
          <Route path="/dashboard/billing" element={<Billing />} />
          <Route path="/dashboard/overview" element={<Overview />} />
          <Route path="/dashboard/database/:dbId" element={<DatabaseDetail />} />
          <Route path="/dashboard/database/:dbId/collection/:collName" element={<CollectionDocuments />} />
          <Route path="/dashboard" element={<Navigate to="/dashboard/overview" />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFound />} />

    </Routes>
  );
}

export default App;