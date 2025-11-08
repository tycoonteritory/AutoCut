"""
YouTube chapters generation using GPT-4
"""
import logging
import json
from typing import List, Dict
from ..ai_services.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class ChapterGenerator:
    """Generates YouTube chapters using GPT-4"""

    def __init__(self):
        self.client = get_openai_client()

    def generate_chapters(self, segments: List[Dict]) -> List[Dict[str, any]]:
        """
        Generate YouTube chapters from transcription segments

        Args:
            segments: List of transcription segments with timestamps

        Returns:
            List of chapters with time and title
        """
        try:
            # Group segments into logical sections (every ~2-3 minutes)
            chapter_segments = self._group_segments(segments)

            # Generate chapter titles using GPT-4
            chapters = []

            for i, segment_group in enumerate(chapter_segments):
                start_time = segment_group[0]["start"]
                texts = [s["text"] for s in segment_group]
                combined_text = " ".join(texts)[:500]  # Limit text

                # Generate chapter title
                title = self._generate_chapter_title(combined_text, i + 1)

                chapters.append({
                    "time": self._format_timestamp(start_time),
                    "timestamp_seconds": start_time,
                    "title": title
                })

            logger.info(f"Generated {len(chapters)} chapters")
            return chapters

        except Exception as e:
            logger.error(f"Error generating chapters: {e}", exc_info=True)
            # Return simple fallback
            return [{"time": "0:00", "timestamp_seconds": 0, "title": "Introduction"}]

    def _group_segments(self, segments: List[Dict], target_duration: float = 150) -> List[List[Dict]]:
        """
        Group segments into chapters (~2-3 minutes each)

        Args:
            segments: List of segments
            target_duration: Target duration per chapter in seconds

        Returns:
            List of segment groups
        """
        groups = []
        current_group = []
        group_start = 0

        for segment in segments:
            current_group.append(segment)

            # Check if we should start a new group
            if segment["end"] - group_start >= target_duration:
                groups.append(current_group)
                current_group = []
                group_start = segment["end"]

        # Add remaining segments
        if current_group:
            groups.append(current_group)

        return groups

    def _generate_chapter_title(self, text: str, chapter_num: int) -> str:
        """Generate title for a chapter using GPT-4"""
        try:
            prompt = f"""Génère un titre court et descriptif (5 mots maximum) pour ce chapitre de vidéo YouTube.

Contenu du chapitre :
{text}

Réponds UNIQUEMENT avec le titre, sans guillemets ni numéro de chapitre."""

            messages = [
                {"role": "system", "content": "Tu génères des titres de chapitres courts et descriptifs en français."},
                {"role": "user", "content": prompt}
            ]

            title = self.client.create_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=50
            )

            # Clean title
            title = title.strip().strip('"\'')

            # Limit length
            if len(title) > 60:
                title = title[:57] + "..."

            return title

        except Exception as e:
            logger.error(f"Error generating chapter title: {e}")
            return f"Partie {chapter_num}"

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to YouTube timestamp (M:SS or H:MM:SS)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
