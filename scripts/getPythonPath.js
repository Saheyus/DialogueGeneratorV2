#!/usr/bin/env node
/**
 * Utilitaire pour obtenir le chemin de l'interpréteur Python du venv.
 * Utilisé par les scripts npm pour garantir l'utilisation du venv.
 * 
 * Usage:
 *   const getPythonPath = require('./scripts/getPythonPath');
 *   const pythonPath = getPythonPath();
 *   
 * Ou en ligne de commande:
 *   node scripts/getPythonPath.js
 *   node scripts/getPythonPath.js -m api.main
 */

const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

/**
 * Détecte le chemin de l'interpréteur Python du venv.
 * @param {string} projectRoot - Chemin racine du projet (optionnel)
 * @returns {string} Chemin absolu vers l'interpréteur Python
 */
function getPythonPath(projectRoot = null) {
  if (!projectRoot) {
    projectRoot = path.join(__dirname, '..');
  }

  // Chemins possibles pour le venv
  const venvPaths = [
    path.join(projectRoot, '.venv', 'Scripts', 'python.exe'), // Windows
    path.join(projectRoot, '.venv', 'bin', 'python'),         // Unix
    path.join(projectRoot, 'venv', 'Scripts', 'python.exe'),  // Windows (alt)
    path.join(projectRoot, 'venv', 'bin', 'python'),          // Unix (alt)
  ];

  // Chercher le premier chemin existant
  for (const venvPath of venvPaths) {
    if (fs.existsSync(venvPath)) {
      return venvPath;
    }
  }

  // Fallback: utiliser Python global
  console.warn('⚠️  Venv non trouvé, utilisation de Python global');
  console.warn('   Créez le venv avec: npm run setup');
  return 'python';
}

/**
 * Vérifie si le venv existe.
 * @param {string} projectRoot - Chemin racine du projet (optionnel)
 * @returns {boolean} true si le venv existe
 */
function venvExists(projectRoot = null) {
  if (!projectRoot) {
    projectRoot = path.join(__dirname, '..');
  }

  const venvDirs = [
    path.join(projectRoot, '.venv'),
    path.join(projectRoot, 'venv'),
  ];

  return venvDirs.some(dir => fs.existsSync(dir));
}

/**
 * Affiche le chemin Python et quitte (mode CLI).
 */
function runCLI() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    // Afficher juste le chemin
    console.log(getPythonPath());
    process.exit(0);
  }
  
  // Exécuter une commande Python
  const pythonPath = getPythonPath();
  const proc = spawn(pythonPath, args, {
    stdio: 'inherit',
    shell: true,
    cwd: path.join(__dirname, '..')
  });
  
  proc.on('close', (code) => {
    process.exit(code || 0);
  });
  
  proc.on('error', (err) => {
    console.error(`❌ Erreur lors de l'exécution de Python: ${err.message}`);
    process.exit(1);
  });
}

// Mode CLI si exécuté directement
if (require.main === module) {
  runCLI();
}

// Export pour utilisation en tant que module
module.exports = getPythonPath;
module.exports.getPythonPath = getPythonPath;
module.exports.venvExists = venvExists;
