import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunk for React and related libraries
          vendor: ['react', 'react-dom'],
          
          // VideoSDK chunk (this is the largest dependency)
          videosdk: ['@videosdk.live/react-sdk'],
          
          // UI libraries chunk
          ui: ['lucide-react', 'react-hot-toast'],
        },
      },
    },
    
    // Increase chunk size warning limit for VideoSDK
    chunkSizeWarningLimit: 1000,
    
    // Enable source maps for better debugging (optional)
    sourcemap: false,
    
    // Optimize for production
    minify: 'esbuild',
    target: 'esnext',
    
    // Split CSS
    cssCodeSplit: true,
  },
  
  // Optimize development server
  server: {
    hmr: {
      overlay: false
    }
  }
});
