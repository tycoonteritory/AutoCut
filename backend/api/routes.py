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

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active jobs
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
    fps: int = Form(30)
):
    """
    Upload a video file for processing

    Args:
        file: Video file (MP4 or MOV)
        silence_threshold: Silence threshold in dB (default: -40)
        min_silence_duration: Minimum silence duration in ms (default: 500)
        padding: Padding around cuts in ms (default: 100)
        fps: Frames per second for export (default: 30)

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
        async with aiofiles.open(upload_path, 'wb') as f:
            while chunk := await file.read(1024 * 1024):  # Read 1MB at a time
                await f.write(chunk)

        logger.info(f"File uploaded: {upload_path}")

        # Store job info
        active_jobs[job_id] = {
            'status': 'uploaded',
            'video_path': upload_path,
            'filename': file.filename,
            'settings': {
                'silence_threshold': silence_threshold,
                'min_silence_duration': min_silence_duration,
                'padding': padding,
                'fps': fps
            }
        }

        # Start processing in background
        asyncio.create_task(
            process_video_task(
                job_id,
                upload_path,
                silence_threshold,
                min_silence_duration,
                padding,
                fps
            )
        )

        return {
            "job_id": job_id,
            "filename": file.filename,
            "status": "processing",
            "message": "Video uploaded successfully. Processing started."
        }

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


async def process_video_task(
    job_id: str,
    video_path: Path,
    silence_threshold: int,
    min_silence_duration: int,
    padding: int,
    fps: int
):
    """Background task to process video"""
    try:
        active_jobs[job_id]['status'] = 'processing'

        # Create processor
        processor = VideoProcessor(
            silence_thresh=silence_threshold,
            min_silence_len=min_silence_duration,
            padding=padding,
            fps=fps
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

        # Update job status
        active_jobs[job_id]['status'] = 'completed' if result['success'] else 'failed'
        active_jobs[job_id]['result'] = result

        # Send result to WebSocket clients
        if result['success']:
            await ws_manager.send_result(job_id, result)
        else:
            await ws_manager.send_error(job_id, result.get('error', 'Unknown error'))

    except Exception as e:
        logger.error(f"Error processing video: {e}", exc_info=True)
        active_jobs[job_id]['status'] = 'failed'
        active_jobs[job_id]['error'] = str(e)
        await ws_manager.send_error(job_id, str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a processing job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return active_jobs[job_id]


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
