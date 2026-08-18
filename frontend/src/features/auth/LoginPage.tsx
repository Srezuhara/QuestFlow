import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { NeonButton, NeonPanel } from "@/components/ui";
import { authErrorMessage, useLogin } from "./hooks";

export function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const login = useLogin();
  const navigate = useNavigate();
  const location = useLocation();

  const redirectTo = (location.state as { from?: string } | null)?.from ?? "/";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ email, password }, { onSuccess: () => navigate(redirectTo, { replace: true }) });
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-neon-black px-6 py-12">
      <NeonPanel className="w-full max-w-sm" glow>
        <p className="font-mono text-label-mono text-neon-lime uppercase">
          &gt;&gt; access terminal
        </p>
        <h1 className="mt-2 font-display text-headline-lg-mobile text-on-surface">Log In</h1>

        <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-5">
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
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="border border-outline-variant bg-surface-container-lowest px-3 py-2 font-body text-body-md text-on-surface outline-none focus:border-neon-yellow"
            />
          </label>

          {login.isError && (
            <p className="font-mono text-label-mono text-neon-pink">
              {authErrorMessage(login.error)}
            </p>
          )}

          <NeonButton type="submit" disabled={login.isPending} className="mt-2 w-full">
            {login.isPending ? "Authenticating…" : "Log In"}
          </NeonButton>
        </form>

        <p className="mt-6 text-center font-body text-body-md text-on-surface-variant">
          No account?{" "}
          <Link to="/register" className="text-neon-lime hover:underline">
            Register
          </Link>
        </p>
      </NeonPanel>
    </main>
  );
}
