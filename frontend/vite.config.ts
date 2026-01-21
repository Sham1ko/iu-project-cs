import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

const isAbsoluteUrl = (value: string) => /^https?:\/\//i.test(value);

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiBaseUrl = env.VITE_API_BASE_URL || "";

  return {
    plugins: [react()],
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
