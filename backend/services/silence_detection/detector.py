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
import threading
import queue
from ..audio_enhancement.enhancer import AudioEnhancer

logger = logging.getLogger(__name__)


class SilenceDetector:
    """Detects silence periods in video/audio files"""

    def __init__(
        self,
        silence_thresh: int = -40,
        min_silence_len: int = 500,
        padding: int = 100,
        enable_audio_enhancement: bool = False,
        noise_reduction_strength: float = 0.7
    ):
        """
        Initialize silence detector

        Args:
            silence_thresh: Silence threshold in dB (default: -40)
            min_silence_len: Minimum silence length in ms (default: 500)
            padding: Padding around cuts in ms (default: 100)
            enable_audio_enhancement: Enable audio enhancement before detection
            noise_reduction_strength: Noise reduction strength (0.0-1.0)
        """
        self.silence_thresh = silence_thresh
        self.min_silence_len = min_silence_len
        self.padding = padding
        self.enable_audio_enhancement = enable_audio_enhancement

        # Initialize audio enhancer if enabled
        if enable_audio_enhancement:
            self.audio_enhancer = AudioEnhancer(
                noise_reduction_strength=noise_reduction_strength,
                normalize_audio=True
            )
            logger.info("Audio enhancement ENABLED")
        else:
            self.audio_enhancer = None
            logger.info("Audio enhancement DISABLED")

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
            universal_newlines=True,
            bufsize=1
        )

        # Create queues for thread-safe reading
        stdout_queue = queue.Queue()
        stderr_queue = queue.Queue()

        def read_stdout():
            """Read stdout in a separate thread to prevent blocking"""
            try:
                for line in process.stdout:
                    stdout_queue.put(line)
            except Exception as e:
                logger.error(f"Error reading stdout: {e}")
            finally:
                process.stdout.close()

        def read_stderr():
            """Read stderr in a separate thread to prevent buffer overflow"""
            try:
                for line in process.stderr:
                    stderr_queue.put(line)
            except Exception as e:
                logger.error(f"Error reading stderr: {e}")
            finally:
                process.stderr.close()

        # Start threads to read stdout and stderr
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()

        # Monitor progress from stdout queue
        while process.poll() is None or not stdout_queue.empty():
            try:
                line = stdout_queue.get(timeout=0.1)
                if line.startswith('out_time_ms='):
                    try:
                        time_ms = int(line.split('=')[1]) / 1000000  # Convert to seconds
                        if duration > 0 and progress_callback:
                            progress = min((time_ms / duration) * 30, 30)  # 0-30% for audio extraction
                            progress_callback(progress)
                    except (ValueError, IndexError):
                        pass
            except queue.Empty:
                continue

        # Wait for process to complete
        process.wait()

        # Wait for threads to finish
        stdout_thread.join(timeout=1)
        stderr_thread.join(timeout=1)

        if process.returncode != 0:
            # Collect all stderr messages
            stderr_lines = []
            while not stderr_queue.empty():
                try:
                    stderr_lines.append(stderr_queue.get_nowait())
                except queue.Empty:
                    break
            error = ''.join(stderr_lines)
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
        # Use seek_step=10 for good balance between speed and accuracy (10ms precision)
        silence_periods = detect_silence(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=10  # Check every 10ms - much faster while maintaining precision
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
        # Use seek_step=10 for good balance between speed and accuracy (10ms precision)
        non_silent_periods = detect_nonsilent(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh,
            seek_step=10  # Check every 10ms - much faster while maintaining precision
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

        # Enhance audio if enabled
        if self.enable_audio_enhancement and self.audio_enhancer:
            logger.info("Applying audio enhancement...")
            if progress_callback:
                progress_callback(32)

            try:
                # Enhance the audio before detection
                audio_path = self.audio_enhancer.enhance_for_silence_detection(
                    audio_path,
                    progress_callback=progress_callback
                )
                logger.info(f"Audio enhanced: {audio_path}")
            except Exception as e:
                logger.error(f"Audio enhancement failed: {e}, continuing with original audio", exc_info=True)
                # Continue with original audio if enhancement fails

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
