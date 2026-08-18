import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { NeonButton, NeonPanel } from "@/components/ui";
import { authErrorMessage, useRegister } from "./hooks";

export function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const register = useRegister();
  const navigate = useNavigate();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    register.mutate(
      {
        email,
        password,
        handle,
        display_name: displayName,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      },
      { onSuccess: () => navigate("/", { replace: true }) },
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neon-black px-6 py-12">
      <NeonPanel className="w-full max-w-sm" glow>
        <p className="font-mono text-label-mono text-neon-lime uppercase">&gt;&gt; new architect</p>
        <h1 className="mt-2 font-display text-headline-lg-mobile text-on-surface">Register</h1>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-label-mono text-on-surface-variant uppercase">
              Display name
            </span>
            <input
              required
              autoComplete="name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-yellow"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-label-mono text-on-surface-variant uppercase">
              Handle
            </span>
            <input
              required
              pattern="^[a-zA-Z0-9_]+$"
              title="Letters, numbers, and underscores only"
              minLength={3}
              maxLength={32}
              value={handle}
              onChange={(e) => setHandle(e.target.value)}
              className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-yellow"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-label-mono text-on-surface-variant uppercase">
              Email
            </span>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-yellow"
            />
          </label>

          <label className="flex flex-col gap-1.5">
            <span className="font-mono text-label-mono text-on-surface-variant uppercase">
              Password
            </span>
            <input
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-yellow"
            />
          </label>

          {register.isError && (
            <p className="font-mono text-label-mono text-neon-pink">
              {authErrorMessage(register.error)}
            </p>
          )}

          <NeonButton type="submit" disabled={register.isPending} className="mt-2 w-full">
            {register.isPending ? "Provisioning…" : "Register"}
          </NeonButton>
        </form>

        <p className="mt-6 text-center font-body text-body-md text-on-surface-variant">
          Already have an account?{" "}
          <Link to="/login" className="text-neon-lime hover:underline">
            Log in
          </Link>
        </p>
      </NeonPanel>
    </main>
  );
}
