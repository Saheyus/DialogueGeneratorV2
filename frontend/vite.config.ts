/// <reference types="vite/client" />
/// <reference types="vite/client" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: 'localhost', // Démarrer sur localhost
    strictPort: true, // Échoue si le port est déjà utilisé au lieu de prendre un autre port
    open: false, // Ne pas ouvrir automatiquement (géré par scripts/dev.js)
    proxy: {
      '/api': {
        target: 'http://localhost:4242',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Désactiver les source maps en production pour réduire la taille
    minify: 'terser', // Utiliser terser pour une meilleure minification
    terserOptions: {
      compress: {
        drop_console: true, // Supprimer les console.log en production
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          // Séparer les dépendances en chunks pour optimiser le chargement
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom'],
          api: ['axios'],
          store: ['zustand'],
        },
      },
    },
  },
  // Base path pour déploiement en sous-dossier (optionnel)
  // base: '/dialogue-generator/',
})

