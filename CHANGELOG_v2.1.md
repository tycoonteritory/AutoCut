# Changelog v2.1.0 - Version Simplifiée

## 📅 Date : 2025-11-09

## 🎯 Objectif
Simplifier l'application en supprimant les fonctionnalités complexes et en se concentrant sur l'essentiel : la détection des silences et des hésitations, avec une IA locale pour optimiser les titres YouTube.

---

## ✨ Nouvelles Fonctionnalités

### 🤖 IA Locale pour Titres YouTube
- Génération de 3 titres optimisés pour A/B testing
- Support d'Ollama (llama2, mistral, etc.)
- Mode fallback automatique si Ollama n'est pas disponible
- Types de titres variés :
  - Émotionnel et accrocheur
  - Informatif et direct
  - Intrigant avec question

**Fichier ajouté** : `backend/services/ai_services/local_title_generator.py`
**Route ajoutée** : `POST /api/generate-titles/{job_id}`

### 📋 Copier-Coller de Transcription
- Bouton "Copier le texte" dans l'interface
- Copie directement la transcription complète dans le presse-papier
- Simplifie le workflow pour utiliser le texte ailleurs

### 🎯 Détection Améliorée des "Euh"

Patterns ajoutés/améliorés dans `backend/services/filler_words/detector.py` :

```python
# Nouveaux patterns
- "ah", "aah", "oh", "ooh" (hésitations)
- "en fait", "du coup", "genre", "tu vois" (fillers français)
- "c'est-à-dire", "enfin bon", "bon ben" (phrases d'hésitation)
- Répétitions plus strictes (évite faux positifs)
- Sons de respiration détectés par Whisper
- Variations phonétiques étendues
```

**Fichier modifié** : `backend/services/filler_words/detector.py`

---

## 🔥 Fonctionnalités Supprimées

### ❌ Choix entre Local et IA GPT-4
- **Avant** : Utilisateur choisit entre mode local ou GPT-4
- **Après** : Toujours en mode local (100% gratuit)
- **Impact** : Suppression de la dépendance OpenAI API

### ❌ Création de Shorts
- Suppression de la détection de moments viraux (GPT-4)
- Suppression de l'extraction de clips courts
- Suppression du système de sous-titres animés
- **Fichiers désactivés** :
  - `backend/services/short_clips/clip_detector.py`
  - `backend/services/short_clips/clip_extractor.py`
  - `backend/services/short_clips/subtitle_renderer.py`

### ❌ Post-Traitement (Optimisation YouTube OpenAI)
- Suppression de la génération de descriptions YouTube
- Suppression de la génération de tags
- Suppression de la génération de chapitres
- Suppression de l'extraction de miniatures
- **Fichiers désactivés** :
  - `backend/services/youtube_optimization/*`
  - `backend/services/ai_services/gpt4_analyzer.py`

### ❌ Routes Phase 2
- Routes de transcription standalone supprimées
- Routes d'optimisation YouTube supprimées
- Routes de génération de clips supprimées
- **Fichier désactivé** : `backend/api/routes_phase2.py`

---

## 📝 Modifications de Code

### Frontend (`frontend/src/App.jsx`)

**Avant** : 2441 lignes
**Après** : 1288 lignes
**Réduction** : -47% (-1153 lignes)

**Changements** :
- Suppression du choix de mode (local/GPT-4)
- Suppression de tout le code relatif aux shorts
- Suppression du post-traitement YouTube
- Ajout du bouton copier-coller
- Ajout de l'interface de génération de titres
- Simplification de l'interface utilisateur
- Styles CSS inline simplifiés

### Backend

#### `backend/main.py`
```python
# Phase 2 routes désactivées
# from .api.routes_phase2 import router as phase2_router
# app.include_router(phase2_router, prefix="/api")
```

#### `backend/api/routes.py`
- Ajout de la route `POST /api/generate-titles/{job_id}`
- Intégration du `LocalTitleGenerator`

#### `backend/services/filler_words/detector.py`
- 16 patterns de détection (avant : 7 patterns)
- Support de plus de variations de "euh"
- Ajout de fillers français courants
- Amélioration de la détection des répétitions

---

## 📚 Documentation

### Fichiers Ajoutés

1. **`SETUP_IA_LOCALE.md`**
   - Guide d'installation d'Ollama
   - Configuration des modèles
   - Dépannage
   - Comparaison avant/après

2. **`CHANGELOG_v2.1.md`** (ce fichier)
   - Résumé complet des changements
   - Liste des fichiers modifiés/ajoutés/supprimés

### Fichiers Modifiés

- **`README.md`**
  - Mise à jour version 2.1.0
  - Nouvelles fonctionnalités
  - Lien vers SETUP_IA_LOCALE.md

---

## 🗂️ Arborescence des Changements

```
AutoCut/
├── frontend/src/
│   └── App.jsx                                    [MODIFIÉ - Simplifié]
│
├── backend/
│   ├── main.py                                    [MODIFIÉ - Routes Phase 2 désactivées]
│   ├── api/
│   │   ├── routes.py                              [MODIFIÉ - Route generate-titles ajoutée]
│   │   └── routes_phase2.py                       [DÉSACTIVÉ]
│   │
│   └── services/
│       ├── ai_services/
│       │   ├── local_title_generator.py           [NOUVEAU]
│       │   ├── openai_client.py                   [DÉSACTIVÉ]
│       │   └── gpt4_analyzer.py                   [DÉSACTIVÉ]
│       │
│       ├── filler_words/
│       │   └── detector.py                        [MODIFIÉ - Patterns améliorés]
│       │
│       ├── short_clips/                           [DÉSACTIVÉ]
│       │   ├── clip_detector.py
│       │   ├── clip_extractor.py
│       │   ├── subtitle_renderer.py
│       │   └── local_clip_scorer.py
│       │
│       └── youtube_optimization/                  [DÉSACTIVÉ]
│           ├── youtube_optimizer.py
│           ├── title_generator.py
│           ├── tag_generator.py
│           ├── chapter_generator.py
│           └── thumbnail_extractor.py
│
├── SETUP_IA_LOCALE.md                             [NOUVEAU]
├── CHANGELOG_v2.1.md                              [NOUVEAU]
└── README.md                                      [MODIFIÉ]
```

---

## 🔧 Dépendances

### Nouvelles Dépendances (Optionnelles)
- **Ollama** (optionnel) : Pour la génération de titres avec IA locale
  - Installation : `curl -fsSL https://ollama.com/install.sh | sh`
  - Modèles recommandés : llama2, mistral

### Dépendances Supprimées
- **OpenAI API** : Plus nécessaire

---

## 🚀 Workflow Simplifié

### Avant (v2.0.0)
1. Upload vidéo
2. **Choix** : Mode local ou GPT-4
3. Traitement
4. **Phase 2** : Transcription
5. **Phase 2** : Optimisation YouTube (OpenAI)
6. **Phase 2** : Génération de shorts (GPT-4)
7. Export

### Après (v2.1.0)
1. Upload vidéo
2. Traitement (toujours local)
3. **Copier** la transcription
4. **Générer** 3 titres YouTube (IA locale)
5. Export

---

## 📊 Métriques

| Métrique | Avant (v2.0) | Après (v2.1) | Amélioration |
|----------|--------------|--------------|--------------|
| Lignes de code frontend | 2441 | 1288 | **-47%** |
| Nombre de routes API | ~15 | ~8 | **-47%** |
| Services actifs | 15 | 8 | **-47%** |
| Dépendances externes | OpenAI API | Ollama (optionnel) | **100% local** |
| Complexité UI | Élevée | Faible | **Simple** |

---

## 🎯 Bénéfices

### Pour l'Utilisateur
- ✅ Interface plus simple et intuitive
- ✅ Workflow plus rapide
- ✅ Pas de coûts API (OpenAI)
- ✅ 100% local et privé
- ✅ Copier-coller direct du texte
- ✅ Génération de titres pour A/B testing

### Pour le Développeur
- ✅ Code plus maintenable (-1153 lignes frontend)
- ✅ Moins de dépendances externes
- ✅ Architecture simplifiée
- ✅ Tests plus faciles
- ✅ Déploiement plus simple

---

## 🔜 Prochaines Étapes (Optionnel)

- [ ] Support de GPT4All comme alternative à Ollama
- [ ] Génération de descriptions YouTube
- [ ] Génération de hashtags optimisés
- [ ] Export direct vers YouTube API
- [ ] Support de plus de langues (anglais, espagnol, etc.)

---

## 📝 Notes de Migration

### Si vous aviez v2.0.0 :

1. **Clés API OpenAI** : Peuvent être supprimées du `.env`
2. **Historique** : L'historique existant continue de fonctionner
3. **Ollama** : Installation optionnelle, mode fallback disponible
4. **Fonctionnalités supprimées** :
   - Shorts : Plus accessibles dans l'UI
   - Optimisation YouTube OpenAI : Remplacée par IA locale
   - Choix local/GPT-4 : Toujours local maintenant

---

## 👥 Contributeurs

- Simplification et refactorisation : Claude (IA Assistant)
- Demande initiale : @tycoonteritory

---

## 📄 Licence

Même licence que le projet AutoCut principal.
