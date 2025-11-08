"""
Clip detection service - identifies interesting moments for short clips
"""
import logging
import json
from typing import List, Dict, Any
from ..ai_services.openai_client import get_openai_client

logger = logging.getLogger(__name__)


class ClipDetector:
    """Detects the best moments in a video for short clips using GPT-4"""

    def __init__(self):
        self.client = get_openai_client()

    def detect_best_moments(
        self,
        transcription: str,
        segments: List[Dict],
        num_clips: int = 3,
        target_duration: int = 45
    ) -> List[Dict[str, Any]]:
        """
        Detect the best moments for short clips

        Args:
            transcription: Full video transcription
            segments: Transcription segments with timestamps
            num_clips: Number of clips to generate (default: 3)
            target_duration: Target duration in seconds (default: 45s)

        Returns:
            List of clip suggestions with start/end times and descriptions
        """
        try:
            logger.info(f"Detecting {num_clips} best moments for short clips...")

            # Prepare segments info for GPT-4
            segments_text = self._prepare_segments_text(segments)

            prompt = f"""Analyse cette transcription de vidéo et identifie les {num_clips} MEILLEURS moments pour créer des clips courts (TikTok/Reels/Shorts).

CRITÈRES pour un BON moment :
✅ Autonome (se comprend sans contexte)
✅ Accrocheur dès les premières secondes
✅ Contient une info/astuce/punchline intéressante
✅ Énergie/émotion forte (rires, surprise, révélation)
✅ Durée idéale : {target_duration-10} à {target_duration+15} secondes
✅ Pas de dépendance à d'autres parties de la vidéo

SEGMENTS DISPONIBLES (avec timecodes) :
{segments_text[:3000]}

INSTRUCTIONS :
1. Identifie les {num_clips} moments les PLUS viraux/engageants
2. Pour chaque moment, trouve le segment de début et de fin qui forme un clip cohérent
3. Assure-toi que chaque clip a un début ET une fin naturels
4. Donne un titre accrocheur pour chaque clip

Réponds UNIQUEMENT avec un JSON array au format suivant :
[
  {{
    "start_segment": 5,
    "end_segment": 12,
    "title": "Titre accrocheur du clip",
    "hook": "Phrase d'accroche pour les 3 premières secondes",
    "why_interesting": "Pourquoi ce moment est viral",
    "estimated_duration": 45
  }}
]

IMPORTANT : Les numéros de segment doivent correspondre aux segments fournis ci-dessus."""

            messages = [
                {
                    "role": "system",
                    "content": "Tu es un expert en création de contenu viral pour TikTok, Instagram Reels et YouTube Shorts. Tu identifies les moments les plus engageants dans les vidéos. Tu réponds TOUJOURS avec du JSON valide."
                },
                {"role": "user", "content": prompt}
            ]

            response = self.client.create_chat_completion(
                messages=messages,
                temperature=0.8,
                max_tokens=1000
            )

            # Parse JSON response
            clips = json.loads(response)

            # Validate and enrich clips with actual timestamps
            validated_clips = []
            for clip in clips[:num_clips]:
                try:
                    start_idx = clip.get("start_segment", 0)
                    end_idx = clip.get("end_segment", 0)

                    # Validate indices
                    if start_idx >= len(segments) or end_idx >= len(segments):
                        logger.warning(f"Invalid segment indices: {start_idx}-{end_idx}")
                        continue

                    if start_idx >= end_idx:
                        logger.warning(f"Start segment >= end segment: {start_idx} >= {end_idx}")
                        continue

                    # Get actual timestamps
                    start_time = segments[start_idx]["start"]
                    end_time = segments[end_idx]["end"]
                    duration = end_time - start_time

                    # Skip clips that are too short or too long
                    if duration < 15 or duration > 90:
                        logger.warning(f"Clip duration out of range: {duration}s")
                        continue

                    # Extract text for this clip
                    clip_text = " ".join([
                        segments[i]["text"]
                        for i in range(start_idx, end_idx + 1)
                    ])

                    validated_clip = {
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "title": clip.get("title", "Clip intéressant"),
                        "hook": clip.get("hook", ""),
                        "why_interesting": clip.get("why_interesting", "Moment engageant"),
                        "clip_text": clip_text[:500],  # Limit text
                        "start_segment_idx": start_idx,
                        "end_segment_idx": end_idx
                    }

                    validated_clips.append(validated_clip)

                except Exception as e:
                    logger.error(f"Error validating clip: {e}")
                    continue

            logger.info(f"Detected {len(validated_clips)} valid clips")
            return validated_clips

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GPT-4 response as JSON: {e}")
            # Fallback: create clips from high-energy moments
            return self._fallback_clip_detection(segments, num_clips, target_duration)

        except Exception as e:
            logger.error(f"Error detecting clips: {e}", exc_info=True)
            return self._fallback_clip_detection(segments, num_clips, target_duration)

    def _prepare_segments_text(self, segments: List[Dict]) -> str:
        """Prepare segments for GPT-4 analysis"""
        lines = []
        for idx, segment in enumerate(segments[:100]):  # Limit to first 100 segments
            start = self._format_timestamp(segment["start"])
            end = self._format_timestamp(segment["end"])
            text = segment["text"]
            lines.append(f"[Segment {idx}] {start}-{end}: {text}")

        return "\n".join(lines)

    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds to MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def _fallback_clip_detection(
        self,
        segments: List[Dict],
        num_clips: int,
        target_duration: int
    ) -> List[Dict[str, Any]]:
        """
        Fallback method: evenly distribute clips across the video
        """
        logger.info("Using fallback clip detection method")

        if not segments:
            return []

        total_duration = segments[-1]["end"]
        clips = []

        # Divide video into equal parts
        for i in range(num_clips):
            # Calculate start time for this clip
            start_time = (total_duration / (num_clips + 1)) * (i + 1)

            # Find segment closest to this time
            start_segment_idx = self._find_nearest_segment(segments, start_time)

            # Calculate end segment
            end_time = min(start_time + target_duration, total_duration)
            end_segment_idx = self._find_nearest_segment(segments, end_time)

            if start_segment_idx < end_segment_idx and end_segment_idx < len(segments):
                clips.append({
                    "start_time": segments[start_segment_idx]["start"],
                    "end_time": segments[end_segment_idx]["end"],
                    "duration": segments[end_segment_idx]["end"] - segments[start_segment_idx]["start"],
                    "title": f"Moment intéressant #{i + 1}",
                    "hook": "À découvrir",
                    "why_interesting": "Extrait de la vidéo",
                    "clip_text": " ".join([s["text"] for s in segments[start_segment_idx:end_segment_idx + 1]])[:500],
                    "start_segment_idx": start_segment_idx,
                    "end_segment_idx": end_segment_idx
                })

        return clips

    def _find_nearest_segment(self, segments: List[Dict], target_time: float) -> int:
        """Find the segment index closest to target time"""
        for i, segment in enumerate(segments):
            if segment["start"] >= target_time:
                return max(0, i - 1)
        return len(segments) - 1
