import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss({
      content: [
        path.resolve(__dirname, "src/**/*.{ts,tsx}"),
        path.resolve(__dirname, "../../packages/ui/src/**/*.{ts,tsx}"),
      ],
    }),
  ],
  resolve: {
    alias: {
      "@mark/ui": path.resolve(__dirname, "../../packages/ui/src"),
      "@mark/shared": path.resolve(__dirname, "../../packages/shared/src"),
    },
  },
  clearScreen: false,
  server: {
    port: 5173,
    strictPort: true,
  },
  envPrefix: ["VITE_", "TAURI_"],
});
