"""
GPT-4 Enhanced Video Analysis Service
Provides intelligent analysis for:
- Filler words detection ("heuu", "hum", etc.)
- Best moments detection
- Jokes and originality detection
- Catchy titles and descriptions generation
"""
import logging
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from .openai_client import OpenAIClient

logger = logging.getLogger(__name__)


class GPT4VideoAnalyzer:
    """
    Intelligent video analyzer using GPT-4 for advanced content understanding
    """

    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """
        Initialize GPT-4 analyzer

        Args:
            openai_client: OpenAI client instance (creates new one if not provided)
        """
        self.client = openai_client or OpenAIClient()
        logger.info("GPT-4 Video Analyzer initialized")

    async def analyze_filler_words(
        self,
        transcription_text: str,
        transcription_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect filler words using GPT-4's understanding of context
        More accurate than pattern matching as it understands when "euh" is actually a filler

        Args:
            transcription_text: Full transcription text
            transcription_segments: Segments with timestamps from Whisper

        Returns:
            List of filler word occurrences with timestamps and context
        """
        logger.info("Analyzing filler words with GPT-4...")

        prompt = f"""Tu es un expert en analyse de parole française. Analyse cette transcription et identifie TOUS les mots de remplissage et hésitations.

Transcription:
{transcription_text}

Identifie:
1. Les hésitations vocales: "euh", "euuh", "heu", "heuu", "heum"
2. Les sons d'hésitation: "hum", "hmm", "mm", "mmh"
3. Les mots de remplissage: "ben", "bah", "donc euh", "alors euh", "en fait euh", "du coup euh"
4. Les répétitions inutiles de mots

Pour chaque occurrence, fournis:
- Le mot ou expression exact
- Le contexte (phrase complète)
- La position approximative dans le texte
- Le niveau de certitude (0-100)

Réponds UNIQUEMENT avec un JSON valide dans ce format:
{{
    "filler_words": [
        {{
            "word": "euh",
            "context": "phrase complète avec le mot",
            "position": "début|milieu|fin",
            "confidence": 95,
            "type": "hesitation|filler|repetition"
        }}
    ],
    "total_count": 0,
    "analysis": "brève analyse de la qualité de la parole"
}}"""

        try:
            response = self.client.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for more consistent detection
                max_tokens=2000
            )

            result = json.loads(response)
            logger.info(f"GPT-4 detected {result.get('total_count', 0)} filler words")

            # Match filler words to transcription segments to get precise timestamps
            filler_words_with_timestamps = self._match_fillers_to_segments(
                result.get('filler_words', []),
                transcription_segments
            )

            return filler_words_with_timestamps

        except Exception as e:
            logger.error(f"Error analyzing filler words with GPT-4: {e}")
            return []

    async def detect_best_moments(
        self,
        transcription_text: str,
        transcription_segments: List[Dict[str, Any]],
        video_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Detect the best moments in the video using GPT-4
        Identifies high-energy, interesting, and engaging segments

        Args:
            transcription_text: Full transcription
            transcription_segments: Timestamped segments
            video_duration: Total video duration in seconds

        Returns:
            List of best moments with timestamps and reasons
        """
        logger.info("Detecting best moments with GPT-4...")

        prompt = f"""Tu es un expert en création de contenu viral pour YouTube, TikTok et Instagram. Analyse cette transcription de vidéo et identifie les 5-10 MEILLEURS moments.

Transcription:
{transcription_text}

Durée totale: {video_duration:.0f} secondes

Identifie les moments qui sont:
1. **Accrocheurs** - Captent immédiatement l'attention
2. **Énergiques** - Moments dynamiques, passionnés
3. **Surprenants** - Révélations, twists, informations inattendues
4. **Émotionnels** - Moments drôles, touchants, impressionnants
5. **Informatifs** - Conseils précieux, insights importants

Pour chaque moment, fournis:
- Un titre accrocheur (max 60 caractères)
- La phrase ou segment exact
- Pourquoi c'est un bon moment
- Le type de moment (hook/energy/surprise/emotional/informative)
- Score viral (0-100)

Réponds UNIQUEMENT avec un JSON valide:
{{
    "best_moments": [
        {{
            "title": "Titre accrocheur du moment",
            "text": "texte exact du segment",
            "why_good": "explication courte",
            "moment_type": "hook|energy|surprise|emotional|informative",
            "viral_score": 85,
            "suggested_duration": "30-60 secondes recommandé"
        }}
    ],
    "overall_analysis": "analyse globale du contenu vidéo"
}}"""

        try:
            response = self.client.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,  # Higher creativity for moment detection
                max_tokens=3000
            )

            result = json.loads(response)
            best_moments = result.get('best_moments', [])

            # Match moments to timestamps
            moments_with_timestamps = self._match_moments_to_segments(
                best_moments,
                transcription_segments
            )

            logger.info(f"GPT-4 detected {len(moments_with_timestamps)} best moments")
            return moments_with_timestamps

        except Exception as e:
            logger.error(f"Error detecting best moments with GPT-4: {e}")
            return []

    async def detect_jokes_and_originality(
        self,
        transcription_text: str,
        transcription_segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Detect jokes, punchlines, and original/creative moments

        Args:
            transcription_text: Full transcription
            transcription_segments: Timestamped segments

        Returns:
            List of jokes and original moments with analysis
        """
        logger.info("Detecting jokes and originality with GPT-4...")

        prompt = f"""Tu es un expert en humour et créativité. Analyse cette transcription et identifie TOUS les moments drôles, vannes, et moments originaux.

Transcription:
{transcription_text}

Identifie:
1. **Vannes et blagues** - Moments humoristiques intentionnels
2. **Punchlines** - Chutes de blagues, révélations drôles
3. **Jeux de mots** - Calembours, double sens
4. **Humour situationnel** - Moments drôles dans le contexte
5. **Observations originales** - Perspectives uniques, créatives
6. **Moments absurdes** - Situations ou commentaires hilarants

Pour chaque moment, fournis:
- Le texte exact de la vanne/moment
- Type de humor
- Score de drôlerie (0-100)
- Pourquoi c'est drôle/original
- Potentiel viral

Réponds UNIQUEMENT avec un JSON valide:
{{
    "funny_moments": [
        {{
            "text": "texte exact de la vanne",
            "type": "joke|punchline|wordplay|situational|observation|absurd",
            "funny_score": 75,
            "why_funny": "explication",
            "viral_potential": 80,
            "context": "contexte si nécessaire"
        }}
    ],
    "humor_analysis": "analyse du style d'humour général"
}}"""

        try:
            response = self.client.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,  # Higher creativity for humor detection
                max_tokens=2500
            )

            result = json.loads(response)
            funny_moments = result.get('funny_moments', [])

            # Match to timestamps
            jokes_with_timestamps = self._match_moments_to_segments(
                funny_moments,
                transcription_segments,
                text_key='text'
            )

            logger.info(f"GPT-4 detected {len(jokes_with_timestamps)} jokes and original moments")
            return jokes_with_timestamps

        except Exception as e:
            logger.error(f"Error detecting jokes with GPT-4: {e}")
            return []

    async def generate_catchy_titles_and_description(
        self,
        transcription_text: str,
        video_duration: float,
        best_moments: Optional[List[Dict[str, Any]]] = None,
        jokes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate multiple catchy title options and an engaging description

        Args:
            transcription_text: Full transcription
            video_duration: Duration in seconds
            best_moments: Optional best moments detected
            jokes: Optional jokes detected

        Returns:
            Dict with titles, description, hooks, and hashtags
        """
        logger.info("Generating catchy titles and description with GPT-4...")

        # Prepare context
        context = f"Transcription:\n{transcription_text}\n\nDurée: {video_duration:.0f}s"

        if best_moments:
            context += f"\n\nMeilleurs moments identifiés: {len(best_moments)}"
        if jokes:
            context += f"\nMoments drôles identifiés: {len(jokes)}"

        prompt = f"""Tu es un expert en marketing YouTube et création de contenu viral. Crée des titres ULTRA accrocheurs et une description engageante.

{context}

Crée:

1. **5 TITRES ACCROCHEURS** (différents styles):
   - Titre curiosity-driven (suscite la curiosité)
   - Titre benefit-driven (met en avant le bénéfice)
   - Titre controversy/hot-take (avis tranché)
   - Titre question (pose une question intrigante)
   - Titre storytelling (raconte une histoire)

Règles pour les titres:
- Max 60-70 caractères
- Commence par un mot fort
- Utilise des chiffres si pertinent
- Crée de l'urgence ou de la curiosité
- Évite le clickbait mensonger

2. **DESCRIPTION YOUTUBE** (200-300 mots):
   - Hook puissant (première ligne)
   - Résumé engageant du contenu
   - Call-to-action
   - Hashtags pertinents

3. **3 HOOKS** pour les courts extraits:
   - Phrases d'accroche percutantes
   - Pour TikTok/Reels/Shorts

Réponds UNIQUEMENT avec un JSON valide:
{{
    "titles": [
        {{
            "text": "Titre complet",
            "style": "curiosity|benefit|controversy|question|storytelling",
            "hook_score": 90
        }}
    ],
    "description": {{
        "hook_line": "Première ligne accrocheuse",
        "full_text": "Description complète avec paragraphes",
        "cta": "Call to action",
        "hashtags": ["#tag1", "#tag2"]
    }},
    "hooks": [
        {{
            "text": "Hook court et percutant",
            "use_case": "TikTok|Reels|Shorts"
        }}
    ],
    "seo_keywords": ["mot-clé1", "mot-clé2"]
}}"""

        try:
            response = self.client.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,  # High creativity for titles
                max_tokens=2000
            )

            result = json.loads(response)
            logger.info(f"GPT-4 generated {len(result.get('titles', []))} title options")
            return result

        except Exception as e:
            logger.error(f"Error generating titles and description: {e}")
            return {
                "titles": [],
                "description": {
                    "hook_line": "",
                    "full_text": "",
                    "cta": "",
                    "hashtags": []
                },
                "hooks": [],
                "seo_keywords": []
            }

    def _match_fillers_to_segments(
        self,
        filler_words: List[Dict[str, Any]],
        segments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Match detected filler words to transcription segments to get timestamps
        """
        result = []

        for filler in filler_words:
            word = filler.get('word', '')
            context = filler.get('context', '').lower()

            # Find matching segment
            for segment in segments:
                segment_text = segment.get('text', '').lower()
                if word.lower() in segment_text and context[:30] in segment_text:
                    result.append({
                        **filler,
                        'start_time': segment.get('start', 0),
                        'end_time': segment.get('end', 0),
                        'segment_id': segment.get('id', 0)
                    })
                    break

        return result

    def _match_moments_to_segments(
        self,
        moments: List[Dict[str, Any]],
        segments: List[Dict[str, Any]],
        text_key: str = 'text'
    ) -> List[Dict[str, Any]]:
        """
        Match detected moments to transcription segments to get timestamps
        """
        result = []

        for moment in moments:
            moment_text = moment.get(text_key, '').lower()
            if not moment_text:
                continue

            # Find best matching segment(s)
            best_match = None
            best_score = 0

            for i, segment in enumerate(segments):
                segment_text = segment.get('text', '').lower()

                # Simple word overlap scoring
                moment_words = set(moment_text.split())
                segment_words = set(segment_text.split())
                overlap = len(moment_words & segment_words)
                score = overlap / max(len(moment_words), 1)

                if score > best_score:
                    best_score = score
                    best_match = segment

            if best_match and best_score > 0.3:  # At least 30% word overlap
                result.append({
                    **moment,
                    'start_time': best_match.get('start', 0),
                    'end_time': best_match.get('end', 0),
                    'match_confidence': best_score
                })

        return result
