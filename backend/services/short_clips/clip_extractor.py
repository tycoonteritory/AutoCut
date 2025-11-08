"""
Clip extraction service - extracts short clips from video
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import asyncio

logger = logging.getLogger(__name__)


class ClipExtractor:
    """Extracts short clips from video files"""

    def __init__(self):
        pass

    async def extract_clips(
        self,
        video_path: Path,
        clips: List[Dict[str, Any]],
        output_dir: Path,
        format: str = "horizontal",  # "horizontal" or "vertical"
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract multiple clips from a video

        Args:
            video_path: Path to source video
            clips: List of clip definitions with start_time, end_time, title
            output_dir: Output directory for clips
            format: "horizontal" (16:9) or "vertical" (9:16)
            progress_callback: Callback for progress updates

        Returns:
            List of extracted clips with file paths
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            extracted_clips = []
            total_clips = len(clips)

            for idx, clip in enumerate(clips):
                if progress_callback:
                    progress = (idx / total_clips) * 100
                    await progress_callback(
                        progress,
                        f"Extraction du clip {idx + 1}/{total_clips}: {clip['title'][:30]}..."
                    )

                # Generate safe filename
                safe_title = self._sanitize_filename(clip["title"])
                output_filename = f"clip_{idx + 1}_{safe_title}.mp4"
                output_path = output_dir / output_filename

                # Extract clip
                success = await self._extract_single_clip(
                    video_path,
                    output_path,
                    clip["start_time"],
                    clip["end_time"],
                    format
                )

                if success:
                    # Add file info to clip
                    extracted_clip = {
                        **clip,
                        "file_path": str(output_path),
                        "filename": output_filename,
                        "format": format,
                        "file_size": output_path.stat().st_size if output_path.exists() else 0
                    }
                    extracted_clips.append(extracted_clip)

                    logger.info(f"Extracted clip {idx + 1}: {output_filename}")
                else:
                    logger.warning(f"Failed to extract clip {idx + 1}")

            if progress_callback:
                await progress_callback(100, "Extraction des clips terminée !")

            logger.info(f"Successfully extracted {len(extracted_clips)}/{total_clips} clips")
            return extracted_clips

        except Exception as e:
            logger.error(f"Error extracting clips: {e}", exc_info=True)
            raise

    async def _extract_single_clip(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
        format: str = "horizontal"
    ) -> bool:
        """
        Extract a single clip from video

        Args:
            video_path: Source video path
            output_path: Output clip path
            start_time: Start time in seconds
            end_time: End time in seconds
            format: "horizontal" or "vertical"

        Returns:
            True if successful, False otherwise
        """
        try:
            duration = end_time - start_time

            # Base ffmpeg command for extraction
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-ss", str(start_time),  # Start time
                "-i", str(video_path),  # Input video
                "-t", str(duration),  # Duration
                "-c:v", "libx264",  # Video codec
                "-preset", "fast",  # Encoding speed
                "-crf", "23",  # Quality (lower = better, 23 is good)
                "-c:a", "aac",  # Audio codec
                "-b:a", "128k",  # Audio bitrate
            ]

            # Add format-specific filters
            if format == "vertical":
                # Crop to 9:16 aspect ratio (CENTER crop - focus on subject)
                # crop=width:height:x:y where x,y is top-left corner
                # For center crop: x=(iw-ow)/2, which crops from center
                cmd.extend([
                    "-vf", "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920",
                    "-aspect", "9:16"
                ])
            else:
                # Keep original aspect ratio (16:9)
                cmd.extend([
                    "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"
                ])

            cmd.append(str(output_path))

            # Run ffmpeg in executor to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
            )

            if result.returncode != 0:
                logger.error(f"ffmpeg error: {result.stderr}")
                return False

            return output_path.exists()

        except subprocess.TimeoutExpired:
            logger.error(f"Clip extraction timeout for {output_path}")
            return False
        except Exception as e:
            logger.error(f"Error extracting clip: {e}", exc_info=True)
            return False

    def _sanitize_filename(self, title: str, max_length: int = 50) -> str:
        """
        Sanitize title for use as filename

        Args:
            title: Original title
            max_length: Maximum filename length

        Returns:
            Safe filename
        """
        # Remove/replace unsafe characters
        safe = "".join(
            c if c.isalnum() or c in (' ', '-', '_') else '_'
            for c in title
        )

        # Replace spaces with underscores
        safe = safe.replace(' ', '_')

        # Remove consecutive underscores
        while '__' in safe:
            safe = safe.replace('__', '_')

        # Trim length
        safe = safe[:max_length].strip('_')

        return safe or "clip"
