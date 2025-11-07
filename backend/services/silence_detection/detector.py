"""
Silence detection service using pydub and FFmpeg
"""
import logging
from typing import List, Tuple, Callable, Optional
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_silence, detect_nonsilent
import subprocess
import json

logger = logging.getLogger(__name__)


class SilenceDetector:
    """Detects silence periods in video/audio files"""

    def __init__(
        self,
        silence_thresh: int = -40,
        min_silence_len: int = 500,
        padding: int = 100
    ):
        """
        Initialize silence detector

        Args:
            silence_thresh: Silence threshold in dB (default: -40)
            min_silence_len: Minimum silence length in ms (default: 500)
            padding: Padding around cuts in ms (default: 100)
        """
        self.silence_thresh = silence_thresh
        self.min_silence_len = min_silence_len
        self.padding = padding

    def extract_audio(
        self,
        video_path: Path,
        output_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Path:
        """
        Extract audio from video file using FFmpeg

        Args:
            video_path: Path to video file
            output_path: Output path for audio file
            progress_callback: Callback for progress updates

        Returns:
            Path to extracted audio file
        """
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_audio.wav"

        # Get video duration first
        duration = self._get_video_duration(video_path)

        logger.info(f"Extracting audio from {video_path}")

        # Extract audio using FFmpeg with progress
        cmd = [
            'ffmpeg',
            '-i', str(video_path),
            '-vn',  # No video
            '-acodec', 'pcm_s16le',  # PCM 16-bit
            '-ar', '44100',  # 44.1kHz sample rate
            '-ac', '2',  # Stereo
            '-y',  # Overwrite output file
            '-progress', 'pipe:1',  # Progress to stdout
            str(output_path)
        ]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Monitor progress
        for line in process.stdout:
            if line.startswith('out_time_ms='):
                try:
                    time_ms = int(line.split('=')[1]) / 1000000  # Convert to seconds
                    if duration > 0 and progress_callback:
                        progress = min((time_ms / duration) * 30, 30)  # 0-30% for audio extraction
                        progress_callback(progress)
                except (ValueError, IndexError):
                    pass

        process.wait()

        if process.returncode != 0:
            error = process.stderr.read()
            raise RuntimeError(f"Failed to extract audio: {error}")

        logger.info(f"Audio extracted to {output_path}")
        return output_path

    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds using FFprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'json',
            str(video_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return float(data['format']['duration'])

    def detect_silence_periods(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Tuple[int, int]]:
        """
        Detect silence periods in audio file

        Args:
            audio_path: Path to audio file
            progress_callback: Callback for progress updates

        Returns:
            List of tuples (start_ms, end_ms) for each silence period
        """
        logger.info(f"Loading audio file: {audio_path}")
        if progress_callback:
            progress_callback(32)

        # Load audio file
        audio = AudioSegment.from_wav(str(audio_path))

        if progress_callback:
            progress_callback(35)

        logger.info(f"Detecting silence (threshold: {self.silence_thresh}dB, min: {self.min_silence_len}ms)")

        if progress_callback:
            progress_callback(40)

        # Detect silence (this can take time for large files)
        silence_periods = detect_silence(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=1  # Check every 1ms for accuracy
        )

        if progress_callback:
            progress_callback(48)

        logger.info(f"Found {len(silence_periods)} silence periods")
        return silence_periods

    def detect_non_silent_periods(
        self,
        audio_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> List[Tuple[int, int]]:
        """
        Detect non-silent (audio content) periods

        Args:
            audio_path: Path to audio file
            progress_callback: Callback for progress updates

        Returns:
            List of tuples (start_ms, end_ms) for each non-silent period
        """
        logger.info(f"Loading audio file: {audio_path}")
        if progress_callback:
            progress_callback(50)

        # Load audio file
        audio = AudioSegment.from_wav(str(audio_path))

        if progress_callback:
            progress_callback(53)

        logger.info(f"Detecting non-silent periods (threshold: {self.silence_thresh}dB, min: {self.min_silence_len}ms)")

        if progress_callback:
            progress_callback(56)

        # Detect non-silent periods (this can take time for large files)
        non_silent_periods = detect_nonsilent(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=1
        )

        if progress_callback:
            progress_callback(68)

        logger.info(f"Found {len(non_silent_periods)} non-silent periods")
        return non_silent_periods

    def analyze_video(
        self,
        video_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> dict:
        """
        Complete analysis of video file

        Args:
            video_path: Path to video file
            progress_callback: Callback for progress updates

        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Starting video analysis: {video_path}")

        # Extract audio
        audio_path = self.extract_audio(video_path, progress_callback=progress_callback)

        # Detect silence
        silence_periods = self.detect_silence_periods(audio_path, progress_callback=progress_callback)

        # Detect non-silent periods
        non_silent_periods = self.detect_non_silent_periods(audio_path, progress_callback=progress_callback)

        # Get video metadata
        duration = self._get_video_duration(video_path)

        if progress_callback:
            progress_callback(70)

        result = {
            'video_path': str(video_path),
            'duration_seconds': duration,
            'audio_path': str(audio_path),
            'silence_periods': silence_periods,
            'non_silent_periods': non_silent_periods,
            'total_silence_periods': len(silence_periods),
            'total_non_silent_periods': len(non_silent_periods),
            'settings': {
                'silence_threshold_db': self.silence_thresh,
                'min_silence_duration_ms': self.min_silence_len,
                'padding_ms': self.padding
            }
        }

        logger.info("Video analysis complete")
        return result
