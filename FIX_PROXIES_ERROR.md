# Fix: Client.__init__() got an unexpected keyword argument 'proxies'

## Problème

Si vous rencontrez l'erreur suivante lors de l'utilisation des sous-titres:
```
❌ Error: Clip generation error: Client.__init__() got an unexpected keyword argument 'proxies'
```

Cette erreur est causée par une incompatibilité entre les versions d'OpenAI et httpx.

## Cause

- La bibliothèque `httpx 0.28.0+` a supprimé le paramètre `proxies` (déprécié)
- Certaines versions d'OpenAI (< 1.55.3) essaient toujours d'utiliser ce paramètre
- Cela provoque une erreur lors de l'initialisation du client OpenAI

## Solution

### Option 1: Réinstaller les dépendances (Recommandé)

```bash
cd backend
pip install --upgrade -r requirements.txt
```

Les versions ont été mises à jour pour:
- `openai>=1.55.3` (corrige le bug)
- `httpx==0.27.2` (version compatible)

### Option 2: Fix rapide manuel

Si vous voulez juste fixer rapidement sans réinstaller tout:

```bash
pip install --upgrade openai
pip install httpx==0.27.2
```

### Option 3: Versions spécifiques

```bash
pip install openai==1.55.3 httpx==0.27.2
```

## Vérification

Après avoir appliqué la correction, redémarrez votre serveur backend:

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Ensuite, testez à nouveau la fonctionnalité de sous-titres.

## Référence

Ce bug est documenté sur:
- [OpenAI GitHub Issue #1903](https://github.com/openai/openai-python/issues/1903)
- [OpenAI Community Discussion](https://community.openai.com/t/error-with-openai-1-56-0/1040332)
