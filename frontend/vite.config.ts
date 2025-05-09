import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/tools': 'http://127.0.0.1:8000' // Alterado de localhost para 127.0.0.1
    }
  }
})
