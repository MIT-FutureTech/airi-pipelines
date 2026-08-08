import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const apiProxyTarget = env.VITE_API_PROXY_TARGET;

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
        "@shared": fileURLToPath(new URL("./shared", import.meta.url)),
      },
    },
    server: apiProxyTarget
      ? {
          proxy: {
            "/api": {
              target: apiProxyTarget,
              changeOrigin: true,
              secure: true,
            },
          },
        }
      : undefined,
  };
});
