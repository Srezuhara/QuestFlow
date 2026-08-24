import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles/tokens.css";
import { Providers } from "./app/providers";
import { AppRouter } from "./app/router";
import { registerServiceWorker } from "./lib/push";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}

// Registration alone triggers no permission prompt — safe to call at load.
// Actually requesting push permission (`enablePush()`) only ever happens
// from a user gesture, in `features/reminders`.
void registerServiceWorker();

createRoot(rootElement).render(
  <StrictMode>
    <Providers>
      <AppRouter />
    </Providers>
  </StrictMode>,
);
