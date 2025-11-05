"""
WebSocket manager for real-time progress updates
"""
import logging
from typing import Dict, Set
from fastapi import WebSocket
import json
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for progress updates"""

    def __init__(self):
        # Map of job_id to set of connected clients
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """Connect a client to a specific job"""
        await websocket.accept()

        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        logger.info(f"Client connected to job {job_id}")

    def disconnect(self, websocket: WebSocket, job_id: str):
        """Disconnect a client from a job"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)

            # Clean up empty job entries
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

        logger.info(f"Client disconnected from job {job_id}")

    async def send_progress(self, job_id: str, progress: float, message: str):
        """Send progress update to all clients watching a job"""
        if job_id not in self.active_connections:
            return

        data = {
            'type': 'progress',
            'job_id': job_id,
            'progress': progress,
            'message': message
        }

        # Send to all connected clients for this job
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, job_id)

    async def send_result(self, job_id: str, result: dict):
        """Send final result to all clients watching a job"""
        if job_id not in self.active_connections:
            return

        data = {
            'type': 'result',
            'job_id': job_id,
            'result': result
        }

        # Send to all connected clients for this job
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, job_id)

    async def send_error(self, job_id: str, error: str):
        """Send error message to all clients watching a job"""
        if job_id not in self.active_connections:
            return

        data = {
            'type': 'error',
            'job_id': job_id,
            'error': error
        }

        # Send to all connected clients for this job
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected.add(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket, job_id)


# Global WebSocket manager instance
ws_manager = WebSocketManager()
