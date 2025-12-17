import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Allow `start_application.bat` (or devs) to choose ports dynamically.
    // Defaults preserve the current behavior if env vars are not provided.
    port: Number.parseInt(process.env.VITE_DEV_PORT ?? '3000', 10),
    host: '127.0.0.1',
    proxy: {
      '/api': {
        target: `http://127.0.0.1:${process.env.VITE_BACKEND_PORT ?? '8000'}`,
        changeOrigin: true,
      },
      '/ws': {
        target: `ws://127.0.0.1:${process.env.VITE_BACKEND_PORT ?? '8000'}`,
        ws: true,
      },
    },
  },
  resolve: {
    alias: {
      // Polyfill buffer for plotly.js
      buffer: 'buffer/',
    },
  },
  optimizeDeps: {
    include: ['buffer'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          plotly: ['plotly.js', 'react-plotly.js'],
        },
      },
    },
  },
})
