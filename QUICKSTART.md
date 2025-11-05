# ⚡ AutoCut - Démarrage Rapide

Guide ultra-rapide pour lancer AutoCut en 2 minutes.

## 🚀 Installation Express

### Windows

1. **Installer les prérequis** (si pas déjà fait) :
   - Python 3.8+ : https://www.python.org/
   - Node.js 18+ : https://nodejs.org/
   - FFmpeg : `choco install ffmpeg` (avec Chocolatey)

2. **Lancer AutoCut** :
   ```
   Double-clic sur scripts/start_windows.bat
   ```

3. **C'est tout !** L'application s'ouvre dans votre navigateur.

### macOS

1. **Installer les prérequis** (si pas déjà fait) :
   ```bash
   # Avec Homebrew
   brew install python node ffmpeg
   ```

2. **Lancer AutoCut** :
   ```bash
   ./scripts/start_mac.sh
   ```

3. **C'est tout !** L'application s'ouvre dans votre navigateur.

## 📝 Première utilisation

### Étape 1 : Télécharger une vidéo
- Glissez votre fichier MP4/MOV dans la zone de téléchargement
- Ou cliquez pour parcourir

### Étape 2 : Lancer le traitement
- Ajustez les paramètres si nécessaire (optionnel)
- Cliquez sur "🚀 Process Video"
- Attendez la fin du traitement (progression en temps réel)

### Étape 3 : Télécharger les exports
- Cliquez sur "Premiere Pro XML" ou "Final Cut Pro XML"
- Importez le fichier dans votre éditeur vidéo

## ⚙️ Paramètres recommandés

| Type de contenu | Seuil (dB) | Durée min (ms) | Padding (ms) |
|-----------------|------------|----------------|--------------|
| **Podcast/Interview** | -40 | 500 | 100 |
| **Tutoriel** | -35 | 300 | 150 |
| **Vlog** | -45 | 700 | 200 |
| **Gaming** | -50 | 1000 | 100 |

## 🎯 Conseils

- **Premier test** : Commencez avec une vidéo courte (< 5 min)
- **Trop de coupes** : Augmentez la durée minimale ou diminuez le seuil (ex: -45)
- **Pas assez de coupes** : Diminuez la durée minimale ou augmentez le seuil (ex: -35)
- **Fichiers volumineux** : Soyez patient, le traitement peut prendre du temps

## 🆘 Problème ?

### Le script ne démarre pas
- Vérifiez que tous les prérequis sont installés
- Exécutez `python --version`, `node --version`, `ffmpeg -version`

### "Port already in use"
- Un service utilise déjà les ports 8765 ou 5173
- Arrêtez l'autre service ou modifiez les ports dans la config

### Traitement très lent
- Normal pour vidéos > 1h
- Fermez les autres applications
- Sur Windows : Ajoutez une exception antivirus pour le dossier AutoCut

## 📖 Documentation complète

Lisez `README.md` pour :
- Configuration avancée
- API endpoints
- Architecture du projet
- Guide de développement

---

**Besoin d'aide ?** Ouvrez une issue sur GitHub ou consultez la FAQ dans le README.
