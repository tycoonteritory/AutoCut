"""
Local AI service for generating YouTube optimized titles
Uses Ollama for local AI inference (no OpenAI dependency)
"""
import logging
import json
import requests
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LocalTitleGenerator:
    """Generates YouTube-optimized titles using local AI (Ollama)"""

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "llama2"
    ):
        """
        Initialize local title generator

        Args:
            ollama_url: URL of Ollama API endpoint
            model: Ollama model to use (llama2, mistral, etc.)
        """
        self.ollama_url = ollama_url
        self.model = model
        logger.info(f"LocalTitleGenerator initialized (model: {model}, url: {ollama_url})")

    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call Ollama API with a prompt

        Args:
            prompt: Prompt text

        Returns:
            Generated text or None if error
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,  # More creative
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            return None

    def generate_titles(
        self,
        transcription_text: str,
        num_titles: int = 3,
        video_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate YouTube-optimized titles from transcription

        Args:
            transcription_text: Transcribed text from video
            num_titles: Number of titles to generate (default: 3 for A/B testing)
            video_context: Optional context about the video

        Returns:
            Dictionary with generated titles and metadata
        """
        # Check if Ollama is available
        if not self._check_ollama_available():
            logger.warning("Ollama not available, using fallback title generation")
            return self._generate_fallback_titles(transcription_text, num_titles)

        # Truncate transcription if too long (keep first 2000 chars)
        truncated_text = transcription_text[:2000] if len(transcription_text) > 2000 else transcription_text

        # Build prompt for title generation
        prompt = self._build_title_prompt(truncated_text, num_titles, video_context)

        # Call Ollama
        logger.info(f"Generating {num_titles} YouTube titles with local AI...")
        response = self._call_ollama(prompt)

        if not response:
            logger.warning("Failed to generate titles with AI, using fallback")
            return self._generate_fallback_titles(transcription_text, num_titles)

        # Parse generated titles
        titles = self._parse_titles_from_response(response, num_titles)

        return {
            "titles": titles,
            "model": self.model,
            "source": "local_ai",
            "total_generated": len(titles)
        }

    def _build_title_prompt(
        self,
        transcription: str,
        num_titles: int,
        context: Optional[str]
    ) -> str:
        """Build optimized prompt for title generation"""

        context_str = f"\nContexte supplémentaire: {context}" if context else ""

        prompt = f"""Tu es un expert en optimisation de titres YouTube. Ton objectif est de créer des titres accrocheurs qui maximisent le taux de clic (CTR).

Transcription de la vidéo:
{transcription}{context_str}

Crée {num_titles} titres YouTube différents pour cette vidéo, optimisés pour l'A/B testing:
- Titre 1: Accrocheur et émotionnel (utilise des mots forts)
- Titre 2: Informatif et direct (met en avant la valeur)
- Titre 3: Intriguant avec question ou mystère

Règles importantes:
✓ Maximum 70 caractères par titre
✓ Utilise des chiffres si pertinent (Ex: "5 astuces", "3 erreurs")
✓ Capitalise les mots importants
✓ Évite le clickbait trompeur
✓ Sois spécifique et concret

Format de réponse (JSON):
{{
  "titre_1": "...",
  "titre_2": "...",
  "titre_3": "..."
}}

Génère uniquement le JSON, sans texte supplémentaire."""

        return prompt

    def _parse_titles_from_response(self, response: str, num_titles: int) -> List[Dict[str, str]]:
        """
        Parse titles from AI response

        Args:
            response: Raw response from AI
            num_titles: Expected number of titles

        Returns:
            List of title dictionaries
        """
        titles = []

        try:
            # Try to parse JSON response
            # Find JSON block in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)

                # Extract titles
                for i in range(1, num_titles + 1):
                    key = f"titre_{i}"
                    if key in parsed:
                        title_text = parsed[key].strip()
                        titles.append({
                            "text": title_text,
                            "variant": f"Variante {i}",
                            "length": len(title_text),
                            "type": self._classify_title_type(i)
                        })
            else:
                # Fallback: parse line by line
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                for i, line in enumerate(lines[:num_titles]):
                    # Remove numbering and quotes
                    clean_title = line
                    for prefix in [f"{i+1}.", f"{i+1})", f"Titre {i+1}:", "-", "*"]:
                        clean_title = clean_title.replace(prefix, "").strip()
                    clean_title = clean_title.strip('"').strip("'")

                    if clean_title:
                        titles.append({
                            "text": clean_title,
                            "variant": f"Variante {i+1}",
                            "length": len(clean_title),
                            "type": self._classify_title_type(i+1)
                        })

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from AI response: {e}")
            # Fallback parsing
            lines = [line.strip() for line in response.split('\n') if line.strip() and len(line.strip()) > 10]
            for i, line in enumerate(lines[:num_titles]):
                titles.append({
                    "text": line[:100],  # Limit to 100 chars
                    "variant": f"Variante {i+1}",
                    "length": len(line[:100]),
                    "type": "Standard"
                })

        # Ensure we have at least num_titles
        if len(titles) < num_titles:
            logger.warning(f"Only generated {len(titles)} titles, expected {num_titles}")

        return titles

    def _classify_title_type(self, variant_num: int) -> str:
        """Classify title type based on variant number"""
        types = {
            1: "Émotionnel",
            2: "Informatif",
            3: "Intrigant"
        }
        return types.get(variant_num, "Standard")

    def _generate_fallback_titles(self, transcription: str, num_titles: int) -> Dict[str, Any]:
        """
        Generate simple rule-based titles when AI is not available

        Args:
            transcription: Video transcription
            num_titles: Number of titles to generate

        Returns:
            Dictionary with fallback titles
        """
        # Extract first sentence or first 100 chars
        first_sentence = transcription.split('.')[0][:70] if transcription else "Nouvelle vidéo"

        # Generate basic titles with variations
        titles = [
            {
                "text": f"{first_sentence}",
                "variant": "Variante 1",
                "length": len(first_sentence),
                "type": "Direct"
            },
            {
                "text": f"🎬 {first_sentence}",
                "variant": "Variante 2",
                "length": len(first_sentence) + 3,
                "type": "Avec emoji"
            },
            {
                "text": f"{first_sentence} - Guide Complet",
                "variant": "Variante 3",
                "length": len(first_sentence) + 17,
                "type": "Informatif"
            }
        ]

        return {
            "titles": titles[:num_titles],
            "model": "fallback",
            "source": "rule_based",
            "total_generated": min(len(titles), num_titles)
        }
