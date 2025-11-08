# Fix: Upload Failed - Internal Server Error

## Diagnostic

L'erreur "Upload failed: Internal Server Error" se produit parce que le serveur backend n'est pas en cours d'exécution.

## Solution

### 1. Installer les dépendances

L'environnement virtuel Python doit être créé et les dépendances installées :

```bash
# Créer l'environnement virtuel
python3 -m venv backend/venv

# Activer l'environnement virtuel
source backend/venv/bin/activate

# Installer les dépendances
pip install --upgrade pip setuptools wheel
pip install -r backend/requirements.txt
```

### 2. Démarrer le serveur backend

Une fois les dépendances installées, démarrez le serveur backend :

```bash
# Activer l'environnement virtuel
source backend/venv/bin/activate

# Démarrer le serveur sur le port 8765
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```

### 3. Démarrer le frontend (dans un autre terminal)

```bash
cd frontend
npm install
npm run dev
```

## Vérification

Une fois les serveurs démarrés :

1. Backend devrait être accessible sur : `http://localhost:8765/health`
2. Frontend devrait être accessible sur : `http://localhost:5173`

Test curl :
```bash
curl http://localhost:8765/health
```

Réponse attendue :
```json
{"status":"healthy","service":"AutoCut","version":"1.0.0"}
```

## Script de démarrage rapide (sans FFmpeg)

Si vous n'avez pas FFmpeg installé mais voulez juste tester l'API :

```bash
#!/bin/bash
# start_backend_only.sh

# Activer le venv
source backend/venv/bin/activate

# Démarrer le serveur
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8765 --reload
```

Note : FFmpeg n'est nécessaire que pour le traitement vidéo réel, pas pour démarrer le serveur API.
