"""
Transcription formatting for various subtitle formats
"""
import logging
from pathlib import Path
from typing import List, Dict
import pysrt

logger = logging.getLogger(__name__)


class TranscriptionFormatter:
    """Formats transcription into various subtitle formats"""

    @staticmethod
    def to_srt(segments: List[Dict], output_path: Path) -> Path:
        """
        Export transcription to SRT format

        Args:
            segments: List of segments with start, end, text
            output_path: Output file path

        Returns:
            Path to created SRT file
        """
        subs = pysrt.SubRipFile()

        for idx, segment in enumerate(segments, 1):
            start_time = pysrt.SubRipTime(seconds=segment["start"])
            end_time = pysrt.SubRipTime(seconds=segment["end"])

            sub = pysrt.SubRipItem(
                index=idx,
                start=start_time,
                end=end_time,
                text=segment["text"]
            )
            subs.append(sub)

        subs.save(str(output_path), encoding='utf-8')
        logger.info(f"SRT file saved: {output_path}")
        return output_path

    @staticmethod
    def to_vtt(segments: List[Dict], output_path: Path) -> Path:
        """
        Export transcription to WebVTT format

        Args:
            segments: List of segments with start, end, text
            output_path: Output file path

        Returns:
            Path to created VTT file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")

            for segment in segments:
                start = TranscriptionFormatter._format_timestamp(segment["start"])
                end = TranscriptionFormatter._format_timestamp(segment["end"])
                f.write(f"{start} --> {end}\n")
                f.write(f"{segment['text']}\n\n")

        logger.info(f"VTT file saved: {output_path}")
        return output_path

    @staticmethod
    def to_txt(text: str, output_path: Path) -> Path:
        """
        Export transcription to plain text

        Args:
            text: Full transcription text
            output_path: Output file path

        Returns:
            Path to created TXT file
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)

        logger.info(f"TXT file saved: {output_path}")
        return output_path

    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to VTT timestamp (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"
