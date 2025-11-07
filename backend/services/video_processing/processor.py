"""
Main video processing service that orchestrates the entire workflow
"""
import logging
import asyncio
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from ..silence_detection.detector import SilenceDetector
from ..filler_words.detector import FillerWordsDetector
from ..export_formats.exporter import ExportService

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Orchestrates the complete video processing workflow"""

    def __init__(
        self,
        silence_thresh: int = -40,
        min_silence_len: int = 500,
        padding: int = 100,
        fps: int = 30,
        detect_filler_words: bool = False,
        filler_sensitivity: float = 0.7,
        whisper_model: str = "base",
        enable_audio_enhancement: bool = False,
        noise_reduction_strength: float = 0.7
    ):
        """
        Initialize video processor

        Args:
            silence_thresh: Silence threshold in dB
            min_silence_len: Minimum silence duration in ms
            padding: Padding around cuts in ms
            fps: Frames per second for export
            detect_filler_words: Enable filler words detection (euh, hum, etc.)
            filler_sensitivity: Filler detection sensitivity (0.0-1.0)
            whisper_model: Whisper model for filler detection (tiny, base, small)
            enable_audio_enhancement: Enable audio noise reduction before detection
            noise_reduction_strength: Noise reduction strength (0.0-1.0)
        """
        self.silence_detector = SilenceDetector(
            silence_thresh=silence_thresh,
            min_silence_len=min_silence_len,
            padding=padding,
            enable_audio_enhancement=enable_audio_enhancement,
            noise_reduction_strength=noise_reduction_strength
        )
        self.fps = fps
        self.detect_filler_words = detect_filler_words
        self.padding = padding

        # Initialize filler detector if enabled
        if detect_filler_words:
            self.filler_detector = FillerWordsDetector(
                whisper_model=whisper_model,
                language="fr",
                sensitivity=filler_sensitivity,
                min_duration_ms=100
            )
            logger.info("Filler words detection ENABLED")
        else:
            self.filler_detector = None
            logger.info("Filler words detection DISABLED")

    async def process_video(
        self,
        video_path: Path,
        output_dir: Path,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process video: detect silences and export cuts

        Args:
            video_path: Path to input video
            output_dir: Directory for output files
            progress_callback: Callback for progress updates (percentage, message)

        Returns:
            Dictionary with processing results
        """
        try:
            logger.info(f"Starting video processing: {video_path}")

            if progress_callback:
                await progress_callback(0, "Starting video analysis...")

            # Create a sync wrapper for the async callback to use in the detector
            loop = asyncio.get_event_loop()

            def sync_progress_callback(progress: float):
                if progress_callback:
                    # Use call_soon_threadsafe to schedule the callback from sync code
                    try:
                        # Determine message based on progress
                        if progress < 30:
                            message = "Extracting audio from video..."
                        elif progress < 40:
                            message = "Loading audio for analysis..."
                        elif progress < 60:
                            message = "Detecting silence periods..."
                        else:
                            message = "Analyzing video content..."

                        # Log for debugging
                        logger.info(f"Progress callback: {progress}% - {message}")

                        future = asyncio.run_coroutine_threadsafe(
                            progress_callback(progress, message),
                            loop
                        )
                        # Don't wait for result to avoid blocking
                    except Exception as e:
                        logger.error(f"Error in progress callback: {e}", exc_info=True)

            # Step 1: Analyze video and detect silences
            # Run in executor to avoid blocking the event loop
            analysis_result = await loop.run_in_executor(
                None,
                lambda: self.silence_detector.analyze_video(
                    video_path,
                    progress_callback=sync_progress_callback
                )
            )

            # Step 1.5: Detect filler words if enabled
            filler_result = None
            final_cuts = analysis_result['non_silent_periods']
            all_cuts = analysis_result['silence_periods']

            if self.detect_filler_words and self.filler_detector:
                if progress_callback:
                    await progress_callback(70, "Detecting verbal hesitations (euh, hum, etc.)...")

                logger.info("Starting filler words detection...")

                # Create async-compatible progress callback for filler detector
                async def filler_progress_callback(progress: float, message: str):
                    if progress_callback:
                        # Map filler detection progress to 70-85% range
                        adjusted_progress = 70 + (progress * 0.15)
                        await progress_callback(adjusted_progress, message)

                # Run filler detection in executor
                filler_result = await loop.run_in_executor(
                    None,
                    lambda: self.filler_detector.detect_in_video(
                        video_path,
                        Path(analysis_result['audio_path']),
                        progress_callback=None  # We'll handle progress separately
                    )
                )

                if progress_callback:
                    await progress_callback(85, f"Found {filler_result['total_fillers']} hesitations, merging results...")

                # Merge silence periods and filler word periods
                all_cuts = FillerWordsDetector.merge_with_silences(
                    silence_periods=analysis_result['silence_periods'],
                    filler_periods=filler_result['filler_periods'],
                    padding=self.padding
                )

                # Calculate kept periods (inverse of cuts)
                duration_ms = int(analysis_result['duration_seconds'] * 1000)
                final_cuts = FillerWordsDetector.get_non_cut_periods(all_cuts, duration_ms)

                logger.info(
                    f"Merged cuts: {len(analysis_result['silence_periods'])} silences + "
                    f"{filler_result['total_fillers']} fillers = {len(all_cuts)} total cuts"
                )

            if progress_callback:
                await progress_callback(88, "Generating export files...")

            # Step 2: Export to video editing formats
            # Use output_dir name as clean_name for export files
            clean_name = output_dir.name
            exporter = ExportService(video_path, self.fps, clean_name=clean_name)

            export_results = exporter.export_all(
                cuts=final_cuts,
                output_dir=output_dir,
                video_duration_seconds=analysis_result['duration_seconds']
            )

            if progress_callback:
                await progress_callback(90, "Exports generated...")

            # Calculate time statistics
            # Total duration of kept segments (final cuts after merging)
            kept_duration_ms = sum(end - start for start, end in final_cuts)
            kept_duration_seconds = kept_duration_ms / 1000.0

            # Total duration of removed segments (all cuts)
            removed_duration_ms = sum(end - start for start, end in all_cuts)
            removed_duration_seconds = removed_duration_ms / 1000.0

            # Percentage saved
            percentage_saved = (removed_duration_seconds / analysis_result['duration_seconds'] * 100) if analysis_result['duration_seconds'] > 0 else 0

            # Compile final result
            result = {
                'success': True,
                'video_path': str(video_path),
                'video_name': video_path.name,
                'duration_seconds': analysis_result['duration_seconds'],
                'total_cuts': len(final_cuts),
                'silence_periods_removed': len(analysis_result['silence_periods']),
                'kept_duration_seconds': kept_duration_seconds,
                'removed_duration_seconds': removed_duration_seconds,
                'percentage_saved': round(percentage_saved, 1),
                'cuts': final_cuts,
                'exports': {
                    'premiere_pro': str(export_results.get('premiere_pro')) if export_results.get('premiere_pro') else None,
                    'final_cut_pro': str(export_results.get('final_cut_pro')) if export_results.get('final_cut_pro') else None
                },
                'settings': analysis_result['settings']
            }

            # Add filler words info if detected
            if filler_result:
                result['filler_words_detected'] = filler_result['total_fillers']
                result['filler_details'] = filler_result['filler_details']
                result['settings']['filler_detection'] = {
                    'enabled': True,
                    'sensitivity': self.filler_detector.sensitivity,
                    'whisper_model': self.filler_detector.whisper_service.model_name
                }
            else:
                result['filler_words_detected'] = 0
                result['settings']['filler_detection'] = {
                    'enabled': False
                }

            if progress_callback:
                await progress_callback(100, "Processing complete!")

            logger.info("Video processing complete")
            return result

        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if progress_callback:
                await progress_callback(0, f"Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_path': str(video_path)
            }
