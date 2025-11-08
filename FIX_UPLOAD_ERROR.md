# Fix: Upload Failed - Internal Server Error

## Diagnostic

L'erreur "Upload failed: Internal Server Error" se produit parce que le **serveur backend n'est pas en cours d'exécution**.

## Solution Automatique (Recommandé)

### Option 1 : Démarrage complet avec vérification automatique

Le script `demarrer_autocut.sh` a été amélioré pour :
- ✅ Vérifier automatiquement la présence des dépendances
- ✅ Installer uniquement les dépendances manquantes
- ✅ Vérifier que le backend démarre correctement
- ✅ Afficher des messages clairs sur l'état

```bash
./demarrer_autocut.sh
```

**Note** : Ce script nécessite FFmpeg installé. Si vous n'avez pas FFmpeg, utilisez l'Option 2.

### Option 2 : Démarrage backend seul (sans FFmpeg requis)

Si vous voulez juste tester l'API ou n'avez pas FFmpeg :

```bash
./start_backend_only.sh
```

Ce script :
- ✅ Crée automatiquement l'environnement virtuel si nécessaire
- ✅ Vérifie et installe les dépendances Python manquantes
- ✅ Démarre le backend sur le port 8765
- ✅ Ne nécessite pas FFmpeg (FFmpeg n'est requis que pour le traitement vidéo)

## Solution Manuelle

### 1. Installer les dépendances

```bash
# Créer l'environnement virtuel (si pas déjà fait)
python3 -m venv backend/venv

# Activer l'environnement virtuel
source backend/venv/bin/activate

# Installer les dépendances (peut prendre 5-10 minutes)
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

**Note importante** : L'installation peut prendre du temps car PyTorch + CUDA représentent environ 5GB de dépendances.

### 2. Démarrer le serveur backend

```bash
# Activer l'environnement virtuel
source backend/venv/bin/activate

# Démarrer le serveur sur le port 8765
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```

### 3. Démarrer le frontend (dans un autre terminal)

```bash
cd frontend
npm install  # Seulement si node_modules n'existe pas
npm run dev
```

## Vérification

### Test 1 : Vérifier que le backend répond

```bash
curl http://localhost:8765/health
```

**Réponse attendue** :
```json
{"status":"healthy","service":"AutoCut","version":"1.0.0"}
```

### Test 2 : Vérifier les endpoints

- Backend API : `http://localhost:8765`
- Documentation API : `http://localhost:8765/docs`
- Frontend : `http://localhost:5173`

## Amélioration du script de démarrage

Le script `demarrer_autocut.sh` a été amélioré avec :

1. **Vérification intelligente des dépendances**
   - Ne télécharge que si nécessaire
   - Vérifie fastapi, uvicorn, sqlalchemy

2. **Vérification de santé du backend**
   - Attend que le backend démarre
   - Teste l'endpoint `/health`
   - Affiche une erreur claire si le démarrage échoue

3. **Messages informatifs**
   - Indique quand les dépendances sont déjà installées
   - Affiche la progression du démarrage
   - Donne des instructions en cas d'erreur

## Troubleshooting

### Le backend ne démarre pas

1. Vérifiez que le port 8765 n'est pas déjà utilisé :
   ```bash
   lsof -i :8765
   ```

2. Vérifiez les logs du backend dans la fenêtre de terminal

3. Testez manuellement :
   ```bash
   cd /chemin/vers/AutoCut
   source backend/venv/bin/activate
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
   ```

### Les dépendances ne s'installent pas

Si l'installation échoue :
```bash
# Supprimer l'ancien venv
rm -rf backend/venv

# Recréer et réinstaller
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

### FFmpeg manquant

FFmpeg n'est **pas nécessaire** pour démarrer le backend, seulement pour le traitement vidéo.

Pour installer FFmpeg :
- **macOS** : `brew install ffmpeg`
- **Linux** : `apt-get install ffmpeg` ou `yum install ffmpeg`
- **Windows** : Télécharger depuis https://ffmpeg.org/
