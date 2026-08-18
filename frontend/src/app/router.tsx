import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { AppShell } from "./AppShell";
import { ComingSoonScreen } from "./ComingSoonScreen";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<DashboardPage />} />
          <Route path="habits" element={<ComingSoonScreen title="Habit Master" />} />
          <Route path="timer" element={<ComingSoonScreen title="Time Keeper" />} />
          <Route path="notes" element={<ComingSoonScreen title="Knowledge Vault" />} />
          <Route path="reminders" element={<ComingSoonScreen title="Reminders" />} />
          <Route path="settings" element={<ComingSoonScreen title="Settings" />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
