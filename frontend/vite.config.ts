import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    strictPort: false,
    proxy: {
      '/api': {
        target: process.env.VITE_API_URL || 'https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api/v1')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom'],
          'router': ['react-router-dom'],
          'api': ['axios']
        }
      }
    }
  }
})
