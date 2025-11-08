"""
CRUD operations for database models
"""
import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
from .models import Job

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository for Job operations"""

    @staticmethod
    def create_job(
        db: Session,
        job_id: str,
        filename: str,
        video_path: str,
        settings: Dict[str, Any]
    ) -> Job:
        """
        Create a new job

        Args:
            db: Database session
            job_id: Unique job ID
            filename: Original filename
            video_path: Path to uploaded video
            settings: Job settings

        Returns:
            Created job
        """
        job = Job(
            id=job_id,
            status="uploaded",
            filename=filename,
            video_path=video_path,
            settings=settings
        )

        db.add(job)
        db.commit()
        db.refresh(job)

        logger.info(f"Created job {job_id} for {filename}")
        return job

    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[Job]:
        """
        Get job by ID

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            Job or None if not found
        """
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_all_jobs(
        db: Session,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None
    ) -> List[Job]:
        """
        Get all jobs with optional filtering

        Args:
            db: Database session
            limit: Maximum number of jobs to return
            offset: Offset for pagination
            status: Filter by status

        Returns:
            List of jobs
        """
        query = db.query(Job).order_by(Job.created_at.desc())

        if status:
            query = query.filter(Job.status == status)

        return query.offset(offset).limit(limit).all()

    @staticmethod
    def update_job_status(
        db: Session,
        job_id: str,
        status: str,
        error: Optional[str] = None
    ) -> Optional[Job]:
        """
        Update job status

        Args:
            db: Database session
            job_id: Job ID
            status: New status
            error: Error message if failed

        Returns:
            Updated job or None
        """
        job = JobRepository.get_job(db, job_id)

        if job:
            job.status = status
            job.updated_at = datetime.utcnow()

            if error:
                job.error = error

            if status == "completed":
                job.completed_at = datetime.utcnow()

            db.commit()
            db.refresh(job)
            logger.info(f"Updated job {job_id} status to {status}")

        return job

    @staticmethod
    def update_job_result(
        db: Session,
        job_id: str,
        result: Dict[str, Any]
    ) -> Optional[Job]:
        """
        Update job with processing result

        Args:
            db: Database session
            job_id: Job ID
            result: Processing result

        Returns:
            Updated job or None
        """
        job = JobRepository.get_job(db, job_id)

        if job:
            job.result = result
            job.status = "completed" if result.get("success") else "failed"
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()

            # Extract statistics from result
            if result.get("success"):
                job.duration_seconds = result.get("duration_seconds")
                job.total_cuts = result.get("total_cuts")
                job.silence_periods_removed = result.get("silence_periods_removed")
                job.filler_words_detected = result.get("filler_words_detected", 0)
                job.percentage_saved = result.get("percentage_saved")

                # Extract export paths
                exports = result.get("exports", {})
                job.premiere_pro_export = exports.get("premiere_pro")
                job.final_cut_pro_export = exports.get("final_cut_pro")

            db.commit()
            db.refresh(job)
            logger.info(f"Updated job {job_id} with result")

        return job

    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        """
        Delete a job and all associated files

        Args:
            db: Database session
            job_id: Job ID

        Returns:
            True if deleted, False otherwise
        """
        job = JobRepository.get_job(db, job_id)

        if job:
            # Delete all associated files before deleting the database record
            files_to_delete = []

            # Add video file if exists
            if job.video_path:
                video_path = Path(job.video_path)
                files_to_delete.append(job.video_path)

                # Add temporary audio files that may have been created
                # Pattern: {video_stem}_audio.wav
                audio_file = video_path.parent / f"{video_path.stem}_audio.wav"
                if audio_file.exists():
                    files_to_delete.append(str(audio_file))

                # Pattern: {video_stem}_enhanced.wav (if audio enhancement was used)
                enhanced_audio_file = video_path.parent / f"{video_path.stem}_enhanced.wav"
                if enhanced_audio_file.exists():
                    files_to_delete.append(str(enhanced_audio_file))

            # Add Premiere Pro export if exists
            if job.premiere_pro_export:
                files_to_delete.append(job.premiere_pro_export)

            # Add Final Cut Pro export if exists
            if job.final_cut_pro_export:
                files_to_delete.append(job.final_cut_pro_export)

            # Delete each file
            for file_path in files_to_delete:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.info(f"Deleted file: {file_path}")
                    else:
                        logger.warning(f"File not found: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")

            # Delete the database record
            db.delete(job)
            db.commit()
            logger.info(f"Deleted job {job_id} and all associated files")
            return True

        return False

    @staticmethod
    def delete_old_jobs(db: Session, days: int = 30) -> int:
        """
        Delete jobs older than specified days

        Args:
            db: Database session
            days: Number of days to keep

        Returns:
            Number of jobs deleted
        """
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted = db.query(Job).filter(Job.created_at < cutoff_date).delete()
        db.commit()

        logger.info(f"Deleted {deleted} jobs older than {days} days")
        return deleted

    @staticmethod
    def count_jobs(db: Session, status: Optional[str] = None) -> int:
        """
        Count jobs with optional status filter

        Args:
            db: Database session
            status: Filter by status

        Returns:
            Number of jobs
        """
        query = db.query(Job)

        if status:
            query = query.filter(Job.status == status)

        return query.count()
