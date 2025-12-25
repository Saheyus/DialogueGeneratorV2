#!/usr/bin/env node
/**
 * Script de démarrage simplifié pour le développement.
 * Lance automatiquement backend + frontend ensemble.
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

console.log('🚀 Démarrage DialogueGenerator en mode développement...\n');

// Vérifier que Node.js et Python sont disponibles
function checkCommand(command, errorMsg) {
  return new Promise((resolve) => {
    const proc = spawn(command, ['--version'], { shell: true, stdio: 'ignore' });
    proc.on('close', (code) => {
      if (code !== 0) {
        console.error(`❌ ${errorMsg}`);
        process.exit(1);
      }
      resolve();
    });
  });
}

async function main() {
  // Vérifications rapides
  await checkCommand('python', 'Python n\'est pas installé ou pas dans le PATH');
  await checkCommand('node', 'Node.js n\'est pas installé ou pas dans le PATH');

  // Vérifier que frontend/node_modules existe
  const frontendNodeModules = path.join(__dirname, '..', 'frontend', 'node_modules');
  if (!fs.existsSync(frontendNodeModules)) {
    console.log('⚠️  Installation des dépendances frontend...');
    const npmInstall = spawn('npm', ['install'], {
      cwd: path.join(__dirname, '..', 'frontend'),
      stdio: 'inherit',
      shell: true
    });
    npmInstall.on('close', (code) => {
      if (code !== 0) {
        console.error('❌ Échec de l\'installation des dépendances frontend');
        process.exit(1);
      }
      startServers();
    });
  } else {
    startServers();
  }
}

function startServers() {
  const apiPort = process.env.API_PORT || '4242';
  console.log('\n📦 Démarrage des serveurs...\n');
  console.log(`   Backend API:  http://localhost:${apiPort}`);
  console.log('   Frontend:     http://localhost:3000');
  console.log(`   API Docs:     http://localhost:${apiPort}/api/docs\n`);
  console.log('💡 Appuyez sur Ctrl+C pour arrêter tous les serveurs\n');

  // Démarrer le backend
  const backend = spawn('python', ['-m', 'api.main'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true,
    env: { ...process.env }
  });

  // Démarrer le frontend
  const frontend = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, '..', 'frontend'),
    stdio: 'inherit',
    shell: true
  });

  // Gérer l'arrêt propre
  process.on('SIGINT', () => {
    console.log('\n\n🛑 Arrêt des serveurs...');
    backend.kill();
    frontend.kill();
    process.exit(0);
  });

  backend.on('close', (code) => {
    if (code !== 0 && code !== null) {
      console.error('\n❌ Backend arrêté avec erreur');
      frontend.kill();
      process.exit(1);
    }
  });

  frontend.on('close', (code) => {
    if (code !== 0 && code !== null) {
      console.error('\n❌ Frontend arrêté avec erreur');
      backend.kill();
      process.exit(1);
    }
  });
}

main();

