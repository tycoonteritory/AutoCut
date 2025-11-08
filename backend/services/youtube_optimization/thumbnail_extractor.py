"""
Thumbnail extraction from video using OpenCV
"""
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from PIL import Image
from ...config import settings

logger = logging.getLogger(__name__)


class ThumbnailExtractor:
    """Extracts potential thumbnail images from video"""

    def __init__(self):
        pass

    def extract_thumbnails(
        self,
        video_path: Path,
        output_dir: Path,
        num_thumbnails: int = None
    ) -> List[Dict[str, any]]:
        """
        Extract best thumbnail candidates from video

        Args:
            video_path: Path to video file
            output_dir: Directory to save thumbnails
            num_thumbnails: Number of thumbnails to extract

        Returns:
            List of thumbnail info dicts
        """
        num_thumbnails = num_thumbnails or settings.NUM_THUMBNAIL_SUGGESTIONS

        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            # Open video
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise RuntimeError(f"Failed to open video: {video_path}")

            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            logger.info(f"Video: {total_frames} frames, {fps} fps, {duration:.2f}s")

            # Sample frames evenly throughout video
            frame_indices = self._get_sample_indices(total_frames, num_thumbnails * 3)

            candidates = []

            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()

                if not ret:
                    continue

                # Score frame quality
                score = self._score_frame(frame)

                candidates.append({
                    "frame_index": idx,
                    "timestamp": idx / fps if fps > 0 else 0,
                    "frame": frame,
                    "score": score
                })

            cap.release()

            # Sort by score and keep top N
            candidates.sort(key=lambda x: x["score"], reverse=True)
            best_candidates = candidates[:num_thumbnails]

            # Save thumbnails
            thumbnails = []
            for i, candidate in enumerate(best_candidates, 1):
                filename = f"thumbnail_{i}.jpg"
                output_path = output_dir / filename

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(candidate["frame"], cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)

                # Resize to YouTube thumbnail size (1280x720)
                img = img.resize((1280, 720), Image.Resampling.LANCZOS)
                img.save(output_path, quality=95)

                thumbnails.append({
                    "index": i,
                    "timestamp": candidate["timestamp"],
                    "score": candidate["score"],
                    "path": str(output_path),
                    "filename": filename
                })

                logger.info(f"Saved thumbnail {i}: {output_path} (score: {candidate['score']:.2f})")

            return thumbnails

        except Exception as e:
            logger.error(f"Error extracting thumbnails: {e}", exc_info=True)
            raise

    def _get_sample_indices(self, total_frames: int, num_samples: int) -> List[int]:
        """Get evenly spaced frame indices"""
        # Skip first 5% and last 5% of video
        start = int(total_frames * 0.05)
        end = int(total_frames * 0.95)

        if end <= start:
            end = total_frames

        step = max(1, (end - start) // num_samples)
        return list(range(start, end, step))[:num_samples]

    def _score_frame(self, frame: np.ndarray) -> float:
        """
        Score frame quality for thumbnail suitability

        Criteria:
        - Sharpness (Laplacian variance)
        - Brightness (not too dark, not too bright)
        - Face detection (bonus if face detected)

        Returns:
            Score (higher is better)
        """
        score = 0.0

        # 1. Sharpness (Laplacian variance)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness_score = min(laplacian_var / 1000, 1.0)  # Normalize
        score += sharpness_score * 40  # 40 points max

        # 2. Brightness (optimal range 80-170)
        brightness = np.mean(gray)
        if 80 <= brightness <= 170:
            brightness_score = 1.0
        else:
            brightness_score = max(0, 1.0 - abs(brightness - 125) / 125)
        score += brightness_score * 30  # 30 points max

        # 3. Face detection (bonus)
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            if len(faces) > 0:
                score += 30  # 30 points bonus for faces
        except:
            pass  # Face detection is optional

        return score
