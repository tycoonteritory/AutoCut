# Sous-titres Animés pour Vidéos Shorts

## Fonctionnalité

Cette fonctionnalité permet d'ajouter automatiquement des **sous-titres animés synchronisés** aux clips vidéo au format 9:16 (shorts), optimisés pour les réseaux sociaux (TikTok, Instagram Reels, YouTube Shorts).

## Caractéristiques

### ✨ Synchronisation Audio
- Utilise la transcription Whisper pour une synchronisation parfaite avec l'audio
- Timestamps précis pour chaque segment de texte
- Support de la langue française par défaut

### 🎨 Styles Optimisés Réseaux Sociaux

**4 styles disponibles :**

1. **default** - Style universel
   - Police : Arial Bold, 22pt
   - Couleur : Blanc avec contour noir
   - Position : Bas de l'écran
   - Idéal pour tous types de contenu

2. **tiktok** - Optimisé pour TikTok
   - Police : Arial Bold, 24pt
   - Couleur : Blanc avec contour noir épais
   - Position : Haut de l'écran (style TikTok)
   - Emphase sur les mots clés en jaune

3. **instagram** - Optimisé pour Instagram Reels
   - Police : Arial Bold, 22pt
   - Couleur : Blanc avec fond transparent
   - Position : Bas de l'écran
   - Accents en magenta (couleur Instagram)

4. **youtube** - Optimisé pour YouTube Shorts
   - Police : Arial Bold, 20pt
   - Couleur : Blanc avec contour noir
   - Position : Bas de l'écran
   - Accents en rouge (couleur YouTube)

### 📱 Optimisation Mobile

- **Césures intelligentes** : max 2 lignes, ~35 caractères par ligne
- **Lisibilité maximale** : contour épais + fond semi-transparent
- **Animations fluides** : fade in/out de 200ms
- **Taille adaptée** : grande police visible sur petit écran

### 🎯 Emphase Automatique

Le système détecte et met en valeur les mots clés importants :
- Émotions fortes (incroyable, génial, wow, etc.)
- Termes importants (crucial, essentiel, clé, etc.)
- Alertes (attention, danger, warning, etc.)

Ces mots sont automatiquement surlignés en jaune vif.

## Utilisation API

### Endpoint

```
POST /api/phase2/generate-clips/{job_id}
```

### Paramètres

| Paramètre | Type | Valeurs | Défaut | Description |
|-----------|------|---------|--------|-------------|
| `num_clips` | int | 1-10 | 3 | Nombre de clips à générer |
| `clip_format` | str | horizontal, vertical | horizontal | Format de la vidéo |
| `use_ai` | bool | true, false | false | Utiliser GPT-4 pour la détection |
| `add_subtitles` | bool | true, false | false | **Activer les sous-titres animés** |
| `subtitle_style` | str | default, tiktok, instagram, youtube | default | Style de sous-titres |
| `subtitle_position` | str | top, center, bottom | bottom | Position des sous-titres |

### Prérequis

⚠️ **IMPORTANT** : Pour utiliser les sous-titres, la vidéo doit avoir été **transcrite avec Whisper** au préalable.

### Exemples d'Appels

#### 1. Clips verticaux avec sous-titres style TikTok

```bash
curl -X POST "http://localhost:8000/api/phase2/generate-clips/{job_id}?num_clips=5&clip_format=vertical&add_subtitles=true&subtitle_style=tiktok&subtitle_position=top"
```

#### 2. Clips Instagram Reels avec sous-titres

```bash
curl -X POST "http://localhost:8000/api/phase2/generate-clips/{job_id}?num_clips=3&clip_format=vertical&add_subtitles=true&subtitle_style=instagram&subtitle_position=bottom"
```

#### 3. YouTube Shorts avec sous-titres

```bash
curl -X POST "http://localhost:8000/api/phase2/generate-clips/{job_id}?num_clips=5&clip_format=vertical&add_subtitles=true&subtitle_style=youtube&subtitle_position=bottom"
```

#### 4. Style personnalisé par défaut

```bash
curl -X POST "http://localhost:8000/api/phase2/generate-clips/{job_id}?num_clips=3&clip_format=vertical&add_subtitles=true"
```

## Workflow Complet

### 1. Upload et Traitement Initial (Phase 1)

```bash
# Upload de la vidéo
POST /api/upload

# Traitement (silence removal, etc.)
POST /api/process/{job_id}
```

### 2. Transcription (Phase 2)

```bash
# Transcription Whisper (OBLIGATOIRE pour les sous-titres)
POST /api/phase2/transcribe/{job_id}
```

### 3. Génération de Clips avec Sous-titres

```bash
# Générer clips avec sous-titres
POST /api/phase2/generate-clips/{job_id}?clip_format=vertical&add_subtitles=true&subtitle_style=tiktok
```

### 4. Récupération des Résultats

```bash
# Obtenir les URLs des clips générés
GET /api/phase2/clips/{job_id}

# Télécharger un clip spécifique
GET /api/phase2/download-clip/{job_id}/{clip_index}
```

## Architecture Technique

### Fichiers Clés

```
backend/services/short_clips/
├── subtitle_renderer.py      # Service de rendu de sous-titres ASS
├── clip_extractor.py          # Extraction de clips (avec support sous-titres)
└── README_SUBTITLES.md        # Cette documentation

backend/api/
└── routes_phase2.py           # API endpoints avec paramètres sous-titres
```

### Format ASS (Advanced SubStation Alpha)

Les sous-titres sont générés au format ASS qui permet :
- **Styles avancés** : polices, couleurs, contours, ombres
- **Animations** : fade in/out, transitions
- **Positionnement précis** : pixel-perfect sur vidéo 1080x1920
- **Effets visuels** : emphase, surlignage, tags personnalisés

### Pipeline de Rendu

```
Transcription Whisper
    ↓
Segments avec timestamps
    ↓
Optimisation (césures, emphase)
    ↓
Génération fichier ASS
    ↓
FFmpeg burn subtitles (filtre ass)
    ↓
Vidéo finale avec sous-titres intégrés
```

### Commande FFmpeg Utilisée

```bash
ffmpeg -y -i input.mp4 \
  -vf "ass=subtitles.ass" \
  -c:v libx264 -preset fast -crf 23 \
  -c:a copy \
  output.mp4
```

## Performances

### Temps de Traitement

Pour un clip de 45 secondes :
- **Sans sous-titres** : ~5-10 secondes
- **Avec sous-titres** : ~10-20 secondes
- Overhead : ~5-10 secondes pour le burn des sous-titres

### Qualité Vidéo

- Codec : H.264 (libx264)
- CRF : 23 (qualité élevée)
- Preset : fast (bon compromis)
- Audio : copie sans ré-encodage

## Limitations et Bonnes Pratiques

### Limitations

1. **Transcription obligatoire** : Les sous-titres nécessitent une transcription Whisper
2. **Langue** : Optimisé pour le français (configurable dans settings.py)
3. **Durée** : Recommandé pour clips de 15-90 secondes
4. **Format** : Optimisé pour vertical 9:16 (1080x1920)

### Bonnes Pratiques

1. **Toujours transcrire avant** de générer des clips avec sous-titres
2. **Choisir le bon style** selon le réseau social ciblé
3. **Position** :
   - TikTok → top
   - Instagram/YouTube → bottom
4. **Vérifier la qualité audio** : meilleure transcription = meilleurs sous-titres
5. **Tester plusieurs styles** pour trouver le plus adapté à votre contenu

## Dépannage

### Erreur "Subtitles require video transcription first"

**Solution** : Lancer la transcription Whisper avant :
```bash
POST /api/phase2/transcribe/{job_id}
```

### Sous-titres mal synchronisés

**Causes possibles** :
1. Audio de mauvaise qualité → Utiliser audio enhancement
2. Langue incorrecte dans settings.py
3. Timestamps de segments incorrects

**Solution** : Vérifier la qualité de la transcription en téléchargeant le fichier SRT

### Sous-titres illisibles

**Solutions** :
1. Changer la position (top/bottom)
2. Essayer un autre style (tiktok a le contour le plus épais)
3. Vérifier que la vidéo source est bien en 1080x1920

## Exemple de Résultat

### Structure du Fichier ASS Généré

```ass
[Script Info]
Title: AutoCut Animated Subtitles
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Style: Default,Arial,22,&H00FFFFFF,&H00FFFF00,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3,2,2,50,50,80,1

[Events]
Dialogue: 0,0:00:00.00,0:00:03.50,Default,,0,0,0,,{\fad(200,200)}Bonjour à tous !
Dialogue: 0,0:00:03.50,0:00:07.20,Default,,0,0,0,,{\fad(200,200)}Aujourd'hui je vais vous montrer\Nune astuce {\c&H00FFFF&}incroyable{\r}
```

## Évolutions Futures

- [ ] Support de plus de langues
- [ ] Détection automatique du meilleur style selon le contenu
- [ ] Animations plus complexes (bounce, slide, etc.)
- [ ] Support de polices custom
- [ ] Karaoke style (mot par mot)
- [ ] Emojis dans les sous-titres

## Support

Pour toute question ou problème, consulter :
- Les logs du backend : `/backend/logs/`
- La documentation API : `http://localhost:8000/docs`
- Les fichiers générés : `/output/{video_name}/short_clips/`
