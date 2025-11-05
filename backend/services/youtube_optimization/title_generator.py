"""
YouTube title generation using GPT-4
"""
import logging
import json
from typing import List
from backend.services.ai_services.openai_client import get_openai_client
from backend.config import settings

logger = logging.getLogger(__name__)


class TitleGenerator:
    """Generates optimized YouTube titles using GPT-4"""

    def __init__(self):
        self.client = get_openai_client()

    def generate_titles(self, transcription: str, video_name: str = None) -> List[str]:
        """
        Generate YouTube title suggestions

        Args:
            transcription: Full video transcription
            video_name: Original video name (optional)

        Returns:
            List of title suggestions
        """
        try:
            # Limit transcription to first 2000 characters for context
            context = transcription[:2000] if len(transcription) > 2000 else transcription

            prompt = f"""Tu es un expert en optimisation YouTube. Génère {settings.NUM_TITLE_SUGGESTIONS} titres courts et accrocheurs pour une vidéo YouTube basée sur cette transcription.

Transcription (extrait) :
{context}

Critères pour les titres :
- Maximum 60 caractères
- Accrocheur et clair
- Optimisé SEO avec mots-clés pertinents
- En français
- Éviter le clickbait excessif
- Utiliser des chiffres si pertinent

Réponds UNIQUEMENT avec un JSON array de {settings.NUM_TITLE_SUGGESTIONS} titres, exemple:
["Titre 1", "Titre 2", "Titre 3"]"""

            messages = [
                {"role": "system", "content": "Tu es un expert en optimisation de contenu YouTube. Tu réponds toujours avec du JSON valide."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.create_chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=500
            )

            # Parse JSON response
            titles = json.loads(response)

            # Ensure we have a list
            if not isinstance(titles, list):
                raise ValueError("Response is not a list")

            # Limit title length
            titles = [title[:60] for title in titles[:settings.NUM_TITLE_SUGGESTIONS]]

            logger.info(f"Generated {len(titles)} title suggestions")
            return titles

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            # Fallback titles
            return [
                f"Nouvelle vidéo - {video_name or 'Sans titre'}",
                f"À découvrir : {video_name or 'Contenu exclusif'}",
                f"Regardez cette vidéo !"
            ]
        except Exception as e:
            logger.error(f"Error generating titles: {e}", exc_info=True)
            raise
