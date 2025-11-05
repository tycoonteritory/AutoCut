# 🔮 AutoCut - Phase 2 Roadmap

## Vue d'ensemble

La Phase 2 d'AutoCut ajoute des fonctionnalités d'intelligence artificielle pour l'optimisation YouTube et la transcription automatique.

## 🎯 Objectifs Phase 2

### 1. Transcription automatique
- Transcription complète de la vidéo
- Support multilingue
- Horodatage précis
- Export en formats SRT, VTT, TXT

### 2. Optimisation YouTube
Pour chaque vidéo traitée :
- **3 suggestions de titres courts** optimisés SEO
- **Suggestions de miniatures** (basées sur les meilleurs moments)
- **Transcription prête à copier-coller** pour la description
- **Tags recommandés** basés sur le contenu
- **Chapitres automatiques** avec horodatage

## 🏗️ Architecture proposée

```
backend/services/
├── transcription/           # Nouveau module
│   ├── transcriber.py      # Moteur de transcription (Whisper)
│   ├── formatter.py        # Formatage SRT/VTT
│   └── analyzer.py         # Analyse du contenu
│
├── youtube_optimization/    # Nouveau module
│   ├── title_generator.py  # Génération de titres
│   ├── thumbnail_suggester.py  # Suggestions de miniatures
│   ├── tag_generator.py    # Génération de tags
│   └── chapter_generator.py # Génération de chapitres
│
└── ai_services/            # Nouveau module
    ├── openai_client.py    # Client OpenAI (GPT-4)
    └── whisper_client.py   # Client Whisper
```

## 🔧 Technologies à ajouter

### Backend
- **OpenAI Whisper** : Transcription audio
- **OpenAI GPT-4** : Génération de titres/tags/descriptions
- **OpenCV** : Extraction de frames pour miniatures
- **spaCy** : Analyse de texte et extraction de mots-clés

### Frontend
- Nouvel onglet "Optimisation YouTube"
- Prévisualisation des miniatures suggérées
- Éditeur de transcription en temps réel
- Génération de chapitres interactifs

## 📦 Dépendances supplémentaires

```python
# backend/requirements_phase2.txt
openai==1.3.0
openai-whisper==20231117
opencv-python==4.8.1
pillow==10.1.0
spacy==3.7.2
youtube-transcript-api==0.6.1
```

## 🚀 Plan d'implémentation

### Étape 1 : Transcription
1. Intégrer Whisper pour la transcription
2. Créer le module `transcription/transcriber.py`
3. Ajouter endpoints API :
   - `POST /api/transcribe/{job_id}` : Lancer la transcription
   - `GET /api/transcription/{job_id}` : Récupérer la transcription
4. Mettre à jour le frontend avec affichage de la transcription

### Étape 2 : Optimisation YouTube
1. Créer le module `youtube_optimization/`
2. Implémenter la génération de titres avec GPT-4
3. Extraire les frames clés pour les miniatures
4. Générer tags et descriptions
5. Créer des chapitres automatiques
6. Ajouter endpoints API :
   - `POST /api/optimize-youtube/{job_id}` : Optimiser pour YouTube
   - `GET /api/youtube-data/{job_id}` : Récupérer les données

### Étape 3 : Interface utilisateur
1. Créer `YouTubeOptimization.jsx` component
2. Afficher les 3 suggestions de titres
3. Galerie de miniatures suggérées
4. Zone de transcription éditable
5. Boutons de copie rapide

## 📊 Nouveaux endpoints API

### POST `/api/transcribe/{job_id}`
Lance la transcription d'une vidéo déjà traitée

**Paramètres :**
- `language` : Langue de la vidéo (auto-détection par défaut)
- `format` : Format de sortie (srt, vtt, txt)

**Réponse :**
```json
{
  "job_id": "uuid",
  "status": "transcribing",
  "estimated_time": "2 minutes"
}
```

### GET `/api/transcription/{job_id}`
Récupère la transcription

**Réponse :**
```json
{
  "transcription": "Texte complet...",
  "segments": [
    {"start": 0.0, "end": 2.5, "text": "Bonjour..."}
  ],
  "language": "fr",
  "confidence": 0.95
}
```

### POST `/api/optimize-youtube/{job_id}`
Génère les optimisations YouTube

**Réponse :**
```json
{
  "titles": [
    "Titre court et accrocheur 1",
    "Titre court et accrocheur 2",
    "Titre court et accrocheur 3"
  ],
  "thumbnail_suggestions": [
    {"frame_time": 45.2, "score": 0.95, "url": "/thumbnails/1.jpg"},
    {"frame_time": 123.5, "score": 0.89, "url": "/thumbnails/2.jpg"}
  ],
  "description": "Description optimisée SEO...",
  "tags": ["tag1", "tag2", "tag3"],
  "chapters": [
    {"time": "0:00", "title": "Introduction"},
    {"time": "1:23", "title": "Partie 1"}
  ]
}
```

## 🎨 Modifications UI

### Nouveau workflow
1. Upload vidéo → Détection silences (Phase 1)
2. Une fois terminé, afficher bouton "Optimiser pour YouTube"
3. Clic → Lance transcription + optimisation
4. Affiche résultats dans nouveaux onglets :
   - 📝 Transcription
   - 🎯 Optimisation YouTube

### Composants à créer

```jsx
// frontend/src/components/TranscriptionPanel.jsx
// Affiche la transcription avec horodatage

// frontend/src/components/YouTubeOptimization.jsx
// Affiche titres, miniatures, tags, chapitres

// frontend/src/components/TitleSuggestions.jsx
// Les 3 suggestions de titres avec bouton copier

// frontend/src/components/ThumbnailGallery.jsx
// Galerie de miniatures suggérées

// frontend/src/components/ChaptersList.jsx
// Liste des chapitres générés
```

## 💡 Algorithmes clés

### Génération de titres
```python
def generate_titles(transcription, video_metadata):
    """
    Utilise GPT-4 pour générer 3 titres courts
    - Analyse du contenu de la transcription
    - Extraction des points clés
    - Optimisation SEO
    - Longueur limitée (60 caractères max)
    """
    prompt = f"""
    Génère 3 titres YouTube accrocheurs et optimisés SEO pour cette vidéo.
    Transcription : {transcription[:500]}...

    Critères :
    - Maximum 60 caractères
    - Accrocheur et clair
    - Inclure mots-clés pertinents
    - Éviter clickbait excessif
    """
    # Appel GPT-4
```

### Suggestions de miniatures
```python
def suggest_thumbnails(video_path, transcription):
    """
    Extrait les frames les plus pertinentes
    - Détection de visages
    - Moments émotionnels forts
    - Éviter frames floues/sombres
    - Score de qualité pour chaque frame
    """
    # Analyse vidéo avec OpenCV
    # Extraction frames toutes les N secondes
    # Scoring basé sur :
    #   - Qualité image (netteté, luminosité)
    #   - Présence de visage
    #   - Moment important (basé sur transcription)
```

### Génération de chapitres
```python
def generate_chapters(transcription, timestamps):
    """
    Crée des chapitres automatiques
    - Détection des changements de sujet
    - Analyse sémantique
    - Génération de titres courts pour chaque chapitre
    """
    # Segmentation du texte
    # Analyse NLP pour détecter changements de thème
    # Génération de titres avec GPT-4
```

## 🔐 Configuration requise

### Clés API nécessaires
```bash
# .env
OPENAI_API_KEY=your_openai_key_here
```

### Modèles à télécharger
```python
# Whisper model (auto-téléchargé au premier usage)
whisper.load_model("base")  # Options: tiny, base, small, medium, large

# spaCy model
python -m spacy download fr_core_news_md  # Français
python -m spacy download en_core_web_md   # Anglais
```

## 📊 Estimation des temps de traitement

| Étape | Vidéo 10min | Vidéo 1h |
|-------|-------------|----------|
| Transcription | ~30s | ~3min |
| Analyse contenu | ~10s | ~30s |
| Génération titres | ~5s | ~5s |
| Extraction miniatures | ~20s | ~1min |
| **Total** | **~1min** | **~5min** |

## 🧪 Tests à implémenter

```python
# tests/test_transcription.py
def test_whisper_transcription()
def test_multiple_languages()
def test_subtitle_formatting()

# tests/test_youtube_optimization.py
def test_title_generation()
def test_thumbnail_extraction()
def test_chapter_generation()
```

## 📈 Métriques de succès Phase 2

- Précision transcription > 95%
- Pertinence des titres (feedback utilisateur)
- Qualité des miniatures (score > 0.8)
- Temps de traitement < 10% de la durée vidéo

## 🚧 Limitations connues

- API OpenAI requise (coût par utilisation)
- Whisper nécessite GPU pour performances optimales
- Langues supportées limitées à celles de Whisper
- Miniatures nécessitent analyse manuelle finale

## 🔄 Migration depuis Phase 1

La Phase 2 est **rétrocompatible** :
- Les fonctionnalités Phase 1 restent inchangées
- Nouveaux modules complètement séparés
- Activation optionnelle (peut être désactivée)
- Pas de breaking changes

## 🎯 Prochaines étapes

1. Validation du design avec l'utilisateur
2. Setup environnement Phase 2
3. Implémentation transcription (Étape 1)
4. Tests et validation
5. Implémentation optimisation YouTube (Étape 2)
6. Interface utilisateur
7. Tests d'intégration complets
8. Documentation utilisateur Phase 2

---

**Note :** Cette roadmap est un document évolutif. Les priorités et l'implémentation peuvent être ajustées selon les besoins.
