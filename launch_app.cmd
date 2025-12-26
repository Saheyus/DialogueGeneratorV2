@echo off
REM ⚠️ DÉPRÉCIÉ : Lancer l'application DialogueGenerator (UI desktop)
REM Utiliser l'interface web React à la place : npm run dev
echo ⚠️ DÉPRÉCIÉ : Interface desktop dépréciée. Utiliser 'npm run dev' pour l'interface web.
cd /d %~dp0
REM Lancement du script de démarrage qui vérifie les dépendances
python launcher.py 