import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute() {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <p className="p-6 text-slate-500 dark:text-slate-400">Loading…</p>;
  }
  if (!user) {
    // remember where the person was going, so login can send them back
    return <Navigate to="/login" replace state={{ from: location }} />;
  }
  return <Outlet />;
}
