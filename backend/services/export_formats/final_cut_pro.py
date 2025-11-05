"""
Final Cut Pro XML export module
Generates .fcpxml files compatible with Final Cut Pro X
"""
import xml.etree.ElementTree as ET
from typing import List, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FinalCutProExporter:
    """Exports cut information to Final Cut Pro X XML format (FCPXML)"""

    def __init__(self, video_path: Path, fps: int = 30):
        """
        Initialize Final Cut Pro exporter

        Args:
            video_path: Path to source video
            fps: Frames per second (default: 30)
        """
        self.video_path = video_path
        self.fps = fps

    def ms_to_seconds(self, milliseconds: int) -> str:
        """Convert milliseconds to seconds string with precision"""
        return f"{milliseconds / 1000:.3f}s"

    def generate_xml(
        self,
        cuts: List[Tuple[int, int]],
        output_path: Path,
        video_duration_seconds: float
    ) -> Path:
        """
        Generate Final Cut Pro XML file

        Args:
            cuts: List of (start_ms, end_ms) tuples for each non-silent segment
            output_path: Output path for FCPXML file
            video_duration_seconds: Total video duration in seconds

        Returns:
            Path to generated XML file
        """
        logger.info(f"Generating Final Cut Pro XML with {len(cuts)} cuts")

        # Create root element with FCPXML namespace
        fcpxml = ET.Element('fcpxml', version='1.9')

        # Add resources
        resources = ET.SubElement(fcpxml, 'resources')

        # Format resource
        format_elem = ET.SubElement(
            resources,
            'format',
            id='r1',
            name='FFVideoFormat1080p30',
            frameDuration=f'1/{self.fps}s',
            width='1920',
            height='1080'
        )

        # Asset resource (video file)
        asset = ET.SubElement(
            resources,
            'asset',
            id='r2',
            name=self.video_path.stem,
            start='0s',
            duration=f"{video_duration_seconds:.3f}s",
            hasVideo='1',
            hasAudio='1'
        )

        # Add media-rep child element (required by DTD)
        media_rep = ET.SubElement(
            asset,
            'media-rep',
            kind='original-media',
            src=f"file:///{self.video_path.as_posix()}"
        )

        # Library
        library = ET.SubElement(fcpxml, 'library')
        event = ET.SubElement(library, 'event', name='AutoCut')
        project = ET.SubElement(event, 'project', name=f"AutoCut_{self.video_path.stem}")

        # Sequence
        sequence = ET.SubElement(
            project,
            'sequence',
            format='r1',
            duration=f"{video_duration_seconds:.3f}s"
        )

        # Spine (main timeline)
        spine = ET.SubElement(sequence, 'spine')

        # Add clips for each non-silent segment
        for idx, (start_ms, end_ms) in enumerate(cuts):
            start_time = self.ms_to_seconds(start_ms)
            duration = self.ms_to_seconds(end_ms - start_ms)

            # Asset clip
            asset_clip = ET.SubElement(
                spine,
                'asset-clip',
                name=f"Segment {idx + 1}",
                ref='r2',
                offset=start_time,
                duration=duration,
                start=start_time,
                format='r1'
            )

        # Write XML to file
        tree = ET.ElementTree(fcpxml)
        ET.indent(tree, space='  ')
        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)

        logger.info(f"Final Cut Pro XML saved to {output_path}")
        return output_path
