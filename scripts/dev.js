#!/usr/bin/env node
/**
 * Script de démarrage simplifié pour le développement.
 * Lance automatiquement backend puis frontend, et ouvre le navigateur.
 */
const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { promisify } = require('util');

const execAsync = promisify(exec);

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
function waitForBackend(port, maxAttempts = 45, delay = 1000) {
  return new Promise((resolve, reject) => {
    let attempts = 0;
    
    const check = () => {
      attempts++;
      const req = http.get(`http://localhost:${port}/health`, (res) => {
        if (res.statusCode === 200) {
          resolve();
        } else {
          if (attempts >= maxAttempts) {
            reject(new Error(`Le backend n'a pas répondu correctement après ${maxAttempts} tentatives (${maxAttempts * delay / 1000}s)`));
          } else {
            setTimeout(check, delay);
          }
        }
      });
      
      req.on('error', () => {
        if (attempts >= maxAttempts) {
          reject(new Error(`Le backend n'a pas démarré après ${maxAttempts} tentatives (${maxAttempts * delay / 1000}s). Vérifiez les logs ci-dessus.`));
        } else {
          setTimeout(check, delay);
        }
      });
      
      req.setTimeout(500, () => {
        req.destroy();
        if (attempts >= maxAttempts) {
          reject(new Error(`Le backend n'a pas démarré après ${maxAttempts} tentatives (${maxAttempts * delay / 1000}s). Vérifiez les logs ci-dessus.`));
        } else {
          setTimeout(check, delay);
        }
      });
    };
    
    check();
  });
}

// Fonction pour vérifier si un port est utilisé (toutes plateformes)
// Utilise une tentative de connexion socket pour une détection plus fiable
async function isPortInUse(port) {
  return new Promise((resolve) => {
    const server = http.createServer();
    server.listen(port, '127.0.0.1', () => {
      // Si on peut écouter, le port est libre
      server.once('close', () => resolve(false));
      server.close();
    });
    server.on('error', (err) => {
      if (err.code === 'EADDRINUSE' || err.code === 'EACCES') {
        // Port vraiment occupé ou accès refusé
        resolve(true);
      } else {
        // Autre erreur, considérer comme libre
        resolve(false);
      }
    });
    
    // Timeout de sécurité
    setTimeout(() => {
      server.removeAllListeners();
      server.close();
      resolve(false);
    }, 1000);
  });
}

// Fonction pour obtenir tous les PIDs des processus utilisant un port (Windows)
// Utilise PowerShell Get-NetTCPConnection qui est plus fiable que netstat
async function getPidsUsingPort(port) {
  if (process.platform === 'win32') {
    try {
      // Utiliser PowerShell pour obtenir les processus actifs uniquement
      const { stdout } = await execAsync(
        `powershell -Command "Get-NetTCPConnection -LocalPort ${port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Sort-Object -Unique"`
      );
      const rawPids = stdout.trim().split('\n')
        .filter(line => line.trim() && !isNaN(line.trim()))
        .map(line => parseInt(line.trim(), 10));
      
      // Filtrer immédiatement les processus qui n'existent plus
      // (Get-NetTCPConnection peut retourner des PIDs de processus récemment terminés)
      const existingPids = [];
      for (const pid of rawPids) {
        if (await processExists(pid)) {
          existingPids.push(pid);
        }
      }
      
      return existingPids;
    } catch (error) {
      // Fallback sur netstat si PowerShell échoue
      try {
        const { stdout } = await execAsync(`netstat -ano | findstr :${port} | findstr LISTENING`);
        const lines = stdout.trim().split('\n').filter(line => line.trim());
        const pids = new Set();
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          const pid = parts[parts.length - 1];
          if (pid && !isNaN(pid)) {
            pids.add(parseInt(pid, 10));
          }
        }
        // Filtrer les processus qui n'existent plus
        const existingPids = [];
        for (const pid of Array.from(pids)) {
          if (await processExists(pid)) {
            existingPids.push(pid);
          }
        }
        return existingPids;
      } catch (fallbackError) {
        return [];
      }
    }
  }
  return [];
}

// Fonction pour vérifier si un processus existe (Windows)
async function processExists(pid) {
  if (process.platform === 'win32') {
    try {
      const { stdout } = await execAsync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`);
      // tasklist peut réussir mais retourner un message d'information si le processus n'existe pas
      // Vérifier que la sortie contient réellement un PID (format CSV avec guillemets)
      if (stdout && stdout.trim() && !stdout.includes('aucune tâche') && !stdout.includes('no tasks')) {
        // Vérifier que la ligne contient bien le PID
        const lines = stdout.trim().split('\n').filter(line => line.trim());
        for (const line of lines) {
          // Format CSV: "Nom","PID","..."
          const pidMatch = line.match(/,"(\d+)",/);
          if (pidMatch && parseInt(pidMatch[1], 10) === pid) {
            return true;
          }
        }
      }
      return false;
    } catch (error) {
      // Si tasklist échoue, le processus n'existe pas
      return false;
    }
  }
  return false;
}

// Fonction pour obtenir le nom d'un processus par PID (Windows)
async function getProcessName(pid) {
  try {
    const { stdout } = await execAsync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`);
    if (stdout && stdout.trim() && !stdout.includes('aucune tâche')) {
      // Format CSV: "Nom","PID","Nom de session","# de session","Utilisation mémoire"
      const match = stdout.match(/"([^"]+)"/);
      return match ? match[1] : `PID ${pid}`;
    }
    return null; // Processus n'existe pas
  } catch (error) {
    return null; // Processus n'existe pas
  }
}

// Fonction pour tuer un processus par PID (Windows)
async function killProcess(pid) {
  try {
    await execAsync(`taskkill /F /PID ${pid}`);
    return true;
  } catch (error) {
    return false;
  }
}

// Fonction pour libérer un port s'il est utilisé
async function ensurePortFree(port, portName) {
  if (await isPortInUse(port)) {
    console.log(`⚠️  Le port ${port} (${portName}) est déjà utilisé.`);
    
    if (process.platform === 'win32') {
      const pids = await getPidsUsingPort(port);
      if (pids.length > 0) {
        console.log(`   Tentative de libération du port (${pids.length} processus trouvé${pids.length > 1 ? 's' : ''})...`);
        
        // Filtrer et afficher uniquement les processus qui existent vraiment
        const existingPids = [];
        const deadPids = [];
        
        for (const pid of pids) {
          const exists = await processExists(pid);
          if (exists) {
            existingPids.push(pid);
            const name = await getProcessName(pid);
            console.log(`   - ${name} (PID: ${pid})`);
          } else {
            deadPids.push(pid);
          }
        }
        
        // Informer sur les processus déjà terminés
        if (deadPids.length > 0) {
          console.log(`   ℹ️  ${deadPids.length} processus déjà terminé${deadPids.length > 1 ? 's' : ''} (port en cours de libération)...`);
        }
        
        // Si tous les processus sont morts, attendre que le port soit libéré naturellement
        if (existingPids.length === 0) {
          console.log(`   ℹ️  Tous les processus sont déjà terminés. Le port devrait être libéré sous peu...`);
          // Attendre plus longtemps car Windows peut mettre du temps à libérer le port
          const waitTime = 6000; // 6 secondes
          console.log(`   ⏳ Attente de libération naturelle du port (${waitTime/1000}s)...`);
          await new Promise(resolve => setTimeout(resolve, waitTime));
          
          // Vérifier que le port est libéré
          const stillInUse = await isPortInUse(port);
          if (stillInUse) {
            console.log(`   ⏳ Le port est toujours occupé, attente supplémentaire (5s)...`);
            await new Promise(resolve => setTimeout(resolve, 5000));
            const stillInUseAfterWait = await isPortInUse(port);
            if (stillInUseAfterWait) {
              console.log(`   ❌ Le port ${port} est toujours occupé après l'attente.`);
              console.log(`   Windows peut mettre plusieurs minutes à libérer un port.`);
              console.log(`   Vous pouvez essayer de redémarrer votre machine ou attendre quelques minutes.\n`);
              return false;
            }
          }
          console.log(`   ✅ Port ${port} libéré.\n`);
          return true;
        }
        
        // Tuer uniquement les processus qui existent
        let allKilled = true;
        for (const pid of existingPids) {
          const name = await getProcessName(pid);
          const killed = await killProcess(pid);
          if (killed) {
            console.log(`   ✅ Processus ${name} (PID: ${pid}) arrêté.`);
          } else {
            console.log(`   ⚠️  Impossible d'arrêter le processus ${name} (PID: ${pid}).`);
            allKilled = false;
          }
        }
        
        // Attendre que le port soit libéré (plus longtemps si des processus étaient déjà morts)
        const waitTime = deadPids.length > 0 ? 4000 : 2000;
        console.log(`   ⏳ Attente de libération du port (${waitTime/1000}s)...`);
        await new Promise(resolve => setTimeout(resolve, waitTime));
        
        // Vérifier que le port est vraiment libéré
        const stillInUse = await isPortInUse(port);
        if (stillInUse) {
          if (allKilled) {
            console.log(`   ⏳ Attente supplémentaire...`);
            await new Promise(resolve => setTimeout(resolve, 3000));
            const stillInUseAfterWait = await isPortInUse(port);
            if (stillInUseAfterWait) {
              console.log(`   ❌ Le port ${port} est toujours occupé.`);
              console.log(`   Vous devrez peut-être arrêter manuellement les processus.\n`);
              return false;
            }
          } else {
            console.log(`   ⚠️  Certains processus n'ont pas pu être arrêtés.`);
            console.log(`   Le port ${port} pourrait encore être utilisé.\n`);
            return false;
          }
        }
        
        console.log(`   ✅ Port ${port} libéré.\n`);
        return true;
      } else {
        // Aucun processus trouvé mais le port semble utilisé
        // Cela peut être un état TIME_WAIT ou une réservation Windows
        // On va essayer quand même de démarrer - le serveur échouera clairement si le port est vraiment occupé
        console.log(`   ℹ️  Aucun processus actif trouvé.`);
        console.log(`   ⚠️  Le port ${port} semble réservé (peut-être en état TIME_WAIT).`);
        console.log(`   💡 Tentative de démarrage quand même - le serveur échouera clairement si le port est vraiment occupé.\n`);
        return true; // Permettre le démarrage, le serveur gérera l'erreur
      }
    } else {
      console.log(`   ❌ Veuillez arrêter manuellement le processus utilisant le port ${port}.\n`);
      return false;
    }
  }
  return true;
}

// Fonction pour ouvrir le navigateur
function openBrowser(url) {
  const start = process.platform === 'win32' ? 'start' : 
                process.platform === 'darwin' ? 'open' : 'xdg-open';
  spawn(start, [url], { shell: true, stdio: 'ignore' });
}

async function startServers() {
  const apiPort = parseInt(process.env.API_PORT || '4242', 10);
  const frontendPort = parseInt(process.env.FRONTEND_PORT || '3000', 10);
  const frontendUrl = `http://localhost:${frontendPort}`;
  
  console.log('\n📦 Démarrage des serveurs...\n');
  console.log(`   Backend API:  http://localhost:${apiPort}`);
  console.log(`   Frontend:     ${frontendUrl}`);
  console.log(`   API Docs:     http://localhost:${apiPort}/api/docs\n`);

  // Vérifier que les ports sont libres
  console.log('🔍 Vérification des ports...');
  const apiPortFree = await ensurePortFree(apiPort, 'Backend API');
  const frontendPortFree = await ensurePortFree(frontendPort, 'Frontend');
  
  if (!apiPortFree || !frontendPortFree) {
    console.error('❌ Impossible de démarrer : ports requis non disponibles.');
    process.exit(1);
  }

  // Démarrer le backend
  console.log('🔄 Démarrage du backend...');
  let backend = null;
  let frontend = null;
  let startupTimeout = null;
  let isShuttingDown = false;

  // Fonction d'arrêt propre
  function shutdown(exitCode = 0, message = null) {
    if (isShuttingDown) return;
    isShuttingDown = true;

    if (startupTimeout) {
      clearTimeout(startupTimeout);
    }

    if (message) {
      console.error(`\n${message}`);
    }

    console.log('\n🛑 Arrêt des serveurs...');
    
    if (backend) {
      try {
        backend.kill('SIGTERM');
        // Force kill après 3 secondes si nécessaire
        setTimeout(() => {
          if (backend && !backend.killed) {
            backend.kill('SIGKILL');
          }
        }, 3000);
      } catch (err) {
        // Ignorer les erreurs lors de l'arrêt
      }
    }

    if (frontend) {
      try {
        frontend.kill('SIGTERM');
        setTimeout(() => {
          if (frontend && !frontend.killed) {
            frontend.kill('SIGKILL');
          }
        }, 3000);
      } catch (err) {
        // Ignorer les erreurs lors de l'arrêt
      }
    }

    setTimeout(() => {
      process.exit(exitCode);
    }, 1000);
  }

  // Gérer l'arrêt propre avec Ctrl+C
  process.on('SIGINT', () => {
    shutdown(0);
  });

  process.on('SIGTERM', () => {
    shutdown(0);
  });

  // Démarrer le backend
  backend = spawn('python', ['-m', 'api.main'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true,
    env: Object.assign({}, process.env, { RELOAD: 'true' }) // Force le hot reload
  });

  // Capturer les erreurs de démarrage immédiates
  backend.on('error', (err) => {
    let errorMsg = `\n❌ ERREUR: Impossible de démarrer le backend\n`;
    errorMsg += `   Cause: ${err.message}\n\n`;
    
    if (err.code === 'ENOENT') {
      errorMsg += `   💡 Python n'est pas trouvé dans le PATH.\n`;
      errorMsg += `   Vérifiez que Python est installé et accessible.\n`;
    } else if (err.message && err.message.includes('EADDRINUSE')) {
      errorMsg += `   💡 Le port ${apiPort} est occupé.\n`;
      errorMsg += `   Arrêtez le processus utilisant ce port ou changez avec: API_PORT=<autre_port>\n`;
    } else {
      errorMsg += `   💡 Vérifiez les logs ci-dessus pour plus de détails.\n`;
    }
    
    shutdown(1, errorMsg);
  });

  // Timeout de démarrage : si le backend ne répond pas après 45 secondes, arrêter
  startupTimeout = setTimeout(() => {
    if (!isShuttingDown) {
      shutdown(1, `\n❌ ERREUR: Le backend n'a pas démarré dans les 45 secondes\n   💡 Vérifiez les logs ci-dessus pour identifier le problème.\n`);
    }
  }, 45000);

  // Attendre que le backend soit prêt
  waitForBackend(apiPort)
    .then(() => {
      if (isShuttingDown) return;
      
      clearTimeout(startupTimeout);
      console.log('✅ Backend démarré et prêt!\n');
      
      // Démarrer le frontend une fois le backend prêt
      console.log('🔄 Démarrage du frontend...\n');
      frontend = spawn('npm', ['run', 'dev'], {
        cwd: path.join(__dirname, '..', 'frontend'),
        stdio: 'inherit',
        shell: true,
        env: Object.assign({}, process.env)
      });

      // Capturer les erreurs de démarrage du frontend
      frontend.on('error', (err) => {
        let errorMsg = `\n❌ ERREUR: Impossible de démarrer le frontend\n`;
        errorMsg += `   Cause: ${err.message}\n\n`;
        
        if (err.code === 'ENOENT') {
          errorMsg += `   💡 Node.js ou npm n'est pas trouvé dans le PATH.\n`;
          errorMsg += `   Vérifiez que Node.js est installé et accessible.\n`;
        } else {
          errorMsg += `   💡 Vérifiez les logs ci-dessus pour plus de détails.\n`;
        }
        
        shutdown(1, errorMsg);
      });

      // Attendre un peu que le frontend démarre, puis ouvrir le navigateur
      setTimeout(() => {
        if (!isShuttingDown) {
          console.log(`\n🌐 Ouverture du navigateur sur ${frontendUrl}...\n`);
          openBrowser(frontendUrl);
        }
      }, 3000);

      // Surveiller l'arrêt du backend
      backend.on('close', (code) => {
        if (isShuttingDown) return;
        
        if (code !== 0 && code !== null) {
          shutdown(1, '\n❌ ERREUR: Le backend s\'est arrêté de manière inattendue\n   💡 Vérifiez les logs ci-dessus pour identifier le problème.\n');
        } else {
          // Arrêt normal
          shutdown(0);
        }
      });

      // Surveiller l'arrêt du frontend
      frontend.on('close', (code) => {
        if (isShuttingDown) return;
        
        if (code !== 0 && code !== null) {
          shutdown(1, '\n❌ ERREUR: Le frontend s\'est arrêté de manière inattendue\n   💡 Vérifiez les logs ci-dessus pour identifier le problème.\n');
        } else {
          // Arrêt normal
          shutdown(0);
        }
      });
    })
    .catch((err) => {
      if (isShuttingDown) return;
      
      let errorMsg = `\n❌ ERREUR: Le backend n'a pas démarré correctement\n`;
      errorMsg += `   Cause: ${err.message}\n\n`;
      errorMsg += `   💡 Vérifiez que:\n`;
      errorMsg += `      - Le port ${apiPort} est libre\n`;
      errorMsg += `      - Les dépendances Python sont installées (pip install -r requirements.txt)\n`;
      errorMsg += `      - Aucune erreur dans les logs ci-dessus\n`;
      
      shutdown(1, errorMsg);
    });
}

main();

