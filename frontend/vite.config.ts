/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    host: true,
    port: 5173,
    watch: {
      // bind-mounted volume in Docker on Windows/macOS needs polling to
      // pick up file changes reliably
      usePolling: true,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    // Vitest's default include glob also matches `*.spec.ts`, which is
    // exactly the naming convention Playwright's own specs in `e2e/` use —
    // without this they'd get collected and run (and fail) as vitest tests.
    exclude: ["**/node_modules/**", "**/dist/**", "e2e/**"],
  },
});
