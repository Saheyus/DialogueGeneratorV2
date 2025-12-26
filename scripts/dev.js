#!/usr/bin/env node
/**
 * Script de démarrage simplifié pour le développement.
 * Lance automatiquement backend puis frontend, et ouvre le navigateur.
 */
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');

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

// Fonction pour vérifier si le serveur backend est prêt
function waitForBackend(port, maxAttempts = 30, delay = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const check = () => {
      attempts++;
      const req = http.get(`http://localhost:${port}/health`, (res) => {
        if (res.statusCode === 200) {
          console.log('✅ Backend prêt!\n');
          resolve();
        } else {
          if (attempts >= maxAttempts) {
            reject(new Error(`Backend n'a pas répondu après ${maxAttempts} tentatives`));
          } else {
            setTimeout(check, delay);
          }
        }
      });
      
      req.on('error', () => {
        if (attempts >= maxAttempts) {
          reject(new Error(`Backend n'a pas démarré après ${maxAttempts} tentatives`));
        } else {
          setTimeout(check, delay);
        }
      });
      
      req.setTimeout(500, () => {
        req.destroy();
        if (attempts >= maxAttempts) {
          reject(new Error(`Backend n'a pas démarré après ${maxAttempts} tentatives`));
        } else {
          setTimeout(check, delay);
        }
      });
    };
    
    check();
  });
}

// Fonction pour ouvrir le navigateur
function openBrowser(url) {
  const start = process.platform === 'win32' ? 'start' : 
                process.platform === 'darwin' ? 'open' : 'xdg-open';
  spawn(start, [url], { shell: true, stdio: 'ignore' });
}

function startServers() {
  const apiPort = process.env.API_PORT || '4242';
  const frontendPort = process.env.FRONTEND_PORT || '3000';
  const frontendUrl = `http://localhost:${frontendPort}`;
  
  console.log('\n📦 Démarrage des serveurs...\n');
  console.log(`   Backend API:  http://localhost:${apiPort}`);
  console.log(`   Frontend:     ${frontendUrl}`);
  console.log(`   API Docs:     http://localhost:${apiPort}/api/docs\n`);

  // Démarrer le backend
  console.log('🔄 Démarrage du backend...');
  const backend = spawn('python', ['-m', 'api.main'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true,
    env: { ...process.env }
  });

  // Attendre que le backend soit prêt
  waitForBackend(apiPort)
    .then(() => {
      // Démarrer le frontend une fois le backend prêt
      console.log('🔄 Démarrage du frontend...\n');
      const frontend = spawn('npm', ['run', 'dev'], {
        cwd: path.join(__dirname, '..', 'frontend'),
        stdio: 'inherit',
        shell: true,
        env: { ...process.env }
      });

      // Attendre un peu que le frontend démarre, puis ouvrir le navigateur
      setTimeout(() => {
        console.log(`\n🌐 Ouverture du navigateur sur ${frontendUrl}...\n`);
        openBrowser(frontendUrl);
      }, 3000);

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
    })
    .catch((err) => {
      console.error(`\n❌ ${err.message}`);
      backend.kill();
      process.exit(1);
    });
}

main();

