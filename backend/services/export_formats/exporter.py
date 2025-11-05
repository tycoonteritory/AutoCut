"""
Main export service that coordinates all export formats
"""
from pathlib import Path
from typing import List, Tuple, Dict
import logging
from .premiere_pro import PremiereProExporter
from .final_cut_pro import FinalCutProExporter

logger = logging.getLogger(__name__)


class ExportService:
    """Coordinates export to different video editing formats"""

    def __init__(self, video_path: Path, fps: int = 30):
        """
        Initialize export service

        Args:
            video_path: Path to source video
            fps: Frames per second (default: 30)
        """
        self.video_path = video_path
        self.fps = fps
        self.premiere_exporter = PremiereProExporter(video_path, fps)
        self.fcpx_exporter = FinalCutProExporter(video_path, fps)

    def export_all(
        self,
        cuts: List[Tuple[int, int]],
        output_dir: Path,
        video_duration_seconds: float
    ) -> Dict[str, Path]:
        """
        Export to all supported formats

        Args:
            cuts: List of (start_ms, end_ms) tuples for each non-silent segment
            output_dir: Output directory for XML files
            video_duration_seconds: Total video duration in seconds

        Returns:
            Dictionary with format names and paths to generated files
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        # Export to Premiere Pro
        try:
            premiere_path = output_dir / f"{self.video_path.stem}_premiere_pro.xml"
            self.premiere_exporter.generate_xml(cuts, premiere_path, video_duration_seconds)
            results['premiere_pro'] = premiere_path
            logger.info(f"Premiere Pro export complete: {premiere_path}")
        except Exception as e:
            logger.error(f"Failed to export Premiere Pro XML: {e}")
            results['premiere_pro'] = None

        # Export to Final Cut Pro X
        try:
            fcpx_path = output_dir / f"{self.video_path.stem}_final_cut_pro.fcpxml"
            self.fcpx_exporter.generate_xml(cuts, fcpx_path, video_duration_seconds)
            results['final_cut_pro'] = fcpx_path
            logger.info(f"Final Cut Pro export complete: {fcpx_path}")
        except Exception as e:
            logger.error(f"Failed to export Final Cut Pro XML: {e}")
            results['final_cut_pro'] = None

        return results

    def export_premiere_pro(
        self,
        cuts: List[Tuple[int, int]],
        output_path: Path,
        video_duration_seconds: float
    ) -> Path:
        """Export to Premiere Pro XML format"""
        return self.premiere_exporter.generate_xml(cuts, output_path, video_duration_seconds)

    def export_final_cut_pro(
        self,
        cuts: List[Tuple[int, int]],
        output_path: Path,
        video_duration_seconds: float
    ) -> Path:
        """Export to Final Cut Pro X XML format"""
        return self.fcpx_exporter.generate_xml(cuts, output_path, video_duration_seconds)
