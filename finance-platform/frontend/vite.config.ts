import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react()
  ],
  server: {
    proxy: {
      // Proxy /api/* from React (5173) -> Node.js backend (5000)
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      // Proxy /gateway/* from React (5173) -> Java Gateway (8080)
      // This avoids CORS entirely for health checks
      '/gateway': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/gateway/, ''),
      },
    }
  }
})
