import { apiJson } from "@/lib/apiClient";
import type { components } from "@/types/api";

export type RegisterRequest = components["schemas"]["RegisterRequest"];
export type LoginRequest = components["schemas"]["LoginRequest"];
export type UserOut = components["schemas"]["UserOut"];
export type ProfileUpdate = components["schemas"]["ProfileUpdate"];

export function registerUser(data: RegisterRequest): Promise<UserOut> {
  return apiJson<UserOut>("/auth/register", { method: "POST", body: JSON.stringify(data) });
}

export function loginUser(data: LoginRequest): Promise<UserOut> {
  return apiJson<UserOut>("/auth/login", { method: "POST", body: JSON.stringify(data) });
}

export function logoutUser(): Promise<void> {
  return apiJson<void>("/auth/logout", { method: "POST" });
}

export function fetchCurrentUser(): Promise<UserOut> {
  return apiJson<UserOut>("/auth/me");
}

export function deleteAccount(): Promise<void> {
  return apiJson<void>("/auth/me", { method: "DELETE" });
}

export function updateProfile(data: ProfileUpdate): Promise<UserOut> {
  return apiJson<UserOut>("/auth/me", { method: "PATCH", body: JSON.stringify(data) });
}
