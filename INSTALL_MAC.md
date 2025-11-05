# 🍎 Installation et Lancement sur macOS

## ⚠️ Erreur courante

**NE PAS copier-coller les backticks markdown** (```bash et ```) !

❌ **FAUX** :
```
```bash
./scripts/start_mac.sh
```
```

✅ **CORRECT** :
```
./scripts/start_mac.sh
```

## 🚀 Guide de lancement étape par étape

### Étape 1 : Ouvrir le Terminal

1. Appuyez sur **Cmd + Space**
2. Tapez **Terminal**
3. Appuyez sur **Entrée**

### Étape 2 : Naviguer vers le dossier AutoCut

```bash
cd ~/chemin/vers/AutoCut
```

Par exemple, si AutoCut est dans Documents :
```bash
cd ~/Documents/AutoCut
```

Ou si AutoCut est sur le Bureau :
```bash
cd ~/Desktop/AutoCut
```

### Étape 3 : Vérifier que vous êtes dans le bon dossier

```bash
pwd
ls
```

Vous devriez voir : `backend/`, `frontend/`, `scripts/`, `README.md`, etc.

### Étape 4 : Lancer AutoCut

**Tapez exactement ceci (SANS les backticks) :**

```bash
./scripts/start_mac.sh
```

Appuyez sur **Entrée**.

### Étape 5 : Première exécution

Le script va :
1. ✅ Vérifier Python, Node.js, FFmpeg
2. 📦 Installer les dépendances (peut prendre 2-3 minutes)
3. 🚀 Lancer le backend et le frontend
4. 🌐 Ouvrir votre navigateur automatiquement

## 🔧 Prérequis (à installer si nécessaire)

### Vérifier si tout est installé

```bash
python3 --version
node --version
ffmpeg -version
```

### Installer les prérequis manquants

#### Option 1 : Avec Homebrew (recommandé)

Si Homebrew n'est pas installé :
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Puis installez les dépendances :
```bash
brew install python node ffmpeg
```

#### Option 2 : Installation manuelle

1. **Python 3.8+** : https://www.python.org/downloads/
2. **Node.js 18+** : https://nodejs.org/
3. **FFmpeg** : https://evermeet.cx/ffmpeg/ (téléchargez et mettez dans `/usr/local/bin`)

## 🛑 Arrêter AutoCut

### Option 1 : Dans le Terminal où AutoCut tourne
Appuyez sur **Ctrl + C**

### Option 2 : Avec le script stop
Dans un nouveau Terminal :
```bash
cd ~/chemin/vers/AutoCut
./scripts/stop_mac.sh
```

## 🐛 Problèmes fréquents

### "Permission denied"
Rendez le script exécutable :
```bash
chmod +x scripts/start_mac.sh scripts/stop_mac.sh
```

### "command not found: python3"
Python n'est pas installé. Installez-le avec Homebrew :
```bash
brew install python
```

### "command not found: node"
Node.js n'est pas installé. Installez-le avec Homebrew :
```bash
brew install node
```

### "command not found: ffmpeg"
FFmpeg n'est pas installé. Installez-le avec Homebrew :
```bash
brew install ffmpeg
```

### "Port already in use"
Un service utilise déjà le port 8765 ou 5173. Tuez les processus :
```bash
lsof -ti:8765 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

Puis relancez AutoCut.

### Le navigateur ne s'ouvre pas
Ouvrez manuellement : http://localhost:5173

## 📝 Commandes utiles

### Voir les logs en temps réel
```bash
# Backend
tail -f backend.log

# Frontend
tail -f frontend.log
```

### Vérifier les ports utilisés
```bash
lsof -i :8765  # Backend
lsof -i :5173  # Frontend
```

### Tuer un processus sur un port
```bash
lsof -ti:8765 | xargs kill -9
```

## ✅ Commandes à copier-coller (dans l'ordre)

Voici toutes les commandes dans l'ordre pour un démarrage rapide :

```bash
# 1. Aller dans le dossier AutoCut
cd ~/Documents/AutoCut  # Ajustez le chemin

# 2. Vérifier qu'on est au bon endroit
pwd
ls

# 3. Rendre le script exécutable (une seule fois)
chmod +x scripts/start_mac.sh scripts/stop_mac.sh

# 4. Lancer AutoCut
./scripts/start_mac.sh
```

## 🎉 Une fois lancé

1. Le navigateur s'ouvre sur http://localhost:5173
2. Glissez-déposez votre vidéo MP4/MOV
3. Ajustez les paramètres si nécessaire
4. Cliquez sur "🚀 Process Video"
5. Téléchargez les exports XML

## 💡 Astuce zsh

macOS utilise maintenant **zsh** par défaut au lieu de bash. Si vous voyez :
```
The default interactive shell is now zsh.
```

Vous pouvez :
- Ignorer le message (bash fonctionne toujours)
- Ou passer à zsh : `chsh -s /bin/zsh` (puis redémarrez le Terminal)

Le script fonctionne avec **bash** ET **zsh** ! ✅

---

**Besoin d'aide ?** Ouvrez une issue sur GitHub avec :
- Le message d'erreur exact
- Le contenu de `backend.log` et `frontend.log`
- Votre version de macOS
