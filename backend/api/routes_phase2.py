"""
API routes for Phase 2 features (Transcription & YouTube Optimization)
"""
import logging
import asyncio
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from ..config import settings
from ..services.transcription.whisper_service import WhisperTranscriptionService
from ..services.transcription.formatter import TranscriptionFormatter
from ..services.youtube_optimization.youtube_optimizer import YouTubeOptimizer
from ..services.short_clips.clip_detector import ClipDetector
from ..services.short_clips.clip_extractor import ClipExtractor
from ..services.short_clips.local_clip_scorer import LocalClipScorer
from .websocket_manager import ws_manager
from .routes import active_jobs
from ..database import SessionLocal, JobRepository

logger = logging.getLogger(__name__)

router = APIRouter()


def update_job_phase2_result(job_id: str, phase_key: str, phase_result: dict):
    """
    Update job result in database with Phase 2 data (transcription, youtube_optimization, clips)

    Args:
        job_id: Job ID
        phase_key: Key for the phase result (e.g., 'transcription', 'youtube_optimization', 'clips')
        phase_result: Result data to store
    """
    db = SessionLocal()
    try:
        job = JobRepository.get_job(db, job_id)
        if job and job.result:
            # Get existing result and update with new phase data
            result = job.result.copy() if isinstance(job.result, dict) else {}
            result[phase_key] = phase_result

            # Update job result in database
            job.result = result
            job.updated_at = __import__('datetime').datetime.utcnow()
            db.commit()
            db.refresh(job)
            logger.info(f"Updated job {job_id} with {phase_key} result in database")
    except Exception as e:
        logger.error(f"Error updating job {job_id} with {phase_key} result: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("/transcribe/{job_id}")
async def transcribe_video(job_id: str):
    """
    Start transcription for a processed video

    Args:
        job_id: Job ID from Phase 1 processing

    Returns:
        Status message
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Video must be processed first (Phase 1)")

    # Start transcription in background
    asyncio.create_task(transcribe_video_task(job_id))

    return {
        "job_id": job_id,
        "status": "transcribing",
        "message": "Transcription started"
    }


async def transcribe_video_task(job_id: str):
    """Background task to transcribe video"""
    try:
        job = active_jobs[job_id]
        video_path = Path(job['video_path'])

        # Update status
        job['transcription_status'] = 'transcribing'

        # Progress callback
        async def progress_callback(progress: float, message: str):
            await ws_manager.send_progress(job_id, progress, message)

        # Get audio path from Phase 1 (already extracted)
        audio_filename = video_path.stem + "_audio.wav"
        audio_path = video_path.parent / audio_filename

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        await progress_callback(0, "Starting transcription...")

        # Transcribe (synchronous operation in thread pool to not block)
        import concurrent.futures
        transcription_service = WhisperTranscriptionService()

        # Run transcription in executor to not block event loop
        loop = asyncio.get_event_loop()
        transcription_result = await loop.run_in_executor(
            None,
            transcription_service.transcribe_video,
            video_path,
            audio_path,
            progress_callback  # Pass the async callback directly
        )

        await progress_callback(90, "Saving transcription files...")

        # Save transcription files
        output_dir = settings.OUTPUT_DIR / Path(video_path.stem).stem
        output_dir.mkdir(parents=True, exist_ok=True)

        formatter = TranscriptionFormatter()

        # Save SRT
        srt_path = formatter.to_srt(transcription_result['segments'], output_dir / f"{Path(video_path).stem}_subtitles.srt")

        # Save VTT
        vtt_path = formatter.to_vtt(transcription_result['segments'], output_dir / f"{Path(video_path).stem}_subtitles.vtt")

        # Save TXT
        txt_path = formatter.to_txt(transcription_result['text'], output_dir / f"{Path(video_path).stem}_transcription.txt")

        # Store result with download URLs
        job['transcription_result'] = {
            **transcription_result,
            'srt_path': str(srt_path),
            'vtt_path': str(vtt_path),
            'txt_path': str(txt_path),
            'download_urls': {
                'srt': f"/download-transcription/{job_id}/srt",
                'vtt': f"/download-transcription/{job_id}/vtt",
                'txt': f"/download-transcription/{job_id}/txt"
            }
        }
        job['transcription_status'] = 'completed'

        # Save to database
        update_job_phase2_result(job_id, 'transcription', job['transcription_result'])

        await progress_callback(100, "✅ Transcription Whisper terminée ! Fichiers disponibles au téléchargement.")
        await ws_manager.send_result(job_id, {'transcription': job['transcription_result']})

    except Exception as e:
        logger.error(f"Error transcribing video: {e}", exc_info=True)
        job['transcription_status'] = 'failed'
        job['transcription_error'] = str(e)
        await ws_manager.send_error(job_id, f"Transcription error: {str(e)}")


@router.post("/optimize-youtube/{job_id}")
async def optimize_youtube(job_id: str):
    """
    Start YouTube optimization for a transcribed video

    Args:
        job_id: Job ID

    Returns:
        Status message
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if 'transcription_result' not in job:
        raise HTTPException(status_code=400, detail="Video must be transcribed first")

    # Start optimization in background
    asyncio.create_task(optimize_youtube_task(job_id))

    return {
        "job_id": job_id,
        "status": "optimizing",
        "message": "YouTube optimization started"
    }


async def optimize_youtube_task(job_id: str):
    """Background task to optimize for YouTube"""
    try:
        job = active_jobs[job_id]
        video_path = Path(job['video_path'])
        transcription_result = job['transcription_result']

        # Update status
        job['youtube_optimization_status'] = 'optimizing'

        # Progress callback
        async def progress_callback(progress: float, message: str):
            await ws_manager.send_progress(job_id, progress, message)

        # Output directory
        clean_name = Path(job['filename']).stem
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
        output_dir = settings.OUTPUT_DIR / clean_name

        # Optimize
        optimizer = YouTubeOptimizer()
        result = await optimizer.optimize_for_youtube(
            video_path,
            transcription_result,
            output_dir,
            progress_callback=progress_callback
        )

        # Store result
        job['youtube_optimization_result'] = result
        job['youtube_optimization_status'] = 'completed'

        # Save to database
        update_job_phase2_result(job_id, 'youtube_optimization', result)

        await ws_manager.send_result(job_id, {'youtube_optimization': result})

    except Exception as e:
        logger.error(f"Error optimizing for YouTube: {e}", exc_info=True)
        job['youtube_optimization_status'] = 'failed'
        job['youtube_optimization_error'] = str(e)
        await ws_manager.send_error(job_id, f"YouTube optimization error: {str(e)}")


@router.get("/transcription/{job_id}")
async def get_transcription(job_id: str):
    """Get transcription result for a job with download links"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if 'transcription_result' not in job:
        raise HTTPException(status_code=404, detail="Transcription not available")

    transcription = job['transcription_result']

    # Ensure download URLs are present (backward compatibility)
    if 'download_urls' not in transcription:
        transcription['download_urls'] = {
            'srt': f"/download-transcription/{job_id}/srt",
            'vtt': f"/download-transcription/{job_id}/vtt",
            'txt': f"/download-transcription/{job_id}/txt"
        }

    return {
        "job_id": job_id,
        "transcription": transcription,
        "message": "✅ Transcription Whisper (OpenAI) - Fichiers prêts au téléchargement"
    }


@router.get("/youtube-optimization/{job_id}")
async def get_youtube_optimization(job_id: str):
    """Get YouTube optimization result for a job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if 'youtube_optimization_result' not in job:
        raise HTTPException(status_code=404, detail="YouTube optimization not available")

    return {
        "job_id": job_id,
        "youtube_optimization": job['youtube_optimization_result']
    }


@router.get("/download-transcription/{job_id}/{format}")
async def download_transcription(job_id: str, format: str):
    """
    Download transcription file

    Args:
        job_id: Job ID
        format: Format (srt, vtt, txt)
    """
    # Try to get from database first (persistent storage)
    db = SessionLocal()
    try:
        job = JobRepository.get_job(db, job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        # Check if job has transcription result
        if not job.result or 'transcription' not in job.result:
            raise HTTPException(status_code=404, detail="Transcription not available")

        transcription_result = job.result['transcription']

        # Get file path
        file_key = f"{format}_path"
        if file_key not in transcription_result:
            raise HTTPException(status_code=404, detail=f"Format {format} not available")

        file_path = transcription_result[file_key]

        if not Path(file_path).exists():
            raise HTTPException(status_code=404, detail="File not found")

        return FileResponse(file_path, filename=Path(file_path).name)
    finally:
        db.close()


@router.post("/generate-clips/{job_id}")
async def generate_short_clips(
    job_id: str,
    num_clips: int = Query(3, ge=1, le=10),
    clip_format: str = Query("horizontal", regex="^(horizontal|vertical)$"),
    use_ai: bool = Query(False, description="Use GPT-4 for detection (requires transcription) or local scoring"),
    add_subtitles: bool = Query(False, description="Ajouter des sous-titres animés aux clips (nécessite la transcription)"),
    subtitle_style: str = Query("default", regex="^(default|tiktok|instagram|youtube)$", description="Style de sous-titres"),
    subtitle_position: str = Query("bottom", regex="^(top|center|bottom)$", description="Position des sous-titres")
):
    """
    Generate short clips (TikTok/Reels/Shorts) from a video

    Args:
        job_id: Job ID
        num_clips: Number of clips to generate (1-10, default: 3)
        clip_format: "horizontal" (16:9) or "vertical" (9:16)
        use_ai: Use GPT-4 AI detection (True) or local scoring (False, default)
        add_subtitles: Ajouter des sous-titres animés (nécessite transcription Whisper)
        subtitle_style: Style de sous-titres (default, tiktok, instagram, youtube)
        subtitle_position: Position des sous-titres (top, center, bottom)

    Returns:
        Status message
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    # Check if video processing is complete
    if job.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="Video must be processed first (Phase 1)")

    # If using AI, require transcription
    if use_ai and 'transcription_result' not in job:
        raise HTTPException(status_code=400, detail="AI mode requires video transcription first")

    # If adding subtitles, require transcription
    if add_subtitles and 'transcription_result' not in job:
        raise HTTPException(status_code=400, detail="Subtitles require video transcription first (Whisper)")

    # Start clip generation in background
    asyncio.create_task(generate_clips_task(
        job_id, num_clips, clip_format, use_ai,
        add_subtitles, subtitle_style, subtitle_position
    ))

    detection_method = "GPT-4 AI (analyse du texte transcrit)" if use_ai else "Local scoring (100% gratuit)"

    subtitle_info = f" avec sous-titres animés ({subtitle_style})" if add_subtitles else ""

    transcription_info = ""
    if use_ai or add_subtitles:
        transcription_info = " | ✅ Réutilise la transcription Whisper déjà faite"

    return {
        "job_id": job_id,
        "status": "generating_clips",
        "message": f"Génération de {num_clips} clips courts via {detection_method}{subtitle_info}{transcription_info}",
        "num_clips": num_clips,
        "format": clip_format,
        "detection_method": detection_method,
        "subtitles_enabled": add_subtitles,
        "subtitle_style": subtitle_style if add_subtitles else None,
        "reuses_transcription": use_ai or (add_subtitles and 'transcription_result' in job)
    }


async def generate_clips_task(
    job_id: str,
    num_clips: int,
    clip_format: str,
    use_ai: bool = False,
    add_subtitles: bool = False,
    subtitle_style: str = "default",
    subtitle_position: str = "bottom"
):
    """Background task to generate short clips"""
    try:
        job = active_jobs[job_id]
        video_path = Path(job['video_path'])

        # Update status
        job['clips_generation_status'] = 'generating'

        # Progress callback
        async def progress_callback(progress: float, message: str):
            await ws_manager.send_progress(job_id, progress, message)

        # Step 1: Detect best moments
        if use_ai and 'transcription_result' in job:
            # Use GPT-4 AI detection
            await progress_callback(0, "✅ Réutilisation de la transcription Whisper existante...")
            await progress_callback(10, "🤖 Analyse IA avec GPT-4 pour détecter les moments viraux...")
            transcription_result = job['transcription_result']

            detector = ClipDetector()
            clip_suggestions = detector.detect_best_moments(
                transcription=transcription_result['text'],
                segments=transcription_result['segments'],
                num_clips=num_clips,
                target_duration=45  # 45 seconds for Shorts/Reels
            )
        else:
            # Use local scoring (no AI, no cost!)
            await progress_callback(0, "Analyse locale des meilleurs moments (vannes, énergie)...")

            # Check if we have transcription from Whisper (local)
            if 'transcription_result' in job:
                # Use Whisper transcription segments
                await progress_callback(5, "✅ Utilisation de la transcription Whisper existante...")
                transcription_result = job['transcription_result']
                segments = transcription_result['segments']
            else:
                # No transcription available - use silence detection data from Phase 1
                # Create dummy segments based on kept audio regions
                logger.warning("No transcription available, using Phase 1 silence data")
                result = job.get('result', {})

                # Get video duration
                if 'duration_seconds' not in result:
                    raise Exception("Cannot generate clips without transcription or duration data")

                # Create segments from kept regions (speech segments)
                # This is a simplified approach - we split the video into equal parts
                duration = result['duration_seconds']
                segment_length = 10  # 10 second segments
                segments = []

                for i in range(0, int(duration), segment_length):
                    segments.append({
                        'start': i,
                        'end': min(i + segment_length, duration),
                        'text': f"Segment {i//segment_length + 1}"  # Dummy text
                    })

            # Use local scorer
            scorer = LocalClipScorer()
            clip_suggestions = scorer.score_segments(
                segments=segments,
                num_clips=num_clips,
                target_duration=45
            )

        if not clip_suggestions:
            raise Exception("No suitable clips detected")

        await progress_callback(30, f"Trouvé {len(clip_suggestions)} moments intéressants ! Extraction en cours...")

        # Step 2: Extract clips
        clean_name = Path(job['filename']).stem
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()
        output_dir = settings.OUTPUT_DIR / clean_name / "short_clips"

        # Préparer les segments de transcription pour les sous-titres
        transcription_segments = None
        if add_subtitles and 'transcription_result' in job:
            await progress_callback(35, "✅ Utilisation de la transcription Whisper pour les sous-titres...")
            transcription_segments = job['transcription_result']['segments']

        extractor = ClipExtractor()
        extracted_clips = await extractor.extract_clips(
            video_path=video_path,
            clips=clip_suggestions,
            output_dir=output_dir,
            format=clip_format,
            progress_callback=progress_callback,
            add_subtitles=add_subtitles,
            transcription_segments=transcription_segments,
            subtitle_style=subtitle_style,
            subtitle_position=subtitle_position
        )

        # Convert file paths to URLs and add download URLs
        for idx, clip in enumerate(extracted_clips):
            abs_path = Path(clip['file_path'])
            rel_path = abs_path.relative_to(settings.OUTPUT_DIR)
            clip['url'] = f"/outputs/{rel_path.as_posix()}"
            clip['download_url'] = f"/download-clip/{job_id}/{idx}"

        # Store result
        job['short_clips_result'] = {
            "success": True,
            "clips": extracted_clips,
            "num_clips": len(extracted_clips),
            "format": clip_format,
            "has_subtitles": add_subtitles,
            "subtitle_style": subtitle_style if add_subtitles else None
        }
        job['clips_generation_status'] = 'completed'

        # Save to database
        update_job_phase2_result(job_id, 'short_clips', job['short_clips_result'])

        await progress_callback(100, f"✅ {len(extracted_clips)} clips générés avec succès ! Téléchargement disponible.")
        await ws_manager.send_result(job_id, {'short_clips': job['short_clips_result']})

    except Exception as e:
        logger.error(f"Error generating clips: {e}", exc_info=True)
        job['clips_generation_status'] = 'failed'
        job['clips_generation_error'] = str(e)
        await ws_manager.send_error(job_id, f"Clip generation error: {str(e)}")


@router.get("/clips/{job_id}")
async def get_short_clips(job_id: str):
    """Get short clips result for a job with download links"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if 'short_clips_result' not in job:
        raise HTTPException(status_code=404, detail="Short clips not available")

    clips_result = job['short_clips_result']

    # Ensure download URLs are present for each clip (backward compatibility)
    for idx, clip in enumerate(clips_result.get('clips', [])):
        if 'download_url' not in clip:
            clip['download_url'] = f"/download-clip/{job_id}/{idx}"

    return {
        "job_id": job_id,
        "short_clips": clips_result,
        "message": "✅ Clips courts générés - Téléchargement disponible"
    }


@router.get("/download-clip/{job_id}/{clip_index}")
async def download_clip(job_id: str, clip_index: int):
    """
    Download a specific short clip

    Args:
        job_id: Job ID
        clip_index: Index of the clip (0-based)
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if 'short_clips_result' not in job:
        raise HTTPException(status_code=404, detail="Short clips not available")

    clips = job['short_clips_result'].get('clips', [])

    if clip_index < 0 or clip_index >= len(clips):
        raise HTTPException(status_code=404, detail="Clip index out of range")

    clip = clips[clip_index]
    file_path = clip['file_path']

    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Clip file not found")

    return FileResponse(file_path, filename=Path(file_path).name)
