import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    UPLOADING = "UPLOADING"
    PROCESSING = "PROCESSING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AssetType(str, enum.Enum):
    RAW_VIDEO = "RAW_VIDEO"
    EXTRACTED_FRAME = "EXTRACTED_FRAME"
    THUMBNAIL = "THUMBNAIL"
    PROCESSED_VIDEO = "PROCESSED_VIDEO"


class AssetStatus(str, enum.Enum):
    PENDING_UPLOAD = "PENDING_UPLOAD"
    UPLOADED = "UPLOADED"
    VERIFIED = "VERIFIED"
    CORRUPT = "CORRUPT"


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    episode_id = Column(String(36), unique=True, default=lambda: str(uuid.uuid4()), nullable=False, index=True)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.DRAFT, nullable=False, index=True)
    task_version = Column(Integer, default=1, nullable=False)
    rejection_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    task = relationship("Task", back_populates="submissions")
    contributor = relationship("User", back_populates="submissions")
    media_assets = relationship("MediaAsset", back_populates="submission", cascade="all, delete-orphan")
    annotations = relationship("Annotation", back_populates="submission", cascade="all, delete-orphan")
    quality_reviews = relationship("QualityReview", back_populates="submission", cascade="all, delete-orphan")
    consents = relationship("Consent", back_populates="submission", cascade="all, delete-orphan")
    dataset_items = relationship("DatasetItem", back_populates="submission", cascade="all, delete-orphan")


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(SQLEnum(AssetType), default=AssetType.RAW_VIDEO, nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    s3_key = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, default=0, nullable=False)
    mime_type = Column(String(100), default="video/mp4", nullable=False)
    checksum_sha256 = Column(String(64), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    status = Column(SQLEnum(AssetStatus), default=AssetStatus.PENDING_UPLOAD, nullable=False)
    upload_session_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("Submission", back_populates="media_assets")
