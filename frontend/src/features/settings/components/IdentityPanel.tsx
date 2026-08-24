import { useEffect, useState } from "react";
import { NeonButton, NeonPanel } from "@/components/ui";
import { useAuthStore } from "@/features/auth/store";
import { useUpdateProfile } from "@/features/auth/hooks";
import { cn } from "@/lib/cn";

const AVATAR_URLS = Array.from(
  { length: 12 },
  (_, i) => `/avatars/avatar-${String(i + 1).padStart(2, "0")}.svg`,
);

export function IdentityPanel() {
  const user = useAuthStore((s) => s.user);
  const updateProfile = useUpdateProfile();

  const [displayName, setDisplayName] = useState("");
  const [title, setTitle] = useState("");
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name);
      setTitle(user.title);
      setAvatarUrl(user.avatar_url);
    }
  }, [user]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    updateProfile.mutate({ display_name: displayName, title, avatar_url: avatarUrl });
  }

  return (
    <NeonPanel className="max-w-xl">
      <h2 className="mb-6 border-b border-surface-container-highest pb-4 font-display text-title-md text-on-surface uppercase">
        Identity
      </h2>

      <form onSubmit={handleSubmit} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <label
            htmlFor="identity-display-name"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Display Name
          </label>
          <input
            id="identity-display-name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            maxLength={80}
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label
            htmlFor="identity-title"
            className="font-mono text-label-mono text-on-surface-variant uppercase"
          >
            Title
          </label>
          <input
            id="identity-title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            maxLength={40}
            required
            className="clip-chamfer border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-lime"
          />
        </div>

        <div className="flex flex-col gap-2">
          <span className="font-mono text-label-mono text-on-surface-variant uppercase">
            Avatar
          </span>
          <div role="radiogroup" aria-label="Avatar" className="grid grid-cols-6 gap-2">
            {AVATAR_URLS.map((url) => {
              const selected = avatarUrl === url;
              return (
                <button
                  key={url}
                  type="button"
                  role="radio"
                  aria-checked={selected}
                  aria-label={url.split("/").pop()}
                  onClick={() => setAvatarUrl(url)}
                  className={cn(
                    "clip-chamfer border-2 p-1 transition-colors",
                    selected
                      ? "border-neon-lime"
                      : "border-outline-variant hover:border-on-surface-variant",
                  )}
                >
                  <img src={url} alt="" className="size-full" />
                </button>
              );
            })}
          </div>
        </div>

        {updateProfile.isError && (
          <p className="font-mono text-label-mono text-neon-pink">
            Failed to save profile. Please try again.
          </p>
        )}

        <div className="mt-2 flex justify-end">
          <NeonButton type="submit" disabled={updateProfile.isPending}>
            {updateProfile.isPending ? "Saving..." : "Save Identity"}
          </NeonButton>
        </div>
      </form>
    </NeonPanel>
  );
}
