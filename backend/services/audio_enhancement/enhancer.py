"""
Audio enhancement service for noise reduction and audio cleanup
"""
import logging
from pathlib import Path
from typing import Optional, Callable
import numpy as np
import librosa
import soundfile as sf
import noisereduce as nr

logger = logging.getLogger(__name__)


class AudioEnhancer:
    """Enhances audio quality through noise reduction and normalization"""

    def __init__(
        self,
        noise_reduction_strength: float = 0.7,
        normalize_audio: bool = True,
        target_sample_rate: int = 44100
    ):
        """
        Initialize audio enhancer

        Args:
            noise_reduction_strength: Strength of noise reduction (0.0-1.0)
            normalize_audio: Whether to normalize audio levels
            target_sample_rate: Target sample rate for output audio
        """
        self.noise_reduction_strength = noise_reduction_strength
        self.normalize_audio = normalize_audio
        self.target_sample_rate = target_sample_rate

        logger.info(
            f"AudioEnhancer initialized (noise_reduction: {noise_reduction_strength}, "
            f"normalize: {normalize_audio})"
        )

    def reduce_noise(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        stationary: bool = True
    ) -> np.ndarray:
        """
        Apply noise reduction to audio data

        Args:
            audio_data: Audio samples as numpy array
            sample_rate: Sample rate of audio
            stationary: Whether to use stationary noise reduction

        Returns:
            Noise-reduced audio data
        """
        logger.info("Applying noise reduction...")

        try:
            # Apply noise reduction using noisereduce
            reduced_audio = nr.reduce_noise(
                y=audio_data,
                sr=sample_rate,
                stationary=stationary,
                prop_decrease=self.noise_reduction_strength
            )

            logger.info("Noise reduction complete")
            return reduced_audio

        except Exception as e:
            logger.error(f"Error during noise reduction: {e}", exc_info=True)
            logger.warning("Returning original audio without noise reduction")
            return audio_data

    def normalize_audio_levels(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Normalize audio levels to prevent clipping and ensure consistent volume

        Args:
            audio_data: Audio samples as numpy array

        Returns:
            Normalized audio data
        """
        logger.info("Normalizing audio levels...")

        try:
            # Calculate peak value
            peak = np.abs(audio_data).max()

            if peak > 0:
                # Normalize to 90% of maximum to prevent clipping
                normalized = audio_data * (0.9 / peak)
                logger.info(f"Audio normalized (peak: {peak:.3f} -> 0.9)")
                return normalized
            else:
                logger.warning("Audio has no signal, skipping normalization")
                return audio_data

        except Exception as e:
            logger.error(f"Error during normalization: {e}", exc_info=True)
            return audio_data

    def enhance_audio_file(
        self,
        input_path: Path,
        output_path: Optional[Path] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> Path:
        """
        Enhance audio file with noise reduction and normalization

        Args:
            input_path: Path to input audio file (WAV)
            output_path: Path for output file (default: input_path with _enhanced suffix)
            progress_callback: Callback for progress updates

        Returns:
            Path to enhanced audio file
        """
        try:
            logger.info(f"Enhancing audio file: {input_path}")

            if progress_callback:
                progress_callback(0, "Loading audio file...")

            # Load audio file
            audio_data, sample_rate = librosa.load(
                str(input_path),
                sr=self.target_sample_rate,
                mono=False  # Keep stereo if available
            )

            if progress_callback:
                progress_callback(20, "Audio loaded, applying noise reduction...")

            # Handle stereo audio
            if len(audio_data.shape) > 1:
                # Process each channel separately
                logger.info("Processing stereo audio (2 channels)")
                enhanced_channels = []

                for i, channel in enumerate(audio_data):
                    if progress_callback:
                        progress_callback(
                            20 + (i * 30),
                            f"Processing channel {i + 1}/2..."
                        )

                    # Apply noise reduction
                    enhanced_channel = self.reduce_noise(channel, sample_rate)

                    # Normalize if enabled
                    if self.normalize_audio:
                        enhanced_channel = self.normalize_audio_levels(enhanced_channel)

                    enhanced_channels.append(enhanced_channel)

                enhanced_audio = np.array(enhanced_channels)

            else:
                # Mono audio
                logger.info("Processing mono audio")

                if progress_callback:
                    progress_callback(20, "Reducing noise...")

                # Apply noise reduction
                enhanced_audio = self.reduce_noise(audio_data, sample_rate)

                if progress_callback:
                    progress_callback(60, "Normalizing audio levels...")

                # Normalize if enabled
                if self.normalize_audio:
                    enhanced_audio = self.normalize_audio_levels(enhanced_audio)

            if progress_callback:
                progress_callback(80, "Saving enhanced audio...")

            # Determine output path
            if output_path is None:
                output_path = input_path.parent / f"{input_path.stem}_enhanced.wav"

            # Save enhanced audio
            sf.write(
                str(output_path),
                enhanced_audio.T if len(enhanced_audio.shape) > 1 else enhanced_audio,
                sample_rate,
                subtype='PCM_16'
            )

            if progress_callback:
                progress_callback(100, "Enhancement complete!")

            logger.info(f"Enhanced audio saved to: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error enhancing audio: {e}", exc_info=True)
            raise

    def enhance_for_silence_detection(
        self,
        input_path: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Path:
        """
        Enhance audio specifically for better silence detection

        Args:
            input_path: Path to input audio file
            progress_callback: Callback for progress updates (0-100)

        Returns:
            Path to enhanced audio file
        """
        logger.info("Enhancing audio for silence detection")

        # Wrapper for progress callback to match signature
        def wrapped_callback(progress: float, message: str):
            if progress_callback:
                progress_callback(progress)

        return self.enhance_audio_file(
            input_path,
            output_path=input_path.parent / f"{input_path.stem}_enhanced.wav",
            progress_callback=wrapped_callback
        )
