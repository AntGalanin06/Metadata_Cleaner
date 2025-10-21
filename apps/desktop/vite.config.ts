import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tauri from "@tauri-apps/vite-plugin";

export default defineConfig(() => ({
  plugins: [
    react(),
    tauri({
      embeddedServer: {
        active: true,
        windowLabels: ["main"],
      },
    }),
  ],
  server: {
    port: 1420,
    strictPort: true,
  },
  clearScreen: false,
}));
