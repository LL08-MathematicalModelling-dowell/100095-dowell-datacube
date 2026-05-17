import { lazy, Suspense } from "react";
import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import { PageFallback } from "./components/ui/PageFallback.tsx";
import DashboardLayout from "./layouts/DashboardLayout";
import Layout from "./layouts/Layout";
import useAuthStore from "./store/authStore";
import { ThemeSync } from "./components/theme/ThemeSync";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const ApiDocs = lazy(() => import("./pages/ApiDocs"));
const Login = lazy(() => import("./pages/Login"));
const Register = lazy(() => import("./pages/Register"));
const VerifyEmail = lazy(() => import("./pages/VerifyEmail"));
const OAuthCallback = lazy(() => import("./pages/OAuthCallback"));
const ForgotPassword = lazy(() => import("./pages/ForgotPassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const ApiKeys = lazy(() => import("./pages/ApiKeys"));
const Billing = lazy(() => import("./pages/Billing"));
const Overview = lazy(() => import("./pages/Overview"));
const FileDetail = lazy(() => import("./pages/FileDetail"));
const DatabaseDetail = lazy(() => import("./pages/DatabaseDetail"));
const CollectionDocuments = lazy(() => import("./pages/CollectionDocuments"));
const NotFound = lazy(() => import("./pages/NotFound"));

const ProtectedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return isAuthenticated ? <Outlet /> : <Navigate to="/" />;
};

const UnauthenticatedRoute = () => {
  const { isAuthenticated } = useAuthStore();
  return !isAuthenticated ? (
    <Outlet />
  ) : (
    <Navigate to="/dashboard/overview" />
  );
};

function App() {
  return (
    <>
      <ThemeSync />
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<LandingPage />} />
            <Route path="/api-docs" element={<ApiDocs />} />
          </Route>

          {/* OAuth return must run even if a stale session exists */}
          <Route path="/oauth/callback" element={<OAuthCallback />} />

          <Route element={<UnauthenticatedRoute />}>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard/api-keys" element={<ApiKeys />} />
              <Route path="/dashboard/billing" element={<Billing />} />
              <Route path="/dashboard/overview" element={<Overview />} />
              <Route path="/dashboard/files/:fileId" element={<FileDetail />} />
              <Route
                path="/dashboard/database/:dbId"
                element={<DatabaseDetail />}
              />
              <Route
                path="/dashboard/database/:dbId/collection/:collName"
                element={<CollectionDocuments />}
              />
              <Route
                path="/dashboard"
                element={<Navigate to="/dashboard/overview" />}
              />
            </Route>
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </>
  );
}

export default App;
