#!/usr/bin/env node
/**
 * Vérification rapide que le build frontend est à jour.
 */
const path = require('path');
const fs = require('fs');

const distPath = path.join(__dirname, '..', 'frontend', 'dist');
const indexHtml = path.join(distPath, 'index.html');

if (!fs.existsSync(distPath) || !fs.existsSync(indexHtml)) {
  console.log('⚠️  Le build frontend n\'existe pas. Exécutez: npm run build');
  process.exit(1);
}

console.log('✓ Build frontend présent');
process.exit(0);

