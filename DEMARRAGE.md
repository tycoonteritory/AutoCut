# 🎬 Guide de Démarrage AutoCut

## 🚀 Démarrage Rapide

### Méthode 1 : Double-clic (Recommandé)

**Double-cliquez sur le fichier :**
```
start.command
```

C'est tout ! Le script va :
- ✅ Vérifier toutes les dépendances (Python, Node.js, FFmpeg)
- ✅ Installer les packages nécessaires
- ✅ Démarrer le backend (port 8765)
- ✅ Démarrer le frontend (port 5173)
- ✅ Ouvrir votre navigateur automatiquement

### Méthode 2 : Terminal

```bash
./start.command
```

## 🛑 Arrêter AutoCut

Dans la fenêtre Terminal qui s'est ouverte :
- Appuyez sur **Ctrl+C**
- Tout sera arrêté proprement automatiquement

## 🔧 En cas de problème

### Le backend ne démarre pas

Vérifiez le fichier `backend.log` :
```bash
cat backend.log
```

### Le frontend ne démarre pas

Vérifiez le fichier `frontend.log` :
```bash
cat frontend.log
```

### Réinstaller les dépendances

```bash
# Supprimer l'environnement virtuel Python
rm -rf backend/venv

# Supprimer les packages Node.js
rm -rf frontend/node_modules

# Relancer start.command
./start.command
```

## 📍 URLs

- **Frontend (Interface)** : http://localhost:5173
- **Backend (API)** : http://localhost:8765

## ⚙️ Configuration requise

- **Python** : 3.9 ou supérieur (3.12 recommandé)
- **Node.js** : 16 ou supérieur
- **FFmpeg** : Dernière version

### Installation des dépendances

#### macOS (Homebrew)
```bash
brew install python@3.12 node ffmpeg
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-venv nodejs npm ffmpeg
```

## 📊 Fonctionnalités

### Mode Local (Gratuit)
- Détection de silence
- Détection d'hésitations basique
- Export XML (Premiere Pro / Final Cut Pro)

### Mode GPT-4 (Premium)
- Tout du mode Local +
- Détection d'hésitations IA
- Détection des meilleurs moments
- Analyse des vannes/originalité
- Titres & descriptions accrocheurs

## 🎯 Workflow

1. **Démarrer** : `./start.command`
2. **Choisir le mode** : Local ou GPT-4
3. **Uploader** : Glisser-déposer votre vidéo
4. **Traiter** : Cliquer sur "Process Video"
5. **Télécharger** : Récupérer vos fichiers XML

## 💡 Astuces

- **Logs en temps réel** : Les logs du backend s'affichent dans le Terminal
- **Ne fermez pas le Terminal** : Tant que vous utilisez AutoCut
- **Progression** : Vous verrez 0%, 20%, 40%... pendant le traitement
- **Historique** : Accédez à vos traitements précédents via le bouton "Historique"

## 🐛 Problèmes connus

### "Broken pipe" error
✅ **Corrigé** dans la dernière version !

### Progression bloquée à "Uploading..."
❌ Le backend n'est pas démarré
✅ Lancez `start.command` d'abord

### Port déjà utilisé
```bash
# Trouver et tuer le processus sur le port 8765
lsof -ti:8765 | xargs kill -9

# Trouver et tuer le processus sur le port 5173
lsof -ti:5173 | xargs kill -9
```

## 📞 Support

Pour signaler un bug ou demander une fonctionnalité :
- Ouvrez une issue sur GitHub
- Consultez la documentation complète

---

**Bon montage ! 🎬✨**
