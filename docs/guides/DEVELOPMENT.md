# Guide de Développement - Diagnostic des Problèmes de Rafraîchissement

Ce guide explique comment diagnostiquer et résoudre les problèmes de rafraîchissement lors du développement avec Vite et React.

## Problème : Les changements ne sont pas visibles après `npm run dev`

### Causes possibles

1. **Cache Vite obsolète** : Le cache de pré-transformation dans `node_modules/.vite` peut être obsolète
2. **HMR (Hot Module Replacement) défaillant** : Le WebSocket pour le rafraîchissement automatique ne fonctionne pas
3. **Watch de fichiers Windows** : Problèmes connus avec le watch de fichiers sur Windows
4. **Cache HTTP du backend** : Le backend peut envoyer des headers de cache agressifs
5. **Cache du navigateur** : Le navigateur peut mettre en cache les assets

## Solutions rapides

### 1. Nettoyer le cache Vite

```bash
# Depuis la racine du projet
npm run dev:clean

# Ou depuis frontend/
cd frontend
npm run dev:clean

# Ou manuellement
.\scripts\clear-vite-cache.ps1
```

### 2. Forcer un rebuild complet

```bash
# Depuis frontend/
npm run dev:force
```

### 3. Vérifier que le HMR fonctionne

1. Ouvrez la console du navigateur (F12)
2. Allez dans l'onglet **Network**
3. Filtrez par **WS** (WebSocket)
4. Vous devriez voir une connexion WebSocket vers `ws://localhost:3000/`
5. Si la connexion est fermée ou absente, le HMR ne fonctionne pas

### 4. Vider le cache du navigateur

- **Chrome/Edge** : `Ctrl+Shift+Delete` → Cocher "Images et fichiers en cache" → Effacer
- **Firefox** : `Ctrl+Shift+Delete` → Cocher "Cache" → Effacer
- **Ou** : Ouvrir en navigation privée pour tester

### 5. Redémarrer avec nettoyage automatique

```bash
npm run dev:clean
```

Cette commande nettoie automatiquement le cache avant de démarrer.

## Diagnostic étape par étape

### Étape 1 : Vérifier que le serveur Vite démarre correctement

Lors du démarrage avec `npm run dev`, vous devriez voir :

```
✅ Backend démarré et prêt!
🔄 Démarrage du frontend...
✅ Frontend démarré sur http://localhost:3000
📡 HMR (Hot Module Replacement) activé
```

Si vous ne voyez pas ces messages, il y a un problème de démarrage.

### Étape 2 : Vérifier les logs Vite

Dans la console où `npm run dev` est lancé, vous devriez voir :

```
VITE v4.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

Si vous voyez des erreurs, notez-les et consultez la section "Erreurs courantes" ci-dessous.

### Étape 3 : Vérifier la connexion WebSocket HMR

1. Ouvrez `http://localhost:3000` dans votre navigateur
2. Ouvrez les outils de développement (F12)
3. Allez dans l'onglet **Network**
4. Filtrez par **WS** (WebSocket)
5. Vous devriez voir une connexion vers `ws://localhost:3000/`

**Si la connexion est absente ou fermée :**
- Vérifiez que le port 3000 n'est pas bloqué par un firewall
- Vérifiez que vous n'utilisez pas un proxy qui bloque les WebSockets
- Essayez de redémarrer avec `npm run dev:clean`

### Étape 4 : Tester un changement simple

1. Ouvrez un fichier React (ex: `frontend/src/App.tsx`)
2. Modifiez un texte visible (ex: un titre)
3. Sauvegardez le fichier
4. **Sans recharger la page**, le changement devrait apparaître automatiquement

**Si le changement n'apparaît pas :**
- Vérifiez la console du navigateur pour des erreurs
- Vérifiez que le fichier est bien sauvegardé
- Vérifiez que le watch de fichiers fonctionne (voir ci-dessous)

### Étape 5 : Vérifier le watch de fichiers

Vite utilise `chokidar` pour surveiller les changements de fichiers. Sur Windows, cela peut parfois échouer.

**Symptômes :**
- Les changements ne sont pas détectés
- Le HMR ne se déclenche pas

**Solutions :**
1. Vérifiez que vous n'avez pas trop de fichiers ouverts
2. Vérifiez que le chemin du projet n'est pas trop long (problème Windows)
3. Essayez de redémarrer avec `npm run dev:clean`
4. Si le problème persiste, activez le polling dans `vite.config.ts` :

```typescript
server: {
  watch: {
    usePolling: true, // Forcer le polling sur Windows
    interval: 1000,
  },
}
```

## Vérification de la configuration

### Configuration HMR dans `vite.config.ts`

La configuration HMR devrait être :

```typescript
server: {
  hmr: {
    protocol: 'ws',
    host: 'localhost',
    port: 3000,
    clientPort: 3000,
    overlay: true,
  },
}
```

### Headers HTTP anti-cache

En développement, le backend devrait envoyer :

```
Cache-Control: no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0
Pragma: no-cache
Expires: 0
```

Ces headers sont automatiquement ajoutés par le middleware `DevNoCacheMiddleware` en développement.

### Cache HTTP du backend

Le cache HTTP du backend est **automatiquement désactivé en développement** (voir `api/middleware/http_cache.py`).

Pour vérifier :

```bash
# Vérifier que ENVIRONMENT n'est pas "production"
echo $env:ENVIRONMENT  # Windows PowerShell
# Devrait afficher "development" ou rien
```

## Erreurs courantes

### "Port 3000 is already in use"

**Solution :**
```bash
# Arrêter le processus utilisant le port
# Le script dev.js le fait automatiquement, mais si ça échoue :
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### "WebSocket connection failed"

**Causes possibles :**
- Firewall bloquant le port 3000
- Proxy bloquant les WebSockets
- Conflit de port

**Solutions :**
1. Vérifiez votre firewall
2. Désactivez temporairement votre proxy
3. Changez le port dans `vite.config.ts` :

```typescript
server: {
  port: 3001, // Changer le port
}
```

### "Cannot find module" ou erreurs d'import

**Solution :**
```bash
# Nettoyer et réinstaller
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev:clean
```

### Les changements ne sont pas visibles même après rechargement

**Solution :**
1. Nettoyer le cache Vite : `npm run dev:clean`
2. Vider le cache du navigateur (voir ci-dessus)
3. Redémarrer avec `npm run dev:clean`
4. Si le problème persiste, vérifier les headers HTTP dans l'onglet Network des DevTools

## Checklist de diagnostic

Avant de signaler un problème, vérifiez :

- [ ] Le serveur Vite démarre sans erreur
- [ ] La connexion WebSocket HMR est active (onglet Network > WS)
- [ ] Le cache Vite a été nettoyé (`npm run dev:clean`)
- [ ] Le cache du navigateur a été vidé
- [ ] Les headers HTTP anti-cache sont présents (onglet Network > Headers)
- [ ] Le fichier modifié est bien sauvegardé
- [ ] Aucune erreur dans la console du navigateur
- [ ] Aucune erreur dans la console du serveur

## Commandes utiles

```bash
# Démarrage normal
npm run dev

# Démarrage avec nettoyage du cache
npm run dev:clean

# Nettoyer le cache manuellement (PowerShell)
.\scripts\clear-vite-cache.ps1

# Nettoyer le cache manuellement (Node.js, cross-platform)
node scripts/clear-vite-cache.js

# Forcer un rebuild complet (depuis frontend/)
cd frontend
npm run dev:force

# Vérifier les ports utilisés
netstat -ano | findstr :3000
netstat -ano | findstr :4243
```

## Configuration automatique

Le projet est configuré pour :

1. **Désactiver le cache HTTP en développement** : Le middleware `DevNoCacheMiddleware` ajoute automatiquement des headers anti-cache
2. **Désactiver le cache Vite si nécessaire** : Utilisez `npm run dev:clean` pour nettoyer avant démarrage
3. **Configurer le HMR robuste** : Configuration explicite dans `vite.config.ts` pour garantir le fonctionnement
4. **Watch de fichiers optimisé** : Configuration pour Windows avec fallback sur polling si nécessaire

## Support

Si le problème persiste après avoir suivi ce guide :

1. Vérifiez les logs complets (console serveur + console navigateur)
2. Vérifiez la version de Node.js (`node --version`) - recommandé : v18+
3. Vérifiez la version de npm (`npm --version`) - recommandé : v9+
4. Vérifiez que tous les fichiers de configuration sont à jour
5. Créez un ticket avec :
   - Version de Node.js/npm
   - Logs complets
   - Étapes pour reproduire
   - Résultats des vérifications de la checklist
