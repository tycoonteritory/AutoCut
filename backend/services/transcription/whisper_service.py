"""
Whisper transcription service for video audio
"""
import logging
import whisper
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import torch
from ...config import settings

logger = logging.getLogger(__name__)


class WhisperTranscriptionService:
    """Transcribes video audio using OpenAI Whisper"""

    def __init__(self, model_name: str = None, language: str = None):
        """
        Initialize Whisper service

        Args:
            model_name: Whisper model (tiny, base, small, medium, large)
            language: Language code (fr, en, etc.)
        """
        self.model_name = model_name or settings.WHISPER_MODEL
        self.language = language or settings.TRANSCRIPTION_LANGUAGE
        self.model = None

        logger.info(f"Whisper service initialized (model: {self.model_name}, language: {self.language})")

    def _load_model(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            logger.info(f"Loading Whisper model: {self.model_name}")
            try:
                self.model = whisper.load_model(self.model_name)
                logger.info("Whisper model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
                raise

    def transcribe_audio(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file

        Args:
            audio_path: Path to audio file (WAV)
            progress_callback: Callback for progress updates (can be sync or async)

        Returns:
            Dictionary with transcription results
        """
        try:
            # Load model
            self._load_model()

            if progress_callback:
                # Try to detect if callback is async and handle it
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(progress_callback):
                    # Async callback - create task without waiting
                    try:
                        loop = asyncio.get_event_loop()
                        asyncio.ensure_future(progress_callback(0, "Starting transcription..."))
                    except:
                        pass  # No event loop, skip
                else:
                    # Sync callback
                    progress_callback(0, "Starting transcription...")

            logger.info(f"Transcribing audio: {audio_path}")

            # Transcribe with Whisper
            # IMPORTANT: Keep all filler words and hesitations!
            result = self.model.transcribe(
                str(audio_path),
                language=self.language,
                task="transcribe",
                verbose=False,
                fp16=False,  # Disable FP16 for better compatibility
                condition_on_previous_text=False,  # Don't filter based on context
                suppress_tokens="",  # Don't suppress any tokens (keep "euh", "hmm", etc.)
                word_timestamps=False  # We use segment timestamps
            )

            # Debug logging
            logger.info(f"Whisper raw result keys: {result.keys()}")
            raw_text = result.get("text", "")
            logger.info(f"Transcription text length: {len(raw_text)} characters")
            logger.info(f"Number of segments: {len(result.get('segments', []))}")
            logger.info(f"Text preview (first 200 chars): {raw_text[:200]}")

            if progress_callback:
                # Try async callback
                import asyncio
                import inspect
                if inspect.iscoroutinefunction(progress_callback):
                    try:
                        asyncio.ensure_future(progress_callback(100, "Transcription complete!"))
                    except:
                        pass
                else:
                    progress_callback(100, "Transcription complete!")

            # Extract segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                segments.append({
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"].strip()
                })

            transcription_result = {
                "text": result["text"].strip(),
                "segments": segments,
                "language": result.get("language", self.language)
            }

            logger.info(f"Transcription complete: {len(segments)} segments")
            return transcription_result

        except Exception as e:
            logger.error(f"Error transcribing audio: {e}", exc_info=True)
            raise

    def transcribe_video(
        self,
        video_path: Path,
        audio_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Transcribe video using pre-extracted audio

        Args:
            video_path: Path to video file (for reference)
            audio_path: Path to extracted audio file
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with transcription results
        """
        logger.info(f"Transcribing video: {video_path}")

        result = self.transcribe_audio(audio_path, progress_callback)

        result["video_path"] = str(video_path)
        result["audio_path"] = str(audio_path)

        return result
