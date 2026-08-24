import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { DashboardPage } from "@/features/dashboard/DashboardPage";
import { HabitMasterPage } from "@/features/habits/HabitMasterPage";
import { LoginPage } from "@/features/auth/LoginPage";
import { KnowledgeVaultPage } from "@/features/notes/KnowledgeVaultPage";
import { ProgressPage } from "@/features/progress/ProgressPage";
import { RegisterPage } from "@/features/auth/RegisterPage";
import { RequireAuth } from "@/features/auth/RequireAuth";
import { SignalRelayPage } from "@/features/reminders/SignalRelayPage";
import { SettingsPage } from "@/features/settings/SettingsPage";
import { LeaderboardPage } from "@/features/social/LeaderboardPage";
import { TimeKeeperPage } from "@/features/timer/TimeKeeperPage";
import { AppShell } from "./AppShell";

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
          <Route path="habits" element={<HabitMasterPage />} />
          <Route path="timer" element={<TimeKeeperPage />} />
          <Route path="notes" element={<KnowledgeVaultPage />} />
          <Route path="notes/:noteId" element={<KnowledgeVaultPage />} />
          <Route path="progress" element={<ProgressPage />} />
          <Route path="progress/leaderboard" element={<LeaderboardPage />} />
          <Route path="reminders" element={<SignalRelayPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
