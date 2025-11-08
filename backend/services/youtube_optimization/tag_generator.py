"""
YouTube tags generation using GPT-4
"""
import logging
import json
from typing import List
from ..ai_services.openai_client import get_openai_client
from ...config import settings

logger = logging.getLogger(__name__)


class TagGenerator:
    """Generates YouTube tags using GPT-4"""

    def __init__(self):
        self.client = get_openai_client()

    def generate_tags(self, transcription: str, title: str = None) -> List[str]:
        """
        Generate YouTube tags

        Args:
            transcription: Full video transcription
            title: Video title (optional)

        Returns:
            List of tags
        """
        try:
            # Limit transcription
            context = transcription[:1500] if len(transcription) > 1500 else transcription

            prompt = f"""Tu es un expert en SEO YouTube. Génère {settings.MAX_TAGS} tags pertinents pour cette vidéo.

{f"Titre: {title}" if title else ""}

Transcription (extrait) :
{context}

Critères pour les tags :
- Mots-clés SEO pertinents
- En français
- Variété (généraux et spécifiques)
- Phrases courtes (2-3 mots max)

Réponds UNIQUEMENT avec un JSON array de {settings.MAX_TAGS} tags, exemple:
["tag 1", "tag 2", "tag 3"]"""

            messages = [
                {"role": "system", "content": "Tu es un expert en SEO YouTube. Tu réponds toujours avec du JSON valide."},
                {"role": "user", "content": prompt}
            ]

            response = self.client.create_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            # Parse JSON response
            tags = json.loads(response)

            if not isinstance(tags, list):
                raise ValueError("Response is not a list")

            tags = tags[:settings.MAX_TAGS]

            logger.info(f"Generated {len(tags)} tags")
            return tags

        except Exception as e:
            logger.error(f"Error generating tags: {e}", exc_info=True)
            # Fallback tags
            return ["vidéo", "contenu", "tutoriel"]
