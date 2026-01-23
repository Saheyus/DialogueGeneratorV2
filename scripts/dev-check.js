#!/usr/bin/env node
/**
 * Script de vérification des processus et ports pour le développement.
 * Détecte les processus "zombies" ou les ports bloqués.
 */
const { exec } = require('child_process');
const { promisify } = require('util');
const path = require('path');
const fs = require('fs');

const execAsync = promisify(exec);
const PROJECT_ROOT = path.join(__dirname, '..');
const services = require('./dev-services');

// Ports utilisés par le projet
const BACKEND_PORT = 4243;
const FRONTEND_PORT = 3000;

// Mode cleanup si --clean est passé
const shouldCleanup = process.argv.includes('--clean') || process.argv.includes('-c');

// Couleurs pour la console
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

// Vérifier si un port est utilisé
async function checkPort(port) {
  try {
    if (process.platform === 'win32') {
      const { stdout } = await execAsync(`netstat -ano | findstr ":${port}"`);
      if (stdout && stdout.trim()) {
        const lines = stdout.trim().split('\n');
        const pids = new Set();
        for (const line of lines) {
          const match = line.match(/\s+(\d+)\s*$/);
          if (match) {
            pids.add(parseInt(match[1], 10));
          }
        }
        return Array.from(pids);
      }
    } else {
      const { stdout } = await execAsync(`lsof -ti:${port}`);
      if (stdout && stdout.trim()) {
        return stdout.trim().split('\n').map(pid => parseInt(pid, 10));
      }
    }
    return [];
  } catch (error) {
    return [];
  }
}

// Vérifier si un processus existe et obtenir ses infos
async function getProcessInfo(pid) {
  try {
    if (process.platform === 'win32') {
      const { stdout } = await execAsync(
        `wmic process where "ProcessId=${pid}" get ProcessId,CommandLine,ExecutablePath /format:list`
      );
      if (stdout && stdout.includes(`ProcessId=${pid}`)) {
        const lines = stdout.split('\n');
        const info = { pid };
        for (const line of lines) {
          if (line.startsWith('CommandLine=')) {
            info.commandLine = line.substring('CommandLine='.length).trim();
          }
          if (line.startsWith('ExecutablePath=')) {
            info.executablePath = line.substring('ExecutablePath='.length).trim();
          }
        }
        return info;
      }
    } else {
      const { stdout } = await execAsync(`ps -p ${pid} -o pid,command=`);
      if (stdout && stdout.trim()) {
        const parts = stdout.trim().split(/\s+/, 2);
        return {
          pid: parseInt(parts[0], 10),
          commandLine: parts[1] || '',
        };
      }
    }
    return null;
  } catch (error) {
    return null;
  }
}

// Vérifier si un processus est lié au projet
function isProjectProcess(processInfo) {
  if (!processInfo || !processInfo.commandLine) {
    return false;
  }
  const cmd = processInfo.commandLine.toLowerCase();
  const projectPath = PROJECT_ROOT.toLowerCase();
  
  // Vérifier si le chemin du projet est dans la commande
  if (cmd.includes(projectPath)) {
    return true;
  }
  
  // Vérifier les commandes typiques du projet
  if (cmd.includes('api.main') || cmd.includes('python -m api.main')) {
    return true;
  }
  // Supporter le venv Python aussi
  if (cmd.includes('.venv') && cmd.includes('python')) {
    return true;
  }
  if (cmd.includes('vite') && cmd.includes('frontend')) {
    return true;
  }
  if (cmd.includes('npm run dev')) {
    return true;
  }
  
  return false;
}

// Vérifier le lockfile
function checkLockfile() {
  const lockfilePath = path.join(PROJECT_ROOT, '.dev', '.dev.lock');
  if (!fs.existsSync(lockfilePath)) {
    return { exists: false, content: null };
  }
  
  try {
    const content = JSON.parse(fs.readFileSync(lockfilePath, 'utf-8'));
    return { exists: true, content };
  } catch (error) {
    return { exists: true, content: null, error: error.message };
  }
}

// Point d'entrée principal
async function main() {
  log('\n🔍 Vérification des processus et ports du projet\n', 'cyan');
  
  let issuesFound = false;
  
  // 1. Vérifier les ports
  log('📡 Vérification des ports...', 'blue');
  const backendPids = await checkPort(BACKEND_PORT);
  const frontendPids = await checkPort(FRONTEND_PORT);
  
  if (backendPids.length > 0) {
    log(`   ⚠️  Port ${BACKEND_PORT} utilisé par: ${backendPids.join(', ')}`, 'yellow');
    issuesFound = true;
    
    // Vérifier si ces processus sont liés au projet
    for (const pid of backendPids) {
      const info = await getProcessInfo(pid);
      if (info) {
        if (isProjectProcess(info)) {
          log(`      🔴 PID ${pid} est lié au projet (zombie?)`, 'red');
          log(`         Commande: ${info.commandLine.substring(0, 100)}...`, 'yellow');
        } else {
          log(`      ℹ️  PID ${pid} n'est pas lié au projet`, 'blue');
        }
      }
    }
  } else {
    log(`   ✅ Port ${BACKEND_PORT} libre`, 'green');
  }
  
  if (frontendPids.length > 0) {
    log(`   ⚠️  Port ${FRONTEND_PORT} utilisé par: ${frontendPids.join(', ')}`, 'yellow');
    issuesFound = true;
    
    for (const pid of frontendPids) {
      const info = await getProcessInfo(pid);
      if (info) {
        if (isProjectProcess(info)) {
          log(`      🔴 PID ${pid} est lié au projet (zombie?)`, 'red');
          log(`         Commande: ${info.commandLine.substring(0, 100)}...`, 'yellow');
        } else {
          log(`      ℹ️  PID ${pid} n'est pas lié au projet`, 'blue');
        }
      }
    }
  } else {
    log(`   ✅ Port ${FRONTEND_PORT} libre`, 'green');
  }
  
  // 2. Vérifier le lockfile
  log('\n📄 Vérification du lockfile...', 'blue');
  const lockfile = checkLockfile();
  if (lockfile.exists) {
    if (lockfile.content) {
      log('   ⚠️  Lockfile présent:', 'yellow');
      if (lockfile.content.backend && lockfile.content.backend.pid) {
        const backendPid = lockfile.content.backend.pid;
        const backendInfo = await getProcessInfo(backendPid);
        if (backendInfo) {
          if (isProjectProcess(backendInfo)) {
            log(`      🔴 Backend PID ${backendPid} dans lockfile mais processus actif (zombie?)`, 'red');
            issuesFound = true;
          } else {
            log(`      ⚠️  Backend PID ${backendPid} dans lockfile mais processus non lié au projet`, 'yellow');
          }
        } else {
          log(`      ✅ Backend PID ${backendPid} dans lockfile mais processus n'existe plus (lockfile stale)`, 'green');
        }
      }
      if (lockfile.content.frontend && lockfile.content.frontend.pid) {
        const frontendPid = lockfile.content.frontend.pid;
        const frontendInfo = await getProcessInfo(frontendPid);
        if (frontendInfo) {
          if (isProjectProcess(frontendInfo)) {
            log(`      🔴 Frontend PID ${frontendPid} dans lockfile mais processus actif (zombie?)`, 'red');
            issuesFound = true;
          } else {
            log(`      ⚠️  Frontend PID ${frontendPid} dans lockfile mais processus non lié au projet`, 'yellow');
          }
        } else {
          log(`      ✅ Frontend PID ${frontendPid} dans lockfile mais processus n'existe plus (lockfile stale)`, 'green');
        }
      }
    } else {
      log('   ⚠️  Lockfile présent mais invalide (peut être supprimé)', 'yellow');
    }
  } else {
    log('   ✅ Aucun lockfile', 'green');
  }
  
  // Résumé et nettoyage
  log('\n📊 Résumé:', 'cyan');
  if (!issuesFound) {
    log('   ✅ Aucun processus zombie détecté', 'green');
    log('   ✅ Tous les ports sont libres', 'green');
    log('   ✅ Aucun lockfile stale', 'green');
    log('\n💡 Tout est propre ! Vous pouvez démarrer avec: npm run dev\n', 'green');
  } else {
    log('   ⚠️  Problèmes détectés (voir ci-dessus)', 'yellow');
    
    if (shouldCleanup) {
      log('\n🧹 Nettoyage automatique...', 'cyan');
      let cleaned = false;
      
      // Nettoyer les ports
      for (const pid of backendPids) {
        const info = await getProcessInfo(pid);
        if (info && isProjectProcess(info)) {
          log(`   🗑️  Arrêt du processus backend (PID: ${pid})...`, 'yellow');
          try {
            await services.killProcessTree(pid);
            cleaned = true;
          } catch (error) {
            log(`   ❌ Erreur lors de l'arrêt du PID ${pid}: ${error.message}`, 'red');
          }
        }
      }
      
      for (const pid of frontendPids) {
        const info = await getProcessInfo(pid);
        if (info && isProjectProcess(info)) {
          log(`   🗑️  Arrêt du processus frontend (PID: ${pid})...`, 'yellow');
          try {
            await services.killProcessTree(pid);
            cleaned = true;
          } catch (error) {
            log(`   ❌ Erreur lors de l'arrêt du PID ${pid}: ${error.message}`, 'red');
          }
        }
      }
      
      // Nettoyer le lockfile stale
      if (lockfile.exists && lockfile.content) {
        let shouldRemoveLock = false;
        if (lockfile.content.backend && lockfile.content.backend.pid) {
          const backendInfo = await getProcessInfo(lockfile.content.backend.pid);
          if (!backendInfo || !isProjectProcess(backendInfo)) {
            shouldRemoveLock = true;
          }
        }
        if (lockfile.content.frontend && lockfile.content.frontend.pid) {
          const frontendInfo = await getProcessInfo(lockfile.content.frontend.pid);
          if (!frontendInfo || !isProjectProcess(frontendInfo)) {
            shouldRemoveLock = true;
          }
        }
        
        if (shouldRemoveLock) {
          log('   🗑️  Suppression du lockfile stale...', 'yellow');
          try {
            const lockfilePath = path.join(PROJECT_ROOT, '.dev', '.dev.lock');
            fs.unlinkSync(lockfilePath);
            cleaned = true;
          } catch (error) {
            log(`   ❌ Erreur lors de la suppression du lockfile: ${error.message}`, 'red');
          }
        }
      }
      
      if (cleaned) {
        log('   ✅ Nettoyage terminé', 'green');
        log('\n💡 Vous pouvez maintenant démarrer avec: npm run dev\n', 'green');
      } else {
        log('   ℹ️  Aucun nettoyage nécessaire (processus non liés au projet)', 'blue');
      }
    } else {
      log('\n💡 Solutions:', 'cyan');
      log('   1. Nettoyer automatiquement: npm run dev:check --clean', 'blue');
      log('   2. Arrêter les processus zombies: npm run dev:stop', 'blue');
      log('   3. Nettoyer manuellement les ports si nécessaire', 'blue');
      log('   4. Supprimer le lockfile stale: rm .dev/.dev.lock', 'blue');
      log('');
    }
  }
}

main().catch((error) => {
  log(`❌ Erreur: ${error.message}`, 'red');
  process.exit(1);
});
