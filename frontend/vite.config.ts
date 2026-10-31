import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: "127.0.0.1",
    port: 5330,
    strictPort: true,
    // Keeps the browser on one origin, so no CORS in development.
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
