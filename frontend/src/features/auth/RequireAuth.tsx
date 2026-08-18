import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { useAuthStore } from "./store";

/** Redirects to `/login` once the bootstrap `/auth/me` check resolves as
 * unauthenticated; renders nothing while it's still `"pending"` so an
 * authenticated user never flashes the login screen on refresh. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const status = useAuthStore((s) => s.status);
  const location = useLocation();

  if (status === "pending") {
    return null;
  }
  if (status === "unauthenticated") {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  return children;
}
