"""
Premiere Pro XML export module
Generates .xml files compatible with Adobe Premiere Pro
"""
import xml.etree.ElementTree as ET
from typing import List, Tuple
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PremiereProExporter:
    """Exports cut information to Premiere Pro XML format"""

    def __init__(self, video_path: Path, fps: int = 30):
        """
        Initialize Premiere Pro exporter

        Args:
            video_path: Path to source video
            fps: Frames per second (default: 30)
        """
        self.video_path = video_path
        self.fps = fps
        self.timebase = fps

    def ms_to_frames(self, milliseconds: int) -> int:
        """Convert milliseconds to frames"""
        return int((milliseconds / 1000.0) * self.fps)

    def generate_xml(
        self,
        cuts: List[Tuple[int, int]],
        output_path: Path,
        video_duration_seconds: float
    ) -> Path:
        """
        Generate Premiere Pro XML file

        Args:
            cuts: List of (start_ms, end_ms) tuples for each non-silent segment
            output_path: Output path for XML file
            video_duration_seconds: Total video duration in seconds

        Returns:
            Path to generated XML file
        """
        logger.info(f"Generating Premiere Pro XML with {len(cuts)} cuts")

        # Create root element
        xmeml = ET.Element('xmeml', version='5')

        # Add sequence
        sequence = ET.SubElement(xmeml, 'sequence')

        # Sequence metadata
        ET.SubElement(sequence, 'name').text = f"AutoCut_{self.video_path.stem}"
        ET.SubElement(sequence, 'duration').text = str(self.ms_to_frames(int(video_duration_seconds * 1000)))

        # Rate (fps)
        rate = ET.SubElement(sequence, 'rate')
        ET.SubElement(rate, 'timebase').text = str(self.timebase)
        ET.SubElement(rate, 'ntsc').text = 'FALSE'

        # Media
        media = ET.SubElement(sequence, 'media')

        # Video track
        video = ET.SubElement(media, 'video')
        video_track = ET.SubElement(video, 'track')

        # Audio track
        audio = ET.SubElement(media, 'audio')
        audio_track = ET.SubElement(audio, 'track')

        # Add clips for each non-silent segment
        # Place clips continuously on timeline (no gaps)
        timeline_position = 0

        for idx, (start_ms, end_ms) in enumerate(cuts):
            source_in_frame = self.ms_to_frames(start_ms)
            source_out_frame = self.ms_to_frames(end_ms)
            duration_frames = source_out_frame - source_in_frame

            # Video clip
            video_clip = self._create_clip(
                idx + 1,
                source_in_frame,
                source_out_frame,
                duration_frames,
                timeline_position,
                'video'
            )
            video_track.append(video_clip)

            # Audio clip
            audio_clip = self._create_clip(
                idx + 1,
                source_in_frame,
                source_out_frame,
                duration_frames,
                timeline_position,
                'audio'
            )
            audio_track.append(audio_clip)

            # Move timeline position forward (no gap)
            timeline_position += duration_frames

        # Write XML to file
        tree = ET.ElementTree(xmeml)
        ET.indent(tree, space='  ')
        tree.write(str(output_path), encoding='utf-8', xml_declaration=True)

        logger.info(f"Premiere Pro XML saved to {output_path}")
        return output_path

    def _create_clip(
        self,
        clip_id: int,
        source_in_frame: int,
        source_out_frame: int,
        duration_frames: int,
        timeline_position: int,
        media_type: str
    ) -> ET.Element:
        """Create a clip element for the XML"""
        clip_item = ET.Element('clipitem', id=f"{media_type}-{clip_id}")

        ET.SubElement(clip_item, 'name').text = f"{self.video_path.name}_segment_{clip_id}"
        ET.SubElement(clip_item, 'duration').text = str(duration_frames)

        # Rate
        rate = ET.SubElement(clip_item, 'rate')
        ET.SubElement(rate, 'timebase').text = str(self.timebase)
        ET.SubElement(rate, 'ntsc').text = 'FALSE'

        # Timeline placement (continuous, no gaps)
        ET.SubElement(clip_item, 'start').text = str(timeline_position)
        ET.SubElement(clip_item, 'end').text = str(timeline_position + duration_frames)

        # Source in/out points (where to read from the source video)
        ET.SubElement(clip_item, 'in').text = str(source_in_frame)
        ET.SubElement(clip_item, 'out').text = str(source_out_frame)

        # File reference
        file_elem = ET.SubElement(clip_item, 'file', id=f"file-{clip_id}")
        ET.SubElement(file_elem, 'name').text = self.video_path.name
        ET.SubElement(file_elem, 'pathurl').text = f"file://localhost/{self.video_path.as_posix()}"

        # Rate for file
        rate = ET.SubElement(file_elem, 'rate')
        ET.SubElement(rate, 'timebase').text = str(self.timebase)
        ET.SubElement(rate, 'ntsc').text = 'FALSE'

        # Media
        media = ET.SubElement(file_elem, 'media')
        media_elem = ET.SubElement(media, media_type)

        # Sample characteristics
        characteristics = ET.SubElement(media_elem, 'samplecharacteristics')
        rate = ET.SubElement(characteristics, 'rate')
        ET.SubElement(rate, 'timebase').text = str(self.timebase)
        ET.SubElement(rate, 'ntsc').text = 'FALSE'

        if media_type == 'video':
            ET.SubElement(characteristics, 'width').text = '1920'
            ET.SubElement(characteristics, 'height').text = '1080'
        else:
            ET.SubElement(characteristics, 'depth').text = '16'
            ET.SubElement(characteristics, 'samplerate').text = '48000'

        return clip_item
