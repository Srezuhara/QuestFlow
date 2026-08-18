import type { ReactNode } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useAuthBootstrap } from "@/features/auth/hooks";
import { queryClient } from "@/lib/queryClient";

function AuthBootstrap({ children }: { children: ReactNode }) {
  useAuthBootstrap();
  return children;
}

/**
 * App-wide context providers: TanStack Query, and the auth bootstrap check
 * (`GET /auth/me` on mount, populating the Zustand auth store the router
 * guard reads from).
 */
export function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthBootstrap>{children}</AuthBootstrap>
    </QueryClientProvider>
  );
}
