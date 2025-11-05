# 🎬 AutoCut - Automatic Silence Detection & Video Cutting

AutoCut est une application web locale qui détecte automatiquement les silences dans vos vidéos et génère des fichiers de montage compatibles avec **Adobe Premiere Pro** et **Final Cut Pro X**.

![AutoCut](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![Node](https://img.shields.io/badge/node-18+-green.svg)

## ✨ Fonctionnalités

- 🎯 **Détection automatique des silences** dans vos vidéos MP4/MOV
- ✂️ **Coupes intelligentes** basées sur l'analyse audio
- 📤 **Export XML** compatible Premiere Pro et Final Cut Pro X
- 📊 **Progression en temps réel** via WebSocket
- 💪 **Gestion de fichiers volumineux** (>1h de vidéo)
- 🎨 **Interface web moderne** et intuitive
- ⚙️ **Paramètres ajustables** (seuil, durée minimale, padding)
- 🏗️ **Architecture atomique** pour faciliter l'évolution

## 🚀 Installation Rapide

### Prérequis

1. **Python 3.8+** : [Télécharger Python](https://www.python.org/)
2. **Node.js 18+** : [Télécharger Node.js](https://nodejs.org/)
3. **FFmpeg** : [Télécharger FFmpeg](https://ffmpeg.org/)

#### Installation FFmpeg

**Windows** (avec Chocolatey) :
```bash
choco install ffmpeg
```

**macOS** (avec Homebrew) :
```bash
brew install ffmpeg
```

**Linux** (Ubuntu/Debian) :
```bash
sudo apt update
sudo apt install ffmpeg
```

### Démarrage

#### 🪟 Windows

1. Double-cliquez sur `scripts/start_windows.bat`
2. L'application s'ouvrira automatiquement dans votre navigateur

#### 🍎 macOS / Linux

1. Ouvrez un terminal dans le dossier AutoCut
2. Exécutez :
```bash
./scripts/start_mac.sh
```
3. L'application s'ouvrira automatiquement dans votre navigateur

### Arrêt

#### Windows
Fermez les fenêtres "AutoCut Backend" et "AutoCut Frontend"

#### macOS / Linux
Appuyez sur `Ctrl+C` dans le terminal, ou exécutez :
```bash
./scripts/stop_mac.sh
```

## 📖 Guide d'utilisation

### 1. Télécharger une vidéo

- Glissez-déposez votre fichier MP4/MOV dans la zone de téléchargement
- Ou cliquez pour parcourir vos fichiers

### 2. Ajuster les paramètres (optionnel)

- **Seuil de silence (dB)** : -40 par défaut (plus bas = plus sensible)
- **Durée minimale du silence (ms)** : 500 par défaut
- **Padding (ms)** : 100 par défaut (marge avant/après les coupes)
- **FPS** : 30 par défaut (frames par seconde)

### 3. Lancer le traitement

- Cliquez sur "🚀 Process Video"
- Suivez la progression en temps réel
- Les fichiers volumineux peuvent prendre plusieurs minutes

### 4. Télécharger les exports

Une fois terminé, téléchargez :
- **Premiere Pro XML** : Pour Adobe Premiere Pro
- **Final Cut Pro XML** : Pour Final Cut Pro X

### 5. Importer dans votre éditeur

#### Premiere Pro
1. Fichier → Importer
2. Sélectionnez le fichier `.xml`
3. Votre séquence avec les coupes apparaît

#### Final Cut Pro X
1. Fichier → Importer → XML
2. Sélectionnez le fichier `.fcpxml`
3. Votre projet avec les coupes apparaît

## 🏗️ Architecture

Le projet utilise une **architecture atomique et modulaire** :

```
AutoCut/
├── backend/                    # API Python FastAPI
│   ├── api/                   # Routes et WebSocket
│   ├── services/              # Services métier (atomiques)
│   │   ├── silence_detection/ # Détection des silences
│   │   ├── video_processing/  # Traitement vidéo
│   │   └── export_formats/    # Export XML
│   └── config/                # Configuration
│
├── frontend/                   # Interface React
│   └── src/
│       ├── components/        # Composants UI
│       └── App.jsx            # Application principale
│
├── scripts/                    # Scripts de lancement
│   ├── start_windows.bat      # Lanceur Windows
│   └── start_mac.sh           # Lanceur macOS/Linux
│
├── uploads/                    # Vidéos téléchargées
├── output/                     # Fichiers XML générés
└── temp/                       # Fichiers temporaires
```

### Modules atomiques

Chaque module est **indépendant** et peut être modifié/étendu facilement :

- **silence_detection/detector.py** : Analyse audio et détection des silences
- **export_formats/premiere_pro.py** : Export Premiere Pro
- **export_formats/final_cut_pro.py** : Export Final Cut Pro
- **video_processing/processor.py** : Orchestration du workflow

## 🔧 Configuration avancée

### Ports utilisés

- **Backend API** : 8765
- **Frontend** : 5173
- **WebSocket** : 8765 (même port que l'API)

Pour modifier les ports, éditez `backend/config/settings.py` :

```python
API_PORT = 8765  # Port de l'API
```

Et `frontend/vite.config.js` :

```javascript
server: {
  port: 5173  // Port du frontend
}
```

### Paramètres de détection

Dans `backend/config/settings.py` :

```python
SILENCE_THRESHOLD_DB = -40      # Seuil en dB
MIN_SILENCE_DURATION_MS = 500   # Durée minimale en ms
PADDING_MS = 100                # Padding en ms
```

## 📊 API Endpoints

### POST `/api/upload`
Télécharge et traite une vidéo

**Paramètres :**
- `file` : Fichier vidéo (MP4/MOV)
- `silence_threshold` : Seuil de silence (dB)
- `min_silence_duration` : Durée minimale (ms)
- `padding` : Padding (ms)
- `fps` : Frames par seconde

**Réponse :**
```json
{
  "job_id": "uuid",
  "filename": "video.mp4",
  "status": "processing"
}
```

### GET `/api/job/{job_id}`
Récupère le statut d'un traitement

### GET `/api/download/{job_id}/{format}`
Télécharge un fichier XML exporté

**Formats :** `premiere_pro` ou `final_cut_pro`

### WebSocket `/api/ws/{job_id}`
Reçoit les mises à jour de progression en temps réel

**Messages :**
```json
{
  "type": "progress",
  "progress": 50,
  "message": "Analyzing video..."
}
```

## 🛠️ Développement

### Installation manuelle

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --port 8765
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm test
```

### Ajout de nouveaux formats d'export

1. Créez un nouveau fichier dans `backend/services/export_formats/`
2. Implémentez la classe d'export avec une méthode `generate_xml()`
3. Ajoutez-le dans `exporter.py`

Exemple :
```python
# backend/services/export_formats/davinci_resolve.py
class DaVinciResolveExporter:
    def generate_xml(self, cuts, output_path, duration):
        # Implémentation
        pass
```

## 🔮 Roadmap - Phase 2

- [ ] 📝 **Transcription automatique** des vidéos
- [ ] 🎯 **Optimisation YouTube**
  - Suggestions de titres courts
  - Génération de miniatures
  - Transcription prête à copier-coller
- [ ] 🎨 **Détection de scènes** (en plus des silences)
- [ ] 🔊 **Analyse audio avancée** (parole, musique, bruit)
- [ ] 📊 **Statistiques détaillées** (temps gagné, etc.)
- [ ] 💾 **Historique des projets**
- [ ] 🌐 **Support multilingue**

## ❓ FAQ

**Q: Quelle est la taille maximale de vidéo supportée ?**
A: 10GB par défaut. Modifiable dans `settings.py`.

**Q: Le traitement est-il fait localement ?**
A: Oui, 100% local. Rien n'est envoyé sur Internet.

**Q: Puis-je modifier les paramètres de détection ?**
A: Oui, dans l'interface ou dans `settings.py`.

**Q: Pourquoi mes coupes ne sont pas précises ?**
A: Ajustez le seuil de silence (plus bas = plus sensible) et la durée minimale.

**Q: Le fichier XML ne s'importe pas dans Premiere/FCPX ?**
A: Vérifiez que le chemin de la vidéo source est accessible depuis l'éditeur.

## 🐛 Problèmes courants

### "FFmpeg not found"
Installez FFmpeg et ajoutez-le au PATH système.

### "Port already in use"
Un autre service utilise les ports 8765 ou 5173. Modifiez les ports dans la configuration.

### "WebSocket connection failed"
Vérifiez que le backend est bien démarré sur le port 8765.

### Vidéo trop longue / Timeout
Pour les vidéos >2h, augmentez les timeouts dans `routes.py`.

## 📄 Licence

MIT License - Libre d'utilisation et de modification

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation
- Vérifiez les logs dans `backend.log` et `frontend.log`

---

Fait avec ❤️ pour les créateurs de contenu vidéo
