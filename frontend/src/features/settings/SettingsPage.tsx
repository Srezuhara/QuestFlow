import { useEffect, useState } from "react";
import { NeonButton, NeonPanel } from "@/components/ui";
import { PushAccessPanel } from "@/features/reminders/components/PushAccessPanel";
import { usePreferences, useUpdatePreferences } from "@/features/timer/hooks";
import { DeleteAccountDialog } from "./components/DeleteAccountDialog";
import { IdentityPanel } from "./components/IdentityPanel";

const FIELDS = [
  { key: "focus_minutes", label: "Focus Minutes", min: 1, max: 180 },
  { key: "short_break_minutes", label: "Short Break Minutes", min: 1, max: 60 },
  { key: "long_break_minutes", label: "Long Break Minutes", min: 1, max: 60 },
  { key: "sessions_before_long_break", label: "Sessions Before Long Break", min: 2, max: 12 },
] as const;

export function SettingsPage() {
  const { data: preferences, isLoading } = usePreferences();
  const updatePreferences = useUpdatePreferences();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const [form, setForm] = useState({
    focus_minutes: 25,
    short_break_minutes: 5,
    long_break_minutes: 15,
    sessions_before_long_break: 4,
    sound_enabled: true,
    leaderboard_opt_in: true,
  });

  useEffect(() => {
    if (preferences) setForm(preferences);
  }, [preferences]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    updatePreferences.mutate(form);
  }

  return (
    <div className="mx-auto flex max-w-[1440px] flex-col gap-8 p-4 md:p-8 lg:p-16">
      <header className="flex flex-col gap-2 border-b border-surface-container-highest pb-4">
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt; System Status: <span className="animate-pulse">Optimal</span>
        </p>
        <h1 className="font-display text-headline-lg text-on-surface uppercase tracking-tight">
          Settings
        </h1>
      </header>

      <IdentityPanel />

      {isLoading ? (
        <NeonPanel className="max-w-xl">
          <p className="font-mono text-label-mono text-on-surface-variant uppercase">
            &gt;&gt; loading preferences...
          </p>
        </NeonPanel>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-8">
          <NeonPanel className="max-w-xl">
            <h2 className="mb-6 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
              Pomodoro
            </h2>

            <div className="flex flex-col gap-5">
              <div className="grid grid-cols-2 gap-4">
                {FIELDS.map((field) => (
                  <div key={field.key} className="flex flex-col gap-2">
                    <label
                      htmlFor={field.key}
                      className="font-mono text-label-mono text-on-surface-variant uppercase"
                    >
                      {field.label}
                    </label>
                    <input
                      id={field.key}
                      type="number"
                      min={field.min}
                      max={field.max}
                      value={form[field.key]}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          [field.key]: Math.max(
                            field.min,
                            Math.min(field.max, Number(e.target.value)),
                          ),
                        }))
                      }
                      className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
                    />
                  </div>
                ))}
              </div>

              <label className="flex items-center gap-3 font-mono text-label-mono text-on-surface-variant uppercase">
                <input
                  type="checkbox"
                  checked={form.sound_enabled}
                  onChange={(e) => setForm((f) => ({ ...f, sound_enabled: e.target.checked }))}
                  className="size-4 accent-neon-lime"
                />
                Sound Enabled
              </label>
            </div>
          </NeonPanel>

          <NeonPanel className="max-w-xl">
            <h2 className="mb-6 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
              Public Profile
            </h2>

            <div className="flex flex-col gap-3">
              <label
                htmlFor="leaderboard_opt_in"
                className="flex items-center gap-3 font-mono text-label-mono text-on-surface-variant uppercase"
              >
                <input
                  id="leaderboard_opt_in"
                  type="checkbox"
                  checked={form.leaderboard_opt_in}
                  onChange={(e) => setForm((f) => ({ ...f, leaderboard_opt_in: e.target.checked }))}
                  className="size-4 accent-neon-lime"
                />
                Appear on the Leaderboard
              </label>
              <p className="font-body text-body-sm text-on-surface-variant">
                <strong className="text-on-surface">Published:</strong> handle, display name, title,
                avatar, level, total XP, current streak.
                <br />
                <strong className="text-on-surface">Never published:</strong> your email, and the
                titles or contents of your quests, habits and notes.
              </p>
            </div>
          </NeonPanel>

          {updatePreferences.isError && (
            <p className="max-w-xl font-mono text-label-mono text-neon-pink">
              Failed to save preferences. Please try again.
            </p>
          )}

          <div className="flex max-w-xl justify-end">
            <NeonButton type="submit" disabled={updatePreferences.isPending}>
              {updatePreferences.isPending ? "Saving..." : "Save Preferences"}
            </NeonButton>
          </div>
        </form>
      )}

      <div className="max-w-xl">
        <PushAccessPanel />
      </div>

      <NeonPanel className="max-w-xl border-neon-pink/40">
        <h2 className="mb-4 border-b border-surface-container-highest pb-4 font-display text-title-md text-neon-pink uppercase">
          Danger Zone
        </h2>
        <p className="mb-4 font-body text-body-sm text-on-surface-variant">
          Permanently delete your account and all associated data. This cannot be undone.
        </p>
        <NeonButton variant="secondary" onClick={() => setDeleteDialogOpen(true)}>
          Delete Account
        </NeonButton>
      </NeonPanel>

      <DeleteAccountDialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} />
    </div>
  );
}
