#!/bin/bash
# Aller dans le dossier où se trouve le script (utile quand on double-clique)
cd "$(dirname "$0")"

# Lancer le fichier Python qui gère l'application native
python3 launcher.py
