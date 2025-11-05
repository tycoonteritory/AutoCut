"""
Main video processing service that orchestrates the entire workflow
"""
import logging
from pathlib import Path
from typing import Callable, Optional, Dict, Any
from ..silence_detection.detector import SilenceDetector
from ..export_formats.exporter import ExportService

logger = logging.getLogger(__name__)


class VideoProcessor:
    """Orchestrates the complete video processing workflow"""

    def __init__(
        self,
        silence_thresh: int = -40,
        min_silence_len: int = 500,
        padding: int = 100,
        fps: int = 30
    ):
        """
        Initialize video processor

        Args:
            silence_thresh: Silence threshold in dB
            min_silence_len: Minimum silence duration in ms
            padding: Padding around cuts in ms
            fps: Frames per second for export
        """
        self.silence_detector = SilenceDetector(
            silence_thresh=silence_thresh,
            min_silence_len=min_silence_len,
            padding=padding
        )
        self.fps = fps

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
                progress_callback(0, "Starting video analysis...")

            # Step 1: Analyze video and detect silences
            analysis_result = self.silence_detector.analyze_video(
                video_path,
                progress_callback=lambda p: progress_callback(p, "Analyzing video...") if progress_callback else None
            )

            if progress_callback:
                progress_callback(70, "Analysis complete, generating exports...")

            # Step 2: Export to video editing formats
            exporter = ExportService(video_path, self.fps)

            export_results = exporter.export_all(
                cuts=analysis_result['non_silent_periods'],
                output_dir=output_dir,
                video_duration_seconds=analysis_result['duration_seconds']
            )

            if progress_callback:
                progress_callback(90, "Exports generated...")

            # Compile final result
            result = {
                'success': True,
                'video_path': str(video_path),
                'video_name': video_path.name,
                'duration_seconds': analysis_result['duration_seconds'],
                'total_cuts': len(analysis_result['non_silent_periods']),
                'silence_periods_removed': len(analysis_result['silence_periods']),
                'cuts': analysis_result['non_silent_periods'],
                'exports': {
                    'premiere_pro': str(export_results.get('premiere_pro')) if export_results.get('premiere_pro') else None,
                    'final_cut_pro': str(export_results.get('final_cut_pro')) if export_results.get('final_cut_pro') else None
                },
                'settings': analysis_result['settings']
            }

            if progress_callback:
                progress_callback(100, "Processing complete!")

            logger.info("Video processing complete")
            return result

        except Exception as e:
            logger.error(f"Error processing video: {e}", exc_info=True)
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'video_path': str(video_path)
            }
