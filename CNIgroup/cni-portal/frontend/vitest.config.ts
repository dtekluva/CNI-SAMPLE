import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Kept separate from vite.config.ts so the production `tsc` build doesn't
// type-check Vitest's config (whose bundled Vite types differ). Vitest loads
// this file automatically and takes precedence over vite.config.ts for tests.
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
  },
});
