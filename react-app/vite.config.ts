import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    strictPort: true,
    // The browser calls /api on this dev server, which forwards it to Flask:
    // same origin for the browser, so no CORS is needed.
    // In Docker the target is the web service (API_PROXY_TARGET=http://web:5000).
    proxy: {
      '/api': process.env.API_PROXY_TARGET ?? 'http://localhost:5000',
    },
    // Docker on Windows does not pass file change events into the container: check for changes instead
    watch: process.env.VITE_USE_POLLING ? { usePolling: true, interval: 300 } : undefined,
  },
})
