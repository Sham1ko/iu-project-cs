import path from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value);

export default defineConfig(({ mode }) => {
  const rootEnvDir = path.resolve(__dirname, "..");
  const env = loadEnv(mode, rootEnvDir, "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "";

  return {
    envDir: rootEnvDir,
    plugins: [react(), tailwindcss()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      port: 5173,
      proxy: isAbsoluteUrl(apiBaseUrl)
        ? {
            "/api": {
              target: apiBaseUrl,
              changeOrigin: true,
            },
          }
        : undefined,
    },
  };
});
