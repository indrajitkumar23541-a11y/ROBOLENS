import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class ReviewDecision(str, enum.Enum):
    PASS = "PASS"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAIL = "FAIL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class QualityReview(Base):
    __tablename__ = "quality_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    decision = Column(SQLEnum(ReviewDecision), nullable=False)
    rejection_reason = Column(String(255), nullable=True)
    feedback_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("Submission", back_populates="quality_reviews")
    reviewer = relationship("User")
