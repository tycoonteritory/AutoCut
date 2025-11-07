"""
Filler words detection service (euh, hum, ben, etc.)
Detects and locates verbal hesitations in French audio
"""
import logging
import re
from pathlib import Path
from typing import List, Tuple, Optional, Callable, Dict, Any
from ..transcription.whisper_service import WhisperTranscriptionService

logger = logging.getLogger(__name__)


class FillerWordsDetector:
    """Detects filler words (hesitations) in French audio using Whisper transcription"""

    # French filler words patterns
    # Using word boundaries and common variations
    FILLER_PATTERNS = [
        # "Euh" variations
        r'\b(?:euh+|heu+|eu+h*|uh+)\b',

        # "Hum" variations
        r'\b(?:hum+|hmm+|mm+h*|mh+)\b',

        # "Ben" and "Bah"
        r'\b(?:ben|bah|beh)\b',

        # Common hesitation phrases
        r'\b(?:alors\s+euh+|donc\s+euh+|et\s+euh+)\b',
        r'\b(?:comment\s+dire|disons|voilà)\b',

        # Repeated words (stuttering)
        r'\b(\w+)\s+\1\b',  # e.g., "je je", "le le"

        # Breathing sounds (optional)
        r'\b(?:\[breath\]|\[respiration\])\b',
    ]

    def __init__(
        self,
        whisper_model: str = "base",
        language: str = "fr",
        sensitivity: float = 0.7,
        min_duration_ms: int = 100,
        custom_patterns: Optional[List[str]] = None
    ):
        """
        Initialize filler words detector

        Args:
            whisper_model: Whisper model to use (tiny, base, small, medium, large)
            language: Language code (default: fr for French)
            sensitivity: Detection sensitivity (0.0 to 1.0, higher = more aggressive)
            min_duration_ms: Minimum duration for a filler word to be considered (ms)
            custom_patterns: Additional regex patterns to detect
        """
        self.whisper_service = WhisperTranscriptionService(
            model_name=whisper_model,
            language=language
        )
        self.sensitivity = sensitivity
        self.min_duration_ms = min_duration_ms
        self.language = language

        # Compile patterns for faster matching
        self.patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.FILLER_PATTERNS]

        if custom_patterns:
            self.patterns.extend([re.compile(p, re.IGNORECASE) for p in custom_patterns])

        logger.info(
            f"FillerWordsDetector initialized (model: {whisper_model}, "
            f"language: {language}, sensitivity: {sensitivity})"
        )

    def _is_filler_word(self, text: str) -> bool:
        """
        Check if a text segment contains a filler word

        Args:
            text: Text to check

        Returns:
            True if text contains a filler word
        """
        text = text.strip().lower()

        # Check against all patterns
        for pattern in self.patterns:
            if pattern.search(text):
                return True

        return False

    def _extract_filler_segments(
        self,
        segments: List[Dict[str, Any]]
    ) -> List[Tuple[int, int, str]]:
        """
        Extract filler word segments from transcription

        Args:
            segments: Transcription segments with timestamps

        Returns:
            List of tuples (start_ms, end_ms, text) for each filler word
        """
        filler_segments = []

        for segment in segments:
            text = segment.get("text", "").strip()
            start = segment.get("start", 0)
            end = segment.get("end", 0)

            # Convert seconds to milliseconds
            start_ms = int(start * 1000)
            end_ms = int(end * 1000)
            duration_ms = end_ms - start_ms

            # Skip segments that are too short
            if duration_ms < self.min_duration_ms:
                continue

            # Check if segment is a filler word
            if self._is_filler_word(text):
                logger.debug(f"Filler word detected: '{text}' at {start_ms}ms - {end_ms}ms")
                filler_segments.append((start_ms, end_ms, text))
                continue

            # For medium/high sensitivity, also check for partial matches in longer segments
            if self.sensitivity >= 0.5 and len(text.split()) > 1:
                # Split into words and check each one
                words = text.split()
                word_duration = duration_ms / len(words)

                for i, word in enumerate(words):
                    if self._is_filler_word(word):
                        # Estimate timestamp for this word
                        word_start_ms = start_ms + int(i * word_duration)
                        word_end_ms = word_start_ms + int(word_duration)

                        logger.debug(f"Partial filler detected: '{word}' at {word_start_ms}ms")
                        filler_segments.append((word_start_ms, word_end_ms, word))

        return filler_segments

    def detect_filler_words(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Detect filler words in audio file

        Args:
            audio_path: Path to audio file (WAV)
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with detection results
        """
        try:
            logger.info(f"Starting filler words detection: {audio_path}")

            if progress_callback:
                progress_callback(0, "Starting transcription for filler detection...")

            # Transcribe audio using Whisper
            transcription = self.whisper_service.transcribe_audio(
                audio_path,
                progress_callback=progress_callback
            )

            if progress_callback:
                progress_callback(80, "Analyzing transcription for hesitations...")

            # Extract filler word segments
            filler_segments = self._extract_filler_segments(transcription["segments"])

            if progress_callback:
                progress_callback(100, "Filler detection complete!")

            result = {
                "filler_periods": [(start, end) for start, end, _ in filler_segments],
                "filler_details": [
                    {
                        "start_ms": start,
                        "end_ms": end,
                        "text": text,
                        "duration_ms": end - start
                    }
                    for start, end, text in filler_segments
                ],
                "total_fillers": len(filler_segments),
                "transcription": transcription["text"],
                "language": transcription.get("language", self.language),
                "settings": {
                    "whisper_model": self.whisper_service.model_name,
                    "sensitivity": self.sensitivity,
                    "min_duration_ms": self.min_duration_ms
                }
            }

            logger.info(f"Filler detection complete: {len(filler_segments)} hesitations found")
            return result

        except Exception as e:
            logger.error(f"Error detecting filler words: {e}", exc_info=True)
            raise

    def detect_in_video(
        self,
        video_path: Path,
        audio_path: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Detect filler words in video using pre-extracted audio

        Args:
            video_path: Path to video file (for reference)
            audio_path: Path to extracted audio file
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with detection results
        """
        logger.info(f"Detecting filler words in video: {video_path}")

        result = self.detect_filler_words(audio_path, progress_callback)

        result["video_path"] = str(video_path)
        result["audio_path"] = str(audio_path)

        return result

    @staticmethod
    def merge_with_silences(
        silence_periods: List[Tuple[int, int]],
        filler_periods: List[Tuple[int, int]],
        padding: int = 100
    ) -> List[Tuple[int, int]]:
        """
        Merge silence periods and filler word periods into a unified cut list

        Args:
            silence_periods: List of (start_ms, end_ms) for silences
            filler_periods: List of (start_ms, end_ms) for filler words
            padding: Padding to add around cuts in ms

        Returns:
            Sorted list of merged periods to cut
        """
        # Combine both lists
        all_cuts = []

        for start, end in silence_periods:
            all_cuts.append((start, end, "silence"))

        for start, end in filler_periods:
            # Add padding around filler words
            padded_start = max(0, start - padding)
            padded_end = end + padding
            all_cuts.append((padded_start, padded_end, "filler"))

        # Sort by start time
        all_cuts.sort(key=lambda x: x[0])

        # Merge overlapping periods
        if not all_cuts:
            return []

        merged = []
        current_start, current_end, _ = all_cuts[0]

        for start, end, cut_type in all_cuts[1:]:
            if start <= current_end:
                # Overlapping, extend the current period
                current_end = max(current_end, end)
            else:
                # No overlap, save current and start new
                merged.append((current_start, current_end))
                current_start, current_end = start, end

        # Add the last period
        merged.append((current_start, current_end))

        logger.info(
            f"Merged {len(silence_periods)} silences + {len(filler_periods)} fillers "
            f"= {len(merged)} total cut periods"
        )

        return merged

    @staticmethod
    def get_non_cut_periods(
        cuts: List[Tuple[int, int]],
        total_duration_ms: int
    ) -> List[Tuple[int, int]]:
        """
        Convert cut periods to keep periods (inverse)

        Args:
            cuts: List of (start_ms, end_ms) to cut
            total_duration_ms: Total duration of video in milliseconds

        Returns:
            List of (start_ms, end_ms) to keep
        """
        if not cuts:
            return [(0, total_duration_ms)]

        keep_periods = []

        # Add segment from start to first cut
        if cuts[0][0] > 0:
            keep_periods.append((0, cuts[0][0]))

        # Add segments between cuts
        for i in range(len(cuts) - 1):
            gap_start = cuts[i][1]
            gap_end = cuts[i + 1][0]
            if gap_end > gap_start:
                keep_periods.append((gap_start, gap_end))

        # Add segment from last cut to end
        if cuts[-1][1] < total_duration_ms:
            keep_periods.append((cuts[-1][1], total_duration_ms))

        return keep_periods
