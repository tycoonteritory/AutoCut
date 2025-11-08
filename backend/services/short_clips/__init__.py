"""
Short clips generation service
"""
from .clip_detector import ClipDetector
from .clip_extractor import ClipExtractor
from .local_clip_scorer import LocalClipScorer

__all__ = ['ClipDetector', 'ClipExtractor', 'LocalClipScorer']
