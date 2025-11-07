# 🔄 Mise à Jour AutoCut

Ce guide explique comment mettre à jour AutoCut vers la dernière version.

---

## 📥 Récupérer les Dernières Modifications

```bash
cd /chemin/vers/AutoCut

# Récupérer les derniers changements
git pull origin main
```

---

## 🍎 Sur Mac

### Solution Rapide (Recommandé)

```bash
# 1. Supprimer l'ancien environnement virtuel
rm -rf backend/venv

# 2. Double-cliquer sur "Start AutoCut.command"
# OU exécuter dans le terminal :
./Start\ AutoCut.command
```

Le script va automatiquement :
- ✅ Créer un nouveau venv
- ✅ Installer toutes les dépendances
- ✅ Démarrer l'application

### Si Ça Ne Marche Pas

```bash
# Vérifier que le script est exécutable
chmod +x Start\ AutoCut.command

# Puis relancer
./Start\ AutoCut.command
```

---

## 🪟 Sur Windows

### Solution Rapide (Recommandé)

1. Supprimer le dossier `backend\venv` (clic droit → Supprimer)
2. Double-cliquer sur `Start AutoCut.bat`

Le script va automatiquement :
- ✅ Créer un nouveau venv
- ✅ Installer toutes les dépendances
- ✅ Démarrer l'application

---

## 🐧 Sur Linux

```bash
# 1. Supprimer l'ancien venv
rm -rf backend/venv

# 2. Lancer le script
./start.sh
```

---

## 📦 Nouvelles Dépendances (v2.0.0)

Les dépendances suivantes ont été ajoutées :

**Pour la détection d'hésitations :**
- Utilise Whisper (déjà installé en Phase 2)

**Pour l'amélioration audio :**
- `noisereduce==3.0.0` - Réduction de bruit
- `librosa==0.10.1` - Traitement audio avancé
- `soundfile==0.12.1` - Lecture/écriture audio

**Pour la persistance :**
- `sqlalchemy==2.0.23` - ORM base de données
- `alembic==1.12.1` - Migrations DB

---

## ⚠️ Problèmes Courants

### "command not found: pip"

Sur Mac, utilisez toujours le script `Start AutoCut.command` qui gère automatiquement l'environnement virtuel.

### "externally-managed-environment"

C'est normal sur macOS récent. Le script `Start AutoCut.command` crée un environnement virtuel isolé automatiquement.

### "Module not found"

```bash
# Solution : supprimer le venv et relancer
rm -rf backend/venv
./Start\ AutoCut.command
```

### Backend ne démarre pas

```bash
# Vérifier les logs
cat backend.log
```

### Frontend ne démarre pas

```bash
# Réinstaller les dépendances Node
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
```

---

## 🔍 Vérifier la Version

Une fois l'application démarrée, vous pouvez vérifier les nouvelles fonctionnalités :

1. **Détection d'hésitations** : Section "🎤 Détection d'Hésitations" dans l'interface
2. **Amélioration audio** : Dans "Paramètres Avancés" → "🔊 Amélioration Audio"
3. **Historique** : Bouton "📜 Historique" en haut à droite

---

## 📞 Support

Si vous rencontrez des problèmes après la mise à jour :

1. Vérifiez les logs :
   - `backend.log` pour le backend
   - `frontend.log` pour le frontend

2. Essayez un redémarrage complet :
   ```bash
   ./Stop\ AutoCut.command
   rm -rf backend/venv
   ./Start\ AutoCut.command
   ```

3. Si le problème persiste, ouvrez une issue sur GitHub avec :
   - Votre OS (macOS, Windows, Linux)
   - Le contenu de `backend.log`
   - Le message d'erreur complet

---

## ✅ Changements de Version

### v2.0.0 (2024-01-07)

**Nouvelles Fonctionnalités :**
- 🎤 Détection d'hésitations vocales ("euh", "hum", etc.)
- 🔊 Amélioration audio (débruitage)
- 💾 Base de données persistante (SQLite)
- 📜 Historique des traitements avec statistiques

**Améliorations Techniques :**
- Persistance des jobs après redémarrage
- Interface historique avec filtres
- Statistiques détaillées par job
- Meilleure gestion des erreurs

**Compatibilité :**
- ✅ 100% rétrocompatible
- ✅ Toutes les anciennes fonctionnalités conservées
- ✅ Nouvelles fonctionnalités optionnelles (désactivées par défaut)

---

**Dernière mise à jour :** 2024-01-07
