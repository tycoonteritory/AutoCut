# 🪟 Guide d'installation AutoCut pour Windows

## Problème courant : Erreur "failed to build openai-whisper"

Si vous rencontrez cette erreur, c'est parce que `openai-whisper` nécessite des outils de compilation C/C++ sur Windows.

## Solutions (choisissez-en une)

### ✅ Solution 1 : Installer Visual Studio Build Tools (RECOMMANDÉ)

1. Téléchargez **Visual Studio Build Tools** :
   - https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. Lancez l'installeur et sélectionnez :
   - ✅ "Développement Desktop en C++"
   - ✅ "Kit de développement Windows 10/11 SDK"

3. Redémarrez votre ordinateur

4. Relancez `start.bat`

### ✅ Solution 2 : Installation manuelle avec pip

Ouvrez une invite de commande **en tant qu'administrateur** et exécutez :

```cmd
cd chemin\vers\AutoCut
backend\venv\Scripts\activate
pip install --upgrade pip
pip install wheel
pip install openai-whisper --no-build-isolation
```

### ✅ Solution 3 : Utiliser une version alternative de Whisper

Si les solutions ci-dessus ne fonctionnent pas, vous pouvez utiliser `whisper-cpp` ou l'API OpenAI directement :

1. Éditez `backend/requirements_windows.txt`
2. Commentez la ligne `openai-whisper==20231117` :
   ```
   # openai-whisper==20231117  # Désactivé - utilise l'API OpenAI à la place
   ```
3. Relancez `start.bat`

**Note :** Cette solution nécessite une clé API OpenAI et sera payante selon l'utilisation.

---

## Prérequis Windows

### 1. Python 3.9 ou supérieur

Téléchargez depuis : https://www.python.org/downloads/

⚠️ **IMPORTANT** : Cochez "Add Python to PATH" lors de l'installation !

### 2. Node.js 18 ou supérieur

Téléchargez depuis : https://nodejs.org/

### 3. FFmpeg

**Option A : Avec Chocolatey (plus simple)**
```cmd
choco install ffmpeg
```

**Option B : Installation manuelle**
1. Téléchargez FFmpeg : https://www.gyan.dev/ffmpeg/builds/
2. Extrayez l'archive (ex: `C:\ffmpeg`)
3. Ajoutez `C:\ffmpeg\bin` à votre PATH :
   - Panneau de configuration → Système → Paramètres système avancés
   - Variables d'environnement → Path → Nouveau
   - Ajoutez : `C:\ffmpeg\bin`

---

## Vérification de l'installation

Pour vérifier que tout est installé correctement :

```cmd
python --version
node --version
ffmpeg -version
```

Si toutes les commandes retournent une version, vous êtes prêt ! 🎉

---

## Lancer AutoCut

Double-cliquez sur `start.bat` ou dans une invite de commande :

```cmd
start.bat
```

---

## Problèmes courants

### "Python n'est pas reconnu..."

- Réinstallez Python en cochant "Add Python to PATH"
- Ou ajoutez manuellement Python au PATH

### "Node.js n'est pas reconnu..."

- Redémarrez votre ordinateur après l'installation de Node.js
- Vérifiez que Node.js est dans le PATH

### "FFmpeg n'est pas reconnu..."

- Vérifiez que FFmpeg est dans le PATH
- Redémarrez votre invite de commande

### Les serveurs ne démarrent pas

1. Vérifiez que les ports 8765 et 5173 ne sont pas utilisés
2. Consultez les fichiers de logs :
   - `backend.log`
   - `frontend.log`

---

## Support

Si vous rencontrez des problèmes, ouvrez une issue sur GitHub avec :
- Votre version de Windows
- Le message d'erreur complet
- Le contenu des fichiers de logs
