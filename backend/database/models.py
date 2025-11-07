"""
Database models for job persistence
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from .database import Base
import uuid


class Job(Base):
    """Job model for storing video processing jobs"""

    __tablename__ = "jobs"

    # Primary key
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Job metadata
    status = Column(String, nullable=False, index=True)  # uploaded, processing, completed, failed
    filename = Column(String, nullable=False)
    video_path = Column(String, nullable=True)

    # Settings (stored as JSON)
    settings = Column(JSON, nullable=True)

    # Results (stored as JSON)
    result = Column(JSON, nullable=True)

    # Error message if failed
    error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    duration_seconds = Column(Float, nullable=True)
    total_cuts = Column(Integer, nullable=True)
    silence_periods_removed = Column(Integer, nullable=True)
    filler_words_detected = Column(Integer, nullable=True, default=0)
    percentage_saved = Column(Float, nullable=True)

    # Export paths
    premiere_pro_export = Column(String, nullable=True)
    final_cut_pro_export = Column(String, nullable=True)

    def __repr__(self):
        return f"<Job(id={self.id}, filename={self.filename}, status={self.status})>"

    def to_dict(self):
        """Convert job to dictionary"""
        return {
            "id": self.id,
            "status": self.status,
            "filename": self.filename,
            "video_path": self.video_path,
            "settings": self.settings,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "total_cuts": self.total_cuts,
            "silence_periods_removed": self.silence_periods_removed,
            "filler_words_detected": self.filler_words_detected,
            "percentage_saved": self.percentage_saved,
            "premiere_pro_export": self.premiere_pro_export,
            "final_cut_pro_export": self.final_cut_pro_export
        }
