import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "https://report-assistant-backend-1029330440039.us-central1.run.app",
        changeOrigin: true,
      },
    },
  },
});
