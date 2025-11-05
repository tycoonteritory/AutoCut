# 🚀 Phase 2 - Installation et Configuration

Phase 2 ajoute la **transcription automatique** et l'**optimisation YouTube** à AutoCut !

## ✅ Ce qui est inclus

### 📝 Transcription automatique
- Transcription audio avec **Whisper d'OpenAI**
- Support français
- Export SRT, VTT, TXT
- Horodatage précis

### 🎯 Optimisation YouTube complète
- **3 suggestions de titres** optimisés SEO (GPT-4)
- **5 suggestions de miniatures** (extraction des meilleurs frames)
- **Tags recommandés** (jusqu'à 10 tags)
- **Description optimisée** prête à copier-coller
- **Chapitres automatiques** avec horodatage

## 🔧 Installation

### 1. Installer les nouvelles dépendances

```bash
cd /Users/vincentmary/Documents/GitHub/AutoCut
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

Cela va installer :
- `openai` - Client OpenAI pour Whisper et GPT-4
- `openai-whisper` - Modèle Whisper
- `opencv-python` - Traitement d'images pour miniatures
- `Pillow` - Manipulation d'images
- `spacy` - Analyse de texte
- `pysrt` - Gestion des sous-titres

### 2. Télécharger le modèle spaCy (français)

```bash
python -m spacy download fr_core_news_sm
```

### 3. Configurer la clé OpenAI

Créez un fichier `.env` à la racine du projet :

```bash
cd /Users/vincentmary/Documents/GitHub/AutoCut
cp .env.example .env
nano .env  # ou utilisez TextEdit, VSCode, etc.
```

Ajoutez votre clé OpenAI dans le fichier `.env` :

```env
# OpenAI API Key (obligatoire pour Phase 2)
OPENAI_API_KEY=sk-votre-clé-openai-ici

# Phase 2 settings (optionnel)
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large
TRANSCRIPTION_LANGUAGE=fr
GPT_MODEL=gpt-4
```

**⚠️ Important** : Le fichier `.env` est dans le `.gitignore` et ne sera jamais committé sur Git.

### 4. Obtenir une clé OpenAI

Si vous n'avez pas encore de clé :

1. Allez sur https://platform.openai.com/
2. Créez un compte ou connectez-vous
3. Allez dans **API Keys** : https://platform.openai.com/api-keys
4. Cliquez sur **Create new secret key**
5. Copiez la clé (elle commence par `sk-`)
6. Collez-la dans votre fichier `.env`

## 💰 Coûts estimés

### Par vidéo d'1 heure

- **Transcription Whisper** : ~0.36$ (0.006$ par minute)
- **Génération titres (GPT-4)** : ~0.03$
- **Génération tags** : ~0.02$
- **Génération description** : ~0.03$
- **Génération chapitres** : ~0.05$ (dépend du nombre)

**Total** : ~0.40-0.50$ par vidéo d'1h

### Modèles Whisper disponibles

| Modèle | Taille | Vitesse | Précision | Recommandé pour |
|--------|--------|---------|-----------|-----------------|
| `tiny` | 39 MB | Très rapide | Correcte | Tests rapides |
| `base` | 74 MB | Rapide | Bonne | **Défaut (recommandé)** |
| `small` | 244 MB | Moyen | Très bonne | Meilleure qualité |
| `medium` | 769 MB | Lent | Excellente | Production |
| `large` | 1550 MB | Très lent | Meilleure | Qualité maximale |

**Note** : Le modèle `base` est un bon équilibre qualité/vitesse.

## 🚀 Utilisation

### Workflow complet

1. **Phase 1** : Upload vidéo → Détection silences → Export XML
2. **Phase 2a** : Transcription → Fichiers SRT/VTT/TXT
3. **Phase 2b** : Optimisation YouTube → Titres, miniatures, tags, etc.

### Via l'interface web

1. Lancez l'application normalement
2. Uploadez et traitez votre vidéo (Phase 1)
3. Une fois terminé, cliquez sur **"Transcrire"**
4. Attendez la transcription (peut prendre 2-5 min pour 1h de vidéo)
5. Cliquez sur **"Optimiser pour YouTube"**
6. Récupérez vos titres, miniatures, tags, description, chapitres !

### Via l'API

#### Transcription

```bash
curl -X POST http://localhost:8765/api/transcribe/{job_id}
```

#### Optimisation YouTube

```bash
curl -X POST http://localhost:8765/api/optimize-youtube/{job_id}
```

#### Télécharger transcription

```bash
# Format SRT
curl http://localhost:8765/api/download-transcription/{job_id}/srt -o subtitles.srt

# Format VTT
curl http://localhost:8765/api/download-transcription/{job_id}/vtt -o subtitles.vtt

# Format TXT
curl http://localhost:8765/api/download-transcription/{job_id}/txt -o transcription.txt
```

## 📂 Structure des fichiers générés

```
output/
└── nom-de-votre-video/
    ├── nom-de-votre-video_premiere_pro.xml
    ├── nom-de-votre-video_final_cut_pro.fcpxml
    ├── nom-de-votre-video_subtitles.srt
    ├── nom-de-votre-video_subtitles.vtt
    ├── nom-de-votre-video_transcription.txt
    └── thumbnails/
        ├── thumbnail_1.jpg
        ├── thumbnail_2.jpg
        ├── thumbnail_3.jpg
        ├── thumbnail_4.jpg
        └── thumbnail_5.jpg
```

## 🐛 Dépannage

### "OPENAI_API_KEY not set"

Vous verrez ce warning au démarrage si la clé n'est pas configurée :
```
⚠️  WARNING: OPENAI_API_KEY not set. Phase 2 features will not work.
```

**Solution** : Créez le fichier `.env` avec votre clé OpenAI (voir étape 3).

### "No module named 'whisper'"

Les dépendances Phase 2 ne sont pas installées.

**Solution** :
```bash
cd /Users/vincentmary/Documents/GitHub/AutoCut
source backend/venv/bin/activate
pip install -r backend/requirements.txt
```

### Transcription très lente

Le modèle Whisper `base` est assez lent sur CPU. Pour accélérer :

**Option 1** : Utiliser le modèle `tiny` (moins précis mais plus rapide)
```env
WHISPER_MODEL=tiny
```

**Option 2** : Utiliser un Mac avec Apple Silicon (M1/M2/M3)
Whisper utilise automatiquement le GPU Apple Silicon.

### Erreur "Rate limit exceeded" (OpenAI)

Vous avez dépassé votre quota OpenAI.

**Solutions** :
- Attendez quelques minutes
- Vérifiez votre quota sur https://platform.openai.com/account/usage
- Ajoutez des crédits sur votre compte OpenAI

### Miniatures de mauvaise qualité

Le score de qualité peut être faible si la vidéo est sombre ou floue.

**Solution** : Les 5 meilleures miniatures sont sélectionnées automatiquement, choisissez celle qui vous convient le mieux.

## ⚙️ Configuration avancée

### Changer le modèle Whisper

Dans `.env` :
```env
WHISPER_MODEL=small  # Meilleure qualité, plus lent
```

### Changer le modèle GPT

Pour économiser, vous pouvez utiliser GPT-3.5 au lieu de GPT-4 :
```env
GPT_MODEL=gpt-3.5-turbo
```

**Note** : GPT-3.5 est moins cher (~10x) mais génère des titres/descriptions moins optimisés.

### Ajuster le nombre de suggestions

Dans `backend/config/settings.py` :
```python
NUM_TITLE_SUGGESTIONS = 5  # Au lieu de 3
NUM_THUMBNAIL_SUGGESTIONS = 10  # Au lieu de 5
MAX_TAGS = 15  # Au lieu de 10
```

## 📊 Temps de traitement estimés

Pour une vidéo d'**1 heure** :

| Étape | Temps (modèle base) | Temps (modèle tiny) |
|-------|---------------------|---------------------|
| Phase 1 (silences) | ~30 secondes | ~30 secondes |
| Transcription | ~3-5 minutes | ~1-2 minutes |
| Optimisation YouTube | ~30-60 secondes | ~30-60 secondes |
| **Total** | **~5-7 minutes** | **~2-3 minutes** |

## 🎉 C'est prêt !

Relancez AutoCut et testez la Phase 2 :

```bash
cd /Users/vincentmary/Documents/GitHub/AutoCut
./scripts/start_mac.sh
```

Uploadez une vidéo, traitez-la, puis cliquez sur **"Transcrire"** et **"Optimiser pour YouTube"** !

Profitez de toutes les nouvelles fonctionnalités ! 🚀
