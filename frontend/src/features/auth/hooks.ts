import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError } from "@/lib/apiClient";
import {
  deleteAccount,
  fetchCurrentUser,
  loginUser,
  logoutUser,
  registerUser,
  updateProfile,
} from "./api";
import type { LoginRequest, ProfileUpdate, RegisterRequest } from "./api";
import { useAuthStore } from "./store";

const ME_QUERY_KEY = ["auth", "me"] as const;

/** Runs once on app mount: checks for an existing session via `/auth/me` and
 * populates the auth store. The router guard waits on `status === "pending"`
 * before making any redirect decision. */
export function useAuthBootstrap(): void {
  const setUser = useAuthStore((s) => s.setUser);
  const clear = useAuthStore((s) => s.clear);

  const query = useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: fetchCurrentUser,
    retry: false,
    staleTime: Infinity,
  });

  useEffect(() => {
    if (query.data) {
      setUser(query.data);
    } else if (query.isError) {
      clear();
    }
  }, [query.data, query.isError, setUser, clear]);
}

export function useRegister() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: (data: RegisterRequest) => registerUser(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.setQueryData(ME_QUERY_KEY, user);
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: (data: LoginRequest) => loginUser(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.setQueryData(ME_QUERY_KEY, user);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const clear = useAuthStore((s) => s.clear);

  return useMutation({
    mutationFn: () => logoutUser(),
    onSettled: () => {
      clear();
      queryClient.setQueryData(ME_QUERY_KEY, null);
    },
  });
}

/** Same cache-clearing shape as `useLogout` — the account is gone server-side
 * either way, so `onSettled` (not `onSuccess`) clears local state even if the
 * response somehow fails after the delete already committed. */
export function useDeleteAccount() {
  const queryClient = useQueryClient();
  const clear = useAuthStore((s) => s.clear);

  return useMutation({
    mutationFn: () => deleteAccount(),
    onSettled: () => {
      clear();
      queryClient.setQueryData(ME_QUERY_KEY, null);
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  return useMutation({
    mutationFn: (data: ProfileUpdate) => updateProfile(data),
    onSuccess: (user) => {
      setUser(user);
      queryClient.setQueryData(ME_QUERY_KEY, user);
    },
  });
}

/** Human-readable message for the common auth error shapes (409 conflicts,
 * 401 invalid credentials, FastAPI 422 validation errors). */
export function authErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) {
      const detail = (error.body as { detail?: string })?.detail;
      return detail ?? "That email or handle is already taken.";
    }
    if (error.status === 401) {
      return "Invalid email or password.";
    }
    if (error.status === 422) {
      return "Please check the form for errors.";
    }
  }
  return "Something went wrong. Please try again.";
}
