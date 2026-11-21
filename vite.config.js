import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [react(), tailwindcss()],
    // ApexCharts is large; it is already split into its own lazy-loaded chunk
    build: { chunkSizeWarningLimit: 1300 },
    server: {
      port: 5173,
      // In dev, every request to /api/* is forwarded to the backend.
      // This avoids CORS issues while the backend team works locally.
      proxy: {
        '/api': {
          target: env.VITE_BACKEND_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})
