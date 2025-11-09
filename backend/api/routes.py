"""
API routes for AutoCut application
"""
import logging
import asyncio
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.responses import FileResponse
import aiofiles
import os

from ..config import settings
from ..services.video_processing.processor import VideoProcessor
from .websocket_manager import ws_manager
from ..database import SessionLocal, JobRepository

logger = logging.getLogger(__name__)

router = APIRouter()

# Legacy: Store active processing jobs (in-memory for WebSocket communication)
# Database now stores persistent job history
active_jobs = {}


@router.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "AutoCut API",
        "version": "1.0.0"
    }


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    silence_threshold: int = Form(-40),
    min_silence_duration: int = Form(500),
    padding: int = Form(100),
    fps: int = Form(30),
    detect_filler_words: bool = Form(False),
    filler_sensitivity: float = Form(0.7),
    whisper_model: str = Form("base"),
    enable_audio_enhancement: bool = Form(False),
    noise_reduction_strength: float = Form(0.7),
    processing_mode: str = Form("local")
):
    """
    Upload a video file for processing

    Args:
        file: Video file (MP4 or MOV)
        silence_threshold: Silence threshold in dB (default: -40)
        min_silence_duration: Minimum silence duration in ms (default: 500)
        padding: Padding around cuts in ms (default: 100)
        fps: Frames per second for export (default: 30)
        detect_filler_words: Enable filler words detection (default: False)
        filler_sensitivity: Filler detection sensitivity 0.0-1.0 (default: 0.7)
        whisper_model: Whisper model for filler detection (default: "base")
        enable_audio_enhancement: Enable audio noise reduction (default: False)
        noise_reduction_strength: Noise reduction strength 0.0-1.0 (default: 0.7)
        processing_mode: Processing mode - 'local' or 'gpt4' (default: 'local')

    Returns:
        Job ID for tracking progress
    """
    # Validate file format
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported formats: {settings.SUPPORTED_FORMATS}"
        )

    # Generate unique job ID
    job_id = str(uuid.uuid4())

    # Save uploaded file
    upload_path = settings.UPLOAD_DIR / f"{job_id}_{file.filename}"

    try:
        # Ensure upload directory exists
        settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(upload_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # Read 1MB at a time
                await f.write(chunk)

        logger.info(f"File uploaded: {upload_path}")

        # Prepare settings
        job_settings = {
            'silence_threshold': silence_threshold,
            'min_silence_duration': min_silence_duration,
            'padding': padding,
            'fps': fps,
            'detect_filler_words': detect_filler_words,
            'filler_sensitivity': filler_sensitivity,
            'whisper_model': whisper_model,
            'enable_audio_enhancement': enable_audio_enhancement,
            'noise_reduction_strength': noise_reduction_strength,
            'processing_mode': processing_mode
        }

        # Store job in database for persistence
        db = SessionLocal()
        try:
            JobRepository.create_job(
                db=db,
                job_id=job_id,
                filename=file.filename,
                video_path=str(upload_path),
                settings=job_settings
            )
        finally:
            db.close()

        # Store job info in memory (for active processing)
        active_jobs[job_id] = {
            'status': 'uploaded',
            'video_path': upload_path,
            'filename': file.filename,
            'settings': job_settings
        }

        # Start processing in background
        asyncio.create_task(
            process_video_task(
                job_id,
                upload_path,
                silence_threshold,
                min_silence_duration,
                padding,
                fps,
                detect_filler_words,
                filler_sensitivity,
                whisper_model,
                enable_audio_enhancement,
                noise_reduction_strength,
                processing_mode
            )
        )

        return {
            "job_id": job_id,
            "filename": file.filename,
            "status": "processing",
            "message": "Video uploaded successfully. Processing started."
        }

    except PermissionError as e:
        logger.error(f"Permission error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur de permissions: impossible d'écrire dans le dossier uploads. Vérifiez les permissions du dossier."
        )
    except OSError as e:
        logger.error(f"OS error uploading file: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur système: {str(e)}. Vérifiez que le disque n'est pas plein et que le dossier uploads existe."
        )
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"❌ Erreur lors de l'upload: {str(e)}"
        )


async def process_video_task(
    job_id: str,
    video_path: Path,
    silence_threshold: int,
    min_silence_duration: int,
    padding: int,
    fps: int,
    detect_filler_words: bool = False,
    filler_sensitivity: float = 0.7,
    whisper_model: str = "base",
    enable_audio_enhancement: bool = False,
    noise_reduction_strength: float = 0.7,
    processing_mode: str = "local"
):
    """Background task to process video"""
    try:
        # Update status in memory
        active_jobs[job_id]['status'] = 'processing'

        # Update status in database
        db = SessionLocal()
        try:
            JobRepository.update_job_status(db, job_id, 'processing')
        finally:
            db.close()

        # Create processor
        processor = VideoProcessor(
            silence_thresh=silence_threshold,
            min_silence_len=min_silence_duration,
            padding=padding,
            fps=fps,
            detect_filler_words=detect_filler_words,
            filler_sensitivity=filler_sensitivity,
            whisper_model=whisper_model,
            enable_audio_enhancement=enable_audio_enhancement,
            noise_reduction_strength=noise_reduction_strength,
            processing_mode=processing_mode
        )

        # Progress callback
        async def progress_callback(progress: float, message: str):
            await ws_manager.send_progress(job_id, progress, message)

        # Use original video name (stem) for output directory
        # Clean the name to remove special characters
        original_name = active_jobs[job_id]['filename']
        clean_name = Path(original_name).stem
        # Remove special characters that might cause issues
        clean_name = "".join(c for c in clean_name if c.isalnum() or c in (' ', '-', '_')).strip()

        # Process video
        result = await processor.process_video(
            video_path,
            settings.OUTPUT_DIR / clean_name,
            progress_callback=progress_callback
        )

        # Update job status in memory
        active_jobs[job_id]['status'] = 'completed' if result['success'] else 'failed'
        active_jobs[job_id]['result'] = result

        # Update job in database
        db = SessionLocal()
        try:
            JobRepository.update_job_result(db, job_id, result)
        finally:
            db.close()

        # Send result to WebSocket clients
        if result['success']:
            await ws_manager.send_result(job_id, result)
        else:
            await ws_manager.send_error(job_id, result.get('error', 'Unknown error'))

    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)

        # Update in memory
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)

        # Update in database
        db = SessionLocal()
        try:
            JobRepository.update_job_status(db, job_id, 'failed', error=str(e))
        finally:
            db.close()

        await ws_manager.send_error(job_id, str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a processing job"""
    # First check active jobs (in-memory for current processing)
    if job_id in active_jobs:
        return active_jobs[job_id]

    # If not in active jobs, check database for completed/failed jobs
    db = SessionLocal()
    try:
        job = JobRepository.get_job(db, job_id)
        if job:
            return job.to_dict()
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    finally:
        db.close()


@router.get("/history")
async def get_job_history(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None
):
    """
    Get job history from database

    Args:
        limit: Maximum number of jobs to return (default: 100)
        offset: Offset for pagination (default: 0)
        status: Filter by status (uploaded, processing, completed, failed)

    Returns:
        List of jobs with metadata
    """
    db = SessionLocal()
    try:
        jobs = JobRepository.get_all_jobs(db, limit=limit, offset=offset, status=status)
        total_count = JobRepository.count_jobs(db, status=status)

        return {
            "jobs": [job.to_dict() for job in jobs],
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    finally:
        db.close()


@router.get("/stats")
async def get_statistics():
    """
    Get processing statistics

    Returns:
        Statistics about all jobs
    """
    db = SessionLocal()
    try:
        total_jobs = JobRepository.count_jobs(db)
        completed_jobs = JobRepository.count_jobs(db, status='completed')
        failed_jobs = JobRepository.count_jobs(db, status='failed')
        processing_jobs = JobRepository.count_jobs(db, status='processing')

        return {
            "total_jobs": total_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "processing": processing_jobs,
            "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
        }
    finally:
        db.close()


@router.delete("/job/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job from history

    Args:
        job_id: Job ID to delete

    Returns:
        Success message
    """
    db = SessionLocal()
    try:
        success = JobRepository.delete_job(db, job_id)
        if success:
            return {"message": "Job deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Job not found")
    finally:
        db.close()


@router.get("/download/{job_id}/{format}")
async def download_export(job_id: str, format: str):
    """
    Download exported XML file

    Args:
        job_id: Job ID
        format: Export format ('premiere_pro' or 'final_cut_pro')
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = active_jobs[job_id]

    if job['status'] != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed yet")

    if 'result' not in job or 'exports' not in job['result']:
        raise HTTPException(status_code=404, detail="Export files not found")

    export_path = job['result']['exports'].get(format)

    if not export_path or not Path(export_path).exists():
        raise HTTPException(status_code=404, detail=f"Export file not found for format: {format}")

    return FileResponse(
        export_path,
        media_type='application/xml',
        filename=Path(export_path).name
    )


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress updates"""
    await ws_manager.connect(websocket, job_id)

    try:
        # Send current status if job exists
        if job_id in active_jobs:
            await websocket.send_json({
                'type': 'status',
                'job_id': job_id,
                'status': active_jobs[job_id]['status']
            })

        # Keep connection alive
        while True:
            try:
                # Wait for messages from client (ping/pong)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Echo back to keep connection alive
                await websocket.send_json({'type': 'pong'})

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_json({'type': 'ping'})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, job_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket, job_id)


@router.post("/generate-titles/{job_id}")
async def generate_titles(job_id: str, request_data: dict):
    """
    Generate YouTube-optimized titles using local AI

    Args:
        job_id: Job ID from processing
        request_data: Dict with 'transcription' key

    Returns:
        Generated titles for A/B testing
    """
    from ..services.ai_services.local_title_generator import LocalTitleGenerator

    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        transcription = request_data.get('transcription', '')

        if not transcription:
            raise HTTPException(
                status_code=400,
                detail="Transcription text is required"
            )

        # Initialize local title generator
        # Try to use Ollama if available, otherwise use fallback
        title_generator = LocalTitleGenerator()

        # Generate 3 titles for A/B testing
        result = title_generator.generate_titles(
            transcription_text=transcription,
            num_titles=3
        )

        logger.info(f"Generated {len(result['titles'])} titles for job {job_id}")

        return result

    except Exception as e:
        logger.error(f"Error generating titles for job {job_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating titles: {str(e)}"
        )
