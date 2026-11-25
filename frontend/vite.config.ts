/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import { contentSecurityPolicyPlugin } from "./csp";

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "VITE_");
  return {
    // The CSP <meta> tag is added to production builds only (see csp.ts).
    plugins: [react(), contentSecurityPolicyPlugin(env.VITE_API_BASE_URL ?? "")],
    server: {
      port: 5173,
      // Forward API calls to FastAPI, so the browser sees one origin (like on
      // Vercel) and the SameSite=Strict refresh cookie works in development.
      proxy: {
        "/api": {
          target: process.env.VITE_DEV_API_TARGET ?? "http://localhost:8000",
          changeOrigin: false,
        },
      },
    },
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      globals: false,
    },
  };
});
