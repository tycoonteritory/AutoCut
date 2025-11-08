"""
Service de rendu de sous-titres animés pour vidéos shorts (9:16)
Optimisé pour les réseaux sociaux (TikTok, Instagram Reels, YouTube Shorts)
"""
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import re

logger = logging.getLogger(__name__)


class AnimatedSubtitleRenderer:
    """Génère et intègre des sous-titres animés dans les vidéos shorts"""

    def __init__(self):
        # Initialiser les styles avec les presets
        self.styles = {
            "default": {
                "font": "Arial",
                "font_size": 22,  # Grande taille pour mobile
                "primary_color": "&H00FFFFFF",  # Blanc
                "secondary_color": "&H00FFFF00",  # Jaune pour emphase
                "outline_color": "&H00000000",  # Noir
                "back_color": "&H80000000",  # Fond noir semi-transparent
                "bold": True,
                "outline": 3,  # Contour épais pour lisibilité
                "shadow": 2,
                "alignment": 2,  # Centre-bas
                "margin_v": 80,  # Marge verticale depuis le bas
            },
            "tiktok": SubtitleStylePresets.get_tiktok_style(),
            "instagram": SubtitleStylePresets.get_instagram_style(),
            "youtube": SubtitleStylePresets.get_youtube_shorts_style()
        }

    async def add_subtitles_to_video(
        self,
        video_path: Path,
        output_path: Path,
        segments: List[Dict[str, Any]],
        start_offset: float = 0,
        duration: Optional[float] = None,
        style_name: str = "default",
        position: str = "bottom"  # "bottom", "top", "center"
    ) -> bool:
        """
        Ajoute des sous-titres animés à une vidéo

        Args:
            video_path: Chemin de la vidéo source
            output_path: Chemin de sortie
            segments: Segments de transcription avec start, end, text
            start_offset: Offset temporel pour synchroniser avec le clip
            duration: Durée du clip (pour filtrer les segments)
            style_name: Style de sous-titres ("default" ou "emphasized")
            position: Position des sous-titres

        Returns:
            True si succès, False sinon
        """
        try:
            # Ajuster l'alignement selon la position
            if position == "top":
                self.styles[style_name]["alignment"] = 8  # Centre-haut
                self.styles[style_name]["margin_v"] = 100
            elif position == "center":
                self.styles[style_name]["alignment"] = 5  # Centre
                self.styles[style_name]["margin_v"] = 0
            else:  # bottom
                self.styles[style_name]["alignment"] = 2  # Centre-bas
                self.styles[style_name]["margin_v"] = 80

            # Filtrer et ajuster les segments pour le clip
            adjusted_segments = self._adjust_segments_for_clip(
                segments, start_offset, duration
            )

            if not adjusted_segments:
                logger.warning("Aucun segment de sous-titres pour ce clip")
                return False

            # Optimiser les segments pour l'affichage (césures, longueur)
            optimized_segments = self._optimize_segments_for_display(adjusted_segments)

            # Générer le fichier ASS
            ass_path = output_path.parent / f"{output_path.stem}_subtitles.ass"
            self._generate_ass_file(optimized_segments, ass_path, style_name)

            # Intégrer les sous-titres avec FFmpeg
            success = await self._burn_subtitles(video_path, output_path, ass_path)

            # Nettoyer le fichier ASS temporaire
            if ass_path.exists():
                ass_path.unlink()

            return success

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout des sous-titres: {e}", exc_info=True)
            return False

    def _adjust_segments_for_clip(
        self,
        segments: List[Dict[str, Any]],
        start_offset: float,
        duration: Optional[float]
    ) -> List[Dict[str, Any]]:
        """
        Ajuste les timestamps des segments pour correspondre au clip extrait

        Args:
            segments: Segments originaux
            start_offset: Temps de début du clip dans la vidéo originale
            duration: Durée du clip

        Returns:
            Segments ajustés
        """
        adjusted = []
        end_time = start_offset + duration if duration else float('inf')

        for segment in segments:
            seg_start = segment["start"]
            seg_end = segment["end"]

            # Vérifier si le segment chevauche le clip
            if seg_end < start_offset or seg_start > end_time:
                continue

            # Ajuster les timestamps
            new_start = max(0, seg_start - start_offset)
            new_end = min(seg_end - start_offset, duration if duration else seg_end)

            if new_end > new_start:
                adjusted.append({
                    "start": new_start,
                    "end": new_end,
                    "text": segment["text"]
                })

        return adjusted

    def _optimize_segments_for_display(
        self,
        segments: List[Dict[str, Any]],
        max_chars_per_line: int = 35,
        max_lines: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Optimise les segments pour l'affichage mobile

        Args:
            segments: Segments à optimiser
            max_chars_per_line: Nombre max de caractères par ligne
            max_lines: Nombre max de lignes

        Returns:
            Segments optimisés avec césures intelligentes
        """
        optimized = []

        for segment in segments:
            text = segment["text"].strip()

            # Appliquer les césures intelligentes
            formatted_text = self._smart_line_breaks(text, max_chars_per_line, max_lines)

            # Détection de mots clés pour emphase (optionnel)
            formatted_text = self._add_emphasis_tags(formatted_text)

            optimized.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": formatted_text
            })

        return optimized

    def _smart_line_breaks(
        self,
        text: str,
        max_chars_per_line: int,
        max_lines: int
    ) -> str:
        """
        Applique des césures intelligentes au texte

        Args:
            text: Texte à formatter
            max_chars_per_line: Caractères max par ligne
            max_lines: Lignes max

        Returns:
            Texte avec césures optimales
        """
        if len(text) <= max_chars_per_line:
            return text

        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            if current_length + word_length + len(current_line) <= max_chars_per_line:
                current_line.append(word)
                current_length += word_length
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
                current_length = word_length

                if len(lines) >= max_lines:
                    break

        if current_line and len(lines) < max_lines:
            lines.append(" ".join(current_line))

        return "\\N".join(lines)  # \\N = saut de ligne en ASS

    def _add_emphasis_tags(self, text: str) -> str:
        """
        Ajoute des tags d'emphase sur certains mots clés

        Args:
            text: Texte à analyser

        Returns:
            Texte avec tags ASS pour emphase
        """
        # Mots clés à emphasiser (émotions fortes, exclamations)
        emphasis_patterns = [
            r'\b(incroyable|génial|super|wow|amazing|parfait)\b',
            r'\b(important|crucial|essentiel|clé)\b',
            r'\b(attention|danger|warning|alerte)\b',
        ]

        result = text
        for pattern in emphasis_patterns:
            # Tag ASS pour couleur: {\c&HBBGGRR&} où RR=rouge, GG=vert, BB=bleu
            # Jaune vif: &H00FFFF
            result = re.sub(
                pattern,
                r'{\\c&H00FFFF&\\b1}\1{\\r}',  # \\r = reset au style par défaut
                result,
                flags=re.IGNORECASE
            )

        return result

    def _generate_ass_file(
        self,
        segments: List[Dict[str, Any]],
        output_path: Path,
        style_name: str = "default"
    ) -> None:
        """
        Génère un fichier ASS avec les sous-titres

        Args:
            segments: Segments de sous-titres
            output_path: Chemin du fichier ASS
            style_name: Nom du style à utiliser
        """
        style = self.styles.get(style_name, self.styles["default"])

        # Header ASS
        ass_content = """[Script Info]
Title: AutoCut Animated Subtitles
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""

        # Style definition
        style_line = (
            f"Style: Default,{style['font']},{style['font_size']},"
            f"{style['primary_color']},{style['secondary_color']},"
            f"{style['outline_color']},{style['back_color']},"
            f"{'-1' if style['bold'] else '0'},0,0,0,100,100,0,0,1,"
            f"{style['outline']},{style['shadow']},{style['alignment']},"
            f"50,50,{style['margin_v']},1\n"
        )

        ass_content += style_line

        # Events
        ass_content += "\n[Events]\n"
        ass_content += "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"

        for segment in segments:
            start_time = self._format_ass_time(segment["start"])
            end_time = self._format_ass_time(segment["end"])
            text = segment["text"]

            # Ajouter effet de fondu (fade in/out)
            # {\fad(300,300)} = fade in 300ms, fade out 300ms
            text_with_effects = f"{{\\fad(200,200)}}{text}"

            event_line = (
                f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,"
                f"{text_with_effects}\n"
            )
            ass_content += event_line

        # Écrire le fichier
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)

        logger.info(f"Fichier ASS généré: {output_path}")

    def _format_ass_time(self, seconds: float) -> str:
        """
        Formate un timestamp en format ASS (H:MM:SS.cc)

        Args:
            seconds: Temps en secondes

        Returns:
            Timestamp formaté
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)

        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

    async def _burn_subtitles(
        self,
        video_path: Path,
        output_path: Path,
        ass_path: Path
    ) -> bool:
        """
        Intègre les sous-titres dans la vidéo avec FFmpeg

        Args:
            video_path: Vidéo source
            output_path: Vidéo de sortie
            ass_path: Fichier ASS

        Returns:
            True si succès
        """
        try:
            # Commande FFmpeg pour burn les sous-titres
            # On utilise le filtre ass pour les sous-titres ASS
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite
                "-i", str(video_path),
                "-vf", f"ass={str(ass_path)}",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-c:a", "copy",  # Copier l'audio sans ré-encodage
                str(output_path)
            ]

            # Exécuter FFmpeg de manière asynchrone
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )

            if result.returncode != 0:
                logger.error(f"Erreur FFmpeg: {result.stderr}")
                return False

            logger.info(f"Sous-titres intégrés avec succès: {output_path}")
            return True

        except subprocess.TimeoutExpired:
            logger.error("Timeout lors de l'intégration des sous-titres")
            return False
        except Exception as e:
            logger.error(f"Erreur lors du burn des sous-titres: {e}", exc_info=True)
            return False


class SubtitleStylePresets:
    """Presets de styles de sous-titres pour différents réseaux sociaux"""

    @staticmethod
    def get_tiktok_style() -> Dict[str, Any]:
        """Style optimisé pour TikTok"""
        return {
            "font": "Arial",
            "font_size": 24,
            "primary_color": "&H00FFFFFF",  # Blanc
            "secondary_color": "&H0000FFFF",  # Jaune
            "outline_color": "&H00000000",  # Noir
            "back_color": "&H80000000",
            "bold": True,
            "outline": 4,  # Contour plus épais
            "shadow": 3,
            "alignment": 8,  # Haut (TikTok style)
            "margin_v": 120,
        }

    @staticmethod
    def get_instagram_style() -> Dict[str, Any]:
        """Style optimisé pour Instagram Reels"""
        return {
            "font": "Arial",
            "font_size": 22,
            "primary_color": "&H00FFFFFF",
            "secondary_color": "&H00FF00FF",  # Magenta
            "outline_color": "&H00000000",
            "back_color": "&H90000000",  # Fond plus transparent
            "bold": True,
            "outline": 3,
            "shadow": 2,
            "alignment": 2,  # Bas
            "margin_v": 100,
        }

    @staticmethod
    def get_youtube_shorts_style() -> Dict[str, Any]:
        """Style optimisé pour YouTube Shorts"""
        return {
            "font": "Arial",
            "font_size": 20,
            "primary_color": "&H00FFFFFF",
            "secondary_color": "&H000000FF",  # Rouge YouTube
            "outline_color": "&H00000000",
            "back_color": "&H80000000",
            "bold": True,
            "outline": 3,
            "shadow": 2,
            "alignment": 2,  # Bas
            "margin_v": 80,
        }
