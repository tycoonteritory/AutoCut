"""
YouTube optimization orchestrator - coordinates all optimization services
"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .title_generator import TitleGenerator
from .thumbnail_extractor import ThumbnailExtractor
from .tag_generator import TagGenerator
from .chapter_generator import ChapterGenerator
from ..ai_services.openai_client import get_openai_client
from ...config import settings

logger = logging.getLogger(__name__)


class YouTubeOptimizer:
    """Orchestrates complete YouTube optimization"""

    def __init__(self):
        self.title_generator = TitleGenerator()
        self.thumbnail_extractor = ThumbnailExtractor()
        self.tag_generator = TagGenerator()
        self.chapter_generator = ChapterGenerator()
        self.openai_client = get_openai_client()

    async def optimize_for_youtube(
        self,
        video_path: Path,
        transcription_result: Dict[str, Any],
        output_dir: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Complete YouTube optimization

        Args:
            video_path: Path to video file
            transcription_result: Transcription result from Whisper
            output_dir: Output directory for thumbnails
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with all optimization results
        """
        try:
            logger.info(f"Starting YouTube optimization for: {video_path}")

            if progress_callback:
                await progress_callback(0, "Starting YouTube optimization...")

            transcription = transcription_result["text"]
            segments = transcription_result["segments"]

            # 1. Generate titles
            if progress_callback:
                await progress_callback(10, "Generating title suggestions...")

            logger.info("Generating titles...")
            titles = self.title_generator.generate_titles(
                transcription,
                video_name=video_path.stem
            )

            if progress_callback:
                await progress_callback(30, "Extracting thumbnail candidates...")

            # 2. Extract thumbnails
            logger.info("Extracting thumbnails...")
            thumbnails_dir = output_dir / "thumbnails"
            thumbnails = self.thumbnail_extractor.extract_thumbnails(
                video_path,
                thumbnails_dir
            )

            if progress_callback:
                await progress_callback(60, "Generating tags...")

            # 3. Generate tags
            logger.info("Generating tags...")
            tags = self.tag_generator.generate_tags(
                transcription,
                title=titles[0] if titles else None
            )

            if progress_callback:
                await progress_callback(75, "Creating chapters...")

            # 4. Generate chapters
            logger.info("Generating chapters...")
            chapters = self.chapter_generator.generate_chapters(segments)

            if progress_callback:
                await progress_callback(90, "Generating description...")

            # 5. Generate optimized description
            logger.info("Generating description...")
            description = self._generate_description(transcription, titles[0] if titles else None)

            if progress_callback:
                await progress_callback(100, "Optimization complete!")

            # Convert thumbnail absolute paths to relative URLs
            for thumb in thumbnails:
                abs_path = Path(thumb['path'])
                rel_path = abs_path.relative_to(settings.OUTPUT_DIR)
                thumb['url'] = f"/outputs/{rel_path.as_posix()}"

            result = {
                "success": True,
                "titles": titles,
                "thumbnails": thumbnails,
                "tags": tags,
                "chapters": chapters,
                "description": description,
                "transcription_summary": transcription[:500] + "..." if len(transcription) > 500 else transcription
            }

            logger.info("YouTube optimization complete")
            return result

        except Exception as e:
            logger.error(f"Error optimizing for YouTube: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_description(self, transcription: str, title: str = None) -> str:
        """Generate optimized YouTube description"""
        try:
            context = transcription[:1000] if len(transcription) > 1000 else transcription

            prompt = f"""Génère une description YouTube optimisée (150-200 mots) pour cette vidéo.

{f"Titre: {title}" if title else ""}

Transcription (extrait) :
{context}

La description doit:
- Résumer le contenu de la vidéo
- Être engageante et inciter au clic
- Inclure des mots-clés pertinents
- Être en français
- Inviter à liker, commenter et s'abonner à la fin

Réponds UNIQUEMENT avec la description, sans formatage spécial."""

            messages = [
                {"role": "system", "content": "Tu es un expert en création de contenu YouTube optimisé."},
                {"role": "user", "content": prompt}
            ]

            description = self.openai_client.create_chat_completion(
                messages=messages,
                temperature=0.7,
                max_tokens=400
            )

            return description.strip()

        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return f"Découvrez cette vidéo ! {title if title else ''}\n\nN'oubliez pas de liker et vous abonner !"
