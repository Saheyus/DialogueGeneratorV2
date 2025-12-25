@echo off
REM Lancer l'application DialogueGenerator (UI)
cd /d %~dp0
REM Lancement du script de démarrage qui vérifie les dépendances
python launcher.py 