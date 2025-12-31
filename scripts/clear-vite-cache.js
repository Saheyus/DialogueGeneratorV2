#!/usr/bin/env node
/**
 * Script Node.js pour nettoyer le cache Vite (alternative cross-platform au script PowerShell).
 * Usage: node scripts/clear-vite-cache.js
 */
const fs = require('fs');
const path = require('path');

const projectRoot = path.join(__dirname, '..');
const viteCachePath = path.join(projectRoot, 'frontend', 'node_modules', '.vite');
const distPath = path.join(projectRoot, 'frontend', 'dist');

console.log('=== Nettoyage du cache Vite ===\n');
console.log(`Répertoire projet: ${projectRoot}\n`);

// Fonction pour supprimer récursivement un dossier
function removeRecursive(dirPath) {
  if (!fs.existsSync(dirPath)) {
    return false;
  }
  
  try {
    const files = fs.readdirSync(dirPath);
    for (const file of files) {
      const filePath = path.join(dirPath, file);
      const stat = fs.statSync(filePath);
      
      if (stat.isDirectory()) {
        removeRecursive(filePath);
      } else {
        fs.unlinkSync(filePath);
      }
    }
    fs.rmdirSync(dirPath);
    return true;
  } catch (error) {
    console.error(`Erreur lors de la suppression de ${dirPath}: ${error.message}`);
    return false;
  }
}

// Supprimer le cache Vite
if (fs.existsSync(viteCachePath)) {
  console.log(`Suppression du cache Vite: ${viteCachePath}`);
  if (removeRecursive(viteCachePath)) {
    console.log('✅ Cache Vite supprimé\n');
  } else {
    console.log('⚠️  Erreur lors de la suppression du cache Vite\n');
  }
} else {
  console.log('ℹ️  Cache Vite introuvable (déjà propre)\n');
}

// Supprimer le dossier dist si présent
if (fs.existsSync(distPath)) {
  console.log(`Suppression du dossier dist: ${distPath}`);
  if (removeRecursive(distPath)) {
    console.log('✅ Dossier dist supprimé\n');
  } else {
    console.log('⚠️  Erreur lors de la suppression du dossier dist\n');
  }
} else {
  console.log('ℹ️  Dossier dist introuvable (déjà propre)\n');
}

console.log('✅ Nettoyage terminé');
console.log('Vous pouvez maintenant lancer "npm run dev" pour un démarrage propre\n');
