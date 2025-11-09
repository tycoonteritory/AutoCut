# Configuration de l'IA Locale pour AutoCut

## 📋 Vue d'ensemble

AutoCut a été simplifié et utilise maintenant une IA locale pour générer des titres YouTube optimisés. Cette version ne nécessite plus OpenAI API et fonctionne entièrement en local.

## ✨ Nouvelles fonctionnalités

- ✅ **Mode local uniquement** : Plus besoin de choisir entre local et IA
- ✅ **Détection améliorée des "euh"** : Patterns plus robustes et complets
- ✅ **Copier-coller du texte** : Bouton pour copier directement la transcription
- ✅ **Génération de 3 titres YouTube** : IA locale pour A/B testing
- ❌ **Supprimé** : Création de shorts, sous-titres, post-traitement OpenAI

## 🚀 Installation de l'IA Locale (Ollama)

### Option 1 : Avec Ollama (Recommandé)

Pour bénéficier de la génération de titres intelligente :

1. **Installer Ollama** :
   ```bash
   # Linux
   curl -fsSL https://ollama.com/install.sh | sh

   # macOS
   brew install ollama

   # Ou télécharger depuis https://ollama.com/download
   ```

2. **Démarrer Ollama** :
   ```bash
   ollama serve
   ```

3. **Télécharger un modèle** (recommandé : llama2 ou mistral) :
   ```bash
   # Modèle recommandé pour la génération de titres
   ollama pull llama2

   # Alternative plus performante (requiert plus de RAM)
   ollama pull mistral
   ```

4. **Vérifier que ça fonctionne** :
   ```bash
   curl http://localhost:11434/api/tags
   ```

### Option 2 : Sans Ollama (Mode Fallback)

Si vous ne souhaitez pas installer Ollama, AutoCut fonctionnera quand même avec un système de génération de titres simple basé sur des règles.

## 📝 Utilisation

### 1. Traiter une vidéo

1. Uploadez votre vidéo (MP4 ou MOV)
2. Ajustez les paramètres de détection des silences et des "euh"
3. Activez la détection des hésitations (activée par défaut)
4. Lancez le traitement

### 2. Copier la transcription

Une fois le traitement terminé, cliquez sur le bouton **"📋 Copier le texte"** pour copier la transcription complète dans votre presse-papier.

### 3. Générer des titres YouTube

1. Après le traitement, cliquez sur **"✨ Générer 3 Titres Optimisés"**
2. L'IA locale générera 3 titres différents :
   - **Titre 1** : Émotionnel et accrocheur
   - **Titre 2** : Informatif et direct
   - **Titre 3** : Intrigant avec question
3. Copiez le titre de votre choix avec le bouton **"📋 Copier"**

## ⚙️ Configuration Ollama (Optionnel)

### Changer le modèle par défaut

Éditez `/home/user/AutoCut/backend/services/ai_services/local_title_generator.py` :

```python
# Ligne 14 - Changer le modèle
def __init__(
    self,
    ollama_url: str = "http://localhost:11434",
    model: str = "mistral"  # Changez ici : llama2, mistral, etc.
):
```

### Modèles recommandés pour la génération de titres

| Modèle | Taille | Qualité | RAM requise |
|--------|--------|---------|-------------|
| `llama2` | 3.8GB | Bonne | 8GB |
| `mistral` | 4.1GB | Excellente | 8GB |
| `llama2:13b` | 7.4GB | Très bonne | 16GB |
| `mixtral` | 26GB | Excellente | 32GB |

## 🔧 Dépannage

### Ollama n'est pas détecté

```bash
# Vérifiez que Ollama est en cours d'exécution
ps aux | grep ollama

# Redémarrez Ollama
killall ollama
ollama serve
```

### Génération de titres lente

- Utilisez un modèle plus petit (llama2 au lieu de mixtral)
- Vérifiez que vous avez assez de RAM
- Fermez les autres applications gourmandes en ressources

### Les titres sont en anglais

Modifiez le prompt dans `local_title_generator.py` pour forcer le français :

```python
# Ligne 130 environ
prompt = f"""Tu es un expert en optimisation de titres YouTube FRANÇAIS.
IMPORTANT : Réponds UNIQUEMENT en français.
...
```

## 📊 Amélioration de la Détection des "Euh"

La nouvelle version détecte maintenant :
- ✅ Variations de "euh" : euh, heu, euuh, heuuh, etc.
- ✅ "Ah" et "Oh" d'hésitation
- ✅ "Hum", "hmm", "mmmh"
- ✅ Fillers français : "ben", "bah", "bof", "en fait", "du coup", "genre"
- ✅ Répétitions : "je je", "le le"
- ✅ Sons de respiration détectés par Whisper

## 📈 Comparaison Avant/Après

### Avant
- 2441 lignes de code frontend
- Choix complexe local/GPT-4
- Multiples fonctionnalités (shorts, sous-titres, etc.)
- Dépendance à OpenAI API ($$$)

### Après
- 1288 lignes de code frontend (-47%)
- Mode local uniquement
- Focus sur l'essentiel : silences + hésitations
- IA locale gratuite avec Ollama

## 🎯 Workflow Optimisé

1. **Upload** → Vidéo MP4/MOV
2. **Traitement** → Détection silences + "euh" améliorée
3. **Copie** → Bouton copier la transcription
4. **Titres** → Génération 3 titres optimisés (A/B testing)
5. **Export** → Vidéo + XML (Premiere/Final Cut)

## 🆘 Support

Pour toute question ou problème :
1. Vérifiez que Ollama est bien installé et en cours d'exécution
2. Consultez les logs du backend : `/home/user/AutoCut/backend/logs/`
3. Mode fallback activé automatiquement si Ollama n'est pas disponible

## 🔄 Prochaines améliorations possibles

- [ ] Support de plus de modèles locaux (GPT4All, LlamaCpp, etc.)
- [ ] Génération de descriptions YouTube
- [ ] Génération de hashtags optimisés
- [ ] Export direct vers YouTube API
