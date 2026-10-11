import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class AnnotationSource(str, enum.Enum):
    AI_GENERATED = "AI_GENERATED"
    HUMAN_VERIFIED = "HUMAN_VERIFIED"


class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(100), nullable=False, index=True)
    start_time_ms = Column(Integer, nullable=False)
    end_time_ms = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=True)
    source = Column(SQLEnum(AnnotationSource), default=AnnotationSource.AI_GENERATED, nullable=False)
    model_name = Column(String(100), nullable=True)
    model_version = Column(String(50), nullable=True)
    revision = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("Submission", back_populates="annotations")
