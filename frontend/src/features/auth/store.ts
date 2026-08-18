import { create } from "zustand";
import type { UserOut } from "./api";

interface AuthState {
  user: UserOut | null;
  /** `"pending"` until the initial `/auth/me` bootstrap check resolves — the
   * router guard must not redirect to /login while this is true, or a
   * refresh on an already-authenticated tab would bounce the user out. */
  status: "pending" | "authenticated" | "unauthenticated";
  setUser: (user: UserOut) => void;
  clear: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  status: "pending",
  setUser: (user) => set({ user, status: "authenticated" }),
  clear: () => set({ user: null, status: "unauthenticated" }),
}));
