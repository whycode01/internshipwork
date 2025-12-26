import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  server: {
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path,
      },
      "/transcripts": {
        target: "http://127.0.0.1:8001",
        changeOrigin: true,
        rewrite: (path) => path,
      },
    },
  },
  plugins: [react(), tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": resolve("src"),
    },
  },
  assetsInclude: ['**/*.md']
})
